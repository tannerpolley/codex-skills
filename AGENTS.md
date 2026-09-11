# Local Codex skill workspace

This repository is the source of truth for personal Codex skills created or revised on this machine.

## Layout

- Keep installable skills in `skills/<skill-name>/`.
- Keep task-specific design notes in `plans/` only when a plan is requested or needed.
- Expose each installed skill with an individual symlink at `~/.agents/skills/<skill-name>`.

## Skill work

For every skill creation or revision, first read both the complete canonical `$skill-creator` skill and the complete `$mattpocock-skills:writing-for-agents` skill, including `SKILL-MECHANICS.md`. Apply them together: skill-creator owns package structure and validation; writing-for-agents owns agent-facing instruction and pointer design. Then follow [the local authoring workflow](docs/skill-authoring.md).

1. Read the complete existing skill and every directly linked instruction before editing it.
2. Make the smallest change that satisfies the request; add scripts, references, assets, or metadata only when they have a concrete use.
3. Keep one authoritative copy under `skills/`. Never copy a second editable version into `~/.agents/skills`.
4. For a new local skill, create its per-skill symlink only after confirming that the destination name is unused.
5. Run the skill-creator validator and verify the local symlink resolves to the repository copy before completion.

Do not modify Codex's managed `.system` skills or plugin cache as part of ordinary local skill work.
