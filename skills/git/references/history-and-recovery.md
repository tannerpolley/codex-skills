# History and recovery

## Prepare and commit

1. Inspect `git status --short --branch`, `git diff`, and `git diff --staged`.
2. Stage explicit files or hunks with `git add -- <paths>` or `git add -p -- <paths>`.
3. Re-read the staged patch. A commit should represent one coherent reason for change and preserve tests or docs required for that change to make sense.
4. Commit only when authorized, then verify status and `git show --stat --oneline HEAD`.

Do not use `git commit -a` when unreviewed tracked changes are present. Never stage secrets, local credentials, build artifacts, or unrelated user changes.

## Choose the least destructive undo

| Intent | Command | Boundary |
|---|---|---|
| Unstage, keep working copy | `git restore --staged -- <paths>` | Index only |
| Reverse a shared commit | `git revert <commit>` | Adds a new commit |
| Fix the last unshared commit | `git commit --amend` | Replaces the commit |
| Reorder/squash unshared commits | `git rebase -i <upstream>` | Rewrites a range |
| Locate a lost local tip | `git reflog` | Read-only discovery |
| Preserve a recovered tip | `git branch rescue/<name> <oid>` | Adds a ref |

`git restore --worktree`, `git reset --hard`, and `git clean -f` can destroy uncommitted data. Use them only with explicit authority after showing the exact affected paths or refs. Prefer `git revert` for history collaborators may already have.

## Branches, worktrees, and synchronization

- Detect detached HEAD and linked-worktree state before creating or switching branches.
- Use `git switch -c <branch>` for a new branch and `git worktree list --porcelain` before adding or removing worktrees.
- Use `git fetch --prune <remote>` to refresh remote-tracking refs only when network access and remote mutation boundaries permit. Fetch does not integrate changes; `git pull` fetches and then merges or rebases.
- Do not select merge versus rebase without repository policy or user intent. Do not rewrite commits already shared unless collaborators explicitly coordinate it.

## Conflicts and interrupted operations

Inspect the active operation and unresolved paths:

```bash
git status
git diff --name-only --diff-filter=U
```

Resolve each file intentionally, stage exact resolved paths, run relevant tests, then use the operation-specific `--continue`. Use the matching `--abort` when the user wants to return to the pre-operation state. Never resolve a conflict by taking one side wholesale unless the content and intent justify it.

## Merge and closeout

For a local-only merge, honor configured guarded hooks. Inspect `core.hooksPath`, the relevant hook, exact branch tips, and worktree occupancy before mutation. Preserve protected, occupied, unmerged, or unrelated branches.

For GitHub closeout, first use the `github` skill to establish the exact merged PR, head, merge commit, remote default branch, authority, and worktree provenance. Then:

1. Fetch and prune the exact remote; verify the merged head's remote-tracking ref is absent.
2. Fast-forward the clean canonical default-branch checkout when available. Preserve dirty or unique work rather than auto-stashing or resetting it.
3. Detach a retained clean feature worktree at the verified integrated commit before deleting the exact merged local head through the repository's guarded workflow.
4. Apply the GitHub preference reference's worktree disposition. Do not infer disposable ownership from a path or ask again when authorized disposition is already established.
5. Run the global cleanup audit and inspect final refs, worktrees, and status.

An already-absent target is satisfied; continue the remaining closeout. An ordinary PR closeout does not sweep unrelated gone branches. If a configured wrapper such as `git-clean-gone` is required, verify it is installed; do not replace it with an unguarded force-deletion loop.

## Sources

- https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository
- https://git-scm.com/book/en/v2/Git-Basics-Undoing-Things
- https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History
- https://git-scm.com/docs/git-restore
- https://git-scm.com/docs/git-reset
- https://git-scm.com/docs/git-revert
- https://git-scm.com/docs/git-reflog
- https://git-scm.com/docs/git-worktree
