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
