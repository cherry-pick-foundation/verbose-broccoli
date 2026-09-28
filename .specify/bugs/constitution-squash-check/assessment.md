# Bug Assessment: Rebase fixup or squash can raise the constitution version more than once

- **Slug**: constitution-squash-check
- **Created**: 2026-09-28
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-17> (Linear CHE-17,
  read with `orca linear issue CHE-17 --json`; host `linear.app`, allowlisted)
- **Verdict**: valid
- **Severity**: low

## Report (verbatim or summarized)

> The constitution says each commit that changes it raises its version exactly
> once, and that the commit-message hook enforces this. `git rebase -i` does
> not run the commit-msg hook for `fixup` or `squash`, so combining two commits
> that each raised the constitution's version produces one commit that raises
> it twice, and nothing refuses it.
>
> Expected: a commit that raises the constitution's version more than once is
> refused before it can reach `develop`, for example by `deno task verify` or
> the pre-finish hook checking each commit on the branch.

The develop merge review of CHE-15 found it; `.specify/bugs/constitution-amend-check/`
fixed only the `--amend` case and lists this one under Residual Risks.

## Symptom

`git rebase -i` can fold two commits that each raised the constitution's
version into one commit that raises it by two steps. No hook runs for the
combined commit, and `git flow feature finish` merges it into `develop`. Such a
commit should be refused before it reaches `develop`.

## Reproduction

Reproduced on 2026-09-28 in a scratch repository holding copies of `deno.json`,
`deno.lock`, `scripts/commitlint.config.mjs`, `scripts/constitution_version.ts`
and `scripts/git-hooks/commit-msg`, with `core.hooksPath` pointing at a copy of
the hook that also logs each run (git 2.53.0, Deno 2.9.6):

1. On `develop`, commit a constitution at version 1.0.0 as `chore: seed`.
2. On a feature branch, commit version 1.0.1 as `docs: first wording` and
   version 1.0.2 as `docs: second wording`. The hook runs twice and accepts
   both.
3. Run `GIT_SEQUENCE_EDITOR="sed -i '2s/^pick/fixup/'" git rebase -i develop`.
4. The rebase succeeds with one commit, `docs: first wording`, that moves the
   version from 1.0.0 to 1.0.2. The hook log still has two entries: the hook did
   not run.
5. The same with `squash` and `GIT_EDITOR=true` gives one commit with the
   message `docs: first wording`, body `docs: second wording`, and the same
   result.

Nothing later catches it. The `pre-flow-feature-finish` hook checks ancestry,
the review record and `deno task verify`
(`scripts/git-flow-hooks/pre-flow-feature-finish`), and `deno task check` has no
step that reads commit history.

A related case found during reproduction: commitlint's default ignores skip
messages that start with `fixup!`, `squash!`, `amend!` or `Revert `. Piping
`fixup! docs: first wording` or `Revert "docs: first wording"` into
`deno task commitlint` exits 0, while `Update stuff` exits 1. So a commit made
with `git commit --fixup` or `git revert` that changes the constitution is not
checked at commit time either, and can reach `develop` unsquashed.

## Suspected Code Paths

- `scripts/git-hooks/commit-msg` — the only place the version rule runs. Git's
  sequencer does not run it for `fixup` or `squash` (reproduction step 4).
- `scripts/constitution_version.ts:105-149` — `constitutionVersionRule` can
  only compare the index with `HEAD` or `HEAD^`, so it cannot check a commit
  that already exists.
- `scripts/commitlint.config.mjs` — keeps commitlint's default ignores, which
  skip `fixup!`, `squash!`, `amend!` and `Revert` messages before any rule runs.
- `scripts/git-flow-hooks/pre-flow-feature-finish` — the gate into `develop`,
  which does not look at the feature's commits.

## Root Cause Hypothesis

The version rule is enforced only when a commit is made, through the
`commit-msg` hook, and some commits are made without it: the combined commits
of `git rebase -i` `fixup` and `squash`, and commits whose messages commitlint
ignores. Nothing checks the commits again before they reach `develop`.
Confidence: high; the reproduction shows the hook not running.

## Proposed Remediation

**Preferred**: check each commit on the feature in the `pre-flow-feature-finish`
hook, the one gate every feature passes on its way into `develop`, reusing the
commit-message rule. Before verification, the hook lists the feature's
non-merge commits that change the constitution
(`git rev-list --no-merges --full-history "$base..$branch" --
.specify/memory/constitution.md`) and pipes each one's message to
`deno task --quiet commitlint` with `CONSTITUTION_VERSION_COMMIT` set to that
commit. With that variable set:

- `constitutionVersionRule` compares the file in `<commit>^` with `<commit>`,
  instead of `HEAD` or `HEAD^` with the index;
- `scripts/commitlint.config.mjs` applies only `local/constitution-version` and
  turns commitlint's default ignores off, so `fixup!` and `Revert` messages are
  checked too, and header rules already applied at commit time do not run
  twice.

A refusal names the commit and changes nothing, like the hook's other checks.
The `commit-msg` hook unsets the variable, so an inherited value cannot change
the commit-time check.

**Alternatives**:

- Check in `deno task verify`. `deno task check` has no base branch: CI runs it
  on a one-commit clone without `develop`, so it would need a hard-coded
  `develop` and a rule for when that ref is missing. Checking the whole history
  instead fails on commits from before the rule, such as `9f9b7d6`, a `build`
  commit that moved the version from 0.20.0 to 0.21.0.
- A Deno script that parses each message itself. It needs
  `conventional-commits-parser` as a direct dependency and repeats what
  commitlint already does.
- A rebase hook. Git has none that runs for each combined commit and can refuse
  it; `post-rewrite` runs after the rebase has finished.

**Files likely to change**:

- `scripts/git-flow-hooks/pre-flow-feature-finish`
- `scripts/constitution_version.ts`
- `scripts/commitlint.config.mjs`
- `scripts/git-hooks/commit-msg`
- `scripts/git_flow_test.ts`, `scripts/commit_msg_test.ts`, and the
  `test:git-flow` permissions in `deno.json`
- `docs/architecture.md`, `specs/006-governance-policies/contracts/review-record.md`
  and `specs/006-governance-policies/contracts/commit-message.md`

**Tests to add or update**:

- A feature whose two `docs` bumps were combined by a real `git rebase -i`
  `fixup`, and one combined by `squash`, is refused at finish and nothing
  changes. Without the fix the finish succeeds.
- A feature with an unsquashed `git commit --fixup` commit that changes the
  constitution is refused.
- A feature with one correct bump still finishes.
- The `commit-msg` hook ignores an inherited `CONSTITUTION_VERSION_COMMIT` and
  still checks the index.

## Risks & Considerations

- Each finish runs commitlint once per constitution-changing commit on the
  feature, about 0.2 s each (the `commit-msg` hook took 175 to 182 ms in
  CHE-15's tests).
- The check runs the rule from the `develop` worktree, where git-flow takes the
  hook from. So it applies from the first finish after this fix is on
  `develop`, not to this fix's own finish.
- Merge commits are not checked, so a conflict resolution that changes the
  constitution in a merge of `develop` into a feature is not caught.
- A refused commit has to be rewritten, which means a new review and review
  record.
- `scripts/git_flow_test.ts` sets `HOME` for git, so its temporary repositories
  need `DENO_DIR` and copies of the commitlint files to run the real rule.

## Open Questions

- The constitution's feature-finish sentence lists what the hook refuses, and
  its Governance section says the commit-message hook enforces the version
  rule. Neither mentions the new check. Whether to add it there is asked of the
  user.
