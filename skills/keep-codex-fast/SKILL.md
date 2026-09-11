---
name: keep-codex-fast
description: Audit and, only with explicit authorization, maintain local Codex state for performance or storage issues. Use for a reported slowdown, oversized state, or requested maintenance; report-only is the default.
---

# Keep Codex Fast

Run the bundled script in report mode first and summarize observed local state. Do not infer that age or size alone makes active chats disposable. Preserve credentials, identity, sessions, SQLite, plugins, skills, hooks, active or pinned threads, and requested artifacts.

Use `python scripts/keep_codex_fast.py` from this skill directory for a read-only report. Before any backup, apply, repair, purge, or scheduling operation, read [maintenance modes](references/maintenance-modes.md). Apply requires explicit scope, all Codex writers stopped, and a private backup with rollback manifests. Credential copying is outside ordinary maintenance. Preserve important tasks and their needed handoffs.

The normal apply bundle backs up metadata, archives eligible old non-pinned sessions, normalizes known Windows paths, prunes missing project blocks, moves stale worktrees, and rotates eligible logs. It does not kill processes, permanently delete archived state, or silently repair thread metadata, Electron indexes, or temporary plugin state. Explain these side effects before applying.

Use targeted options only when explicitly selected: --wait-for-codex-exit, --archive-older-than-days N, --worktree-older-than-days N, --repair-thread-metadata-bloat, --repair-delegation-thread-titles, --repair-electron-ui-state, and --archive-temp-plugin-state. Hard purge requires explicit --permanent-purge-archived --archive-retention-days N; --vacuum-sqlite is a separate explicit choice.

Create reminders only when asked. Codex automations are report-only; separately authorized machine scheduling follows the safeguards in the reference. Do not run maintenance while this skill is only being reviewed.
