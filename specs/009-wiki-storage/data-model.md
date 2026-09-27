# Data Model: Wiki Storage and Raw Documents

All data lives outside the repository, under the XDG roots of the user who runs
the import. `DATA`, `STATE`, `CACHE` and `CONFIG` stand for
`$XDG_DATA_HOME/verbose-broccoli` (default `~/.local/share/verbose-broccoli`),
`$XDG_STATE_HOME/verbose-broccoli`, `$XDG_CACHE_HOME/verbose-broccoli` and
`$XDG_CONFIG_HOME/verbose-broccoli`.

## Wiki instance

```text
DATA/wikis/default/
├── AGENTS.md          # schema: raw admission and provenance rules only
├── .gitignore         # ignores raw/
├── .git/              # history of AGENTS.md and wiki/
├── raw/
│   ├── web/
│   ├── files/
│   ├── notes/
│   └── assets/
└── wiki/
    ├── index.md       # empty catalog
    ├── overview.md    # empty synthesis
    └── log.md         # append-only; one entry per import
```

The layers beside `raw/` follow the clarification in [spec.md](spec.md).
`init` creates what is missing and never changes what exists. No Wiki page is
created.

## Source and source revision

```text
DATA/wikis/default/raw/<kind>/<source-id>/<revision>/
├── bagit.txt
├── bag-info.txt
├── manifest-sha256.txt
├── tagmanifest-sha256.txt
└── data/<original file name>
```

| Field | Where | Rule |
| --- | --- | --- |
| kind | folder `raw/<kind>/` | one of `web`, `files`, `notes`, `assets`, from the selection |
| source ID | folder name and `External-Identifier` | UUID version 7, assigned at first admission; equal in every revision of the source |
| revision | folder name and `Admission-Time` | UTC time `YYYYMMDDTHHMMSSffffffZ`; revisions sort by it |
| original path | `Internal-Sender-Identifier` | absolute path of the original after resolving symbolic links, exact bytes of the name |
| original modification time | `Source-Modified` | ISO 8601 with offset, read before copying |
| admission date | `Bagging-Date` | written by bagit |
| SHA-256 digest | `manifest-sha256.txt` | digest of `data/<name>` |
| size | `Payload-Oxum` | written by bagit |

Rules:

- One source revision is one valid bag with exactly one payload file.
- All fields of a source's revisions except the revision, digest, size,
  modification time and admission date are equal.
- The bag is read-only after publication and is never edited or removed by
  the capability.
- The latest revision of a source is the one whose revision name sorts last.
- A source is found for an original path by reading
  `raw/*/*/*/bag-info.txt` and matching `Internal-Sender-Identifier`. Two
  sources with the same original path are an error that stops that item.

State transitions for one selected original:

```text
not admitted ──admit──▶ source with revision r1
revision rN, same digest ──admit──▶ unchanged (already admitted)
revision rN, new digest  ──admit──▶ revision rN+1 added; rN kept
```

## Selection

A JSON Lines file outside the repository, written by the agent from the
user-approved list, at `STATE/wikis/default/selections/<name>.jsonl`. It is
kept until the import of that list passes `verify`, then removed; the bags
hold the lasting provenance. One object per line:

| Field | Rule |
| --- | --- |
| `path` | absolute path of a regular file |
| `kind` | `web`, `files`, `notes` or `assets` |

Duplicate paths, relative paths, unknown fields and unknown kinds make the
whole selection invalid before anything is copied.

## Configuration

`CONFIG/config.toml`:

```toml
[wiki.raw_import]
exclude = ["/absolute/path", "..."]
```

A missing file or table means no user exclusions. The data, state and cache
roots are always excluded. A file that does not parse, a table or `exclude`
of the wrong type, or an entry that is not an absolute path string stops the
command with exit 2 before anything is written.

## Run state

| Item | Location | Lifetime |
| --- | --- | --- |
| lock | `STATE/wikis/default/raw-import.lock` | kept; held with `flock` during a run |
| staging | `CACHE/raw-import/<wiki>/<run-id>/` | removed at the end of the run and at the start of the next run of the same Wiki, only while that Wiki's lock is held |

## Import report

JSON Lines on standard output, one object per selected item with all of
`path`, `outcome`, `source_id`, `revision` and `reason` (null where not
applicable), then one line `{"summary": {"admitted": n,
"already_admitted": n, "refused": n, "failed": n}}`. Outcomes: `admitted`, `already_admitted`, `refused`,
`failed`. The agent keeps the report outside the repository; the repository
gets counts only.
