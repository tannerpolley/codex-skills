#!/usr/bin/env python3
"""Smoke tests for keep-codex-fast using a fake Codex home."""

from __future__ import annotations

import argparse
import contextlib
import io
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "keep_codex_fast.py"


def load_module():
    spec = importlib.util.spec_from_file_location("keep_codex_fast", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["keep_codex_fast"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.real_codex_processes_running = module.codex_processes_running
    module.codex_processes_running = lambda: []
    module.top_node_processes = lambda details=False: module.report("top_node_processes skipped_in_smoke")
    return module


def assert_plain_codex_process_detection(module) -> None:
    original_system = module.platform.system
    original_check_output = module.subprocess.check_output
    try:
        module.platform.system = lambda: "Linux"
        module.subprocess.check_output = lambda *args, **kwargs: (
            "123 codex /usr/bin/codex\n"
            "124 python3 python3 scripts/keep_codex_fast.py --apply\n"
        )
        running = module.real_codex_processes_running()
    finally:
        module.platform.system = original_system
        module.subprocess.check_output = original_check_output
    assert len(running) == 1, "plain Codex writers must block live-state maintenance"


def make_fake_home(root: Path) -> dict[str, Path]:
    codex_home = root / ".codex"
    sessions = codex_home / "sessions" / "2026" / "01" / "01"
    sessions.mkdir(parents=True)
    rollout = sessions / "rollout-2026-01-01T00-00-00-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jsonl"
    rollout.write_text('{"type":"test"}\n', encoding="utf-8")
    old_time = time.time() - 30 * 86400
    os.utime(rollout, (old_time, old_time))

    source_thread_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    delegated_thread_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    orphan_thread_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    global_state = {
        "pinned-thread-ids": [],
        "projectless-thread-ids": [source_thread_id, "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", orphan_thread_id],
        "thread-project-assignments": {
            source_thread_id: "active-project",
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": "archived-project",
            orphan_thread_id: "orphan-project",
        },
        "thread-workspace-root-hints": {
            source_thread_id: str(root),
            orphan_thread_id: str(root / "missing"),
        },
        "thread-projectless-output-directories": {
            source_thread_id: str(root / "output"),
            orphan_thread_id: str(root / "old-output"),
        },
        "electron-persisted-atom-state": {
            "thread-descriptions-v1": {
                source_thread_id: {"label": "active"},
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": {"label": "archived"},
                orphan_thread_id: {"label": "orphan"},
            },
            "unread-thread-ids-by-host-v1": {
                "local": [source_thread_id, "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", orphan_thread_id]
            },
            "prompt-history": {
                "global": ["keep"],
                source_thread_id: ["active"],
                orphan_thread_id: ["orphan"],
            },
            "heartbeat-thread-permissions-by-id": {
                source_thread_id: {"permission": "keep"},
                orphan_thread_id: {"permission": "drop"},
            },
        },
    }
    (codex_home / ".codex-global-state.json").write_text(
        json.dumps(global_state), encoding="utf-8"
    )
    (codex_home / "config.toml").write_text(
        '[projects."C:\\\\DefinitelyMissingKeepCodexFast"]\ntrust_level = "trusted"\n',
        encoding="utf-8",
    )

    plugin_data = codex_home / "plugins" / "data"
    plugin_data.mkdir(parents=True)
    (plugin_data / "registry.json").write_text("{}\n", encoding="utf-8")
    plugin_cache = codex_home / "plugins" / "cache"
    plugin_cache.mkdir()
    try:
        (plugin_cache / "latest").symlink_to("missing-version", target_is_directory=True)
    except OSError:
        (plugin_cache / "latest").mkdir()
    plugin_staging = codex_home / "plugins" / ".remote-plugin-install-staging"
    plugin_staging.mkdir()
    (plugin_staging / "temporary").write_text("temporary\n", encoding="utf-8")
    plugin_appserver = codex_home / "plugins" / ".plugin-appserver"
    plugin_appserver.mkdir()
    (plugin_appserver / "codex").write_text("temporary\n", encoding="utf-8")
    nested_plugin_cache = codex_home / "plugins" / "user-plugin" / "cache"
    nested_plugin_cache.mkdir(parents=True)
    (nested_plugin_cache / "keep.txt").write_text("durable\n", encoding="utf-8")

    temp_plugins = codex_home / ".tmp" / "plugins"
    temp_plugins.mkdir(parents=True)
    (temp_plugins / "checkout.txt").write_text("disposable plugin checkout\n", encoding="utf-8")
    temp_marketplaces = codex_home / ".tmp" / "marketplaces"
    temp_marketplaces.mkdir(parents=True)
    (temp_marketplaces / "staging.txt").write_text("disposable marketplace staging\n", encoding="utf-8")
    (codex_home / ".tmp" / "plugins.sha").write_text("test-sha\n", encoding="utf-8")
    (codex_home / ".tmp" / "plugins.sync.lock").write_text("", encoding="utf-8")

    worktree = codex_home / "worktrees" / "oldtree"
    worktree.mkdir(parents=True)
    (worktree / "file.txt").write_text("x", encoding="utf-8")
    os.utime(worktree, (old_time, old_time))

    log_file = codex_home / "logs_2.sqlite"
    log_file.write_text("log", encoding="utf-8")

    state_db = codex_home / "state_5.sqlite"
    conn = sqlite3.connect(state_db)
    conn.execute(
        "create table threads (id text primary key, title text, first_user_message text, rollout_path text, cwd text, updated_at integer, archived_at integer, archived integer)"
    )
    long_title = "Title " + ("x" * 300)
    long_preview = "Preview " + ("y" * 600)
    conn.execute(
        "insert into threads values (?,?,?,?,?,?,?,?)",
        (
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            long_title,
            long_preview,
            str(rollout),
            r"\\?\C:\DefinitelyMissingKeepCodexFast",
            int(old_time),
            None,
            0,
        ),
    )
    delegated_message = (
        "<codex_delegation><source_thread_id>"
        + source_thread_id
        + "</source_thread_id><input>Investigate the delegated task.</input></codex_delegation>"
    )
    recent_time = int(time.time())
    conn.execute(
        "insert into threads values (?,?,?,?,?,?,?,?)",
        (
            source_thread_id,
            "Human source thread",
            "Human source preview",
            str(sessions / "source.jsonl"),
            str(root),
            recent_time,
            None,
            0,
        ),
    )
    conn.execute(
        "insert into threads values (?,?,?,?,?,?,?,?)",
        (
            delegated_thread_id,
            delegated_message,
            delegated_message,
            str(sessions / "delegated.jsonl"),
            str(root),
            recent_time,
            None,
            0,
        ),
    )
    conn.commit()
    conn.close()

    session_index = codex_home / "session_index.jsonl"
    session_index.write_text(
        "\n".join(
            [
                '{"id":"' + source_thread_id + '","thread_name":"Human source thread"}',
                json.dumps({"id": delegated_thread_id, "thread_name": delegated_message}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "codex_home": codex_home,
        "rollout": rollout,
        "worktree": worktree,
        "log_file": log_file,
        "state_db": state_db,
        "delegated_thread_id": delegated_thread_id,
        "source_thread_id": source_thread_id,
        "temp_plugins": temp_plugins,
    }


def assert_report_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        backup = Path(td) / "backup-report"
        args = argparse.Namespace(
            apply=False,
            backup_only=False,
            details=False,
            wait_for_codex_exit=False,
            codex_home=str(paths["codex_home"]),
            backup_root=str(backup),
            archive_older_than_days=10,
            worktree_older_than_days=7,
            rotate_logs_above_mb=0,
            thread_title_limit=120,
            thread_preview_limit=240,
            repair_thread_metadata_bloat=False,
            repair_delegation_thread_titles=False,
            repair_electron_ui_state=False,
            archive_temp_plugin_state=False,
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert module.run(args) == 0
        text = output.getvalue()
        assert paths["rollout"].exists(), "report mode must not move sessions"
        assert paths["worktree"].exists(), "report mode must not move worktrees"
        assert paths["log_file"].exists(), "report mode must not rotate logs"
        assert not backup.exists(), "report mode must not create backup artifacts"
        assert "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" not in text
        assert str(paths["codex_home"]) not in text
        conn = sqlite3.connect(paths["state_db"])
        title, preview = conn.execute(
            "select title, first_user_message from threads where id=?",
            ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
        ).fetchone()
        conn.close()
        assert len(title) > 120, "report mode must not trim titles"
        assert len(preview) > 240, "report mode must not trim previews"


def assert_backup_only_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        backup = Path(td) / "backup-only"
        args = argparse.Namespace(
            apply=False,
            backup_only=True,
            details=False,
            wait_for_codex_exit=False,
            codex_home=str(paths["codex_home"]),
            backup_root=str(backup),
            archive_older_than_days=10,
            worktree_older_than_days=7,
            rotate_logs_above_mb=0,
            thread_title_limit=120,
            thread_preview_limit=240,
            repair_thread_metadata_bloat=False,
            repair_delegation_thread_titles=False,
            repair_electron_ui_state=False,
            archive_temp_plugin_state=False,
        )
        assert module.run(args) == 0
        assert paths["rollout"].exists(), "backup-only mode must not move sessions"
        assert paths["worktree"].exists(), "backup-only mode must not move worktrees"
        assert paths["log_file"].exists(), "backup-only mode must not rotate logs"
        assert (backup / "state_5.sqlite").exists()
        assert (backup / "config.toml").exists()
        assert (backup / "plugins" / "data" / "registry.json").exists()
        assert not (backup / "plugins" / "cache").exists()
        assert not (backup / "plugins" / ".remote-plugin-install-staging").exists()
        assert not (backup / "plugins" / ".plugin-appserver").exists()
        assert (backup / "plugins" / "user-plugin" / "cache" / "keep.txt").exists()
        assert not (backup / "moved-sessions.jsonl").exists()
        conn = sqlite3.connect(paths["state_db"])
        title, preview = conn.execute(
            "select title, first_user_message from threads where id=?",
            ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
        ).fetchone()
        conn.close()
        assert len(title) > 120, "backup-only mode must not trim titles"
        assert len(preview) > 240, "backup-only mode must not trim previews"


def assert_session_alias_detection(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        real_root = root / "real"
        alias_root = root / "alias"
        real_root.mkdir()
        try:
            alias_root.symlink_to(real_root, target_is_directory=True)
        except OSError:
            return

        paths = make_fake_home(real_root)
        alias_home = alias_root / ".codex"
        conn = module.sqlite_connect(alias_home / "state_5.sqlite", readonly=True)
        try:
            candidates = module.active_session_candidates(conn, alias_home, 10)
        finally:
            conn.close()
        assert len(candidates) == 1


def assert_apply_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        backup = Path(td) / "backup-apply"
        args = argparse.Namespace(
            apply=True,
            backup_only=False,
            details=False,
            wait_for_codex_exit=False,
            codex_home=str(paths["codex_home"]),
            backup_root=str(backup),
            archive_older_than_days=10,
            worktree_older_than_days=7,
            rotate_logs_above_mb=0,
            thread_title_limit=120,
            thread_preview_limit=240,
            repair_thread_metadata_bloat=True,
            repair_delegation_thread_titles=False,
            repair_electron_ui_state=True,
            archive_temp_plugin_state=True,
        )
        assert module.run(args) == 0

        conn = sqlite3.connect(paths["state_db"])
        archived, archived_at, rollout_path, cwd, title, preview = conn.execute(
            "select archived, archived_at, rollout_path, cwd, title, first_user_message from threads where id=?",
            ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
        ).fetchone()
        conn.close()

        assert archived == 1
        assert archived_at is not None
        assert "archived_sessions" in rollout_path
        assert cwd == r"C:\DefinitelyMissingKeepCodexFast"
        assert len(title) <= 120
        assert len(preview) <= 240
        conn = sqlite3.connect(paths["state_db"])
        delegation_title = conn.execute(
            "select title from threads where id=?",
            (paths["delegated_thread_id"],),
        ).fetchone()[0]
        conn.close()
        assert delegation_title.endswith("</codex_delegation>"), (
            "generic metadata repair must leave delegation envelopes for the explicit repair"
        )
        assert not paths["rollout"].exists()
        assert not paths["worktree"].exists()
        assert not paths["log_file"].exists()
        assert "DefinitelyMissingKeepCodexFast" not in (paths["codex_home"] / "config.toml").read_text(
            encoding="utf-8"
        )
        assert (backup / "restore-sessions.py").exists()
        assert (backup / "restore-thread-metadata.py").exists()
        assert (backup / "moved-sessions.jsonl").exists()
        assert (backup / "thread-metadata-repairs.jsonl").exists()
        assert (backup / "moved-worktrees.jsonl").exists()
        assert (backup / "electron-ui-state-repair.json").exists()
        assert (backup / "restore-electron-ui-state.py").exists()
        assert (backup / "archived-temp-plugin-state.jsonl").exists()
        assert (backup / "restore-temp-plugin-state.py").exists()
        assert not paths["temp_plugins"].exists()
        repaired_state = json.loads(
            (paths["codex_home"] / ".codex-global-state.json").read_text(encoding="utf-8")
        )
        descriptions = repaired_state["electron-persisted-atom-state"]["thread-descriptions-v1"]
        assert set(descriptions) == {paths["source_thread_id"]}
        assert repaired_state["electron-persisted-atom-state"]["prompt-history"]["global"] == ["keep"]
        session_index = paths["codex_home"] / "session_index.jsonl"
        assert session_index.exists()
        assert "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" in session_index.read_text(encoding="utf-8")


def assert_normal_apply_does_not_repair_thread_metadata(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        backup = Path(td) / "backup-normal-apply"
        args = argparse.Namespace(
            apply=True,
            backup_only=False,
            details=False,
            wait_for_codex_exit=False,
            codex_home=str(paths["codex_home"]),
            backup_root=str(backup),
            archive_older_than_days=10,
            worktree_older_than_days=7,
            rotate_logs_above_mb=64,
            thread_title_limit=120,
            thread_preview_limit=240,
            repair_thread_metadata_bloat=False,
            repair_delegation_thread_titles=False,
            repair_electron_ui_state=False,
            archive_temp_plugin_state=False,
        )
        assert module.run(args) == 0

        conn = sqlite3.connect(paths["state_db"])
        title, preview = conn.execute(
            "select title, first_user_message from threads where id=?",
            ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
        ).fetchone()
        conn.close()

        assert len(title) > 120, "normal apply must not trim titles without explicit repair flag"
        assert len(preview) > 240, "normal apply must not trim previews without explicit repair flag"
        assert not (backup / "thread-metadata-repairs.jsonl").exists()
        assert not (backup / "restore-thread-metadata.py").exists()
        assert paths["temp_plugins"].exists()


def assert_delegation_thread_title_repair(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        backup = Path(td) / "backup-delegation-repair"
        args = argparse.Namespace(
            apply=True,
            backup_only=False,
            details=False,
            wait_for_codex_exit=False,
            codex_home=str(paths["codex_home"]),
            backup_root=str(backup),
            archive_older_than_days=1000,
            worktree_older_than_days=1000,
            rotate_logs_above_mb=64,
            thread_title_limit=120,
            thread_preview_limit=240,
            repair_thread_metadata_bloat=False,
            repair_delegation_thread_titles=True,
            repair_electron_ui_state=False,
            archive_temp_plugin_state=False,
        )
        assert module.run(args) == 0

        conn = sqlite3.connect(paths["state_db"])
        title, preview = conn.execute(
            "select title, first_user_message from threads where id=?",
            (paths["delegated_thread_id"],),
        ).fetchone()
        conn.close()
        assert title == "Delegated: Human source thread"
        assert preview == "Delegated: Human source thread"

        latest_names = {}
        for line in (paths["codex_home"] / "session_index.jsonl").read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            latest_names[record["id"]] = record["thread_name"]
        assert latest_names[paths["delegated_thread_id"]] == "Delegated: Human source thread"
        assert (backup / "delegation-thread-title-repairs.jsonl").exists()
        assert (backup / "restore-delegation-thread-titles.py").exists()


def main() -> int:
    module = load_module()
    assert_plain_codex_process_detection(module)
    assert_report_mode(module)
    assert_backup_only_mode(module)
    assert_session_alias_detection(module)
    assert_normal_apply_does_not_repair_thread_metadata(module)
    assert_delegation_thread_title_repair(module)
    assert_apply_mode(module)
    print("smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
