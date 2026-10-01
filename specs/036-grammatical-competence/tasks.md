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
- [x] T004 [US1] Rerun the two pilot materials: `inventory` and `extract`,
  new proposals, `check`, `record --auto-accept 0.5`; score against the kept
  answer key with families collapsed.
  - 2026-10-01: stage 1's proposals scored at family level: precision 0.965
    (276 of 286), recall 0.945 (276 of 292).
  - Proposers: two Claude Code workers, `fable` at medium (backfire: 0.90,
    confidence 0.88), one per material.
  - 2026-10-01 rerun: the volume 250 sentences, 5,835 proposed items, about
    13 minutes; the exam 280 sentences, 5,660 items, about 12 minutes.
    Proposer tokens: 252,000 and 341,000 output, 723,000 and 546,000 cache
    writes, 4.4 and 4.6 million cache reads. Check: 524 calls, 7.2 million
    tokens, about 7 minutes of calls, 9 invalid results; at the default
    0.8, 3,006 kept, 3 dropped, 8,486 unclear.
  - Scored on the 15 key sentences (292 true items, families collapsed):
    proposer precision 0.936 (264 of 282), recall 0.904 (264 of 292);
    kept at 0.5 precision 0.970 (224 of 231), recall 0.767; kept at 0.8
    precision 0.966 (86 of 89), recall 0.295. Per material at 0.5: the
    volume 0.970 and 0.810, the exam 0.970 and 0.716. The key came from
    stage 1's proposals, so true items only the new proposer found count
    as false.
  - Records written at 0.5 (vault commit e05c0c0): the volume 4,651 kept,
    18 dropped, 1,166 unclear; the exam 4,576 kept, 20 dropped, 1,064
    unclear. Check: 0 problems on the record pages.
- [x] T005 [US1] Choose the full run's proposer with `model-choice` from the
  rerun's accuracy, time and quota.
  - 2026-10-01: the user fixed the model, Codex `gpt-6-astra`; backfire
    chose medium effort (0.88, confidence 0.85), given that CHE-69's arbiter
    shares the Codex weekly window (43% used). One worker per material,
    started in waves.

---

## Phase 3: User Story 2 - Mappings to four reference books (P1)

- [ ] T006 [US2] Add `map` and the mapping `record` to the script, with
  tests; describe the section index and the map step in the procedure.
- [x] T007 [P] [US2] Build a section index for each of the four reference
  texts.
  - Four Claude Code workers, `sonnet` at medium (backfire: 0.56,
    confidence 0.49), one per book; only Claude Code and Codex could read
    the book text.
  - 2026-10-01 done: 152, 122 and 115 sections for the three practice
    books (units, appendices and grammar reminders; none split), 772 for
    the reference grammar (166 numbered sections split at subsections).
    Main checked every index: unique labels, ordered, inside the text, at
    most 19,654 characters a section. The 7 Hangul lines of one practice
    book lie inside its sections, so `map` leaves them out of the evidence.
- [x] T008 [US2] Propose sections for every item per reference; run `map`
  and `record`; run `wiki-consistency`; commit the four mapping records in
  the vault.
  - Proposers: four Claude Code workers, `fable` at medium (backfire: 0.66,
    confidence 0.62 for the practice books; 0.64 and 0.59 for the reference
    grammar).
  - 2026-10-01 proposals, items with zero, one, two and three sections:
    the elementary book 604, 345, 136, 34 (about 6 minutes); the
    intermediate book 427, 495, 175, 22 (7); the advanced book 311, 378,
    359, 71 (8); the reference grammar 4, 292, 612, 211 (10). Items with no
    section are mostly above or below the book's level.
  - 2026-10-01 `map` (OpenRouter Jev): the elementary book 515 calls, 1.5
    million tokens; the intermediate book 692 calls, 2.2 million tokens, 1
    invalid; the advanced book 808 calls, 3.4 million tokens. The
    intermediate book's run stopped at row 701 when education mode refused
    an example that looked like an identifier; `map` now runs without
    education mode (7795d55) and resumed there. Recorded at 0.5, kept,
    dropped and unclear sections: the elementary book 532, 29, 158 (unclear
    share 22%); the intermediate book 668, 28, 215 (24%); the advanced book
    913, 56, 340 (26%).
  - 2026-10-01 the reference grammar: 1,115 calls, 7.0 million tokens, 2
    invalid; at 0.5, 1,112 kept, 304 dropped, 733 unclear (34%). The four
    records and the two pilot profiles recorded unchecked are in vault
    commit 7d5577d; check: 0 problems on these pages.

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
- [x] T010 [US3] Ask the user the catalog choice, with the rerun's numbers,
  and the material list with its admissions and check cost; record the
  answers in the spec.
  - 2026-10-01: answers in the spec's Clarifications. The pilot volume and
    the pilot exam paper keep their rerun proposals (Fable at medium) and
    were recorded again unchecked.
- [x] T011 [US3] Copy the approved originals into the approved folder and
  admit them with `wiki-raw-import`.
  - 2026-10-01: the user approved 289 main-text files of 54 textbook
    volumes (34.8 MB) and 6 exam papers (5.8 MB), and the 2 exam papers
    already in the vault; left out 3 whole-book PDFs that duplicate
    worksheet volumes and 2 March grade 10 papers (2015 curriculum
    content). Copied with matching SHA-256 into the textbooks and new exams
    folders; admitted 295, refused 0, failed 0; `verify` passed (447
    revisions); vault commit b6ad171. First batch: 63 materials, 55
    volumes and 8 exam papers, 308 sources.
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
