---
name: wiki-consistency
description: Keep a verbose-broccoli Wiki instance's pages consistent with their raw evidence and with each other. Use after changing Wiki pages or admitting raw revisions, before committing the instance, and when the user asks for a lint of the Wiki; not for admitting raw documents or for writing pages from them.
---

# Wiki Consistency

A Wiki page is made of mechanical regions, which a generator rebuilds from
named files, and agent-written text, which backfire judges against the raw
evidence the page cites. Agent-written text is in English, apart from short
direct quotes kept next to their translation. Student names keep the
roster's spelling so that step 3 can replace them, and schools are written
as their domain IDs. The instance's `AGENTS.md` states these rules, the page
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
as libraries, the `.venv/` their builds need; `check` reads the roster and
finds names, phone numbers and email addresses with backfire's code.

| Command | What it does | Network | Writes |
| --- | --- | --- | --- |
| `check` | Checks mechanical regions, links, page metadata, the topics declared in `AGENTS.md`, cited bags, that `log.md` only grew, and the page rules a pattern can test (below); lists orphan pages and stale citations | none | nothing |
| `update` | Regenerates stale mechanical regions | none | region text in `wiki/` |
| `convert [--scope changed\|lint]` | Converts cited raw revisions to Markdown | none | `CACHE/wiki-evidence/` |
| `index` | Builds the local search index | the embedding model's one-time download | `CACHE/qmd/` |
| `prepare --scope changed\|lint` | Prints ready-to-send backfire requests | none | nothing |

On success a command prints one JSON object and exits 0. A failed check or an
execution failure exits 1 and invalid arguments exit 2; both print their
details on stderr only.
`check` needs Git and lychee; `index` and `prepare` need Node 22 or later.

The page rules that `check` tests, in every page except `log.md`, outside
mechanical regions and outside the front matter's `sources` field: no
phone numbers, email or postal addresses, or registration numbers; each
page directly in `wiki/students/` is named after a student in the roster;
no Hangul, Chinese or Japanese text except roster names and one quote of at
most 100 characters with its English translation on the same line, as
`"<original>" (<translation>)` or `"<translation>" ("<original>")`, with
`"…"`, `“…”`, `‘…’`, `「…」` or `『…』` as quotation marks; no roster school
name in Hangul outside such a quote; dates as YYYY-MM-DD
and times with `Z`, an offset from `-14:00` to `+14:00` (a minus offset
only in an ISO date-time), or a UTC form. The language, school and date
rules skip link targets outside code (link destinations, autolinks and
bare URLs), which a page cannot change without breaking the link. A failure names the page,
line and rule but not the matched text. `check` reads the roster through
backfire's `education.toml` only when a student page or such text exists;
it then fails if the file is missing. The instance's `AGENTS.md` lists the
rules that stay with the judgment step.

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
3. Send each request's `arguments` to the backfire tool it names, on the
   **work plugin's** backfire server. Before the provider sees them, its judge
   replaces the student, guardian and school names in the operator's roster,
   phone numbers and email addresses; every other identifier and all other
   text are sent as they are. In Claude Code its tools include
   `mcp__plugin_work_backfire__jev_verify`. Never use the code plugin's
   server for Wiki text.
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
