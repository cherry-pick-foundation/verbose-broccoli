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

- [X] T002 [US1] Vendor the Ministry's legal-district code ZIP unmodified
  with its record, add `es-hangul` 2.4.0, write the region generator and its
  `--check` mode, generate `packages/backfire/src/backfire_education/regions.json`,
  and run the check in `npm run verify`.
- [X] T003 [US1] In `packages/backfire/src/backfire_education/`: English
  stand-ins and prefix conversion (`table.py`), `id` and `romanized` columns
  (`roster.py`), the new detectors and the re-scan (`pseudonymize.py`);
  keep `session_select.py` and `wiki_consistency.rules` working.
- [X] T004 [US1] [US2] Hangul refusal for both modes in
  `packages/backfire/src/backfire/providers.py`, new errors in
  `failures.py`.
- [X] T005 [US1] [US2] Tests in `packages/backfire/tests/`: every kind and
  form in FR-002 to FR-008, academic years kept, English stand-ins, table
  conversion, region forms (`Jongno-gu`, `Gangneung-si`, `Pyeongtaek`,
  `North Chungcheong`, `Chungbuk`), leak tests through `_OrderProvider`,
  both refusals, stand-ins not refused by the re-scan, errors without
  matched text.
- [X] T006 [US3] Documents and instructions as plan.md "Documents and
  instructions" lists.

## Phase 3: Review of Part 1

- [ ] T007 Privacy review, read-only, by a reviewer from another provider,
  with its own leak test. Coordinator dispatches.
- [ ] T008 Resolve findings; rerun `npm run verify`; commit. Coordinator.

## Phase 4: User Stories 3-4, student pages (P2, after CHE-59)

- [X] T009 [US4] Fill the roster's `id` and `romanized` columns; ask the user
  before assigning numbers to students without one. Coordinator.
- [ ] T010 [US4] Rename the vault's student pages to `s-<id>.md`, romanize
  names in pages, fix links, change the schema's naming rule; commit in the
  vault repository. Done and staged; the commit waits for T011's check.
- [ ] T011 [US4] Wiki check and schema template for `s-<id>` names and no
  Hangul names; tests.
- [ ] T012 [US3] Work plugin instructions for resolving Korean names to
  EduOK numbers; lookup tests in a Claude Code and a Codex session.

- [X] T015 Add the develop session's rule of 2026-09-30: workers and
  reviewers that read student data run only on Claude Code or Codex, never
  Copilot or OMP (`AGENTS.md` "Review", the model-choice reference, the work
  plugin's backfire reference); add the vendored district codes to
  `licenses/THIRD_PARTY_NOTICES.md`. Coordinator.

## Phase 5: Finish

- [ ] T013 Final review by a reviewer from the other provider; resolve
  findings. Coordinator.
- [ ] T014 Record, In Review, merge `develop`, `npm run verify`, review
  record, `git flow feature finish` when the develop session allows; Done
  with one completion comment. Coordinator.

## Workers

- T002-T006: Claude Code Sonnet at high effort, chosen by backfire's
  `jev_decide` (probability 0.24, confidence 0.15; next Codex `gpt-6-astra`
  high at 0.23) over Codex `gpt-6-luna` and `gpt-6-sol` high and Claude Code
  Fable and Opus high. The first call's output was cut off in display, so the
  unchanged decision was called a second time; the second answer is used.
  Commits `a0b4f11`, `f43cb50`, `0031f76`, `547b725`; `npm run verify`
  VERIFIED. Two plan details changed with approval (plan.md "As built").
- T009-T010: Claude Code Sonnet at high effort (`jev_decide` 0.62, confidence
  0.57; next Codex `gpt-6-luna` high at 0.27). All 43 roster students had an
  EduOK number, so none was assigned; one name shared by two students was
  matched to their numbers by grade. 10 pages renamed, staged in the vault.
- Only Claude Code and Codex candidates were offered for this feature,
  because its workers can reach student data.
