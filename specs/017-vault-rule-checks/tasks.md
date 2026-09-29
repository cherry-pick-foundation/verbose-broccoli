---

description: "Task list for vault page rule checks"
---

# Tasks: Vault Page Rule Checks

**Input**: Design documents from `specs/017-vault-rule-checks/`

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

- [x] T001 [US1] [US2] In `packages/backfire/tests/test_education_pseudonymize.py`,
  add cases for a public span finder in `backfire_education.pseudonymize`
  (research R4): roster spans with their kinds (student, given, guardian,
  school), phone and email spans, and overlap merging, matching what
  `pseudonymize` replaces today. Commit the cases failing, then move the
  `spans` closure to that module-level function, leaving `pseudonymize`'s
  behavior and existing tests unchanged, and commit the move.
- [x] T002 [US1] Add `backfire[education]` as a path dependency of `WC`
  (`../backfire`, editable, as `doc-regions` is), update `WC/uv.lock`, and
  confirm `uv sync --locked --project WC` and the built work plugin's
  offline install in `packages/backfire/tests/test_build.py` (research R3).
  - 2026-09-29: A Codex worker (`gpt-6-luna`, `max`; Orca dispatch
    `ctx_e39d83fa019a`) committed T001's cases in `c648c0e`, where 9 new
    cases failed, then moved the finder to `compile_roster_pattern` and
    `find_spans` in `dc8b679`. T002 is `5028f2e`; the built plugin's
    install test now syncs backfire before `wiki-consistency`. Afterwards
    169 wiki-consistency and 1,360 backfire tests passed (3 deselected), and
    `deno task verify` passed with Node 24.19.0 first on `PATH`, because the
    mise `node` shim failed. Main reviewed the diff. Next: T003 and T004 in
    the same terminal (`ctx_276b91ba0ade`).

## Phase 2: The rules (US1 to US3)

- [x] T003 [US1] [US2] [US3] In `TESTS/conftest.py`, set `XDG_CONFIG_HOME`
  to a temporary folder for every test, so no test can read the user's
  roster. In a new `TESTS/test_rules.py`, add cases for every rule of the
  [contract](contracts/page-rules.md) through `lint.check`: for each rule,
  failing pages with the page, line and rule named and no matched text in
  the message, and close passing cases; mechanical regions, the `sources`
  field and `log.md` ignored; student pages found only directly in
  `wiki/students/`; the roster read only when the contract says,
  and a missing, malformed or relative-path roster configuration failing
  with its file named; the roster and vault unchanged after the check
  (SC-004). Commit the cases and record in this file how many fail per
  rule before T004.
- [x] T004 [US1] [US2] [US3] Implement `SRC/rules.py` as the contract says,
  using `load_roster`, T001's span finder, `doc_regions.regions.scan`,
  PyYAML node positions, `unicodedata` and `datetime`, and add its problems
  in `SRC/lint.py`'s `check` (research R1, R2, R5 to R8). T003's cases and
  the rest of `deno task test:wiki-consistency` and `deno task
  test:backfire` pass. Measure `check` on a synthetic vault of 500 pages
  and a 100-row synthetic roster and record the time here (SC-003).
  - 2026-09-29: The same worker (`ctx_276b91ba0ade`) committed T003's cases
    in `5d1c8e6`: 18 of them failed before T004 (phone 2, email 1,
    id-number 1, address 1, student-roster 1, english 4, school 2, date 2,
    time 1, roster configuration 4; the Hangul school case counts for both
    english and school). T004 is `6a17e1a`. Afterwards 213 wiki-consistency
    and 1,360 backfire tests passed, and `check` of 500 synthetic pages with
    a 100-row roster took 4.6 seconds with all files unchanged. Main's
    review found two defects: `english` named only the first offending line
    of a page, and a zone such as `(UTC+09:00)` failed `time` because its
    minutes read as a second time. The worker fixed both, test first
    (`ctx_b920c283f91f`): `007859f` holds four cases that failed, and
    `eec5d4b` the fix. Then 217 wiki-consistency tests passed and
    `deno task verify` passed. Main reran the review cases. Next: T008.

## Phase 3: Documents and environments (US4)

- [x] T005 [P] [US4] In `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  state how student pages are laid out, which rules `check` enforces, and
  the rules left to judgment (FR-014).
- [x] T006 [P] [US4] In `plugins/work/skills/wiki-consistency/SKILL.md`
  and `docs/architecture.md`, describe the new rules the same way, and in
  `docs/examples/wiki/AGENTS.md` state the student page layout (FR-015); in
  the skill's install steps sync `../../backfire` with its `education`
  extra before `wiki-consistency`.
- [x] T007 [P] In `deno.json`'s `wiki-consistency:install` and `orca.yaml`'s
  setup, sync `packages/backfire` with its `education` extra before
  `packages/wiki-consistency`, and name it in `docs/architecture.md`'s
  install bullet.
  - 2026-09-29: Main wrote T005 to T007 in `dbb2751`.

## Phase 4: Verification and review

- [x] T008 Run `deno task test:wiki-consistency`, `deno task test:backfire`
  and `deno task verify`; check the feature's files against the real roster
  by count only (no overlap) and confirm that no vault, roster or
  configuration file changed (FR-016, FR-017, SC-005).
  - 2026-09-29: Main merged `develop` at `3627cb2` (CHE-30's ShellCheck)
    cleanly in `3df9a79`, synced the environments that Orca's setup lists,
    and `deno task verify --task CHE26-vault-rule-checks --base 8f1de1e`
    passed (VERIFIED, REVIEW mode), with Node 24.19.0 first on `PATH`. The
    feature diff's added lines hold no roster name, given name, school or
    guardian and no ASCII roster value, compared by count only. The `work`,
    `default` and `chat` vaults have no uncommitted changes; the `code`
    vault has another session's new pages, which this feature did not
    touch.
- [x] T009 Run the document judgment step as feature 015's T009 did for
  the changed template, skill and documents; correct or record each
  contradicted or flagged unit.
  - 2026-09-29: Prepare gave five `backfire_verify` requests (229 units of
    the constitution, `AGENTS.md`, `README.md`, `docs/architecture.md` and
    `docs/backfire.md`, with the feature diff as evidence) and one
    `backfire_classify` request; one more `backfire_verify` covered the
    seven changed units of the template, the skill and the example schema,
    with the spec's clarifications and requirements, the contract, the new
    code and the install task as evidence. Main ran them through the
    develop worktree's backfire package. No unit was contradicted. The
    changed architecture install bullet (234-238) was verified and
    classified as an agent region. Five of the seven template, skill and
    example units were verified; the skill's install commands and its
    `check` row were unsupported, since the evidence did not include the
    built plugin's layout or the unchanged checks, and stand. 24 units
    across the requests were flagged for review, each with a
    contradiction probability of 0.05 or less; this feature changes none
    but the install bullet. The judgments used 263,839 input and 111,836
    output tokens.
- [ ] T010 Merge `develop`, verify, move CHE-26 to In Review, run the merge
  review (a fresh Claude Code reviewer for T001 to T004, a fresh Codex
  reviewer for the documents), resolve findings, commit the review record,
  check that `develop` has not moved, and run
  `git flow feature finish vault-rule-checks` in the `develop` worktree.
  - 2026-09-29: Backfire rated the code review difficult (0.81) and the
    document review medium (0.65). A fresh Claude Code reviewer
    (`claude-opus-5-5`, high effort; Orca dispatch `ctx_753a93c3abc8`)
    reviewed the code at `03a33b8` and found 5 minor issues and 3 nits: a
    roster name touching an email hid it, `14:00 -15:30` passed without a
    zone, the date rule skipped any text in angle brackets, regions with
    malformed markers were skipped, many contract forms had no test, a stray
    quotation mark could open a quote, and the spec and contract disagreed on
    a Korean year and month; its ponytail pass listed about 19 lines to cut.
    Main tightened the contract and FR-012 in `b634d4c`; the Codex worker
    (`ctx_f61d32e7ba89`) added tests in `917b8a0`, 13 of which failed, and
    fixed the code in `3f1c472`. A follow-up Claude Code review
    (`ctx_b5975c6b85d6`) found every finding resolved and one nit in
    research R7, which main fixed. A fresh Codex reviewer (`gpt-6-luna`,
    `max`; `ctx_e8f24b0a5e9d`) reviewed the documents and found 1 major
    issue (the summaries did not say that `sources` is skipped), 2 minor
    and 1 nit; main fixed them in `b3beb20`. Its follow-up
    (`ctx_5c11bd0b75f9`) found them resolved and 2 new minor gaps (the
    summaries lacked the quote-mark pairs and the offset limits), which
    main added. Next: verify, the review record and the finish.
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
