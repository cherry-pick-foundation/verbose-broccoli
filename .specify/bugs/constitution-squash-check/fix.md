# Bug Fix: Rebase fixup or squash can raise the constitution version more than once

- **Slug**: constitution-squash-check
- **Fixed**: 2026-09-28
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

`git flow feature finish` now checks every non-merge feature commit that
changes the constitution, so a commit that raises its version more than once
cannot reach `develop`, however it was made. The `pre-flow-feature-finish` hook
pipes each such commit's message to commitlint with
`CONSTITUTION_VERSION_COMMIT` set to the commit. In that mode the version rule
compares the commit with its parent, and the commitlint configuration applies
only that rule, with default ignores off. The constitution names the new check,
in wording the user chose (see Deviations from Assessment).

## Changes

| File | Change | Notes |
|------|--------|-------|
| `scripts/git-flow-hooks/pre-flow-feature-finish` | modified | After the review-record checks and before verification, lists the commits with `git rev-list --no-merges --full-history "$base..$branch" -- .specify/memory/constitution.md` and checks each one; refuses the finish if the list fails or a commit fails. |
| `scripts/constitution_version.ts` | modified | With `CONSTITUTION_VERSION_COMMIT` set, compares `<commit>^` with `<commit>` instead of `HEAD` or `HEAD^` with the index. |
| `scripts/commitlint.config.mjs` | modified | With the variable set, only `local/constitution-version` and `defaultIgnores: false`. |
| `scripts/git-hooks/commit-msg` | modified | Unsets the variable, so an inherited value cannot change the commit-time check. |
| `scripts/git_flow_test.ts`, `scripts/commit_msg_test.ts`, `deno.json` | tests | Real rebases and finishes; `test:git-flow` may now read the commitlint files and `HOME` and `DENO_DIR`. |
| `docs/architecture.md`, `specs/006-governance-policies/contracts/review-record.md`, `specs/006-governance-policies/contracts/commit-message.md` | modified | Describe the check and why commit time is not enough. |
| `.specify/memory/constitution.md` | modified | One clause each in the feature-finish sentence and in Governance, version 1.0.1 and a new Sync Impact Report, in its own `docs` commit. |

## Diff Highlights (optional)

Commits `a89e26f` (the fix) and `87be437` (the constitution). The combined
commits of `git rebase -i` `fixup` and `squash` keep a normal header, so the
rule refuses the double bump. A `fixup!` or `Revert` message has no type the
rule accepts, so a commit with one that changes the constitution is refused
too, which the constitution's rule already requires ("commits of other types
do not change this document").

## Tests Added or Updated

- `scripts/git_flow_test.ts`:
  - "fixup rebase that raises the constitution twice is refused" and "squash
    rebase that raises the constitution twice is refused": two `docs` commits
    (1.0.0 to 1.0.1 to 1.0.2) combined by a real `git rebase -i`, then a review
    record; the finish is refused, the message names the combined commit, and
    no ref, worktree or file changes.
  - "unsquashed fixup commit that changes the constitution is refused": a
    `git commit --fixup` commit that raises 1.0.1 to 1.0.2.
  - "one correct constitution bump still finishes".
- `scripts/commit_msg_test.ts`, "inherited commit ref does not replace the
  index check": with `CONSTITUTION_VERSION_COMMIT` naming an earlier commit in
  git's environment, a new `docs!` commit is still checked against the index.

The first three and the `commit-msg` case fail without the fix; see
[test.md](./test.md).

## Local Verification

- Reported by the implementing Codex worker (gpt-6-luna, max effort; Orca
  dispatch `ctx_e69720b35743`): the three refusal cases failed before the hook
  change because the finish succeeded; afterwards `deno task test:git-flow`
  (20 tests) and `deno task test:commit-msg` (5 tests) passed, and so did
  `format:check`, `lint`, `typecheck`, `docs:check` and
  `deno task verify --task CHE-17`.
- Coordinator: see [test.md](./test.md).

## Deviations from Assessment

- The assessment left the constitution text open. The coordinator asked
  through Orca (`ask` messages `msg_2368ad3398ae` and `msg_54068ebb5116` in
  the develop session's Run `run_8b222073b123`), and the develop session
  relayed the answers to the coordinator on 2026-09-28 (status messages
  `msg_26464522f733` and `msg_f82b4ad41489` in the same Run). The user's answer to
  the first, verbatim: "(A) add one short clause in each of the two places
  (the finish hook's refusal list under Development Workflow, and the
  enforcement sentence under Governance) in a docs commit, raising the version
  1.0.0 to 1.0.1. Keep the wording to what the new check does; add nothing
  else." The second asked about the Sync Impact Report; the develop session
  answered from the Spec Kit procedure, which produces a new report with each
  update (`plugins/code/skills/speckit-constitution/SKILL.md:110`), so the
  report was rewritten for this change.
- The rule now checks for a git failure on the commit's side before it decides
  that the check does not apply, so a failed `git ls-tree` refuses instead of
  passing. For the index the result is the same as before.

## Follow-ups

- Merge commits are still not checked: a conflict resolution in a merge of
  `develop` into a feature that changes the constitution is not caught.
- At commit time, commitlint still ignores some messages, such as `fixup!`,
  `squash!`, `amend!`, `Revert` and `Reapply` messages, so such a commit that
  changes the constitution is only refused at finish.
- Releases and hotfixes are finished by hand, so the new check does not run
  for them: a double bump made on a release or hotfix branch reaches `develop`
  unless the review before the merge into `main` catches it. The develop merge
  review reported this; the check was scoped to the feature finish hook, as
  CHE-17 and the user's constitution wording ask.
