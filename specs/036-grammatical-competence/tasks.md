---

description: "Task list for grammatical competence profiles, stage 2"
---

# Tasks: Grammatical Competence Profiles, Stage 2

**Input**: Design documents from `specs/036-grammatical-competence/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: The script's pytest cases use synthetic inventories, sources,
reference texts and a stubbed backfire call; `npm run verify` runs them.

**Organization**: Main (a Claude Code orchestrator under the develop
session) owns the Spec Kit records, the vault steps, the user questions and
the merge. Workers propose items, build section indexes and survey the
materials; each worker's agent, model and effort comes from the code
plugin's `model-choice` skill and is noted under its task. The final review
comes from a provider other than the implementer's.

**Private data**: No task writes inventory text, material text, reference
text or the answer key into the repository, commits, or Orca or Linear
messages. Run files stay in the run folders and records in the work vault.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [ ] T001 Write `spec.md`, `plan.md` and this file; record the user's
  answers in the spec's Clarifications.

---

## Phase 2: User Story 1 - Tier families and a pilot rerun (P1)

- [x] T002 [US1] Rename the skill to `grammatical-competence` (folder,
  script, tests, task wiring, docs, the vault template's section and
  pointer), the record kind catalog to inventory and concept to item; move
  the vault's inventory page to `wiki/inventories/` and relink the profile
  pages.
  - 2026-10-01: main. Vault commits b0a5554 (move and relink) and f101a22
    (schema section synced to the template, with CHE-69's lexicon lines, as
    its orchestrator asked).
- [x] T003 [US1] Count tier families as one item in `inventory`, `check` and
  `record`; write the tier rule for every proposer into the procedure; drop
  the review sheet.
  - 2026-10-01: main; 7 tests pass. The inventory page gained
    `family: <tier column>`: 1,119 items from 1,222 rows.
- [ ] T004 [US1] Rerun the two pilot materials: `inventory` and `extract`,
  new proposals, `check`, `record --auto-accept 0.5`; score against the kept
  answer key with families collapsed.
  - 2026-10-01: stage 1's proposals scored at family level: precision 0.965
    (276 of 286), recall 0.945 (276 of 292).
  - Proposers: two Claude Code workers, `fable` at medium (backfire: 0.90,
    confidence 0.88), one per material.
- [ ] T005 [US1] Choose the full run's proposer with `model-choice` from the
  rerun's accuracy, time and quota.

---

## Phase 3: User Story 2 - Mappings to four reference books (P1)

- [ ] T006 [US2] Add `map` and the mapping `record` to the script, with
  tests; describe the section index and the map step in the procedure.
- [ ] T007 [P] [US2] Build a section index for each of the four reference
  texts.
  - Four Claude Code workers, `sonnet` at medium (backfire: 0.56,
    confidence 0.49), one per book; only Claude Code and Codex could read
    the book text.
- [ ] T008 [US2] Propose sections for every item per reference; run `map`
  and `record`; run `wiki-consistency`; commit the four mapping records in
  the vault.

---

## Phase 4: User Story 3 - Full run (P1)

- [ ] T009 [P] [US3] Survey the local stores for textbook volumes and exam
  papers and list the candidate materials.
  - Worker: Claude Code `sonnet` at medium (backfire: 0.71, confidence
    0.65); only Claude Code and Codex could run it, since the Documents
    folders may hold student files.
  - 2026-10-01 done: 512 candidate materials: 104 textbook volumes (46 of
    the 2015 curriculum, 58 of 2022; 101 from 673 HWP or HWPX main-text
    files, 3 from PDFs) and 408 exam papers (85 national CSAT and mock
    papers, 140 education-office assessments, 174 middle-school exams, 7
    photo sets, 2 others). Already admitted: 6 fully, 5 partly. 15 scanned
    PDFs have no text layer. The list and summary stay in the
    coordinator's scratch space.
- [ ] T010 [US3] Ask the user the catalog choice, with the rerun's numbers,
  and the material list with its admissions and check cost; record the
  answers in the spec.
- [ ] T011 [US3] Copy the approved originals into the approved folder and
  admit them with `wiki-raw-import`.
- [ ] T012 [US3] Profile every approved material: proposals, `check`,
  `record`, `wiki-consistency`, vault commits; record counts per material
  here.

---

## Phase 5: Review and finish

- [ ] T013 Measure the change against `develop`; move CHE-68 to In Review
  and the board status to `in-review`; after CHE-67 merges, merge `develop`
  and run `npm run verify`.
- [ ] T014 Develop merge review by a fresh reviewer from another provider;
  resolve findings; review-record commit; ask the develop session for the
  finish slot; check `develop` has not moved; `git flow feature finish`;
  CHE-68 Done with one completion comment; board status `completed`.
