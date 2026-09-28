---
name: wiki-consistency
description: Keep a verbose-broccoli Wiki instance's pages consistent with their raw evidence and with each other. Use after changing Wiki pages or admitting raw revisions, before committing the instance, and when the user asks for a lint of the Wiki; not for admitting raw documents or for writing pages from them.
---

# Wiki Consistency

A Wiki page is made of mechanical regions, which a generator rebuilds from
named files, and agent-written text, which backfire judges against the raw
evidence the page cites. The instance's `AGENTS.md` states the page metadata,
the special pages and these steps.

`DATA` and `CACHE` below are the `verbose-broccoli` folders under the XDG data
and cache roots (by default `~/.local/share` and `~/.cache`). The default
instance is `DATA/wikis/default/`.

## Commands

Run them from this skill's folder. The tool is the `wiki-consistency` project
at the work plugin's root:

```sh
uv run --project ../../wiki-consistency --frozen --offline --no-sync wiki-consistency <command> [--wiki <name>]
```

Install it once after the plugin is installed or updated:

```sh
uv sync --project ../../doc-regions --frozen --no-dev
uv sync --project ../../wiki-consistency --frozen --no-dev
npm ci --ignore-scripts --no-audit --no-fund --prefix ../../wiki-consistency
```

The first line gives `doc-regions`, which the tool uses as a library, the
`.venv/` its build needs.

| Command | What it does | Network | Writes |
| --- | --- | --- | --- |
| `check` | Checks mechanical regions, links, page metadata, cited bags and that `log.md` only grew; lists orphan pages and stale citations | none | nothing |
| `update` | Regenerates stale mechanical regions | none | region text in `wiki/` |
| `convert [--scope changed\|lint]` | Converts cited raw revisions to Markdown | none | `CACHE/wiki-evidence/` |
| `index` | Builds the local search index | the embedding model's one-time download | `CACHE/qmd/` |
| `prepare --scope changed\|lint` | Prints ready-to-send backfire requests | none | nothing |

On success a command prints one JSON object and exits 0. A failed check or an
execution failure exits 1 and invalid arguments exit 2; both print their
details on stderr only.
`check` needs Git and lychee; `index` and `prepare` need Node 22 or later.

## After an operation that changed the Wiki

1. Run `update`, then `check`. Fix every failure `check` names; it gives page
   and line.
2. Run `convert`, `index` and `prepare --scope changed`. Read `calls` first:
   it counts the requests per backfire tool.
3. Send each request's `arguments` to the backfire tool it names, on the
   **work plugin's** backfire server. Before the provider sees them, its judge
   replaces the student, guardian and school names in the operator's roster,
   phone numbers and email addresses; every other identifier and all other
   text are sent as they are. In Claude Code its tools are
   named `mcp__plugin_work_backfire__<tool>`. Never use the code plugin's
   server for Wiki text.
4. For a `pages` request whose result is `contradicted`, call
   `backfire_compare` with the two units' texts. Report every confirmed
   contradiction between pages to the user.
5. Fix `evidence` units that come back `contradicted` or `review`, or tell the
   user why they stand. Report the units listed as `unverifiable`: all their
   cited sources were unreadable (for example HWP or scanned PDF files), or
   no passage of a long source matched them within `--max-evidence-chars`.
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
