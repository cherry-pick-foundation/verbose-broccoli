---

description: "Task list for topics in vault page metadata"
---

# Tasks: Topics in Vault Page Metadata

**Input**: Design documents from `specs/015-vault-topics/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. The root `AGENTS.md` asks for tests with every code
change; T001's new cases fail before T002 to T004.

**Organization**: Main (Claude Code) owns the Spec Kit records, the schema
template, `docs/architecture.md`, the skill, the document judgment step and
every write outside the repository. A Codex worker owns the code and tests.
`PKG` is `packages/wiki-consistency`, `SRC` is
`packages/wiki-consistency/src/wiki_consistency` and `TESTS` is
`packages/wiki-consistency/tests`.

**Private data**: The `work` vault holds student data. No task reads it, and
no task writes a student name or real vault content into the repository or
into Orca or Linear messages; tests use synthetic vaults only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US3)

---

## Phase 1: Code and tests (US1, US2)

- [x] T001 [US1] [US2] In `TESTS/conftest.py`, give the synthetic schema
  `AGENTS.md` front matter that declares topics and give each synthetic page
  a `topics` list, so the existing tests keep passing after T002 to T004.
  Then add cases for the [data model](data-model.md) and the
  [contract](contracts/topics.md): in `TESTS/test_instance.py`, page
  `topics` that is missing, not a list, empty, holds a non-string, empty or
  multi-line name, or lists a name twice, and `declared_topics` for a valid
  list, an empty list, a missing `AGENTS.md`, missing front matter, a
  missing or non-list `topics`, and bad or repeated names; in
  `TESTS/test_check.py`, `check` failing with the page or `AGENTS.md` named
  for each case above and for an undeclared page topic, passing for a
  declared topic without pages and for an empty vault, and `update`
  refusing on each case with every file unchanged; in
  `TESTS/test_sources.py`, the grouped index of the data model's example,
  a vault with three topics where one page carries two of them and is listed
  under exactly those (SC-001), sorted topics and pages, identical output
  from two runs, an empty region for a vault without pages, and a stale
  index after a page's topics change.
- [x] T002 [US2] In `SRC/instance.py`, validate `topics` in `_metadata` next
  to `title`, `summary` and `sources` and return it; add
  `declared_topics(root)`, which reads the list from `AGENTS.md`'s front
  matter with `_front_matter` and PyYAML and returns the names and problems
  (research R1, R2, R5).
- [x] T003 [US2] In `SRC/lint.py`, add one helper that returns the schema's
  problems and each page's undeclared topics, skipping the undeclared check
  when the schema has problems; call it from `check` and, before
  regeneration, from `update` (research R3, R5).
- [x] T004 [US1] In `SRC/sources.py`, make `page_catalog` write one
  `## <topic>` heading per topic, sorted, with the existing page lines
  sorted by path under it and a blank line between groups (research R4).
  T001's cases and the rest of `deno task test:wiki-consistency` pass.
  - 2026-09-29: A Codex worker (`gpt-6-luna`, `max`; Orca dispatch
    `ctx_8c5f078b3c4f`) made T001 to T004 in `2dcaaf3`; 51 of T001's cases
    failed before T002 to T004, and 169 tests pass. With main's approval it
    also added topics to the synthetic pages in `test_lint.py` and
    `test_prepare.py`, which the required field broke. After main's review,
    the same worker (`ctx_72230381a6f3`) shared the front matter and topic
    name checks and made `update` pick refused pages by their empty topic
    list instead of by message text, in `7760ab4`. Next: verification and
    the merge review.

## Phase 2: Documents (US3)

- [x] T005 [P] [US3] In `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  add the schema front matter with an empty list, the `topics` field and its
  rules in `## Pages`, and the grouped index in the `index.md` bullet, as
  the [contract](contracts/topics.md) states (FR-005, FR-010).
- [x] T006 [P] [US3] In `docs/architecture.md`, add topics to the Wiki
  consistency bullets on page metadata, `index.md` and the check (FR-007).
- [x] T007 [P] [US3] In `plugins/work/skills/wiki-consistency/SKILL.md`, name
  topics in the `check` row of the command table (FR-007).
  - 2026-09-29: Main wrote T005 to T007 in `60b505f`, after merging
    `develop` at `df912f4` (CHE-25) into this branch, so the template keeps
    CHE-25's English and page rules.

## Phase 3: Verification and review

- [x] T008 Run `deno task test:wiki-consistency`,
  `deno task test:wiki-raw-import` and `deno task verify`; confirm that the
  layer folders, the region line in `index.md` and the judgment step are
  unchanged (FR-006) and that no student name or vault content entered the
  feature's files (SC-005).
  - 2026-09-29: The first `deno task verify` failed in one test outside the
    plan: `packages/backfire/tests/test_build.py` runs the built work
    plugin's `check` on a synthetic vault whose `AGENTS.md` had no topic
    list. Main gave it an empty list in `f93eee3`. After merging `develop`
    at `7e4c92b` (the answerless provider reply fix), `deno task verify`
    passed at `d2682e2`. The feature leaves the constitution, the region
    line in `index.md` and the judgment step's modules unchanged, and its
    added lines hold no Hangul text.
- [x] T009 Run the document judgment step as feature 013's T009 did:
  `deno task doc-regions:prepare -- --base develop --max-evidence-chars 20000`
  plus one `backfire_verify` for the changed units of the template and the
  skill; correct or record each contradicted or flagged unit.
  - 2026-09-29: Prepare gave four `backfire_verify` requests (229 units of
    the constitution, `AGENTS.md`, `README.md`, `docs/architecture.md` and
    `docs/backfire.md`, with the feature diff as evidence) and one
    `backfire_classify` request; one more `backfire_verify` covered the six
    changed units of the template and the skill, with the spec's
    clarifications and requirements, the research and the new code as
    evidence. No unit was contradicted. Both changed `docs/architecture.md`
    units (187-195, 196-202) were verified, and 187-195 was classified as an
    agent region. All six template and skill units were verified; the index
    sentence was flagged for review at 0.85 support and stands. Five
    unchanged constitution units (58-59, 61-67, 68-73, 122-144, 146-148)
    were flagged for review; this feature does not change them. Three
    requests failed twice at the provider and succeeded on the third try;
    the judgments used 190,810 input and 64,240 output tokens.
- [ ] T010 Merge `develop`, verify, move CHE-27 to In Review, run the merge
  review (a fresh Claude Code reviewer for T001 to T004, a fresh Codex
  reviewer for the documents), resolve findings, commit the review record,
  check that `develop` has not moved, and run
  `git flow feature finish vault-topics` in the `develop` worktree.

## Phase 4: After the finish

These run after the merge, so their evidence goes into CHE-27's completion
comment, not into this file.

- [ ] T011 For each of the `default`, `chat` and `code` vaults, add the
  template's front matter and topic rules to its `AGENTS.md` without
  touching its other lines, run `update` and `check` with the develop
  worktree's tool, append one `schema` entry to `wiki/log.md`, and commit
  once (research R6, FR-008). Leave the `work` vault to the develop session.
- [ ] T012 Move CHE-27 to Done with one completion comment giving the merge
  commit, the review-record commit, the three vault commits and the record
  location.

## Dependencies

- T002 to T004 follow T001; T003 uses T002's `declared_topics`.
- T005 to T007 are independent of each other and of Phase 1.
- T008 needs T001 to T007; T009 needs T005 to T007; T010 needs T008 and
  T009; T011 needs T010; T012 needs T011.

## Parallel execution

- Codex worker: T001, then T002 to T004 (`PKG`).
- Main, meanwhile: T005 to T007.

## Implementation strategy

US1 and US2 share the page metadata change and ship together; US3's
template and documents describe them. Vault adoption (T011) follows the
finish because it uses the merged tool.
