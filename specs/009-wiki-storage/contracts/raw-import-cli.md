# Contract: `raw_import.py`

The script lives at `plugins/work/skills/wiki-raw-import/scripts/raw_import.py`
and always runs as:

```sh
uv run --locked --script plugins/work/skills/wiki-raw-import/scripts/raw_import.py <command> [options]
```

It reads `XDG_DATA_HOME`, `XDG_STATE_HOME`, `XDG_CACHE_HOME` and
`XDG_CONFIG_HOME` (unset or empty means the default under `HOME`), so tests point every root at a
temporary folder. Names in this contract refer to
[data-model.md](../data-model.md).

## Commands

| Command | Effect |
| --- | --- |
| `init` | Create the default instance's missing folders and files; change nothing that exists. |
| `admit --selection <file>` | Validate the selection, then admit each item in order. |
| `verify` | Validate every revision under `raw/`; write nothing. |

`--wiki <name>` selects `wikis/<name>/` and defaults to `default`.

## Exit status and output

| Case | Exit | stdout | stderr |
| --- | --- | --- | --- |
| `init` done | 0 | One JSON object listing created paths | Empty |
| `admit`: every item admitted or already admitted | 0 | Report (JSON Lines) | Empty |
| `admit`: at least one item refused or failed | 1 | Report (JSON Lines) | One line naming the counts |
| `verify`: every revision valid | 0 | JSON object with the count | Empty |
| `verify`: at least one invalid revision | 1 | JSON object listing each invalid revision and its reason | One line naming the count |
| Invalid arguments or selection, missing instance, lock held | 2 | Empty | Error message; nothing written |

Upstream warnings (for example bagit's `DeprecationWarning` on Python 3.14)
are suppressed so stderr carries only this contract's messages.

## `admit` item rules, in order

1. Resolve the path. Refuse when it is not a regular file, lies under an
   excluded location, or its name is not valid UTF-8.
2. Read the original's digest and modification time.
3. Find the source by original path. If its latest revision has the same
   digest, report `already_admitted`.
4. Copy into staging with its modification time, make the bag, and validate
   it.
5. Read the original's digest again; if it differs from step 2, fail the item.
6. Rename the bag into `raw/<kind>/<source-id>/<revision>/` and make it
   read-only; report `admitted`.

Any error in steps 2 to 6 fails the item, removes its staging folder and
continues with the next item. The original is only read.

## Guarantees checked by tests

- Originals: bytes and modification time unchanged in every case.
- `raw/`: only complete, valid revisions, after success, refusal, failure and
  interruption at each step.
- Rerun: an unchanged selection adds nothing; one changed original adds one
  revision to its source.
- Lock: a second concurrent `admit` exits 2 and writes nothing; a lock left by
  a killed process does not block the next run.
- `verify` reports a changed payload byte and a changed `bag-info.txt`.
