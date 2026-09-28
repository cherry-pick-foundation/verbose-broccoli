# Topics Contract

This contract is what the implementation adds to the schema template
(`plugins/work/skills/wiki-raw-import/assets/AGENTS.md`), so every vault's
`AGENTS.md` states it. Feature 010's pages contract
(`specs/010-wiki-consistency/contracts/pages.md`) stays in force except where
this contract adds to it.

## Schema front matter

The template starts with front matter that declares the vault's topics:

```yaml
---
# The topics this vault's pages may list; see "Pages".
topics: []
---
```

- `topics` is a list of non-empty single-line names, each listed once. A new
  vault's list is empty.
- An agent adds a topic to this list in the same vault commit as the first
  page that lists it, and reuses a declared topic instead of adding another
  spelling of it.

## Page metadata

The example front matter gains a `topics` list:

```yaml
---
title: Quadratic formula
summary: How the quadratic formula follows from completing the square.
topics:
  - Algebra
sources:
  - id: 0199a0e2-7c1b-7d3e-9f00-000000000000
    revision: 20260928T010203000000Z
---
```

- `topics` lists one or more topics declared at the top of this file, each
  once. A page may carry several topics. Topics do not replace the folders:
  a page stays in the folder for its kind.

## Index

- `update` lists every other page under a heading for each of its topics,
  with its title and summary; topics and pages are in sorted order, and a
  page with several topics appears under each. The region line in
  `index.md` does not change.

## Check

- `check` fails on a page whose `topics` is missing, empty, malformed, lists
  a name twice or names an undeclared topic, and on an `AGENTS.md` whose
  topic list is missing or malformed. `update` refuses on the same problems
  and writes nothing.
