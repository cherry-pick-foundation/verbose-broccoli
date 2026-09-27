# Contract: Branch Names for New Worktrees

## Invocation

Orca's setup script runs `sh scripts/worktree-branch.sh` from the new
worktree's root, before its other steps. The script takes no arguments and
reads nothing from the environment besides Git's.

## Name mapping

The worktree name is the base name of `git rev-parse --show-toplevel`.

| Worktree name | Branch |
| --- | --- |
| `release-<rest>` | `release/<rest>` |
| `hotfix-<rest>` | `hotfix/<rest>` |
| `feature-<rest>` | `feature/<rest>` |
| any other `<name>` | `feature/<name>` |

Examples: `release-1.0` → `release/1.0`, `hotfix-1.0` → `hotfix/1.0`,
`governance-policies` and `feature-governance-policies` →
`feature/governance-policies`.

## When it renames

All must hold; otherwise it exits 0 without changes:

1. HEAD is a branch (not detached).
2. The branch is not `main` or `develop`, and does not start with `feature/`,
   `release/` or `hotfix/`.
3. The branch has no upstream.
4. The branch tip is contained in at least one other local or remote-tracking
   branch, so it has no commits of its own.

## Failures

With the conditions above met, the script exits 1 with one line on standard
error and renames nothing when:

- the name has nothing after `release-`, `hotfix-` or `feature-`;
- `git check-ref-format --branch <target>` rejects the target;
- the target branch already exists.

Orca's setup uses `set -eu`, so a failure stops the setup.

## Guarantees

- Only the branch checked out in this worktree is renamed, with `git branch
  -m`. Folder names, other branches and other worktrees do not change.
- A second run changes nothing.
- Remove the script and its setup line once `orca worktree create` offers a
  branch option.
