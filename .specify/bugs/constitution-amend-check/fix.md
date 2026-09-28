# Bug Fix: Commit-message check rejects amending a constitution commit

- **Slug**: constitution-amend-check
- **Fixed**: 2026-09-28
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The `commit-msg` hook now reads the arguments of the `git` process that runs it.
When one of them is `--amend` or an abbreviation git accepts for it, it sets
`CONSTITUTION_VERSION_AMEND`, and
the constitution version rule compares the index with `HEAD^`, the parent of the
commit being replaced, instead of with `HEAD`. So an amend keeps the version the
replaced commit set, and a new commit still needs its own bump.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `scripts/git-hooks/commit-msg` | modified | Reads `/proc/$PPID/cmdline`, split on NUL bytes; exports `CONSTITUTION_VERSION_AMEND=1` for an amend and unsets it otherwise. |
| `scripts/constitution_version.ts` | modified | `constitutionVersionRule` uses `HEAD^` as the baseline when the variable is set. |
| `scripts/commit_msg_test.ts` | added test | Real amends through the hook. |
| `docs/architecture.md` | modified | Describes how amends are checked and when the old refusal remains. |

## Diff Highlights (optional)

The hook turns the parent's argument list into decimal bytes with `od` and
rebuilds each argument in `awk`, so an argument is compared whole, never a
line inside a multi-line message. `--am`, `--ame` and `--amen` count as
`--amend`, and a later `--no-amend`, `--no-am`, `--no-ame` or `--no-amen`
cancels it, as in git's own parsing. An amended root commit has no `HEAD^`, so
the check does not apply, as for a first commit.

## Tests Added or Updated

- `scripts/commit_msg_test.ts`, test "commit-msg hook: amendments use the parent
  constitution version":
  - After `docs!: break` sets 1.0.0, `git commit --amend --no-edit` with more
    text and 1.0.0 is accepted and replaces `HEAD`. Before the fix it failed with
    "Constitution version 1.0.0 with commit type 'docs' requires 2.0.0; found
    1.0.0. [local/constitution-version]".
  - The same with `git commit --amend -m 'docs!: break'` is accepted.
  - An amend that raises 1.0.0 to 2.0.0 again is refused ("requires 1.0.0;
    found 2.0.0"), and `HEAD` is unchanged.
  - Amending a `docs` commit that did not change the constitution so that it
    does is refused without the patch bump and accepted with it.
  - A new commit after a constitution commit still needs its own bump, even with
    `CONSTITUTION_VERSION_AMEND=1` in the environment git runs with.
  - `git commit --amen --no-edit` with new text at 1.0.0 is accepted. Before the
    hook recognized abbreviations, it failed with "requires 2.0.0; found 1.0.0".
  - `git commit --am -m 'docs!: break again'` with 2.0.0 is refused, and `HEAD`
    is unchanged.
  - `git commit --am --no-am` makes a new commit, which needs its own bump.

## Local Verification

- Reported by the implementing Codex worker (Orca dispatch `ctx_6c1f978fb088`):
  the first new test failed before the fix with the message above;
  `deno task test:commit-msg` then passed (4 tests), and `deno task check` and
  `deno task verify` passed.
- Reported by the Codex worker that added the abbreviations (Orca dispatch
  `ctx_0a6f80b132a7`): the `--amen` case failed before the hook change, and
  `deno task test:commit-msg`, `deno task format:check`, `deno task lint` and
  `deno task verify` passed after it.
- Coordinator: `deno task test:commit-msg` passed (4 tests; the hook took 175 ms
  in the runtime test), and `deno task format:check` and `deno task lint`
  passed.
- Coordinator: a scratch hook that printed its parent's arguments showed
  `/usr/lib/git-core/git commit --amend -q --no-edit --allow-empty` for an
  alias `fixup2 = commit --amend` (git 2.53.0). Git runs an alias as a child
  process, so the hook still sees `--amend`.

## Deviations from Assessment

- No `ps -o args=` fallback. Where `/proc/$PPID/cmdline` cannot be read, the
  hook treats the commit as not an amend. This keeps the hook to the one path
  its tests run.
- The assessment's Risks & Considerations says an amend the hook cannot see
  falls back to today's refusal, "never to a false acceptance". That is wrong,
  as the develop merge review showed: an undetected amend is compared with the
  commit it replaces. So it is refused when it changes the text and keeps that
  commit's version, but accepted when it raises the version once more, or when
  it leaves the file as that commit left it, even as a `chore`. For example,
  after `docs!: break` sets 1.0.0, an undetected amend `docs!: break again`
  with 2.0.0 is accepted, and one commit then moves 0.22.0 to 2.0.0.
- The assessment left abbreviated flags such as `--amen` undetected. Git
  accepts `--am`, `--ame` and `--amen` as `--amend`, so, given the risk above,
  the hook recognizes them too, and `--no-am`, `--no-ame` and `--no-amen` as
  `--no-amend`. Only an amend whose arguments cannot be read stays undetected.

## Follow-ups

- None.
