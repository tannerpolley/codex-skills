# GitHub CLI and `gh skill`

Use this reference for GitHub operations performed with `gh`, including the
GitHub CLI's Agent Skills commands. Treat remote writes as separately
authorized actions: inspect first, target the exact repository, and review
the proposed change before creating, editing, merging, publishing, or
deleting anything.

## Contents

- [Invocation and targeting](#invocation-and-targeting)
- [Structured output and pagination](#structured-output-and-pagination)
- [Search and list](#search-and-list)
- [Issues, relationships, and discussions](#issues-relationships-and-discussions)
- [Pull requests and API fallback](#pull-requests-and-api-fallback)
- [Projects and extensions](#projects-and-extensions)
- [Authentication](#authentication)
- [Managing Agent Skills](#managing-agent-skills)

## Invocation and targeting

`gh` infers the repository from the current working directory's Git remote.
Pass `--repo OWNER/REPO` or `-R OWNER/REPO` when the target is not the
repository inferred from the current directory or when deterministic targeting
matters.

In non-TTY contexts, `gh` skips the pager, strips ANSI color, and fails rather
than prompting for required values. Supply flags such as `--title`, `--body`,
and `--category` explicitly for agent-operated commands. Do not add a
nonexistent `--no-pager` flag; use `GH_FORCE_TTY=1` only when TTY-style output
is specifically needed.

## Structured output and pagination

Human-readable `gh` output is column-formatted. Prefer structured output when
the result will be parsed:

- Add `--json field1,field2,...`; run the command with `--json` and no field
  list first to discover available fields.
- Use `--jq '<expr>'` for filtering without a separate `jq` process.
- Use `--template '<go-template>'` with `--json` for shaped text. Check
  `--help` first because `--template`/`-T` collides with body-template flags
  on commands such as `gh pr create` and `gh issue create`.

List commands cap results. Pass `-L N` or `--limit N` to `gh issue list`,
`gh pr list`, and `gh search ...`; the default is commonly 30. These typed
list commands do not expose aggregate totals through `--json`. Use
`gh api graphql` and query `totalCount` when a true total is required.

For raw API calls, use `gh api --paginate <path>`. Combine it with `--jq`
and, when needed, `--slurp` to assemble one array.

## Search and list

Use `gh search issues|prs|code|repos|commits|users` for cross-repository
queries or GitHub search syntax such as `is:open`, `author:`, `label:`,
`repo:owner/name`, and `in:title`:

```bash
gh search issues "is:open author:octocat repo:cli/cli"
```

Use `gh issue list --search "..."` or `gh pr list --search "..."` for the
same syntax scoped to the current repository.

## Issues, relationships, and discussions

Check `gh issue --help` before choosing an extension because newer versions
may expose overlapping native features. Newer `gh issue` commands can model
issue types, parent/sub-issue hierarchy, and blocked-by/blocking relationships:

- `gh issue create` accepts `--type`, `--parent`, `--blocked-by`, and
  `--blocking`.
- `gh issue edit` accepts the corresponding `--type`, `--parent`,
  `--add-sub-issue`, `--remove-sub-issue`, `--add-blocked-by`, and
  `--add-blocking` flags, plus their removal forms.
- `gh issue list --type` filters by issue type.
- Prefer `issueType`, `parent`, `subIssues`, `subIssuesSummary`, `blockedBy`,
  and `blocking` fields in `gh issue view` or `gh issue list` JSON output.
  Relationship fields are capped objects with `nodes` and `totalCount`; compare
  the counts to detect truncation.

Issue types and sub-issues require GitHub Enterprise Server 3.17+; blocked-by
and blocking relationships require 3.19+.

The `gh discussion` command set is preview functionality. Common forms are:

```bash
gh discussion list --state open --limit 30 --json number,title
gh discussion view 12 --comments --order oldest
gh discussion create --title "Question" --body-file question.md --category Q&A
gh discussion edit 12 --title "Updated question"
gh discussion comment 12 --body "Follow-up"
```

`gh discussion list` supports state, category, author, labels, answered,
search, sort/order, limit, cursors, JSON, and web flags. `view` accepts a
discussion, comment, or reply target; use `--comments` for discussion comments
and pass a comment target to list its replies. `create` requires a title,
body, and category non-interactively. `edit` changes title, body, category,
or labels. `comment --edit` and `--delete` need a comment ID or URL; use
`--yes` to skip delete confirmation.

## Pull requests and API fallback

Use `gh pr view` or `gh pr diff` when you only need to inspect a pull request.
`gh pr checkout <number>` switches to its branch when that state change is
intended.

The `--comments` flag on `gh pr view` shows issue-level comments, not inline
review-thread comments. Use the REST API for review threads:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments
```

Use `gh api graphql -f query='...' -F var=value` for arbitrary GraphQL and
`gh api repos/{owner}/{repo}/...` for REST shortcuts. Placeholders are filled
from the detected repository when supported; pass the owner and repository
literally when deterministic behavior is required.

## Projects and extensions

Verify installed extensions with `gh extension list` before relying on one;
extensions can be upgraded or removed. Common local extensions include:

- `gh projects` for name-based Projects v2 board and item shortcuts;
- `gh sub-issue` for parent-child issue operations when native commands do not
  cover the needed feature;
- `gh dash` for a terminal PR/issue dashboard;
- `gh notify` for notifications;
- `gh pr-review` for inline review threads;
- `gh branch` for fuzzy branch switching/deletion (requires `fzf`);
- `gh poi` for safe cleanup of merged local branches; run `--dry-run` first;
- `gh markdown-preview` for local GitHub-style Markdown previews;
- `gh act` for local GitHub Actions runs (requires Docker).

Use native `gh project` for standard Projects CRUD. Use `gh projects` only
when its board and item shortcuts are more convenient.

## Authentication

Run `gh auth status` to inspect active hosts, the authenticated user, and the
environment variable being honored. `gh auth status --json` is available when
the result needs structured parsing. Do not print or expose credentials.

## Managing Agent Skills

`gh skill` manages Agent Skills in GitHub repositories; `gh skills` is an alias,
but use the singular command in scripts and documentation.

### Search and preview

```bash
gh skill search <query>
gh skill search <query> --owner <org> --limit 20 --page 2
gh skill search <query> --json skillName,repo,description
gh skill preview <owner>/<repo> <skill-name>
gh skill preview <owner>/<repo> <skill-name>@v1.2.0
gh skill list --scope user --agent codex --json skillName,path,version
```

### Install and update

```bash
gh skill install <owner>/<repo> <skill-name> --agent codex --scope user
gh skill install <owner>/<repo> <skill-name> --pin v1.2.0
gh skill install <owner>/<repo> skills/<scope>/<skill-name> --agent codex
gh skill install ./local-skills-repo --from-local --agent codex
gh skill install <owner>/<repo> --all --agent codex --scope user
gh skill update --all
gh skill update <skill>
gh skill update <skill> --force
gh skill update --unpin
```

The repository is required for repository installs, while the skill name is
optional: omit it to list or interactively choose among discovered skills, or
use `--all` to install every discovered skill. Exact nested paths can be used
to skip broad repository traversal. Use `--from-local` for a local directory,
and `--dir` to install into a custom directory instead of the selected agent
and scope. Use `--agent codex` for this environment rather than relying on the
non-interactive default. `--scope project|user` controls whether installation
is local to the current repository or user-wide. `--pin` accepts a tag or
commit SHA and is mutually exclusive with `--from-local` and inline
`@version`. Use `--upstream` only when deliberately bypassing a re-published
skill's source. Use `--allow-hidden-dirs` only when a dot-directory skill is
intentionally in scope. Use `--force` only when overwriting is authorized.

`gh skill update` checks installed skills for remote changes; use `--dry-run`
for a read-only update check. Pinned skills are skipped unless `--unpin` is
used. Skills without GitHub source metadata are skipped in non-interactive
mode.

### Publish

Publishing is a remote write. Validate first and obtain explicit authorization
before adding repository topics, pushing commits, creating releases, or
publishing a skill:

```bash
gh skill publish --dry-run
gh skill publish --dry-run ./path/to/repo
gh skill publish --fix
gh skill publish --tag v1.0.0
```

`--fix` and `--dry-run` are mutually exclusive. `--fix` only strips
install-injected `metadata.github-*` keys; review and commit the result before
publishing. A publish flow discovers skills from `skills/<name>/SKILL.md`,
`skills/<scope>/<name>/SKILL.md`, `<name>/SKILL.md`, or
`plugins/<scope>/skills/<name>/SKILL.md`. Each skill needs YAML frontmatter
with a matching directory name and description.

Always pass `--tag` for a non-interactive publish. The publish flow may add
the `agent-skills` topic, push unpushed commits, and create a GitHub release.
