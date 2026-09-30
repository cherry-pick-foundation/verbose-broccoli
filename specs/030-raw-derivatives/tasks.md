---

description: "Task list for Raw derivatives"
---

# Tasks: Raw derivatives

**Input**: Design documents from `specs/030-raw-derivatives/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[removals.md](removals.md)

**Tests**: No code changes. The vault's `raw_import.py verify` and
`wiki-consistency check`, and the repository's `npm run verify`, accept the
work (SC-001 to SC-004).

**Organization**: A Claude Code implementer owns T003 to T006; a Codex
worker owns T002; main owns the records, the commits and integration.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Checked list (US1)

- [x] T001 [US1] List the 43 bags (bag path and source path) in
  [removals.md](removals.md) from their `Internal-Sender-Identifier`.
- [x] T002 [US1] Check the list against CHE-59's categories, read-only
  (FR-002). All 43 rows match their bags and categories, no keep-item is
  listed, and each source has one revision. The checker named 15 ggcj-h
  per-question mock-exam vocabulary PDFs as doubtful; CHE-59 does not list
  them, so they stay.

## Phase 2: Vault (US1, US2)

- [x] T003 [US2] Repoint or drop every citation and link in
  `wiki/sources/local-materials.md` and the student pages that reaches a
  removed file or a trashed worksheet folder (FR-004).
- [x] T004 [US1] Remove the 43 bag folders and run `verify` (FR-001).
- [x] T005 [US1] [US2] Run `update` and `check` until only CHE-58's findings
  remain, and append the removal's log entry (FR-003, FR-005). Result:
  `verify` counts 150 bags with none invalid; `check` reports only CHE-58's
  106 phone, 2 date and 1 English findings. Six pages changed: 50 source
  citations dropped, 5 added for the original mock papers, and 73 catalog
  rows removed, 62 of them links into the trashed worksheet folders.

## Phase 3: Rule (US3)

- [x] T006 [P] [US3] Add the derivative rule to the skill's steps 1 and 4,
  the schema template and the four vault schemas (FR-006, FR-007).

## Phase 3b: Original sources only (FR-008, FR-009)

- [x] T010 [US2] Replace or drop the page links to the selected passage and
  word lists, the AI-written teaching analyses and the midterm-scope text's
  own copy (FR-008).
- [ ] T011 [US2] Replace or drop the page links to Markdown text
  extractions, the earlier Wiki build's process records, the older student
  notes and the midterm scope decision record (FR-008).
- [ ] T012 [US2] Drop the vocabulary-test registry's links and add a
  vocabulary test plan section to each of the 9 student pages it covers
  (FR-009).

## Phase 4: Integration

- [ ] T007 Review each diff, commit the repository and each vault, merge
  `develop`, run `npm run verify`, and pass the `develop` merge review.
- [ ] T008 Finish into `develop` with `git flow feature finish`.

## Phase 5: After the finish

These run after the merge, so their evidence goes into CHE-59's completion
comment, not into this file.

- [ ] T009 Move CHE-59 to Done with one completion comment giving the merge
  commit, the vault commit and the record location.

## Dependencies

- T004 needs T002. T005 needs T003 and T004.
- T006 is independent of T002 to T005.
- T010, T011 and T012 need T003 and run in that order.
- T007 needs T002 to T006 and T010 to T012; T008 needs T007; T009 needs T008.

## Worker Assignment

- Codex `gpt-6-luna` at `high` (backfire 0.45, confidence 0.37): T002.
- Claude Code `claude-sonnet-5-5` at `high` (backfire 0.29, confidence
  0.19): T003 to T006 and T010 to T012, in one reused terminal.
- Main: everything else.
