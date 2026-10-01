# Feature Specification: Grammatical Competence Profiles, Stage 2

**Feature Branch**: `feature/grammatical-competence`

**Created**: 2026-10-01

**Status**: Draft

**Linear issue**: CHE-68

**Input**: Linear issue CHE-68, "Profile all textbooks and exams against the
grammatical inventory (stage 2 of CHE-57)", and the develop session's task
brief of 2026-10-01. Stage 1 (CHE-57, `specs/028-concept-profile/`, merged
into `develop` as `4065748`) built the `concept-profile` skill and piloted it
on one textbook volume and one exam paper
([pilot report](../028-concept-profile/pilot-report.md)). The user decided:

- The skill is renamed `grammatical-competence`. Names that code and records
  add take the CEFR's terms; where one clashes with a source-of-truth file's
  own terms, the file wins. The first catalog is "the first grammatical
  inventory", the level list of grammatical items. Stage 1's merged records
  and branch keep their old names. The specific inventory and reference
  books are named only in vault pages.
- Each word-level tier family of the inventory counts as one item when
  profiling (2026-09-30); the inventory itself stays unchanged.
- An item is kept when the check says `verified` with confidence 0.5 or more
  (2026-09-30; `record --auto-accept`).
- No review queue for the user at this scale: unclear items stay listed as
  unclear in the record.
- The pilot's issues are resolved before any full run: the tier family rule
  in the catalog record, the proposer instructions and the script; one
  written tier rule for every proposer; a rerun of the two pilot materials
  scored against the kept answer key; a proposer that scales to many
  materials; the four inventory-to-reference mappings with a map step that
  keeps Hangul out of backfire; and the list of materials to profile.
- New originals are admitted only after the user approves them.
- Before the full run the user decides the open catalog choice: keep the
  current inventory with tier families collapsed, or switch to the reference
  books' units with levels through a unit-to-inventory mapping.
- Material text, the inventory's text and the answer key stay in the work
  vault and the run folder, never in the repository, commits, Linear or Orca
  messages; reports give counts only. No student data is involved.

## Clarifications

### Session 2026-10-01

- Q: Which names change with the rename? → A: The skill folder, script,
  tests, task wiring and docs become `grammatical-competence`
  (`grammatical_competence.py`), and the run folders move to
  `$XDG_STATE_HOME/verbose-broccoli/grammatical-competence/`. The kept answer
  key and the pilot's two proposals files stay where stage 1 left them.
- Q: Which record names does the rename change? → A: The record kind catalog
  becomes inventory, in `wiki/inventories/`; the vault's grammatical
  inventory page moves there with its links fixed. The template's section
  heading becomes "Inventory records" and its pointer names
  `grammatical-competence`. "Concept" becomes "item" in the script, fields
  and docs: `concepts` becomes `items` in proposal and profile rows, and
  `concept` becomes `item` in mapping rows. The kinds reference, mapping and
  profile keep their names. CHE-69's lexical inventory page follows into
  `wiki/inventories/`.
- Q: After the rerun, which catalog, scope, check and admissions? → A: (1)
  Keep the grammatical inventory, each tier family counted as one item. (2)
  The first batch is the 2022 curriculum's materials: the 58 textbook
  volumes, with exam papers that may belong to that curriculum listed
  separately for the user; everything else waits for later batches. The
  proposer is Codex `gpt-6-astra` (the user's fixed choice); only its effort
  comes from `model-choice`. (3) Skip the check: record the proposer's items
  without backfire, so no OpenRouter credit is spent. (4) Copy, never move,
  only the chosen files from `~/data` into `~/Documents/20_reference/textbooks/`
  (and `exams/` there only if exams are chosen), then admit them; leave out
  the scanned PDFs without text and the photo sets that may carry student
  marks, and show the exact file list and its size first.

## Terms

Stage 1's terms hold, with these names:

- **Inventory**: a level list of items for one competence. The first
  grammatical inventory is the stage 1 catalog. Its vault page is an
  inventory record.
- **Item**: one entry of an inventory; stage 1 called it a concept.
- **Tier family**: inventory rows that share a label and differ only in a
  numbered tier of how wide a range of words they cover. A family counts as
  one item.
- **Section index**: the list of one reference text's sections, each with a
  label and a line range in the reference record's text file.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tier families and a pilot rerun (Priority: P1)

An agent profiles a material with tier families counted as one item: the
inventory record names the family column, `inventory.tsv` lists each family
once, every proposer follows one written tier rule, and the check and the
record use the family's item. The two pilot materials are profiled again and
scored against the kept answer key.

**Why this priority**: Tiers caused 43 of the pilot's 52 false proposals; the
user made the rerun a precondition of the full run.

**Independent Test**: With a synthetic inventory whose rows include a tier
family, `inventory.tsv` lists the family once under its lowest tier's key, a
proposal naming another member's key is refused, the check's claim and
evidence carry every tier's statement and examples, and the record names the
family by its lowest tier's ID.

**Acceptance Scenarios**:

1. **Given** rows with a tier number in the family column and the same label
   after whitespace is collapsed, **When** `inventory` runs, **Then** one line
   lists them with their levels joined by `/` and their statements by `; `.
2. **Given** the rerun's proposals and checks, **When** they are scored
   against the answer key with families collapsed, **Then** the proposer's
   and the kept items' precision and recall are recorded in `tasks.md` with
   their counts.
3. **Given** a check run, **When** it ends, **Then** no review sheet is
   written, and every unclear item stays in its row's unclear list.

---

### User Story 2 - Map the inventory to four reference books (Priority: P1)

An agent maps every item of the inventory to the sections of each reference
book that explain it: one mapping record per book, built with a section
index, proposals of at most three sections per item, and one check for each
item with proposed sections, whose evidence never contains Hangul. An item
with no proposed section gets an empty row and no check.

**Why this priority**: The user listed the mappings among the issues to
resolve before the full run, and the catalog choice depends on them.

**Independent Test**: With a synthetic reference text, section index,
inventory and mapping proposals, `map` and `record` refuse unknown sections
and keys and a mappings file that misses or repeats an item; `map` sends one
call per item with sections, with every proposed section's text minus its
Hangul lines, and resumes after a failure; `record` writes the mapping page
and data file.

**Acceptance Scenarios**:

1. **Given** a section whose text has Hangul lines, **When** it is evidence,
   **Then** those lines are left out and the rest is sent.
2. **Given** mapping checks, **When** the mapping is recorded, **Then** one
   data row per item lists its kept and unclear sections with their line
   ranges.

---

### User Story 3 - Profile the listed materials (Priority: P1)

Once the user has chosen the catalog and approved the material list, every
listed material is admitted, profiled, checked and recorded in the work
vault, and each run's counts are reported.

**Why this priority**: This is what CHE-68 asks for.

**Independent Test**: The materials list, the counts per material in
`tasks.md`, and the records in the work vault with a passing Wiki check on
them.

**Acceptance Scenarios**:

1. **Given** the approved list, **When** the full run ends, **Then** each
   material has a profile record and its counts are in `tasks.md`.
2. **Given** a material whose originals live only in an older store, **When**
   the user approves it, **Then** its files are copied, never moved, to the
   approved folder and admitted from there.

### Edge Cases

- A family has one tier only: it is one item, as before.
- Tiers of a family are not in row order: the lowest tier still gives the
  key and ID.
- A label differs only in inner whitespace between tiers: it is the same
  family.
- A section index entry points past the end of the text file: `map` refuses
  it before any call.
- A mapping proposal names no section: the item gets an empty row.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The skill, its script, tests, task wiring, docs and the vault
  schema template's pointer MUST use the name `grammatical-competence`.
- **FR-002**: The inventory record's block MAY name a `family` column; the
  script MUST then count each tier family as one item in `inventory`,
  `check` and `record`, as User Story 1 describes.
- **FR-003**: The procedure MUST give every proposer one written tier rule.
- **FR-004**: `check` MUST NOT write a review sheet and `record` MUST NOT
  read one; unclear items stay listed as unclear. `record --unchecked` MUST
  record every valid proposal without a check.
- **FR-005**: The two pilot materials MUST be profiled again and scored
  against the kept answer key with families collapsed; the scoring runs
  outside the repository.
- **FR-006**: The proposer for the full run MUST be chosen with the code
  plugin's `model-choice` skill from the rerun's accuracy, time and quota.
- **FR-007**: The script MUST map an inventory to a reference with a section
  index, mapping proposals that list every inventory item exactly once, one
  `jev_verify` call per item with sections and with Hangul lines left out of
  the evidence, resume after a failure, and a mapping record.
- **FR-008**: The four mapping records MUST be built in the work vault.
- **FR-009**: The list of materials MUST be surveyed from the user's local
  stores, and new originals admitted only after the user approves them.
- **FR-010**: The user's catalog choice MUST be recorded in this spec's
  Clarifications before the full run.
- **FR-011**: The full run's first batch MUST profile every approved material
  and report counts per material in `tasks.md`; its records MUST pass the
  vault's Wiki check.
- **FR-012**: No inventory text, material text, reference text or answer key
  MUST enter the repository, commits, or Orca or Linear messages; tests MUST
  use synthetic entries.
- **FR-013**: `npm run verify` MUST pass on the result merged with `develop`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `tasks.md` gives the rerun's precision and recall against the
  answer key, with counts.
- **SC-002**: The four mapping records and every full-run profile record are
  in the work vault, and the vault's Wiki check reports no problem on them.
- **SC-003**: `tasks.md` gives the full run's counts per material.
- **SC-004**: `npm run verify` reports VERIFIED on the result merged with
  `develop`.

## Assumptions

- Stage 1's accuracy is agreement with a Claude-made answer key that the user
  accepted, and so is the rerun's.
- Mappings are checked with backfire's `jev_verify` without education mode,
  because a reference holds no student data; profile checks keep education
  mode, as in stage 1. The first batch's profiles are recorded unchecked, by
  the user's choice.
