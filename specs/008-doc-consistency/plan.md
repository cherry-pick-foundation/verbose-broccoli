# Implementation Plan: Repository Document Consistency

**Branch**: `feature/doc-consistency` | **Date**: 2026-09-27 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/008-doc-consistency/spec.md`

## Summary

Keep `README.md`, `docs/architecture.md`, `docs/backfire.md` and
project-written plugin documents consistent with the repository by splitting them into mechanical and agent
regions:

- Mechanical regions are Cog blocks whose code is one call of a registered
  generator on named source files. `deno task check`, and so `deno task
  verify`, runs Cog's `--check` and lychee's offline link check, writing
  nothing and using no network. One command regenerates stale regions.
- Before each `develop` merge review, an offline command splits agent regions
  into units with markdown-it-py and prints `backfire_verify` and
  `backfire_classify` arguments; the main agent sends them to backfire, fixes
  target documents, and reports drift in `AGENTS.md` and the constitution,
  which also get a MemoryLint audit. `deno task workflow` prints the step.
- The engine is a reusable Python package, `packages/doc-regions/`, for
  feature 010; the target list and generators are repository automation in
  `scripts/`.

Implementation starts only after `feature/005-backfire-mcp` merges into
`develop` (FR-018). Research: [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14.4 through uv 0.11.32 for the package and
generators (R5); TypeScript on Deno 2.9.6 for the doctor and workflow changes.

**Primary Dependencies**: `cogapp` 3.6.0 and `markdown-it-py` 4.2.0 (MIT,
locked in `packages/doc-regions/uv.lock`); lychee 0.24.2 (MIT or Apache-2.0,
host tool, R4); MemoryLint 1.5.1's audit script (MIT, pinned archive in the
cache, R7); backfire's `backfire_verify` and `backfire_classify` from feature
005, called by the main agent (R6).

**Storage**: None added to the repository. MemoryLint's archive is cached in
`~/.cache/verbose-broccoli/memorylint/1.5.1/` (rebuildable; constitution VI's
cache rule).

**Testing**: pytest in the package's uv environment for region parsing, the
source-naming rule, regeneration, unit splitting and request preparation, with
socket access blocked and tree hashes compared before and after check runs;
`deno test` for the doctor and workflow changes.

**Target Platform**: The development machine (Linux x86_64) inside Orca
worktrees.

**Project Type**: A reusable package under `packages/` plus repository
automation under `scripts/`.

**Performance Goals**: The check adds at most 5 seconds to `deno task check`
(SC-002); Cog and lychee each took under a second in the probes.

**Constraints**: The check never writes and never uses the network; backfire
never runs in `verify` or the finish hook; `scripts/docs.ts` and `deno task
docs:check` are unchanged, and `docs/reference/` changes only through `deno
task docs:generate` (FR-017); `AGENTS.md` and
the constitution are never edited by this tooling; local code is limited to
glue (the source-naming check, unit selection and request shaping).

**Scale/Scope**: One package (about four modules and their tests), one
generator module, one target list, four `deno.json` tasks, and edits to
`scripts/doctor.ts`, `scripts/workflow.ts`, `orca.yaml` and
`docs/architecture.md`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Status |
| --- | --- |
| I. Proven dependencies | PASS. Versions, licenses and behavior probed (R1, R3, R4, R7); lychee is a pinned host tool checked by `doctor`; Python packages are locked. |
| II. Working capabilities | PASS. Every behavior is tested by running the real tools on scratch documents; backfire requests are checked against 005's published input schemas. |
| V. Observable acceptance | PASS. Tests cover passing, stale, malformed and missing-source regions, unbalanced markers, broken links, no-network runs and unchanged files. SC-005 runs real backfire three times. |
| VI. Storage | PASS. Only a rebuildable archive in the XDG cache; nothing in data or state. |
| VII. Generated writers | PASS. The audit's cache writer has a 1 MiB budget and cleanup on success, failure and interruption (R7); `update` rewrites only region text. |
| VII. Minimum implementation, one owner | PASS. Cog, markdown-it-py, lychee and MemoryLint own their parts; each generated region has one source and a non-mutating drift check in verification; the generated reference stays with `scripts/docs.ts`. |
| IX. Layout | PASS. Reusable code in `packages/doc-regions/src/`, repository generators and list in `scripts/`. It is not a Deno workspace member (no Deno code). |
| Governance | No constitution change. |

Re-check after design: unchanged; no violations. Rechecked on 2026-09-28
against constitution 1.0.0 after merging `develop`: principle VIII no longer
exists, and the other rows hold.

## Project Structure

### Documentation (this feature)

```text
specs/008-doc-consistency/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── regions.md
│   └── commands.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
packages/doc-regions/
├── pyproject.toml, .python-version, uv.lock
├── src/doc_regions/
│   ├── __main__.py        # check, update, prepare, audit
│   ├── config.py          # target list (tomllib)
│   ├── regions.py         # markers, source-naming rule, Cog calls
│   ├── units.py           # markdown-it-py unit splitting
│   ├── requests.py        # backfire request shaping and splitting
│   └── audit.py           # MemoryLint download, hash check, run
└── tests/
scripts/
├── doc_regions.toml       # targets and report-only documents
├── doc_sources.py         # repository generators
├── doc_sources_test.py    # generator tests (run by test:doc-regions)
├── doctor.ts, doctor_test.ts
└── workflow.ts, workflow_test.ts
deno.json                  # doc-regions:* tasks; check and test entries
orca.yaml                  # uv sync for packages/doc-regions
docs/architecture.md       # document consistency section; first regions
```

**Structure Decision**: The engine is reusable by feature 010 and so goes in
`packages/` (constitution IX). What is specific to this repository, the target
list and the generators, is repository automation in `scripts/`. The
package's layout copies backfire's so a plugin build can copy it the same way.

## Design Decisions

- **Region model** ([data-model.md](data-model.md)): a document is a sequence
  of mechanical regions (marked) and agent regions (the rest). Feature 010
  uses the same model with its own list and generators.
- **Markers and sources** ([contracts/regions.md](contracts/regions.md)): Cog
  markers in HTML comments; code limited to one generator call whose string
  arguments are source paths or globs (R2).
- **Commands** ([contracts/commands.md](contracts/commands.md)):
  `doc-regions check|update|prepare|audit` with a config path, run through
  `deno task doc-regions:*`. `check` joins `deno task check`; `prepare` and
  `audit` run only in the pre-review step.
- **Library interface** ([contracts/commands.md](contracts/commands.md)):
  the commands wrap functions that take a root, globbed targets and
  caller-supplied `(units, evidence)` groups, so feature 010 calls them on a
  Wiki instance without changing the package (research, "For feature 010").
- **Judgment step**: the main agent runs `prepare` and `audit`, sends each
  printed request to backfire through its MCP client, fixes contradicted or
  review-flagged units of target documents, reports findings for `AGENTS.md`
  and the constitution to the user, and then asks for the merge review.
  `deno task workflow` prints this in REVIEW mode (R8).
- **Host tool**: lychee is installed like git-flow, from its release archive
  after a checksum check, into `~/.local/bin`. Installing it is a host change
  that needs the user's approval at implementation time.

## Work Split and Ownership

Main (Claude Code) owns shared files, installs, Git operations, integration
and repository prose; Codex workers implement code in disjoint files through
Orca orchestration, per `.claude/rules/claude-code.md`.

1. **Main, first**: confirm 005 has merged, merge `develop` into this branch,
   recheck backfire's tool schemas against R6, install lychee after the user
   approves, create the package's `pyproject.toml` and lock, and add the
   `deno.json` tasks and the `orca.yaml` line.
2. **Workers in parallel**:
   - the package engine and its tests (regions, units, requests, audit, CLI);
   - the repository generators and their tests, and the doctor checks;
   - the workflow REVIEW text and its tests.
3. **Main**: `scripts/doc_regions.toml`, the first mechanical regions in
   `docs/architecture.md`, the documentation section, and the first real
   judgment step (SC-005).

Model, reasoning effort and time budget for each worker come from backfire's
judgments, chosen per worker when it is started.

## Review and Finish

- Before each commit, the implementer or the orchestrator reviews the diff.
- Run this feature's own judgment step before its merge review.
- Merge review for `develop` (favoring speed) by fresh reviewers from the other
  provider, given only the scope and requirements; then the review-record
  commit and `git flow feature finish doc-consistency` from the `develop`
  worktree.

## Complexity Tracking

No constitution violations to justify.
