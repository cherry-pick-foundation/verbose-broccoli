# Feature Specification: Grammatical Competence Profiles, Later Batches

**Feature Branch**: `feature/grammatical-competence-batches`

**Created**: 2026-10-02

**Status**: Draft

**Linear issue**: CHE-71

**Input**: Linear issue CHE-71, "Profile the next batches of textbooks and
exams against the grammatical inventory", and the develop session's task
brief of 2026-10-02. Feature 036 (CHE-68, merged into `develop` as
`c1a7c2a`) built and ran the `grammatical-competence` skill on the first
batch: 63 materials of the 2022 curriculum and the four reference mappings,
all in the work vault. This feature profiles the batches that remain, with
that skill unchanged unless a missing capability is shown.

The user decided (2026-10-01 and 2026-10-02):

- Keep the grammatical inventory, each tier family counted as one item.
- The proposer for these batches is Codex `gpt-6.1-sol` at `xhigh` effort,
  started natively through Orca. This replaces the earlier `max` effort and
  terminal route.
- No backfire check step: record the proposer's items (`record
  --unchecked`). Every structure in every sentence is profiled, and one
  record belongs to each actual material.
- Copy originals, never move, rewrite or delete them, into the approved
  reference folders (`~/Documents/20_reference/textbooks/` and `exams/`),
  then admit them with `wiki-raw-import`, only after the user approves the
  exact file list.
- Leave out scanned PDFs without text and photo sets that may carry student
  marks.
- Codex usage: use the weekly limit fully; on an actual usage-limit error,
  stop starting new Codex work, keep finished results and report the reset
  time and remaining work to the develop session. Only the user spends
  reset credits.
- Open, for the user: which batch comes next, and in what order.

## Terms

Feature 036's terms hold. In addition:

- **Batch**: a group of materials of one kind that the user approves and
  that is profiled together. The batches below follow the survey's groups.
- **Exact file list**: every original file that would be copied and admitted
  for a batch, with its source path, SHA-256 digest, size and destination.
  It stays in the private survey folder; the user approves it before any
  copy.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reconcile what remains (Priority: P1)

An agent compares the survey's materials with the profiles that exist in the
work vault and reports which materials still need a profile, by batch, with
current counts, dedupe results and source checks.

**Why this priority**: The survey is two days old and the first batch
changed what remains; the user decides the next batch from these counts.

**Independent Test**: The counts in `tasks.md` T002 to T004 can be
recomputed from the private survey folder and the vault's
`wiki/profiles/` pages; the same read-only comparison gives the same numbers.

**Acceptance Scenarios**:

1. **Given** the 63 recorded profiles, **When** each survey file's
   SHA-256 is compared with the digests of every profile's source revisions,
   **Then** each material is `done`, `partial` or `none`, and every
   `partial` volume is explained.
2. **Given** the materials that remain, **When** every listed file is
   converted to text read-only, **Then** each material is `readable`,
   `scanned or unreadable`, `photo set` or `whole-book PDF`.

---

### User Story 2 - Prepare the user's decision (Priority: P1)

An agent turns the reconciled counts into one batch proposal with a
recommended order, and one exact file list per batch in the private survey
folder, and asks the user (through the develop session) for the batch order
and the first batch's file list.

**Why this priority**: Nothing is copied or admitted without this approval.

**Independent Test**: Each list's file count and total size match the counts
in `tasks.md`; no file outside the four batches is listed; every listed file
has a digest that equals its source's.

**Acceptance Scenarios**:

1. **Given** the reconciled counts, **When** the proposal is sent, **Then**
   it names each batch's materials, files, size and expected work, the items
   left out with reasons, and a recommendation.
2. **Given** an approved first-batch list, **When** the agent copies, **Then**
   every copy's digest equals its source's and every original is untouched.

---

### User Story 3 - Profile the approved batches (Priority: P1)

For each approved batch, the agent copies the approved originals, admits
them, runs one Codex `gpt-6.1-sol` `xhigh` proposer worker per material,
records every profile unchecked, and passes the vault's Wiki check.

**Why this priority**: This is what CHE-71 asks for.

**Independent Test**: The batch's profile pages and data files are in the
work vault, `update` and `check` of the `wiki-consistency` skill report no
problem on them, and `tasks.md` gives the counts per batch.

**Acceptance Scenarios**:

1. **Given** an approved list, **When** the copy ends, **Then** each copy's
   SHA-256 read back from the destination equals the list's digest, and the
   raw import's own `verify` passes.
2. **Given** a material with several files, **When** it is profiled, **Then**
   one record holds every file's sentences.
3. **Given** a usage-limit error from Codex, **When** a worker stops, **Then**
   no new Codex worker starts, finished records stay, and the reset time and
   the unfinished materials are reported to the develop session.

### Edge Cases

- A lesson exists as HWP and HWPX in one volume: the HWPX is profiled; the
  HWP twin is not copied or counted.
- One paper is listed under two materials (same SHA-256): it is one
  material.
- A paper's file the converter cannot read, while its other files can: the
  readable files are profiled and the unreadable one is reported.
- Two exam files share a name in different packages: the destination keeps
  each in its own paper folder.
- A file name holds the literal text `%0A` or `%0D`: `raw_import.py` fails
  on it, so it is reported and not admitted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Current counts MUST come from a read-only comparison of the
  survey list with the vault's profile pages, not from the survey's older
  numbers.
- **FR-002**: Every remaining file MUST be converted to text read-only before
  it is listed; scanned PDFs without text, photo sets and unreadable files
  MUST stay out of the lists.
- **FR-003**: The agent MUST write one exact file list per batch in the
  private survey folder, and MUST NOT copy or admit an original before the
  user approves that list.
- **FR-004**: Originals MUST be copied, never moved, rewritten or deleted;
  each copy's digest MUST be read back and equal its source's.
- **FR-005**: Proposers MUST be Codex `gpt-6.1-sol` at `xhigh` effort,
  started natively through Orca, one per material.
- **FR-006**: Profiles MUST be recorded with `record --unchecked`, every
  sentence of every file, one record per material, tier families counted as
  one item.
- **FR-007**: No source name, source text, inventory text or student datum
  MUST enter the repository, commits, or Orca or Linear messages; records
  and reports give counts and references only.
- **FR-008**: The skill and its script MUST NOT change without a shown
  missing capability.
- **FR-009**: `npm run verify` MUST pass on the result merged with `develop`,
  and a fresh review from another provider MUST precede the finish.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `tasks.md` gives the current counts of materials that remain,
  by batch, and the items left out with their reasons.
- **SC-002**: For every approved batch, its profiles are in the work vault
  with a passing Wiki check and its counts are in `tasks.md`.
- **SC-003**: Every copied original has a read-back digest equal to its
  source's, and the raw import's `verify` reports no invalid revision.
- **SC-004**: `npm run verify` reports VERIFIED on the result merged with
  `develop`.

## Assumptions

- Source file names can name schools, publishers and authors, never
  students; they stay in the private survey folder and the vault.
- Feature 036's proposer prompt and tier rule hold for all kinds of material;
  an exam paper's sentences are those of its English passages, dialogues and
  full-sentence answer choices.
- Work volume is estimated from the English letters a converter reads, at the
  first batch's rates: about 16 sentences per thousand letters for textbooks
  and 12 for exam papers.
