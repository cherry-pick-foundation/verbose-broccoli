---

description: "Task list for the backfire rebuild on jev-judge-mcp"
---

# Tasks: Backfire Rebuilt on jev-judge-mcp

**Input**: Design documents from `specs/021-backfire-rebuild/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: The spec requires a failing-first CHE-37 test (FR-013), the
kept CHE-33 answerless-reply test (FR-006), stub tests for each provider
(SC-002), the CHE-38 known failure (FR-014), and the tool-list check
(SC-001). Every code task includes its tests.

**Organization**: Main (Claude Code) owns the Spec Kit records, repository
prose, integration and commits, and reviews each Codex worker's diff. Codex
workers (`gpt-6-luna`, `max` effort, started through Orca's terminal path)
implement in disjoint file scopes. A fresh Claude Code reviewer gives the
develop merge review of the code; a fresh Codex reviewer reviews the
coordinator's records and documents.

**Redesign**: on 2026-09-30 the user replaced the first design (a vendored
copy of PyModel) with PyModel as a published dependency. T001 to T005 below
were done for the first design (commit `051f834`) and are undone by T006.
The first design's later tasks were never committed and are replaced by
T006 onward.

**Private data**: No task writes a student name, a private backfire record
or evaluation data into the repository, Linear or Orca messages. No task
opens `$XDG_DATA_HOME/verbose-broccoli/backfire-eval/heldout-v1.jsonl`.
Billed provider calls happen only in T016. No task reads or prints a key.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US3)

---

## Phase 1 (first design, superseded 2026-09-30): the vendored upstream

**Purpose**: the upstream copy, its license and record, and the checks that
must leave it in its upstream form. Blocks every later phase.

- [x] T001 Copy the 64 upstream modules listed in
  [research.md](research.md) R1 from jev-judge-mcp at
  `fd6829c3fd1c3eb244f0feb011b6ca55298459f8` into
  `packages/backfire/src/jev_judge_mcp/`, byte for byte, with the upstream
  `LICENSE` and `THIRD_PARTY_NOTICES.md` in that directory; add
  `jev_judge_mcp` to `module-name` and raise `requires-python` to `>=3.12`
  in `packages/backfire/pyproject.toml`; pin `pydantic-settings` (2.x) and
  `httpx` (0.28.x) there and update `uv.lock`. Confirm
  `import jev_judge_mcp.tools, jev_judge_mcp.stdio` works in the workspace
  environment (FR-015).
- [x] T002 Write `packages/backfire/src/jev_judge_mcp/UPSTREAM.md` as
  [contracts/upstream-record.md](contracts/upstream-record.md) defines,
  with every file `unchanged` so far, and add
  `packages/backfire/tests/test_upstream_record.py`: it checks each file
  against the table and fails, naming the file, on an unrecorded
  difference, a missing row or a missing file; a case on a temporary copy
  proves the failure (FR-015, SC-007).
- [x] T003 Vendor the upstream tests that exercise the vendored modules and
  run offline without Node.js, Docker or network, with their support files
  and fixtures, under `packages/backfire/tests/upstream/`, keeping the
  upstream `tests/` layout below it; record them in `UPSTREAM.md`; pin any
  test-only dependency in the `dev` group; make them run in
  `npm run test:backfire`, and report their count and added run time
  ([research.md](research.md) R9, SC-002).
- [x] T004 Keep the vendored files out of the repository's style checks, as
  `.specify/extensions/` already is: `ruff.toml` (lint and format),
  the Prettier file lists in `package.json` (`format`, `format:check`), and
  any other check that `npm run verify` shows touching them (for example
  link checks or `clean-code` scope); keep
  `packages/backfire/tests/test_no_provider_names.py` passing.
- [x] T005 Replace the jev-mcp 0.9.0 entry in
  `licenses/THIRD_PARTY_NOTICES.md` with jev-judge-mcp 0.6.0's credit (MIT,
  copyright holder, revision, where the copy lives, and that it carries its
  own notice for jev-mcp 0.5.0 text).

  - 2026-09-30: worker A (Codex `gpt-6-luna`, max) did T001–T005 after a
    restart interrupted the first attempt. 64 modules and 348 upstream test
    files (44 test modules, 3,314 tests, about 40 s) are byte-identical to
    `fd6829c`; the coordinator re-checked every file against a fresh clone.
    Test-only pins: `hypothesis`, `respx`. `build.py` already copies
    `jev_judge_mcp` into both builds (moved forward from T017 because the
    module list changed). The jev-mcp 0.9.0 notice stays until T009
    removes the port. `npm run verify` passed.

---

## Phase 2: User Story 1 — PyModel's tools through backfire (Priority: P1) 🎯 MVP (core worker)

**Goal**: `backfire serve-mcp [--education]` serves PyModel's server and
tools plus `jev_noul`, with backfire's profiles as providers.

**Independent Test**: start both plugin commands with stub providers; list
and call the tools ([quickstart.md](quickstart.md)).

- [x] T006 [US1] Switch `packages/backfire` to the published dependency:
  pin `jev-judge-mcp==0.6.0` (with the extra its TypeSafe provider needs)
  in `packages/backfire/pyproject.toml` and `uv.lock`; remove
  `packages/backfire/src/jev_judge_mcp/`, `packages/backfire/tests/upstream/`,
  `test_upstream_record.py`, the module from `module-name`, the Ruff and
  Prettier exclusions and the dev pins that only the vendored tests needed.
- [x] T007 [US1] Write the entry point in
  `packages/backfire/src/backfire/__main__.py` as [plan.md](plan.md)
  section 1 says, with a test that the server lists PyModel's `TOOLS` then
  `jev_noul` and reports PyModel's name (FR-001, FR-002, SC-001).
- [x] T008 [US1] Write `packages/backfire/src/backfire/providers.py`,
  `config.py` (simplified) and `failures.py` (`JudgmentError` only) as
  [contracts/provider-seam.md](contracts/provider-seam.md) says, reusing
  worker B's `jev_provider.py` where it fits: the Hive provider through
  system-one-adapter with PyModel's retries plus CHE-33's answerless-reply
  retry (keep and adapt CHE-33's existing test), Jev profiles through
  PyModel's `resolve_provider`, the education wrapper, and configuration
  errors as `ProviderConfigError`. Tests use local stubs only (FR-005,
  FR-006, FR-008, FR-009).
- [x] T009 [US1] Port the Vercel provider into
  `packages/backfire/src/backfire/vercel.py` from jev-agent-tools 0.1.2
  ([research.md](research.md) R11), credited with its MIT notice; add the
  unselected `vercel` profile to `packages/backfire/src/backfire/config.toml`
  with `credential_file` pointing at the chat plugin's `jev.env` and
  `credential = "AI_GATEWAY_API_KEY"`; test the request (URL path,
  headers, body, question and answer mapping, usage) against a local stub
  without reading the real key (FR-007).
- [x] T010 [US1] Make `packages/backfire/src/backfire/noul.py` define
  `jev_noul` on PyModel's framework as [plan.md](plan.md) section 4 says,
  with tests for its definition, questions, labels, invalid answers,
  budget error and the `auto_accept` bound (0.5 rejected, 0.51 accepted)
  (FR-003).
- [x] T011 [US1] Remove what the user dropped (FR-010): `boundary.py`,
  `decisions.py`, `judge.py`, `provider.py`, `ready.py`, `records.py`,
  `registry.py`, `server.py`, `validate.py`, `jev_provider.py` once its code
  moved, `packages/backfire/src/backfire_tools/`, `scripts/backfire/fixtures/`,
  the backfire `build`, `ready` and `eval` scripts in `package.json` and
  `turbo.json`, and every test that covers only removed code; adapt the
  education tests that stay. List each removed file's importers first.

  - 2026-09-30: the core worker (Codex `gpt-6-luna`, max) did T006–T013;
    `npm run test:backfire` gave 136 passed and one strict expected failure
    (CHE-38). Own code under `packages/backfire/src/backfire/`: 757 Python
    and TOML lines (`noul.py` 199, `providers.py` 204, `config.py` 145,
    `vercel.py` 122 with its 23-line license text, `__main__.py` 47,
    `failures.py` 23, `config.toml` 16, `__init__.py` 1); the user's
    approval above 500 lines was asked for and is pending. The coordinator
    checked that the kept CHE-33 test fails without the answerless-reply
    retry and passes with it.

**Checkpoint**: `npm run test:backfire` passes; both plugin commands start
from `packages/backfire`.

---

## Phase 3: User Story 2 — CHE-37 fixed, CHE-38 handed upstream (Priority: P1)

- [x] T012 [US2] (core worker) Rerun CHE-37's heavy-load reproduction
  (`.specify/bugs/extract-regex-startup-timeout/assessment.md` on branch
  `feature/backfire-extract-test`) against PyModel's own regex executor
  through backfire's server: 80 busy processes, simple and runaway fields,
  several runs; record under T012 how many simple-pattern fields timed out
  falsely. Runaway patterns use one that runs away under Python's `re`,
  such as `(a+)+$` (FR-004, FR-013). The user dropped the `regex` library
  on 2026-09-30: no `regex` pin and no custom executor.
  - Five `jev_extract` runs with 80 `nice -n 19 yes` processes and `(a|aa)+$` against 60 `a` characters plus `b`: false simple-pattern timeouts `0, 0, 0, 0, 0`; the runaway field returned `invalid_pattern` in each run. Worst event-loop lags were `3.467, 3.099, 1.731, 3.576, 5.590 ms`.
- [x] T013 [US2] (core worker) Adapt
  `packages/backfire/tests/test_bounded_work.py` to the rebuilt server:
  PyModel's eleven tools and `jev_noul`, runaway extract fields that run away
  under Python's `re`, 10 MiB messages and the 1-second check kept, and the
  `jev_verify` case marked as an expected failure naming CHE-38. Run it
  3 times with 16 busy processes and the extract case 5 times with 80, and
  record the results under T013 (FR-014, SC-003, SC-004).
  - 16-process sweep, worst event-loop lag in ms (runs 1/2/3): `jev_verify` 2629.162/5294.561/5615.968; `jev_screen` 2.276/7.638/4.140; `jev_find` 116.386/131.583/148.254; `jev_classify` 6.854/2.813/5.696; `jev_decide` 4.620/22.904/42.318; `jev_rerank` 28.587/18.664/8.724; `jev_compare` 3.811/2.661/77.081; `jev_extract` 54.640/2.991/90.373; `jev_review` 57.054/2.792/6.895; `jev_gate` 3.644/3.027/33.277; `jev_score` 3.313/20.174/50.884; `jev_noul` 2.552/44.411/51.579. Each sweep passed 11 and xfailed `jev_verify` for CHE-38.
  - Five 80-process extract runs using `(a|aa)+$` against 60 `a` characters plus `b`: worst event-loop lags were `3.007, 2.997, 9.910, 2.233, 7.622 ms`; false simple-pattern timeouts were `0, 0, 0, 0, 0`.
- [x] T014 [P] [US2] (upstream worker) Prepare the PyModel contribution in
  `specs/021-backfire-rebuild/upstream/` as [plan.md](plan.md) section 6
  says: `pymodel.patch` against `v0.6.0` with PyModel-style tests, and
  `pull-request.md`; include CHE-37's fix only if its rerun (T012 and the
  worker's own check) shows false time-outs; run PyModel's suite on the
  patched clone and the `jev_verify` load case against it; publish nothing
  (FR-013, FR-014).
  - 2026-09-30: the upstream worker wrote `upstream/pymodel.patch` (linear
    duplicate IDs, a 10 MiB stdin line limit, `exclusiveMinimum` and
    `exclusiveMaximum`, and off-loop parsing, serialization and the large
    `jev_verify` and `jev_find` steps) and `upstream/pull-request.md`. The
    patch applies to `v0.6.0`; PyModel's offline suite passed (4,584
    passed, 8 skipped, 17 deselected); the 10 MiB `jev_verify` case with
    100,000 identical IDs went from at least 2,000 ms of stall to 8.3 ms
    with 16 busy processes. Its CHE-37 check (8 runs with 80 busy
    processes) found no false time-out, so no CHE-37 fix was added.

---

## Phase 4: User Story 3 — small, and run from the repository (Priority: P2)

- [x] T015 [US3] (plugins worker, after T011) Point both plugins'
  `mcp.json` at `packages/backfire` (the work plugin with `--education`),
  point `plugins/work/skills/wiki-consistency/SKILL.md`'s commands at the
  repository's `packages/`, change the doc-regions and wiki-consistency
  request builders and their tests to `jev_` names, and fix any `scripts/`
  check that names the removed build or the old tool names (FR-011,
  FR-012, SC-008).
  - 2026-09-30: the plugins worker did T015: doc-regions 106 passed,
    wiki-consistency 291 passed, `plugins:validate` passed, workflow tests
    58 passed; both plugin commands started from the repository and
    reported `jev-mcp` 0.6.0. The request limits in doc-regions stay
    within PyModel's (it sets no maximum for `jev_verify` claims or
    evidence; `jev_classify` allows 64 items, the batch size used). A
    client that copies a plugin elsewhere, such as a Codex local
    marketplace install, cannot reach `packages/backfire`.

---

## Phase 5: Polish and acceptance (coordinator)

- [ ] T016 Run the live checks: one judgment per tool through the shipped
  Hive profile (at most 15 billed calls) and one judgment through the
  Vercel profile; record the call counts and outcomes under T016 (SC-006).
- [x] T017 [P] Update `docs/backfire.md`, `docs/architecture.md`, the
  backfire skills in both plugins (`jev_` names; `upstream.json`
  `local_modifications`), `licenses/THIRD_PARTY_NOTICES.md` (notices only
  for copied code: add jev-agent-tools for the Vercel port, keep jev-mcp
  only for the skill text, remove the jev-judge-mcp and system-one-adapter
  entries, update the python-phonenumbers entry), and regenerate
  `docs/reference/` if its inputs changed (FR-012, FR-015).
- [ ] T018 Count backfire's own code against `develop` with its file list
  and report it; stop and ask before exceeding 500 lines (FR-017, SC-007).
- [ ] T019 Run the document judgment step the develop merge review uses and
  resolve contradicted units; run `npm run verify` three times in a row
  without a rerun and record each result (SC-005).
- [ ] T020 Write `specs/021-backfire-rebuild/report.md`, commit it, move
  CHE-39 to In Review, get the develop merge review (fresh Claude Code
  reviewer for code, fresh Codex reviewer for records), resolve findings,
  add the review-record commit, merge `develop` into the branch and verify,
  confirm `develop` has not moved, run `git flow feature finish
  backfire-rebuild` from the `develop` worktree, move CHE-39 to Done with
  one completion comment, and tell the develop session that CHE-37 is fixed
  and CHE-38 waits for PyModel.

---

## Dependencies & Execution Order

- T006 first; T007–T011 follow in the core worker's order; T012 and T013
  after T007 (both measure through the rebuilt entry point).
- T014 is independent and runs in parallel from the start.
- T015 after T011 (it needs the removed build and final entry command).
- T016–T020 after T006–T015.

## Implementation Strategy

1. The core worker swaps backfire onto PyModel and removes what the user
   dropped, so the MVP is PyModel's server with backfire's providers.
2. The upstream worker prepares the PyModel patch in parallel.
3. The plugins worker then points the plugins and consumers at the result.
4. The coordinator finishes documents, checks and the merge.
