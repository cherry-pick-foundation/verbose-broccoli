---

description: "Task list for Wiki vaults"
---

# Tasks: Wiki Vaults

**Input**: Design documents from `specs/012-wiki-vaults/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. The root `AGENTS.md` asks for tests with every code
change; the new cases fail against the script before T001.

**Organization**: Main (Claude Code) owns the Spec Kit records, the
constitution, `AGENTS.md`, the other documents, the backfire judgments and
every write outside the repository; a Codex worker owns the script and its
tests. `SCRIPT` is `plugins/work/skills/wiki-raw-import/scripts/raw_import.py`
and `TEST` is `scripts/wiki_raw_import_test.ts`.

**Private data**: The vaults hold real student data. No task writes a student
name, file name or record into the repository or into Orca or Linear
messages; tests use only synthetic fixtures.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Script and tests (US1, US2, US3)

- [x] T001 [US1] [US2] In `SCRIPT`, build the data path as
  `DATA/vaults/<name>` and the lock path as `STATE/vaults/<name>/raw-import.lock`,
  and default `--wiki` to `work`
  ([contract](contracts/raw-import-cli.md)).
- [x] T002 [US1] [US2] [US3] In `TEST`, move every path from `wikis/` to
  `vaults/` and the default instance from `default` to `work`; add a case in
  which `init`, `admit` and `verify` without `--wiki` use
  `DATA/vaults/work/` and `STATE/vaults/work/` and nothing named `wikis`
  appears, and a case that admits a synthetic exported conversation with
  `--wiki chat` and verifies it (research R3).
  - 2026-09-28: A Codex worker (`gpt-6-luna`, `max`; Orca dispatch
    `ctx_8e99c3bb93bd`) made T001 and T002; both new cases failed before the
    script change and passed after it. Main replaced the new case's check for
    the old folder name with an assertion that the data and state roots hold
    only `vaults`. Next: the merge review.

## Phase 2: Policies and documents (US1, US2, US3)

- [x] T003 [P] [US2] [US3] Amend `.specify/memory/constitution.md`:
  principle VI names `vaults/` and the four vaults and limits the
  conversation-records rule to the vaults other than `chat`; IX says the chat
  package's persistent state is its vault; Governance records the 2026-09-28
  decisions; version 2.0.0 in one `feat(constitution)!` commit (FR-005 to
  FR-007).
- [x] T004 [P] [US2] In `AGENTS.md` Records, say that the code vault holds
  coding knowledge for any project and is not this repository's development
  memory (FR-008).
- [x] T005 [P] [US2] In `docs/architecture.md`, describe the four vaults,
  their owners, the default rule, shared vault storage and the chat package's
  state (FR-009).
- [x] T006 [P] [US1] [US2] [US3] In the `wiki-raw-import` skill's `SKILL.md`
  and `assets/AGENTS.md`, name `vaults/`, the default `work`, and allow
  exported conversations only in the chat vault (FR-010).
- [x] T007 [P] [US1] In `specs/009-wiki-storage/`, rename the storage folder
  in the units research R1 lists; leave the single-instance statements
  (FR-011).

## Phase 3: Verification and review

- [x] T008 Run `deno task test:wiki-raw-import`, `deno task verify` and
  `git grep -n wikis`; no storage folder mention may remain.
  - 2026-09-28: 43 tests passed, `deno task verify` passed at `948011b`, and
    `git grep -n wikis` found nothing.
- [x] T009 Run the document judgment step of research R2; correct or record
  each contradicted or flagged unit; report the requests and input tokens.
  - 2026-09-28: No correction was needed; the results, the reasons the
    flagged units stand, and the token use are in research R2.
- [ ] T010 Merge `develop`, verify, move CHE-19 to In Review, run the merge
  review (a fresh Claude Code reviewer for T001 and T002, a fresh Codex
  reviewer for the documents), resolve findings, commit the review record and
  run `git flow feature finish vaults` in the `develop` worktree.

## Phase 4: After the finish (US4)

These run after the merge, so their evidence goes into CHE-19's completion
comment, not into this file.

- [ ] T011 [US4] Move the live instance and its state folder as research R4
  says, create `default`, `chat` and `code`, verify all four vaults and remove
  the empty `wikis/` folders.
- [ ] T012 Move CHE-19 to Done with one completion comment giving the merge
  commit, the record location, the move's evidence and the backfire use.

## Dependencies

- T002's new cases are written against the contract and fail until T001.
- T003 to T007 are independent of T001 and T002 and of each other.
- T008 and T009 need Phases 1 and 2; T010 needs T008 and T009; T011 needs
  T010; T012 needs T011.

## Worker Assignment

- Codex worker, `gpt-6-luna` at `max`: T001 and T002.
- Main: everything else.
