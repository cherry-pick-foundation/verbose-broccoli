# Data Model: Governance Policies of 2026-09-27

No persistent storage is added. The entities below are Git objects, refs and
settings that the checks read.

## Review-record commit

| Field | Source | Rule |
| --- | --- | --- |
| parent | `git rev-list --parents -n 1 <tip>` | exactly one |
| tree | `<tip>^{tree}` | equals `<parent>^{tree}` |
| `Reviewed-by` | trailer | exactly one, non-empty, free text |
| `Reviewed-commit` | trailer | exactly one; resolves to `<parent>` |

Lifecycle: created after the merge review on the reviewed tip; becomes the
merge's second parent when the feature finishes; any later commit on the
feature (including a merge of `develop`) makes it stale, and a new review and
record are needed.

## Commit message

| Part | Rule |
| --- | --- |
| header | Conventional Commits 1.0.0 per `config-conventional` |
| breaking | `!` in the header or a `BREAKING CHANGE` footer |
| trailers | any; the four repository trailers always accepted |
| Git default merge message | ignored by the check |

## Constitution version

| Field | Source | Rule |
| --- | --- | --- |
| previous | `HEAD:.specify/memory/constitution.md`, line `**Version**: X.Y.Z` | exactly one match |
| next | index copy of the same file | exactly one match |
| expected next | commit type | breaking → `(X+1).0.0`; `feat` → `X.(Y+1).0`; `docs`/`fix` → `X.Y.(Z+1)`; other → refused |

State: a commit that changes the file moves the version one step; a commit
that leaves the file identical does not apply the rule.

## Worktree branch name

| Field | Source |
| --- | --- |
| worktree name | base name of `git rev-parse --show-toplevel` |
| current branch | `git symbolic-ref --short HEAD` |
| upstream | `@{upstream}`, must be absent |
| own commits | none when another branch contains the tip |
| target | mapping in [contracts/worktree-branch.md](contracts/worktree-branch.md) |

State transition: `<orca-made name>` → `<type>/<rest>` once; a git flow name is
final for this script.

## Repository setting

| Key | Value | Owner |
| --- | --- | --- |
| `core.hooksPath` | `scripts/git-hooks` | Orca setup writes; `deno task doctor` checks |
