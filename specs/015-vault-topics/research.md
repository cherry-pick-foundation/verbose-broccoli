# Research: Topics in Vault Page Metadata

## R1. Where the schema declares its topics

- **Decision**: YAML front matter at the top of the vault's `AGENTS.md`,
  holding one key, `topics`, a list of names; the template ships an empty
  list with a comment that points to the page rules.
- **Rationale**: The user chose a list declared in each vault's schema
  (spec Clarifications), and constitution VI makes `AGENTS.md` the schema, so
  a separate topics file would split it. Front matter reuses the tool's own
  `_front_matter` helper and PyYAML (`packages/wiki-consistency/src/wiki_consistency/instance.py`),
  the same format as page metadata, and agents read it first.
- **Alternatives considered**: A `## Topics` section with a Markdown list or
  a fenced YAML block, which needs new Markdown parsing and can drift from
  the prose around it; a `topics.yml` file beside `AGENTS.md`, which the
  user's answer and principle VI rule out.

## R2. How a page names its topics

- **Decision**: A required `topics` key in page front matter: a non-empty
  list of non-empty single-line strings, each listed once, each an exact
  match of a declared name.
- **Rationale**: The user made topics required (spec Clarifications). Exact
  matching keeps the rule mechanical; the declared list is where spellings
  are settled.
- **Alternatives considered**: Case-insensitive or normalized matching,
  rejected because constitution III forbids normalization as identity and
  the declared list already catches variants; a single `topic` string,
  rejected because CHE-27 allows several topics per page.

## R3. Where each rule is checked

- **Decision**: Page shape in `instance._metadata`, next to `title`,
  `summary` and `sources`, so `check`, `update` (through `page_catalog`) and
  `prepare` see the same problems. The schema list in a new
  `instance.declared_topics(root)`, reported on `AGENTS.md`. Membership in
  one helper in `lint.py`, called by `check` and, before regeneration, by
  `update`. `page_catalog` does not read the schema.
- **Rationale**: The generator stays a function of the files its region
  names (`wiki/**/*.md`), so the region line in every vault's `index.md`
  stays the same and doc-regions' staleness check still holds. `update`
  already refuses before regeneration on a bad `index.md` shape
  (`lint.update`), and doc-regions restores a document whose generator fails
  (`packages/doc-regions/src/doc_regions/regions.py`, `process`), so no
  partial index is written.
- **Alternatives considered**: Passing `AGENTS.md` to `page_catalog` as a
  second source, which would change the region line in every vault and the
  `_index_shape` rule; checking membership only in `check`, which would let
  `update` write a group for a misspelled topic.

## R4. Index layout

- **Decision**: One `## <topic>` heading per topic that at least one page
  carries, topics in sorted order; under each, a blank line and the existing
  page lines, `- [<title>](<path>) — <summary>`, sorted by path; one blank
  line between groups. No pages give an empty region, as today.
- **Rationale**: Keeps feature 010's line format, adds only headings, and is
  deterministic. Headings give each topic a link anchor.
- **Alternatives considered**: Declaration order, which would make the
  generator read the schema (R3); a nested list per topic, which reads worse
  and gives no anchors.

## R5. A schema without a topic list

- **Decision**: `check` and `update` fail on `AGENTS.md` when it is missing,
  has no front matter, or its `topics` value is not a list of unique
  non-empty single-line names; an empty list is valid. When the schema list
  is broken, undeclared-name problems are not reported, to avoid one
  failure per page for one cause.
- **Rationale**: Every vault must declare its list (spec FR-010). The
  `work` vault, which has no list yet, fails until the develop session
  applies the change there, which the user accepted (spec Clarifications).

## R6. Adopting the rule in the vaults

- **Decision**: After `git flow feature finish`, for each of `default`,
  `chat` and `code`: add the template's front matter with an empty list and
  the template's topic sentences in the page rules to the vault's
  `AGENTS.md`, leaving its other lines as they are; run `update` and `check`
  with the develop worktree's tool; append a `## [YYYY-MM-DD] schema | Page
  topics` entry to `wiki/log.md`, as the vaults' earlier schema commits did;
  commit once. The `work` vault is left to the develop session.
- **Rationale**: The three vaults' schema copies still lack feature 013's
  wording (checked on 2026-09-29), so copying the whole template would apply
  another feature's rules without its go-ahead.

## R7. Conflicts with parallel work

- CHE-25 (`feature/english-vaults`) adds bullets to the template's `## Wiki`
  section and edits the first paragraph of the consistency skill and one
  bullet of `docs/architecture.md`. This feature edits the template's front
  matter and `## Pages` section, the skill's command table and the
  architecture document's metadata and check bullets. Whoever merges
  `develop` later keeps both sides.
- CHE-26 will add rule checks to `lint.check`; this feature keeps its check
  additions in one helper so that a later merge stays small.
