# History and recovery

## Prepare and commit

1. Inspect `git status --short --branch`, `git diff`, and `git diff --staged`.
2. Stage explicit files or hunks with `git add -- <paths>` or `git add -p -- <paths>`.
3. Re-read the staged patch. A commit should represent one coherent reason for change and preserve tests or docs required for that change to make sense.
4. Make focused local commits within authorized implementation, then verify status and `git show --stat --oneline HEAD`. A commit grants no remote publication authority.

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

For GitHub closeout, first use the `github` skill to verify the exact PR is merged and establish its repository/remote, reviewed head/ref, merge identity/method, target branch, issue closure, authority, and worktree provenance. Remote branch disappearance alone is not merge evidence. Then:

1. Before pruning upstream metadata, map local branches to that exact remote head/PR using upstream configuration, task provenance, and commits. Include differently named related branches; neither a similar name nor a `gone` marker establishes association.
2. Verify each candidate has no additional unmerged work. For squash/rebase merges, use verified PR mapping and integration evidence; ancestry alone may be insufficient. Preserve uncertainty rather than force-delete after `git branch -d` refuses.
3. Require the exact remote feature head to be absent, deleting it through GitHub only when necessary and authorized. Fetch/prune the relevant remote-tracking state and verify absence; pruning does not delete local branches.
4. Return the saved task checkout to local `main` and fast-forward it safely. Preserve unrelated dirty state and unique commits; no automatic stash, hard reset, default-branch rename, or forced takeover of occupied `main`. If `main` is invalid, divergent, or occupied, report the exact blocker and use native input for an unresolved material choice. A detached saved checkout does not meet this endpoint.
5. Remove the identified integrated feature branches after switching off them, through repository-guarded mechanics. Apply the GitHub reference's worktree disposition; preserve occupied user/unknown worktrees and remove only obsolete metadata for exact disposable worktrees. Do not infer provenance from paths or repeat established approvals.
6. Verify integration, relevant local/remote refs, worktrees, saved-checkout branch/status, and issue closure. Report safety blockers without destroying unrelated work.

An already-absent target is satisfied; continue the remaining closeout. An ordinary PR closeout does not sweep unrelated gone branches. If a configured wrapper such as `git-clean-gone` is required, verify it is installed and can stay within these exact candidates; do not use a broad sweep or unguarded force-deletion loop.

## Sources

- https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository
- https://git-scm.com/book/en/v2/Git-Basics-Undoing-Things
- https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History
- https://git-scm.com/docs/git-restore
- https://git-scm.com/docs/git-reset
- https://git-scm.com/docs/git-revert
- https://git-scm.com/docs/git-reflog
- https://git-scm.com/docs/git-worktree
