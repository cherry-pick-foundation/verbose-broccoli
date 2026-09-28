---

description: "Task list for ShellCheck"
---

# Tasks: ShellCheck

**Input**: Design documents from `specs/016-shellcheck/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: `scripts/doctor_test.ts` covers the new environment check. The
script fixes keep behavior, which the existing `test:git-flow`,
`test:worktree-branch` and `test:commit-msg` suites check. The shell check
itself is accepted by a clean run and a failing synthetic script (SC-002).

**Organization**: A Codex implementer owns T001 to T004; main (Claude Code)
owns the records, T005 and integration.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Pinned tool (US2)

- [x] T001 [US2] Create `tools/shellcheck/` as a uv project like
  `tools/spec-kit/` that pins `shellcheck-py` 0.11.0.1 in `uv.lock`; sync it
  in `orca.yaml`'s setup script (FR-001).
- [x] T002 [US2] In `scripts/doctor.ts`, check the `tools/shellcheck`
  environment the way it checks `tools/spec-kit`, with a case in
  `scripts/doctor_test.ts`; name ShellCheck in the `doctor` task description
  in `deno.json` (FR-001, SC-003).

## Phase 2: Check (US1)

- [x] T003 [US1] Add the root `.shellcheckrc` (FR-005) and a `lint:shell`
  task that runs the pinned ShellCheck on the scripts of FR-002 and not on
  `.specify/` (FR-004); add it to `check` (FR-003) and regenerate
  `docs/reference/commands.md`.
- [x] T004 [US1] Fix every finding in `scripts/worktree-branch.sh`,
  `scripts/git-flow-hooks/pre-flow-feature-finish` and
  `scripts/git-hooks/commit-msg` without changing behavior (FR-006).
- [x] T005 [P] [US1] In `docs/architecture.md`, name the shell check in the
  list of checks and describe the pinned tool next to `tools/spec-kit/`.
  - 2026-09-29: A Codex implementer (`gpt-6-luna`, max effort; Orca
    dispatch `ctx_74165f78c106`) did T001 to T004, committed after review
    as `91b4a35` (T004) and `d80dbdd` (T001 to T003). The owned scripts had
    one default finding, the finish hook's intended word splitting, now
    kept with a scoped directive, and 80 `require-variable-braces`
    findings. It reported `deno task check` and `deno task verify` passing,
    the SC-002 probe failing and then passing, and the doctor failing with
    the repair command without the environment. Main reran `lint:shell` and
    the SC-002 probe with the same results; `.specify/` is unchanged since
    `df912f4`. T005 is main's.

## Phase 3: Verification and review

- [x] T006 Run `deno task verify` (SC-001) and the acceptance runs of SC-002
  to SC-004.
  - 2026-09-29: `develop` at `7e4c92b` (CHE-27's merge) was merged in at
    `66c4a78` without conflicts, and `deno task verify` passed there. The
    document judgment step (`doc-regions:prepare -- --base develop
    --max-evidence-chars 20000`) sent 229 units in five `backfire_verify`
    requests: none was contradicted, the changed `docs/architecture.md`
    unit (27-54) was verified, and the three units flagged for review
    (`AGENTS.md` 51-52, `README.md` 1 and 8-10, all unchanged) are weak
    partial matches with the diff and stand. Two requests failed at the
    provider twice each and succeeded on the third try; the judgments used
    201,397 input and 71,089 output tokens. `doc-regions:audit` reported
    the same 19 MemoryLint `boundary` warnings on the constitution as
    earlier features; they are reported, not acted on.
- [ ] T007 Merge `develop`, verify, move CHE-30 to In Review, run the merge
  review, resolve findings, commit the review record, check that `develop`
  has not moved, and run `git flow feature finish shellcheck` in the
  `develop` worktree.
  - 2026-09-29: Backfire rated the code review medium, so a fresh Claude
    Code reviewer (`claude-sonnet-5`, high effort; Orca dispatch
    `ctx_03135c503913`) reviewed T001 to T004 at `08492d0` and approved,
    with one should-fix and one nit. A fresh Codex reviewer (`gpt-6-luna`,
    `max`; `ctx_e81551855653`) reviewed the documents and found one
    must-fix, two should-fix and one nit. Both reports are in the ignored
    `.local/reviews/016-develop-merge/`.
  - Fixes: `lint:shell` now passes NUL-delimited paths, so a script path
    with a space reaches ShellCheck whole (both reviews; Codex implementer
    `ctx_3b7b5f5d4271`, reviewed by main). The spec now records the guide's
    "When to use Shell" advice as left out, marks planning-time statements
    as such, and says `require-double-brackets` applies to Bash and Ksh.
    The code review's should-fix asked for evidence of SC-002 and SC-003 on
    the reviewed tip: main ran both at `08492d0`. The probe
    `scripts/shellcheck_probe.sh` failed `lint:shell` with SC2086 and the
    task passed after its removal; `deno task doctor` failed with "run uv
    sync --locked --project tools/shellcheck" while `tools/shellcheck/.venv`
    was moved aside and passed with `shellCheck` in sync once it was back.
    After the fix, a probe named `scripts/shellcheck probe.sh` failed the
    same way and the task passed after its removal.
  - 2026-09-29: `develop` moved to `8f1de1e` (CHE-27's vault topics
    merge) and was merged in at `e26dda5` without conflicts. There
    `deno task verify` passed, and its log shows the `lint:shell` step. The
    document judgment step, rerun there, sent 229 units in five
    `backfire_verify` requests: none was contradicted, and the changed
    `docs/architecture.md` unit (27-54) was verified. Nine units flagged
    for review are unchanged `docs/architecture.md` text (365-481 and
    571-574) with weak partial matches to the diff; they stand. Two
    requests failed at the provider and succeeded on retry; the judgments
    used 201,696 input and 64,218 output tokens. Next: the review record
    and the finish.

## Phase 4: After the finish

These run after the merge, so their evidence goes into CHE-30's completion
comment, not into this file.

- [ ] T008 Move CHE-30 to Done with one completion comment giving the merge
  commit, the review record and the record location.

## Dependencies

- T002 needs T001; T003 needs T001; T004 needs T003's configuration.
- T005 is independent of T001 to T004.
- T006 needs T001 to T005; T007 needs T006; T008 needs T007.

## Worker Assignment

- Codex implementer, `gpt-6-luna` at `max`: T001 to T004.
- Fresh Claude Code reviewer: the code in T007. Fresh Codex reviewer,
  `gpt-6-luna` at `max`: the documents in T007.
- Main: everything else.
