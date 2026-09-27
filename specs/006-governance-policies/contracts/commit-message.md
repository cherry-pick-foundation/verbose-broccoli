# Contract: Commit-Message Check

## Installation

- Hook file: `scripts/git-hooks/commit-msg`, executable, POSIX shell.
- Repository setting: `core.hooksPath = scripts/git-hooks` (relative, so each
  worktree runs its own checkout's hook). Orca's setup runs `git config
  core.hooksPath scripts/git-hooks`.
- `deno task doctor` fails with guidance when `git config --get
  core.hooksPath` is not exactly `scripts/git-hooks`, and its report records
  the checked value.

## Hook behavior

1. Find Deno: `$HOME/.deno/bin/deno` if executable, else `deno` on `PATH`.
   If neither exists, print `Commit refused: Deno 2.9.6 was not found.` to
   standard error and exit 1.
2. Run `deno task --quiet commitlint --edit "$1"` from the worktree root and
   exit with its status.

`deno task commitlint` runs the pinned `@commitlint/cli` with `--config
scripts/commitlint.config.mjs`, frozen and cached-only.

## Rules

- Everything in `@commitlint/config-conventional` 21.2.3 at its own levels,
  with the parser preset passed as an object (research R1).
- commitlint's default ignores stay on, so Git's default merge messages pass
  without any rule.
- Trailers are not restricted: `Spec-Kit-Task`, `Reviewed-by`,
  `Reviewed-commit`, `Co-Authored-By` and any other trailer are accepted.
- `local/constitution-version` (error level), implemented in
  `scripts/constitution_version.ts`:

| Situation | Result |
| --- | --- |
| No `HEAD`, or `.specify/memory/constitution.md` absent in `HEAD` or the index | Pass (not applied) |
| File identical in `HEAD` and the index | Pass |
| Changed; version line missing or malformed on either side | Refuse |
| Changed; breaking (`!` or `BREAKING CHANGE` footer) | Require `(X+1).0.0` |
| Changed; `feat`, not breaking | Require `X.(Y+1).0` |
| Changed; `docs` or `fix`, not breaking | Require `X.Y.(Z+1)` |
| Changed; any other type, not breaking | Refuse |
| Changed; version equal to `X.Y.Z` | Refuse (every change bumps once) |

The version line is the single line matching `**Version**: X.Y.Z` (the
constitution's footer). Refusal messages state the previous version, the
commit type and the expected version, or that the type cannot change the
constitution.

## Known limit

A `commit-msg` hook is not told about `--amend`, so an amend is compared with
the commit being replaced (research R3).
