# Quickstart: Topics in Vault Page Metadata

## Prerequisites

- The `wiki-consistency` and `doc-regions` environments:
  `deno task wiki-consistency:install`.
- lychee and Git on `PATH` (`deno task doctor` checks both).

## Repository checks

```sh
deno task test:wiki-consistency
deno task test:wiki-raw-import
deno task verify
```

Expected: all pass. The wiki-consistency tests cover, with synthetic vaults:

- a grouped index with several topics and a page under two of them (US1);
- identical output from two regenerations and a stale index after a topic
  change (US1);
- each invalid page and schema case in [data-model.md](data-model.md),
  failing with the page or `AGENTS.md` named, and `update` leaving every
  file unchanged (US2);
- an empty vault and a declared topic without pages passing (edge cases).

## Vault adoption (after the merge)

For each of `default`, `chat` and `code`, with the develop worktree's tool:

```sh
uv run --project packages/wiki-consistency --frozen --offline --no-sync \
  wiki-consistency update --wiki <name>
uv run --project packages/wiki-consistency --frozen --offline --no-sync \
  wiki-consistency check --wiki <name>
git -C ~/.local/share/verbose-broccoli/vaults/<name> show --stat HEAD
```

Expected: `check` prints a JSON object with no problems; the last commit
changes `AGENTS.md` (front matter and page rules only) and appends one
`wiki/log.md` entry. The `work` vault is not touched.
