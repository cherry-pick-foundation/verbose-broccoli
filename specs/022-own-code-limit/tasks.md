---

description: "Task list for the own-code limit per feature"
---

# Tasks: Own-Code Limit per Feature

**Input**: Design documents from `specs/022-own-code-limit/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/own-code-check.md](contracts/own-code-check.md),
[quickstart.md](quickstart.md)

**Tests**: `scripts/own_code_test.ts` runs the check on synthetic Git
repositories (spec SC-001, SC-002; constitution V). Tests come before the
code they cover in each task.

**Organization**: Main (Claude Code) owns the Spec Kit records, the
`docs/architecture.md` prose of T007, reviews the Codex worker's diff and runs
the merge. One Codex worker (`gpt-6-luna`, max effort) implements T001 to
T006 and regenerates `docs/reference/` for T007, because every story lands
in the same script. A fresh Claude Code reviewer gives the develop merge review of the
code; a fresh Codex reviewer reviews the coordinator's records.

**Own-code budget**: This feature's own net change, as the check itself
reports it, stays within 300 lines (FR-012). The plan estimates about 75.

**Private data**: No task writes a student name or record into the
repository or into Orca or Linear messages.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Setup

- [x] T001 Pin scc: add `tools/scc/pyproject.toml` (`scc-bin==4.1.0`,
  Python `==3.14.*`, uv `==0.11.32`, `package = false`, like
  `tools/shellcheck/pyproject.toml`) and its `tools/scc/uv.lock`; sync it in
  `orca.yaml`'s setup script after `tools/ruff`; check its environment in
  `scripts/doctor.ts` with `checkUvEnvironment` like `tools/shellcheck`, name
  scc in the `//#doctor` description in `turbo.json`, and update
  `scripts/doctor_test.ts` (FR-010, FR-013; research.md R1).
- [x] T002 [P] Pin `linguist-languages` 9.5.0 as a root dev dependency in
  `package.json` and `package-lock.json` (FR-004; research.md R2).

---

## Phase 2: User Story 1 - A feature over the limit fails verification (P1) 🎯 MVP

**Goal**: `npm run verify` fails when the branch's own code grows by more
than 300 net lines against its merge base with `develop`.

**Independent Test**: In a synthetic repository, 300 net lines pass and 301
fail; a clean `develop` gives net 0.

- [x] T003 [US1] In `scripts/own_code_test.ts`, build synthetic Git
  repositories in temporary directories with a `develop` branch and a feature
  branch, run the check there, and assert: 300 net lines pass and 301 fail
  with the sizes, the net change and the limit in the output; 400 added and
  150 deleted give net 250 and pass; a clean `develop` gives net 0; an
  untracked, not ignored, file counts; a symbolic link does not; a repository
  without `develop` fails; and after passing and failing runs the synthetic
  repository's files, `git status` and index are unchanged and the run's
  temporary directory is gone (US1 scenarios 1 to 4, edge cases; FR-002,
  FR-008 to FR-011; constitution V).
- [x] T004 [US1] Add `scripts/own_code.ts` as
  [contracts/own-code-check.md](contracts/own-code-check.md) and
  [data-model.md](data-model.md) describe, using research.md R1, R2 and R5:
  merge base with `develop`, `git archive` into a temporary directory removed
  in a `finally` block, file lists from `git ls-tree` and `git ls-files`,
  scc's per-file JSON, Linguist's `programming` type; add the `own-code` and
  `test:own-code` scripts to `package.json` with Node's permission flags like
  the other checks, `//#own-code` to the `check` dependencies and
  `//#test:own-code` to the `test` dependencies in `turbo.json`, and the new
  files to `tsconfig.json` if its file list requires it (FR-001 to FR-004,
  FR-008 to FR-011).

**Checkpoint**: The limit works without approvals, test or upstream rules.

- 2026-09-30: A Codex worker (`gpt-6-luna`, max effort, started through
  Orca's terminal path) did T001 to T006 and the generated part of T007 in
  `16bd03f` and `b272b04`. The coordinator's review found the behavior right
  but the script at 137 code lines, about twice the plan's estimate; the same
  worker shortened it to 127 without changing behavior and added the
  deletion-only case in `9ab206a`. `npm run test:own-code` passes 15 tests,
  and `npm run verify -- --task che-42 --base 0bc0c63` ended VERIFIED on
  `9ab206a`. scc 4.1.0 reports the full path it was given in `Filename`, which
  the check relies on; the coordinator confirmed this by hand.

---

## Phase 3: User Story 2 - The user's recorded approval raises the limit (P1)

**Goal**: An approval line the branch adds raises that branch's limit.

**Independent Test**: With net 400, an added approval for 450 passes and one
for 320 fails.

- [x] T005 [US2] Test first in `scripts/own_code_test.ts`, then implement in
  `scripts/own_code.ts`: added `**Own-code limit**: <number>` lines under
  `specs/`, `.specify/bugs/` or `.specify/assessments/` raise the limit to
  their largest number and are named in the output; a line already at the
  merge base, a number at or below 300, and a matching line elsewhere do not
  raise it (US2 scenarios 1 to 3; FR-007; research.md R6).

---

## Phase 4: User Story 3 - Tests and upstream copies do not count (P2)

**Goal**: Tests, upstream copies and non-code files add nothing.

**Independent Test**: A 500-line test file and a 500-line file whose
SHA-256 is in an `UPSTREAM.md` add nothing; one changed byte makes the copy
count.

- [x] T006 [US3] Test first in `scripts/own_code_test.ts`, then implement in
  `scripts/own_code.ts`: files under `tests/` or named `*_test.*` or
  `*.test.*`; files whose SHA-256 appears in an `UPSTREAM.md`, an
  `upstream.json` or a `.specify/integrations/*.manifest.json` of the same
  tree; Markdown, JSON and other non-programming files; and a patched copy
  that counts in full (US3 scenarios 1, 2, 4 and 5; FR-003 to FR-006;
  research.md R3, R4).

---

## Phase 5: User Story 4 - The user sees the own-code size (P3)

**Goal**: The output and the records give the sizes.

- [x] T007 [US4] Describe the check in `docs/architecture.md` next to the
  other checks and tools, including the approval line and the upstream
  record rule, and regenerate `docs/reference/` with `npm run docs:generate`
  (FR-013).
- [x] T008 [US4] Run [quickstart.md](quickstart.md) steps 1, 2 and 4 and
  record here the own-code size of `develop` at 0bc0c63, this feature's own
  net change and the backfire rebuild's net change at 8a1d2f0 (US3 scenario
  3, US4; FR-012; SC-004 to SC-006).
  - 2026-09-30, measured by `npm run own-code` (scc code lines, neither
    blank nor comment):
    - `develop` at 0bc0c63: 18,418 own-code lines (SC-006). Spec Kit's
      extension scripts and Ponytail's hook modules have no recorded hashes
      and are part of this number.
    - This feature at `9ab206a`: net +129 of 300 allowed, 127 lines in
      `scripts/own_code.ts` and 2 in `scripts/doctor.ts` (FR-012, SC-005).
    - The backfire rebuild at 8a1d2f0, run in a temporary detached worktree
      with this branch's script: 18,344 lines at its merge base ae8cadf and
      in its tree, net +0, so none of its roughly 5,850 vendored
      jev-judge-mcp code lines counted (SC-004).
    - A temporary detached worktree of this branch with 172 extra code
      lines in a new TypeScript file: net +301 of 300, exit 1. After an added
      `**Own-code limit**: 450` line in `specs/022-own-code-limit/spec.md`:
      net +301 of 450 allowed, naming that file, exit 0 (SC-001, SC-002).
      Without `uv sync` of `tools/scc`, the check failed with uv's
      "Failed to spawn: scc" (FR-011); uv then created an empty
      `tools/scc/.venv`, which Git ignores.

---

## Phase 6: Verification and review

- [x] T009 Run `npm run verify` (SC-003).
  - 2026-09-30: `npm run verify -- --task che-42 --base 0bc0c63` ended
    VERIFIED on `28a60bd`. `develop` then moved to 63fe2fd, the license
    notices feature; the coordinator merged it in `1b2fd0d` without
    conflicts, the check still reported net +129 against the new merge base,
    and `npm run verify -- --task che-42 --base develop` ended VERIFIED on
    `1b2fd0d`.
- [ ] T010 Merge `develop`, fix new findings, verify, move CHE-42 to In
  Review, run the document judgment step (`npm run doc-regions:prepare --
  --base develop --max-evidence-chars <n>` and `npm run doc-regions:audit`)
  and act on it, run the merge review, resolve findings, commit the review record
  and run `git flow feature finish own-code-limit` in the `develop`
  worktree after checking that `develop` has not moved; then move CHE-42 to
  Done with one completion comment.
  - 2026-09-30: CHE-42 moved to In Review. The document judgment step ran at
    `1b2fd0d` against `develop` 63fe2fd: `npm run doc-regions:prepare --
    --base develop --max-evidence-chars 40000` printed 5 `backfire_verify`
    requests for 236 units and 1 `backfire_classify` request for the 6 units
    this feature added. A scratch MCP client outside the repository sent them
    to the repository's backfire server (`backfire serve-mcp`, `hive`
    profile, DeepSeek V4.1 Flash). No unit was contradicted: 11 verified and
    225 unsupported against this branch's diff. The seven
    `docs/architecture.md` units this feature changed were verified; 30-61
    at confidence 0.4, so it was flagged for review, and it stands because
    the diff supports the added own-code and scc wording. The other 16
    flagged units describe files this feature does not change, 10 of them in
    `AGENTS.md` and the constitution, which are report-only; they stand.
    `backfire_classify` put all 6 added units in agent regions, so no
    mechanical region is added. `npm run doc-regions:audit` reported the same
    19 MemoryLint `boundary` warnings on the constitution as earlier
    features; they are reported, not acted on. Paid provider calls: 9 (2 from
    `npm run backfire:ready`; 1 from a first client run whose result the
    client lost to its own error; 6 judgment calls, all without error).
  - 2026-09-30: Merge review at `1f98d53`, both reviewers fresh and started
    through Orca in the coordinator's child Run. The backfire judgment tools
    are not loaded in this session, so the code reviewer follows the last
    speed-favoring merge reviews' choice: a Claude Code worker on
    `claude-sonnet-5-5` at medium effort (dispatch `ctx_0b850f98f1d5`)
    approved with 0 blockers, 0 majors and 4 minors. A Codex worker
    (`gpt-6-luna`, max effort; dispatch `ctx_869a6812eb76`) reviewed the
    records and approved after fixes with 1 minor.
  - 2026-09-30: Resolution. Code minor 4, a renamed records file reviving an
    old approval, was a real gap; the implementing Codex worker keyed
    approvals by line text in `38a64d2` and added its test in `df6dc74`,
    with tests for code minors 2 (a line-counter failure fails) and 3
    (`develop` merged after the branch point adds nothing). Code minor 1,
    scc language names that Linguist's names do not match, stands as a known
    limit in research.md R2, since the repository has none of those
    languages. The records minor, that the spec said a missing scc
    environment names its install command, was corrected in `4e2a58b`,
    which also updated the approval rule in spec.md, research.md and
    data-model.md. The fixes change one line of the check, so the
    coordinator reviewed them instead of a new review round. The worker's
    `npm run verify` failed twice on backfire timing tests
    (`test_concurrent_sessions_share_records_without_interfering`, a
    5-second answer limit, and
    `test_each_tool_keeps_event_loop_lag_below_one_second`, 1.165 s) while
    the machine's 5-minute load average was about 17 on 8 processors; this
    branch changes nothing under `packages/`, and both tests passed alone
    (12 passed). The coordinator's `npm run verify -- --task che-42 --base
    develop` then ended VERIFIED on `df6dc74`: 18 own-code tests, net +129
    of 300 against 63fe2fd, 127 code lines in `scripts/own_code.ts`.

## Dependencies

- T001 and T002 come before T004. T003 comes before T004; T005 and T006
  follow T004 in the same two files. T007 follows T004. T008 follows T006.
- T009 follows T001 to T008; T010 follows T009.

## Parallel Opportunities

- T002 can run beside T001. Every other implementation task edits
  `scripts/own_code.ts` or its test, so they run in order in one worker.

## Implementation Strategy

T001 to T004 give the MVP: the limit without exemptions. T005 and T006 add
approvals and the exemptions. T004 already puts the check into
`npm run check`, and without T006 it would count this branch's test file, so
run `npm run verify` on the branch only after T006.
