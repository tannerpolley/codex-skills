# Diffs and attributes

## Code-only change statistics

Keep documentation tracked. Limit the comparison instead of changing what Git versions.

Prefer positive inclusion when implementation paths are known:

```bash
git diff --stat <base>...HEAD -- src/ tests/ scripts/
git diff --staged --stat -- src/ tests/ scripts/
```

When code is spread across the repository, start with the whole tree and add quoted exclusion pathspecs:

```bash
git diff --stat <base>...HEAD -- . \
  ':(exclude,glob)docs/**' \
  ':(exclude,glob)**/*.md'
```

Replace `<base>` with the repository's actual integration ref. For `git diff`, `A...B` compares the merge base of A and B with B; `A..B` compares the two endpoints. Use `--numstat` for machine-readable line counts and expect `-` for binary files.

If the command will be reused, add a repository-owned helper that requires the range explicitly:

```bash
#!/usr/bin/env bash
set -euo pipefail
range=${1:?usage: code-diff <range>}
exec git diff --stat "$range" -- . \
  ':(exclude,glob)docs/**' \
  ':(exclude,glob)**/*.md'
```

## Tracking-policy decision

Apply this decision when staging or diff review encounters data, documentation, or artifacts whose treatment is unresolved, as well as for explicit ignore or line-count requests. Inspect the affected paths, their role in the project, and existing repository instructions, ignore files, and attribute files before editing:

```bash
git config --includes --show-origin --show-scope --get-regexp '^(core\.(excludesfile|attributesfile)$|include\.path$|includeif\..*\.path$)'
git ls-files -- path/to/file
git check-ignore -v --no-index -- path/to/file
git check-attr -a -- path/to/file
```

The config query and `check-ignore` return exit status 1 when nothing matches; that alone is not a failure. Inspect default global ignore/attribute files too when their config keys are unset. `check-ignore --no-index` tests patterns even for tracked paths; use `ls-files` to establish tracking state.

Honor the user's existing choices and repository policy. Ask only for unresolved path groups, especially ambiguous `.csv`, `.json`, `.yaml`, `.yml`, and `.svg` files. Show representative paths, their tracked/untracked state, and what accounts for the large diff before offering these treatments:

1. Ignore it entirely because it is disposable: add a repository `.gitignore` rule, or `.git/info/exclude` for a personal repository-only exclusion. For tracked paths, explain that `git rm --cached` keeps the working file but removes it from future snapshots; execute it only when the user's choice authorizes untracking those paths. Ignoring alone does not affect tracked files.
2. Keep it tracked but suppress local line-oriented diffs: use `-diff` in `.gitattributes` for opaque text artifacts. Use `binary` for binary files; it also disables text normalization and normal text merging. A global `core.attributesFile` applies across repositories locally and requires an explicit machine-wide request.
3. Keep it tracked but exclude it from GitHub language statistics or generated-file presentation: use repository-owned `linguist-documentation`, `linguist-generated`, or related attributes. These do not change local Git line statistics.
4. Leave Git tracking and diffs unchanged, but omit it from code-focused reports using positive path inclusion or quoted exclusion pathspecs.

Apply the root native-question policy for unresolved handling preferences. Offer compatible combinations when needed (such as local diff suppression plus GitHub classification), and preserve current behavior until an unresolved choice is answered. Group equivalent paths in one question and reuse that decision for matching paths. Existing rules and repository instructions are the record; add no separate decision ledger. Prefer directory or generated-output paths over broad extension rules. Do not use `assume-unchanged` or `skip-worktree` as classification controls.

After applying a selected policy, verify the effective rule with `git check-ignore -v` or `git check-attr -a`, then verify repository status and the relevant diff/stat output against the same comparison base. Report machine-wide changes separately. Local Git verification does not establish that a UI summary or GitHub honors those rules; verify the requested display before claiming its counts changed.

## Keep docs reviewable

- Keep hand-written docs in the same repository when they describe the same versioned system.
- Use separate coherent commits for implementation, tests, and docs when that improves review. This does not alter the combined pull-request line total.
- Use a separate pull request only when a platform-native code-only total matters more than atomic code-and-doc delivery.

## `.gitattributes` choices

For GitHub language statistics, mark documentation with Linguist attributes:

```gitattributes
*.md linguist-documentation
docs/** linguist-documentation
```

These are GitHub Linguist attributes; they do not change local `git diff` statistics. Reserve `linguist-generated` for machine-generated output because GitHub excludes it from language statistics and hides it in diffs by default.

Git's own `diff` attribute is different:

```gitattributes
docs/snapshots/** -diff
```

Unsetting `diff` keeps versions tracked but reports the file as binary, removing useful line-by-line review and line statistics. Use it only for genuinely opaque snapshots, not hand-written Markdown.

Verify effective attributes:

```bash
git check-attr -a -- docs/example.md
```

## Sources

- https://git-scm.com/docs/gitignore
- https://git-scm.com/docs/git-config
- https://git-scm.com/docs/git-diff
- https://git-scm.com/docs/gitglossary#def_pathspec
- https://git-scm.com/docs/gitattributes
- https://github.com/github-linguist/linguist/blob/main/docs/overrides.md
- https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/filtering-files-in-a-pull-request
