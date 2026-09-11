---
name: baton-pass
description: Coordinate a substantial GitHub-backed repository change through fresh planner, manager, and worker tasks plus an independent reviewer. Use when the user invokes Baton Pass or wants a lightweight multi-agent delivery workflow; always confirm before creating tasks or Git state.
---

# Baton Pass

Run one cooperative delivery workflow in the repository's saved local checkout. Use native Codex task and collaboration tools directly.

## Hard boundary

Run only during active user turns. Never create or use automations, scheduled tasks, heartbeats, cron, timers, delayed wakeups, or background watchers. The manager may use app-task `wait_threads` only for the exact current holder during the active user turn. If CI or another external condition is still pending, report it and wait for a new user message.

## Start

1. Inspect the saved project and repository without changing them. Confirm that the task is substantial enough to benefit from planner, manager, worker, and independent-review roles.
2. Recommend an available model and supported reasoning effort for the planner, with a short reason. Ask the user to confirm or choose another combination and whether to include optional Fable review.
3. After confirmation, require a clean GitHub-backed saved local checkout. Fix the role topology: the calling task is the coordinator unless the user explicitly makes it the manager; never create a second manager. Create `docs/baton-pass/<session-id>/`, add `/docs/baton-pass/` only to the checkout's local `.git/info/exclude`, and write `brief.md` plus a small `status.md` containing the session, repository, topology, current holder, and role task IDs.
4. Create one fresh planner app task in the saved project with `environment: {type: "local"}`, the confirmed model and effort, and a prompt containing the session path, task brief, and its exact next handoff from [Handoffs](#handoffs). Do not create manager or worker yet.

If task creation or a direct message has an ambiguous result, stop and show the user the known facts. Never retry automatically or create a replacement task without the user's direction.

## Planner

The planner is repository-read-only except for the ignored session folder.

1. Read the brief, repository instructions, relevant code, tests, and issue or specification.
2. Write `plan.md` with the implementation approach, acceptance criteria, important risks, and verification.
3. Choose any currently available model and supported reasoning effort for manager, worker, and the fresh candidate reviewer. Explain what each assignment needs and why that model/effort fits. Role names do not imply model families.
4. When `status.md` already names the calling task as manager, set it as holder, send it the `plan-ready` handoff, and stop. The manager asks the user to approve or revise the plan and staffing together, then creates only the worker after approval.
5. Otherwise ask the user to approve or revise the plan and staffing together. After approval, create fresh manager and worker app tasks in the same saved local checkout using the approved combinations. Give each an inert setup prompt naming its role, session path, and exact next handoff.
6. Record their task IDs in `status.md`, set manager as holder, send the manager the `plan-ready` handoff, and stop.

When the manager later requests plan-fidelity review, compare the candidate with `brief.md` and `plan.md`. Return `PASS` or one consolidated findings list, then stop.

## Manager

The manager is the only role that mutates Git or GitHub.

1. Read the approved plan, verify the checkout, create the task feature branch, and turn the plan into a bounded worker assignment.
2. Set worker as holder in `status.md`, send one concise handoff, then wait on that exact worker. When it completes or needs attention, immediately continue at step 3. Successful message delivery is not a stopping condition.
3. When work returns, inspect the complete diff and evidence. Make only tiny obvious corrections; send substantive corrections back to the worker.
4. Run repository-required checks, commit the coherent change, push it, and open or update one draft PR.
5. Ask the original planner for plan-fidelity review. Resolve any findings through the worker before continuing.
6. If the user enabled Fable, use the available `fable-review` skill on a self-contained candidate packet. Treat its result as advisory, verify the findings, and ask the user whether to apply or decline them.
7. Spawn one fresh collaboration reviewer with `fork_turns: "none"` and the reviewer model/effort approved in the plan. Its prompt must include the brief, plan, candidate SHA, changed files, checks, and review criteria. Require read-only work, no helpers, no Git/GitHub or app-task mutation, and the same no-scheduling boundary as this skill.
8. Route actionable reviewer findings through the worker. A changed candidate repeats planner fidelity and fresh independent review.
9. When the planner returns `PASS`, optional Fable findings are dispositioned, and the independent reviewer returns `ACCEPT`, present the exact PR, checks, reviewed head SHA, and merge method to the user.
10. On approval, revalidate the PR head and make one direct merge request guarded by that reviewed SHA. Never enable auto-merge or a merge queue.
11. Follow the installed Git and GitHub skills for closeout: verify the merge, return the saved checkout to its clean default branch, remove only the exact merged feature branch locally and remotely, and run the repository cleanup audit.

If checks or mergeability are pending, stop and ask the user to resume later. Do not poll.

## Worker

The worker writes implementation and tests but does not mutate Git or GitHub.

1. Read only the current assignment, brief, and approved plan.
2. Implement the smallest maintainable change and run proportionate checks.
3. Write a short result in the session folder with changed paths, checks, and remaining risk.
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
```

If the direct message fails or is ambiguous, restore the sender as holder, record the failed handoff in `status.md`, report it to the user, and stop. Do not retry or create a replacement task without direction.

If a non-holder receives a manual prompt, it may read `status.md`, identify the current holder, and stop without changing repository or workflow state.

This file-based coordination is a convention among trusted tasks, not a security or transaction boundary.

## Finish

Completion means the requested change is merged, required checks passed, the saved checkout is clean on its updated default branch, exact feature-branch cleanup is complete, and the user receives the final result. Ask whether to retain or delete the ignored session folder. Archive tasks only when the user asks.
