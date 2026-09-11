# Takeover handoff template

Use this template for the successor prompt. Replace required placeholders with observed facts; keep evidence bounded and point to full artifacts by absolute path.

```markdown
You are taking over from an oversized Codex thread. Continue from this handoff; do not restart the task or merely acknowledge the takeover.

Verify the workspace, current state, and known-good check, then execute the first authorized action in `## Next Steps`. Preserve unresolved decisions and recovery pauses. Continue through authorized phases until the endpoint or a genuine blocker; report concrete results.

# Takeover Handoff

## Objective
<Current user goal and expected finish line.>

## Acceptance and Review State
- Authorized phases and non-goals: <...>
- Acceptance evidence: <...>
- Optional experiments and future possibilities, not authorized work: <...>
- Finding dispositions and correction rounds for this acceptance boundary: <...>
- Recovery decision or unresolved stop: <...>

## Source Thread
- Thread id: <exact source thread id>
- Host id: <exact source host id, when available>

## Workspace
- Path: <absolute path>
- Project/repo: <name or project id if useful>
- Branch/state: <branch, dirty state, relevant uncommitted files>

## Source Execution Settings
- Model: <exact source model id>
- Thinking: <exact source thinking level>

## User Constraints
- <Durable instructions, approvals, forbidden actions, style rules, deadlines>

## Completed Work
- <Concrete changes already made>
- <Files created/edited/deleted>

## Current State
- <What is true right now>
- <Running commands, servers, tests, or known stopped processes>

## Evidence Checkpoint
- Failure signature: <...>
- Expected value/trend/invariant and tolerance: <...>
- Key equations/assumptions or durable decisions: <...>
- Evidence ledger and rejected paths: <file path or bounded table>
- Known-good verification and expected result: <...>
- Full artifacts: <absolute paths>

## Important Files And Context
- <absolute/path: why it matters>

## Validation
- <Commands run and pass/fail result>
- <Validation still needed>

## Blockers And Risks
- <Known issue, ambiguity, or decision needed>

## Next Steps
1. <First concrete action>
2. <Second concrete action>
3. <Finish/verify/report action>
```
