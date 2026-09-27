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

- [x] T001 In this worktree run `deno task backfire:install` (develop now has
  `packages/backfire`, which `deno task check` tests) and `deno task workflow
  --task linear-usage --base 8ab332b`; confirm `deno task verify --task
  linear-usage --base 8ab332b` passes before any change.
  - 2026-09-28: `backfire:install` built the ignored `.venv` on uv's managed
    CPython 3.14.4, which lacks `os.pidfd_open`, so `test:backfire` failed
    (Linear CHE-14, owned by `develop`). Rebuilt it with `uv sync --project
    packages/backfire --frozen --python /usr/bin/python3.14` (system
    3.14.4); 1233 backfire tests then passed.

---

## Phase 2: User Story 1 - Each feature or bug is one Linear issue that the repository can find (Priority: P1) 🎯 MVP

**Goal**: New specs ask for the issue line; every agent knows only main writes
to Linear.

**Independent Test**: The resolved spec template ends with the Linear line;
`AGENTS.md` has the approved rule; features 007 to 010 each have one issue,
one linked worktree and one spec line (SC-001).

- [x] T002 [P] [US1] Create the preset source outside the repository
  (`preset.yml` with one `append` layer for `spec-template`, and
  `templates/spec-template.md` holding the comment and the line
  `**Linear issue**: [CHE-###]` described in [research.md](research.md) R2),
  install it with `uv run --project tools/spec-kit specify preset add --dev
  <source>`, and commit `.specify/presets/.registry` and
  `.specify/presets/linear-issue/`. Check with `specify preset resolve
  spec-template` and `.specify/scripts/bash/resolve-template.sh
  spec-template`.
  - 2026-09-28: installed from a scratch source; `specify preset resolve
    spec-template` lists the core base and the `append` layer.
- [x] T003 [US1] Add under "Records" in the root `AGENTS.md` the approved
  line: "Only the main agent writes to Linear. It creates one issue per
  feature or bug, without sub-issues, after searching for similar ones; other
  agents report out-of-scope bugs to it through Orca messages."
- [x] T004 [US1] SC-001: confirm CHE-5 to CHE-8 exist, each linked worktree
  names its issue, and each of the four specs has exactly one Linear line
  (run after 010's spec is committed).
  - 2026-09-28: CHE-5 to CHE-8 exist (In Progress); Orca links
    feature-linear-usage, feature-doc-consistency, feature-wiki-storage and
    feature-wiki-consistency to them; each of specs 007 to 010 has exactly
    one `**Linear issue**` line.

---

## Phase 3: User Story 2 - Merging into `develop` completes the issue in a fixed order (Priority: P1)

**Goal**: The completion order reaches the main agent before completion.

**Independent Test**: `deno task test:workflow` passes with a test that every
mode prints the Linear instruction.

- [x] T005 [P] [US2] In `scripts/workflow.ts`, add to
  `buildWorkModeInstructions` the instruction in [research.md](research.md) R3
  for every mode; in `scripts/workflow_test.ts`, test that DIRECT, DELEGATE,
  PARALLEL and REVIEW each print it with "main agent only", "In Review",
  "Done", "merge commit" and "record location". Run `deno task
  test:workflow`.
  - 2026-09-28: `deno task test:workflow` passed (56 tests); no other
    instruction contains "main agent only", so the test fails without the
    line.

---

## Phase 4: User Story 3 - Nothing private reaches Linear (Priority: P1)

**Goal**: Every agent reads the privacy rule.

**Independent Test**: `grep -n Linear AGENTS.md` shows the privacy line.

- [x] T006 [US3] Add under "Records" in the root `AGENTS.md`, before T003's
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
  - 2026-09-28: not set. The user had never set the period and chose to
    finish without it; it stays pending for the user in Linear's UI (Team
    Settings > Issue statuses & automations). Until then Linear's own
    default applies.
- [x] T008 [P] [US5] Confirm no Linear plugin is enabled in Claude Code's or
  Codex's saved configuration and no Linear extension is in
  `.specify/extensions.yml`; record the result.
  - 2026-09-28: Claude Code's `enabledPlugins` has no Linear plugin,
    `~/.codex/config.toml` has no `linear@` entry, and
    `.specify/extensions.yml` installs only `agent-context`, `assess`, `bug`
    and `git`.

---

## Phase 6: User Story 6 - A reader at HEAD can learn how the repository uses Linear (Priority: P3)

**Goal**: One explanation for readers.

**Independent Test**: The section answers SC-003's four moments.

- [x] T009 [US6] Add "Linear — 2026-09-27" to `docs/architecture.md` after
  "Commit messages" (team, labels, life cycle with the commands of
  [contracts/linear-lifecycle.md](contracts/linear-lifecycle.md), limit and
  archiving, where each rule lives), and name the `linear-issue` preset in
  "Spec Kit extensions — 2026-09-27". Run `deno task docs:check`.

---

## Phase 7: Polish and Integration

- [x] T010 Run the quickstart's repository checks and `deno task verify
  --task linear-usage --base 8ab332b`; rerun `deno task workflow` with the
  same task and base; repair until both pass.
  - 2026-09-28: quickstart repository checks pass (two `AGENTS.md` lines,
    the resolved template ends with the Linear line, `deno task
    test:workflow` 56 passed, no Linear extension or plugin); `deno task
    verify` passed on the tree this note is committed in, with the CHE-14
    workaround from T001.
- [x] T011 Merge review for `develop`, favoring speed: a fresh Codex reviewer
  gets only the scope (this branch against `develop`) and the requirements
  (spec FR-001 to FR-014 and SC-003); as part of it, the reviewer does
  SC-003's walkthrough from the repository at the feature tip. Resolve
  actionable findings and rerun affected checks.
  - 2026-09-28: fresh Codex reviewer `gpt-6-sol` at high effort
    (backfire_classify rated the review medium, 0.55, with 0.33 on
    difficult) reviewed 8ab332b..099331d. Findings: the rule for Linear
    capabilities Orca lacks lived only in `docs/architecture.md` (fixed in
    f97c924: the workflow instruction carries it); the contract's label
    example contained shell pipes (fixed in c205b29); the auto-archive
    setting is unconfirmed (T007, left pending by the user's choice). SC-003
    walkthrough: three of four moments were found where agents read them;
    the fourth is the fixed finding.
- [ ] T012 Commit the record in this file, move CHE-5 to In Review, add the
  review-record commit, finish with `git flow feature finish linear-usage`
  from the `develop` worktree, then move CHE-5 to Done with one completion
  comment naming the merge commit and `specs/007-linear-usage/` (SC-002).
  - 2026-09-28: record committed; CHE-5 moved to In Review only after the
    review ran, not before it as FR-006 orders; finish next from the
    `develop` worktree.

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
