# Maintenance modes

Read this reference only for the selected maintenance operation. Resolve the bundled script relative to this skill directory. The script is an existing local maintenance tool, not proof that all its modes are authorized.

## Report and scope

Run `python scripts/keep_codex_fast.py` first. Report mode must not write files, create backups, move folders, or change Codex state. Summarize sizes and pseudonymous candidates; use `--details` only when the user requests identifying details. Do not print credentials, prompt contents, raw database contents, or large logs.

Age and size identify candidates, not disposal authority. Establish the requested operations and targets from the report. Do not prune a real repository's config entry merely because a drive or mount is temporarily unavailable.

## Shared mutation requirements

- Apply only the user-authorized operations. The normal `--apply` bundle performs several actions together; use it only when the entire candidate bundle is authorized.
- All Codex Desktop, app-server, and CLI writers must be stopped before applying changes. Use `--wait-for-codex-exit` only when waiting for them to exit is authorized; do not kill them automatically.
- Create the script's private pre-run backup and restore manifests before mutation. Preserve memory, skills, durable plugin and automation data; exclude app-managed plugin cache and staging/scratch directories from durable backups. Never copy credential or auth files unless that exact operation is explicitly requested.
- Backups may contain private titles and message previews. Keep them local and private; do not publish or upload them as diagnostic evidence.
- Preserve current, pinned, and explicitly needed tasks. Before archiving an important active task, confirm a usable handoff exists or the user has said one is not needed. Use [the handoff template](handoff-template.md) only when a handoff is needed.
- Verify results with a subsequent report and distinguish skipped application from completed maintenance. Preserve the rollback bundle and restore instructions.

## Backup only and normal apply

`--backup-only` creates the requested private backup without archiving or modifying live state. It is separate from the report and apply modes.

Normal `--apply` backs up metadata, archives eligible old non-pinned sessions, moves eligible stale worktrees, rotates oversized logs, normalizes supported malformed Windows paths, and prunes verified obsolete project entries. Choose `--archive-older-than-days N` and `--worktree-older-than-days N` from the authorized scope rather than treating the script's defaults as a retention preference. It does not permanently purge state, kill processes, or enable optional repairs.

## Targeted repairs

Each flag requires the corresponding repair to be selected explicitly, the same offline/backup safeguards, and a report showing the relevant problem.

| Flag | Bounded effect |
|---|---|
| `--repair-delegation-thread-titles` | Repair delegation display names in thread metadata and session index. |
| `--repair-thread-metadata-bloat` | Shorten oversized display title/preview metadata; retain old values in the repair manifest and preserve rollout transcripts. |
| `--repair-electron-ui-state` | Prune rebuildable archived/orphaned UI indexes, preserving active-task entries and global prompt history. |
| `--archive-temp-plugin-state` | Move known temporary plugin/marketplace checkout entries under Codex's `.tmp` into the rollback bundle. Ordinary plugin-cache maintenance remains outside scope. |

Inspect the selected script's actual options and manifest before use; these are repairs of specific metadata, not permission to rewrite session history or arbitrary runtime files.

## Permanent purge and SQLite compaction

Permanent purge requires explicit authorization, a stated retention period, private pre-run backup, offline writer guard, and a purge manifest. Use `--apply --permanent-purge-archived --archive-retention-days N` only for the confirmed archived scope.

Eligible scope is limited to archived thread rows whose rollout paths are inside `archived_sessions`, their matching archived rollout files, and eligible old `keep-codex-fast-*` worktree/log archives and maintenance backups. Preserve active, pinned, current, credential, configuration, skill, plugin, and unknown-provenance state. Do not expand a named archived-state purge to other files.

`--vacuum-sqlite` is an additional explicit choice. It checkpoints and compacts the existing SQLite database without resetting the schema. Full vacuum requires the script's fragmentation and free-space checks. The backup matters because removed rows cannot be recovered from the live database.

## Scheduling

Offer no unsolicited reminders. If the user requests a Codex automation, keep it report-only. A separately authorized machine scheduler may run the specified soft or hard maintenance only with an explicit cadence and retention scope and the same offline, backup, and exact-target safeguards.
