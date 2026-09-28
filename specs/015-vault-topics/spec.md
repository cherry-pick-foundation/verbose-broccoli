# Feature Specification: Topics in Vault Page Metadata

**Feature Branch**: `feature/vault-topics`

**Created**: 2026-09-29

**Status**: Draft

**Linear issue**: CHE-27

**Input**: Linear issue CHE-27, "Group vault pages by topic metadata instead of
more vaults", and the develop session's task brief of 2026-09-29: organize
topics inside a vault with page metadata instead of creating more vaults. Add
a `topics` field, which may hold several topics, to the page metadata of the
vault schema template; have the generated `index.md` group pages by topic;
have the offline check validate the field; keep the constitution's layer
folders. The issue leaves open whether topic names are free or a list
declared per vault. After the merge, the `default`, `chat` and `code` vaults
adopt the change; the `work` vault is left to the develop session.

## Background

- The user's decision of 2026-09-29 (CHE-27): vaults stay split by the rules
  that differ in how a vault is run (evidence policy, privacy regime, ingest
  workflow, lifecycle): `default`, `chat`, `code` and `work`. A subject or
  topic does not get its own vault; it lives inside the vault whose rules fit
  it. Pages cannot cite another vault's evidence, so fewer vaults with finer
  topics keep knowledge together.
- Feature 010 (`specs/010-wiki-consistency/`) defined the page metadata: a
  title, a one-line summary and the cited source revisions. Its `index.md` is
  one generated region that lists every other page with its title and
  summary, sorted by path, and its offline `check` rejects a page with
  missing or malformed metadata. Constitution principle VI says `index.md` is
  regenerated from page metadata and that source summaries, entities,
  concepts, comparisons and synthesis keep their own folders.
- The vault schema template is
  `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`; each vault keeps its
  own copy as its `AGENTS.md`. On 2026-09-29 the `default`, `chat` and `code`
  vaults hold no pages yet, only the special pages. The `work` vault holds
  pages; CHE-21 works in it, and the develop session applies this change
  there.
- Other work touches the same files: CHE-25 (feature 014, merged into
  `develop` as `df912f4`) added rules to the template's Wiki section and
  applied them to the `default`, `chat` and `code` vaults, and CHE-26 will
  add rule checks to the same offline check. Whichever feature finishes
  later merges `develop` and keeps both changes.

## Clarifications

### Session 2026-09-29

The develop session relayed these questions to the user and returned the
answers the same day; the user took both recommended options.

- Q: Are topic names free, or must they come from a list declared per vault?
  → A: A declared list. Each vault's schema lists its topics, the offline
  check fails on a name not on the list, and an agent adds a new topic to the
  list in the same vault commit as the first page that uses it.
- Q: Must every page carry at least one topic? → A: Yes. Every page lists at
  least one declared topic, and the check fails on a page without one. The
  `work` vault gets its topics when the change is applied there after CHE-21
  finishes; this feature leaves that vault alone.

## User Scenarios & Testing *(mandatory)*

The actors are the user, who owns the vaults and decides their rules, and a
coding agent (Claude Code or Codex) that writes pages and runs the checks.

### User Story 1 - Find pages by topic in the index (Priority: P1)

An agent writes pages on several subjects into one vault and gives each page
one or more topics. After the regeneration step, the vault's `index.md`
shows each topic once, with the pages that carry it listed under it, so the
user and later agents find related pages together.

**Why this priority**: Grouping by topic is what lets one vault hold many
subjects without a vault per subject.

**Independent Test**: In a temporary vault with synthetic pages that carry
different and overlapping topics, regenerate the index and read it.

**Acceptance Scenarios**:

1. **Given** pages whose topics differ, **When** the index is regenerated,
   **Then** each topic appears once, and under it every page that carries
   the topic, with its link, title and summary.
2. **Given** a page with two topics, **When** the index is regenerated,
   **Then** the page is listed under both topics.
3. **Given** the same pages, **When** the index is regenerated twice, **Then**
   the output is identical, and topics and pages appear in a fixed order.
4. **Given** a page whose topics change, **When** the offline check runs
   before regeneration, **Then** it reports the index as stale.

---

### User Story 2 - The offline check rejects a bad topics field (Priority: P1)

Before a vault is committed, the offline check reads every page's topics and
fails, naming the page, when the field breaks the schema's rule.

**Why this priority**: The index is only as good as the topics; a misspelled
or malformed topic would split one topic into two groups or break the index.

**Independent Test**: In a temporary vault, give synthetic pages each kind of
invalid topics field, run the check, and confirm that each failure names the
page; then run it on valid pages and confirm it passes.

**Acceptance Scenarios**:

1. **Given** a page whose topics field breaks the rule (FR-003), **When**
   the check runs, **Then** it fails and names that page.
2. **Given** pages whose topics all follow the rule, **When** the check runs,
   **Then** it passes.
3. **Given** a failing page, **When** the index is regenerated, **Then**
   regeneration refuses and names the page instead of writing a partial
   index.

---

### User Story 3 - The vaults adopt the topics rule (Priority: P2)

The schema template states the topics rule for new vaults. After this
feature is merged into `develop`, the `default`, `chat` and `code` vaults
adopt the same rule in their own schema, each in one vault commit, and each
vault passes the offline check.

**Why this priority**: The rule only helps once the vaults that agents write
into state it.

**Independent Test**: Read the template's page rules. After the merge, read
each vault's schema, its latest commit and the check's result.

**Acceptance Scenarios**:

1. **Given** the schema template, **When** an agent reads its page rules,
   **Then** they describe the topics field, the declared topic list, their
   rules and the index grouped by topic.
2. **Given** the merged feature, **When** each of the `default`, `chat` and
   `code` vaults adopts the rule, **Then** each has exactly one new commit
   that changes only the topics part of its schema, its generated index if
   regeneration changes it, and its log, which gains one entry; and its
   check passes.
3. **Given** a vault's schema that differs from the template in unrelated
   rules, **When** the topics rule is adopted, **Then** the unrelated rules
   stay as they are.

---

### Edge Cases

- A vault without pages: the index region stays empty and the check passes.
- A page lists the same topic twice: the check fails.
- A page names a topic that the vault's schema does not declare, such as a
  variant spelling of a declared topic: the check fails and names the page
  and the name.
- The schema declares a topic twice, or declares an empty or multi-line
  name: the check fails and names the schema.
- The schema declares a topic that no page uses: the check passes; the topic
  gets no group in the index.
- A page without a topics field, or with an empty list: the check fails and
  names the page; every page carries at least one topic.
- A vault whose schema declares no topics yet, such as a new vault: the
  check passes while it has no pages; its first page's commit also declares
  the page's topics.
- A topic name holds Markdown syntax, such as a link: the index writes the
  name as declared, as it writes page titles today; a resulting broken link
  fails the check.
- A page moves to another folder: its topics stay, and the index lists it
  under the same topics with its new link.
- The `work` vault's pages have no topics yet: this feature does not change
  that vault; the develop session applies the rule there.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Page metadata MUST gain a required `topics` field that lists one
  or more topic names declared in the vault's schema; a page MAY carry
  several topics.
- **FR-002**: The generated `index.md` MUST group pages by topic: each topic
  once, and under it every page that carries it with its link, title and
  summary. A page with several topics MUST appear under each. The order of
  topics and of pages under a topic MUST be fixed and independent of the
  machine, the clock and the environment.
- **FR-003**: The offline check MUST fail, naming the page, when a page's
  topics field is not a list of non-empty single-line names, lists a name
  twice, names a topic that the vault's schema does not declare, or is
  missing.
- **FR-004**: Index regeneration MUST refuse, naming the page, when a page's
  topics field fails FR-003, and MUST NOT write a partial index.
- **FR-005**: The vault schema template MUST describe the topics field, the
  declared topic list, their rules and the grouped index, next to the other
  page metadata rules.
- **FR-006**: The constitution's layer folders (`sources/` and the folders
  for entities, concepts, comparisons and synthesis) MUST stay as they are;
  topics do not replace folders and do not create vaults.
- **FR-007**: The repository documents that describe page metadata or the
  index MUST describe topics the same way as the template.
- **FR-008**: After the merge into `develop`, each of the `default`, `chat`
  and `code` vaults MUST adopt the topics rule in exactly one vault commit,
  changing only the topics part of its schema, its regenerated index and one
  appended `log.md` entry, and MUST pass the offline check. The `work` vault is not changed by this
  feature; the develop session applies the rule there after CHE-21 finishes.
- **FR-009**: Tests MUST use synthetic fixtures. No student name, real page
  or vault content enters the repository, Linear or Orca messages.
- **FR-010**: Each vault's schema MUST declare the vault's topics as a list of
  unique non-empty single-line names; a new vault's list starts empty. The
  offline check MUST fail, naming the schema, when the list is malformed. An
  agent adds a topic to the list in the same vault commit as the first page
  that uses it.

### Key Entities

- **Topic**: A name that groups pages inside one vault, declared in that
  vault's schema. It exists only in that vault; the same name in two vaults
  means nothing shared.
- **Page metadata**: The YAML front matter of a Wiki page: title, summary,
  cited source revisions and, with this feature, topics.
- **Index**: The vault's `wiki/index.md`, one generated region listing the
  pages grouped by topic.
- **Vault schema**: The vault's `AGENTS.md`, copied from the template when
  the vault is created and versioned in the vault's own Git history. With
  this feature it also declares the vault's topics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a synthetic vault with at least three topics and one page
  that carries two of them, the regenerated index lists every page under
  every one of its topics and no page under any other topic.
- **SC-002**: Every invalid case in FR-003 and FR-010 makes the offline check
  fail with the page or the schema named, and a vault with only valid pages
  and a valid topic list passes.
- **SC-003**: Regenerating the same synthetic vault twice gives byte-identical
  indexes.
- **SC-004**: The `default`, `chat` and `code` vaults each have one commit
  that adopts the topics rule, and each passes the offline check afterwards.
- **SC-005**: No repository file, commit, Linear comment or Orca message from
  this feature holds a student name or real vault content.

## Assumptions

- Topics are a flat list per page; there are no nested topics or topic
  hierarchies.
- Folders keep their meaning (source summaries, entities, concepts and so
  on); a topic is independent of the folder a page is in.
- The judgment step (`convert`, `index`, `prepare`) and backfire need no
  change; topics only affect the index and the offline check.
- Adopting topics in the `default`, `chat` and `code` vaults adds only the
  topics part of the template, so rules that other features add to the
  template stay with those features.
- The older example schema `docs/examples/wiki/AGENTS.md` is not the
  template; this feature does not change it.

## Out of Scope

- New vaults, or moving pages between vaults.
- Topics in the `work` vault; the develop session applies the rule there.
- Suggesting or assigning topics automatically.
- Rule checks beyond the topics field; CHE-26 adds those.
