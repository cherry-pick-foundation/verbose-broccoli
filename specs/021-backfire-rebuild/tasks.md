---

description: "Task list for the backfire rebuild from jev-judge-mcp"
---

# Tasks: Backfire Rebuilt From jev-judge-mcp

**Input**: Design documents from `specs/021-backfire-rebuild/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: The spec requires tests: upstream equality of the tools
(SC-001), the vendored upstream tests (SC-002), a failing-before test for
each of CHE-37 and CHE-38 (FR-014), and the upstream-record check (SC-007).
Every code task includes its tests.

**Organization**: Main (Claude Code) owns the Spec Kit records, repository
prose, integration and commits, and reviews each Codex worker's diff. Codex
workers (`gpt-6-luna`, `max` effort, started through Orca's terminal path)
implement in disjoint file scopes: worker A (vendor), worker B (rebuild),
worker C (adapt) and worker D (load fixes). A fresh Claude Code reviewer
gives the develop merge review of the code; a fresh Codex reviewer reviews
the coordinator's records and documents.

**Private data**: No task writes a student name, a private backfire record
or evaluation data into the repository, Linear or Orca messages. No task
opens `$XDG_DATA_HOME/verbose-broccoli/backfire-eval/heldout-v1.jsonl`.
Billed provider calls happen only in T024.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Setup — the vendored upstream (worker A)

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

**Checkpoint**: `npm run test:backfire` passes with the old port still
serving, the vendored upstream tests included; `npm run verify` passes.

---

## Phase 2: User Story 1 — agents use the tools from the upstream (Priority: P1) 🎯 MVP (worker B, then worker C)

**Goal**: `backfire serve-mcp` serves the twelve tools of
[contracts/tools.md](contracts/tools.md) from the vendored upstream,
through backfire's judge.

**Independent Test**: start the server with a scripted provider, list the
tools, call each with synthetic input; compare definitions with the
upstream's and results with the upstream tool's for the same answers.

- [ ] T006 [US1] Add the provider seam of
  [contracts/provider-seam.md](contracts/provider-seam.md) in
  `packages/backfire/src/backfire/jev_provider.py` (the `JevProvider`
  subclass, the per-call context variable, the `Runtime` construction with
  `Settings.model_construct()`), with
  `packages/backfire/tests/test_jev_provider.py`: answers, usage and model
  pass through; `provider` is `compatible`; each judgment error type becomes
  the right upstream error with backfire's text; the deadline and record
  file come from the call context; cancellation propagates; no `JEV_*`
  variable changes behaviour (FR-006).
- [ ] T007 [US1] Add the registry in `packages/backfire/src/backfire/registry.py`
  (renamed copies of the eleven upstream tools, as
  [research.md](research.md) R3 decides) and rewrite `backfire_noul` onto
  the upstream framework in `packages/backfire/src/backfire/noul.py`, with
  `packages/backfire/tests/test_registry.py`: the list equals
  [contracts/tools.md](contracts/tools.md); each definition equals the
  upstream's after the mapping (compared with the vendored
  `jev_judge_mcp.tools` definitions); no `jev_<tool>` name appears in any
  listed definition or in any result or error text of the call corpus;
  `backfire_noul`'s definition, questions, labels, invalid-answer handling
  and budget error keep their current behaviour (FR-002, FR-003, FR-004).
- [ ] T008 [US1] Rewrite `packages/backfire/src/backfire/server.py` as
  [research.md](research.md) R5 and R6 decide: an `MCPServer` subclass
  (credited to PyModel's `JevMCPServer`), the `Toolset` from T007, the
  `Runtime` from T006, run inside `Boundary.run` over the vendored
  `stdio_streams()`; patch `packages/backfire/src/jev_judge_mcp/stdio.py`
  to read at most 10 MiB per line and end the session with
  `message_limit_exceeded` beyond it, and record the patch in
  `UPSTREAM.md`; remove `BoundedLineReader` from
  `packages/backfire/src/backfire/boundary.py`; keep
  `packages/backfire/src/backfire/__main__.py`'s commands and give its
  test hook a scripted provider instead of the scripted judge
  (`packages/backfire/tests/scripted_judge.py` or a successor). Adapt
  `test_server.py`, `test_server_faults.py`, `test_entry.py`,
  `test_boundary.py`, `test_boundary_core.py` and `test_lifecycle.py` in
  `packages/backfire/tests/` (FR-001, FR-009).
- [ ] T009 [US1] Remove the port: `packages/backfire/src/backfire/tools/`,
  `lib.py`, `patterns.py`, `backfire/UPSTREAM.md`,
  `packages/backfire/src/backfire_tools/acceptance/capture_upstream.py`,
  `scripts/backfire/fixtures/upstream-0.9.0/`, and the tests that cover
  only them (`test_tools_part1.py`, `test_tools_part2.py`, `test_lib.py`,
  `test_patterns.py`, `test_fidelity.py`, `test_capture_upstream.py`, and
  any other the impact graph shows); before each removal list its importers
  with `npm run workflow -- --task <id> --graph impact --file <path>` and
  remove or adapt each; move any still-needed shared helper next to its
  consumer (FR-016).
- [ ] T010 [US1] Adapt the remaining judgment and education tests in
  `packages/backfire/tests/` to the rebuilt server:
  `test_education_e2e.py`, `test_adapter_wiring.py`, `test_doubles.py`,
  `test_faults.py`, `test_deadline.py`, `test_load.py`,
  `test_pseudonymize_hook.py`, `fake_provider.py`; the provider sees only
  pseudonyms and results restore names; CHE-33's retries still apply
  through the tools (FR-006, FR-007).

**Checkpoint**: US1 works end to end with a scripted provider;
`npm run test:backfire` passes.

---

## Phase 3: User Story 2 — responsive and fair under load (Priority: P1) (worker D)

**Goal**: CHE-37 and CHE-38 fixed on the rebuilt server, each shown by a
test that fails first.

**Independent Test**: [quickstart.md](quickstart.md) step 3, before and
after each fix.

- [ ] T011 [US2] Write the CHE-37 test in
  `packages/backfire/tests/test_regex_executor.py` against the rebuilt
  server with the upstream process pool: when a matching process's start
  takes more than one second (for example a slowed spawn), a simple pattern
  such as `!` must still match; run it, and record the failing output in
  this file under T011 (FR-012, FR-014).
- [ ] T012 [US2] Pin `regex` 2026.9.29; add the regex-library executor in
  `packages/backfire/src/backfire/regex_executor.py` as
  [research.md](research.md) R7 decides (thread, `concurrent=True`, one
  second of `regex` timeout per field carried across searches, flags mapped
  by name, timeouts and compile errors mapped to the upstream results);
  patch `match_all` in
  `packages/backfire/src/jev_judge_mcp/extract/executor.py` to take its
  compile step as a parameter and record it; pass the executor through the
  `Runtime`. Extend `test_regex_executor.py`: T011's case passes;
  `(a|aa)+$` on 60 `a` and a `b` times out with the upstream reason; several
  runaway patterns in one call and in concurrent calls do not make a simple
  pattern time out; cancellation returns at once; the event loop keeps
  running during a runaway search (FR-012, SC-003).
- [ ] T013 [US2] Adapt `packages/backfire/tests/test_bounded_work.py` to the
  rebuilt server (twelve tools, `backfire_score` and `backfire_noul` cases,
  the extract case's runaway fields using patterns that run away under
  `regex`), keeping its 10 MiB messages and 1-second check; run it before
  any CHE-38 fix and record the failing `backfire_verify` case under T013
  (FR-013, FR-014).
- [ ] T014 [US2] Fix CHE-38: patch
  `packages/backfire/src/jev_judge_mcp/ids.py` for linear duplicate IDs
  with the same result (a test with 100,000 identical IDs checks IDs,
  order and linear time); profile each tool's bounded case and move every
  synchronous step over about 20 ms off the event loop, in the vendored
  files the profile names or in `backfire/server.py` and
  `backfire/boundary.py`; record each vendored patch. Then run the
  bounded-work test 3 times with 16 busy processes and the extract case 5
  times with 80, as [quickstart.md](quickstart.md) step 3 says, and record
  the worst stall per tool and the extract outcomes under T014 (FR-005,
  FR-013, SC-003, SC-004).

**Checkpoint**: both load fixes pass; the failing runs are recorded.

---

## Phase 4: User Story 3 — backfire's own services (Priority: P2) (worker C)

**Goal**: records, readiness and builds work with the rebuilt server.

**Independent Test**: the record, readiness and build tests pass.

- [ ] T015 [P] [US3] Update `packages/backfire/src/backfire/decisions.py` to
  the rebuilt tools' result fields and add `backfire_score`; adapt
  `test_decisions.py` and `test_records.py` in `packages/backfire/tests/`
  (record kinds, fields, budget and failure rules unchanged) (FR-008).
- [ ] T016 [P] [US3] Adapt `packages/backfire/src/backfire/ready.py` and
  `packages/backfire/tests/test_ready.py` to the rebuilt server, with no
  billed call in the tests (FR-010).
- [ ] T017 [P] [US3] Copy `jev_judge_mcp` into both builds in
  `packages/backfire/src/backfire_tools/build.py`, and extend
  `packages/backfire/tests/test_build.py` to check the license files and a
  started build's twelve tools (FR-011).
- [ ] T018 [US3] Check the workspace consumers: run
  `npm run test:doc-regions` and `npm run test:wiki-consistency`, and
  confirm the request limits in
  `packages/doc-regions/src/doc_regions/requests.py` and
  `packages/wiki-consistency/src/wiki_consistency/requests.py` still hold
  on the rebuilt tools; change them only if a limit no longer holds
  (FR-020).

**Checkpoint**: US3 passes; `npm run verify` passes.

---

## Phase 5: User Story 4 — the upstream record is complete (Priority: P2) (coordinator)

- [ ] T019 [US4] Check `packages/backfire/src/jev_judge_mcp/UPSTREAM.md`
  against every patch made in T008, T012 and T014 and every glue
  behaviour in [contracts/tools.md](contracts/tools.md) and
  [contracts/provider-seam.md](contracts/provider-seam.md); complete its
  "Behaviour differences outside the vendored files" section (FR-015).

---

## Phase 6: Polish and acceptance (coordinator)

- [ ] T020 [P] Update `docs/backfire.md` and `docs/architecture.md` for the
  rebuilt server (upstream, tools, `regex`, removed port), and regenerate
  generated references with `npm run docs:generate` if their inputs changed
  (FR-019).
- [ ] T021 [P] Check the backfire skills in
  `plugins/code/skills/backfire/` and `plugins/work/skills/backfire/`
  (`SKILL.md`, `reference/tools.md`, `references/verbose-broccoli.md`)
  against the rebuilt tools; correct each contradiction and record it in
  that skill's `upstream.json` `local_modifications`; add
  `backfire_score` where the reference lists tools (FR-019).
- [ ] T022 Run the document judgment step the develop merge review uses
  (as in earlier features' records) and resolve contradicted units.
- [ ] T023 Run `npm run verify` three times in a row without a rerun and
  record each result under T023 (SC-005).
- [ ] T024 Run the live check through the configured provider with at most
  15 billed calls (for example `npm run backfire:ready` and a few tool
  calls with synthetic input); record the number of billed calls and the
  outcome under T024 (SC-006).
- [ ] T025 Write the feature report in
  `specs/021-backfire-rebuild/report.md` (what changed, measurements,
  unperformed checks), commit it, move CHE-39 to In Review, get the develop
  merge review (fresh Claude Code reviewer for code, fresh Codex reviewer
  for records), resolve findings, add the review-record commit, merge
  `develop` into the branch and verify, confirm `develop` has not moved,
  run `git flow feature finish backfire-rebuild` from the `develop`
  worktree, move CHE-39 to Done with one completion comment, and report
  CHE-37 and CHE-38 as fixed to the develop session.

---

## Dependencies & Execution Order

- Phase 1 (T001–T005) blocks everything. T002 needs T001; T003 needs T001;
  T004 and T005 can follow T001 in any order.
- Phase 2: T006 and T007 can run together; T008 needs both; T009 needs
  T008; T010 needs T008 and T009.
- Phase 3 needs T008 and T009. T011 comes before T012; T013 comes before
  T014. The T011/T012 pair and the T013/T014 pair share only
  `backfire/server.py` changes, which belong to T014.
- Phase 4 needs T008 and T009 and can run in parallel with Phase 3;
  T015–T017 touch different files.
- Phase 5 needs Phases 2–4. Phase 6 needs Phase 5; T020–T022 can run in
  parallel with T019.

## Parallel Example

```text
After T009:
  worker C: T010, T015, T016, T017, T018   (tests and services)
  worker D: T011 → T012, then T013 → T014  (load fixes)
  coordinator: T020, T021 drafts
```

## Implementation Strategy

1. Phase 1 lands first and keeps the old port serving, so the vendored copy
   and its record are verified on their own.
2. Phase 2 swaps the server over in one step (MVP): the rebuilt tools with
   upstream behaviour, including the upstream process pool and quadratic
   IDs, so that Phase 3's tests can fail first against the rebuilt server.
3. Phases 3 and 4 run in parallel on disjoint files.
4. Phases 5 and 6 complete the record, documents and acceptance.

## Notes

- Commit with Conventional Commits and one `Spec-Kit-Task: Txxx` trailer
  per covered task; the coordinator reviews each worker's diff before it
  commits.
- Before editing, after scope changes and before completion, run
  `npm run workflow` with the task's `--task`, `--base` and `--plan`.
