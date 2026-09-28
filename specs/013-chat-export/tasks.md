---

description: "Task list for the ChatGPT export into the chat vault"
---

# Tasks: ChatGPT Export into the Chat Vault

**Input**: Design documents from `specs/013-chat-export/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. The root `AGENTS.md` asks for tests with every code
change; T001's cases fail against `evidence.py` before T002.

**Organization**: Main (Claude Code) owns the Spec Kit records, the
constitution, the skill, the schema template, `docs/architecture.md`, the
document judgment step and every write outside the repository. Codex workers
own the code and tests. `EVIDENCE` is
`packages/wiki-consistency/src/wiki_consistency/evidence.py`, `EVIDENCE_TEST`
is `packages/wiki-consistency/tests/test_evidence.py`, `IMPORT_TEST` is
`scripts/wiki_raw_import_test.ts` and `SKILL` is
`plugins/work/skills/wiki-raw-import/SKILL.md`.

**Private data**: The vaults and the user's real export hold student data. No
task writes a student name, conversation text or private file name into the
repository or into Orca or Linear messages; tests use only synthetic
exports built in temporary folders.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Code and tests (US1 to US4)

- [ ] T001 [US4] In `EVIDENCE_TEST`, add cases for the
  [evidence contract](contracts/evidence-json.md): a synthetic export ZIP
  whose `conversations.json` writes Korean and English messages with
  `\uXXXX` escapes converts to text containing the characters; the same with
  direct characters; a ZIP with two numbered conversation JSON files instead
  of `conversations.json`; a `.jsonl` payload with a blank line; a `.json`
  payload that does not parse comes back as plain text; and the evidence
  cache path's converter version differs from MarkItDown's version alone.
- [ ] T002 [US4] In `EVIDENCE`, register one JSON converter on the
  MarkItDown instance with `register_converter`, and add a local converter
  revision to `CONVERTER_VERSION` (research R3). T001's cases and the
  existing `deno task test:wiki-consistency` cases pass.
- [ ] T003 [P] [US1] [US2] [US3] In `IMPORT_TEST`, turn "raw import US5: a
  synthetic conversation export is admitted to chat" into the
  [procedure](contracts/export-procedure.md)'s scenario: a synthetic export
  ZIP at `<temporary home>/Documents/chatgpt/chatgpt-export.zip` passes
  `python3 -m zipfile -t` and is admitted into `chat` and then `work`; a
  changed export saved over the same file gives each vault a second revision
  of the same source; an unchanged rerun is `already_admitted` in both; both
  vaults verify; the fixed file is unchanged by the tool. A truncated copy of
  the ZIP fails `python3 -m zipfile -t`.

## Phase 2: Policies and documents (US1, US2, US3)

- [ ] T004 [P] [US3] Amend `.specify/memory/constitution.md`: principle VI
  makes the `chat` and `work` vaults the exceptions for exported
  conversations; the Sync Impact Report and Governance record the user's
  2026-09-29 decision; version 2.1.0 in one `feat(constitution)` commit
  (FR-007).
- [ ] T005 [P] [US1] [US2] [US3] In `SKILL`, add a "ChatGPT exports" section
  with the procedure contract's steps, and state the rule for the `chat` and
  `work` vaults where the skill names the vaults, the raw kinds and its
  boundaries (FR-001 to FR-007).
- [ ] T006 [P] [US3] In `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  state the rule for the `chat` and `work` vaults (FR-007).
- [ ] T007 [P] [US3] In `docs/architecture.md`, state the rule and the work
  vault's exports in the vault table and the raw import paragraph (FR-007).

## Phase 3: Verification and review

- [ ] T008 Run `deno task test:wiki-raw-import`,
  `deno task test:wiki-consistency` and `deno task verify`; follow `SKILL`'s
  "ChatGPT exports" section once with a synthetic export in a temporary home
  (quickstart's manual walk-through, SC-001); search the repository outside
  earlier features' records for statements that only the `chat` vault admits
  exported conversations (SC-004, SC-005).
- [ ] T009 Run the document judgment step as feature 012's research R2 did:
  `deno task doc-regions:prepare -- --base develop --max-evidence-chars 20000`
  plus one `backfire_verify` for the changed units of the skill and the
  schema template; correct or record each contradicted or flagged unit.
- [ ] T010 Merge `develop`, verify, move CHE-20 to In Review, run the merge
  review (a fresh Claude Code reviewer for T001 to T003, a fresh Codex
  reviewer for the documents), resolve findings, commit the review record,
  check that `develop` has not moved, and run
  `git flow feature finish chat-export` in the `develop` worktree.

## Phase 4: After the finish

These run after the merge, so their evidence goes into CHE-20's completion
comment, not into this file.

- [ ] T011 Move CHE-20 to Done with one completion comment giving the merge
  commit and the record location.
- [ ] T012 With the user's go-ahead, update the schema copies in the user's
  `chat` and `work` vaults to the new rule; when the user's real export has
  arrived and the user says go, run the procedure on the real vaults. CHE-20
  does not wait for this.

## Dependencies

- T002 follows T001. T003 is independent of both.
- T004 to T007 are independent of each other and of Phase 1.
- T008 needs T001 to T007; T009 needs T004 to T007; T010 needs T008 and T009;
  T011 needs T010; T012 needs the merge and the user.

## Parallel execution

- Codex worker A: T001, then T002 (`packages/wiki-consistency/`).
- Codex worker B: T003 (`scripts/wiki_raw_import_test.ts`).
- Main, meanwhile: T004 to T007.

## Implementation strategy

US1 to US3 need only T003 and the documents, since the raw import does not
change; US4 needs T001 and T002. All four ship together in one finish, because
the skill's procedure and the consistency check are meant to be used together.
