# Data Model: Topics in Vault Page Metadata

## Declared topic list

Front matter at the top of a vault's `AGENTS.md`:

```yaml
---
# The topics this vault's pages may list; see "Pages".
topics: []
---
```

| Field | Rule |
| --- | --- |
| `topics` | A list, possibly empty, of non-empty single-line strings, each listed once |

- Identity: the exact string. `Algebra` and `algebra` are two topics.
- Lifecycle: a topic is added in the same vault commit as the first page
  that lists it. Removing or renaming one is an ordinary schema edit; the
  check then names every page that still lists the old name.
- A declared topic that no page lists is valid and gets no index group.

## Page metadata

Feature 010's front matter plus one required field:

| Field | Rule |
| --- | --- |
| `title` | Unchanged: a non-empty single line |
| `summary` | Unchanged: a non-empty single line |
| `sources` | Unchanged: a non-empty list of `id` and `revision` |
| `topics` | A non-empty list of non-empty single-line strings, each listed once, each declared in the vault's `AGENTS.md` |

`instance.pages()` returns `topics` with the other fields; a page whose
`topics` is malformed carries a problem and an empty list.

## Index

`wiki/index.md` keeps its one region, `page_catalog("wiki/**/*.md")`. Its
output for pages `concepts/alpha.md` (topics `Algebra`, `Geometry`) and
`sources/source.md` (topic `Algebra`):

```markdown
## Algebra

- [Alpha](concepts/alpha.md) — A synthetic page.
- [Source](sources/source.md) — A synthetic source.

## Geometry

- [Alpha](concepts/alpha.md) — A synthetic page.
```

- Topics sorted by Python string order; pages under a topic sorted by path.
- A vault without pages gives an empty region.

## Check problems

| Condition | Document | Command |
| --- | --- | --- |
| `topics` missing, not a list, empty, or holds a non-string, empty or multi-line name | the page | `check`; `update` refuses through `page_catalog` |
| A page lists a name twice | the page | `check`; `update` refuses |
| A page lists a name `AGENTS.md` does not declare | the page | `check`; `update` refuses |
| `AGENTS.md` missing, unreadable, without front matter, or `topics` not a list of unique non-empty single-line names | `AGENTS.md` | `check`; `update` refuses |
