# Feature Specification: Wiki Document Consistency

**Feature Branch**: `feature/wiki-consistency`

**Created**: 2026-09-28

**Status**: Draft

**Linear issue**: CHE-8

**Input**: Section 3, "Wiki document consistency", of the brief
`briefs/2026-09-27-linear-and-documents.md` outside the repository (in the
`briefs/` folder beside the worktrees). The goal is to keep the Wiki of
constitution principle VI consistent the way feature 008
(`specs/008-doc-consistency/`, branch `feature/doc-consistency`) keeps the
repository's documents consistent: mechanical regions derived from raw
evidence and its metadata, and agent regions judged by backfire, the judgment
server of feature 005 (`packages/backfire/`, [docs/backfire.md](../../docs/backfire.md)).
The user decided on 2026-09-27:

1. The region model and the "no human-written parts" rule of the brief's
   section 2 apply unchanged: every part of a Wiki page is either a marked
   mechanical region that names its sources and is regenerated from them, or
   an agent region that backfire judges. No protection for human prose, no
   approval trailers and no edit locks are designed.
2. Tools: feature 008's (Cog, markdown-it-py, lychee), plus markitdown, which
   converts PDF, Word and PowerPoint files to Markdown so backfire can read raw
   evidence, and qmd (`tobi/qmd`, npm `@tobilu/qmd`), a local Markdown search
   tool unrelated to Quarto's `.qmd` format. qmd finds candidates only
   (`qmd search`, `qmd vsearch`); backfire makes the final judgments
   (`backfire_find`, `backfire_compare`, `backfire_verify`), because qmd's own
   language-model reranking overlaps `backfire_rerank`. qmd's rebuildable index
   lives in the XDG cache. Docling is added only when markitdown is not good
   enough for a source.
3. The specification is written now. Implementation starts after feature 005
   (merged into `develop` at `8ab332b`) and the Wiki storage feature 009
   (`specs/009-wiki-storage/`, branch `feature/wiki-storage`, Linear CHE-7)
   have merged, and after CHE-9, backfire for education work (feature 011,
   `specs/011-backfire-education/` on `feature/backfire-education`), because
   that feature decides which personal data backfire may receive.

The brief also sets these constraints, settled in the Clarifications below and
in [research.md](research.md): whether `index.md`, `overview.md` or `log.md`
can be mechanical under principle VI's wording; keeping credentials, and
personal data beyond what feature 011 allows, out of backfire judgments; the
tooling running inside the work plugin, with components shared with feature
008 going through `packages/`; and which lint checks of Andrej Karpathy's LLM
Wiki pattern are deterministic and which are backfire judgments.

## Clarifications

### Session 2026-09-28

Five questions went to the user through the orchestrator on 2026-09-28; the
orchestrator relayed the answers the same day. Each names the requirements it
affects.

- Q: Principle VI says "The LLM maintains pages, cross-references,
  `index.md`, `overview.md`, and the append-only `log.md`". Which of the three
  may be mechanical regions? → A (the user's choice): `index.md` becomes one
  mechanical region, a catalog line per page generated from each page's title
  and summary. `overview.md` stays an agent region judged by backfire.
  `log.md` stays agent-written: it is checked offline for being append-only
  and is not judged, because it records past events. The sentence in
  principle VI gets a patch amendment (a `docs` commit) as the first
  implementation task. Affects FR-005 to FR-008 and FR-022.
- Q: markitdown refuses HWP files and returns empty text for image-only
  (scanned) PDFs; feature 009's survey found HWP files among the raw
  candidates. → A: such sources are listed as unreadable in the conversion
  report; a claim whose cited sources are all unreadable is reported as
  unverifiable and never sent to backfire. Adding Docling or an HWP converter
  is a later decision by the user. Affects FR-011 and FR-012.
- Q: Backfire is declared only by the code plugin, and constitution IX needs
  each plugin to work without the others. Who declares backfire in the work
  plugin and builds it? → A, confirmed by CHE-9's orchestrator: feature 011
  owns the backfire declaration in `plugins/work/mcp.json` and a per-plugin
  build of `packages/backfire` that assembles each plugin's server from
  modules (the work plugin gets the shared judgment core plus a
  pseudonymization module and an education profile). The build takes the
  plugin name, and each plugin's module list is the one place to extend, so
  this feature adds its packages to the work plugin's list. The exact build
  interface is fixed only in feature 011's plan, so this feature assumes none.
  Affects FR-020, FR-021 and FR-023.
- Q: When do the paid backfire judgments run? → A: in an explicit lint
  operation over the whole Wiki, and at the end of any operation that changed
  pages, limited to the changed parts and to pages citing a source that got a
  new revision. Affects FR-014 and FR-015.
- Q: No feature defines Wiki page conventions yet; feature 009 defines only
  raw admission. → A: this feature adds only the page metadata its checks
  read (a title, a one-line summary, and cited sources as source ID plus
  revision) to feature 009's schema template after 009 merges; a later ingest
  feature may add fields but does not redefine these. Affects FR-003 and
  FR-022.

## User Scenarios & Testing *(mandatory)*

The actors are the coding agents (Claude Code or Codex) that maintain the Wiki
through the work plugin, and the user, who owns the Wiki and its raw evidence
and reads the reports. The Wiki is feature 009's default instance at
`$XDG_DATA_HOME/verbose-broccoli/wikis/default/`: the schema `AGENTS.md`,
`raw/` with one BagIt bag per source revision, and `wiki/` with `index.md`,
`overview.md` and `log.md`, versioned by the instance's own Git repository with
`raw/` excluded.

### User Story 1 - The offline check refuses a stale or broken Wiki before it is committed (Priority: P1)

An agent changes the Wiki, for example admits a new revision of a source or
adds a page, and forgets to refresh a mechanical region, breaks a link, leaves
a page without metadata, or edits an earlier `log.md` entry. Before the
instance is committed, the offline check fails, names the page, line and
problem, and names the command that fixes regenerable problems. After the
agent regenerates or corrects them, the check passes. The check never writes a
file and never uses the network. It also lists orphan pages and citations of
revisions that are no longer the latest, as findings that do not block the
commit.

**Why this priority**: It runs on every Wiki change at no cost and catches the
mechanical drift before it enters the Wiki's history.

**Independent Test**: In a temporary instance built from synthetic pages and
bags, add a revision to a cited source, run the check, confirm it fails
without changing any file, run the regeneration command, and confirm the check
passes and the old citation is listed as a finding.

**Acceptance Scenarios**:

1. **Given** every mechanical region matches its sources, every link resolves,
   every page has its metadata and `log.md` keeps its committed text, **When**
   the check runs, **Then** it passes and no file changes.
2. **Given** a source revision was added and a region derived from that
   source's metadata was not regenerated, **When** the check runs, **Then** it
   fails, names the page and region, shows the difference and the
   regeneration command, and no file changes.
3. **Given** a stale region, **When** the agent runs the regeneration command,
   **Then** only region text changes, the rest of every page is
   byte-identical, and a second run changes nothing.
4. **Given** a page links to a page or heading that does not exist, **When**
   the check runs, **Then** it fails and names the link.
5. **Given** a page lacks its title, summary or cited sources, or cites a
   source ID or revision that no bag in `raw/` has, **When** the check runs,
   **Then** it fails and names the page and field.
6. **Given** a committed `log.md` entry was changed or removed, **When** the
   check runs, **Then** it fails and names the first differing line.
7. **Given** a page no other page links to, or a page citing a revision that
   is not its source's latest, **When** the check runs, **Then** it passes but
   lists the orphan page or the stale citation.
8. **Given** the machine has no network, **When** the check runs, **Then** it
   gives the same result as with a network.

---

### User Story 2 - Changed Wiki text is judged against its evidence (Priority: P1)

At the end of an operation that changed pages, the agent converts the cited
raw evidence to Markdown in the cache, updates the local search index, and
runs one offline command that splits the affected pages into agent-region
units, finds candidate related passages with local search, and prints
ready-to-send backfire requests: each unit
verified against the text of the sources its page cites, and against
candidate units of other pages for contradictions. The agent sends them to
backfire, corrects units that backfire finds contradicted, and reports the
rest to the user. Mechanical regions and `log.md` are never sent.

**Why this priority**: Agent regions carry the Wiki's knowledge; without this
step nothing notices a claim its evidence does not support or two pages that
disagree.

**Independent Test**: In a temporary instance, write a page whose paragraph
contradicts its synthetic cited source, run the preparation command, confirm
the paragraph is a claim with the source's converted text as evidence, send
the request to backfire and confirm the paragraph comes back `contradicted` or
flagged for review.

**Acceptance Scenarios**:

1. **Given** changed pages, **When** the preparation command runs, **Then** it
   prints, without network access or writes outside the cache, verify requests
   whose claims are the changed agent-region units, each with the converted
   text of its page's cited source revisions as evidence, every unit
   identified by page, heading path and line range.
2. **Given** the same instance and cache, **When** the command runs twice,
   **Then** both outputs are byte-identical.
3. **Given** a changed unit, **When** the command runs, **Then** it also
   prints verify requests that check the unit against the candidate units of
   other pages that local search returned, up to a fixed number per unit, so
   that a contradicted result names the conflicting candidate; the agent
   confirms each such pair with one compare judgment before reporting it.
4. **Given** a source revision was added and pages cite the earlier revision,
   **When** the command runs, **Then** the units of those pages are verified
   against the new revision's text.
5. **Given** a unit whose cited sources are all unreadable, **When** the
   command runs, **Then** that unit is listed as unverifiable and is in no
   request.
6. **Given** units or evidence larger than backfire accepts in one call,
   **When** the command runs, **Then** it splits them into several requests
   within the limits and loses no unit.
7. **Given** backfire returns `contradicted` or `review` for a unit, **When**
   the agent finishes the step, **Then** the unit is corrected before the
   operation's commit, or the finding is reported to the user with the reason
   it stands; contradictions between two pages are always reported.

---

### User Story 3 - A lint operation reviews the whole Wiki (Priority: P2)

The user asks for a lint of the Wiki. The agent runs the offline check, then
prepares judgments for every page: claims against their evidence,
contradictions between pages, and missing cross-references, where local search
proposes related pages that are not linked and backfire judges whether a link
belongs. New units are also classified as candidates for mechanical regions.
The agent fixes what the check requires, applies accepted suggestions, reports
the rest, and appends one entry to `log.md`.

**Why this priority**: It covers drift that no single change caused, but the
user starts it; the per-change step of User Story 2 catches most drift first.

**Independent Test**: On a temporary instance with two pages about the same
synthetic topic that neither links to the other, run the lint preparation and
confirm a find request proposes the other page for each; send it and confirm
the result is a suggestion that is not marked final.

**Acceptance Scenarios**:

1. **Given** a lint request, **When** the preparation command runs in lint
   scope, **Then** it covers every agent-region unit of every page except
   `log.md` exactly once in the evidence requests, except units listed as
   unverifiable or withheld.
2. **Given** two related pages that do not link to each other, **When** the
   lint preparation runs, **Then** a find request for each page lists the
   other among its candidates.
3. **Given** backfire's result for a find request, **When** the agent reads
   it, **Then** it treats the result as a suggestion to accept or reject,
   never as a final decision.
4. **Given** the lint finished, **When** the instance is committed, **Then**
   `log.md` has exactly one new entry for it and its earlier entries are
   unchanged.

---

### User Story 4 - Personal data and credentials stay where the user allows (Priority: P2)

The preparation command sends backfire only Wiki pages and the converted text
of raw revisions the pages cite. It never includes credentials, configuration,
state, or files outside the instance, and it follows feature 011's policy for
which personal data the selected provider profile may receive. When a request
would break that policy, the command leaves the unit out and reports why.

**Why this priority**: Backfire sends what it judges to an external provider.
The user wants backfire used for education work, so the rule must be exact
rather than a blanket ban.

**Independent Test**: With a synthetic instance, a configured policy that
forbids a marked class of data for the selected profile, and a page citing a
source of that class, run the preparation command and confirm the unit is left
out and reported; confirm no configuration or credential file content appears
in any request.

**Acceptance Scenarios**:

1. **Given** any instance, **When** the preparation command runs, **Then** no
   request contains text read from outside the instance's `wiki/` pages and
   the converted text of cited raw revisions.
2. **Given** feature 011's policy forbids the data of a cited source for the
   selected profile, **When** the command runs, **Then** units citing it are in
   no request and are reported as withheld with the policy's reason.

---

### User Story 5 - The tooling ships with the work plugin (Priority: P3)

The Wiki consistency procedure and its commands ship in the work plugin, so a
client with only the work plugin installed can run them. Components shared
with feature 008 come from `packages/` through the work plugin's build copy,
and the procedure is written into the Wiki's schema so any agent working on the
instance finds it.

**Why this priority**: It has no effect of its own, but without it the
capability depends on the repository checkout or on the code plugin.

**Independent Test**: Build the work plugin into a temporary folder outside
the repository, install its runtime environment offline from the locks, and
run the offline check against a temporary instance from that copy.

**Acceptance Scenarios**:

1. **Given** a built work plugin outside the repository, **When** its Wiki
   check runs, **Then** it works without the repository checkout and without
   the code plugin.
2. **Given** the schema template, **When** a new instance is created, **Then**
   its `AGENTS.md` names the page metadata, the check before each commit, the
   judgment step and the lint operation.

---

### Edge Cases

- A cited source has a newer revision: the offline check lists the stale
  citation; the judgment step verifies the page's units against the newer
  revision; the agent updates the citation after the page is correct.
- A cited source cannot be converted (HWP, image-only PDF, damaged file): the
  conversion report lists it as unreadable; units resting only on it are
  unverifiable, not judged.
- A cited bag fails BagIt's fast validation: the check fails and names the bag; the
  Wiki tooling never repairs raw evidence (feature 009 leaves repair to the
  user).
- The local search index is missing, stale or deleted with the cache: the
  preparation command refuses and names the indexing step, which rebuilds it
  from `wiki/` and the converted evidence; the offline check and direct page
  reading never need it (principle VI).
- The embedding model for semantic search is not downloaded: keyword search
  still gives candidates, and the report says semantic search was skipped.
- A page quotes the region marker syntax: as in feature 008, Cog would treat
  it as a region, so pages do not quote markers and the check reports such a
  quote as a malformed region.
- Two pages contradict each other and each agrees with its own source: the
  finding is reported to the user, since the sources themselves disagree.
- A page is deleted or renamed: links to it fail the check; the catalog in
  `index.md` is regenerated; `log.md` records the operation.
- Backfire is not configured or unreachable: the preparation command still
  works; the agent reports that the judgment step did not run, and the
  operation is not reported as checked.
- Backfire's `find`, `rerank` and `decide` results are never final without
  review (`specs/005-jev-decision-backend/contracts/evaluation.md`), so
  cross-reference suggestions always need the agent's decision.
- A generated writer in the cache (converted text, qmd index and models)
  reaches its storage budget: it stops before writing and names the budget.

## Requirements *(mandatory)*

### Functional Requirements

**Region model (decision 1)**

- **FR-001**: Every part of a Wiki page MUST be either a mechanical region or
  an agent region, with feature 008's markers and source-naming rule: a
  mechanical region names its generator and every source file its text comes
  from, and its text depends only on those files.
- **FR-002**: Mechanical regions MAY be derived only from raw evidence
  metadata (the BagIt bags of feature 009) and from page metadata; they MUST
  NOT be derived from raw file contents or from anything outside the instance.
- **FR-003**: Every page other than `index.md`, `overview.md` and `log.md`
  MUST have metadata giving a title, a one-line summary, and one or more cited
  sources, each a source ID and revision of a bag in `raw/`.
- **FR-004**: One command MUST regenerate every stale mechanical region of an
  instance in place, changing nothing outside the regions; a second run MUST
  change nothing.

**The three special pages (constraint on principle VI)**

- **FR-005**: `index.md` MUST be one mechanical region listing every other
  page once, with a relative link, its title and its summary, generated from
  page metadata.
- **FR-006**: `overview.md` MUST be an agent region judged against the pages
  it links to.
- **FR-007**: `log.md` MUST stay append-only: the offline check MUST fail when
  its committed text is not a prefix of its current text. Its entries MUST NOT
  be sent to backfire.
- **FR-008**: Each operation that changes an instance MUST append exactly one
  `log.md` entry.

**Offline check**

- **FR-009**: The offline check MUST fail on a stale or malformed mechanical
  region, a link to a missing page or heading, missing or unresolvable page
  metadata, a cited bag that fails BagIt's fast validation (structure and
  payload size; full digest validation stays with feature 009's integrity
  check), or a changed earlier `log.md` entry,
  and MUST list orphan pages and citations of non-latest revisions as findings
  that do not fail it.
- **FR-010**: The offline check MUST NOT write any file or use the network,
  MUST NOT need the cache, and MUST run before every commit of the instance.

**Evidence conversion and candidate search (decision 2)**

- **FR-011**: Cited raw revisions MUST be converted to Markdown into the cache
  root, one file per revision and converter version; the conversion MUST
  report every revision it cannot convert or that converts to empty text as
  unreadable.
- **FR-012**: A unit whose cited sources are all unreadable MUST be reported
  as unverifiable and MUST NOT be sent to backfire.
- **FR-013**: Local search MUST index only Markdown: the instance's `wiki/`
  pages and the converted evidence in the cache. It MUST keep its index and
  models in the cache root under the `verbose-broccoli` namespace, and be used
  only to choose candidates; it MUST NOT make a final judgment. Its only
  network use MUST be the one-time download of a pinned embedding model.

**Judgments (decisions 1 and 2)**

- **FR-014**: An offline, deterministic command MUST print ready-to-send
  backfire requests for a given scope: the units an operation changed plus the
  units of pages citing a source with a new revision, or, in lint scope, every
  unit of every page except `log.md`.
- **FR-015**: The requests MUST be: evidence requests, verifying units
  against the converted text of their cited revisions (for `overview.md`,
  against the pages it links to); page requests, verifying units against the
  candidate units of other pages that local search returns, up to a fixed
  count per unit; in lint scope, find requests proposing unlinked related
  pages as cross-references; and classify requests for new units, as in
  feature 008. A page request whose verdict is `contradicted` MUST be
  confirmed with one compare judgment of the two units before it is
  reported.
- **FR-016**: Requests MUST stay within backfire's published input limits,
  every in-scope unit MUST appear in exactly one evidence request unless it is
  unverifiable or withheld, and the output MUST state the number of requests
  per tool before any is sent.
- **FR-017**: The agent MUST correct contradicted or review-flagged units
  before the operation's commit or report them with the reason they stand,
  MUST report every contradiction between pages to the user, and MUST treat
  find results as suggestions.

**Data boundaries (constraint)**

- **FR-018**: Requests MUST contain only text from the instance's `wiki/`
  pages and the converted text of cited raw revisions. Credentials,
  configuration, state and files outside the instance MUST NOT be read into
  a request.
- **FR-019**: Which personal data the selected backfire provider profile may
  receive MUST follow feature 011's policy; units whose evidence that policy
  withholds MUST be left out of requests and reported as withheld.

**Packaging (constraint)**

- **FR-020**: The procedure and its commands MUST ship in the work plugin and
  work without the repository checkout and without the code plugin.
- **FR-021**: Components shared with feature 008 MUST come from `packages/`
  through the work plugin's build copy; this feature MUST NOT copy their
  source into the plugin.
- **FR-022**: The schema template MUST state the page metadata, the offline
  check before each commit, the judgment step, the lint operation and the
  special pages' rules, without contradicting feature 009's raw rules.

**Order (decision 3)**

- **FR-023**: Implementation MUST start only after feature 009, feature 011
  (CHE-9) and feature 008, whose shared package this feature uses, have
  merged into `develop`, and MUST use backfire's tools, feature 011's build
  and policy, and feature 008's package as they are on `develop` then.

### Key Entities

- **Wiki instance**: Feature 009's instance folder: schema, `raw/`, `wiki/`.
- **Page**: A Markdown file under `wiki/`, with metadata (title, summary,
  cited sources) except for the three special pages.
- **Citation**: A page's reference to one source revision (source ID and
  revision name of a bag).
- **Mechanical region**, **agent region**, **unit**, **judgment request**,
  **drift finding**: as defined by feature 008's data model, with pages as
  target documents and cited evidence instead of a repository diff.
- **Converted evidence**: The Markdown text of one raw revision in the cache,
  or an unreadable mark with its reason.
- **Candidate**: A unit of another page that local search returned for an
  in-scope unit; input to compare and find requests only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the automated tests, every stale, malformed, broken-link,
  missing-metadata and changed-log case fails the offline check, every passing
  case passes, and no case changes a file or opens a network connection.
- **SC-002**: The offline check of an instance with 500 pages finishes in
  under 10 seconds on the development machine.
- **SC-003**: Regeneration run twice changes nothing the second time in every
  test case.
- **SC-004**: The preparation command gives byte-identical output for the same
  instance and cache, and every in-scope unit appears in exactly one evidence
  request or in the unverifiable or withheld list.
- **SC-005**: On a synthetic instance with one paragraph contradicting its
  cited source and one pair of contradicting pages, backfire flags both
  (`contradicted` or review) in each of three runs.
- **SC-006**: In the automated tests, no request contains text from outside
  the instance's pages and cited converted evidence, and every withheld unit
  is reported.
- **SC-007**: The offline check runs from a work plugin built outside the
  repository, without the code plugin.

## Assumptions

- Feature 009's instance layout, bag fields and `log.md` convention are as
  committed on `feature/wiki-storage` at `c8fbabc`; if they change before 009
  merges, this feature follows them.
- Feature 008's region markers, source-naming rule, unit splitting and request
  splitting are reused as specified on `feature/doc-consistency` at
  `5252aef`; the extensions this feature needs are listed in
  [research.md](research.md) R8.
- The main agent, not a script, calls backfire through its MCP client, as in
  feature 008, so no credential handling is added.
- The Wiki holds Markdown only, so indexing `**/*.md` under `wiki/` covers it.
- The instance's schema `AGENTS.md` is not a target: it holds the rules the
  checks enforce and changes by the user's decision.
- The user's separate web wiki (Quarto pages published with Docusaurus) is
  not part of this feature.
- The example schema `docs/examples/wiki/AGENTS.md` describes a `wiki apply`
  command that does not exist; feature 008 left it to this feature. It is not
  a target here, and whether to replace it with the real schema template is a
  follow-up for the orchestrator.

## Out of Scope

- Writing Wiki pages from raw evidence (ingest) and answering queries.
- Converting HWP files or scanned PDFs, and adding Docling, until the user
  decides a source needs it.
- Deciding which personal data backfire may receive; feature 011 owns that.
- Repository document consistency (feature 008).
