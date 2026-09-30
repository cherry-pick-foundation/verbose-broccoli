---
name: wiki-consistency
description: Keep a verbose-broccoli Wiki instance's pages consistent with their raw evidence and with each other. Use after changing Wiki pages or admitting raw revisions, before committing the instance, and when the user asks for a lint of the Wiki; not for admitting raw documents or for writing pages from them.
---

# Wiki Consistency

A Wiki page is made of mechanical regions, which a generator rebuilds from
named files, and agent-written text, which backfire judges against the raw
evidence the page cites. Agent-written text is in English, apart from short
direct quotes kept next to their translation. Student names use the
roster's romanized spelling so that step 3 can replace them, the Korean
spelling stays only in the roster, and schools are written as their domain
IDs. The instance's `AGENTS.md` states these rules, the page
metadata, the special pages and these steps.

`DATA` and `CACHE` below are the `verbose-broccoli` folders under the XDG data
and cache roots (by default `~/.local/share` and `~/.cache`). The Wiki lives
in vaults, `DATA/vaults/<name>/`; this skill uses the `work` vault unless the
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
uv sync --project ../../../../packages/backfire --frozen --no-dev --extra education
uv sync --project ../../../../packages/wiki-consistency --frozen --no-dev
npm ci --ignore-scripts --no-audit --no-fund --prefix ../../../../packages/wiki-consistency
```

The first two lines give `doc-regions` and `backfire`, which the tool uses
as libraries, the `.venv/` their builds need. `check` uses local Vale 3.23.0
regex rules for page text; it reads backfire's roster only when a direct student
page or Hangul, Chinese or Japanese text needs roster checks.

| Command | What it does | Network | Writes |
| --- | --- | --- | --- |
| `check` | Checks mechanical regions, links, page metadata, the topics declared in `AGENTS.md`, cited bags, that `log.md` only grew, and the Vale page rules below; lists orphan pages and stale citations | none | nothing |
| `update` | Regenerates stale mechanical regions | none | region text in `wiki/` |
| `convert [--scope changed\|lint]` | Converts cited raw revisions to Markdown | none | `CACHE/wiki-evidence/` |
| `index` | Builds the local search index | the embedding model's one-time download | `CACHE/qmd/` |
| `prepare --scope changed\|lint` | Prints ready-to-send backfire requests | none | nothing |

On success a command prints one JSON object and exits 0. A failed check or an
execution failure exits 1 and invalid arguments exit 2; both print their
details on stderr only.
`check` needs Vale 3.23.0, Git and lychee; `index` and `prepare` need Node 22
or later.

Vale checks every Markdown page except `log.md`, outside Cog regions and all
front matter. Its privacy and time rules inspect code and link targets. Its
language, school and date rules use Markdown text scope, which skips code,
link targets and front matter. A page rule reports the page, line and rule,
never the matched text.

Vale patterns flag phone numbers, email addresses, postal addresses,
registration numbers and dates not shaped as `YYYY-MM-DD`. Registration
numbers are not birth-date validated, and impossible dates in the fixed ISO
shape pass. Time patterns accept `Z`, numeric offsets and UTC forms; a range
with a zoned end is a pattern approximation. Phone and email detection uses
Vale regexes instead of backfire's phone and email code.

Direct pages in `wiki/students/` must be named `s-<id>`, with `<id>` a value of
the roster's `id` column (the EduOK student number). No page may hold the
Korean spelling of a roster student, given or guardian name, in a quote, the
front matter or a mechanical region too; write the roster's romanized name.
That rule reads every line of every page except `log.md`. Other Hangul,
Chinese and Japanese text must be a short quote with an English
translation on the same line, using `"…"`, `“…”`, `‘…’`, `「…」` or
`『…』`. Vale approximates the quote length and translation form with patterns.
Roster school names in Hangul are flagged outside that quote form. Since Vale
skips front matter, page rules do not inspect title or summary text; metadata
shape checks still apply. The instance's `AGENTS.md` lists rules that stay
with the judgment step.

## After an operation that changed the Wiki

1. Run `update`, then `check`. Fix every failure `check` names; it gives page
   and line.
2. Run `convert`, `index` and `prepare --scope changed`. Read `calls` first:
   it counts the requests per backfire tool. If `prepare`'s
   `search.not_searched` is not empty, semantic search was not ready: tell
   the user that other pages and cross-references were not searched. The
   cause is a missing embedding model (`index` downloads it once) or
   documents qmd has not embedded yet; when `index` gave a `semantic_error`,
   pass it on as it is. Report any `partial` revisions from `convert` with
   their warning details.
3. Translate any Korean text in each request's `arguments`, such as a quoted
   passage of the evidence, into English yourself, in your own session, and
   keep the structure and IDs as they are. Then send the `arguments` to the
   backfire tool the request names, on the **work plugin's** backfire server.
   Before the provider sees them, its judge replaces the identifiers it
   detects (names and numbers from the operator's roster, schools, regions,
   school years, birth dates, addresses, phone numbers and email addresses)
   with English stand-ins and refuses a request that still contains Hangul
   (`hangul_remaining`); all other text is sent as it is. In Claude Code its
   tools include `mcp__plugin_work_backfire__jev_verify`. Never use the code
   plugin's server for Wiki text.
4. For a `pages` request whose result is `contradicted`, call
   `jev_compare` with the two units' texts. Report every confirmed
   contradiction between pages to the user.
5. Fix `evidence` units that come back `contradicted` or `review`, or tell the
   user why they stand. Report every unit listed as `unverifiable`, with its
   cause: for example, its cited sources were unreadable (such as scanned PDF
   files), no passage of a long source matched it within
   `--max-evidence-chars`, or an `overview.md` unit has no linked page to
   check against.
6. Treat `crossref` and `classify` results as suggestions. Accept or reject
   each one; none is final.
7. Run `check` again, append one entry to `wiki/log.md` in the form
   `## [YYYY-MM-DD] <operation> | <detail>` with counts of changed pages and
   findings, and commit the instance.

If backfire is not configured or cannot be reached, stop after step 2 and
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
rejected, and the `log.md` entry. Keep raw contents, private paths and
personal data out of code repositories and Orca or Linear messages.
