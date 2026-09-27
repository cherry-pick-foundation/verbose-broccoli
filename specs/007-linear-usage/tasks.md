---

description: "Task list for Linear usage through Orca"
---

# Tasks: Linear Usage Through Orca

**Input**: Design documents from `specs/007-linear-usage/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required for the one code change (the workflow instruction); the
preset and the prose are checked by the quickstart commands.

**Organization**: Tasks are grouped by user story. Main (Claude Code) writes
every change itself, since the change is small; so a fresh Codex agent reviews
it at the `develop` merge (root `AGENTS.md`, "Review"). Only main writes to
Linear.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US6)

---

## Phase 1: Setup

- [ ] T001 In this worktree run `deno task backfire:install` (develop now has
  `packages/backfire`, which `deno task check` tests) and `deno task workflow
  --task linear-usage --base 8ab332b`; confirm `deno task verify --task
  linear-usage --base 8ab332b` passes before any change.

---

## Phase 2: User Story 1 - Each feature or bug is one Linear issue that the repository can find (Priority: P1) 🎯 MVP

**Goal**: New specs ask for the issue line; every agent knows only main writes
to Linear.

**Independent Test**: The resolved spec template ends with the Linear line;
`AGENTS.md` has the approved rule; features 007 to 010 each have one issue,
one linked worktree and one spec line (SC-001).

- [ ] T002 [P] [US1] Create the preset source outside the repository
  (`preset.yml` with one `append` layer for `spec-template`, and
  `templates/spec-template.md` holding the comment and the line
  `**Linear issue**: [CHE-###]` described in [research.md](research.md) R2),
  install it with `uv run --project tools/spec-kit specify preset add --dev
  <source>`, and commit `.specify/presets/.registry` and
  `.specify/presets/linear-issue/`. Check with `specify preset resolve
  spec-template` and `.specify/scripts/bash/resolve-template.sh
  spec-template`.
- [ ] T003 [US1] Add under "Records" in the root `AGENTS.md` the approved
  line: "Only the main agent writes to Linear. It creates one issue per
  feature or bug, without sub-issues, after searching for similar ones; other
  agents report out-of-scope bugs to it through Orca messages."
- [ ] T004 [US1] SC-001: confirm CHE-5 to CHE-8 exist, each linked worktree
  names its issue, and each of the four specs has exactly one Linear line
  (run after 010's spec is committed).

---

## Phase 3: User Story 2 - Merging into `develop` completes the issue in a fixed order (Priority: P1)

**Goal**: The completion order reaches the main agent before completion.

**Independent Test**: `deno task test:workflow` passes with a test that every
mode prints the Linear instruction.

- [ ] T005 [P] [US2] In `scripts/workflow.ts`, add to
  `buildWorkModeInstructions` the instruction in [research.md](research.md) R3
  for every mode; in `scripts/workflow_test.ts`, test that DIRECT, DELEGATE,
  PARALLEL and REVIEW each print it with "main agent only", "In Review",
  "Done", "merge commit" and "record location". Run `deno task
  test:workflow`.

---

## Phase 4: User Story 3 - Nothing private reaches Linear (Priority: P1)

**Goal**: Every agent reads the privacy rule.

**Independent Test**: `grep -n Linear AGENTS.md` shows the privacy line.

- [ ] T006 [US3] Add under "Records" in the root `AGENTS.md`, before T003's
  line: "Treat Linear issues and comments as writing to an external service:
  never put operational data such as student records, or secret values, in
  them." (depends on nothing; same file as T003, so not parallel with it)

---

## Phase 5: User Story 4 and User Story 5 - The free plan keeps working; Linear only through Orca (Priority: P2)

**Goal**: Configuration matches the decisions.

**Independent Test**: Quickstart "SC-005" and "SC-006" sections.

- [ ] T007 [US4] Outside the repository, ask the user to set Team Settings >
  Issue statuses & automations > auto-archive to 1 month for team
  `cherry-pick-foundation` (R5), and record the answer here.
- [ ] T008 [P] [US5] Confirm no Linear plugin is enabled in Claude Code's or
  Codex's saved configuration and no Linear extension is in
  `.specify/extensions.yml`; record the result.

---

## Phase 6: User Story 6 - A reader at HEAD can learn how the repository uses Linear (Priority: P3)

**Goal**: One explanation for readers.

**Independent Test**: The section answers SC-003's four moments.

- [ ] T009 [US6] Add "Linear — 2026-09-27" to `docs/architecture.md` after
  "Commit messages" (team, labels, life cycle with the commands of
  [contracts/linear-lifecycle.md](contracts/linear-lifecycle.md), limit and
  archiving, where each rule lives), and name the `linear-issue` preset in
  "Spec Kit extensions — 2026-09-27". Run `deno task docs:check`.

---

## Phase 7: Polish and Integration

- [ ] T010 Run the quickstart's repository checks and `deno task verify
  --task linear-usage --base 8ab332b`; rerun `deno task workflow` with the
  same task and base; repair until both pass.
- [ ] T011 Merge review for `develop`, favoring speed: a fresh Codex reviewer
  gets only the scope (this branch against `develop`) and the requirements
  (spec FR-001 to FR-014 and SC-003); as part of it, the reviewer does
  SC-003's walkthrough from the repository at the feature tip. Resolve
  actionable findings and rerun affected checks.
- [ ] T012 Commit the record in this file, move CHE-5 to In Review, add the
  review-record commit, finish with `git flow feature finish linear-usage`
  from the `develop` worktree, then move CHE-5 to Done with one completion
  comment naming the merge commit and `specs/007-linear-usage/` (SC-002).

---

## Dependencies & Execution Order

- T001 first.
- T002, T005 and T008 are independent ([P]); T006 then T003 (same file); T009
  after T002, T003, T005 and T006, so it describes what exists.
- T004 waits for feature 010's spec commit. T007 waits for the user.
- T010 needs T002, T003, T005, T006 and T009; T011 needs T010; T012 needs
  T011, T004 and T007's answer or its recorded absence.

## Implementation Strategy

1. Setup (T001).
2. Carriers: T002, T005, T006, T003, then the documentation T009.
3. Checks (T004, T008, T010), the user's setting (T007).
4. Merge review, record, finish and Linear completion (T011, T012).
