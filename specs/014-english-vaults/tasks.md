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

- [x] T001 [US1] In `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  add the rule to the Wiki section (FR-001, FR-002), and the source
  precedence sentence and the three page rules next to it (FR-006, FR-007).
- [x] T002 [P] [US1] In `plugins/work/skills/wiki-consistency/SKILL.md`,
  state the rule in one sentence (FR-003).
- [x] T003 [P] [US1] In `docs/architecture.md`'s Wiki consistency section,
  state the rule in one sentence (FR-003).
- [x] T004 [P] [US1] In `docs/examples/wiki/AGENTS.md`, add the rule as one
  bullet (FR-003).

## Phase 2: Verification and review

- [x] T005 Run `deno task verify` (SC-003).
  - 2026-09-29: `deno task verify` passed with the Phase 1 changes. The
    document judgment step (`doc-regions:prepare -- --base develop
    --max-evidence-chars 20000`) sent 229 units in three `backfire_verify`
    requests and one `backfire_classify` request: no unit was contradicted,
    the new `docs/architecture.md` unit (182-185) was verified and classified
    as an agent region, and the three units flagged for review (constitution
    74-79 and 85-95, `docs/architecture.md` 10-25) were judged supported and
    stand unchanged. Two requests failed at the provider and succeeded on
    retry; 8 judgments used 146,057 input and 36,335 output tokens.
    `doc-regions:audit` reported the same 19 MemoryLint `boundary` warnings
    on the constitution as feature 012; they are reported, not acted on.
- [ ] T006 Merge `develop`, verify, move CHE-25 to In Review, run the merge
  review with a fresh Codex reviewer, resolve findings, commit the review
  record and run `git flow feature finish english-vaults` in the `develop`
  worktree (SC-001).
  - 2026-09-29: A fresh Codex reviewer (`gpt-6-luna`, max effort) reviewed
    `ec50c25` and found one minor issue: feature 010's page contract lacks
    the rule. That contract records what feature 010 built, so FR-003 and
    SC-001 now leave earlier features' Spec Kit records out.
  - 2026-09-29: The user then added the school domain ID rule, the source
    precedence rule and three page rules (spec Clarifications), and
    `develop` with CHE-20's merge was merged in at `2452123`. There
    `deno task verify` passed, and the document judgment step found no
    contradicted or flagged unit; the changed `docs/architecture.md`
    unit (183-186) was verified and classified as an agent region. Two
    requests failed at the provider and succeeded on retry; 6 judgments
    used 146,370 input and 34,841 output tokens. The audit's 19
    constitution warnings are unchanged.

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
