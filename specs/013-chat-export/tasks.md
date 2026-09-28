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

- [x] T001 [US4] In `EVIDENCE_TEST`, add cases for the
  [evidence contract](contracts/evidence-json.md): a synthetic export ZIP
  whose `conversations.json` writes Korean and English messages with
  `\uXXXX` escapes converts to text containing the characters; the same with
  direct characters; a ZIP with two numbered conversation JSON files instead
  of `conversations.json`; a `.jsonl` payload with a blank line; a `.json`
  payload that does not parse comes back as plain text; and the evidence
  cache path's converter version differs from MarkItDown's version alone.
- [x] T002 [US4] In `EVIDENCE`, register one JSON converter on the
  MarkItDown instance with `register_converter`, and add a local converter
  revision to `CONVERTER_VERSION` (research R3). T001's cases and the
  existing `deno task test:wiki-consistency` cases pass.
- [x] T003 [P] [US1] [US2] [US3] In `IMPORT_TEST`, turn "raw import US5: a
  synthetic conversation export is admitted to chat" into the
  [procedure](contracts/export-procedure.md)'s scenario: a synthetic export
  ZIP at `<temporary home>/Documents/chatgpt/chatgpt-export.zip` passes
  `python3 -m zipfile -t` and is admitted into `chat` and then `work`; a
  changed export saved over the same file gives each vault a second revision
  of the same source; an unchanged rerun is `already_admitted` in both; both
  vaults verify; the fixed file is unchanged by the tool. A truncated copy of
  the ZIP fails `python3 -m zipfile -t`.
  - 2026-09-29: Codex workers (`gpt-6-luna`, `max`) made T001 and T002
    (Orca dispatch `ctx_d0d3fb06959f`; `CONVERTER_VERSION` is `0.1.8-json-1`,
    and `test_search.py`'s two pinned cache paths now follow it) and T003
    (`ctx_8323b40e534c`). Four of T001's cases failed before T002. Both
    sessions stopped once on a revoked Codex login and finished after the
    user signed in again. `worker-start` failed at `agent_readiness` on
    Codex 0.158.0 (`ctx_a4dc1da627e5`), so both ran through
    `dispatch --inject`. Next: the merge review.

## Phase 2: Policies and documents (US1, US2, US3)

- [x] T004 [P] [US3] Amend `.specify/memory/constitution.md`: principle VI
  makes the `chat` and `work` vaults the exceptions for exported
  conversations; the Sync Impact Report and Governance record the user's
  2026-09-29 decision; version 2.1.0 in one `feat(constitution)` commit
  (FR-007).
- [x] T005 [P] [US1] [US2] [US3] In `SKILL`, add a "ChatGPT exports" section
  with the procedure contract's steps, and state the rule for the `chat` and
  `work` vaults where the skill names the vaults, the raw kinds and its
  boundaries (FR-001 to FR-007).
- [x] T006 [P] [US3] In `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  state the rule for the `chat` and `work` vaults (FR-007).
- [x] T007 [P] [US3] In `docs/architecture.md`, state the rule and the work
  vault's exports in the vault table and the raw import paragraph (FR-007).

## Phase 3: Verification and review

- [x] T008 Run `deno task test:wiki-raw-import`,
  `deno task test:wiki-consistency` and `deno task verify`; follow `SKILL`'s
  "ChatGPT exports" section once with a synthetic export in a temporary home
  (quickstart's manual walk-through, SC-001); search the repository outside
  earlier features' records for statements that only the `chat` vault admits
  exported conversations (SC-004, SC-005).
  - 2026-09-29: 43 raw import tests, 118 wiki-consistency tests and
    `deno task verify` passed at `9b887fc`. The walk-through admitted a
    synthetic export into both vaults, verified them and reported
    `already_admitted` on a rerun. Only the new two-vault statements match
    the search.
- [x] T009 Run the document judgment step as feature 012's research R2 did:
  `deno task doc-regions:prepare -- --base develop --max-evidence-chars 20000`
  plus one `backfire_verify` for the changed units of the skill and the
  schema template; correct or record each contradicted or flagged unit.
  - 2026-09-29: Prepare gave three `backfire_verify` requests (228 units of
    the constitution, `AGENTS.md`, `README.md`, `docs/architecture.md` and
    `docs/backfire.md`, with the feature diff as evidence); one more covered
    the nine changed units of the skill and the schema template, with the
    spec's background and clarifications, research R2 and R4, principle VI
    and the raw import's source as evidence. No unit was contradicted. Five
    units were flagged for review: `docs/architecture.md` 148-153 (the
    vault table, verified), 175-181 and 194-209 (unchanged text), and the
    skill's step 5 and raw kinds line (both verified); they stand. The first
    request failed once with `malformed_output` and succeeded on retry.
    Input tokens 161,847; output tokens 50,783.
- [ ] T010 Merge `develop`, verify, move CHE-20 to In Review, run the merge
  review (a fresh Claude Code reviewer for T001 to T003, a fresh Codex
  reviewer for the documents), resolve findings, commit the review record,
  check that `develop` has not moved, and run
  `git flow feature finish chat-export` in the `develop` worktree.
  - 2026-09-29: Backfire rated the code review medium, so a fresh Claude
    Code reviewer (`claude-sonnet-5`, high effort; Orca dispatch
    `ctx_f0cae78f75e6`) reviewed T001 to T003 at `c3ee8d3` and found
    nothing. A fresh Codex reviewer (`gpt-6-luna`, `max`;
    `ctx_8dcdb75a3466`) reviewed the documents and found one major issue
    (the spec named a file inside the work vault) and one minor one (an
    unattributed claim about the student pages); both are fixed in the
    spec, which also names the fixed export path as SC-005's one exception.
    Next: the review record and the finish.

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
