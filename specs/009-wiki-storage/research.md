# Research: Wiki Storage and Raw Documents

Probes ran on 2026-09-27 on the development machine (Linux x86_64, uv 0.11.32,
Python 3.14.6 through uv, GNU coreutils 9.7), in scratch folders outside the
checkout and with synthetic files only. The survey of candidate locations read
folder sizes, file counts and file types; it opened no file and did not enter
`~/projects/work/students`.

## R1. Recording provenance

- **Decision**: Record each source revision as one BagIt bag (RFC 8493),
  created and validated with bagit-python 1.9.0 (Library of Congress, public
  domain, released 2025-06-13). The bag holds the copy under `data/`, a SHA-256
  payload manifest, a tag manifest, and `bag-info.txt` with the provenance
  fields (see [data-model.md](data-model.md)).
- **Rationale**:
  - BagIt is the standard packaging format for transferring files with fixity
    information, and bagit-python both writes bags and validates them. The
    SHA-256 digest the brief asks for is the bag's payload manifest, and
    validation recomputes it, so the integrity check (FR-007) is upstream code.
  - `bag-info.txt` has standard fields that fit: `External-Identifier` for the
    stable source ID, `Internal-Sender-Identifier` for the original path, and
    `Bagging-Date` for the admission date. Other fields are allowed by the
    standard; the original's modification time and the exact admission time go
    in two such fields. The tag manifest covers `bag-info.txt`, so a changed
    record fails validation too.
  - Probe: a bag made from a synthetic file with the Python API
    `bagit.make_bag(dir, bag_info=..., checksums=["sha256"])` validated; after
    one byte was appended to the copy, validation failed with a Payload-Oxum
    error. A file name with Korean text, spaces and a leading dash was kept
    exactly in the manifest. Copying with `shutil.copy2` or `cp
    --preserve=timestamps` kept the original's modification time on the copy.
    Python 3.14 prints `DeprecationWarning`s from bagit's use of
    `codecs.open`; they do not change results.
  - The bag inside `raw/` is the only provenance record. Revisions of a source
    are found by reading the `bag-info.txt` files under `raw/`, so there is no
    second list that could disagree with them (constitution VI forbids
    parallel registries; FR-009).
- **Alternatives considered**:
  - `sha256sum` files plus a hand-written descriptor: the digest check is
    upstream (`sha256sum -c`), but the descriptor format, its own integrity and
    its reader would be local code that BagIt already defines.
  - A central manifest (one JSON or database file listing every source): a
    parallel registry that can drift from `raw/`; rejected by principle VI.
  - git-annex or DVC: content-addressed storage with metadata in Git. Neither
    is installed, both add a second version-control system, and keeping their
    metadata out of the Wiki's Git history needs a separate repository; far
    more than the need.
  - bdbag 1.8.0 (BagIt with remote-file extensions): adds features this
    feature does not use.

## R2. Where the capability lives and how its dependency is pinned

- **Decision**: A work-plugin skill, `plugins/work/skills/wiki-raw-import/`,
  holds the agent procedure (`SKILL.md`: survey, confirmation, selection,
  import, check) and one small Python glue script,
  `scripts/raw_import.py`, with inline script metadata (PEP 723) that requires
  `bagit==1.9.0` and Python 3.14. `uv lock --script` writes
  `scripts/raw_import.py.lock` next to it, and every run uses `uv run --locked
  --script`, so resolution and hashes are pinned.
- **Rationale**:
  - Constitution IX puts business capabilities in the work package, and the
    brief `briefs/2026-09-27-linear-and-documents.md` (section 3) says Wiki
    tooling runs as part of the work plugin. A skill folder with its script and
    lock is self-contained when a client copies the plugin.
  - Probe: `uv lock --script` resolved one package; `uv run --locked --script`
    installed it and ran on Python 3.14.6. `uv sync --script` exists, so Orca's
    setup can prepare the environment ahead of offline test runs, as it does
    for `tools/spec-kit`.
  - The glue is limited to what no upstream tool does for this layout: reading
    the approved selection, refusing excluded paths, checking the original's
    digest before and after copying, choosing the source ID and revision name,
    staging, publishing by rename, and the single-run lock. Copying
    (`shutil.copy2`), hashing (`hashlib`), bag writing and validation
    (bagit), TOML parsing (`tomllib`), locking (`fcntl.flock`) and IDs
    (`uuid.uuid7`) are standard library or upstream.
- **Alternatives considered**:
  - A documented procedure only, with the agent typing `cp`, `sha256sum` and
    `bagit.py` per file: hundreds of files make per-item typing error-prone,
    and principles II and V require tested recovery behavior, which needs a
    runnable unit.
  - `uvx --from bagit==1.9.0 bagit.py`: pins the version but not hashes, and
    the command line cannot add the custom provenance fields.
  - A package under `packages/`: there is no second consumer yet; a package
    can be split out when feature 010 or an ingest feature needs the same code.
  - A script under `scripts/`: that folder is for repository automation, and
    this capability acts on the user's data, not on the repository.

## R3. Publication, interruption and concurrency

- **Decision**: For each item, copy the original into a staging folder under
  `$XDG_CACHE_HOME/verbose-broccoli/raw-import/`, make and validate the bag
  there, check the original's digest again, then publish with one `rename`
  into `raw/<kind>/<source-id>/<revision>/`. The bag's files and subfolders
  are made read-only before the rename and the revision folder right after
  it. A run holds an exclusive `flock` on
  `$XDG_STATE_HOME/verbose-broccoli/wikis/default/raw-import.lock` and removes
  stale staging folders when it starts.
- **Rationale**:
  - `rename` within one file system is atomic, so `raw/` never shows a partial
    revision (FR-015). The home folder, the data root and the cache root are on
    one file system (`df` on 2026-09-27); if they are not, `rename` fails with
    `EXDEV` and the item fails with that reason instead of copying across file
    systems.
  - No progress file is needed: the digest comparison with the latest revision
    makes a rerun skip finished items (FR-008, FR-016). The state root holds
    only the lock file. Staging is temporary work, so it belongs in cache
    (constitution VI) and is removed at the end of every run and at the start
    of the next one.
  - The kernel releases a `flock` when its process dies, so a crashed run
    never blocks the next one.
  - Interruption tests can create the state each failure point leaves (a
    partial staged copy, a complete staged bag not yet renamed, a lock file
    from a dead process) and check that `raw/` is unaffected and a rerun
    completes; one test also kills a real run with `SIGKILL`.
- **Alternatives considered**: Writing directly into `raw/` and deleting on
  failure: a crash between write and delete leaves partial evidence, and
  deleting in `raw/` conflicts with its create-only rule.

## R4. Source identity and revisions

- **Decision**: A source is one original file. Its ID is a UUID version 7
  assigned at first admission and stored as `External-Identifier`. A revision
  folder is named by its admission time in UTC (`YYYYMMDDTHHMMSSffffffZ`), and
  the same time is recorded in the bag. An original path whose latest revision
  has a different digest gets a new revision in the same source; a path not
  seen before gets a new source.
- **Rationale**: Principle III forbids using search normalization as an
  identity key, and file names may hold private text or change. A UUID says
  nothing about content and sorts by creation time. The original path links a
  new revision to its source; directory names only mirror the recorded values,
  which are the evidence (principle VI).
- **Alternatives considered**: A slug of the file name (breaks on renames and
  non-Latin names, and copies private names into folder names); the content
  digest as source ID (two revisions of one document would become two
  sources).

## R5. Excluded locations

- **Decision**: The script refuses any selected path under the Wiki data root,
  the state and cache roots, or a path listed in the user's configuration
  `$XDG_CONFIG_HOME/verbose-broccoli/config.toml` under `[wiki.raw_import]
  exclude`. Paths are compared after resolving symbolic links. The
  implementation writes the user's exclusions there after the user confirms
  them; the repository holds no user paths.
- **Rationale**: Principle VI gives configuration to `config.toml`. Keeping
  user-specific paths out of plugin code keeps the plugin usable for any home
  folder, and the confirmation step decides the list.

## R6. Survey of the candidate locations

Read-only counts on 2026-09-27. Sizes are from `du`; types count file
extensions. No file was opened.

| Location | Size | Files | Main types | Finding |
| --- | --- | --- | --- | --- |
| `~/Documents/20_reference` | 63 MB | 78 | 47 docx, 16 md, 6 pdf, 4 hwp | One subfolder of vocabulary material (22 MB, 67 files); the rest are loose files |
| `~/Documents/10_midterm` | 619 MB | 189 | 105 pdf, 33 md, 10 py, 6 docx, 3 bat | Two school-level subfolders; mixed with scripts and Markdown conversions |
| `~/Documents/11_final` | 4 MB | 62 | 50 pdf, 9 md, 2 hwp | Two school-level subfolders |
| Loose files in `~/Documents` | 1.8 MB | 10 | 3 pdf, 1 docx, 2 md, 4 txt | |
| `~/projects/work/sources` | 26 MB | 60 | 41 json, 8 lock, 3 pdf, 2 hwp, 5 md | Eight entries, each one original (pdf, hwp or md) beside about five JSON files and a lock file written by an earlier tool; two entries look like operational references |
| `~/projects/work/materials` | 2.7 MB | 70 | 33 json, 20 docx, 8 md, 4 qmd | Three entries, mostly the user's own lesson materials and tool JSON |
| `~/projects/work/intake` | 1.6 GB | 5,820 | 1,113 txt, 1,004 py, 985 pyc, 679 java | Nine entries; one entry is 1.5 GB with 5,420 files of program code and extracted text, not documents |
| `~/projects/work/{concepts,decisions,stable,draft}` | 316 MB | 2,419 | json, md, qmd, svg | `stable` is empty |
| `~/Zotero` | 42 MB | 782 | 757 js, 15 csl | `storage/` is empty: the folder holds only Zotero's translators, styles and database, no attachments |
| `~/ownCloud` | 989 MB | 105 | 33 pdf, 36 png, 12 jpg | Mostly one shared-materials folder (984 MB); sync journals and logs belong to the client |
| `~/data` | 39 GB | not counted | | Legacy archives |

Findings that change the brief's assumptions:

- `~/Zotero` has no attachment files, so there is nothing to copy from it;
  its library database is Zotero's own data.
- `~/projects/work/sources`, `materials` and `intake` are not raw as whole
  folders. Their entries mix originals with JSON and lock files from an
  earlier tool, which constitution IV does not accept as evidence, and one
  intake entry is a 1.5 GB tree of program code. Selection must be per file.
- `~/Documents/10_midterm` also holds scripts and Markdown conversions, so
  its selection must separate original papers from the user's edits,
  conversions and tools.
- Locations not in the brief's table were found: `~/Documents/ChatGPT`
  (2.7 GB, 58,718 files) and `~/Documents/Codex` (686 MB, 5,752 files), which
  by their names hold conversation records or earlier projects;
  `~/Documents/var`, `~/Documents/Restore Firefox`,
  `~/Documents/verbose-broccoli-artifacts` (163 MB) and
  `~/projects/work/{datasets,rules,deprecated}`. They are out of scope unless
  the user adds them; tasks.md asks.
