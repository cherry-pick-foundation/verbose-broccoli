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

- [x] T001 Write `spec.md`, `plan.md` and this file; record the user's
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

- [x] T006 [US2] Add `map` and the mapping `record` to the script, with
  tests; describe the section index and the map step in the procedure.
  - 2026-10-01: main; 4697c8e, 7fcf07c (optional title column), 7795d55
    (no education mode for references).
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

- [x] T009 [P] [US3] Survey the local stores for textbook volumes and exam
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
- [x] T012 [US3] Profile every approved material: proposals, `check`,
  `record`, `wiki-consistency`, vault commits; record counts per material
  here.
  - 2026-10-01: 61 Codex workers, `gpt-6-astra` at medium, six at a time,
    about 7 to 35 minutes each (middle school volumes 7 to 17, high school
    volumes and exam papers 12 to 35); the 2 pilot materials kept their
    rerun proposals. Every material recorded with `record --unchecked`:
    63 records, 15,647 sentences, 337,598 items; 0 refused rows. Codex's
    weekly window went from 43% to 67% during the batch, shared with
    CHE-69. Two workers asked questions (lesson labels; one sentence with a
    Korean quotation, kept as its English part). Vault commits 3fba692 and
    88f8308; check: 0 problems on the records after the fix in dad95fe (the
    check read an unindented sources list as page text, and one source ID
    matched the phone pattern).
  - The user's decision of 2026-10-01, for later batches: every proposal
    runs on Codex `gpt-6.1-sol` at max effort, through the terminal path in
    `~/.claude/rules/worker-dispatch.md`. The develop session's Codex guard
    was lifted the same day: use the weekly limit fully; on a usage-limit
    error, stop starting Codex work, keep the results and report to the
    develop session; never use a usage-reset credit.
  - Counts per material (Fable: Claude Code `fable` at medium; Astra: Codex
    `gpt-6-astra` at medium):

  | Material | Proposer | Sentences | Items |
  | --- | --- | --- | --- |
  | 2022-hs-common1-chunjae-gangsanggu-2025 | Astra | 235 | 5,990 |
  | 2022-hs-common1-chunjae-josugyeong-2025 | Astra | 266 | 5,981 |
  | 2022-hs-common1-donga-ibyeongmin-2025 | Astra | 250 | 5,444 |
  | 2022-hs-common1-jihak-sinsanggeun-2025 | Astra | 236 | 6,014 |
  | 2022-hs-common1-mirae-n-gimseongyeon-2025 | Astra | 217 | 5,248 |
  | 2022-hs-common1-ne-minbyeongcheon-2025 | Astra | 282 | 6,088 |
  | 2022-hs-common1-ne-oseonyeong-2025 | Astra | 291 | 6,852 |
  | 2022-hs-common1-visang-hongminpyo-2025 | Astra | 269 | 6,886 |
  | 2022-hs-common1-ybm-bakjuneon-2025 | Astra | 235 | 5,785 |
  | 2022-hs-common1-ybm-gimeunhyeong-2025 | Astra | 287 | 6,321 |
  | 2022-hs-common2-chunjae-gangsanggu-2025 | Astra | 247 | 5,919 |
  | 2022-hs-common2-chunjae-josugyeong-2025 | Astra | 272 | 6,248 |
  | 2022-hs-common2-donga-ibyeongmin-2025 | Astra | 240 | 5,637 |
  | 2022-hs-common2-jihak-sinsanggeun-2025 | Astra | 267 | 6,593 |
  | 2022-hs-common2-mirae-n-gimseongyeon-2025 | Astra | 208 | 5,596 |
  | 2022-hs-common2-ne-minbyeongcheon-2025 | Astra | 281 | 6,656 |
  | 2022-hs-common2-visang-hongminpyo-2025 | Astra | 225 | 5,971 |
  | 2022-hs-common2-ybm-bakjuneon-2025 | Astra | 260 | 6,128 |
  | 2022-hs-common2-ybm-gimeunhyeong-2025 | Astra | 290 | 7,167 |
  | 2022-hs-yeongeo1-chunjae-gangsanggu-2026 | Astra | 400 | 10,078 |
  | 2022-hs-yeongeo1-chunjae-josugyeong-2026 | Astra | 403 | 9,375 |
  | 2022-hs-yeongeo1-donga-bakyongye-2026 | Astra | 326 | 8,420 |
  | 2022-hs-yeongeo1-jihak-sinsanggeun-2026 | Astra | 366 | 8,067 |
  | 2022-hs-yeongeo1-mirae-n-gimseongyeon-2026 | Astra | 299 | 7,132 |
  | 2022-hs-yeongeo1-ne-oseonyeong-2026 | Astra | 361 | 8,712 |
  | 2022-hs-yeongeo1-visang-hongminpyo-2026 | Astra | 282 | 7,701 |
  | 2022-hs-yeongeo1-ybm-bakjuneon-2026 | Astra | 195 | 4,655 |
  | 2022-hs-yeongeo2-chunjae-gangsanggu-2026 | Astra | 230 | 5,375 |
  | 2022-hs-yeongeo2-chunjae-josugyeong-2026 | Astra | 198 | 5,331 |
  | 2022-hs-yeongeo2-donga-bakyongye-2026 | Astra | 170 | 4,458 |
  | 2022-hs-yeongeo2-jihak-sinsanggeun-2026 | Astra | 218 | 5,907 |
  | 2022-hs-yeongeo2-mirae-n-gimseongyeon-2026 | Astra | 202 | 5,199 |
  | 2022-hs-yeongeo2-ne-oseonyeong-2026 | Astra | 177 | 4,481 |
  | 2022-hs-yeongeo2-visang-hongminpyo-2026 | Astra | 55 | 1,322 |
  | 2022-ms-ms1-chunjae-isanggi-2025 | Astra | 313 | 4,219 |
  | 2022-ms-ms1-chunjae-soyeongsun-2025 | Astra | 301 | 4,303 |
  | 2022-ms-ms1-donga-ibyeongmin-2025 | Astra | 275 | 3,704 |
  | 2022-ms-ms1-donga-yunjeongmi-2025 | Astra | 244 | 3,961 |
  | 2022-ms-ms1-jihak-songmijeong-2025 | Astra | 186 | 3,075 |
  | 2022-ms-ms1-mirae-n-munyeongin-2025 | Astra | 353 | 5,071 |
  | 2022-ms-ms1-ne-gimgitaek-2025 | Astra | 296 | 4,074 |
  | 2022-ms-ms1-visang-hwangjongbae-2025 | Astra | 220 | 3,150 |
  | 2022-ms-ms1-ybm-bakjuneon-2025 | Astra | 279 | 4,031 |
  | 2022-ms-ms1-ybm-gimeunhyeong-2025 | Astra | 316 | 4,020 |
  | 2022-ms-ms2-chunjae-isanggi-2026 | Astra | 204 | 3,571 |
  | 2022-ms-ms2-chunjae-soyeongsun-2026 | Astra | 214 | 3,662 |
  | 2022-ms-ms2-donga-ibyeongmin-2026 | Astra | 249 | 4,280 |
  | 2022-ms-ms2-donga-yunjeongmi-2026 | Astra | 174 | 3,416 |
  | 2022-ms-ms2-jihak-songmijeong-2026 | Astra | 164 | 3,076 |
  | 2022-ms-ms2-mirae-n-munyeongin-2026 | Astra | 188 | 3,362 |
  | 2022-ms-ms2-ne-gimgitaek-2026 | Astra | 226 | 4,151 |
  | 2022-ms-ms2-visang-hwangjongbae-2026 | Astra | 226 | 3,568 |
  | 2022-ms-ms2-ybm-bakjuneon-2026 | Astra | 187 | 3,524 |
  | 2022-ms-ms2-ybm-gimeunhyeong-2026 | Astra | 229 | 3,662 |
  | common-english-2-ne-oh-2022 | Fable | 250 | 5,835 |
  | 2026-09-grade-10-incheon | Fable | 280 | 5,660 |
  | listening-test-2025-ms1-02 | Astra | 9 | 112 |
  | office-busan-2025-06-g1 | Astra | 257 | 6,292 |
  | office-busan-2026-06-g1 | Astra | 230 | 5,879 |
  | office-busan-2026-06-g2 | Astra | 252 | 6,082 |
  | office-gyeonggi-2025-10-g1 | Astra | 255 | 5,996 |
  | office-incheon-2025-09-g1 | Astra | 274 | 6,898 |
  | office-seoul-2026-03-g2 | Astra | 256 | 6,227 |
  | All 63 | | 15,647 | 337,598 |

---

## Phase 5: Review and finish

- [ ] T013 Measure the change against `develop`; move CHE-68 to In Review
  and the board status to `in-review`; after CHE-67 merges, merge `develop`
  and run `npm run verify`.
  - 2026-10-01: develop `80a8e6e` (CHE-67 merged) is merged (4f97f75). Size
    against the merge base: 1,669 lines added and 733 deleted, about 1,840
    by the repository's count (3 whole files deleted count as one line
    each). Git does not pair the renamed procedure and test file with
    their old names, so about 500 added lines are moved text; 609 are
    these Spec Kit records and 53 a regenerated docs table. Not split: the
    rename, tier families, the map step and `--unchecked` are one skill's
    change, and the 3-line check fix with its test is what lets this
    feature's records pass the vault check.
- [ ] T014 Develop merge review by a fresh reviewer from another provider;
  resolve findings; review-record commit; ask the develop session for the
  finish slot; check `develop` has not moved; `git flow feature finish`;
  CHE-68 Done with one completion comment; board status `completed`.
