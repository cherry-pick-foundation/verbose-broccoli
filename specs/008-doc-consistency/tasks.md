---

description: "Task list for repository document consistency"
---

# Tasks: Repository Document Consistency

**Input**: Design documents from `specs/008-doc-consistency/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Start condition**: Do not start any task until `feature/005-backfire-mcp`
has merged into `develop` (FR-018). Until then, `develop` has no backfire
package or tools, and these tasks must not assume them. Backfire's contracts
can be read on that branch with `git show feature/005-backfire-mcp:<path>`;
never edit that branch or its worktree.

**Tests**: Required. The root `AGENTS.md` asks for tests with every code
change, and each user story names an independent test.

**Organization**: Tasks are grouped by user story. Main (Claude Code) owns
shared files (`deno.json`, `orca.yaml`, `packages/doc-regions/pyproject.toml`
and its lock), installs, Git operations, integration and repository prose;
Codex workers own the code tasks marked in the Worker Assignment section.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Bring in backfire and create the shared environment every worker
runs in.

- [x] T001 Confirm `feature/005-backfire-mcp` has merged into `develop`
  (`git merge-base --is-ancestor feature/005-backfire-mcp develop`), merge
  `develop` into `feature/doc-consistency`, and run `deno task verify`. Then
  compare `backfire_verify`'s and `backfire_classify`'s input schemas and the
  request limits in `backfire ready`'s report with
  [research.md](research.md) R6; record any difference in research.md and
  update [contracts/commands.md](contracts/commands.md) before workers start.
  - 2026-09-28: `develop` is at the 005 merge (8ab332b), already in this
    branch. The schemas match R6, but `backfire ready` reports no limits;
    the fixed option and cell limits now set the claims per request (R6), so
    `--max-claims` is gone. Feature 010's needs (target globs, another root,
    caller evidence) became the library interface in the commands contract
    and FR-014. Baseline `deno task verify` failed only on CHE-14 and passed
    `test:backfire` after `uv sync --project packages/backfire --frozen
    --python /usr/bin/python3.14`.
- [x] T002 Ask the user to approve installing lychee 0.24.2 into
  `~/.local/bin/lychee` (a host change). After approval, download
  `lychee-x86_64-unknown-linux-gnu.tar.gz` and its `.sha256` from the
  `lychee-v0.24.2` release, check the hash
  (`1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a`),
  install the binary, and confirm `lychee --version` prints `lychee 0.24.2`.
  - 2026-09-28: approved and installed; the hash matched and
    `lychee --version` prints `lychee 0.24.2`.
- [x] T003 Create `packages/doc-regions/pyproject.toml` (project
  `doc-regions`, console script `doc-regions = "doc_regions.__main__:main"`,
  dependencies `cogapp==3.6.0` and `markdown-it-py==4.2.0`, dev group
  `pytest` at backfire's pinned version, `required-version = ">=0.11.32"`,
  src layout as backfire), `.python-version` `3.14.4`, an empty
  `src/doc_regions/__init__.py`, and `uv.lock` with `uv lock --project
  packages/doc-regions`; confirm `uv sync --locked --project
  packages/doc-regions` works.
- [ ] T004 Update `deno.json`: add the tasks `doc-regions:check`,
  `doc-regions:update`, `doc-regions:prepare`, `doc-regions:audit` and
  `test:doc-regions` per [contracts/commands.md](contracts/commands.md), each
  running `uv run --project packages/doc-regions --frozen --offline
  --no-sync` (the audit without `--offline`); add `doc-regions:check` to
  `check` and `test:doc-regions` to `test`; allow `doctor` to run `lychee`.
  Do not change `docs:generate`, `docs:check` or `scripts/docs.ts`.
  - 2026-09-28: tasks added, `doctor` may run `lychee`, and `deno task
    docs:generate` refreshed `docs/reference/commands.md` (FR-017). The
    `check` and `test` entries wait until T009 and T011 land, so every commit
    keeps `deno task verify` passing.
- [x] T005 [P] Add `uv sync --locked --project packages/doc-regions` to
  `orca.yaml`'s setup script next to the `tools/spec-kit` line; check with
  `deno fmt --check orca.yaml`.
- [x] T006 Create `scripts/doc_regions.toml` with `targets = ["README.md",
  "docs/architecture.md", "docs/backfire.md"]` plus any project-written plugin
  documents per the spec's Clarifications (none today), `report_only = ["AGENTS.md",
  ".specify/memory/constitution.md"]`, `generators = "doc_sources"` and
  `generator_path = "scripts"` (see [data-model.md](data-model.md)).

**Checkpoint**: The environment, tasks and target list exist; workers can run
their suites.

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T007 Create `packages/doc-regions/src/doc_regions/config.py` and
  `tests/test_config.py`: `load(config_path, root)` reads the TOML with
  `tomllib`, expands path and glob entries against `root` into sorted
  root-relative paths, resolves a relative `generator_path` against `root`,
  and fails with the entry when it matches no file, a file is matched by both
  lists, or a field is missing (library interface in
  [contracts/commands.md](contracts/commands.md)). Tests first; they fail
  before the module exists.

**Checkpoint**: Every command can load its configuration.

---

## Phase 3: User Story 1 - Verification refuses a stale mechanical region (Priority: P1) 🎯 MVP

**Goal**: `deno task check` fails on stale, malformed or missing-source
regions and broken local links, without writing or network.

**Independent Test**: `deno task test:doc-regions` and the quickstart's
"Stale region by hand" ([contracts/regions.md](contracts/regions.md)).

- [ ] T008 [US1] Write `packages/doc-regions/tests/test_regions.py` with
  scratch repositories built in temporary directories: a current region
  passes; a stale region fails with Cog's diff and the text `deno task
  doc-regions:update`; unbalanced and nested markers, a code shape other than
  the allowed one, an unknown function, a keyword argument and a missing
  source each fail naming the line; a broken local link and a missing heading
  fragment fail through lychee; an external URL does not fail; `update`
  changes only region lines and a second run changes nothing; `update` on a
  shape failure changes no file. Every check case compares a hash of all
  files before and after, and runs with `socket.socket` patched to raise.
  The tests fail before T009.
- [ ] T009 [US1] Implement `packages/doc-regions/src/doc_regions/regions.py`
  and the `check` and `update` commands in `__main__.py` per
  [contracts/regions.md](contracts/regions.md): marker scan, the `ast` shape
  rule, source existence, Cog's `Cog().main()` with `--check --diff
  --check-fail-msg` or `-r` and `-I <generator_path>`, and `lychee --offline
  --include-fragments --no-progress` on the targets only; exit codes and output per
  [contracts/commands.md](contracts/commands.md). T008 passes.
- [ ] T010 [P] [US1] Write `scripts/doc_sources_test.py` for a
  `skill_table(glob)` generator: fixture skill folders give the exact
  expected table, sorted by package then skill; a missing glob match raises.
  The tests fail before T011.
- [ ] T011 [P] [US1] Implement `scripts/doc_sources.py` with `skill_table`,
  which lists `SKILL.md` folders under `plugins/*/skills/` as the ownership
  table's rows; no network, clock or environment use. T010 passes.
- [ ] T012 [P] [US1] Extend `scripts/doctor.ts` and `scripts/doctor_test.ts`:
  fail when `lychee --version` is not `lychee 0.24.2`, and when
  `packages/doc-regions/.venv` is missing or differs from its lock (reuse the
  existing `tools/spec-kit` check). Tests first.
- [ ] T013 [US1] Replace the skill ownership table in `docs/architecture.md`
  with a mechanical region calling `doc_sources.skill_table("plugins/*/skills/*/SKILL.md")`,
  run `deno task doc-regions:update`, and confirm `deno task
  doc-regions:check` passes and `git status` shows only the region (depends
  on T009, T011).

**Checkpoint**: User Story 1 works on its own; `deno task check` includes it.

---

## Phase 4: User Story 2 - Agent regions are judged before the `develop` merge review (Priority: P1)

**Goal**: `prepare` prints valid, split backfire requests for every agent
unit; the workflow tool prints the step.

**Independent Test**: `deno task test:doc-regions` and the quickstart's
"Judgment step" steps 1 to 3.

- [ ] T014 [US2] Write `packages/doc-regions/tests/test_units.py`: headings,
  paragraphs, items of a top-level list, a table, a fenced code block and an
  HTML block and a blockquote become units with 1-based inclusive lines and
  their heading path; mechanical-region lines never appear in a unit; units
  cover every non-blank agent-region line exactly once except thematic breaks
  and link reference definitions; `split(document, text,
  base_text)` marks `added` by `difflib` (false for all with `None`, true for
  all with `""`). Fails before T015.
- [ ] T015 [US2] Implement `packages/doc-regions/src/doc_regions/units.py`
  with markdown-it-py (`commonmark` preset, `table` enabled) per
  [data-model.md](data-model.md). T014 passes.
- [ ] T016 [US2] Write `packages/doc-regions/tests/test_requests.py`: in a
  scratch repository with a `develop` branch and a feature commit, `prepare
  --base develop` prints units and requests per
  [contracts/commands.md](contracts/commands.md); every `arguments` object
  validates against copies of backfire's `backfire_verify` and
  `backfire_classify` input schemas kept as test fixtures (taken in T001);
  every verify request stays within 672 answer cells and 250 options as the
  contract computes them, classify requests have at most 64 items, more than
  249 evidence items raise, long diffs split into numbered evidence items
  within `--max-evidence-chars`, and each unit is in exactly one request per
  tool; `added` is true only for fully added units; two runs give
  byte-identical output; no file changes and no socket opens. Library cases:
  `verify_requests` with several `(units, evidence)` groups keeps input
  order and passes evidence through unchanged. Fails before T017.
- [ ] T017 [US2] Implement `packages/doc-regions/src/doc_regions/requests.py`
  and the `prepare` command (`git merge-base`, `git diff` through
  `subprocess`, splitting and sorting). T016 passes.
- [ ] T018 [P] [US2] Extend the REVIEW text in `scripts/workflow.ts`
  (`actions.REVIEW`) and `scripts/workflow_test.ts` (and help snapshots if
  they change): before the `develop` merge review, run `deno task
  doc-regions:prepare` and `deno task doc-regions:audit`, send the requests
  to backfire, fix target documents and report `AGENTS.md` and constitution
  findings to the user. Tests first.

**Checkpoint**: The main agent can run the judgment step.

---

## Phase 5: User Story 3 - Drift in `AGENTS.md` and the constitution is reported, not fixed (Priority: P2)

**Goal**: `audit` runs MemoryLint on the report-only documents without
changing them.

**Independent Test**: `deno task test:doc-regions` and the quickstart's
"Judgment step" step 4.

- [ ] T019 [US3] Write `packages/doc-regions/tests/test_audit.py`: with a
  local copy of the pinned archive served from a temporary directory, the
  audit checks the SHA-256, extracts into a temporary cache directory, runs
  `scripts/audit_workspace.py <root> --format json`, and returns only findings
  for report-only documents; a planted stale path in a scratch `AGENTS.md`
  appears as a `reality` finding; a wrong hash fails without running
  anything; a download that would pass the 1 MiB budget, a failure and a
  SIGTERM each leave no temporary directory, and a leftover from a killed run
  is removed by the next run; the repository's files are unchanged. Fails
  before T020.
- [ ] T020 [US3] Implement `packages/doc-regions/src/doc_regions/audit.py`
  and the `audit` command per [research.md](research.md) R7: download once
  into `~/.cache/verbose-broccoli/memorylint/1.5.1/` (honoring
  `XDG_CACHE_HOME`) within the 1 MiB budget and cleanup rules of
  [contracts/commands.md](contracts/commands.md), check the hash, run with the
  environment's Python, and never run MemoryLint's `apply`. T019 passes.

**Checkpoint**: The judgment step covers the report-only documents.

---

## Phase 6: User Story 4 - A reader and feature 010 can find the region model (Priority: P3)

**Goal**: The documentation describes the model and the procedures.

**Independent Test**: Read the section; add a region to a scratch document by
following it.

- [x] T021 [US4] Add a "Document consistency" section to
  `docs/architecture.md`: the region model, the target list and its location,
  how to add a generator and a region, the check in `deno task check`, the
  judgment step before the `develop` merge review, the MemoryLint audit, and
  what stays manual (acting on judgments, reporting to the user, installing
  lychee). Mention that feature 010 reuses `packages/doc-regions`. Link to
  the marker syntax in [contracts/regions.md](contracts/regions.md) instead of
  quoting it: Cog would run a quoted marker as a region.
- [x] T022 [US4] Add lychee, cogapp, markdown-it-py and MemoryLint to
  `licenses/THIRD_PARTY_NOTICES.md` with source, version and license.
- [ ] T023 [US4] Run the judgment step on this feature's own changes: send
  `backfire_classify` the current units of `README.md`,
  `docs/architecture.md` and `docs/backfire.md` and convert the candidates the main agent confirms
  into regions with tested generators (R9); send `backfire_verify` and fix
  what it flags; report `AGENTS.md` and constitution findings to the user
  (depends on T013, T017, T020).

---

## Phase 7: Polish and Integration

- [ ] T024 Run the quickstart, `deno task verify` and `deno task docs:check`
  on the combined result; rerun `deno task workflow` with the same task and
  base; repair until they pass. Check SC-002 (the check adds at most 5 s).
- [ ] T025 SC-005: on a scratch branch that renames a task
  `docs/architecture.md` describes in prose, run `prepare` and
  `backfire_verify` three times; the paragraph must come back `contradicted`
  or `review` every time. Record the results in this file.
- [ ] T026 Merge review for `develop`, favoring speed: fresh reviewers from
  the other provider for the Codex code and for main's prose, given only the
  scope and requirements; resolve findings; add the review-record commit and
  finish with `git flow feature finish doc-consistency` from the `develop`
  worktree.

---

## Dependencies & Execution Order

- Nothing starts before 005 merges; T001 first.
- T002 to T006 follow T001; T005 is independent of T003 and T004.
- T007 needs T003. US1 (T008 → T009; T010 → T011; T012) needs T004 and T007;
  T013 needs T009 and T011.
- US2 (T014 → T015 → T016 → T017) needs T007; T018 is independent.
- US3 (T019 → T020) needs T007.
- T021 and T022 can be written while workers work; T023 needs T013, T017 and
  T020. T024 needs all implementation; T025 and T026 follow T024.

## Worker Assignment

| Worker | Tasks | Writable files |
| --- | --- | --- |
| Codex A | T007 to T009, T014 to T017, T019, T020 | `packages/doc-regions/src/doc_regions/`, `packages/doc-regions/tests/` |
| Codex B | T010 to T012, T018 | `scripts/doc_sources.py`, `scripts/doc_sources_test.py`, `scripts/doctor.ts`, `scripts/doctor_test.ts`, `scripts/workflow.ts`, `scripts/workflow_test.ts`, `scripts/__snapshots__/` if a snapshot changes |
| Main | T001 to T006, T013, T021 to T026 | shared files, `docs/architecture.md`, `licenses/`, prose, Git |

## Parallel Example

```text
After T007: Codex A takes US1, then US2 and US3 in the package; Codex B takes
T010 to T012 and T018; main writes T021 and T022.
```

## Implementation Strategy

1. After 005 merges: setup (T001 to T006), then T007.
2. MVP: User Story 1, so `deno task check` guards mechanical regions.
3. User Stories 2 and 3 in the package; the workflow text.
4. Documentation and the first real judgment step on this feature.
5. Verify, SC-005, merge review, review record, finish.
