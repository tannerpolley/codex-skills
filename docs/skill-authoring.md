# Skill Authoring

Use this workflow when creating, revising, auditing, or installing personal Codex skills.

## Required guidance

Before writing or revising a skill, read both complete skills below and apply them together:

- Canonical `$skill-creator`: package structure, resources, metadata, initialization, and validation.
- `$mattpocock-skills:writing-for-agents`: instruction hierarchy, context pointers, progressive disclosure, and pruning. Also read its `SKILL-MECHANICS.md` for skill invocation design.

The user's request controls the outcome. Neither skill expands authorization or the requested scope.

## Local workflow

1. Keep the authoritative skill at `skills/<skill-name>/` in this repository. Resolve an existing `~/.agents/skills/<skill-name>` link before editing.
2. For a new skill, confirm the install name is unused, create it under `skills/`, then add one individual symlink at `~/.agents/skills/<skill-name>`.
3. Keep planning and evaluation material outside the runtime skill unless an agent must load it while using the skill. Use `plans/` for active design work and `evaluations/` for external regression cases.
4. Run the canonical skill validator, any smallest relevant resource check, and a symlink-resolution check. Completion requires valid metadata and a local install link resolving to the repository copy.

Plugin caches, bundled `.system` skills, generated task artifacts, and copied install trees are not source locations.

## Review revisions

Compare every review-driven change with the original request and trigger cases. Remove review-created machinery when it no longer serves them; do not preserve rejected drafts as current guidance.
