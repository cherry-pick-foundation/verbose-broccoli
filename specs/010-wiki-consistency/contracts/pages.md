# Pages Contract

This contract is what the implementation adds to the schema template of
feature 009 (`plugins/work/skills/wiki-raw-import/assets/AGENTS.md`), so every
instance's `AGENTS.md` states it. Feature 009's raw admission rules stay as
they are.

## Page metadata

Every page under `wiki/` except `index.md`, `overview.md` and `log.md` starts
with YAML front matter:

```yaml
---
title: Quadratic formula
summary: How the quadratic formula follows from completing the square.
sources:
  - id: 0199a0e2-7c1b-7d3e-9f00-000000000000
    revision: 20260928T010203000000Z
---
```

- `title` and `summary` are non-empty single lines.
- `sources` is a non-empty list; each `id` and `revision` names a bag under
  `raw/`. A page cites the revision it was checked against.
- A later ingest feature may add fields; it does not change these.

## Special pages

- `index.md`: one mechanical region calling `page_catalog("wiki/**/*.md")`
  and nothing else to edit by hand; the check fails when it is stale. Before
  the first `update`, its whole content is these two lines, which `update`
  then fills:

  ```markdown
  <!-- [[[cog import wiki_consistency.sources; cog.out(wiki_consistency.sources.page_catalog("wiki/**/*.md")) ]]] -->
  <!-- [[[end]]] -->
  ```
- `overview.md`: agent-written synthesis; it links to the pages it
  summarizes, and those pages are its evidence.
- `log.md`: one entry per operation, appended at the end; earlier entries are
  never changed. An entry starts with `## [YYYY-MM-DD] <operation> |
  <detail>`, as feature 009's `raw-import` entries do: the UTC date, the
  operation (`raw-import`, `ingest`, `lint` or another named operation) and
  a short detail, then a body with counts of changed pages and findings,
  never raw contents.

## Mechanical regions

- Markers and the one-call rule follow feature 008's
  `contracts/regions.md`; the generator module is `wiki_consistency.sources`
  and sources are instance-relative paths or globs.
- A source page (`wiki/sources/`) may hold one `source_provenance` region for
  the source it summarizes.
- Pages never quote the marker syntax.

## Steps the schema states

1. After changing pages or admitting revisions: `update`, then `check`; fix
   every failure.
2. `convert`, `index`, `prepare --scope changed`; send each request to the
   backfire tool it names; confirm `contradicted` page results with
   `backfire_compare`; fix contradicted or review-flagged units or report why
   they stand; report contradictions between pages and unverifiable
   units to the user.
3. `check` again, append one `log.md` entry, commit the instance.
4. A lint operation does the same with `--scope lint` and also handles the
   cross-reference suggestions and the orphan and stale-citation findings.
