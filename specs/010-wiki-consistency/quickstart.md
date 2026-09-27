# Quickstart: Validating Wiki Document Consistency

Run from the feature worktree's root after implementation, with Deno on
`PATH`, lychee 0.24.2 and Node 22 or later installed, and Orca's setup having
run `uv sync --locked --project packages/wiki-consistency` and
`npm ci --ignore-scripts --prefix packages/wiki-consistency`. Every manual
step below uses a temporary instance: set `XDG_DATA_HOME`, `XDG_CACHE_HOME`,
`XDG_STATE_HOME` and `XDG_CONFIG_HOME` to folders under a scratch directory,
and never point them at the user's real roots.

`WC` below stands for `uv run --project packages/wiki-consistency --frozen
--offline --no-sync wiki-consistency`.

## Automated checks

```sh
deno task doctor                 # package environment and locks
deno task test:wiki-consistency  # package tests on synthetic instances
deno task verify                 # everything, with recorded evidence
```

Expected: all pass, and `git status --short` is empty afterwards.

## Offline check (User Story 1)

1. Create a synthetic instance with feature 009's `init`, admit two synthetic
   files, write two pages citing them ([contracts/pages.md](contracts/pages.md)),
   run `WC update`, `WC check`, and commit the instance.
2. Admit a changed copy of one file (a new revision). `WC check` fails on the
   stale `source_provenance` region and names `update`; no file changed.
3. `WC update`; a second `WC update` changes nothing; `WC check` passes and
   lists the older citation under `stale_citations`.
4. Change the first line of `wiki/log.md`; `WC check` fails and names it.

## Judgment step (User Stories 2 and 3)

1. Write a paragraph that contradicts its cited synthetic source, and a
   second page that contradicts the first page.
2. `WC convert`, `WC index`, `WC prepare --scope changed`: the paragraph is a
   claim of an `evidence` request with the source's converted text, and the
   two pages meet in a `pages` request; `calls` counts the requests.
3. Send them through the agent's MCP client; both come back `contradicted` or
   `review`, and `backfire_compare` confirms the page pair (SC-005: in each of
   three runs).
4. Add an image-only PDF source and cite only it from a new page: `WC convert`
   lists it as unreadable, and `WC prepare` lists the page's units as
   `unverifiable`.
5. `WC prepare --scope lint` also prints `crossref` requests proposing the
   related unlinked page.

## Build (User Story 5)

Build the work plugin into a scratch folder outside the repository, run
`uv sync --frozen --no-dev` and `npm ci --ignore-scripts` in its copied
`wiki-consistency/` folder, and run `check` from there against the synthetic
instance without the code plugin present.
