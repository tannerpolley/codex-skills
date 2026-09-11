# GitHub profile preferences

These preferences are standing workflow authority for the authenticated `tannerpolley` account. They do not authorize changes to unrelated repositories or user work.

## Scope

- Apply repository defaults only to active, non-archived repositories owned by `tannerpolley` when a current authorized workflow touches that repository.
- Treat current tasks, recent commits or pull requests, and active canonical checkouts as evidence of activity. Do not sweep dormant repositories, old mirrors, archived repositories, or untouched forks.
- Preserve organization and third-party repository policy unless the user explicitly includes it.

## Delivery

- A completed implementation request includes repository-contract validation, a focused commit, push, and a draft pull request.
- Merge requires an explicit request unless the original task already includes merge authority.
- Use an exact closing keyword when the PR fully resolves an issue and verify closure after merge. Use non-closing references for partial work.

## Repository defaults

On an authorized creation, configuration, delivery, or merge workflow, inspect and enable these settings when supported:

- `delete_branch_on_merge: true`
- `allow_auto_merge: true`
- `allow_update_branch: true`

Keep visibility, default branch, allowed merge methods, branch rules, security settings, and other repository configuration repository-specific.

## Pull requests

- New PRs default to draft.
- Follow explicit repository merge policy, then recent accepted PR history. Ask only when neither establishes the merge method.
- An explicit merge request authorizes marking the exact eligible draft ready.
- Require repository-documented validation and review gates, a clean PR head, and no known failures even when GitHub has no required checks.
- Enable auto-merge when an explicitly requested merge is waiting only on pending gates.
- Update a behind branch only when repository policy, mergeability, or meaningful validation requires it, then rerun affected gates.

## Governed closeout

An explicit request to merge the exact PR authorizes all of the following without separate branch-cleanup permission:

- verify the merge and declared issue closure;
- require the exact remote head and remote-tracking ref to be absent;
- delete the exact merged local head branch;
- fast-forward the clean canonical default-branch checkout;
- leave every retained checkout clean;
- run the repository cleanup audit.

Closeout is idempotent and state-driven. Already-satisfied invariants are success. Cleanup covers only the exact merged PR head, not unrelated stale branches. When the user merges through GitHub separately, the related task completes these local invariants when it resumes or closes.

## Worktrees and tasks

- Classify provenance only from explicit task or creation context; never infer it from a filesystem path.
- Automatically retire a clean, integrated worktree that was explicitly created by an agent as disposable orchestration state. Do not ask permission. Archive its completed task as the final action when applicable.
- For a user-created Codex worktree task, detach and clean the worktree after merge, then use native user input to ask whether to delete/archive it or retain it for more work. Archive the task when deletion is chosen.
- Treat unknown provenance as user-created and ask.
- Retain and report any worktree or branch with unique unmerged work; automatic disposal never destroys it.
