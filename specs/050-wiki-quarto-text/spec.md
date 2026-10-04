# Feature Specification: Persistent Text and Quarto Wiki

**Feature Branch**: `feature/wiki-quarto-text`

**Created**: 2026-10-04

**Status**: Implementation in progress; final acceptance pending

**Linear issue**: CHE-84

**Input**: User-approved F1 scope, relayed through develop Run
`run_9cb76d19f9da`; main confirmation `msg_551cbbb545ba`.

## Assumptions and authority

A format migration preserves existing knowledge and check status. It does not
claim that previously unchecked text was reviewed or invent a sentence locator.
The approved migration covers all four existing vaults. Develop must confirm a
writer window before real writes. Repository implementation and synthetic checks
may proceed now. Main owns raw selection/admission, student-bearing conversion,
site readers and publication selection. New batch conversion remains held.

This specification supersedes the maintained-Wiki `.md` and cache-only
conversion statements of specs 009, 010, 012, 014 and 030. Those records remain
history. Existing admission, BagIt, converters, privacy gates, topic catalogs,
profiles and mappings are reused. The six old feature branches remain held.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep one reviewed extraction per original revision (Priority: P1)

The user reads a full extraction in its original language, checks it against the
original, and corrects it through the vault's local history. Later requests use
that extraction instead of converting the original again.

**Why this priority**: Retained text makes reviewed evidence reusable and keeps
corrections when rebuildable caches disappear.

**Independent Test**: Synthetic originals and extractions prove retained text,
accurate provenance, separate original-language evidence and unchanged raw bytes.

**Acceptance Scenarios**:

1. **Given** a selected raw revision, **When** converted once, **Then** one
   original-language `.qmd` under `text/` records source, revision, SHA-256,
   converter/version and whether checked against the original.
2. **Given** an existing extraction, **When** corrected, **Then** local Git
   versions the correction and raw remains byte-identical; a new raw revision
   receives a distinct extraction.
3. **Given** an existing conversion with incomplete provenance, **When** reused,
   **Then** missing evidence is reported and no successful review is invented.

### User Story 2 - Cite the exact evidence for each sentence (Priority: P1)

English knowledge pages cite each supported sentence with a source and a page or
section locator. Judgment preparation reads only the referenced text span.

**Why this priority**: Whole-document requests waste work and can attach the
wrong revision or unrelated evidence to a claim.

**Independent Test**: A synthetic multi-page source includes a sentinel outside
the cited span; prepared evidence excludes it and reports bad locators.

**Acceptance Scenarios**:

1. **Given** a sentence with `[@source, p. 25]` and a matching stable marker,
   **When** prepared, **Then** its evidence contains only that referenced span
   and identifies the exact source revision.
2. **Given** a missing source, revision, hash match, text or locator, **When**
   resolved, **Then** preparation reports the failure without substituting the
   whole document, latest revision or guessed page.
3. **Given** a run with cached citation data from an older run, **When** started,
   **Then** citation sources are regenerated from BagIt records into cache;
   no persistent bibliography or second source registry is created.

### User Story 3 - Maintain every Wiki page as English Quarto text (Priority: P1)

All maintained pages, including index, overview and log, become `.qmd`.
Repeated folder defaults move to `_metadata.yml` while page overrides survive.
The agent still navigates the generated Cog catalog without a site or cache.

**Why this priority**: One maintained English source prevents format and language
copies from becoming competing knowledge owners.

**Independent Test**: Synthetic pages exercise discovery, links, special pages,
metadata inheritance/overrides, catalog output and append-only log history.

**Acceptance Scenarios**:

1. **Given** all existing vault pages, **When** migrated, **Then** every body,
   meaningful metadata override and earlier grammar unchecked status survives,
   with only necessary link/catalog pattern changes.
2. **Given** folder defaults and a page override, **When** checked, **Then** the
   checker merges them itself without invoking `quarto inspect` per page.
3. **Given** the catalog, overview and committed log, **When** checked after
   rename, **Then** catalog discovery covers `wiki/**/*.qmd`, links resolve and
   the entire earlier log remains a byte prefix.
4. **Given** staged or unrelated edits, **When** migrated, **Then** they remain
   preserved and no worker commits another writer's staged changes.

### User Story 4 - Separate evidence, knowledge and translated delivery (Priority: P2)

The schema declares raw, text, wiki, site and schema roles. `wiki/` is English
with topics; `site/` derives Korean text with tags from chosen English versions.
F2/CHE-12 owns freshness and publishing, using F1's concrete contract.

**Why this priority**: The language and storage roles must be clear before two
features share a checker or schema.

**Independent Test**: Synthetic role separation plus schema/constitution review
proves text is not treated as English Wiki or published content.

**Acceptance Scenarios**:

1. **Given** original-language text, English knowledge and Korean delivery,
   **When** checked, **Then** each follows its role; there is no `ko/` tree.
2. **Given** the approved principle VI amendment, **When** committed, **Then**
   one `feat` commit receives one Commitizen MINOR version bump.
3. **Given** the settled F1 contract, **When** sent through develop, **Then** F2
   can plan against it; shared source edits still require coordinated ownership.

### Edge Cases

Missing or duplicate markers; page ranges with a missing interior page; wrong
revision/hash; unreadable/partial extraction; absent review evidence; conflicting
text targets; nested metadata or explicit empty overrides; encoded relative links
and fragments; `.md`/`.qmd` collision; renamed log before its first commit;
interruption after a rename; staged page edits; mixed-language sources; stale
search collection masks; cache deletion; no network. Each must preserve evidence
and expose unresolved work without a full-source fallback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Raw remains immutable, create-only BagIt originals outside Git.
- **FR-002**: `text/` retains one full original-language `.qmd` per converted raw
  revision in vault Git with no remote; provenance records the five facts in US1.
- **FR-003**: Existing conversion paths are reused before any new converter;
  corrections are local Git commits and revisions have distinct extractions.
- **FR-004**: Stable page/section markers support sentence-level citation spans;
  missing or ambiguous locators fail clearly with no broadened evidence.
- **FR-005**: Citation sources derive from bags into cache every run, never a
  persistent bibliography or source registry; revision provenance stays exact.
- **FR-006**: Every maintained Wiki page is English `.qmd` with topics, including
  generated index, maintained overview and append-only log; bodies survive.
- **FR-007**: Folder `_metadata.yml` defaults merge in the checker; meaningful
  page overrides survive; no per-page Quarto process is used.
- **FR-008**: Cog remains the catalog; its input pattern becomes
  `wiki/**/*.qmd`. Source stays readable without executable cells or heavy
  includes/shortcodes. All real callers, linters and search masks migrate.
- **FR-009**: The four existing reference `.markdown` side files move to
  `text/` with preserved provenance; unknown evidence/status stays explicit.
  Existing conversions are reuse sources, not new batch-conversion authority.
- **FR-010**: Before/after readback receipts prove raw, every body, prior log,
  metadata, unchecked status and unrelated/staged edits are preserved.
- **FR-011**: Only scoped own-account workers read private vault material;
  messages and repository artifacts contain aggregate/public/synthetic data.
- **FR-012**: Base schema and principle VI declare all five roles, local history,
  languages and storage. F2 owns translation freshness and publishing.
- **FR-013**: Plan/contract, ownership and held decisions go through develop;
  live conversion, publication and student/audience decisions stay with main.
- **FR-014**: Narrow checks, full verification of the combined frozen feature,
  fresh independent review and exact evidence precede integration by develop.

### Key Entities

- **Raw revision**: Immutable admitted original and its BagIt provenance.
- **Text extraction**: Retained original-language text tied to one raw revision.
- **Wiki page**: Maintained English knowledge with topics and sentence citations.
- **Locator**: Stable page or section marker delimiting a cited evidence span.
- **Derived citation data**: Rebuildable run-local bibliography from raw bags.
- **Site page**: Korean derived delivery with tags and chosen English provenance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Positive, negative and boundary synthetic cases cover every
  requirement above, including absence of uncited sentinel text in requests.
- **SC-002**: Before/after receipts account for every current page in all four
  vaults; no original byte or foreign staged change is lost or committed.
- **SC-003**: Cache deletion leaves retained text, catalog and direct page reading
  usable; no-network consistency checks remain deterministic.
- **SC-004**: The frozen combined feature has passing full checks and fresh
  other-provider review; its report names the commit/tree and measured size.
- **SC-005**: Every held operational task stays unticked with its owner and next
  action; no unavailable conversion or judgment is called completed.
