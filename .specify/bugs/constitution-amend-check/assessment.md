# Bug Assessment: Commit-message check rejects amending a constitution commit

- **Slug**: constitution-amend-check
- **Created**: 2026-09-28
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-15> (Linear CHE-15,
  read with `orca linear issue CHE-15 --full --json`; host `linear.app`,
  allowlisted)
- **Verdict**: valid
- **Severity**: low

## Report (verbatim or summarized)

> `git commit --amend` on a commit that changes
> `.specify/memory/constitution.md` is refused by the commit-message hook. The
> constitution version rule (`scripts/constitution_version.ts`) compares the new
> version with the version at `HEAD`, which during an amend is the commit being
> replaced, instead of with that commit's parent.
>
> Expected: an amend is checked against the parent of the amended commit, so the
> version stays 1.0.0. The user prefers amending when a fix belongs to the same
> commit. Workaround used: `git reset --soft HEAD^`, then commit again.

## Symptom

Amending a commit that changed the constitution fails, because the hook expects
a second version bump on top of the commit being replaced. The amend should be
checked against that commit's parent and keep the version the commit already
set.

## Reproduction

Reproduced on 2026-09-28 in a scratch repository holding copies of `deno.json`,
`deno.lock`, `scripts/commitlint.config.mjs`, `scripts/constitution_version.ts`
and `scripts/git-hooks/commit-msg`, with `core.hooksPath` set to
`scripts/git-hooks` (git 2.53.0, Deno 2.9.6):

1. Commit a constitution at version 0.22.0 as `chore: seed`.
2. Change its text, set the version to 1.0.0, and commit it as `docs!: break`.
   The hook accepts it.
3. Change the text again, keep 1.0.0, stage it, and run
   `git commit --amend --no-edit`.
4. The hook refuses: "Constitution version 1.0.0 with commit type 'docs'
   requires 2.0.0; found 1.0.0. [local/constitution-version]". `HEAD` is
   unchanged.

## Suspected Code Paths

- `scripts/constitution_version.ts:109-130` — `constitutionVersionRule` reads
  the previous version from `HEAD` (`git ls-tree … HEAD` and
  `git show HEAD:<path>`). During an amend, `HEAD` is the commit being replaced,
  so its already bumped version becomes the baseline.
- `scripts/git-hooks/commit-msg:12` — runs commitlint with only the message
  file; nothing tells the rule that the commit is an amend.

## Root Cause Hypothesis

The rule assumes the new commit's parent is `HEAD`. That is false for
`git commit --amend`, whose parent is `HEAD`'s parent. Confidence: high; the
reproduction shows the exact message from the report.

Git gives a commit-msg hook no direct sign of an amend. A hook that dumped its
environment saw the same `GIT_*` variables for a new commit, for
`--amend --no-edit` and for `--amend -m`: `GIT_AUTHOR_*`, `GIT_EDITOR`,
`GIT_EXEC_PATH`, `GIT_INDEX_FILE`, `GIT_PREFIX` and the `GIT_CONFIG_*` pairs.
`prepare-commit-msg` receives `commit HEAD` for `--amend --no-edit` but only
`message` for `--amend -m`, and `commit HEAD` also for `git commit -C HEAD`,
which is not an amend. The hook's parent process is the `git commit` process,
and its argument list does contain `--amend`.

## Proposed Remediation

The approach is an open decision for the user (see Open Questions). The options:

- **Read git's arguments**: the sh hook reads its parent git process's arguments
  (`/proc/$PPID/cmdline`, split on NUL bytes; `ps -o args=` where `/proc` is
  missing). When `--amend` is present, it tells the rule to use `HEAD^` as the
  baseline instead of `HEAD`; an amended root commit has no baseline, so the
  check does not apply. About 10 lines. An abbreviated flag such as `--amen`
  keeps today's refusal.
- **Check history at verify**: drop the commit-time rule and have
  `deno task verify` check each constitution-changing, non-merge commit on the
  branch against its real parent. Exact for amends, but errors surface at verify
  instead of at commit, and the constitution's sentence "The repository's
  commit-message hook enforces this rule" must change.
- **Won't fix**: keep the check and the `git reset --soft HEAD^` workaround.

Rejected: a `prepare-commit-msg` marker (misses `--amend -m`), comparing
`GIT_AUTHOR_DATE` with `HEAD`'s author date (misses `--reset-author` and
`--date`), and accepting an unchanged version whenever `HEAD` changed the
constitution (lets a new follow-up commit skip its bump).

**Files likely to change** (reading git's arguments):

- `scripts/git-hooks/commit-msg`
- `scripts/constitution_version.ts`
- `scripts/commit_msg_test.ts`

**Tests to add or update**:

- A real amend of a breaking constitution commit that keeps 1.0.0 is accepted;
  this case fails without the fix.
- An amend that bumps again (1.0.0 to 2.0.0 under `!`) is refused.
- An amend of a commit that did not change the constitution still needs the bump
  its type requires.
- A new commit after a constitution commit still needs its own bump.

## Risks & Considerations

- Reading the parent process ties the hook to `git commit` running it directly;
  a wrapper process between them would hide `--amend` and fall back to today's
  refusal, never to a false acceptance.
- The fix must not accept a new commit that skips its bump, which the
  constitution's "exactly once per commit" rule forbids.

## Open Questions

- Resolved on 2026-09-28: the user chose reading git's arguments. (Asked the
  same day: read git's arguments, check history at verify, or won't fix?)
