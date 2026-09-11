---
name: git
description: Inspect or change local Git state, commits, branches, worktrees, synchronization, conflicts, and recovery. Use github for hosted objects.
---

# Git

Use the current attached checkout. For a write, inspect the root, branch, status, and relevant staged and unstaged changes; preserve unrelated state. Before material implementation, reuse the task feature branch or create one when needed. A read-only agent does not need a worktree; honor the user's explicit checkout/isolation choice.

Use the smallest native Git command that answers the question. Keep implementation, review, commit, push, and integration in the task checkout. Scope mutations to exact paths or refs. Reading local status does not require remote discovery.

Read [diffs and attributes](references/diffs-and-attributes.md) for unresolved tracking or presentation decisions. Read [history and recovery](references/history-and-recovery.md) for commits, synchronization, undo, conflicts, local merges, or post-merge closeout. Inspect both index and working-tree changes before committing.

Use `github` for hosted objects, delivery preferences, and merge authority. Complete the exact merged PR's state-driven local closeout; preserve unrelated branches, occupied worktrees, dirty state, and unique commits.
