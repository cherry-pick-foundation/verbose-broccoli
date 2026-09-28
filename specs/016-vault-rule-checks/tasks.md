---

description: "Task list for vault page rule checks"
---

# Tasks: Vault Page Rule Checks

**Input**: Design documents from `specs/016-vault-rule-checks/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [contracts/page-rules.md](contracts/page-rules.md),
[quickstart.md](quickstart.md)

**Tests**: Required. The root `AGENTS.md` asks for tests with every code
change, and the brief asks for failing-then-passing tests for each new
check: T001's and T003's cases are committed and seen failing before the
code that makes them pass.

**Organization**: Main (Claude Code) owns the Spec Kit records, the schema
template, the documents, `deno.json`, `orca.yaml`, and every write outside
the repository. A Codex worker owns the code, the tests and the package
metadata. `WC` is `packages/wiki-consistency`, `SRC` is
`packages/wiki-consistency/src/wiki_consistency` and `TESTS` is
`packages/wiki-consistency/tests`.

**Private data**: The `work` vault and the roster hold student data. No
task reads the vault's pages or prints roster rows, and no task writes a
student name, roster row or real vault content into the repository, Orca or
Linear. Tests use synthetic names from
`scripts/backfire/fixtures/education-roster-v1.csv` or backfire's tests;
main checks new fixtures against the real roster by count only before the
merge review.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Shared span finder and dependency

- [ ] T001 [US1] [US2] In `packages/backfire/tests/test_education_pseudonymize.py`,
  add cases for a public span finder in `backfire_education.pseudonymize`
  (research R4): roster spans with their kinds (student, given, guardian,
  school), phone and email spans, and overlap merging, matching what
  `pseudonymize` replaces today. Commit the cases failing, then move the
  `spans` closure to that module-level function, leaving `pseudonymize`'s
  behavior and existing tests unchanged, and commit the move.
- [ ] T002 [US1] Add `backfire[education]` as a path dependency of `WC`
  (`../backfire`, editable, as `doc-regions` is), update `WC/uv.lock`, and
  confirm `uv sync --locked --project WC` and the built work plugin's
  offline install in `packages/backfire/tests/test_build.py` (research R3).

## Phase 2: The rules (US1 to US3)

- [ ] T003 [US1] [US2] [US3] In `TESTS/conftest.py`, set `XDG_CONFIG_HOME`
  to a temporary folder for every test, so no test can read the user's
  roster. In a new `TESTS/test_rules.py`, add cases for every rule of the
  [contract](contracts/page-rules.md) through `lint.check`: for each rule,
  failing pages with the page, line and rule named and no matched text in
  the message, and close passing cases; mechanical regions and the
  `sources` field ignored; the roster read only when the contract says,
  and a missing, malformed or relative-path roster configuration failing
  with its file named; the roster and vault unchanged after the check
  (SC-004). Commit the cases and record in this file how many fail per
  rule before T004.
- [ ] T004 [US1] [US2] [US3] Implement `SRC/rules.py` as the contract says,
  using `load_roster`, T001's span finder, `doc_regions.regions.scan`,
  PyYAML node positions, `unicodedata` and `datetime`, and add its problems
  in `SRC/lint.py`'s `check` (research R1, R2, R5 to R8). T003's cases and
  the rest of `deno task test:wiki-consistency` and `deno task
  test:backfire` pass. Measure `check` on a synthetic vault of 500 pages
  and a 100-row synthetic roster and record the time here (SC-003).

## Phase 3: Documents and environments (US4)

- [ ] T005 [P] [US4] In `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  state how student pages are laid out, which rules `check` enforces, and
  the rules left to judgment (FR-014).
- [ ] T006 [P] [US4] In `plugins/work/skills/wiki-consistency/SKILL.md`,
  `docs/architecture.md` and `docs/examples/wiki/AGENTS.md`, describe the
  new rules the same way (FR-015), and in the skill's install steps sync
  `../../backfire` with its `education` extra before `wiki-consistency`.
- [ ] T007 [P] In `deno.json`'s `wiki-consistency:install` and `orca.yaml`'s
  setup, sync `packages/backfire` with its `education` extra before
  `packages/wiki-consistency`, and name it in `docs/architecture.md`'s
  install bullet.

## Phase 4: Verification and review

- [ ] T008 Run `deno task test:wiki-consistency`, `deno task test:backfire`
  and `deno task verify`; check the feature's files against the real roster
  by count only (no overlap) and confirm that no vault, roster or
  configuration file changed (FR-016, FR-017, SC-005).
- [ ] T009 Run the document judgment step as feature 015's T009 did for
  the changed template, skill and documents; correct or record each
  contradicted or flagged unit.
- [ ] T010 Merge `develop`, verify, move CHE-26 to In Review, run the merge
  review (a fresh Claude Code reviewer for T001 to T004, a fresh Codex
  reviewer for the documents), resolve findings, commit the review record,
  check that `develop` has not moved, and run
  `git flow feature finish vault-rule-checks` in the `develop` worktree.
- [ ] T011 Move CHE-26 to Done with one completion comment giving the merge
  commit, the review-record commit and the record location.

## Dependencies

- T002 needs T001's function only for T004; T003 needs T002's environment.
- T004 follows T003. T005 to T007 are independent of Phase 1 and 2.
- T008 needs T001 to T007; T009 needs T005 and T006; T010 needs T008 and
  T009; T011 needs T010.

## Parallel execution

- Codex worker: T001 to T004 (`packages/backfire` span finder and its test,
  `WC`).
- Main, meanwhile: T005 to T007.

## Implementation strategy

US1 to US3 share one module and one test file and ship together; US4's
documents describe them. The `work` vault fails the new rules until CHE-28
commits its rewrite; this feature changes no vault.
