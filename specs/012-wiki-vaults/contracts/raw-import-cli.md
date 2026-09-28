# Contract change: `raw_import.py`

Feature 009's [contract](../../009-wiki-storage/contracts/raw-import-cli.md)
holds, with two changes:

- `--wiki <name>` selects `DATA/vaults/<name>/`, and the run lock is
  `STATE/vaults/<name>/raw-import.lock`. Staging stays at
  `CACHE/raw-import/<name>/`. Name validation is unchanged.
- Without `--wiki`, every command uses `work`.

The script neither reads nor creates anything under a `wikis/` folder, and it
does not inspect file contents, so an exported conversation is admitted into
any vault the agent names; the skill's procedure keeps conversation records
out of every vault except `chat`.

## Guarantees checked by tests

Feature 009's guarantees, on the new paths, plus:

- `init`, `admit` and `verify` without `--wiki` use `DATA/vaults/work/` and
  `STATE/vaults/work/`, and nothing named `wikis` appears under any root.
- A synthetic exported conversation admitted with `--wiki chat` becomes one
  revision, and `verify --wiki chat` reports it valid.
