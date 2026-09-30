# Tasks: Student Privacy Gate

**Input**: [spec.md](spec.md) and [plan.md](plan.md) in
`specs/033-student-privacy/`

**Tests**: required; synthetic roster only, leak tests with a fake provider.

**Format**: `[ID] [P?] [Story] Description`; `[P]` tasks touch different
files and can run in parallel.

## Phase 1: Setup

- [X] T001 Write spec, plan and tasks; ask the user about the romanization
  convention (answered: customary surnames, Revised Romanization given
  names, written together). Coordinator.

## Phase 2: User Stories 1-2, the gate (P1)

- [ ] T002 [US1] Vendor the Ministry's legal-district code ZIP unmodified
  with its record, add `es-hangul` 2.4.0, write the region generator and its
  `--check` mode, generate `packages/backfire/src/backfire_education/regions.json`,
  and run the check in `npm run verify`.
- [ ] T003 [US1] In `packages/backfire/src/backfire_education/`: English
  stand-ins and prefix conversion (`table.py`), `id` and `romanized` columns
  (`roster.py`), the new detectors and the re-scan (`pseudonymize.py`);
  keep `session_select.py` and `wiki_consistency.rules` working.
- [ ] T004 [US1] [US2] Hangul refusal for both modes in
  `packages/backfire/src/backfire/providers.py`, new errors in
  `failures.py`.
- [ ] T005 [US1] [US2] Tests in `packages/backfire/tests/`: every kind and
  form in FR-002 to FR-008, academic years kept, English stand-ins, table
  conversion, region forms (`Jongno-gu`, `Gangneung-si`, `Pyeongtaek`,
  `North Chungcheong`, `Chungbuk`), leak tests through `_OrderProvider`,
  both refusals, stand-ins not refused by the re-scan, errors without
  matched text.
- [ ] T006 [US3] Documents and instructions as plan.md "Documents and
  instructions" lists.

## Phase 3: Review of Part 1

- [ ] T007 Privacy review, read-only, by a reviewer from another provider,
  with its own leak test. Coordinator dispatches.
- [ ] T008 Resolve findings; rerun `npm run verify`; commit. Coordinator.

## Phase 4: User Stories 3-4, student pages (P2, after CHE-59)

- [ ] T009 [US4] Fill the roster's `id` and `romanized` columns; ask the user
  before assigning numbers to students without one. Coordinator.
- [ ] T010 [US4] Rename the vault's student pages to `s-<id>.md`, romanize
  names in pages, fix links, change the schema's naming rule; commit in the
  vault repository.
- [ ] T011 [US4] Wiki check and schema template for `s-<id>` names and no
  Hangul names; tests.
- [ ] T012 [US3] Work plugin instructions for resolving Korean names to
  EduOK numbers; lookup tests in a Claude Code and a Codex session.

## Phase 5: Finish

- [ ] T013 Final review by a reviewer from the other provider; resolve
  findings. Coordinator.
- [ ] T014 Record, In Review, merge `develop`, `npm run verify`, review
  record, `git flow feature finish` when the develop session allows; Done
  with one completion comment. Coordinator.

## Workers

Recorded as they are dispatched.
