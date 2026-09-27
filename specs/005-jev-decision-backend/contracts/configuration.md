# Configuration and Storage Contract

All paths use the `verbose-broccoli` XDG namespace. When an XDG variable is
unset, its default applies: `~/.config`, `~/.local/state`, `~/.cache` and
`~/.local/share`.

## Operator files (config)

| Path | Content | Rules |
| --- | --- | --- |
| `$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml` | `provider = "<name>"` and optional `[providers.<name>]` tables | Optional; its `provider` replaces the shipped selection (`hive`), and its tables add or replace shipped provider tables whole ([provider-profile.md](provider-profile.md#location-and-selection)). |
| `$XDG_CONFIG_HOME/verbose-broccoli/backfire/<name>.env` | `<credential>=<key>`, with the selected profile's credential name (for `hive`: `hive.env` with `HIVE_API_KEY=<key>`) | Mode exactly 0600 and owned by the operator. A missing or empty file, any group or other permission bit, or another owner fails each judgment with `backend_not_configured`, whose message names the path. |

There are no other settings. The files live in neither the repository nor the
plugin package. The credential is read by the judge only, for each judgment;
it never appears in environment variables, logs, records, reports
or error messages.

## Written state

| Path | Content | Budget |
| --- | --- | --- |
| `$XDG_STATE_HOME/verbose-broccoli/backfire/records/` | Tool-call and judgment records, JSON Lines, one locked file per session written by the server, and the `.lock` file | At most 50 MiB in total, checked under `.lock` before every append; the oldest unlocked files are deleted to make room, and a record that still does not fit fails its request. A session's file rotates at 10 MiB. |

Rules for writing, locking, interrupted writes and write failures are in
[data-model.md](../data-model.md#record-files).

## Rebuildable cache

| Path | Content |
| --- | --- |
| `$XDG_CACHE_HOME/verbose-broccoli/backfire/eval/` | Downloaded JevBench file, verified by SHA-256, and the working directory of a running evaluation; at most 256 MiB in total, checked before each write; the working directory is removed when the run ends, fails or is interrupted |

Deleting the cache never removes state or configuration.

## Component environment

Each component copy's Python environment is `.venv/` in its own directory
(`packages/backfire/` or `<plugin root>/backfire/`), made only by the install
command ([mcp-server.md](mcp-server.md#entry-commands)) from `uv.lock`. uv
keeps its downloads in its own cache. Deleting `.venv/` requires rerunning the
install command.

## Evaluation data

| Path | Content |
| --- | --- |
| `$XDG_DATA_HOME/verbose-broccoli/backfire-eval/heldout-v1.jsonl` | The sealed held-out set, written once before implementation and read only by final acceptance |

## Never written

Request content, tool results or caller-supplied identifiers anywhere the
feature writes; credentials and authentication headers anywhere; any file
inside the repository or the installed plugin package at runtime, with two
exceptions: uv writes only the copy's `.venv/`, which the install command
fills and a start before installing leaves empty
([mcp-server.md](mcp-server.md#entry-commands)), and Python writes its
disposable bytecode caches, `__pycache__/`, beside the copy's source modules
when the directory is writable. The one
repository file the feature writes is the final acceptance record, written only
by the evaluation command ([evaluation.md](evaluation.md#run-protocol)).
