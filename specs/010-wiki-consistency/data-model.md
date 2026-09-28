# Data Model: Wiki Document Consistency

Nothing is stored in the repository. `DATA` and `CACHE` stand for
`$XDG_DATA_HOME/verbose-broccoli` (default `~/.local/share/verbose-broccoli`)
and `$XDG_CACHE_HOME/verbose-broccoli`. `INSTANCE` is
`DATA/wikis/<wiki-id>/`, `default` for feature 009's instance. Feature 008's
entities (mechanical region, agent region, unit, judgment request, drift
finding; `specs/008-doc-consistency/data-model.md` on `feature/doc-consistency`)
apply with the differences below.

## Instance (feature 009)

```text
INSTANCE/
├── AGENTS.md          # schema; extended by this feature (contracts/pages.md)
├── .git/              # history of AGENTS.md and wiki/
├── raw/<kind>/<source-id>/<revision>/   # one BagIt bag per revision
└── wiki/
    ├── index.md       # one mechanical region: page_catalog
    ├── overview.md    # agent region
    ├── log.md         # agent-written, append-only, never judged
    └── sources/, entities/, concepts/, comparisons/, synthesis/  # pages
```

## Page

| Field | Source | Rule |
| --- | --- | --- |
| path | file | `wiki/**/*.md` except the three special pages |
| `title` | front matter | non-empty, one line |
| `summary` | front matter | non-empty, one line; used by the catalog and find requests |
| `sources` | front matter | non-empty list of citations |
| links | markdown-it-py link tokens | relative links to other pages resolve to files |

## Citation

| Field | Rule |
| --- | --- |
| `id` | a source ID: a folder `raw/<kind>/<id>/` exists |
| `revision` | a revision name: `raw/<kind>/<id>/<revision>/` is a bag that passes fast validation |
| stale | derived: `revision` is not the source's last revision by name |

## Mechanical regions in Wiki pages

| Generator | Sources | Output |
| --- | --- | --- |
| `page_catalog` | `wiki/**/*.md` | one line per page, sorted by path: `- [<title>](<relative path>) — <summary>` |
| `source_provenance` | `raw/<kind>/<source-id>/*/bag-info.txt` and `raw/<kind>/<source-id>/*/manifest-sha256.txt` | source ID, kind, original file name (from the manifest's `data/<name>`), and per revision: name, `Source-Modified`, `Payload-Oxum` size, SHA-256 from the manifest |

Sources are relative to `INSTANCE`. Generators read only those files.

`page_catalog` output, for a page `wiki/concepts/quad.md`:

```markdown
- [Quadratic formula](concepts/quad.md) — How the quadratic formula follows from completing the square.
```

`source_provenance` output, one source per call, revisions sorted by name:

```markdown
Source `<source-id>` (`<kind>`), original file `<name from data/<name>>`:

- `<revision>`: modified `<Source-Modified>`, <bytes from Payload-Oxum> bytes, SHA-256 `<hex>`
```

It has no heading, so it does not change the page's heading structure, and it
ends with a newline.

## Converted evidence

| Field | Location | Rule |
| --- | --- | --- |
| text | `CACHE/wiki-evidence/<wiki-id>/markitdown-<version>/<source-id>/<revision>.md` | converted once per revision and converter version; never updated |
| unreadable mark | `.../<revision>.unreadable.json` | `{"reason": "unsupported_format" \| "empty_text" \| "conversion_failed", "detail": "..."}` |

Lifecycle: created by `convert`; removed only by deleting the cache. Budget
1 GiB for `CACHE/wiki-evidence/`, checked before each write; temporary files
beside the target are removed on failure, SIGINT, SIGTERM and at the next
start.

## Search index

| Item | Location |
| --- | --- |
| index | `CACHE/qmd/<wiki-id>.sqlite` |
| collections configuration | `CACHE/qmd/config/<wiki-id>.yml` (`pages` → `INSTANCE/wiki`, `evidence` → the converted evidence folder) |
| models | `CACHE/qmd/models/`; the embedding model is `QMD_EMBED_MODEL=hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf` (610 MB) |
| GPU shader cache | `CACHE/qmd/mesa_shader_cache/` (`MESA_SHADER_CACHE_DIR`) |

Budget 3 GiB for `CACHE/qmd/`, checked before `qmd update` and `qmd embed`.
A failed or interrupted update deletes the index file; the next `index` run
rebuilds it.

## Candidate

| Field | Rule |
| --- | --- |
| unit | the in-scope unit it was found for |
| candidate unit | the unit of another page whose line range contains the hit's line |
| tool | `search` or `vsearch` |

Candidates are not stored; `prepare` computes them from the index.

## Judgment request (differences from feature 008)

| `kind` | Tool | Claims or query | Evidence or candidates |
| --- | --- | --- | --- |
| `evidence` | `backfire_verify` | units of one page | cited revisions' converted text (whole, or matching passages), items `<source-id>/<revision>` or `<source-id>/<revision>#<n>`; for `overview.md`, linked pages, items by path |
| `pages` | `backfire_verify` | units | candidate units of other pages, items by unit id |
| `crossref` | `backfire_find` | page title and summary | unlinked candidate pages, `{id: path, text: title, summary and first paragraph}` |
| `classify` | `backfire_classify` | added units | as feature 008 |

## Unit outcome

Every in-scope unit ends in exactly one of: `requested` (in one evidence
request) or `unverifiable`: all cited sources are unreadable, or no evidence
is left to send (an `overview.md` unit whose page links to no page, or a unit
for which no passage fits `--max-evidence-chars`); its `sources` list the
cited revisions or linked pages, possibly none.

## Module interfaces

The workers share these Python interfaces in `src/wiki_consistency/`; paths
in results are POSIX strings relative to `INSTANCE` unless named otherwise.

| Module | Function | Contract |
| --- | --- | --- |
| `instance` | `roots(env)` | `{"data": Path, "cache": Path}`: `DATA` and `CACHE`, with feature 009's XDG rules (unset, empty or relative means the default under `HOME`) |
| `instance` | `instance_path(wiki_id, env)` | `DATA/wikis/<wiki-id>/`; `ValueError` for feature 009's invalid names |
| `instance` | `pages(instance)` | pages sorted by path: `{"path", "title", "summary", "sources": [{"id", "revision"}], "special": bool, "problems": [...]}`; front matter read with PyYAML |
| `instance` | `mask_front_matter(text)` | the text with each front-matter line replaced by an empty line, so line numbers stay |
| `instance` | `revisions(instance)` | `{source_id: [{"kind", "id", "revision", "path"}]}`, each list sorted by revision name; the last is the latest |
| `evidence` | `convert(instance, wiki_id, cache, revisions)` | converts the given revisions (items of `revisions(instance)`); returns `{"converted", "present", "unreadable": [{"id", "revision", "reason", "detail"}]}` |
| `evidence` | `read(cache, wiki_id, source_id, revision)` | `{"text": str}` or `{"unreadable": reason}`; `LookupError` when `convert` has not run for it |
| `search` | `index(instance, wiki_id, cache, *, download)` | builds or updates the `pages` and `evidence` collections; returns counts and `"semantic": bool` |
| `search` | `search(wiki_id, cache, queries)` | one Node process for all queries; each query `{"id", "text", "collection", "limit"}`; each hit `{"query", "collection", "path", "line", "score", "mode": "lex" or "vec"}`, `path` relative to the collection's folder; `LookupError` when the index is missing |
| `requests` | `prepare(instance, wiki_id, cache, *, scope, max_evidence_chars, candidates)` | the `prepare` output object of [contracts/commands.md](contracts/commands.md) |

## Drift finding (additions)

| origin | Meaning |
| --- | --- |
| `check` | failed deterministic check: region, link, metadata, bag, log |
| `orphan`, `stale_citation` | deterministic findings that do not fail the check |
| `backfire_verify`, `backfire_compare`, `backfire_find`, `backfire_classify` | judgment results |

Findings are reported by the agent and are not stored by the tooling; the
operation's `log.md` entry summarizes them.
