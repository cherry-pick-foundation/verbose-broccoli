# Implementation Plan: Wiki Storage and Raw Documents

**Branch**: `feature/wiki-storage` | **Date**: 2026-09-27 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/009-wiki-storage/spec.md`

## Summary

Create the default Wiki instance in constitution principle VI's layout and
admit the user's confirmed documents into its `raw/` by copying, with each
revision's provenance recorded in the revision itself:

- Each source revision is one BagIt bag (RFC 8493) made and validated by
  bagit-python 1.9.0: the copy, its SHA-256 manifest, and `bag-info.txt` with
  the stable source ID, the original path, the original's modification time
  and the admission time (research R1). Revisions are found by reading the
  bags, so there is no parallel registry (FR-009).
- A work-plugin skill, `wiki-raw-import`, holds the agent procedure and one
  Python glue script pinned with a uv script lock (R2). The script's `init`,
  `admit` and `verify` commands follow
  [contracts/raw-import-cli.md](contracts/raw-import-cli.md).
- Copies are staged in the cache root, validated, rechecked against the
  original and published with one atomic rename; one run at a time holds a
  lock in the state root (R3).
- The real import happens only after the user decides on each candidate
  location and approves each file list; tasks.md holds one confirmation task
  per location with the brief's first judgment and the survey's findings (R6).

## Technical Context

**Language/Version**: Python 3.14 through uv 0.11.32 for the glue script;
TypeScript on Deno 2.9.6 for the black-box tests, as the other repository
checks are.

**Primary Dependencies**: bagit 1.9.0 (PyPI, public domain), pinned by
`raw_import.py.lock`; Python standard library (`hashlib`, `shutil`,
`tomllib`, `fcntl`, `uuid`, `json`); Git for the instance's history.

**Storage**: Files under the XDG data, state, cache and configuration roots
([data-model.md](data-model.md)); nothing in the repository.

**Testing**: `scripts/wiki_raw_import_test.ts` runs the script as a child
process with every XDG root and `HOME` in a temporary folder and synthetic
fixtures only; `deno task test:wiki-raw-import`, part of `deno task test`.

**Target Platform**: The development machine (Linux), one user, one file
system for the home folder and the XDG roots.

**Project Type**: Agent skill with a command-line glue script in the work
plugin.

**Performance Goals**: The real import (at most a few thousand files, about
2 GB) finishes in one session; hashing and copying are I/O bound. No other
target.

**Constraints**: Originals are only read; `raw/` never shows a partial or
changed revision; no user path, name or content enters the repository;
locally owned code is limited to glue (root `AGENTS.md` reuse order).

**Scale/Scope**: One skill (procedure, schema template, script, lock), one
test file, edits to `deno.json` and `orca.yaml`, a skill-table row in
`docs/architecture.md`, regenerated `docs/reference/`, and the real import.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Status |
| --- | --- |
| I. Proven dependencies | PASS. bagit 1.9.0 is pure Python; the probe ran it on the selected Python 3.14.6 through uv, and the script lock pins resolution and hashes (R2). |
| II. Working capabilities | PASS. Tests run the real script and bagit on synthetic files and read back copies, records and originals. |
| III. Sources and ownership | PASS. Originals stay in place and unchanged; revisions keep provenance; source IDs are not derived from normalized names (R4); operational data is excluded by path (R5). |
| IV. Importing user data | PASS. This feature is the separately specified import. Ownership: the user decides each location and approves each file list before any write (FR-013). Verification: digests before and after copying and bag validation (FR-010, FR-007). Recovery: staged, atomic publication and idempotent reruns (FR-015, FR-016). Unknown ownership stops that location. |
| V. Observable acceptance | PASS. Positive, negative, boundary, duplicate, interrupted-write, lock, readback and unchanged-original cases are in the tests (contract "Guarantees"). |
| VI. Wiki layers and storage | PASS. Layout and XDG roots as the principle states; raw is create-only; raw never enters the instance's Git history (`.gitignore`) or the repository; staging in cache, lock in state; no parallel registry. `registry.json` is not created (spec Assumptions). |
| VII. One owner, minimum implementation | PASS. The bag is the only provenance record; the glue does only what no upstream tool does (R2). Storage budget: staging holds one item at a time and has explicit success, failure and interruption cleanup; `raw/` grows only by the approved file lists, whose total size the user sees before approving; the lock file is a single empty file. |
| VIII. No new exceptions | PASS. No exception is claimed. |
| IX. Layout | PASS. Business capability in `plugins/work/skills/`; its test is a repository check under `scripts/`; the work package gains no Deno configuration. |
| Product and Data Boundaries | PASS. Private records stay out of fixtures, snapshots and reports; repository records hold counts, sizes and folder-level judgments. |
| Workflow | PASS. Spec Kit flow, git flow feature branch, merge-time review. |

Re-check after design: unchanged; no violations.

## Project Structure

### Documentation (this feature)

```text
specs/009-wiki-storage/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── raw-import-cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
plugins/work/skills/wiki-raw-import/
├── SKILL.md                    # procedure: survey, confirm, select, init, admit, verify, log
├── assets/AGENTS.md            # schema template for a new instance
└── scripts/
    ├── raw_import.py           # glue: init, admit, verify
    └── raw_import.py.lock      # uv script lock (bagit 1.9.0)
scripts/wiki_raw_import_test.ts # black-box tests with synthetic fixtures
deno.json                       # test:wiki-raw-import task, added to test
orca.yaml                       # setup: uv sync --locked --script …
docs/architecture.md            # skill ownership table row
docs/reference/                 # regenerated
```

**Structure Decision**: The capability acts on the user's data, so it is a
work-plugin skill (constitution IX; brief
`briefs/2026-09-27-linear-and-documents.md`, section 3). Its test is a
repository check that drives the script from outside, so the work package
needs no Deno configuration. A shared package under `packages/` waits for a
second consumer.

## Work Split and Ownership

Main (Claude Code) owns shared files, repository prose, the confirmations with
the user and every write outside the repository; a Codex worker implements the
script and its tests (`.claude/rules/claude-code.md`).

1. **Main, first**: `deno.json` task, `orca.yaml` setup line, `uv lock
   --script` after the worker's metadata block exists.
2. **Codex worker**: `raw_import.py` and `scripts/wiki_raw_import_test.ts`
   against the contract.
3. **Main, in parallel**: `SKILL.md`, `assets/AGENTS.md`,
   `docs/architecture.md`.
4. **Main, after verification**: the confirmations with the user, the user's
   configuration, `init`, the real import and `verify`, the instance's first
   log entry and commit, and the ledger lines in tasks.md.

Model, reasoning effort and time budget for the worker come from backfire's
judgments (the local jev setup until backfire works), chosen when it starts.

## Review and Finish

- Before each commit, the implementer or the orchestrator reviews the diff.
- The merge review for `develop` favors speed: a fresh Claude Code reviewer
  for the Codex-written script and tests, and a fresh Codex reviewer for the
  prose main wrote, each given only the scope and requirements. Then the
  review-record commit and `git flow feature finish wiki-storage`.
- The real import runs before the merge review, so its ledger lines in
  tasks.md are part of the reviewed branch and merging into `develop` still
  means the feature is done.

## Complexity Tracking

No constitution violations to justify.
