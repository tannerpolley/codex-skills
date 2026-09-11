# GitHub profile preferences

These preferences are standing workflow authority for the authenticated `tannerpolley` account. They do not authorize changes to unrelated repositories or user work.

## Scope

- Apply repository defaults only to active, non-archived repositories owned by `tannerpolley` when a current authorized workflow touches that repository.
- Treat current tasks, recent commits or pull requests, and active canonical checkouts as evidence of activity. Do not sweep dormant repositories, old mirrors, archived repositories, or untouched forks.
- Preserve organization and third-party repository policy unless the user explicitly includes it.

## Delivery

- Apply the root authority boundary: local implementation may include focused commits; remote publication and merge need matching task authority, reused when already clear. A local-only endpoint is complete without a push or PR.
- An explicit merge request covers necessary prerequisites for that reviewed PR, not unrelated branch updates. A push to an already armed auto-merge PR requires merge authority as well as publication authority.
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
- Enable auto-merge when an explicitly requested merge is waiting only on pending hosted gates after selected local review. Use an available exact-head guard and verify the hosted head; it does not lock out later pushes. Report pending honestly and preserve any selected workflow's no-watcher boundary.
- Update a behind branch only when repository policy, mergeability, or meaningful validation requires it, then rerun affected gates.

## Governed closeout

An explicit request to merge the exact PR authorizes verified merge/issue closure, removal of its remote feature head, and the associated local closeout without separate branch-cleanup permission. Use [Git history and recovery](../../git/references/history-and-recovery.md#merge-and-closeout) for branch mapping, integration checks, pruning, and returning the saved checkout to updated local `main`.

Closeout is idempotent and state-driven. Already-satisfied invariants are success. It covers safely integrated local branches associated with that exact PR, including different local names, not unrelated stale branches. When the user merges through GitHub separately, the related task completes these local invariants when it resumes or closes. Preserve dirty state, unique work, and occupied checkouts; pending auto-merge is not merge evidence.

## Worktrees and tasks

- Classify provenance only from explicit task or creation context; never infer it from a filesystem path.
- Automatically retire a clean, integrated worktree that was explicitly created by an agent as disposable orchestration state. Do not ask permission. Archive its completed task as the final action when applicable.
- For a user-created Codex worktree task, preserve it and use native input to decide deletion/archive or retention. Return the saved task checkout to local `main` through Git closeout when safe; do not force occupied branches or destroy dirty state. Archive the task when deletion is chosen.
- Treat unknown provenance as user-created and ask.
- Retain and report any worktree or branch with unique unmerged work; automatic disposal never destroys it.
