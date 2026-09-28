# Feature Specification: Wiki Storage and Raw Documents

**Feature Branch**: `feature/wiki-storage`

**Created**: 2026-09-27

**Status**: Draft

**Linear issue**: CHE-7

**Input**: Work item H, "Raw documents and Wiki storage", in the addendum "raw
documents and the Wiki storage" of the brief
`briefs/2026-09-27-governance-policies.md` (outside the repository), handed to
this feature by `briefs/2026-09-27-linear-and-documents.md`, "Overview and
order". The user decided on 2026-09-27:

- Use constitution principle VI's layout as is: the default Wiki instance is
  `~/.local/share/verbose-broccoli/wikis/default/` with the schema `AGENTS.md`,
  `raw/{web,files,notes,assets}/` and `wiki/`; configuration, state and cache
  go in the matching XDG (freedesktop.org base directory) roots. Raw files in a
  hidden folder are fine because people do not browse them.
- Admit raw evidence by copying, never by moving. The original location stays
  the user's workspace, and `raw/` gets an unchanged copy with its source
  recorded (original path, date, SHA-256), so a changed original becomes a new
  revision. Folders owned by other programs (Zotero in `~/Zotero`, the ownCloud
  sync folder `~/ownCloud`) stay where they are; only selected items are
  copied.
- The user's own work (lesson materials, edited exam papers, deliverables)
  stays in `~/Documents`. Student records and other operational data,
  conversation records and legacy backups stay outside the Wiki.
- `~/projects/work/{concepts,decisions,stable,draft}` are old wiki-like trees,
  read only as references; `~/projects/work/{sources,materials,intake}` are raw
  candidates.
- The brief's table of candidate locations holds first judgments only. The
  user confirms each item, and nothing is copied before that confirmation.
  Deleting or moving anything the user owns needs the user's approval first.

Item H.1 of the same addendum, removing `conversations` from the example Wiki
schema `docs/examples/wiki/AGENTS.md`, was done by feature 006 (commit
`7b30d41`) and is not repeated here.

Copying the user's documents is importing existing user data, which
constitution principle IV makes a separately specified capability with its own
ownership, verification and recovery checks before any affected write. This
feature specifies that capability and the one-time import of the confirmed
locations.

## Clarifications

### Session 2026-09-27

- Q: How much of the default instance does this feature create, given that
  principle VI requires every instance to contain the Raw, Wiki and Schema
  layers? → A: A minimal complete instance: `raw/` with the admitted copies, a
  schema `AGENTS.md` that states only the raw admission and provenance rules,
  and `wiki/` with empty `index.md` and `overview.md` and a `log.md` that gets
  one entry per import, versioned by Git with `raw/` excluded; no Wiki pages
  are generated. The orchestrator answered on 2026-09-28 from the governance
  brief's addendum H, which already fixes the layout ("holds `AGENTS.md` (the
  schema), `raw/{web,files,notes,assets}/` and `wiki/`"), and principle VI,
  which requires all three layers in every instance.

## User Scenarios & Testing *(mandatory)*

The actors are the user, who owns the documents and confirms every admission,
and a coding agent (Claude Code or Codex) that runs the import on the user's
behalf.

### User Story 1 - A confirmed document becomes raw evidence with its source recorded (Priority: P1)

The user confirms that a document, for example an original exam paper, is raw
evidence. The agent copies it into the default Wiki instance's `raw/`. The copy
is byte-for-byte identical, the original is untouched, and the copy carries a
record of where it came from: the original path, the original's modification
time, the admission date and its SHA-256 digest. Anyone can later check that
the copy still matches its record.

**Why this priority**: This is the core capability. Without it nothing enters
the Wiki's evidence layer.

**Independent Test**: With synthetic fixture files in a temporary home folder,
admit one file, then compare the copy's bytes with the original, read back its
source record, check that the original's bytes and modification time are
unchanged, and run the integrity check on the copy.

**Acceptance Scenarios**:

1. **Given** a confirmed original file, **When** it is admitted, **Then**
   `raw/` holds one new source revision whose copy has the same bytes and
   SHA-256 digest as the original, and whose record names the original path,
   the original's modification time and the admission date.
2. **Given** an admitted revision, **When** the integrity check runs, **Then**
   it passes; **When** a byte of the copy or of its record is changed, **Then**
   the check fails and names the revision.
3. **Given** an admission, **When** it finishes or fails, **Then** the
   original's bytes, modification time and location are unchanged.
4. **Given** an original that cannot be read, **When** it is admitted,
   **Then** the admission stops for that item with a message and `raw/` gains
   nothing for it.

---

### User Story 2 - A changed original becomes a new revision; an unchanged one adds nothing (Priority: P1)

The user keeps working on documents in their own folders. When the same
selection is imported again, an original whose bytes changed since its last
admission becomes a new revision of the same source, and the earlier revision
stays readable. An original whose bytes did not change adds nothing.

**Why this priority**: The brief's reason for recording provenance is that a
changed original becomes a new revision. It also makes a rerun after an
interruption safe.

**Independent Test**: Admit a fixture file, import again unchanged, change the
fixture, import again, and inspect the revisions and their records.

**Acceptance Scenarios**:

1. **Given** an admitted original whose bytes are unchanged, **When** the
   selection is imported again, **Then** no revision is added and the report
   lists the item as already admitted.
2. **Given** an admitted original whose bytes changed, **When** the selection
   is imported again, **Then** the same source gains one new revision with the
   new digest, and every earlier revision keeps its bytes and passes the
   integrity check.
3. **Given** an original whose bytes changed back to an earlier revision's
   bytes, **When** it is imported again, **Then** a new revision is added,
   because the latest revision differs; earlier revisions are never reused or
   reordered.

---

### User Story 3 - Nothing is admitted without the user's confirmation, and excluded data never enters (Priority: P1)

Before anything is copied, the agent presents each candidate location with its
size, file counts and first judgment, and the user confirms or changes the
judgment. For locations the user admits, the agent prepares the exact list of
files to copy, and the user approves that list. Only approved files are
copied. Student records and other operational data, conversation records,
legacy archives and program-owned folders are never copied unless the user
explicitly selects an item from a program-owned folder.

**Why this priority**: Principle IV stops any write whose ownership is unknown,
and principles III and VI keep operational and private data out of the Wiki.
A wrong copy of private data is hard to take back.

**Independent Test**: Run the import with a selection that includes an
unconfirmed location, a file outside the approved list and a file under an
excluded location, and check that none of them is copied and each is reported.

**Acceptance Scenarios**:

1. **Given** a candidate location without the user's confirmation, **When**
   the import runs, **Then** nothing from it is copied.
2. **Given** an approved file list, **When** the import runs, **Then** exactly
   the listed files are admitted and every other file is left alone.
3. **Given** a listed file whose path lies under an excluded location, **When**
   the import runs, **Then** it is refused and reported, and nothing is copied
   for it.
4. **Given** any import, **When** it finishes, **Then** the product repository
   holds no copied file, file content or private file name, and repository
   records give only counts, sizes and folder-level judgments.

---

### User Story 4 - An interrupted import leaves no partial evidence and can be rerun (Priority: P2)

An import of hundreds of files can be interrupted by a crash, a full disk or
the user stopping it. Afterwards `raw/` holds only complete, verified
revisions, and running the same import again finishes the remaining items
without duplicating finished ones.

**Why this priority**: Principle IV requires recovery checks before any write,
and principle V requires recovery at the relevant failure points.

**Independent Test**: Interrupt an import of fixture files at each failure
point (during a copy, after a copy before its record is complete, and before a
finished revision is published), then inspect `raw/` and rerun.

**Acceptance Scenarios**:

1. **Given** an import interrupted at any point, **When** `raw/` is inspected,
   **Then** every revision in it is complete and passes the integrity check,
   and no partial copy is visible there.
2. **Given** an interrupted import, **When** it is run again with the same
   selection, **Then** the remaining items are admitted and the finished items
   are reported as already admitted.
3. **Given** a failure on one item, **When** the import continues, **Then**
   the other items are processed and the report lists the failed item and its
   reason; the import is not reported as complete.

---

### User Story 5 - The default Wiki instance exists in the constitution's layout (Priority: P2)

After this feature, the default Wiki instance exists at
`~/.local/share/verbose-broccoli/wikis/default/` in principle VI's layout, so
later features (Wiki ingest, Wiki document consistency) find it where the
constitution says. Its layers are exactly those decided in the Clarifications
section.

**Why this priority**: The instance is the target of every admission, but it
has no value of its own until documents are admitted.

**Independent Test**: Create the instance in a temporary home folder, list its
layout, and create it again to see that nothing changes.

**Acceptance Scenarios**:

1. **Given** no instance, **When** the instance is created, **Then** it has
   `raw/web/`, `raw/files/`, `raw/notes/` and `raw/assets/` and the other
   layers decided in the Clarifications section, and no folder for
   conversation records.
2. **Given** an existing instance, **When** creation runs again, **Then**
   nothing in it changes.
3. **Given** the instance's versioned tree, **When** its history is
   inspected, **Then** no raw file or raw record appears in it.

---

### User Story 6 - The user's confirmed documents are imported (Priority: P3)

With stories 1 to 5 in place, the agent walks the user through the candidate
locations one by one, records each decision, and imports the approved files
from the user's real folders. The user can see what was admitted, what was
left out and why.

**Why this priority**: It applies the capability to the real data. It depends
on the user's decisions for each location.

**Independent Test**: After the import, the report lists for each location its
decision and the counts admitted, skipped as already admitted, refused and
failed; the integrity check passes over all of `raw/`; and the originals are
unchanged.

**Acceptance Scenarios**:

1. **Given** the candidate locations, **When** the user has decided on each,
   **Then** each decision is recorded in this feature's task list with the
   location, the first judgment and the user's decision, without file names or
   contents.
2. **Given** the approved file lists, **When** the import finishes, **Then**
   every approved file has a verified revision, and every original is
   unchanged.

---

### Edge Cases

- Two approved files have identical bytes but different paths: each is its own
  source with its own record; admission does not merge sources by content.
- An original is renamed or moved after its admission: a later import sees a
  new path. Whether it is the same source is the user's decision; the default
  is a new source, and the earlier source stays as it is.
- An original changes while it is being copied: the copy's digest does not
  match the digest taken before and after copying, so the item fails and is
  reported; nothing is published for it.
- An original is a symbolic link, a device, a socket or a folder: only regular
  files are admitted; others are refused and reported. An approved folder is
  expanded into its regular files before approval.
- A file name holds characters that are unusual on Linux (spaces, Korean
  text, leading dashes): the copy and the recorded path keep the exact name.
- The target file system runs out of space: the item fails, no partial
  revision appears in `raw/`, and the report says why.
- The same import runs twice at once: the second run refuses to start while
  the first holds the instance.
- A candidate location does not exist or is empty: it is reported and
  skipped.
- A file under a program-owned folder (`~/Zotero`, `~/ownCloud`) is approved:
  it is copied like any other file; the program's own database, logs and sync
  state are never copied.
- The integrity check finds a damaged revision: it reports the revision and
  changes nothing; repairing it is the user's decision.

## Requirements *(mandatory)*

### Functional Requirements

**Wiki instance**

- **FR-001**: The capability MUST create the default Wiki instance at
  `$XDG_DATA_HOME/verbose-broccoli/wikis/default/` (by default
  `~/.local/share/verbose-broccoli/wikis/default/`) with the layers decided in
  the Clarifications section, including `raw/web/`, `raw/files/`, `raw/notes/`
  and `raw/assets/`, and no folder for conversation records.
- **FR-002**: Creating the instance again MUST change nothing that exists.
- **FR-003**: Raw files and their records MUST NOT enter the Wiki's versioned
  knowledge tree or the product repository.

**Admission**

- **FR-004**: Admission MUST copy, never move: the original's bytes,
  modification time and location stay unchanged.
- **FR-005**: Each admitted original MUST produce one source revision in
  `raw/` whose copy is byte-for-byte identical to the original and whose
  record gives the original path, the original's modification time, the
  admission date, the SHA-256 digest and a stable source identifier.
- **FR-006**: A revision's copy and record MUST NOT change after admission.
  The capability MUST NOT edit or delete an admitted revision.
- **FR-007**: The capability MUST offer an integrity check that confirms each
  revision's copy against its recorded digest, reports every mismatch and
  changes nothing.
- **FR-008**: When an original's current digest equals its source's latest
  revision, admission MUST add nothing and report the item as already
  admitted. When it differs, admission MUST add a new revision to the same
  source and keep every earlier revision.
- **FR-009**: A source's revisions MUST be found from the records inside
  `raw/` alone; the capability MUST NOT keep a separate list, index or
  database of sources or revisions that could disagree with them.
- **FR-010**: Only regular files MUST be admitted. The digest MUST be checked
  on the original before copying, on the copy, and on the original after
  copying; any difference fails the item.

**Confirmation and ownership**

- **FR-011**: The capability MUST copy only files named in a selection the
  user has approved. It MUST NOT discover or add files by itself during the
  import.
- **FR-012**: The import MUST refuse any selected file under an excluded
  location: the Wiki's own data, state and cache folders, and every location
  the user excludes at confirmation, which for this user starts with the
  student records folder (`~/projects/work/students`), conversation records
  and legacy archives (`~/data`). The user's exclusions MUST live in the
  user's configuration, not in the product repository.
- **FR-013**: Before any real import, the agent MUST present each candidate
  location with its size, file counts by type and first judgment, record the
  user's decision, and have the user approve the file list for every admitted
  location.
- **FR-014**: Selections, reports and other outputs that name the user's files
  MUST stay outside the product repository. Repository records MUST give only
  counts, sizes and folder-level judgments.

**Recovery**

- **FR-015**: A revision MUST appear in `raw/` only when its copy and record
  are complete and verified; an interruption at any point MUST leave no
  partial revision in `raw/`.
- **FR-016**: Rerunning an interrupted or partly failed import with the same
  selection MUST admit the remaining items and add nothing for finished ones.
- **FR-017**: A failure on one item MUST NOT stop the other items. The import
  report MUST list each item as admitted, already admitted, refused or failed,
  with a reason for the last two, and MUST NOT report success while any item
  was refused or failed.
- **FR-018**: Temporary files of an import MUST live in the cache root and
  MUST be removed when the run ends; leftovers of an interrupted run MUST be
  removed when the next run starts. Resuming MUST NOT depend on any progress
  record other than `raw/` itself.
- **FR-019**: Only one import at a time MUST run against an instance.

**Data boundaries**

- **FR-020**: The capability MUST NOT delete, move or change any file outside
  the Wiki instance and its own state and cache folders.
- **FR-021**: Automated acceptance MUST use synthetic fixtures only; no user
  document, file name or content may enter a committed fixture, snapshot or
  report.

### Key Entities

- **Wiki instance**: The default instance folder and its layers under the
  data root, as principle VI defines them.
- **Candidate location**: A folder the brief names as a possible source, with
  its size, file counts, first judgment and the user's decision.
- **Selection**: The user-approved list of original files to admit, each with
  its raw kind (`web`, `files`, `notes` or `assets`). Lives outside the
  repository.
- **Source**: One original document admitted into `raw/`, identified by a
  stable identifier assigned at its first admission.
- **Source revision**: One immutable copy of a source's bytes with its record:
  original path, original modification time, admission date and SHA-256
  digest.
- **Import report**: Per-item outcome of one import run (admitted, already
  admitted, refused, failed and reason). Lives outside the repository.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the automated acceptance, 100% of admitted fixture files have
  byte-identical copies whose recorded digest matches, and 100% of originals
  keep their bytes and modification times.
- **SC-002**: In the automated acceptance, every interruption point in User
  Story 4 leaves `raw/` with only revisions that pass the integrity check, and
  a rerun completes the import with no duplicate revision.
- **SC-003**: Re-importing an unchanged selection adds zero revisions; changing
  one fixture file adds exactly one.
- **SC-004**: Every refusal case in User Story 3 copies nothing.
- **SC-005**: After the real import, the integrity check passes for every
  revision in `raw/`, and every file in the approved selection is either
  admitted or listed as failed with a reason.
- **SC-006**: The product repository gains no user file, file content or
  private file name; `deno task check` passes.

## Assumptions

- "Date" in the brief means both the original's modification time and the
  admission date; both are recorded.
- A source is one original file. Folders are expanded into files at
  selection time, so each file has its own revisions.
- A new original path starts a new source unless the user says it continues an
  existing one.
- Raw kinds: the user's documents go to `files/` by default; `notes/` holds
  the user's own text notes, `assets/` images and other media, and `web/`
  captured web pages. The selection states each file's kind.
- The capability runs on the development machine for the user's home folder;
  the Wiki instance, state and cache roots are on one file system (checked on
  2026-09-27: the home folder is one file system).
- `registry.json` in the data root is not created by this feature; no current
  consumer chooses among Wikis. The feature that first needs it specifies it.
- Backing up the data root is the user's matter; this feature guarantees only
  that originals stay untouched and that admitted revisions are never changed.
- Excluding locations is by path. Private data inside a file the user approved
  is the user's decision at approval; the agent points out files whose names
  or locations suggest operational or private data.
- No scheduler watches originals for changes; a changed original becomes a new
  revision when the user asks for another import.

## Out of Scope

- Generating Wiki pages from raw evidence, and any ingest, query or lint
  workflow beyond raw admission.
- Wiki document consistency (feature 010) and repository document consistency
  (feature 008).
- Deleting, moving or reorganizing any of the user's original folders,
  including the old wiki-like trees under `~/projects/work`.
- Converting raw documents to Markdown or building search indexes.
- Admitting web pages by fetching them; `raw/web/` is created but filled only
  from files the user selects.
