# Evidence-first checkpoint

Use this reference when the takeover involves mathematics, science, numerical behavior, debugging, or a long chain of experiments.

## Required fields

- objective and exact failure signature;
- expected value, trend, invariant, or tolerance;
- equations, assumptions, units, parameters, solver/settings, commit, and environment;
- evidence ledger with experiment/run ID, command, result, and interpretation;
- active hypotheses and supporting/contradicting evidence;
- rejected hypotheses and the test or observation that rejected each;
- known-good reference check and its expected result;
- absolute paths to full logs, plots, tables, and generated artifacts;
- one next discriminating experiment with pass/fail criteria.

## Minimal ledger

| Run | Command/input | Result | Interpretation / what it rules out |
|---|---|---|---|
| ... | ... | ... | ... |

Keep full evidence in files and put only bounded excerpts and paths in the successor prompt. Preserve decisions and evidence, not private chain-of-thought.

## Gate

The source remains active when required fields or artifact paths are missing. The successor must verify the known-good check before continuing. A mismatch is a stop condition, not an invitation to infer missing context or repeat rejected work.
