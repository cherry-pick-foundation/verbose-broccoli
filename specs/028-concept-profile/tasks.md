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

- [x] T002 [US1] Create `plugins/work/skills/concept-profile/SKILL.md` and
  `references/procedure.md`: the procedure (admit, extract, propose, check,
  review, record, consistency, cleanup), the proposer's instructions and
  proposal format, the record layouts including the mapping record and its
  method, and the limits that keep unclear items from piling up (FR-001 to
  FR-004, FR-010, FR-013; plan.md "Record layouts", R5).
- [x] T003 [US1] Create `scripts/concept_profile.py` with the `catalog`,
  `extract`, `check` and `record` commands, and
  `scripts/concept_profile_test.py`; wire `test:concept-profile` into
  `package.json` and `turbo.json`; regenerate `docs/` (FR-005 to FR-011;
  plan.md "Script", "Run folder and working files").
  - T002 to T004: Codex `gpt-6-luna` at max (backfire: model 0.45,
    confidence 0.38; effort 0.46, confidence 0.37), through the terminal
    launch path because Orca caps this model at xhigh.
  - 2026-09-30 handoff (computer restart): the worker was stopped after
    about 30 minutes, uncommitted. Done in the worktree: SKILL.md,
    references/procedure.md, the script (713 lines after formatting) and its
    tests (572 lines, 6 passing), the test wiring in package.json and
    turbo.json, and the template section. Main's follow-ups not yet
    confirmed as applied: catalog.tsv without the catalog ID column, one
    backfire session per check run, `record` replacing an existing record,
    `--proposer` on `record`, the template's `topics: []` kept and the
    section moved after "Pages", and trimming. Next: a fresh implementer
    (same choice) reviews the uncommitted files against the spec and these
    follow-ups, trims, runs `npm run verify` and commits.
  - 2026-09-30 after the restart: the stopped dispatch stays as it was; a new
    task takes over the draft with a hard trim (script at most 350 lines,
    tests at most 250). Claude Code `sonnet` at high (backfire through
    develop's provider order, OpenRouter Jev: model 0.46, confidence 0.40;
    effort 0.51, confidence 0.43). The first call failed on Hive with an
    empty provider answer; the user chose one retry from develop's backfire.
  - 2026-09-30 done: commits fd97217 (T002), e382259 (T003), 82527dd (T004)
    and, after main's review, b7ad08c (T003: a backfire failure stops the
    run so a rerun resumes, instead of marking the rest unclear). Script 344
    lines, tests 246, procedure 217, SKILL.md 13; `npm run verify` VERIFIED.
    Main merged develop (b1eb510) in between and ran its setup.
- [x] T004 [US1] Add the catalog, profile and mapping records to the vault
  schema template `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  pointing to the `concept-profile` skill for their layout (FR-012).

---

## Phase 3: User Story 2 - Pilot (P1)

**Goal**: Two pilot records in the work vault and the numbers for the
user's decision.

**Independent Test**: `wiki-consistency check` passes on the vault; the
report gives the numbers SC-002 names; the user's decision is recorded
below.

- [x] T005 [US2] Copy the pilot volume's five main-text files from the legacy
  source cache into `~/Documents/20_reference/textbooks/`, keeping their
  names; admit them, the exam paper and the catalog spreadsheet into the
  work vault with `wiki-raw-import`.
  - 2026-09-30: main. Five files copied and matched by SHA-256; admitted 6,
    already admitted 1 (the exam paper, admitted 2026-09-28), refused 0,
    failed 0; `verify` passed; logged and committed in the vault.
- [ ] T006 [US2] Bring the vault's `AGENTS.md` in line with the template
  (T004); write the catalog record; run `catalog` and `extract` for each
  material in its own run folder (depends on T003, T004, T005).
  - 2026-09-30: vault schema section added and catalog record written
    (uncommitted in the vault until the pilot records join them); both run
    folders hold catalog.tsv (1,222 concepts) and the extracted texts. The
    vault's `check` fails on 171 lines of earlier pages (Linear CHE-58 and
    moved worksheet folders), none on this feature's pages.
- [x] T007 [P] [US2] Propose concepts for every sentence of the volume into
  its `proposals.jsonl` (depends on T006).
- [x] T008 [P] [US2] Propose concepts for every sentence of the exam paper
  into its `proposals.jsonl` (depends on T006).
  - T007 and T008: Claude Code `fable` at xhigh (backfire: model 0.70,
    confidence 0.66; effort 0.48, confidence 0.39).
  - 2026-09-30 done: the volume 250 sentences, 7,352 proposals, about 19
    minutes; the exam 281 sentences, 6,247 proposals, about 24 minutes. The
    exam paper's default pdftotext order split 13 sentences across columns;
    extraction now uses `pdftotext -raw` (d3d79e6), which keeps them whole.
- [ ] T009 [US2] Run `check` for both materials; write the hand-check sheet
  of 30 sampled sentences; ask the user to return it and the review sheets.
  - 2026-09-30: a 5-sentence probe found `result.isError` (mcp 2.2.0 has
    `is_error`) and calls of about 86,000 tokens that failed above 30
    claims; fixed with one evidence text per call (2c6045e). Check: 531
    sentences, 530 calls, 7.6 million tokens, about 3 minutes, about $0.28;
    2,047 kept, 1 dropped, 11,551 unclear, 12 invalid. The unclear-item
    sheet is not sent (too many to review); the hand-check sheet (30
    sentences, 783 proposals) went to the user.
- [ ] T010 [US2] Run `record --reviewed`, `wiki-consistency update` and
  `check`, log and commit in the vault; score the hand-check; report
  accuracy, calls, tokens and time to the user and record the decision on
  the full run here; delete the run folders.

---

## Phase 3b: Reference books in the vault (FR-017)

- [x] T013 [US3] Add the reference record to the procedure and the vault
  schema template, and address mapping sections in its text file.
  - 2026-09-30: main, 0c7d344.
- [x] T014 [US3] Admit the four reference PDFs with `wiki-raw-import`; write
  the four reference pages with their unchanged text files; bring the vault
  schema in line; run `wiki-consistency update` and `check`, log and commit
  in the vault.
  - 2026-09-30: main. The PDFs were already admitted on 2026-09-28 (rerun:
    4 already admitted); each extraction's recorded digest matches its bag.
    Vault commit aea4652: 4 pages and 4 unchanged text files in
    wiki/references/. Check: 0 problems on these pages. Judgment step: 4
    units unverifiable (they describe the extraction, which the PDFs cannot
    confirm); semantic search was not ready after a 30-minute index. The
    Advanced Grammar in Use text has 7 Hangul lines that the mapping
    feature must keep out of backfire calls.

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
