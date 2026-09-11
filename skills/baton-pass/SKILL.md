---
name: baton-pass
description: Coordinate an explicitly selected Baton Pass workflow through planner, manager, worker, and independent review, preserving its planning and staffing gates.
---

# Baton Pass

Run one cooperative delivery workflow in the repository's saved local checkout. Use native Codex task and collaboration tools directly.

Before planning or review disposition, read [shared review recovery](/home/tnnrpolley21/.codex/references/review-control.md). Keep acceptance, finding dispositions, and correction history in the existing brief and handoffs.

## Hard boundary

Run only during active user turns. Never create or use automations, scheduled tasks, heartbeats, cron, timers, delayed wakeups, or background watchers. The manager may use app-task `wait_threads` only for the exact current holder during the active user turn. If CI or another external condition is still pending, report it and wait for a new user message.

## Start

1. Inspect the saved project and repository without changing them. Confirm that the task is substantial enough to benefit from planner, manager, worker, and independent-review roles.
2. Verify the required app-task and native-reviewer tools are callable. Recommend an available model and supported reasoning effort for the planner, with a short reason. Use native input to settle planner staffing and optional Fable review, reusing choices already established. Report unavailable required capabilities before creating tasks; app tasks and native children are distinct.
3. After confirmation, require a clean GitHub-backed saved local checkout. Fix the role topology: the calling task is the coordinator unless the user explicitly makes it the manager; never create a second manager. Create `docs/baton-pass/<session-id>/`, add `/docs/baton-pass/` only to the checkout's local `.git/info/exclude`, and write `brief.md` plus a small `status.md` containing the session, repository, topology, current holder, and role task IDs.
4. Create one fresh planner app task in the saved project with `environment: {type: "local"}`, the confirmed model and effort, and a prompt containing the session path, task brief, and its exact next handoff from [Handoffs](#handoffs). Do not create manager or worker yet.

If task creation or a direct message has an ambiguous result, stop and show the user the known facts. Never retry automatically or create a replacement task without the user's direction.

## Planner

The planner is repository-read-only except for the ignored session folder.

1. Read the brief, repository instructions, relevant code, tests, and issue or specification.
2. Write `plan.md` with authorized outcomes/phases, non-goals, implementation approach, observable acceptance, material ownership decisions, important risks, and verification. Keep optional experiments and future phases distinct from authorized implementation.
3. Choose any currently available model and supported reasoning effort for manager, worker, and the fresh candidate reviewer. Explain what each assignment needs and why that model/effort fits. Role names do not imply model families.
4. When `status.md` already names the calling task as manager, set it as holder, send it the `plan-ready` handoff, and stop. The manager asks the user to approve or revise the plan and staffing together, then creates only the worker after approval.
5. Otherwise ask the user to approve or revise the plan and staffing together. After approval, create fresh manager and worker app tasks in the same saved local checkout using the approved combinations. Give each an inert setup prompt naming its role, session path, and exact next handoff.
6. Record their task IDs in `status.md`, set manager as holder, send the manager the `plan-ready` handoff, and stop.

When the manager later requests plan-fidelity review, compare the local candidate with `brief.md` and `plan.md`, including the root no-overengineering rule. Reject bandaid layers that retain the diagnosed broken implementation. Return `PASS` or one consolidated findings list tied to requirements and evidence, distinguishing blockers from optional advice, then stop.

## Manager

The manager is the only role that mutates Git or GitHub. Enforce the root no-overengineering rule in assignments and acceptance: the only accepted repair removes all broken code within the diagnosed boundary and replaces it with the simplest correct solution. Never dispatch or accept bandaid layers over problematic code; preserve required behavior, safeguards, and unrelated work.

1. Read the approved plan, verify the checkout, reuse or create the task feature branch, and turn the plan into a bounded worker assignment with the same outcome, non-goals, acceptance, and correction history reviewers will receive.
2. Set worker as holder in `status.md`, send one concise handoff, then wait on that exact worker. When it completes or needs attention, immediately continue at step 3. Successful message delivery is not a stopping condition.
3. When work returns, inspect the complete diff and evidence, including Serena use or its concrete fallback reason for supported code work. Verify that repairs replace the defective implementation at its responsible boundary rather than mask its symptoms. Classify findings before making tiny obvious in-scope replacements or sending substantive replacements to the worker under shared recovery.
4. Run required local checks and commit a coherent candidate. Prepare local review evidence: brief, plan, candidate SHA, relevant diff, changed paths, checks, and limitations. A published PR is not a local-review prerequisite.
5. Ask the original planner for plan-fidelity review. Adjudicate findings against accepted scope before assigning corrections.
6. If the user enabled Fable, use the available `fable-review` skill on a self-contained candidate packet that includes the root no-overengineering requirement. Treat its result as advisory, verify the findings, and ask the user whether to apply or decline them.
7. Spawn one fresh native collaboration reviewer with no inherited turns and the approved model/effort, using the live tool schema. Supply the brief, plan, outcome/non-goals, candidate SHA, diff, checks, review criteria, and correction history. Require read-only work, no helpers, no Git/GitHub or app-task mutation, and the same no-scheduling boundary. Explicitly require rejection of overengineering and bandaid layers: acceptance requires removal of the diagnosed broken implementation, a correct replacement, and preserved required behavior and safeguards. Findings must identify a violated requirement and evidence, or be labeled optional.
8. Adjudicate findings before bounded worker corrections. Renew only invalidated checks or reviews and establish acceptance at the actual final candidate. Preserve correction history across every holder and reviewer.
9. After planner `PASS`, selected Fable disposition, and independent `ACCEPT`, verify publication authority. A local-only endpoint finishes locally; otherwise obtain missing publication authority natively. Immediately before push, verify HEAD, relevant index/worktree state, review evidence, remote target, and existing auto-merge state. A push that could trigger armed auto-merge also needs merge authority.
10. Push only the accepted candidate, create/update the authorized draft PR, and verify its hosted head. Hosted CI and required GitHub reviews that need publication remain merge gates afterward. Any branch update requires renewed affected evidence.
11. Present the exact PR, checks, reviewed head, and merge method. With existing or newly granted merge authority, revalidate the hosted head and request a guarded merge, or enable native auto-merge while hosted gates are pending. Honor existing merge-queue policy without introducing or bypassing one. A head guard is not a permanent lock on later pushes.
12. On observed merge, follow Git and GitHub for exact associated-branch closeout and return the saved checkout to updated local `main`. Pending auto-merge is not a completed merge.

If hosted checks or mergeability are pending, report the actual gate and await an active authorized continuation. Do not poll or schedule a watcher. At a shared recovery trigger, the holder pauses affected edits and returns evidence to the registered manager; the manager must resolve the recovery boundary before another corrective dispatch.

## Worker

The worker writes implementation and tests but does not mutate Git or GitHub.

1. Read only the current assignment, brief, and approved plan.
2. Follow the root no-overengineering rule: never add bandaid code over problematic code. Remove all broken code within the diagnosed boundary and replace it with the simplest correct solution, preserving required behavior, safeguards, and unrelated work. Run proportionate checks against the original failure and affected behavior; if replacement exceeds authority, return the blocker instead of layering a workaround.
3. Write a short result in the session folder with changed paths, checks, remaining risk, and inherited correction history. At a recovery trigger, pause affected edits and return the evidence to the manager through the same handoff.
4. Set manager as holder in `status.md`, then call `mcp__codex_app__send_message_to_thread` exactly once with the manager task ID recorded there and the concise handoff below; only a successful tool result completes the handoff. Create no helper agents or app tasks.

## Handoffs

Only the holder works. Every role-creation or follow-up prompt names the exact next handoff that role must perform. A final response reports a completed handoff; it does not replace one.

A handoff is complete only when the sender:

1. writes its required artifact;
2. updates `status.md` with the registered next holder;
3. successfully sends that task the direct handoff message; and
4. reports the completed handoff in its final response.

Keep the direct message short:

```text
$baton-pass session=<id> role=<role> action=<action> read=<absolute-session-path>
Completion gate: return a final response only after the required artifact, holder update, and direct message to the recorded next task all succeed; otherwise restore yourself as holder and report the blocker.
```

If the direct message fails or is ambiguous, restore the sender as holder, record the failed handoff in `status.md`, report it to the user, and stop. Do not retry or create a replacement task without direction.

If a non-holder receives a manual prompt, it may read `status.md`, identify the current holder, and stop without changing repository or workflow state.

This file-based coordination is a convention among trusted tasks, not a security or transaction boundary.

## Finish

Completion means the authorized endpoint and its applicable checks/reviews are satisfied. For an authorized merge endpoint, verify the merge, associated-branch closeout, and saved checkout on updated local `main`, preserving unrelated work. A local-only endpoint does not require publication. Ask whether to retain or delete the ignored session folder. Archive tasks only when the user asks.
