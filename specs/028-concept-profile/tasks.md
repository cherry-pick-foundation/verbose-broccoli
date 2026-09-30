---

description: "Task list for concept profiles of teaching materials"
---

# Tasks: Concept Profiles of Teaching Materials

**Input**: Design documents from `specs/028-concept-profile/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: The script gets pytest cases with synthetic catalogs, sources and
a stubbed backfire call (constitution V); `npm run verify` runs them. The
pilot exercises real files in the work vault.

**Organization**: Main (a Claude Code orchestrator) owns the Spec Kit
records, the pilot's vault steps, the user questions and the merge. Workers
implement the skill and propose concepts; each worker's agent, model and
effort comes from the code plugin's `model-choice` skill and is noted under
its task. The final review comes from a provider other than the
implementer's.

**Private data**: No task writes catalog data, material text, student names
or records into the repository, commits, or Orca or Linear messages. Pilot
files stay in the work vault and the run folder.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US3)

---

## Phase 1: Setup

- [x] T001 Write `spec.md`, `plan.md` and this file; record the user's
  answers of 2026-09-30 in the spec's Clarifications.
  - 2026-09-30: main (Claude Code, Opus). The user picked the pilot volume
    and exam paper, approved the vault and folder changes, and moved the
    reference mappings to a later feature.

---

## Phase 2: User Story 1 - Profile one material (P1), with the mapping design (US3)

**Goal**: The skill, its script and the vault schema template exist and pass
`npm run verify`.

**Independent Test**: The script's tests pass on synthetic data; the
procedure and the template describe the three record kinds as `plan.md`
does.

- [ ] T002 [US1] Create `plugins/work/skills/concept-profile/SKILL.md` and
  `references/procedure.md`: the procedure (admit, extract, propose, check,
  review, record, consistency, cleanup), the proposer's instructions and
  proposal format, the record layouts including the mapping record and its
  method, and the limits that keep unclear items from piling up (FR-001 to
  FR-004, FR-010, FR-013; plan.md "Record layouts", R5).
- [ ] T003 [US1] Create `scripts/concept_profile.py` with the `catalog`,
  `extract`, `check` and `record` commands, and
  `scripts/concept_profile_test.py`; wire `test:concept-profile` into
  `package.json` and `turbo.json`; regenerate `docs/` (FR-005 to FR-011;
  plan.md "Script", "Run folder and working files").
  - T002 to T004: Codex `gpt-6-luna` at max (backfire: model 0.45,
    confidence 0.38; effort 0.46, confidence 0.37), through the terminal
    launch path because Orca caps this model at xhigh.
- [ ] T004 [US1] Add the catalog, profile and mapping records to the vault
  schema template `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  pointing to the `concept-profile` skill for their layout (FR-012).

---

## Phase 3: User Story 2 - Pilot (P1)

**Goal**: Two pilot records in the work vault and the numbers for the
user's decision.

**Independent Test**: `wiki-consistency check` passes on the vault; the
report gives the numbers SC-002 names; the user's decision is recorded
below.

- [ ] T005 [US2] Copy the pilot volume's five main-text files from the legacy
  source cache into `~/Documents/20_reference/textbooks/`, keeping their
  names; admit them, the exam paper and the catalog spreadsheet into the
  work vault with `wiki-raw-import`.
- [ ] T006 [US2] Bring the vault's `AGENTS.md` in line with the template
  (T004); write the catalog record; run `catalog` and `extract` for each
  material in its own run folder (depends on T003, T004, T005).
- [ ] T007 [P] [US2] Propose concepts for every sentence of the volume into
  its `proposals.jsonl` (depends on T006).
- [ ] T008 [P] [US2] Propose concepts for every sentence of the exam paper
  into its `proposals.jsonl` (depends on T006).
- [ ] T009 [US2] Run `check` for both materials; write the hand-check sheet
  of 30 sampled sentences; ask the user to return it and the review sheets.
- [ ] T010 [US2] Run `record --reviewed`, `wiki-consistency update` and
  `check`, log and commit in the vault; score the hand-check; report
  accuracy, calls, tokens and time to the user and record the decision on
  the full run here; delete the run folders.

---

## Phase 4: Review and finish

- [ ] T011 Measure the change size against `develop`; move CHE-57 to In
  Review and the worktree's board status to `in-review`; merge `develop`;
  run `npm run verify`.
- [ ] T012 Develop merge review by a fresh reviewer from the other provider,
  given only the scope and requirements; resolve findings; add the
  review-record commit; check `develop` has not moved; `git flow feature
  finish`; comment on CHE-57 with the merge commit and the record location,
  leaving it open for stage 2; set the board status to `completed`.
