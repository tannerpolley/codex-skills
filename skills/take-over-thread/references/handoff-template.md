# Takeover handoff template

Use this template for the successor prompt. Replace required placeholders with observed facts; keep evidence bounded and point to full artifacts by absolute path.

```markdown
You are taking over from an oversized Codex thread. Continue from this handoff; do not restart the task or merely acknowledge the takeover.

Use tools first to verify the workspace and current state, verify the known-good check, then execute the first concrete action in `## Next Steps`. Continue until the objective is complete or a genuine blocker remains. Report concrete work and results, not an acknowledgement-only response.

# Takeover Handoff

## Objective
<Current user goal and expected finish line.>

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
