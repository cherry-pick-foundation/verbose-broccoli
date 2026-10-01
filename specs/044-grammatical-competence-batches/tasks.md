---

description: "Task list for grammatical competence profiles, later batches"
---

# Tasks: Grammatical Competence Profiles, Later Batches

**Input**: Design documents from `specs/044-grammatical-competence-batches/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: No repository code changes; acceptance is operational: copy
digests read back, `raw_import.py verify`, the vault's Wiki check and the
counts per material. `npm run verify` runs on the result merged with
`develop`.

**Organization**: One feature orchestrator (Claude Code, Sonnet 5.5 at high
effort) owns these records and the vault steps and asks the develop session
for the user's decisions. Proposers are Orca workers: Codex `gpt-6.1-sol` at
`xhigh`, one per material (the user's fixed choice). The final review comes
from a provider other than the implementer's.

**Private data**: No task writes source names, source text, inventory text or
student data into the repository, commits, or Orca or Linear messages. The
exact file lists and checks are in the private survey folder
(`~/.local/state/verbose-broccoli/grammatical-competence/survey/`).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [x] T001 Write `spec.md`, `plan.md` and this file.
  - 2026-10-02: setup ran from `orca.yaml` under the CPU wrapper, then again
    through the single `mise run setup` task after CHE-74 merged (develop
    `3d4613f`, merged into the branch); `npm run doctor` passed.
  - Model choice for this orchestrator (launch evidence from the develop
    session; probabilities do not prove correctness): backfire Jev
    (OpenRouter `typesafe/jev-1.13`) chose Claude (0.69, confidence 0.62),
    then Sonnet at high effort (0.50, confidence 0.44), for a difficult
    operational scope; Codex weekly use was 68% until 2026-10-03T17:28:48Z,
    Claude session 16% and weekly 55%. The proposers are not chosen this
    way: the user fixed Codex `gpt-6.1-sol` at `xhigh`.

---

## Phase 2: User Story 1 - Reconcile what remains (P1)

- [x] T002 [US1] Compare the survey list with the 63 recorded profiles by
  SHA-256 and dedupe.
  - 2026-10-02 (read-only): of the survey's 512 materials, 63 have a
    profile (55 textbook volumes, 7 office papers, 1 listening paper). The
    historical 439 candidates are now 438: 46 textbook volumes of the 2015
    curriculum, 85 national papers, 133 education-office papers (the survey
    listed 140; 7 are profiled) and 174 middle-school exams, plus 7 photo
    sets that stay out.
  - Not repeated: 11 of the first batch's volumes show as `partial` only
    because the survey also lists 45 HWP copies of lessons that were
    profiled from their HWPX twin (every one has a twin of the same name).
    3 more 2022 entries are whole-book publisher PDFs, not main-text
    worksheets; they are left out.
  - Duplicate: one loose paper is the same file (same SHA-256) as an office
    paper; it counts once. Two office papers and two 2015 files are already
    admitted in the vault but have no profile.
  - Hash groups across stores do not matter for the new lists, because each
    list names one source path per digest.
- [x] T003 [US1] Convert every listed file to text, read-only.
  - 2026-10-02: 1,144 files (every listed file of the 512 materials) with
    `pdftotext -raw` and python-hwpx through markitdown, in the CPU wrapper,
    3 processes. 16 zip members first failed in my script only (a name
    decoding bug), then read after the fix.
  - Left out: 13 national papers that are scanned PDFs without text; 7 papers
    (6 national, 1 office) whose old HWP files the converter cannot read, so
    the user may convert them first; 2 more files inside materials whose other
    files are readable (1 scanned PDF in a national paper, 1 unreadable HWP in
    an office paper); 7 photo sets (46 JPGs); 4 HWP twins in
    2015 volumes.
  - Result: 418 materials can be profiled: 46 textbook volumes, 66 national
    papers, 132 office papers, 174 middle-school exams.
- [x] T004 [US2] Write one exact file list per batch in the private survey
  folder (`lists-2026-10-02/`): source path, SHA-256, size, destination.
  - 2026-10-02: textbooks-2015 46 volumes, 324 files, 59 MB; education-office
    132 papers, 133 files, 131 MB (all inside zips); national-papers 66
    papers, 80 files, 121 MB (34 inside zips); school-middle 174 papers, 174
    HWP files, 50 MB; `excluded.tsv` has the reasons. English letters read:
    1.54 million, 2.81 million, 1.82 million and 1.40 million; at the first
    batch's rates about 25,000, 33,000, 21,000 and 16,000 sentences (the
    first batch had about 15,600).
  - Exam destinations are per-paper folders because 17 file names collide.

---

## Phase 3: User Story 2 - The user's decision (P1)

- [ ] T005 [US2] Ask the develop session for the user's batch order and the
  first batch's exact-list approval.
  - 2026-10-02: asked with counts and the recommendation 1 (2015 textbooks)
    then 2, 3, 4, because the 2015 textbooks use the same worksheet format
    as the profiled 2022 ones, have no unreadable file, and the 2024 to 2026
    grade-3 school exams belong to the 2015 curriculum, so their link to a
    textbook needs batch 1. A first wave of 12 volumes measures real Codex
    `xhigh` use before the rest. Answer pending.

---

## Phase 4: User Story 3 - Profile the approved batches (P1)

Waits for T005. One block per approved batch.

- [ ] T006 [US3] Copy the approved files; read each destination's SHA-256 back
  and compare with the list; write the selection; `raw_import.py admit` and
  `verify`.
- [ ] T007 [US3] Per material: `inventory`, `extract`, one native Orca worker
  (Codex `gpt-6.1-sol`, `xhigh`), `record --unchecked`; counts per material
  in this file.
- [ ] T008 [US3] `wiki-consistency` `update` and `check`, the log entry, a
  vault commit per batch, and the run folders deleted after their record
  commits.

---

## Phase 5: Review and finish

- [ ] T009 Merge the latest `develop`, run `npm run verify` (one full run at
  a time on the machine, in the CPU wrapper), measure the change against
  `develop`, move the board status to `in-review`.
- [ ] T010 Fresh review from another provider that its data scope permits;
  record the reviewed commit; ask the develop session for the finish slot;
  never push, release or merge into `main`.

Unperformed at the time of writing: every Phase 3 to 5 task; no original has
been copied or admitted.
