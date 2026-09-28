---

description: "Task list for English vaults"
---

# Tasks: English Vaults

**Input**: Design documents from `specs/014-english-vaults/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: None added. The feature changes no code; `deno task verify` checks
the documents and `check` checks each vault.

**Organization**: Main (Claude Code) owns every task; a fresh Codex reviewer
gives the merge review.

**Private data**: No task writes a student name, file name or record into the
repository or into Orca or Linear messages.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Documents (US1)

- [ ] T001 [US1] In `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  add the rule to the Wiki section (FR-001, FR-002).
- [ ] T002 [P] [US1] In `plugins/work/skills/wiki-consistency/SKILL.md`,
  state the rule in one sentence (FR-003).
- [ ] T003 [P] [US1] In `docs/architecture.md`'s Wiki consistency section,
  state the rule in one sentence (FR-003).
- [ ] T004 [P] [US1] In `docs/examples/wiki/AGENTS.md`, add the rule as one
  bullet (FR-003).

## Phase 2: Verification and review

- [ ] T005 Run `deno task verify` (SC-003).
- [ ] T006 Merge `develop`, verify, move CHE-25 to In Review, run the merge
  review with a fresh Codex reviewer, resolve findings, commit the review
  record and run `git flow feature finish english-vaults` in the `develop`
  worktree (SC-001).

## Phase 3: After the finish (US2)

These run after the merge, so their evidence goes into CHE-25's completion
comment, not into this file.

- [ ] T007 [US2] Copy the template into the `default`, `chat` and `code`
  vaults, run `check` in each and commit each vault once (FR-004, SC-002).
- [ ] T008 Move CHE-25 to Done with one completion comment giving the merge
  commit, the review record and the three vault commits.

## Dependencies

- T002 to T004 are independent of T001 and of each other.
- T005 needs Phase 1; T006 needs T005; T007 needs T006; T008 needs T007.

## Worker Assignment

- Codex reviewer, `gpt-6-luna` at `max`: the merge review in T006.
- Main: everything else.
