#!/usr/bin/env python3
"""Backup-first Codex local-state maintenance.

Default mode is a read-only, privacy-safe report. Use --apply to archive/move/normalize.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


THREAD_ID_RE = re.compile(
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.I,
)
DELEGATION_SOURCE_RE = re.compile(
    r"<source_thread_id>\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s*</source_thread_id>",
    re.I | re.S,
)
PROJECT_HEADER_RE = re.compile(r"^\[projects\.([\"'])(.+)\1\]\s*$")
TEMP_PROJECT_RE = re.compile(
    r"(\\AppData\\Local\\Temp\\|/AppData/Local/Temp/|\\Temp\\codex-|/Temp/codex-|\\Temp\\spark-|/Temp/spark-)",
    re.I,
)
DEFAULT_TITLE_LIMIT = 120
DEFAULT_PREVIEW_LIMIT = 240
TEMP_PLUGIN_STATE_NAMES = (
    "bundled-marketplaces",
    "marketplaces",
    "plugins",
    "plugins.sha",
    "plugins.sync.lock",
)


@dataclass
class SessionCandidate:
    size: int
    thread_id: str
    title: str
    source: Path
    relative: Path
    updated_at: int | None


@dataclass
class ArchivedThreadPurgeCandidate:
    thread_id: str
    rollout_path: Path
    archived_at: int
    bytes: int


@dataclass
class ThreadMetadataRepair:
    thread_id: str
    old_title: str
    new_title: str
    old_preview: str
    new_preview: str


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def codex_home_from_args(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    override = os.environ.get("CODEX_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".codex"


def documents_backup_root() -> Path:
    docs = Path.home() / "Documents" / "Codex" / "codex-backups"
    if docs.parent.exists() or platform.system() == "Windows":
        return docs
    return Path.home() / ".codex" / "backups"


def size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return total


def gb(value: int) -> str:
    return f"{value / 1024 / 1024 / 1024:.3f}"


def mb(value: int) -> str:
    return f"{value / 1024 / 1024:.1f}"


def report(line: str) -> None:
    print(line)


def sqlite_connect(path: Path, *, readonly: bool) -> sqlite3.Connection:
    if readonly:
        return sqlite3.connect(f"{canonical_path(path).as_uri()}?mode=ro", uri=True)
    return sqlite3.connect(path)


def canonical_path(path: Path) -> Path:
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError):
        return path.absolute()


def codex_processes_running() -> list[str]:
    system = platform.system()
    try:
        if system == "Windows":
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process | Select-Object Name,ProcessId,CommandLine | ConvertTo-Json -Compress"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            if not output.strip():
                return []
            data = json.loads(output)
            rows = data if isinstance(data, list) else [data]
            hits = []
            for row in rows:
                name = str(row.get("Name") or "")
                cmd = str(row.get("CommandLine") or "")
                pid = row.get("ProcessId")
                if name.lower() == "codex.exe":
                    hits.append(f"{pid} {name}")
            return hits
        output = subprocess.check_output(["ps", "-axo", "pid=,comm=,args="], text=True)
        hits = []
        for line in output.splitlines():
            lower = line.lower()
            parts = line.strip().split(None, 2)
            command = Path(parts[1]).name.lower() if len(parts) >= 2 else ""
            if command == "codex" or (
                "codex" in lower
                and ("app-server" in lower or "openai.codex" in lower or "codex desktop" in lower)
            ):
                hits.append(line.strip())
        return hits
    except Exception:
        return []


def wait_for_codex_exit() -> None:
    while codex_processes_running():
        time.sleep(2)


def sqlite_backup(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite_connect(src, readonly=True)
    target = sqlite3.connect(dst)
    source.backup(target)
    target.close()
    source.close()


def copy_if_exists(src: Path, dst: Path, ignore_names: tuple[str, ...] = ()) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        ignore_patterns = shutil.ignore_patterns(
            "node_modules",
            ".git",
            ".next",
            "dist",
            "build",
            ".venv",
            "__pycache__",
            ".pytest_cache",
        )

        def ignore(path: str, names: list[str]) -> set[str]:
            ignored = set(ignore_patterns(path, names))
            if Path(path) == src:
                ignored.update(name for name in ignore_names if name in names)
            return ignored

        shutil.copytree(
            src,
            dst,
            ignore=ignore,
            dirs_exist_ok=True,
        )
    else:
        shutil.copy2(src, dst)
    report(f"backed_up {src.name}")


def backup_metadata(codex_home: Path, backup_root: Path) -> None:
    backup_root.mkdir(parents=True, exist_ok=True)
    for name in [
        ".codex-global-state.json",
        "config.toml",
        "history.jsonl",
        "installation_id",
        "models_cache.json",
        "session_index.jsonl",
        "version.json",
        "memories",
        "skills",
        "rules",
        "plugins",
        "automations",
    ]:
        ignore_names = (
            ("cache", ".remote-plugin-install-staging", ".plugin-appserver")
            if name == "plugins"
            else ()
        )
        copy_if_exists(codex_home / name, backup_root / name, ignore_names)
    sqlite_backup(codex_home / "state_5.sqlite", backup_root / "state_5.sqlite")


def load_pinned(codex_home: Path) -> set[str]:
    path = codex_home / ".codex-global-state.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("pinned-thread-ids", []))
    except Exception:
        return set()


def active_thread_ids(conn: sqlite3.Connection) -> set[str]:
    columns = table_columns(conn, "threads")
    if "id" not in columns:
        return set()
    if "archived" in columns:
        rows = conn.execute("select id from threads where COALESCE(archived,0)=0")
    elif "archived_at" in columns:
        rows = conn.execute("select id from threads where archived_at is null")
    else:
        rows = conn.execute("select id from threads")
    return {str(row[0]) for row in rows}


def repair_electron_ui_state(
    conn: sqlite3.Connection,
    codex_home: Path,
    backup_root: Path,
    *,
    apply: bool,
) -> None:
    path = codex_home / ".codex-global-state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        report("electron_ui_state skipped_unreadable")
        return

    active = active_thread_ids(conn)
    atoms = state.get("electron-persisted-atom-state")
    if not isinstance(atoms, dict):
        atoms = {}

    changes: dict[str, int] = {}

    def prune_map(container: dict, key: str, *, preserve: set[str] | None = None) -> None:
        value = container.get(key)
        if not isinstance(value, dict):
            return
        allowed = active | (preserve or set())
        stale = [item for item in value if item not in allowed]
        changes[key] = len(stale)
        if apply:
            container[key] = {item: item_value for item, item_value in value.items() if item in allowed}

    def prune_list(container: dict, key: str) -> None:
        value = container.get(key)
        if not isinstance(value, list):
            return
        kept = [item for item in value if item in active]
        changes[key] = len(value) - len(kept)
        if apply:
            container[key] = kept

    prune_map(atoms, "thread-descriptions-v1")
    unread = atoms.get("unread-thread-ids-by-host-v1")
    if isinstance(unread, dict):
        prune_list(unread, "local")
        if "local" in changes:
            changes["unread-thread-ids-by-host-v1.local"] = changes.pop("local")
    prune_map(atoms, "prompt-history", preserve={"global"})
    prune_map(atoms, "heartbeat-thread-permissions-by-id")
    prune_list(state, "projectless-thread-ids")
    prune_map(state, "thread-project-assignments")
    prune_map(state, "thread-workspace-root-hints")
    prune_map(state, "thread-projectless-output-directories")
    prune_map(state, "queued-follow-ups")

    total = sum(changes.values())
    report(f"electron_ui_state_stale_entries {total}")
    for key, count in sorted(changes.items()):
        report(f"electron_ui_state_candidate {key}={count}")
    if not apply or total == 0:
        return

    manifest = backup_root / "electron-ui-state-repair.json"
    manifest.write_text(
        json.dumps(
            {
                "live_file": str(path),
                "backup_file": str(backup_root / path.name),
                "removed_counts": changes,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary = path.with_name(path.name + ".keep-codex-fast.tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    os.chmod(temporary, path.stat().st_mode)
    os.replace(temporary, path)

    restore = backup_root / "restore-electron-ui-state.py"
    restore.write_text(
        f'''import os
import shutil
from pathlib import Path

live = Path(r"{path}")
backup = Path(r"{backup_root / path.name}")
if not backup.exists():
    raise SystemExit(f"Missing backup: {{backup}}")
temporary = live.with_name(live.name + ".restore.tmp")
shutil.copy2(backup, temporary)
os.replace(temporary, live)
print(f"Restored {{live}}")
''',
        encoding="utf-8",
    )
    report("electron_ui_state_repair applied")
    report(f"electron_ui_state_manifest {manifest}")
    report(f"electron_ui_state_restore_script {restore}")


def archive_temp_plugin_state(
    codex_home: Path,
    backup_root: Path,
    *,
    apply: bool,
) -> None:
    temp_root = codex_home / ".tmp"
    candidates = [temp_root / name for name in TEMP_PLUGIN_STATE_NAMES if (temp_root / name).exists()]
    total = sum(size_bytes(path) for path in candidates)
    report(f"temp_plugin_archive_candidates {len(candidates)}")
    report(f"temp_plugin_archive_mb {mb(total)}")
    if not apply or not candidates:
        return

    archive_root = backup_root / "archived-codex-tmp"
    archive_root.mkdir(parents=True, exist_ok=True)
    records = []
    for source in candidates:
        destination = archive_root / source.name
        if destination.exists():
            raise RuntimeError(f"temporary plugin archive destination already exists: {destination}")
        shutil.move(str(source), str(destination))
        records.append({"source": str(source), "archived": str(destination)})

    manifest = backup_root / "archived-temp-plugin-state.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    restore = backup_root / "restore-temp-plugin-state.py"
    restore.write_text(
        f'''import json
import shutil
from pathlib import Path

manifest = Path(r"{manifest}")
records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
for record in records:
    source = Path(record["archived"])
    destination = Path(record["source"])
    if destination.exists():
        raise SystemExit(f"Restore target already exists: {{destination}}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    print(f"Restored {{destination}}")
''',
        encoding="utf-8",
    )
    report(f"temp_plugin_archive_root {archive_root}")
    report(f"temp_plugin_archive_manifest {manifest}")
    report(f"temp_plugin_restore_script {restore}")


def normalize_extended_path(value: str) -> str:
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {row[1] for row in conn.execute(f'pragma table_info("{table}")').fetchall()}
    except sqlite3.Error:
        return set()


def has_threads_columns(conn: sqlite3.Connection, required: set[str]) -> bool:
    return required.issubset(table_columns(conn, "threads"))


def bounded_text(value: str, limit: int) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


def append_session_index_name(codex_home: Path, thread_id: str, name: str) -> None:
    path = codex_home / "session_index.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "id": thread_id,
        "thread_name": name,
        "updated_at": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def is_delegation_metadata(value: str | None) -> bool:
    text = str(value or "")
    return "<codex_delegation>" in text or "<source_thread_id>" in text


def load_latest_session_names(codex_home: Path) -> dict[str, str]:
    path = codex_home / "session_index.jsonl"
    latest: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return latest
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        thread_id = record.get("id")
        if thread_id and "thread_name" in record:
            latest[str(thread_id)] = str(record.get("thread_name") or "")
    return latest


def delegation_source_id(*values: str | None) -> str | None:
    for value in values:
        match = DELEGATION_SOURCE_RE.search(str(value or ""))
        if match:
            return match.group(1)
    return None


def repair_delegation_thread_titles(
    conn: sqlite3.Connection,
    codex_home: Path,
    backup_root: Path,
    *,
    apply: bool,
    title_limit: int,
) -> None:
    columns = table_columns(conn, "threads")
    if not {"id", "title"}.issubset(columns):
        report("delegation_thread_title_repair skipped_missing_threads_columns")
        return

    has_preview = "first_user_message" in columns
    preview_select = "first_user_message" if has_preview else "''"
    if "archived" in columns:
        active_select = "COALESCE(archived,0)=0"
    elif "archived_at" in columns:
        active_select = "archived_at is null"
    else:
        active_select = "1"
    rows = conn.execute(
        f"select id, title, {preview_select}, {active_select} from threads"
    ).fetchall()
    thread_rows = {
        str(thread_id): {
            "title": str(title or ""),
            "preview": str(preview or ""),
            "active": bool(active),
        }
        for thread_id, title, preview, active in rows
    }
    latest_names = load_latest_session_names(codex_home)

    def clean_name(value: str | None) -> str | None:
        text = str(value or "").strip()
        if not text or is_delegation_metadata(text):
            return None
        return bounded_text(text, title_limit)

    def corrected_name(thread_id: str, *values: str | None) -> str:
        existing_index_name = clean_name(latest_names.get(thread_id))
        if existing_index_name:
            return existing_index_name
        source_id = delegation_source_id(*values)
        if source_id:
            source_name = clean_name(latest_names.get(source_id))
            if not source_name:
                source_row = thread_rows.get(source_id)
                source_name = clean_name(source_row.get("title")) if source_row else None
            if source_name:
                return bounded_text(f"Delegated: {source_name}", title_limit)
        return "Delegated task"

    db_repairs: dict[str, dict[str, str]] = {}
    for thread_id, row in thread_rows.items():
        if not row["active"]:
            continue
        old_title = row["title"]
        old_preview = row["preview"]
        title_is_delegation = is_delegation_metadata(old_title)
        preview_is_delegation = is_delegation_metadata(old_preview)
        if not title_is_delegation and not preview_is_delegation:
            continue
        new_title = (
            corrected_name(thread_id, old_title, old_preview, latest_names.get(thread_id))
            if title_is_delegation
            else old_title
        )
        new_preview = new_title if preview_is_delegation else old_preview
        db_repairs[thread_id] = {
            "old_title": old_title,
            "new_title": new_title,
            "old_preview": old_preview,
            "new_preview": new_preview,
        }

    index_repairs: dict[str, str] = {}
    for thread_id, old_name in latest_names.items():
        if not is_delegation_metadata(old_name):
            continue
        row = thread_rows.get(thread_id)
        clean_db_title = clean_name(row.get("title")) if row else None
        if thread_id in db_repairs:
            new_name = db_repairs[thread_id]["new_title"]
        elif clean_db_title:
            new_name = clean_db_title
        else:
            values = [old_name]
            if row:
                values.extend([row.get("title"), row.get("preview")])
            new_name = corrected_name(thread_id, *values)
        if new_name != old_name:
            index_repairs[thread_id] = new_name
    for thread_id, repair in db_repairs.items():
        if repair["new_title"] != repair["old_title"]:
            index_repairs[thread_id] = repair["new_title"]

    report(f"delegation_thread_db_repair_candidates {len(db_repairs)}")
    report(f"delegation_thread_index_repair_candidates {len(index_repairs)}")
    generic_names = sum(name == "Delegated task" for name in index_repairs.values())
    report(f"delegation_thread_generic_name_candidates {generic_names}")
    if not apply or (not db_repairs and not index_repairs):
        return

    manifest = backup_root / "delegation-thread-title-repairs.jsonl"
    all_thread_ids = sorted(set(db_repairs) | set(index_repairs))
    with manifest.open("w", encoding="utf-8") as handle:
        for thread_id in all_thread_ids:
            row = thread_rows.get(thread_id, {"title": "", "preview": ""})
            repair = db_repairs.get(thread_id)
            record = {
                "thread_id": thread_id,
                "db_updated": repair is not None,
                "old_title": repair["old_title"] if repair else row["title"],
                "new_title": repair["new_title"] if repair else row["title"],
                "old_first_user_message": repair["old_preview"] if repair else row["preview"],
                "new_first_user_message": repair["new_preview"] if repair else row["preview"],
                "index_updated": thread_id in index_repairs,
                "old_index_name": latest_names.get(thread_id),
                "new_index_name": index_repairs.get(thread_id),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    cur = conn.cursor()
    for thread_id, repair in db_repairs.items():
        if has_preview:
            cur.execute(
                "update threads set title=?, first_user_message=? where id=?",
                (repair["new_title"], repair["new_preview"], thread_id),
            )
        else:
            cur.execute(
                "update threads set title=? where id=?",
                (repair["new_title"], thread_id),
            )
    for thread_id, new_name in index_repairs.items():
        append_session_index_name(codex_home, thread_id, new_name)

    restore = backup_root / "restore-delegation-thread-titles.py"
    restore.write_text(
        f'''import json
import sqlite3
from datetime import datetime
from pathlib import Path

manifest = Path(r"{manifest}")
db = Path(r"{codex_home / 'state_5.sqlite'}")
session_index = Path(r"{codex_home / 'session_index.jsonl'}")
conn = sqlite3.connect(db)
conn.execute("pragma busy_timeout=10000")
cols = {{row[1] for row in conn.execute('pragma table_info("threads")').fetchall()}}
has_preview = "first_user_message" in cols
records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
for rec in records:
    if rec["db_updated"]:
        if has_preview:
            conn.execute(
                "update threads set title=?, first_user_message=? where id=?",
                (rec["old_title"], rec["old_first_user_message"], rec["thread_id"]),
            )
        else:
            conn.execute("update threads set title=? where id=?", (rec["old_title"], rec["thread_id"]))
conn.commit()
conn.close()
with session_index.open("a", encoding="utf-8") as handle:
    for rec in records:
        if rec["index_updated"]:
            old_name = rec["old_index_name"] if rec["old_index_name"] is not None else rec["old_title"]
            entry = {{
                "id": rec["thread_id"],
                "thread_name": old_name,
                "updated_at": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            }}
            handle.write(json.dumps(entry, ensure_ascii=False) + "\\n")
''',
        encoding="utf-8",
    )
    report("delegation_thread_title_repair applied")
    report(f"delegation_thread_title_repair_manifest {manifest}")
    report(f"delegation_thread_title_restore_script {restore}")


def report_thread_metadata_bloat(
    conn: sqlite3.Connection,
    *,
    title_limit: int,
    preview_limit: int,
) -> None:
    columns = table_columns(conn, "threads")
    if not {"id", "title"}.issubset(columns):
        report("thread_metadata_bloat skipped_missing_threads_columns")
        return
    archived_expr = "COALESCE(archived,0)=0" if "archived" in columns else "archived_at is null"
    preview_col = "first_user_message" if "first_user_message" in columns else None
    if preview_col:
        row = conn.execute(
            f"""
            select
              count(*),
              coalesce(sum(length(title)), 0),
              coalesce(sum(length(first_user_message)), 0),
              coalesce(max(length(title)), 0),
              coalesce(max(length(first_user_message)), 0),
              sum(case when length(title) > ? then 1 else 0 end),
              sum(case when length(first_user_message) > ? then 1 else 0 end),
              sum(case when length(first_user_message) > 10000 then 1 else 0 end)
            from threads
            where {archived_expr}
            """,
            (title_limit, preview_limit),
        ).fetchone()
        (
            active_rows,
            title_chars,
            preview_chars,
            max_title,
            max_preview,
            title_over_limit,
            preview_over_limit,
            preview_over_10k,
        ) = row
    else:
        row = conn.execute(
            f"""
            select
              count(*),
              coalesce(sum(length(title)), 0),
              coalesce(max(length(title)), 0),
              sum(case when length(title) > ? then 1 else 0 end)
            from threads
            where {archived_expr}
            """,
            (title_limit,),
        ).fetchone()
        active_rows, title_chars, max_title, title_over_limit = row
        preview_chars = max_preview = preview_over_limit = preview_over_10k = 0

    report(f"thread_active_rows {active_rows}")
    report(f"thread_title_chars {title_chars}")
    report(f"thread_first_user_message_chars {preview_chars}")
    report(f"thread_max_title_chars {max_title}")
    report(f"thread_max_first_user_message_chars {max_preview}")
    report(f"thread_titles_over_limit {title_over_limit or 0}")
    report(f"thread_first_user_message_over_limit {preview_over_limit or 0}")
    report(f"thread_first_user_message_over_10k {preview_over_10k or 0}")


def repair_thread_metadata_bloat(
    conn: sqlite3.Connection,
    codex_home: Path,
    backup_root: Path,
    *,
    apply: bool,
    details: bool,
    title_limit: int,
    preview_limit: int,
) -> None:
    required = {"id", "title"}
    if not has_threads_columns(conn, required):
        report("thread_metadata_repair skipped_missing_threads_columns")
        return
    columns = table_columns(conn, "threads")
    has_preview = "first_user_message" in columns
    archived_expr = "COALESCE(archived,0)=0" if "archived" in columns else "archived_at is null"
    select_preview = "first_user_message" if has_preview else "''"
    rows = conn.execute(
        f"""
        select id, title, {select_preview}
        from threads
        where {archived_expr}
          and (
            length(title) > ?
            {"or length(first_user_message) > ?" if has_preview else ""}
          )
        """,
        (title_limit, preview_limit) if has_preview else (title_limit,),
    ).fetchall()

    repairs: list[ThreadMetadataRepair] = []
    for thread_id, title, preview in rows:
        old_title = title or ""
        old_preview = preview or ""
        if is_delegation_metadata(old_title) or is_delegation_metadata(old_preview):
            continue
        new_title = bounded_text(old_title, title_limit)
        new_preview = bounded_text(old_preview, preview_limit) if has_preview else ""
        if new_title != old_title or new_preview != old_preview:
            repairs.append(
                ThreadMetadataRepair(
                    str(thread_id),
                    old_title,
                    new_title,
                    old_preview,
                    new_preview,
                )
            )

    report(f"thread_metadata_repair_candidates {len(repairs)}")
    for index, item in enumerate(repairs[:10], start=1):
        label = f"thread_{index:03d}"
        title_delta = len(item.old_title) - len(item.new_title)
        preview_delta = len(item.old_preview) - len(item.new_preview)
        if details:
            report(
                f"thread_metadata_repair_candidate {label} thread_id={item.thread_id} "
                f"title_delta={title_delta} preview_delta={preview_delta}"
            )
        else:
            report(
                f"thread_metadata_repair_candidate {label} "
                f"title_delta={title_delta} preview_delta={preview_delta}"
            )

    if not apply or not repairs:
        return

    manifest = backup_root / "thread-metadata-repairs.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for item in repairs:
            record = {
                "thread_id": item.thread_id,
                "old_title": item.old_title,
                "new_title": item.new_title,
                "old_first_user_message": item.old_preview,
                "new_first_user_message": item.new_preview,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    cur = conn.cursor()
    for item in repairs:
        if has_preview:
            cur.execute(
                "update threads set title=?, first_user_message=? where id=?",
                (item.new_title, item.new_preview, item.thread_id),
            )
        else:
            cur.execute(
                "update threads set title=? where id=?",
                (item.new_title, item.thread_id),
            )
        if item.new_title and item.new_title != item.old_title:
            append_session_index_name(codex_home, item.thread_id, item.new_title)
    report("thread_metadata_repair applied")
    report(f"thread_metadata_repair_manifest {manifest}")
    write_thread_metadata_restore_script(manifest, codex_home / "state_5.sqlite", backup_root)


def write_thread_metadata_restore_script(manifest: Path, state_db: Path, backup_root: Path) -> None:
    restore = backup_root / "restore-thread-metadata.py"
    restore.write_text(
        f'''import json
import sqlite3
from pathlib import Path

manifest = Path(r"{manifest}")
db = Path(r"{state_db}")
conn = sqlite3.connect(db)
conn.execute("pragma busy_timeout=10000")
cols = {{row[1] for row in conn.execute('pragma table_info("threads")').fetchall()}}
has_preview = "first_user_message" in cols
for line in manifest.read_text(encoding="utf-8").splitlines():
    rec = json.loads(line)
    if has_preview:
        conn.execute(
            "update threads set title=?, first_user_message=? where id=?",
            (rec["old_title"], rec["old_first_user_message"], rec["thread_id"]),
        )
    else:
        conn.execute(
            "update threads set title=? where id=?",
            (rec["old_title"], rec["thread_id"]),
        )
conn.commit()
conn.close()
''',
        encoding="utf-8",
    )
    report(f"thread_metadata_restore_script {restore}")


def normalize_sqlite_paths(conn: sqlite3.Connection, apply: bool) -> int:
    cur = conn.cursor()
    total = 0
    tables = [
        row[0]
        for row in cur.execute(
            "select name from sqlite_master where type='table' and name not like 'sqlite_%'"
        )
    ]
    for table in tables:
        cols = cur.execute(f'pragma table_info("{table}")').fetchall()
        text_cols = [col[1] for col in cols if "TEXT" in (col[2] or "").upper() or col[2] == ""]
        for col in text_cols:
            rows = cur.execute(
                f'select rowid, "{col}" from "{table}" where "{col}" like ?',
                ("\\\\?\\%",),
            ).fetchall()
            changed = 0
            for rowid, value in rows:
                if isinstance(value, str) and value.startswith("\\\\?\\"):
                    changed += 1
                    if apply:
                        cur.execute(
                            f'update "{table}" set "{col}"=? where rowid=?',
                            (normalize_extended_path(value), rowid),
                        )
            if changed:
                report(f"extended_paths {table}.{col} {changed}")
                total += changed
    if total == 0:
        report("extended_paths 0")
    return total


def active_session_candidates(
    conn: sqlite3.Connection,
    codex_home: Path,
    archive_older_than_days: int,
) -> list[SessionCandidate]:
    sessions_root = codex_home / "sessions"
    sessions_root_canonical = canonical_path(sessions_root)
    cutoff = int((datetime.now() - timedelta(days=archive_older_than_days)).timestamp())
    pinned = load_pinned(codex_home)
    rows = conn.execute(
        "select id, title, rollout_path, updated_at from threads where archived_at is null"
    ).fetchall()
    candidates: list[SessionCandidate] = []
    for thread_id, title, rollout_path, updated_at in rows:
        if thread_id in pinned or not rollout_path:
            continue
        if updated_at is not None and int(updated_at) >= cutoff:
            continue
        source = Path(rollout_path)
        if not source.exists():
            continue
        try:
            relative = canonical_path(source).relative_to(sessions_root_canonical)
        except ValueError:
            continue
        candidates.append(
            SessionCandidate(source.stat().st_size, thread_id, title or "", source, relative, updated_at)
        )
    candidates.sort(key=lambda item: item.size, reverse=True)
    return candidates


def archive_sessions(
    conn: sqlite3.Connection,
    candidates: list[SessionCandidate],
    codex_home: Path,
    backup_root: Path,
    stamp: str,
    apply: bool,
    details: bool,
) -> None:
    total = sum(item.size for item in candidates)
    report(f"old_session_candidates {len(candidates)}")
    report(f"old_session_candidate_gb {gb(total)}")
    for index, item in enumerate(candidates[:10], start=1):
        label = f"session_{index:03d}"
        if details:
            report(f"large_session_mb {mb(item.size)} {label} thread_id={item.thread_id} title={item.title[:70]}")
        else:
            report(f"large_session_mb {mb(item.size)} {label}")
    if not apply or not candidates:
        return

    archive_root = codex_home / "archived_sessions" / f"keep-codex-fast-{stamp}"
    manifest = backup_root / "moved-sessions.jsonl"
    archive_root.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    cur = conn.cursor()
    with manifest.open("w", encoding="utf-8") as handle:
        for item in candidates:
            dest = archive_root / item.relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item.source), str(dest))
            record = {
                "thread_id": item.thread_id,
                "bytes": item.size,
                "from": str(item.source),
                "to": str(dest),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            cur.execute(
                "update threads set rollout_path=?, archived=1, archived_at=? where id=?",
                (str(dest), now, item.thread_id),
            )
    write_session_restore_script(manifest, codex_home / "state_5.sqlite", backup_root)
    report(f"archived_sessions_root {archive_root}")
    report(f"archived_sessions_manifest {manifest}")


def write_session_restore_script(manifest: Path, state_db: Path, backup_root: Path) -> None:
    restore = backup_root / "restore-sessions.py"
    restore.write_text(
        f'''import json
import shutil
import sqlite3
from pathlib import Path

manifest = Path(r"{manifest}")
db = Path(r"{state_db}")
conn = sqlite3.connect(db)
conn.execute("pragma busy_timeout=10000")
for line in manifest.read_text(encoding="utf-8").splitlines():
    rec = json.loads(line)
    src = Path(rec["to"])
    dest = Path(rec["from"])
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
    if rec.get("thread_id"):
        conn.execute(
            "update threads set rollout_path=?, archived=0, archived_at=NULL where id=?",
            (str(dest), rec["thread_id"]),
        )
conn.commit()
conn.close()
''',
        encoding="utf-8",
    )
    report(f"session_restore_script {restore}")


def prune_config(codex_home: Path, backup_root: Path, apply: bool, write_artifacts: bool) -> None:
    path = codex_home / "config.toml"
    if not path.exists():
        report("config_prune_candidates 0")
        return
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    out: list[str] = []
    removed: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = PROJECT_HEADER_RE.match(line)
        if not match:
            out.append(line)
            i += 1
            continue
        project_path = match.group(2)
        block = [line]
        i += 1
        while i < len(lines) and not lines[i].startswith("["):
            block.append(lines[i])
            i += 1
        should_remove = bool(TEMP_PROJECT_RE.search(project_path)) or not Path(project_path).exists()
        if should_remove:
            removed.append(project_path)
        else:
            out.extend(block)

    if write_artifacts:
        (backup_root / "pruned-projects.txt").write_text(
            "\n".join(removed) + ("\n" if removed else ""),
            encoding="utf-8",
        )
    report(f"config_prune_candidates {len(removed)}")
    if apply and removed:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        report("config_pruned applied")


def move_stale_worktrees(codex_home: Path, backup_root: Path, days: int, stamp: str, apply: bool) -> None:
    root = codex_home / "worktrees"
    if not root.exists():
        report("worktree_candidates 0")
        return
    cutoff = time.time() - days * 24 * 60 * 60
    candidates = [path for path in root.iterdir() if path.is_dir() and path.stat().st_mtime < cutoff]
    total = sum(size_bytes(path) for path in candidates)
    report(f"worktree_candidates {len(candidates)}")
    report(f"worktree_candidate_gb {gb(total)}")
    if not apply or not candidates:
        return
    archive_root = codex_home / "archived_worktrees" / f"keep-codex-fast-{stamp}"
    manifest = backup_root / "moved-worktrees.jsonl"
    archive_root.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", encoding="utf-8") as handle:
        for source in candidates:
            dest = archive_root / source.name
            item_size = size_bytes(source)
            shutil.move(str(source), str(dest))
            handle.write(json.dumps({"from": str(source), "to": str(dest), "bytes": item_size}) + "\n")
    report(f"worktree_archive_root {archive_root}")
    report(f"worktree_manifest {manifest}")


def rotate_logs(codex_home: Path, threshold_mb: int, stamp: str, apply: bool) -> None:
    files = [path for path in codex_home.glob("logs_2.sqlite*") if path.is_file()]
    total = sum(path.stat().st_size for path in files)
    report(f"logs_mb {mb(total)}")
    if total < threshold_mb * 1024 * 1024:
        report("logs_rotate skipped_below_threshold")
        return
    if apply and files:
        archive_root = codex_home / "archived_logs" / f"keep-codex-fast-{stamp}"
        archive_root.mkdir(parents=True, exist_ok=True)
        for path in files:
            shutil.move(str(path), str(archive_root / path.name))
        report(f"logs_archive_root {archive_root}")


def path_inside(path: Path, root: Path) -> Path | None:
    resolved = canonical_path(path)
    root_resolved = canonical_path(root)
    if resolved == root_resolved:
        return None
    try:
        resolved.relative_to(root_resolved)
    except (OSError, RuntimeError, ValueError):
        return None
    return resolved


def archived_thread_purge_candidates(
    conn: sqlite3.Connection,
    codex_home: Path,
    retention_days: int,
    details: bool,
) -> list[ArchivedThreadPurgeCandidate] | None:
    columns = table_columns(conn, "threads")
    required = {"id", "rollout_path", "archived_at"}
    if not required.issubset(columns):
        report("permanent_purge skipped_missing_threads_columns")
        return None

    archived_expr = "COALESCE(archived,0)=1" if "archived" in columns else "archived_at is not null"
    pinned_expr = "COALESCE(is_pinned,0)=0" if "is_pinned" in columns else "1"
    cutoff = int(time.time()) - retention_days * 24 * 60 * 60
    rows = conn.execute(
        f"select id, rollout_path, archived_at from threads "
        f"where {archived_expr} and {pinned_expr} and archived_at < ?",
        (cutoff,),
    ).fetchall()
    archive_root = codex_home / "archived_sessions"
    pinned = load_pinned(codex_home)
    candidates: list[ArchivedThreadPurgeCandidate] = []
    outside = 0
    missing = 0
    for thread_id, rollout_path, archived_at in rows:
        thread_id = str(thread_id)
        if thread_id in pinned or rollout_path is None:
            continue
        safe_path = path_inside(Path(str(rollout_path)), archive_root)
        if safe_path is None:
            outside += 1
            continue
        try:
            archived_timestamp = int(archived_at)
        except (TypeError, ValueError):
            continue
        item_bytes = size_bytes(safe_path)
        if not safe_path.exists():
            missing += 1
        candidates.append(
            ArchivedThreadPurgeCandidate(thread_id, safe_path, archived_timestamp, item_bytes)
        )

    total = sum(item.bytes for item in candidates)
    report(f"permanent_purge_retention_days {retention_days}")
    report(f"permanent_purge_candidates {len(candidates)}")
    report(f"permanent_purge_candidate_gb {gb(total)}")
    report(f"permanent_purge_missing_rollouts {missing}")
    report(f"permanent_purge_outside_archive {outside}")
    for index, item in enumerate(candidates[:10], start=1):
        if details:
            report(
                f"permanent_purge_candidate_{index:03d} "
                f"thread_id={item.thread_id} bytes={item.bytes}"
            )
        else:
            report(f"permanent_purge_candidate_{index:03d} bytes={item.bytes}")
    return candidates


def delete_archived_thread_rows(
    conn: sqlite3.Connection,
    candidates: list[ArchivedThreadPurgeCandidate],
    archive_root: Path,
    cutoff: int,
) -> set[str]:
    if not candidates:
        return set()
    columns = table_columns(conn, "threads")
    archived_expr = "COALESCE(archived,0)=1" if "archived" in columns else "archived_at is not null"
    pinned_expr = "COALESCE(is_pinned,0)=0" if "is_pinned" in columns else "1"
    root_prefix = str(canonical_path(archive_root)) + os.sep
    valid_ids: list[str] = []
    for item in candidates:
        row = conn.execute(
            f"select 1 from threads where id=? and {archived_expr} and {pinned_expr} "
            "and archived_at < ? and rollout_path like ?",
            (item.thread_id, cutoff, root_prefix + "%"),
        ).fetchone()
        if row:
            valid_ids.append(item.thread_id)
    if not valid_ids:
        return set()

    conn.execute("pragma foreign_keys=on")
    conn.execute("begin immediate")
    try:
        edge_columns = table_columns(conn, "thread_spawn_edges")
        if {"parent_thread_id", "child_thread_id"}.issubset(edge_columns):
            for thread_id in valid_ids:
                conn.execute(
                    "delete from thread_spawn_edges "
                    "where parent_thread_id=? or child_thread_id=?",
                    (thread_id, thread_id),
                )
        deleted_ids: set[str] = set()
        for thread_id in valid_ids:
            cursor = conn.execute("delete from threads where id=?", (thread_id,))
            if cursor.rowcount > 0:
                deleted_ids.add(thread_id)
        conn.commit()
        return deleted_ids
    except Exception:
        conn.rollback()
        raise


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def prune_empty_directories(root: Path) -> int:
    if not root.exists():
        return 0
    removed = 0
    paths = sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True)
    for path in paths:
        if not path.is_dir() or path.is_symlink():
            continue
        try:
            path.rmdir()
        except OSError:
            continue
        removed += 1
    return removed


def purge_archived_state(
    conn: sqlite3.Connection,
    codex_home: Path,
    backup_root: Path,
    *,
    retention_days: int,
    details: bool,
) -> dict[str, object]:
    candidates = archived_thread_purge_candidates(conn, codex_home, retention_days, details)
    if candidates is None:
        return {"ready": False, "deleted_rows": 0}

    archive_root = codex_home / "archived_sessions"
    cutoff = int(time.time()) - retention_days * 24 * 60 * 60
    manifest = backup_root / "permanent-purge.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for item in candidates:
            handle.write(
                json.dumps(
                    {
                        "thread_id": item.thread_id,
                        "archived_at": item.archived_at,
                        "rollout_path": str(item.rollout_path),
                        "bytes": item.bytes,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    deleted_ids = delete_archived_thread_rows(conn, candidates, archive_root, cutoff)
    deleted_rows = len(deleted_ids)
    removed_paths = 0
    removed_bytes = 0
    remove_errors = 0
    seen_paths: set[str] = set()
    for item in candidates:
        if item.thread_id not in deleted_ids:
            continue
        safe_path = path_inside(item.rollout_path, archive_root)
        if safe_path is None or str(safe_path) in seen_paths:
            continue
        seen_paths.add(str(safe_path))
        if not safe_path.exists() and not safe_path.is_symlink():
            continue
        try:
            remove_path(safe_path)
        except OSError:
            remove_errors += 1
            continue
        removed_paths += 1
        removed_bytes += item.bytes

    empty_dirs = prune_empty_directories(archive_root)
    summary = {
        "retention_days": retention_days,
        "candidate_rows": len(candidates),
        "deleted_rows": deleted_rows,
        "removed_rollout_paths": removed_paths,
        "removed_rollout_bytes": removed_bytes,
        "remove_errors": remove_errors,
        "empty_archive_directories_removed": empty_dirs,
        "manifest": str(manifest),
    }
    (backup_root / "permanent-purge-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report(f"permanent_purge_deleted_rows {deleted_rows}")
    report(f"permanent_purge_removed_rollouts {removed_paths}")
    report(f"permanent_purge_removed_gb {gb(removed_bytes)}")
    report(f"permanent_purge_remove_errors {remove_errors}")
    report(f"permanent_purge_manifest {manifest}")
    return {"ready": True, "deleted_rows": deleted_rows}


def purge_old_archive_containers(codex_home: Path, backup_root: Path, retention_days: int) -> None:
    cutoff = time.time() - retention_days * 24 * 60 * 60
    for relative, label in (("archived_worktrees", "worktrees"), ("archived_logs", "logs")):
        root = codex_home / relative
        if not root.exists():
            continue
        candidates = [
            path
            for path in root.iterdir()
            if path.name.startswith("keep-codex-fast-")
            and path.stat().st_mtime < cutoff
        ]
        total = sum(size_bytes(path) for path in candidates)
        report(f"permanent_{label}_archive_candidates {len(candidates)}")
        report(f"permanent_{label}_archive_candidate_gb {gb(total)}")
        for path in candidates:
            safe_path = path_inside(path, root)
            if safe_path is None:
                continue
            try:
                remove_path(safe_path)
            except OSError as exc:
                report(f"permanent_{label}_archive_remove_error {exc}")

    backup_parent = backup_root.parent
    if backup_parent.exists():
        candidates = [
            path
            for path in backup_parent.iterdir()
            if path != backup_root
            and path.name.startswith("keep-codex-fast-")
            and path.stat().st_mtime < cutoff
        ]
        total = sum(size_bytes(path) for path in candidates)
        report(f"permanent_backup_candidates {len(candidates)}")
        report(f"permanent_backup_candidate_gb {gb(total)}")
        for path in candidates:
            try:
                remove_path(path)
            except OSError as exc:
                report(f"permanent_backup_remove_error {exc}")


def compact_sqlite(conn: sqlite3.Connection, state_db: Path, deleted_rows: int) -> None:
    try:
        before_pages = int(conn.execute("pragma page_count").fetchone()[0])
        before_free = int(conn.execute("pragma freelist_count").fetchone()[0])
        auto_vacuum = int(conn.execute("pragma auto_vacuum").fetchone()[0])
        report(f"sqlite_compaction_before_pages {before_pages}")
        report(f"sqlite_compaction_before_freelist {before_free}")
        if auto_vacuum == 2:
            conn.execute("pragma incremental_vacuum")
        else:
            report(f"sqlite_incremental_vacuum_skipped auto_vacuum={auto_vacuum}")
        conn.execute("pragma wal_checkpoint(truncate)")
        after_incremental_free = int(conn.execute("pragma freelist_count").fetchone()[0])
        should_full_vacuum = before_pages > 0 and before_free / before_pages >= 0.05
        if should_full_vacuum:
            database_bytes = state_db.stat().st_size if state_db.exists() else 0
            free_bytes = shutil.disk_usage(state_db.parent).free
            if free_bytes < max(database_bytes * 2, 32 * 1024 * 1024):
                report("sqlite_vacuum_skipped low_disk_space")
            else:
                conn.execute("vacuum")
                report("sqlite_vacuum applied")
        elif deleted_rows:
            report("sqlite_vacuum skipped_below_fragmentation_threshold")
        conn.execute("pragma optimize")
        after_pages = int(conn.execute("pragma page_count").fetchone()[0])
        after_free = int(conn.execute("pragma freelist_count").fetchone()[0])
        report(f"sqlite_compaction_after_pages {after_pages}")
        report(f"sqlite_compaction_after_freelist {after_free}")
        report(f"sqlite_compaction_incremental_freelist {after_incremental_free}")
        conn.commit()
    except sqlite3.Error as exc:
        report(f"sqlite_compaction_failed {exc}")


def top_node_processes(details: bool) -> None:
    system = platform.system()
    report("top_node_processes")
    try:
        if system == "Windows":
            command = (
                "Get-Process node -ErrorAction SilentlyContinue | "
                "Sort-Object WorkingSet64 -Descending | Select-Object -First 10 "
                "Id,ProcessName,@{n='MB';e={[math]::Round($_.WorkingSet64/1MB,1)}},Path | "
                "ConvertTo-Json -Compress"
            )
            output = subprocess.check_output(["powershell", "-NoProfile", "-Command", command], text=True)
            if not output.strip():
                return
            data = json.loads(output)
            rows = data if isinstance(data, list) else [data]
            for row in rows:
                if details:
                    report(f"node_mb {row.get('MB')} pid={row.get('Id')} path={row.get('Path')}")
                else:
                    report(f"node_mb {row.get('MB')} process=node")
            return
        output = subprocess.check_output(["ps", "-axo", "pid=,rss=,comm=,args="], text=True)
        rows = []
        for line in output.splitlines():
            parts = line.strip().split(None, 3)
            if len(parts) >= 3 and "node" in parts[2].lower():
                rows.append((int(parts[1]), line.strip()))
        for rss, line in sorted(rows, reverse=True)[:10]:
            if details:
                report(f"node_mb {rss / 1024:.1f} {line}")
            else:
                report(f"node_mb {rss / 1024:.1f} process=node")
    except Exception as exc:
        report(f"node_process_report_skipped {exc}")


def verify_sizes(codex_home: Path) -> None:
    for rel in ["sessions", "archived_sessions", "worktrees", "archived_worktrees", "archived_logs"]:
        path = codex_home / rel
        if path.exists():
            report(f"size_{rel}_gb {gb(size_bytes(path))}")


def run(args: argparse.Namespace) -> int:
    codex_home = codex_home_from_args(args.codex_home)
    if not codex_home.exists():
        report(f"codex_home_missing {codex_home}")
        return 2

    stamp = now_stamp()
    backup_root = Path(args.backup_root).expanduser() if args.backup_root else documents_backup_root() / f"keep-codex-fast-{stamp}"
    backup_root = backup_root.resolve()

    running = codex_processes_running()
    if args.apply and running and args.wait_for_codex_exit:
        report("waiting_for_codex_exit")
        wait_for_codex_exit()
        running = []

    effective_apply = bool(args.apply and not running)
    effective_backup = bool(effective_apply or args.backup_only)
    requested_mode = "apply" if args.apply else "backup-only" if args.backup_only else "report"
    effective_mode = "apply" if effective_apply else "backup-only" if effective_backup else "report"
    if args.details:
        report(f"codex_home {codex_home}")
        if effective_backup:
            report(f"backup_root {backup_root}")
    elif effective_backup:
        report(f"backup_root {backup_root}")
    report(f"requested_mode {requested_mode}")
    report(f"effective_mode {effective_mode}")
    if effective_mode == "report":
        report("mode_safety read_only=true privacy=pseudonymous")
    elif effective_mode == "backup-only":
        report("mode_safety backup_only=true archives=false state_writes=false")
    elif args.permanent_purge_archived:
        report("mode_safety backup_first=true archive_and_permanent_purge=true")
    else:
        report("mode_safety backup_first=true archive_only=true permanent_delete=false")
    if args.apply and running:
        report("apply_skipped_codex_running")
        for index, proc in enumerate(running, start=1):
            if args.details:
                report(f"blocking_process {proc}")
            else:
                report(f"blocking_process codex_process_{index:03d}")

    if effective_backup:
        backup_metadata(codex_home, backup_root)

    state_db = codex_home / "state_5.sqlite"
    purge_result: dict[str, object] = {"ready": False, "deleted_rows": 0}
    if state_db.exists():
        conn = sqlite_connect(state_db, readonly=not effective_apply)
        conn.execute("pragma busy_timeout=10000")
        normalize_sqlite_paths(conn, effective_apply)
        report_thread_metadata_bloat(
            conn,
            title_limit=args.thread_title_limit,
            preview_limit=args.thread_preview_limit,
        )
        repair_delegation_thread_titles(
            conn,
            codex_home,
            backup_root,
            apply=effective_apply and args.repair_delegation_thread_titles,
            title_limit=args.thread_title_limit,
        )
        repair_thread_metadata_bloat(
            conn,
            codex_home,
            backup_root,
            apply=effective_apply and args.repair_thread_metadata_bloat,
            details=args.details,
            title_limit=args.thread_title_limit,
            preview_limit=args.thread_preview_limit,
        )
        candidates = active_session_candidates(conn, codex_home, args.archive_older_than_days)
        archive_sessions(conn, candidates, codex_home, backup_root, stamp, effective_apply, args.details)
        repair_electron_ui_state(
            conn,
            codex_home,
            backup_root,
            apply=effective_apply and args.repair_electron_ui_state,
        )
        if effective_apply:
            conn.commit()
            if args.permanent_purge_archived:
                purge_result = purge_archived_state(
                    conn,
                    codex_home,
                    backup_root,
                    retention_days=args.archive_retention_days,
                    details=args.details,
                )
            try:
                conn.execute("pragma wal_checkpoint(truncate)")
            except Exception as exc:
                report(f"wal_checkpoint_skipped {exc}")
            if args.vacuum_sqlite:
                compact_sqlite(conn, state_db, int(purge_result.get("deleted_rows", 0)))
            else:
                try:
                    conn.execute("pragma optimize")
                except Exception as exc:
                    report(f"sqlite_optimize_skipped {exc}")
        conn.close()
    else:
        report("state_db_missing")

    prune_config(codex_home, backup_root, effective_apply, effective_backup)
    move_stale_worktrees(codex_home, backup_root, args.worktree_older_than_days, stamp, effective_apply)
    rotate_logs(codex_home, args.rotate_logs_above_mb, stamp, effective_apply)
    archive_temp_plugin_state(
        codex_home,
        backup_root,
        apply=effective_apply and args.archive_temp_plugin_state,
    )
    if effective_apply and args.permanent_purge_archived and purge_result.get("ready"):
        purge_old_archive_containers(codex_home, backup_root, args.archive_retention_days)
    verify_sizes(codex_home)
    top_node_processes(args.details)
    report("done")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backup-first Codex local-state maintenance; permanent purge is explicit."
    )
    parser.add_argument("--apply", action="store_true", help="Apply maintenance actions. Default is report-only.")
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Create backups without applying maintenance actions. Default report mode writes no files.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Include raw thread IDs, titles, paths, and process paths in output.",
    )
    parser.add_argument("--wait-for-codex-exit", action="store_true", help="Wait until Codex exits before applying.")
    parser.add_argument("--codex-home", help="Override Codex home. Defaults to CODEX_HOME or ~/.codex.")
    parser.add_argument("--backup-root", help="Override backup output folder.")
    parser.add_argument("--archive-older-than-days", type=int, default=10)
    parser.add_argument(
        "--archive-retention-days",
        type=int,
        default=60,
        help="With --permanent-purge-archived, permanently remove archived state older than this many days.",
    )
    parser.add_argument("--worktree-older-than-days", type=int, default=7)
    parser.add_argument("--rotate-logs-above-mb", type=int, default=64)
    parser.add_argument(
        "--thread-title-limit",
        type=int,
        default=DEFAULT_TITLE_LIMIT,
        help="Title length threshold for metadata-bloat reporting and optional repair.",
    )
    parser.add_argument(
        "--thread-preview-limit",
        type=int,
        default=DEFAULT_PREVIEW_LIMIT,
        help="Preview length threshold for metadata-bloat reporting and optional repair.",
    )
    parser.add_argument(
        "--repair-delegation-thread-titles",
        action="store_true",
        help="With --apply, replace delegation-envelope display names with bounded source-thread names.",
    )
    parser.add_argument(
        "--repair-thread-metadata-bloat",
        action="store_true",
        help="With --apply, trim oversized thread title/preview metadata. Default --apply only reports candidates.",
    )
    parser.add_argument(
        "--repair-electron-ui-state",
        action="store_true",
        help="With --apply, prune archived/orphaned thread entries from rebuildable Electron UI indexes.",
    )
    parser.add_argument(
        "--archive-temp-plugin-state",
        action="store_true",
        help="With --apply, move disposable Codex temporary plugin checkouts into the rollback bundle.",
    )
    parser.add_argument(
        "--permanent-purge-archived",
        action="store_true",
        help="With --apply, permanently delete old archived sessions and maintenance archives after backup.",
    )
    parser.add_argument(
        "--vacuum-sqlite",
        action="store_true",
        help="With --apply, compact SQLite incrementally and run VACUUM only above the fragmentation threshold.",
    )
    args = parser.parse_args(argv)
    if args.apply and args.backup_only:
        parser.error("--apply and --backup-only cannot be used together")
    if args.permanent_purge_archived and not args.apply:
        parser.error("--permanent-purge-archived requires --apply")
    if args.vacuum_sqlite and not args.apply:
        parser.error("--vacuum-sqlite requires --apply")
    if args.archive_retention_days < 7:
        parser.error("--archive-retention-days must be at least 7")
    if args.thread_title_limit < 20:
        parser.error("--thread-title-limit must be at least 20")
    if args.thread_preview_limit < args.thread_title_limit:
        parser.error("--thread-preview-limit must be greater than or equal to --thread-title-limit")
    return args


if __name__ == "__main__":
    raise SystemExit(run(parse_args(sys.argv[1:])))
