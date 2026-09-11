---
name: take-over-thread
description: Move ongoing work into a fresh Codex task when the user requests a takeover. For an observed continuation problem, recommend a takeover without creating one automatically.
---

# Take Over Thread

An explicit request for a fresh successor task authorizes takeover. An ordinary “continue” request stays in the existing task. Observable timeout or inaccessible context may justify one recommendation; turn counts and compaction counts alone are not takeover gates. Await the user's choice before creating a successor. Use the active tool contract for asking, and do not repeat an unchanged recommendation.

Work at a safe boundary. Preserve active experiments, pending approvals, and intentionally running processes.

## Prepare the handoff

Capture the source task and host IDs, exact active model and thinking settings, actual checkout, objective, constraints, completed work, evidence, known-good check, artifacts, and next action. Obtain settings from source-task metadata or UI rather than inferring configured defaults. If exact required settings cannot be established, preserve the source and report that specific gap.

Read [the handoff template](references/handoff-template.md); for scientific or diagnosis-heavy work also read [evidence guidance](references/evidence-first.md). Verify required artifact paths and distinguish unavailable evidence from completed work. Keep the handoff concise; preserve decisions and evidence rather than raw transcripts or private reasoning.

## Create and verify

Use only callable tools needed for the selected target. Use `list_projects` to resolve project work, retaining the local checkout unless isolation was explicitly requested; projectless work needs no project lookup. Establish a supported observation route before creating work.

Create the successor with the exact source model and thinking values and a direct instruction to continue from the handoff. Require it to verify the relevant known-good check and perform the first concrete next action. A setup-only `clientThreadId` is not an addressable task ID: retain it and keep the source active until a real task ID is established. Do not guess the mapping or launch a duplicate.

Observe the ready successor with supported wait/read tools. Keep the source active on a timeout, missing result, mismatched check, unavailable artifact, or unverifiable continuation. Only after concrete continuation is verified may `set_thread_archived` archive the exact source. Optional title-setting failure does not invalidate successful creation.

Report the ready or pending state and whether the source was archived. Include the app's created-task directive on its own line: `::created-thread{threadId="..."}` for a ready task or `::created-thread{clientThreadId="..."}` for pending setup.
