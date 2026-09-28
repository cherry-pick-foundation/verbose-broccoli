---

description: "Task list for Wiki storage and raw documents"
---

# Tasks: Wiki Storage and Raw Documents

**Input**: Design documents from `specs/009-wiki-storage/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. The root `AGENTS.md` asks for tests with every code
change, and constitution principles II and V require functional tests of
admission, refusal and recovery with synthetic fixtures.

**Organization**: Tasks are grouped by user story. Main (Claude Code) owns
shared files, repository prose, the confirmations with the user and every
write outside the repository; a Codex worker owns the script and its tests
(Worker Assignment below). `SCRIPT` is
`plugins/work/skills/wiki-raw-import/scripts/raw_import.py` and `TEST` is
`scripts/wiki_raw_import_test.ts`.

**Private data**: No task writes a user file name, file content or private
path into the repository or into Orca or Linear messages. Records give
locations from the brief's table, counts, sizes and folder-level judgments.
Nothing outside the repository is created, copied or changed before Phase 8,
and in Phase 8 only after the user's decision for that location.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US6)

---

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Add the task `test:wiki-raw-import` to `deno.json` (`deno test
  --frozen --cached-only --no-prompt --allow-read --allow-write --allow-env
  --allow-run TEST`) and add it to the `test` dependencies.
- [x] T002 [P] Add `"$uv_bin" sync --locked --script SCRIPT` to the setup
  script in `orca.yaml`, after the `tools/spec-kit` sync; check with `deno fmt
  --check orca.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The script runs, resolves its roots and can create the raw
folders every story's tests need.

- [x] T003 Create SCRIPT with the PEP 723 block (`requires-python =
  ">=3.14"`, `dependencies = ["bagit==1.9.0"]`), the `init`, `admit
  --selection <file>` and `verify` commands with `--wiki <name>` (default
  `default`), XDG root resolution where unset, empty or relative means the default under
  `HOME`, suppression of upstream warnings, and the exit and output rules of
  [contracts/raw-import-cli.md](contracts/raw-import-cli.md). `init` creates
  `raw/{web,files,notes,assets}/` and changes nothing that exists; `admit`
  and `verify` exit 2 when the instance is missing.
- [x] T004 Run `uv lock --script SCRIPT` to write
  `plugins/work/skills/wiki-raw-import/scripts/raw_import.py.lock`, then
  confirm `uv run --locked --offline --script SCRIPT --help` works (depends
  on T003).
- [x] T005 Create TEST's fixture helper: a temporary `HOME` with every XDG
  root inside it, a synthetic-file writer, a selection writer, a runner that
  calls `uv run --locked --offline --script SCRIPT` with that environment,
  and a snapshot of originals (bytes, modification time) and of `raw/`
  (paths, bytes, modes) for before-and-after comparisons.

**Checkpoint**: `deno task test:wiki-raw-import` runs (with no cases yet).

---

## Phase 3: User Story 1 - A confirmed document becomes raw evidence with its source recorded (Priority: P1) 🎯 MVP

**Goal**: Admit one original into a valid, read-only BagIt revision with its
provenance, leaving the original unchanged.

**Independent Test**: Admit one fixture file, compare bytes, read the record,
check the original, run `verify` (spec US1).

- [x] T006 [US1] Add TEST cases for spec US1 scenarios 1 to 4: one admitted
  revision under `raw/files/<uuid7>/<revision>/` whose payload bytes and
  `manifest-sha256.txt` digest match the original and whose `bag-info.txt`
  holds `External-Identifier`, `Internal-Sender-Identifier`,
  `Source-Modified`, `Admission-Time` and `Bagging-Date` as in
  [data-model.md](data-model.md); read-only files after publication; `verify`
  passes, then fails and names the revision after one payload byte changes
  and, separately, after `bag-info.txt` changes; an unreadable original fails
  the item and adds nothing; names with Korean text, spaces and a leading
  dash are kept; originals unchanged in every case. Test an original that
  changes during the copy (contract step 5) only with a deterministic method;
  otherwise record it in this file as an unperformed check.
  Unperformed check (2026-09-28): no deterministic way was found to change an
  original during the copy, so the step 5 recheck is untested.
- [x] T007 [US1] Implement in SCRIPT `admit` steps 1 to 6 of the contract for
  a path with no existing source (UUID version 7 source ID, UTC revision
  name, staging under `CACHE/raw-import/<wiki>/<run-id>/`, `bagit.make_bag`
  with SHA-256, validation, digest recheck of the original, rename, read-only
  modes) and `verify` with `bagit.Bag(...).validate()` over every revision,
  until T006 passes.

**Checkpoint**: One document can be admitted and checked.

---

## Phase 4: User Story 2 - A changed original becomes a new revision; an unchanged one adds nothing (Priority: P1)

**Goal**: Revisions follow the original's digest.

**Independent Test**: Admit, re-admit unchanged, change, re-admit (spec US2).

- [x] T008 [US2] Add TEST cases for spec US2 scenarios 1 to 3: unchanged
  rerun reports `already_admitted` and leaves the `raw/` snapshot unchanged;
  a changed original adds exactly one revision to the same source ID and the
  earlier revision still validates; a change back to earlier bytes adds a new
  revision; two identical files at different paths become two sources; two
  existing sources with one original path fail that item.
- [x] T009 [US2] Implement in SCRIPT the source lookup by
  `Internal-Sender-Identifier` over `raw/*/*/*/bag-info.txt`, the
  latest-revision digest comparison and the new-revision path, until T008
  passes.

---

## Phase 5: User Story 3 - Nothing is admitted without the user's confirmation, and excluded data never enters (Priority: P1)

**Goal**: Only listed regular files outside excluded locations are copied.

**Independent Test**: Selections with unlisted, excluded and invalid entries
copy nothing for them (spec US3).

- [x] T010 [US3] Add TEST cases: a file beside a listed file is not copied; a
  path under a `[wiki.raw_import] exclude` entry in `CONFIG/config.toml`, a
  path under the data, state or cache root, and a symbolic link resolving
  into an excluded folder are `refused`; a symbolic link, folder or other
  non-regular path is `refused`; duplicate paths, a relative path, an unknown
  field or an unknown kind make the selection invalid (exit 2, `raw/`
  unchanged); a missing configuration file means no user exclusions.
- [x] T011 [US3] Implement in SCRIPT the selection validation, the exclusion
  list (fixed roots plus `tomllib` configuration, compared after resolving
  links) and the refusal reasons, until T010 passes.

---

## Phase 6: User Story 4 - An interrupted import leaves no partial evidence and can be rerun (Priority: P2)

**Goal**: Staged publication, cleanup, per-item failure and one run at a
time.

**Independent Test**: Failure points and reruns leave only valid revisions
(spec US4).

- [x] T012 [US4] Add TEST cases: a leftover staging folder with a partial
  copy and one with a complete bag that was never renamed are removed at the
  next run and never appear in `raw/`; a publication failure (the target
  source folder made unwritable) fails that item, keeps the others and exits
  1 (a full disk is not simulated; record that as an unperformed check); a
  second `admit` while the first holds the lock exits 2 and writes
  nothing; a lock file left by a process killed with `SIGKILL` during a run
  does not block the next run, and after that rerun `verify` passes with no
  duplicate revision; the staging root is empty after every run.
  Unperformed check (2026-09-28): a full disk is not simulated.
- [x] T013 [US4] Implement in SCRIPT the `flock` on
  `STATE/wikis/<name>/raw-import.lock`, staging cleanup at start and end,
  per-item error handling that continues, and the summary line, until T012
  passes.

---

## Phase 7: User Story 5 - The default Wiki instance exists in the constitution's layout (Priority: P2)

**Goal**: `init` creates the layers decided in spec Clarifications.

**Independent Test**: `init` twice in a scratch home; inspect the layout and
the instance's Git status (spec US5).

- [x] T014 [P] [US5] Write the schema template
  `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`: what `raw/` holds,
  the four kinds, the bag layout and fields, that raw is create-only and
  outside the instance's Git history, that conversation records are not raw,
  and that page conventions and ingest come from a later feature.
- [x] T015 [US5] Add TEST cases: `init` creates the full layout of
  [data-model.md](data-model.md) ("Wiki instance"); a second `init` changes
  no byte and no modification time; `git status --ignored` in the instance
  lists `raw/` as ignored after an admission; no `conversations` folder.
- [x] T016 [US5] Extend `init` in SCRIPT to copy the schema template, write
  `.gitignore`, `wiki/index.md`, `wiki/overview.md` and `wiki/log.md`, and
  create the instance's Git repository without committing, until T015 passes
  (depends on T014).

---

## Phase 8: User Story 6 - The user's confirmed documents are imported (Priority: P3)

**Goal**: The real import, one location at a time, with the user's decisions.

**Independent Test**: Report counts per location, `verify` over all of `raw/`,
originals unchanged (spec US6).

- [x] T017 [US6] Write `plugins/work/skills/wiki-raw-import/SKILL.md`: survey
  a location read-only (sizes, counts, types; never open files under excluded
  or private folders), present it with its first judgment, record the user's
  decision, build and show the file list, write the selection under
  `STATE/wikis/default/selections/`, run `init`, `admit` and `verify`, append
  one `wiki/log.md` entry per import and commit the instance, remove the
  selection after `verify` passes, and keep file names out of repositories
  and messages.

Confirm each location with the user through the orchestrator, then record the
decision on the task line (decision and date only). Findings come from
[research.md](research.md) R6.

- [x] T018 [US6] Confirm `~/Documents/20_reference` (63 MB, 78 files). First
  judgment: grammar books and vocabulary profiles are raw candidates; where a
  `.md` is a conversion of a PDF, the PDF is the raw original and the `.md`
  may be rebuildable cache. Finding: 47 docx, 6 pdf, 16 md, 4 hwp.
  Decision (2026-09-28): originals only (docx, pdf, hwp); Markdown
  conversions left out.
- [x] T019 [US6] Confirm `~/Documents/10_midterm`, `~/Documents/11_final` and
  the loose PDF and docx files in `~/Documents` (625 MB, 261 files). First
  judgment: original exam papers go to raw; the user's edited versions stay.
  Finding: 10_midterm also holds scripts (py, bat) and Markdown conversions.
  Decision (2026-09-28): original exam papers only; the user's edits,
  conversions and scripts left out.
- [x] T020 [US6] Confirm `~/projects/work/sources` (26 MB, 8 entries). First
  judgment: raw candidates. Finding: each entry is one original beside JSON
  and lock files from an earlier tool (not evidence under principle IV), and
  two entries look like operational references.
  Decision (2026-09-28): the eight originals only, without the tool's JSON
  and lock files; the file list marks the two operational-looking entries.
- [x] T021 [US6] Confirm `~/projects/work/materials` (2.7 MB, 3 entries).
  First judgment: raw candidates. Finding: mostly the user's own lesson
  materials and tool JSON, which the brief says stay in the user's workspace.
  Decision (2026-09-28): left out.
- [x] T022 [US6] Confirm `~/projects/work/intake` (1.6 GB, 9 entries). First
  judgment: raw candidates. Finding: one entry is a 1.5 GB tree of program
  code and extracted text (5,420 files), not documents.
  Decision (2026-09-28): documents from the other eight entries; the code
  tree left out.
- [x] T023 [US6] Confirm `~/projects/work/{concepts,decisions,stable,draft}`
  (316 MB). First judgment: reference only; the Wiki is rebuilt from raw.
  Nothing is copied. Decision (2026-09-28): reference only, no exclusion.
- [x] T024 [US6] Confirm `~/projects/work/students`. First judgment:
  operational data outside the Wiki; add it to the exclusions. Not surveyed.
  Decision (2026-09-28): excluded.
- [x] T025 [US6] Confirm `~/Zotero` (42 MB). First judgment: stays in place;
  copy selected items with their source. Finding: `storage/` is empty, so
  there are no attachments to copy. Decision (2026-09-28): nothing copied
  now, no exclusion.
- [x] T026 [US6] Confirm `~/ownCloud` (989 MB). First judgment: stays in
  place; copy selected items with their source. Finding: almost all of it is
  one shared-materials folder; the client's journals and logs are never
  copied. Decision (2026-09-28): the user picks files of the
  shared-materials folder from its file list.
- [x] T027 [US6] Confirm `~/data` (39 GB). First judgment: legacy archives,
  not raw; add it to the exclusions. Decision (2026-09-28): excluded.
- [x] T028 [US6] Ask whether any location outside the brief's table joins:
  `~/Documents/ChatGPT` and `~/Documents/Codex` (first judgment: conversation
  records or earlier projects, excluded), `~/Documents/var`,
  `~/Documents/Restore Firefox`, `~/Documents/verbose-broccoli-artifacts` and
  `~/projects/work/{datasets,rules,deprecated}` (first judgment: out of
  scope). Decision (2026-09-28): `~/Documents/ChatGPT` and `~/Documents/Codex`
  excluded as conversation records; the others left out, no exclusion.
- [x] T029 [US6] After the user approves the list, write the exclusions from
  T018 to T028 to `~/.config/verbose-broccoli/config.toml` under
  `[wiki.raw_import]`.
  Done (2026-09-28): six exclusions, those of T024, T027 and T028 plus two
  the user added (the student-Wiki intake entry and ownCloud's personal
  folder).
- [x] T030 [US6] Run `init` on the real default instance and make its first
  commit (schema, `.gitignore`, empty `wiki/` files) in the instance's own
  Git repository.
  Done (2026-09-28): the instance already held `wiki/` pages the user had
  asked another session to write; `init` kept them, and by the user's
  decision the first commit includes all of `wiki/`.
- [x] T031 [US6] For each location admitted in T018 to T028, show the user the
  file list (outside the repository), write the approved selection and run
  `admit`; resolve or report every `refused` and `failed` item.
  Done (2026-09-28): the user approved the proposed lists as shown: 104
  files copied; 185 files offered for the user's call and 605 left out with
  a reason stay out. The ten grammar-book PDF originals come from
  `~/ownCloud`, and byte-identical files at different paths are separate
  sources, both by the user's decision. In `~/projects/work/sources` seven
  originals were copied; the eighth entry is derived from a list of selected
  students and stays out. No item was refused or failed.
- [x] T032 [US6] Run `verify` over the whole instance, append the import's
  entry to `wiki/log.md` and commit it in the instance, remove the finished
  selections, and record in this file per location only the counts admitted,
  already admitted, refused and failed.
  Done (2026-09-28): `verify` passed for all 104 revisions, the originals'
  digests and modification times are unchanged, a rerun reported every item
  as already admitted, and the selections are removed. Counts (admitted,
  already admitted, refused, failed): `~/Documents/20_reference` 48, 0, 0,
  0; `~/Documents/10_midterm` 2, 0, 0, 0; `~/Documents/11_final` and the
  loose files in `~/Documents` nothing selected; `~/projects/work/sources` 7,
  0, 0, 0; `~/projects/work/intake` 37, 0, 0, 0; `~/ownCloud` 10, 0, 0, 0.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [x] T033 [P] Update `docs/architecture.md`: add `wiki-raw-import` to the
  `plugins/work/skills` row of the skill ownership table and a short
  paragraph on where the default Wiki instance lives and how raw provenance
  is recorded.
- [x] T037 [P] In `docs/examples/wiki/AGENTS.md`, remove the paragraph that
  prepares JSON for `wiki apply --input <file>`, a command that does not
  exist, and align the example with the schema template from T014. Added on
  2026-09-28 at the develop session's request instead of a separate issue.
- [x] T034 Run `deno task docs:generate`, then `deno task test:plugin-skills`
  and fix any packaging finding for the new skill's `assets/` and lock file.
- [x] T035 Run `deno task workflow`, then `deno task verify`, and repeat
  diagnosis, repair and verification until it passes.
- [ ] T036 Merge review for `develop` (fresh Claude Code reviewer for the
  script and tests, fresh Codex reviewer for the prose), resolve findings,
  add the review-record commit, and finish with `git flow feature finish
  wiki-storage` from the `develop` worktree.

---

## Dependencies & Execution Order

- T001 and T002 first; T003 → T004 → T005.
- US1 (T006 → T007) needs T005. US2 (T008 → T009), US3 (T010 → T011) and US4
  (T012 → T013) need T007 and edit the same two files, so one worker runs
  them in order.
- US5: T014 is independent; T015 → T016 need T005.
- US6: T017 can be written any time. T018 to T028 are conversations with the
  user and can start any time, but T029 to T032 need T035 to pass first, so
  the real import runs only on verified code.
- T033 and T034 after T016 and T017; T037 after T014; T035 after all code; T036 after T032
  and T035.

## Worker Assignment

| Worker | Tasks | Writable files |
| --- | --- | --- |
| Codex A | T003 to T013, T015, T016 | SCRIPT, the lock file, TEST |
| Main | T001, T002, T014, T017 to T037 | `deno.json`, `orca.yaml`, `assets/AGENTS.md`, `SKILL.md`, `docs/`, this file, everything outside the repository |

T004 moved from main to Codex A on 2026-09-28, because the worker's tests
need the lock file.

## Parallel Example

```text
After T002: Codex A starts T003; main writes T014 and T017 and begins the
confirmations T018 to T028 with the user through the orchestrator.
```

## Implementation Strategy

1. Setup and foundation (T001 to T005).
2. MVP: US1 (T006, T007), then US2, US3 and US4 by the same worker, then US5.
3. Verify (T035) before any real write.
4. Real import (T029 to T032) only after every location has a decision.
5. Docs, merge review, finish.
