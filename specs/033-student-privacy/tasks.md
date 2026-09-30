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

- [X] T007 Privacy review, read-only, by a reviewer from another provider,
  with its own leak test. Coordinator dispatches. Result: 181 leaks in 801
  synthetic cases in six groups (numbers as JSON numbers, meaning carried by
  field names, birth-date forms, house numbers beside road names, grade
  wordings, provider errors echoing request text); all 165 refusal checks
  passed. A fresh privacy review follows T008.
- [X] T008 Resolve findings; rerun `npm run verify`; commit. Coordinator.
  Commit `acd3a0a` fixes all six groups with tests that fail on the old
  source; the reviewer's script then reported 0 leaks in 801 cases, 55/55
  documented limits and 165/165 refusals, and `npm run verify` VERIFIED.
  A second, fresh Codex privacy review (`gpt-6-astra` xhigh, `jev_decide`
  0.97) of `5ac6e3d` then found four more leak classes (fields in Markdown
  markup, nested objects under a named field, English prose forms, compound
  road names): 102 exposures in 539 cases. Round two, Claude Code Opus at
  xhigh (`jev_decide` 0.58), closed them as classes and added a fail-closed
  refusal for labeled birth-date, address and student-number fields whose
  value stays; commit `e48e215`, both reviewers' scripts at 0 unexpected
  exposures, 63 new tests failing on the old source, `npm run verify`
  VERIFIED.

## Phase 4: User Stories 3-4, student pages (P2, after CHE-59)

- [X] T009 [US4] Fill the roster's `id` and `romanized` columns; ask the user
  before assigning numbers to students without one. Coordinator.
- [X] T010 [US4] Rename the vault's student pages to `s-<id>.md`, romanize
  names in pages, fix links, change the schema's naming rule; commit in the
  vault repository. Vault commit `7a62e7c`; `264548d` adds the user's
  allow-list of personal details (romanized name, school domain ID, school
  year, EduOK number as the file name).
- [X] T011 [US4] Wiki check and schema template for `s-<id>` names and no
  Hangul names; tests.
- [X] T012 [US3] Work plugin instructions for resolving Korean names to
  EduOK numbers; lookup tests in a Claude Code and a Codex session.

- [X] T015 Add the develop session's rule of 2026-09-30: workers and
  reviewers that read student data run only on Claude Code or Codex, never
  Copilot or OMP (`AGENTS.md` "Review", the model-choice reference, the work
  plugin's backfire reference); add the vendored district codes to
  `licenses/THIRD_PARTY_NOTICES.md`. Coordinator.

## Phase 5: Finish

- 2026-09-30: `develop` 4f12cb2 (CHE-63's kebab-case renames) merged in
  `3bda766`; four conflicts were renames against this branch's changes and
  kept both sides. `npm run verify` VERIFIED there (35 of 35 tasks) after
  removing untracked bytecode caches that the new name check flagged.
- Size: 3,700 changed lines against `develop` (1,054 generated region list,
  1,112 tests, 672 code, 514 specs, 316 documents). Not split: the gate's
  detectors, region list and tests protect student data only together, and
  Part 2's repository change is under 200 lines.
- Document judgment step against `develop`'s merge base: 262 units in 14
  `jev_verify` calls and 22 added units in 2 `jev_classify` calls. Backfire
  now refuses Hangul, so each Hangul run in the requests (Korean examples in
  the documents and the district names) was romanized with es-hangul first,
  the same way in claims and evidence, and the generated region list and the
  lockfile were left out of the evidence, which otherwise exceeded the
  provider's token limit. One low-confidence contradiction (0.11) found a
  real ambiguity in `docs/architecture.md` about which rule reads the front
  matter; fixed. 8 added units in `docs/backfire.md` were suggested as
  mechanical-region candidates and stay prose: no generator owns them. The
  audit's 20 findings concern the constitution's existing text, not this
  change, and go to the user unchanged.

- [ ] T013 Final review by a reviewer from the other provider; resolve
  findings. Coordinator. The develop merge review (Codex `gpt-6-luna`
  medium, `jev_decide` 0.88) of `5ac6e3d` asked for one change: a link
  leaving the Wiki made the page rules skip every page, an older shortcut;
  fixed in `74f8977` and approved on follow-up.
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
- T011-T012: Claude Code Sonnet at high effort (`jev_decide` 0.97,
  confidence 0.95). Commit `123ef16`; the new check finds no student-name or
  page-name problem in the vault, and 108 older findings (CHE-58) stay. The
  Korean lookup passed in a Claude Code session (Sonnet) and a Codex session
  (`gpt-6-luna`, read-only) for a given name with a particle and for a name
  two students share.
- T007: Codex `gpt-6-astra` at xhigh effort (`jev_decide` 0.57, confidence
  0.51, next `gpt-6-luna` xhigh at 0.34), read-only, with its own 801-case
  synthetic leak script.
- T008: Claude Code Sonnet at xhigh effort (`jev_decide` 0.83, confidence
  0.80).
- Only Claude Code and Codex candidates were offered for this feature,
  because its workers can reach student data.
