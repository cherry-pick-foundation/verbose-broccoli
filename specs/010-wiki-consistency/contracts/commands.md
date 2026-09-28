# Commands Contract

The package's console command is `wiki-consistency`. The skill runs it as
`uv run --project <plugin>/wiki-consistency --frozen --offline --no-sync
wiki-consistency <command> [--wiki <wiki-id>]`; in the repository,
`--project packages/wiki-consistency`. `--wiki` defaults to `work`, the work
plugin's vault (feature 012), and selects
`$XDG_DATA_HOME/verbose-broccoli/vaults/<wiki-id>/`.

| Command | Network | Writes |
| --- | --- | --- |
| `check` | none | none |
| `update` | none | mechanical-region text in `wiki/` only |
| `convert [--scope changed\|lint]` | none | `CACHE/wiki-evidence/` only |
| `index` | model download on first `embed` only | `CACHE/qmd/` only |
| `prepare --scope changed\|lint [--max-evidence-chars <n>] [--candidates <n>]` | none | none |

Exit codes and output follow the repository's command rules: 0 with one JSON
object on stdout; 2 for invalid arguments; 1 for a failed check or execution
failure, with each problem on stderr.

## `check`

Fails, naming page and line, when:

1. a mechanical region is stale, malformed, or names a missing source or an
   unknown generator (through `doc_regions`);
2. lychee in offline mode finds a link to a missing local file or heading
   under `wiki/`;
3. a page lacks `title`, `summary` or `sources`, or a citation names no bag;
4. a cited bag fails bagit's fast validation;
5. `git show HEAD:wiki/log.md` in the instance is not a prefix of
   `wiki/log.md` (skipped when the instance has no commit yet).

Output on success lists `orphans` (pages without inbound links from other
pages than `index.md`) and `stale_citations` (page, source ID, cited and
latest revision). It needs no cache and fails with a named tool when lychee
or Git is missing.

## `update`

Runs `doc_regions` regeneration on every page with a mechanical region, after
its shape checks. Only region text changes; a second run changes nothing.

## `convert`

Converts every cited revision in scope that has no converted text or
unreadable mark yet (R3 of research.md), within the 1 GiB budget. Output:
counts of converted, already present and unreadable revisions, and the
unreadable list with reasons.

## `index`

Creates or updates the qmd collections `pages` and `evidence` for the
instance and runs `qmd embed` with the Qwen3 embedding model of
[data-model.md](../data-model.md) when it is present or may be downloaded,
within the 3 GiB budget. Output: counts, whether semantic search is
available, and `semantic_error`, the reason in one line when the model could
not be downloaded or embedding failed (the keyword index is kept and the
command still exits 0), otherwise `null`.

## `prepare`

Needs `convert` and `index` to have run; refuses with a named step otherwise.

```json
{
  "wiki": "work",
  "scope": "changed",
  "head": "<instance HEAD commit or null>",
  "units": [{"id": "wiki/concepts/quad.md:8-9", "page": "wiki/concepts/quad.md", "heading_path": ["Quadratic formula"], "kind": "paragraph", "first_line": 8, "last_line": 9, "added": true, "outcome": "requested"}],
  "unverifiable": [{"unit": "...", "sources": ["<source-id>/<revision>"]}],
  "search": {"keyword": true, "semantic": false, "not_searched": ["crossref", "pages"]},
  "calls": {"backfire_verify": 3, "backfire_find": 0, "backfire_classify": 1},
  "requests": [
    {"kind": "evidence", "tool": "backfire_verify", "units": ["wiki/concepts/quad.md:8-9"], "arguments": {"claims": ["..."], "evidence": [{"id": "<source-id>/<revision>", "text": "..."}]}},
    {"kind": "pages", "tool": "backfire_verify", "units": ["wiki/concepts/quad.md:8-9"], "arguments": {"claims": ["..."], "evidence": [{"id": "wiki/concepts/roots.md:5-6", "text": "..."}]}},
    {"kind": "classify", "tool": "backfire_classify", "units": ["wiki/concepts/quad.md:8-9"], "arguments": {"items": [{"id": "wiki/concepts/quad.md:8-9", "text": "..."}], "classes": [{"id": "mechanical_candidate", "description": "..."}, {"id": "agent_region", "description": "..."}], "purpose": "..."}}
  ]
}
```

- Scope `changed`: units whose lines differ from the instance's `HEAD`
  (all units when there is no commit), plus every unit of pages with a stale
  citation; scope `lint`: every unit of every page except `log.md`.
  Mechanical-region text is never a unit.
- Evidence for a page's units: the converted text of each cited revision and,
  for a stale citation, of the latest revision; whole when it fits
  `--max-evidence-chars`, otherwise the passages qmd's `evidence` collection
  returns for the unit's text, limited to those revisions' files.
- Page requests: for each unit, up to `--candidates` (default 3) units of
  other pages from `qmd search` and `qmd vsearch`, deduplicated and sorted by
  page and line.
- Crossref requests (lint only): per page, candidate pages it does not link
  to, at least two, at most 20.
- Semantic search is ready when the embedding model is cached and qmd
  reports no document that still needs embeddings. When it is not ready,
  keyword search alone finds no other page for a whole unit, so `prepare`
  makes no page or crossref requests and lists them in
  `search.not_searched`; otherwise the list is empty.
- Each request stays within backfire's limits (research.md R6); every
  in-scope unit is in exactly one evidence request or in `unverifiable`.
  Output is sorted, so the same instance and cache give
  byte-identical output.
- Text comes only from `wiki/` pages and the converted evidence of cited
  revisions.

## The judgment step (agent)

1. Run `update`, `check`, `convert`, `index`, `prepare`; read `calls` before
   sending anything.
2. Send each request to the tool it names on the work plugin's backfire
   server through the MCP client. If
   backfire is unavailable, stop and report that the step did not run.
3. For a `pages` result `contradicted`, call `backfire_compare` with the two
   units' texts (`passage_a`, `passage_b`) and report a confirmed
   contradiction to the user.
4. Fix `evidence` results that are `contradicted` or `review`, or report why
   they stand; report `unverifiable` units.
5. Treat `crossref` and `classify` results as suggestions.
6. `check`, one `log.md` entry, commit.
