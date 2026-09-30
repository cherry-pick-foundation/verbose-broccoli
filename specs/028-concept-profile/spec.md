# Feature Specification: Concept Profiles of Teaching Materials

**Feature Branch**: `feature/grammar-profile`

**Created**: 2026-09-30

**Status**: Draft

**Linear issue**: CHE-57

**Input**: Linear issue CHE-57, "Profile the grammar of every sentence in
school textbooks and past exams against the English Grammar Profile", its
comment of 2026-09-30, and the develop session's task brief of 2026-09-30.
The user decided:

- The first concept catalog is the English Grammar Profile (EGP), read from
  the user's original spreadsheet (1,222 grammar points in 19 categories,
  levels A1 to C2), not from the older JSON conversion, whose entries carry
  fields merged in from other books. The spreadsheet's terms allow internal
  reference only, so its data stays in the private work vault, never in the
  repository or in Orca or Linear messages; tests use synthetic entries.
- Every structure in every sentence is profiled, not only what a lesson
  targets or an exam question tests.
- One independent record per real school textbook volume and one per
  original exam paper. Academy course books come later, once the user has
  their raw files. Records live in the work vault, with their sources
  admitted as raw through the work plugin's `wiki-raw-import` skill, and
  pages follow that vault's schema.
- The catalog stays unchanged. Reference books are mapped to it in separate
  per-book mapping records, never merged into catalog entries: CGEL (The
  Cambridge Grammar of the English Language) and Essential, English and
  Advanced Grammar in Use, one record per book. This feature designs their
  record layout; the user decides whether it also builds them.
- The earlier textbook-to-CGEL matching in the legacy store is dropped. It
  stalled with 1,505 unreviewed candidate links; this design must avoid that.
- Method: a worker model proposes the concepts in each sentence; backfire's
  `jev_verify` checks all of a sentence's proposals in one call against each
  concept's catalog statement and examples. Confident results are kept,
  contradicted ones dropped, and only unclear ones go to the user. Backfire's
  education mode is used wherever text could hold student data. Existing
  tools do the extraction: python-hwpx and markitdown for HWP, HWPX and DOCX,
  and pdftotext for PDF.
- Pilot first: one textbook volume and one original exam paper, picked by
  the user. The user hand-checks about 30 sentences; accuracy against that
  check, backfire calls, tokens and time are brought to the user before any
  full run.
- Stage 1, this feature: the procedure, the minimum glue, the record layouts
  including the per-book mappings, and the pilot. Stage 2, the full run, is a
  later feature.

On 2026-09-30 the user added a naming rule, relayed by the develop session:
nothing built here is named after EGP or grammar. Names are subject-neutral,
so the same mechanism can profile concepts of other subjects later; EGP and
English specifics appear only in the data that describes the first catalog.
The branch and worktree names stay as they are.

## Clarifications

### Session 2026-09-30

- Q: Which textbook volume is the pilot's? → A: Common English 2, NE
  Neungyule (Oh Seon-young), 2022 curriculum: the main-text files of Lessons
  1 to 4 and the Special Lesson, 5 HWPX files.
- Q: The volume's originals are only in the legacy store under `~/data`,
  which the raw-import settings exclude. How are they admitted? → A: Copy
  the five files, keeping their names, into a new folder the user approved,
  `~/Documents/20_reference/textbooks/`, and admit them from there. Only
  copy: nothing under `~/data` moves or changes, and the exclusion stays.
- Q: Which exam paper is the pilot's? → A: The original question paper (PDF)
  of the 2026 September Grade 10 academic assessment (Incheon), from the
  user's midterm folder.
- Q: Are the four reference mappings built in this feature? → A: No. Their
  layout and method are designed here; a later feature builds them.
- Q: Which changes outside the repository are approved? → A: Admitting the
  catalog spreadsheet, the pilot volume and the pilot exam paper into the
  work vault's raw layer; the vault schema change adding catalogs, profiles
  and mappings; writing, logging and committing the catalog record and the
  two pilot profile records in the vault; and the run folder
  `~/.local/state/verbose-broccoli/concept-profile/`, emptied after the
  records are committed.
- Q: What counts as a sentence? → A: Every English sentence in passages,
  dialogues and full-sentence English answer choices; Korean text, headings,
  labels and phrase-only choices are skipped.

## Terms

One term per idea, used in every name this feature adds:

- **Catalog**: a subject's list of concepts. EGP is the first catalog:
  subject English, grammar points as concepts, levels A1 to C2.
- **Concept**: one catalog entry, with an ID, a label, a level, a statement
  and examples.
- **Material**: one thing that is profiled: a school textbook volume or an
  original exam paper. A material has one or more raw sources (for a
  textbook volume, usually one file per lesson).
- **Profile**: the record of one material: every sentence, in order, with
  the concepts it shows.
- **Reference**: a book that explains concepts, such as CGEL or a Grammar in
  Use book.
- **Mapping**: the record that links each concept of one catalog to the
  sections of one reference that explain it.
- **Proposal**: a concept that the proposer (a worker model) says a
  sentence shows, or a reference section it says explains a concept.
- **Check**: one `jev_verify` call on all proposals of one sentence (or of
  one concept, for a mapping).
- **Outcome**: each proposal ends as **kept**, **dropped** or **unclear**.
- **Run folder**: the working folder of one profiling or mapping run, outside
  the repository and the vault.
- **Review sheet**: a Markdown file in the run folder where the user decides
  unclear proposals or hand-checks sentences.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Profile one material (Priority: P1)

An agent profiles one material, for example a textbook volume, in the work
vault by following the work plugin's `concept-profile` skill. The material's
files and the catalog are admitted as raw; the text is extracted with
existing tools; a proposer model proposes concepts per sentence; the
script checks each sentence's proposals with backfire in one call and sorts
them into kept, dropped and unclear; the user decides only the unclear ones
on a review sheet; the profile record is written and committed in the vault.

**Why this priority**: This is the capability the issue asks for.

**Independent Test**: With a synthetic vault holding a synthetic catalog and
a synthetic material, the script's commands produce the check requests,
sort stubbed backfire results into the three outcomes, write a review sheet
for the unclear ones, apply the user's decisions and write the record, whose
data file and page follow the layout in [plan.md](plan.md).

**Acceptance Scenarios**:

1. **Given** proposals for a sentence, **When** the check runs, **Then** one
   `jev_verify` call carries every proposal of that sentence as a claim, with
   the sentence and each proposed concept's statement and examples as
   evidence.
2. **Given** a result that is `verified` with action `auto`, **When** it is
   sorted, **Then** the concept is kept; `contradicted` or `unsupported` with
   action `auto` is dropped; anything else (`review`, `unknown`,
   `invalid_response`) is unclear.
3. **Given** a proposal whose sentence does not occur in the extracted text,
   or whose concept key is not in the catalog, **When** the script reads it,
   **Then** it names every such proposal and sends and writes nothing, so the
   proposer fixes the file first.
4. **Given** a run interrupted during checks, **When** it is rerun, **Then**
   sentences already checked are not sent again.
5. **Given** unclear proposals, **When** the user returns the review sheet,
   **Then** the record keeps the ticked ones and drops the unticked ones;
   **When** the sheet has not been returned, **Then** every unclear proposal
   stays listed as unclear.

---

### User Story 2 - Pilot measures accuracy and cost before a full run (Priority: P1)

The user picks one textbook volume and one original exam paper. Both are
profiled. The user hand-checks about 30 sampled sentences on a sheet that
shows every proposal without its outcome. Accuracy, backfire calls, tokens
and time are reported to the user, who decides whether and how the full
run goes ahead.

**Why this priority**: The user made the pilot a precondition for stage 2.

**Independent Test**: The pilot report states, for the sampled sentences,
the precision of kept concepts, the recall of the record, how many dropped
concepts the user marked as present, the unclear share, and the proposer's
recall; and for the whole pilot, the number of backfire calls, their tokens,
the proposer's tokens where the agent reports them, and wall-clock time per
step. The user's decision on the full run is recorded in
[tasks.md](tasks.md).

**Acceptance Scenarios**:

1. **Given** the hand-check sheet, **When** the user reads it, **Then** each
   sampled sentence lists every proposed concept unchecked, in catalog order,
   with no sign of its outcome, and has a line for missing concept IDs.
2. **Given** the user's marks, **When** accuracy is computed, **Then** the
   numbers above are reported with their counts, not only as percentages.

---

### User Story 3 - Map a catalog to a reference book (Priority: P2)

An agent maps every concept of a catalog to the sections of one reference
book that explain it, in one mapping record per book, with the same
propose, check and decide method. This feature designs the layout and the
procedure; a later feature builds the four mappings (Clarifications).

**Why this priority**: The user asked for the design now and the build
later.

**Independent Test**: The procedure and [plan.md](plan.md) give the mapping
record's page and data layout, how a reference section is addressed, and the
rules that keep unclear links from piling up.

**Acceptance Scenarios**:

1. **Given** the mapping layout, **When** a reader looks up a concept, **Then**
   one data row per concept lists the kept sections and any unclear ones.
2. **Given** a run whose unclear share exceeds the limit agreed in the pilot,
   **When** the run ends, **Then** it stops for a method change instead of
   filling a review queue.

### Edge Cases

- A sentence has no proposal: it stays in the record with an empty concept
  list, so the record still lists every sentence.
- A sentence occurs twice in a material: each occurrence is its own row.
- Extracted text splits a sentence over lines or pages: whitespace is
  normalized before the verbatim test.
- A source is a scanned PDF with no text layer: extraction reports it and the
  material is not profiled until the user decides.
- Backfire fails (a transport or tool error): the run stops before anything
  is written for that sentence, and rerunning resumes there. A single result
  that comes back `unknown` (`invalid_response`) is unclear and counted.
- A catalog cell holds several examples: all of them go into the evidence.
- The material could hold student data (for example a school's own exam with
  names in it): backfire runs in education mode, which replaces roster names
  before anything leaves.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The work plugin MUST gain a skill, `concept-profile`, whose
  `SKILL.md` gives when to use it and links a reference file,
  `references/procedure.md`, that holds the procedure and the record layouts.
- **FR-002**: The procedure MUST admit every source (catalog spreadsheet,
  material files, reference extractions) through `wiki-raw-import`, and read
  them only from their raw revisions.
- **FR-003**: The procedure MUST extract text with existing tools: python-hwpx
  and markitdown for HWP, HWPX and DOCX, and pdftotext for PDF.
- **FR-004**: The procedure MUST have a proposer model list, for every
  English sentence of a material, every concept the sentence shows, in a
  documented proposal file format.
- **FR-005**: A script MUST check all proposals of one sentence in one
  `jev_verify` call on the work plugin's backfire in education mode, with
  claim wording taken from the catalog record, and sort each result into
  kept, dropped or unclear by the rule in User Story 1, scenario 2.
- **FR-006**: The script MUST refuse proposals whose sentence is not verbatim
  in the extracted text (after whitespace normalization) or whose concept key
  is not in the catalog, before any check is sent.
- **FR-007**: The script MUST resume an interrupted check run without
  re-sending checked sentences, and keep its working files within a stated
  storage budget, with cleanup after the record is committed.
- **FR-008**: The script MUST write unclear proposals to a review sheet and
  apply the user's marks from it.
- **FR-009**: The script MUST write the profile record (page and data file)
  in the layout of [plan.md](plan.md); the page MUST pass the vault's
  `wiki-consistency check`.
- **FR-010**: Names of the skill, script, commands, record folders, fields
  and files MUST be subject-neutral; catalog-specific names, columns, levels
  and claim wording MUST come from the catalog record in the vault.
- **FR-011**: No catalog data, material text or student data MUST enter the
  repository, commits, or Orca or Linear messages; tests MUST use synthetic
  entries.
- **FR-012**: The vault schema template
  (`plugins/work/skills/wiki-raw-import/assets/AGENTS.md`) MUST describe the
  catalog, profile and mapping records, and the live work vault's schema MUST
  follow it once the user approves the vault change.
- **FR-013**: The procedure MUST describe the mapping record and its method,
  including the limits that keep unclear links from piling up.
- **FR-014**: The pilot MUST profile the user's chosen volume and exam paper
  and report accuracy against the user's hand-check of about 30 sentences,
  backfire calls, tokens and time, and record the user's decision on the full
  run.
- **FR-015**: Nothing outside the repository (vault changes, raw admissions,
  run folders) MUST be created before the user approves it.
- **FR-016**: `npm run verify` MUST pass on the result merged with `develop`.

### Key Entities

- **Catalog record**: a vault page naming the catalog's raw spreadsheet and
  describing its columns, levels and claim wording.
- **Profile record**: a vault page and a JSON Lines data file, one row per
  sentence.
- **Mapping record**: a vault page and a JSON Lines data file, one row per
  concept.
- **Proposal file**, **check results**, **review sheet**: working files in
  the run folder.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The two pilot records exist in the work vault, list every
  English sentence of their materials, and pass `wiki-consistency check`.
- **SC-002**: The pilot report gives precision, recall, drop accuracy, the
  unclear share and the proposer's recall on about 30 hand-checked sentences,
  with their counts, and the calls, tokens and time of each step.
- **SC-003**: The user decides on the full run after seeing SC-002.
- **SC-004**: `rg -i 'egp|grammar'` finds no match in the names the feature
  adds (skill, script, commands, fields, record folders).
- **SC-005**: `npm run verify` reports VERIFIED on the result merged with
  `develop`.

## Assumptions

- A confident `unsupported` result counts as dropped: the evidence holds the
  sentence and the concept's statement and examples, so confident silence
  means the sentence does not show the concept. The pilot measures how often
  a dropped concept was in fact present.
- The proposer is an Orca worker whose agent, model and effort come from the
  code plugin's `model-choice` skill. A direct API proposer for stage 2 is a
  later decision informed by the pilot's token and time numbers.
- Pilot measurement (sampling, the hand-check sheet, scoring) is done in the
  run folder and not kept as repository code.
