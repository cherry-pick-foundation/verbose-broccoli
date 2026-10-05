---
name: wiki-consistency
description: Keep a verbose-broccoli Wiki instance's pages consistent with their raw evidence and with each other. Use after changing Wiki pages or admitting raw revisions, before committing the instance, and when the user asks for a lint of the Wiki; not for admitting raw documents or for writing pages from them.
---

Read [the work plugin rules](../../AGENTS.md) before using this skill.

# Wiki Consistency

An English `.qmd` Wiki page is made of mechanical regions, which a generator rebuilds from
named files, and agent-written text, which Jev judges against the raw
evidence the page cites. Agent-written text is in English, apart from short
direct quotes kept next to their translation. Student names use the
roster's romanized spelling so that step 3 can replace them, the Korean
spelling stays only in the roster, and schools are written as their domain
IDs. The instance's `AGENTS.md` states these rules, the page
metadata, the special pages and these steps. It also owns the separate raw,
original-language `text/` and derived Korean `site/` roles; Wiki page rules do
not turn retained source text into English knowledge or published material.

`DATA` and `CACHE` below are the `verbose-broccoli` folders under the XDG data
and cache roots (by default `~/.local/share` and `~/.cache`). The Wiki lives
in the shared container, `DATA/llm-wiki/<name>/`; this skill uses the `work` wiki unless the
user selects another with `--wiki <name>`.

## Commands

Run them from this skill's folder. The tool is the repository's
`packages/wiki-consistency` project:

```sh
uv run --project ../../../../packages/wiki-consistency --frozen --offline --no-sync wiki-consistency <command> [--wiki <name>]
```

Install it once after the plugin is installed or updated:

```sh
uv sync --project ../../../../packages/doc-regions --frozen --no-dev
uv sync --project ../../../../packages/education-privacy-gate --frozen --no-dev
uv sync --project ../../../../packages/wiki-consistency --frozen --no-dev
npm ci --ignore-scripts --no-audit --no-fund --prefix ../../../../packages/wiki-consistency
```

The first two lines prepare `doc-regions` and the gated judgment proxy. `check` uses local Vale 3.23.0
regex rules for page text; it reads the work-owned domain roster only when a direct student
page or Hangul, Chinese or Japanese text needs roster checks.

| Command | What it does | Network | Writes |
| --- | --- | --- | --- |
| `check` | Checks mechanical regions, links, page metadata, the topics declared in `AGENTS.md`, cited bags, that `log.qmd` only grew, and the Vale page rules below; lists orphan pages and stale citations | none | nothing |
| `update` | Regenerates stale mechanical regions | none | region text in `wiki/` |
| `convert [--scope changed\|lint]` | Retains selected cited raw revisions as full original-language `.qmd`, reusing existing text | none | `text/<source-id>/<revision>.qmd`; failure diagnostics in `CACHE/wiki-evidence/` |
| `index` | Builds the local search index | the embedding model's one-time download | `CACHE/qmd/` |
| `prepare --scope changed\|lint [--review-receipts <json>]` | Prints Jev requests and reason-bearing unverifiable diagnostics | none | nothing |

On success a command prints one JSON object and exits 0. `prepare` also prints
its diagnostic JSON on stdout when `unverifiable` is nonempty, then exits 1.
Boundary, bag, index and execution errors, and failed `check` problems, print
diagnostics on stderr and exit 1. Invalid command-line arguments exit 2.
`check` is the separate offline structural, metadata and rule stage; a pass
does not prove exact sentence evidence or semantic correctness.
It reports every leftover `wiki/**/*.md` as a migration failure before catalog
or privacy checks. It rejects executable Quarto cells and executable inline
code, plus includes/shortcodes in Wiki source, including active shortcodes
inside code examples; escape them with `{{{< ... >}}}`. Inert code examples
remain allowed. Executable inline expressions use single backticks around
`{language}` followed by a space or tab and an expression, including Python,
R, Jupyter kernel languages and Observable (`ojs`). Bare `{notcode}` or `{a,b}`,
fence-style options, no-space forms and double-backtick examples stay literal.
Quarto preprocesses these raw spans inside comments, image labels and ordinary
code examples too; its R path also preprocesses front matter. A backslash before
the opening backtick does not escape execution, and extra closing backticks do not prevent it. For literal examples,
use double backticks directly around the brace-tag expression, with no nested
single-backtick executable span. Inline diagnostics name the opening backtick's
actual source line, including after multiline spans. These
source checks do not impose Wiki language rules on original-language `text/`.
`check` needs Vale 3.23.0, Git and lychee; `index` and `prepare` need Node 22
or later.

Vale checks every English Wiki `.qmd` page except `log.qmd`, outside Cog regions and all
front matter. Its privacy and time rules inspect code and link targets. Its
language, school and date rules use Markdown text scope, which skips code,
link targets and front matter. A page rule reports the page, line and rule,
never the matched text.

Vale patterns flag phone numbers, email addresses, postal addresses,
registration numbers and dates not shaped as `YYYY-MM-DD`. Registration
numbers are not birth-date validated, and impossible dates in the fixed ISO
shape pass. Time patterns accept `Z`, numeric offsets and UTC forms; a range
with a zoned end is a pattern approximation. Phone and email detection uses
Vale regexes instead of the privacy gate's phone and email code.

Direct pages in `wiki/students/` must be named `s-<id>`, with `<id>` a value of
the roster's `id` column (the EduOK student number). No page may hold the
Korean spelling of a roster student, given or guardian name, in a quote, the
front matter or a mechanical region too; write the roster's romanized name.
That rule reads every line of every page except `log.qmd`. Other Hangul,
Chinese and Japanese text must be a short quote with an English
translation on the same line, using `"…"`, `“…”`, `‘…’`, `「…」` or
`『…』`. Vale approximates the quote length and translation form with patterns.
Roster school names in Hangul are flagged outside that quote form. Since Vale
skips front matter, page rules do not inspect title or summary text; metadata
shape checks still apply. The instance's `AGENTS.md` lists rules that stay
with the judgment step.

## Retained evidence and metadata

Folder `_metadata.yml` defaults merge in the checker from root to page, then
page front matter, without per-page `quarto inspect`. Mappings merge recursively;
arrays combine uniquely in order, empty/null array overrides inherit, scalar/list
pairs combine and ordinary page scalars override. Preserve meaningful overrides,
including `profile.checker: none`. `read_metadata(instance, document,
named_defaults=...)` returns the full mapping and problems for a literal
Wiki-relative `.qmd` path; `metadata_sources` lists safe ordered ancestors without
content reads. The single Cog catalog uses `wiki/**/*.qmd` and names each actual
existing metadata input it consumes as a literal argument, never an absent glob.

`evidence.convert` keeps its positional arguments and retains the full returned
original-language output in `text/<source-id>/<revision>.qmd`. Existing text is
reused without replacement. `evidence.read(instance, source_id, revision,
review=...)` reads its body and provenance without conversion. Unknown converter
or review facts remain explicit, and partial output stays partial.
PDF extraction uses the existing `pdftotext -raw` content-stream order and
records the actual backend version; `pdftotext` must be on `PATH`. A missing
or failed backend is unreadable, and backend warnings mark output partial.
Other formats keep the existing MarkItDown/JSON/python-hwpx routes.
`conversion-status: extracted` records backend output only, not completeness or
review. A true `checked-against-original` requires actual caller review with raw
`sha256`, full-file `extraction-sha256` and a nonempty `evidence` reference;
corrections invalidate earlier evidence. Do not invent review receipts.
For retained text marked reviewed, pass the real receipts to `prepare` with
`--review-receipts <path>`. This optional JSON file maps canonical
`source-id/revision` keys to objects with `sha256`, `extraction-sha256` and
`evidence`; the API accepts the same mapping as `reviews=...`. Missing or stale
receipts leave true review status unresolved. Receipts do not promote unchecked
text to reviewed or replace the bags as the source registry.

Each supported knowledge sentence ends with a bag-derived canonical citation
`[@source-id/revision, p. 25]`, using a declared exact revision and `p.`, `pp.` or
`sec.` locator. `read_located(..., locator, max_chars=..., review=...)` selects only
that span. Supported markers are page/section headings and page fenced divs;
missing boundaries cannot be inferred from PDF formfeeds. Arbitrary inline
markers, section divs and lone-CR mappings remain unresolved. No whole-source,
latest-revision or search fallback is allowed. Full retained bodies remain locally
readable when an exact judgment fails. Native Pandoc parsing uses restricted
literal alignment of plain paragraphs and simple list items; pySBD proposes
candidate sentence spans, with exact slice and citation-coverage checks.
Unsupported or ambiguous formatting, headings, tables, callouts, quotes and
source maps, or lost text/citation coverage, are explicit unresolved failures,
never skipped into a zero-request success or called sentence-complete.
Keep source inert without executable cells, executable inline code, heavy
includes or shortcodes.

`prepare` records each unit's `outcome` as `requested` or `unverifiable`, with
unit/source IDs and reasons in `unverifiable`. Missing inline citations and
unchecked original-review status are operational limits, not reasons to invent
citations, receipts or a new conversion/judgment batch. Claim counts/characters,
item and decision limits, and the caller's evidence budget are separate from
complete serialized tool-argument character/byte measurements. None establishes
a whole-body cap or the provider's unknown HTTP/token expansion limits.

`evidence.bibliography(instance, revisions, budget_bytes=..., env=...)` yields
fresh private cache `sources.json` only within its context, cleaning it on
success, failure and catchable interruption. CSL entries use `id: source-id/revision`,
`type: document`, the BagIt payload filename as `title`, and custom provenance;
no invented author/date, sender or absolute paths. Earlier output is not new-run
authority. No bibliography belongs in wiki Git. F2 supplies renderer source and
audience selection and owns Korean site tags, freshness and publishing; there is
no `ko/` tree. Main's publication and student decisions remain undecided.
`prepare` derives only its selected revisions; index and search do not build
an unused whole-wiki bibliography.

## After an operation that changed the Wiki

1. Run `update`, then `check`. Fix every failure `check` names; it gives page
   and line.
2. Reuse retained text; run `convert` only for selected, authorized revisions.
   New real conversion and student-bearing decisions remain held with main.
   Run `index` and `prepare --scope changed`, supplying real review receipts
   where required. On exit 1 with stdout JSON, read and report `unverifiable`
   reasons before sending any request; a zero call count does not establish
   success. Read `calls`:
   it counts the requests per Jev tool. If `prepare`'s
   `search.not_searched` is not empty, semantic search was not ready: tell
   the user that other pages and cross-references were not searched. The
   cause is a missing embedding model (`index` downloads it once) or
   documents qmd has not embedded yet; when `index` gave a `semantic_error`,
   pass it on as it is. Report any `partial` revisions from `convert` with
   their warning details.
3. Send each request's `arguments` to its named tool on the only registered
   server, `jev-mcp`, following the upstream `jev` skill and work privacy rules.
   Its gate always swaps registered person and school spellings, phone numbers,
   e-mail addresses, EduOK student numbers and resident numbers for fresh
   per-call stand-ins, then restores result text. Korean text is allowed;
   translation is not required by the server. School years, regions, addresses
   and observations remain unchanged unless they match registered spellings or
   covered patterns. Unregistered names/schools remain a known risk: a passing
   gate does not establish safe disclosure. Never send credentials to Jev.
4. For a `pages` request whose result is `contradicted`, call
   `jev_compare` with the two units' texts. Report every confirmed
   contradiction between pages to the user.
5. Fix `evidence` units that come back `contradicted` or `review`, or tell the
   user why they stand. Report every unit listed as `unverifiable`, with its
   cause: for example, its cited sources were unreadable (such as scanned PDF
   files), retained provenance or exact citation markers were missing, the
   cited span was partial or exceeded `--max-evidence-chars`, or an
   `overview.qmd` unit has no linked page to check against.
6. Treat `crossref` and `classify` results as suggestions. Accept or reject
   each one; none is final.
7. Run `check` again, append one entry to `wiki/log.qmd` in the form
   `## [YYYY-MM-DD] <operation> | <detail>` with counts of changed pages and
   findings, and commit the instance.

If `jev-mcp` is not configured or cannot be reached, stop after step 2 and
tell the user that the judgment step did not run. Do not report the
operation as checked.

## Lint

When the user asks for a lint, run the same steps with `--scope lint`. Also
handle the `crossref` suggestions and the `orphans` and `stale_citations`
that `check` lists: link or merge an orphan page, and update a stale citation
after the page is correct against the newer revision.

## Report to the user

Give counts and page paths only: failures fixed, units corrected,
contradictions between pages, unverifiable units, suggestions accepted and
rejected, and the `log.qmd` entry. Keep raw contents, private paths and
personal data out of code repositories and Orca or Linear messages.
