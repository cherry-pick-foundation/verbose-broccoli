# Research: Wiki Document Consistency

Probes ran on 2026-09-28 on the development machine (Linux x86_64, uv 0.11.32,
Python 3.14 through uv, Node 24.19.0, npm 12.1.0, Quarto's bundled Pandoc and
Typst 0.15.1), in the session's scratch folder outside the checkout, with
synthetic files only. The brief is `briefs/2026-09-27-linear-and-documents.md`,
section 3; its decisions are settled, and this file confirms what it leaves
open. Feature 008's documents were read from `feature/doc-consistency` at
`5252aef`, feature 009's from `feature/wiki-storage` at `c8fbabc`, and
backfire's code from `packages/backfire/` on this branch.

## R1. Region model and shared component

- **Decision**: Reuse feature 008 unchanged in its model: Cog blocks in HTML
  comments whose code is one call of a registered generator on named source
  files (008 `contracts/regions.md`), units from markdown-it-py, and
  request splitting from `packages/doc-regions`. For the Wiki, sources are
  paths relative to the instance root, the targets are every `wiki/**/*.md`
  page, and the generators live in this feature's package (R7).
- **Rationale**: The brief's decision 1 repeats section 2's model. Feature
  008's research ends with "For feature 010", which lists these parts for
  reuse.
- **Generators this feature adds** (the only mechanical regions at first):
  - `page_catalog("wiki/**/*.md")`: the `index.md` catalog, one line per page
    (relative link, title, summary), sorted by path; `index.md`,
    `overview.md` and `log.md` are left out.
  - `source_provenance("raw/<kind>/<source-id>/*/bag-info.txt",
    "raw/<kind>/<source-id>/*/manifest-sha256.txt")`: in a source
    page, the source ID, kind, original file name, and each revision's
    admission time, modification time, size and digest, read from the bags.
  Further regions come from `backfire_classify` suggestions, as in 008 R9.
- **Alternatives considered**: A Wiki-only marker syntax; rejected, because
  decision 1 asks for the same model and one engine keeps one owner
  (constitution VII).

## R2. `index.md`, `overview.md` and `log.md` under principle VI

Principle VI, point 2, says: "The LLM maintains pages, cross-references,
`index.md`, `overview.md`, and the append-only `log.md` under the selected
operation's scope." The draft in the `feature-constitution-cleanup` worktree
(uncommitted on 2026-09-28) keeps the sentence without the last phrase.

- **Decision (the user's choice on 2026-09-28, spec.md Clarifications)**:
  - `index.md` is one mechanical region (`page_catalog`). A generator that
    the LLM runs is not the LLM maintaining the text, so the sentence needs a
    patch amendment, for example "The LLM maintains pages, cross-references,
    `overview.md`, and the append-only `log.md`; `index.md` is regenerated
    from page metadata." The amendment is a `docs` commit (patch bump under
    the Governance rule) and the first implementation task, coordinated with
    the constitution cleanup feature if that has not merged.
  - `overview.md` is synthesis, which no generator can derive; it stays an
    agent region, judged against the pages it links to.
  - `log.md` is history: its entries are right about the moment they
    describe, so judging them against current evidence would report false
    drift, and regenerating them is impossible because feature 009 keeps no
    import report (009 FR-014). It stays agent-written; the offline check
    compares the committed text (`git show HEAD:wiki/log.md` in the instance)
    with the working text and fails unless the first is a prefix of the
    second.
- **Rationale**: Principle VI's "Direct Wiki index navigation and page
  reading MUST work without cache" holds, because the catalog is committed
  Markdown, not a cache product. Feature 009 creates `index.md` empty, so the
  first regeneration adds the region markers.

## R3. Evidence conversion: markitdown

- **Decision**: Use markitdown 0.1.8 (PyPI, MIT, released 2026-09-21,
  Python 3.10 to 3.14) with the `docx`, `pdf` and `pptx` extras, locked in
  this feature's package (R7). Plain-text and Markdown sources are read as
  they are. Each cited revision's payload is converted once into
  `$XDG_CACHE_HOME/verbose-broccoli/wiki-evidence/<wiki-id>/markitdown-0.1.8/<source-id>/<revision>.md`;
  a revision that cannot be converted, or converts to text without letters,
  gets a `<revision>.unreadable.json` beside it with the reason.
- **Probe**:
  - A DOCX and a PPTX made from a Korean Markdown file with a table
    (Pandoc), and a text PDF (Typst, Noto Sans CJK KR), all converted with
    Korean text and the table intact; the three runs took 5.8 s in total,
    including uv's first install.
  - An image-only PDF (one filled rectangle) converted to empty output with
    exit 0, so emptiness must be detected by the tool.
  - A file with the OLE compound-file signature and a `.hwp` name failed with
    `UnsupportedFormatException` and exit 1. HWP is the format of several
    files in feature 009's survey (009 research R6).
  - The extras pull in `magika` and `onnxruntime` (37 MB of wheels); they run
    locally, and conversion of local files makes no network request.
- **Changed from the brief**: markitdown cannot read HWP, and neither
  markitdown nor anything else in the brief reads scanned PDFs without OCR.
  As the user decided, both are reported as unreadable; Docling (OCR) and an
  HWP converter wait for the user's decision.
- **Cache writer** (constitution VII): budget 1 GiB for the `wiki-evidence`
  folder, checked before each write; each file is written to a temporary name
  in the same folder and renamed into place, and temporary names are removed
  on failure, on SIGINT or SIGTERM, and at the start of the next run. Files
  are keyed by immutable revisions and the converter version, so they never
  need updating; deleting the folder only costs reconversion.

## R4. Candidate search: qmd

- **Decision**: Use qmd 2.8.3 (npm `@tobilu/qmd`, MIT, Node 22 or later),
  pinned with `package.json` and `package-lock.json` in this feature's package
  and installed with `npm ci --ignore-scripts`. Run it with
  `XDG_CACHE_HOME=$XDG_CACHE_HOME/verbose-broccoli`,
  `QMD_CONFIG_DIR=$XDG_CACHE_HOME/verbose-broccoli/qmd/config` and
  `--index <wiki-id>`, with two collections: `pages` (the instance's `wiki/`)
  and `evidence` (the converted evidence folder of R3), both with qmd's
  default `**/*.md` pattern. Use `qmd search --json` and `qmd vsearch --json`
  only, never `qmd query`, whose reranking overlaps `backfire_rerank`.
- **Probe** (keyword search only):
  - `npm install --save-exact @tobilu/qmd@2.8.3` took 15 s and 854 MB
    (`node-llama-cpp` ships prebuilt binaries); npm 12 held back the
    packages' install scripts, and `qmd collection add` and `qmd search` still
    worked.
  - With the variables above, qmd wrote only `qmd/index.sqlite` and
    `qmd/config/index.yml` under the given cache folder and nothing into the
    collection folder.
  - `qmd search "학생"` found a Korean page containing `학생이`, and English
    keyword search worked; `--json` results give the file and line, which map
    to a unit's line range.
  - Source reading: the index path comes from `INDEX_PATH` or
    `$XDG_CACHE_HOME/qmd/<index>.sqlite` (`dist/store.js`), models from
    `$XDG_CACHE_HOME/qmd/models` (`dist/llm.js`), and the configuration from
    `QMD_CONFIG_DIR` (`dist/collections.js`); FTS5 uses the `porter
    unicode61` tokenizer (`dist/store.js`).
- **Not yet proved**: `qmd embed` and `vsearch`. They download GGUF models
  from Hugging Face on first use. qmd's README says the default
  `embeddinggemma-300M` has limited coverage for Korean and recommends
  `QMD_EMBED_MODEL=hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf`
  for multilingual text. Constitution I requires native tools to be proved
  before adoption, so the first implementation task runs `embed` and
  `vsearch` with that model on synthetic Korean pages, records the download
  size and whether the held-back install scripts matter, and sets the model.
  Until then `vsearch` is optional: without the model, keyword candidates are
  used and the output says so.
- **Changed from the brief**: qmd also indexes the converted evidence, which
  is Markdown in the cache, so evidence for a long source can be narrowed to
  the passages that match a claim (R6). Semantic search needs a one-time model
  download (network) and a multilingual model for this Korean corpus.
- **Cache writer**: budget 3 GiB for `qmd/` (models, index, configuration),
  checked before `qmd update` and `qmd embed`; on a failed or interrupted
  update the index file is deleted and rebuilt next time, since it is
  rebuildable. Principle VI's direct reading and the offline check never use
  it.

## R5. Lint: deterministic checks and backfire judgments

Karpathy's LLM Wiki names contradictions between pages, stale claims, orphan
pages, missing pages and missing cross-references.

| Lint item | Kind | How |
| --- | --- | --- |
| Missing pages (a link to a page or heading that does not exist) | Deterministic, fails the check | lychee `--offline --include-fragments` on `wiki/` (008 R4) |
| Orphan pages (no inbound link from another page; `index.md` does not count, since it lists every page) | Deterministic finding | link graph from markdown-it-py link tokens |
| Stale citations (a cited revision that is not its source's latest) | Deterministic finding | bag names under `raw/` |
| Stale claims | Backfire | `backfire_verify` of the page's units against the cited revisions' text, including the newest revision when a citation is stale |
| Contradictions between pages | qmd candidates, backfire judgment | `backfire_verify` of a unit against candidate units of other pages as evidence items; a `contradicted` verdict names the item (`supporting_evidence`), and one `backfire_compare` of the two units confirms it before it is reported |
| Missing cross-references | qmd candidates, backfire suggestion | `backfire_find` with the page's title and summary as the query and unlinked candidate pages; never final (005 `contracts/evaluation.md`) |

"Missing pages" in Karpathy's wider sense, a concept discussed on several
pages without a page of its own, is not a consistency check; it stays with the
agent that writes pages (a future ingest feature).

- **Why verify first for contradictions**: `backfire_compare` judges one pair
  per call. `backfire_verify` takes many claims and evidence items in one
  request (each claim costs three answer cells plus one per evidence item and
  one for "none", within the 672-cell limit in [docs/backfire.md](../../docs/backfire.md)),
  so pages are screened in batches and only flagged pairs cost a compare call.

## R6. Backfire requests

Read from `packages/backfire/src/backfire/tools/` and `lib.py` on this branch.

- `backfire_verify`: `claims` (strings), `evidence` (`{id, text}` items),
  optional `auto_accept` (default 0.8). With more than one evidence item it
  asks which item a claim rests on, and returns it as `supporting_evidence`.
  Answer cells per claim: 3, plus evidence items + 1 when there are two or
  more.
- `backfire_compare`: `passage_a`, `passage_b` (each at most 20,000
  characters), optional `aspects` (at most 10), `purpose`.
- `backfire_find`: `query`, `candidates` (1 to 250, text truncated at 2,000
  characters), `top_k` (1 to 50). Needs at least two candidates
  ([docs/backfire.md](../../docs/backfire.md), `invalid_request`).
- `backfire_classify`: at most 64 items per call, 2,000 characters each
  (`MAX_ITEMS`, `MAX_ITEM_CHARS` in `lib.py`).
- **Decision**: The preparation command prints, per scope: evidence requests
  (units of one page as claims; evidence items are the cited revisions'
  converted text, whole when under `--max-evidence-chars`, otherwise the
  passages qmd's `evidence` collection returns for the claims, limited to the
  cited revisions' files); page requests (units as claims, up to
  `--candidates` candidate units of other pages as evidence); find requests
  in lint scope; classify requests for added units. It splits requests to
  stay within the cell limit, and prints the number of
  calls per tool. The agent sends them through its MCP client and confirms
  `contradicted` page results with `backfire_compare`, as in 008 R6.
- **Evidence selection is deterministic**: qmd's keyword search gives the
  same result for the same index; `vsearch` output depends on the model,
  which is pinned by name, and the index state, both in the cache. The
  byte-identical guarantee (SC-004) is for the same instance and cache.

## R7. Where the code lives and how it ships

- **Decision**: A new uv project `packages/wiki-consistency/` laid out like
  backfire and `packages/doc-regions` (`pyproject.toml`, `.python-version`
  3.14.4, `uv.lock`, `src/wiki_consistency/`, `tests/`), depending on
  `doc-regions` through a relative path source (`../doc-regions`), markitdown
  0.1.8 with extras, bagit 1.9.0 (feature 009's pin) and PyYAML for page
  metadata; its `package.json` and `package-lock.json` pin qmd. A work-plugin
  skill `plugins/work/skills/wiki-consistency/SKILL.md` holds the procedure.
  The work plugin's build copies `packages/doc-regions` and
  `packages/wiki-consistency` side by side into the built plugin, so the
  relative path source still resolves, and the skill runs
  `uv run --project <plugin>/wiki-consistency --frozen --offline --no-sync
  wiki-consistency ...`.
- **Rationale**: The brief says the Wiki tooling runs as part of the work
  plugin and shared components go through `packages/` and the build copy, as
  backfire does; backfire is also one plugin's runtime package under
  `packages/` (docs/architecture.md, "Backfire server"). Feature 009 put its
  single glue script in its skill with a uv script lock because it has no
  local dependency; this feature depends on `doc-regions`, which a script
  lock cannot express portably.
- **Build**: feature 011 (CHE-9) owns the backfire declaration in
  `plugins/work/mcp.json` and a per-plugin build that takes the plugin name
  and a per-plugin module list (spec.md Clarifications). This feature adds
  `doc-regions` and `wiki-consistency` to the work plugin's list, side by
  side at the built plugin's root. The build's interface is fixed only in
  feature 011's plan, so this plan assumes none; T002 records it.
- **2026-09-28, 011's build as planned** (`87563f8` on
  `feature/backfire-education`, its `contracts/build.md`): `deno task
  backfire:build -- <plugin> <output>`; one table in
  `packages/backfire/src/backfire_tools/build.py` lists, per plugin, the
  packages under `packages/backfire/src/` copied into `<output>/backfire/`.
  011 will not add copying of whole `packages/<name>` projects, since it has
  no consumer for it. So this feature adds, in its own change after 011
  merges, a second kind of entry to that table: a per-plugin list of
  `packages/<name>` projects copied beside `backfire/`, without `.venv` and
  `node_modules`, and lists `doc-regions` and `wiki-consistency` in the work
  row (T025). The table stays the one place to extend, as the user decided.
- **Host tools**: lychee 0.24.2 (feature 008 installs it) and Node 22 or
  later; the tool fails with a named missing tool when either is absent.
- **Alternatives considered**: The glue as a skill script with PEP 723
  metadata (cannot depend on a local package portably); the glue inside
  `packages/doc-regions` (would put Wiki-only code and markitdown into the
  repository tooling's environment).

## R8. What this feature needs from feature 008's package

Feature 008 US4 says feature 010 reuses its component "without change to the
component's region rules, unit splitting or request preparation". The Wiki
needs three things 008's plan does not state:

1. Target globs (`wiki/**/*.md`) instead of a fixed list of existing files.
2. A root other than the repository (the instance) against which sources and
   targets resolve, and a generator path outside it.
3. Request preparation with caller-supplied evidence per unit, instead of the
   repository diff that 008's `prepare` always uses.

- **Decision**: Use `doc_regions` as a library (its `regions`, `units` and
  `requests` modules) rather than its `prepare` command, and, at
  implementation, add these as backward-compatible parameters to those
  modules if 008 has not. This is a conflict to settle with feature 008's
  owner; the orchestrator is told in this feature's completion report.
- **2026-09-28, settled with 008's orchestrator**: feature 008 adds all three
  to `packages/doc-regions` as library parameters, so T012's fallback should
  not be needed. Planned interface: `config.load(config_path, root)` accepts
  globs in `targets` and `report_only`, resolved against `root` and returned
  as sorted root-relative paths; every function takes `root: Path`, and
  `generator_path` may lie outside it; `requests.verify_requests(groups,
  max_claims, max_evidence_chars)` takes a list of `(units, evidence)`
  groups, evidence being `{id, text}` items, and splits each group within
  backfire's limits. 008's orchestrator confirmed that `verify_requests`
  never drops or trims a unit or evidence item and raises `ValueError` when a
  group's evidence alone cannot fit (more than 249 items); that ids and texts
  pass through and each request carries its `units` in claim order; that
  output follows input order; and that `units.split(document, text,
  base_text=None)` marks a unit `added` only when all its lines are inserted
  relative to `base_text`. This feature's `changed` scope needs units with
  any changed line, so `requests.py` derives it from the unit line ranges and
  a diff against the instance's `HEAD`; `added` still selects classify
  requests. `classify_requests` returns at most 64 items per request and does
  not trim text; backfire truncates past 2,000 characters. `verify_requests`
  also raises for a group with no evidence, so `requests.py` builds no group
  for an unverifiable unit or for a unit without candidates. Units have the
  kinds of 008's contract, including `blockquote`; thematic breaks and link
  reference definitions are no unit. T002 rechecks all of this on `develop`.

## R9. Personal data and credentials

- **Decision**: The preparation command reads only `wiki/` pages and the
  converted evidence of cited revisions; it never opens the configuration,
  state, credential files or anything outside the instance and its cache
  folders. Personal identifiers are handled by feature 011 (CHE-9): the
  agent sends the requests to the work plugin's backfire server, whose judge
  replaces them before the provider call. This feature adds no filter of its
  own and no blanket prohibition, as the brief asks (the user's choice of
  2026-09-28, spec.md Clarifications).
- **Current conflict**: [docs/backfire.md](../../docs/backfire.md), "Requests,
  data, and records", says "Do not send secrets, credentials, or private
  personal records such as student data." Feature 011 is expected to replace
  that sentence with its policy; until it merges, this feature is not
  implemented (FR-023).
- **Feature 011's scope**: its orchestrator reported that the work plugin's
  backfire gets a pseudonymization module and an education profile. Whether
  pseudonymization happens inside backfire or must be applied to requests
  before they are sent decides where FR-019 is enforced; T002 records it.
- **2026-09-28, 011's answer**: 011 has no withhold rule and no data
  classification. When the work build's shipped `config.toml` sets
  `pseudonymize = true`, its judge replaces identifiers (roster full and
  given names, guardian names, schools, phone numbers, emails) before the
  provider call, and sends everything else as is (011
  `contracts/pseudonymization.md`). So there is no policy for FR-019 to
  read; the user chose to rely on that replacement and drop the `withheld`
  list. Both plugins' `mcp.json` declare the server as `backfire` with the
  same eleven tool names; how Codex CLI and Claude Code tell two same-named
  servers from two plugins apart is unverified, and 011's client check (its
  T020) will report it. The judgment step must use the work plugin's server.
- **Existing limits**: feature 009 keeps student records out of `raw/` by an
  excluded path (009 FR-012), and constitution III keeps operational records
  out of the Wiki, so evidence is the user's own teaching material and
  similar documents.

## R10. Left out

- Docling and HWP conversion (R3), until the user decides.
- `qmd query` and qmd's MCP server: the agent calls qmd through this
  feature's command only, for candidates.
- Vale and code maps, as in feature 008.
- The example schema `docs/examples/wiki/AGENTS.md`: it describes a
  `wiki apply` command that does not exist; feature 009's task T037 fixes it.

## R11. Recheck on `develop` (T002, 2026-09-28)

After features 009, 008 and 011 merged (`develop` at `1166a84`), the
interfaces this plan assumed were read again. Differences and their effect:

- **Feature 009** (`specs/009-wiki-storage/`, the schema template in
  `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`): the bag layout,
  the `bag-info.txt` fields and the revision names
  (`YYYYMMDDTHHMMSSffffffZ`) are as assumed. The SHA-256 digest is in
  `manifest-sha256.txt`, not `bag-info.txt`, so `source_provenance` names
  both files as sources; the original file name comes from the manifest's
  `data/<name>` path. `log.md` entries start with
  `## [YYYY-MM-DD] <operation> | <detail>` (009 writes `raw-import |
  <location>`), so this feature's entries use the same form. `init` runs
  `git init` without a commit, which the `log.md` prefix check already
  allows. `--wiki` names and XDG roots follow 009's rules: an empty name,
  `.`, `..` or a name with `/` or NUL is invalid, and an unset, empty or
  relative XDG value means the default under `HOME`. The template's last
  line, "Page conventions and the ingest, query and lint workflows come from
  a later change to this file", is what T027 replaces.
- **Feature 008** (`packages/doc-regions`): `config.files(root, glob)`
  expands a root-relative glob, and `regions.check` and `regions.update`
  take `root`, an explicit target list, the generator module name and a
  generator path, so this feature needs no TOML file; the generator module
  is `wiki_consistency.sources` and the generator path is the package's
  `src/` folder. `regions.check` also runs lychee offline on each target,
  so the link check comes from it. Three differences:
  1. `requests.verify_requests(groups)` has no `max_claims` or
     `max_evidence_chars`; it splits claims by the 672-cell limit only. This
     feature drops `--max-claims`, as 008 did, and keeps
     `--max-evidence-chars` for its own evidence selection.
  2. `regions.cog` hard-codes the failure message "Run deno task
     doc-regions:update", but the Wiki check must name `wiki-consistency
     update`. T012 adds a backward-compatible keyword for that message,
     default unchanged.
  3. `units.split` parses YAML front matter as a thematic break and a
     setext heading, which would make the metadata a unit. This feature
     replaces the front-matter lines with empty lines, keeping line numbers,
     before splitting the current and the base text.
- **Backfire** (R6): the limits are as recorded; `backfire_verify` has no
  text limit of its own, so `--max-evidence-chars` bounds the provider's
  context; `backfire_compare` truncates each passage at 20,000 characters
  rather than refusing it.
- **Feature 011**: the build table is `PLUGINS` in
  `packages/backfire/src/backfire_tools/build.py`, mapping a plugin to its
  packages under `packages/backfire/src/` and its profile; it copies
  `plugins/<plugin>/` and then `backfire/` into the output within a 16 MiB
  budget, so T025's projects must stay small and leave out `.venv`,
  `node_modules` and `__pycache__`. `plugins/work/mcp.json` declares
  `backfire` at `${PLUGIN_ROOT}/backfire`. Claude Code's plugin
  documentation names the work plugin's tools
  `mcp__plugin_work_backfire__<tool>` (documented, not observed); how Codex
  separates two same-named servers is unverified (011 research, "Results").
  [docs/backfire.md](../../docs/backfire.md) now describes the work build's
  pseudonymization, so R9's "Current conflict" is resolved.

