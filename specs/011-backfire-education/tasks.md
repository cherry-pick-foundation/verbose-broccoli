---
description: "Task list for Backfire for Education Work"
---

# Tasks: Backfire for Education Work

**Input**: Design documents from `specs/011-backfire-education/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. AGENTS.md asks for tests with every code change, and
constitution V asks for positive, negative and boundary cases with synthetic
data.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete
  task)
- **[Story]**: The user story the task belongs to (US1, US2, US3)
- Paths are relative to the repository root.

## Conventions for Every Task

- Read `AGENTS.md` first and run `deno task workflow` before editing, as it
  says. Use `$HOME/.deno/bin/deno` when `deno` is not on `PATH`.
- Feature 005's rules for `packages/backfire/` still hold
  ([005 tasks](../005-jev-decision-backend/tasks.md#conventions-for-every-task)):
  the src layout, no provider names in code, and the offline suites run by
  `deno task test:backfire`.
- The code build's behavior must not change (FR-002): feature 005's offline
  tests keep passing unchanged, except where a task below names the test to
  update.
- Synthetic data only. No real student name, school, guardian or contact
  detail enters the repository, a test, a fixture, a log or a report.
- Workers do not edit `specs/`; they return results to the coordinator, who
  records them. Workers do not commit; the coordinator reviews each diff and
  commits it with one `Spec-Kit-Task: Txxx` trailer per covered task.
- **On demand** tasks make billed provider calls or run signed-in clients.
  They need the user's go-ahead and are never part of `deno task check`.
- Installing into saved client configuration needs the user's separate
  approval; this feature's client check registers per invocation only.

---

## Phase 1: Setup

**Purpose**: Dependencies and environment for both builds.

- [ ] T001 Add the optional extra `education = ["phonenumbers==9.0.40"]` to `packages/backfire/pyproject.toml`, add `backfire_education` and `backfire_education.*` to `[tool.setuptools.packages.find]` and its `config.toml` to package data, relock `packages/backfire/uv.lock` with the pinned uv, and change the `backfire:install` task in `deno.json` to `uv sync --project packages/backfire --frozen --extra education` (CI runs that task). Acceptance: `deno task backfire:install` succeeds and `phonenumbers` 9.0.40 imports in `packages/backfire/.venv`; `uv sync --frozen --no-dev` without the extra still installs the code build's set.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The per-plugin build and the judge hook that every story needs.

- [ ] T002 [P] Change `packages/backfire/src/backfire_tools/build.py` to `build <plugin> <output>` with the plugin table of [contracts/build.md](contracts/build.md): copy `plugins/<plugin>/`, then each listed package under `packages/backfire/src/` without `__pycache__/` and without its own `config.toml`, then write the row's profile source to `backfire/src/backfire/config.toml`; refuse an unknown plugin (including `chat`) before writing anything; keep every feature 005 build rule. Update `packages/backfire/tests/test_build.py`: the existing cases run with `code`; add cases for the work build's contents, the absence of `backfire_education/` and the education profile in a code build, the absence of the development profile in a work build, an unknown plugin, and the usage message. Update the build line in `deno.json`'s task description if it names the arguments.
- [ ] T003 [P] Add the judge hook of [contracts/pseudonymization.md](contracts/pseudonymization.md#place-in-the-judge) and [contracts/configuration.md](contracts/configuration.md): in `packages/backfire/src/backfire/config.py`, accept a top-level boolean `pseudonymize` only in the shipped file and reject it in the operator file with `backend_not_configured` naming that file, and expose the shipped value; in `packages/backfire/src/backfire/failures.py`, add `pseudonym_conflict` with the contract's message; in `packages/backfire/src/backfire/judge.py`, add the keyword `pseudonymize: bool | None = None` (None follows the shipped file), and when it is on, import `backfire_education.pseudonymize` (failure: `backend_not_configured` naming the shipped `config.toml`), run `pseudonymize(state, questions)` with `asyncio.to_thread` after request validation, send its state and questions to the adapter, apply its `restore` to the answers after answer validation, and keep writing the judgment record with the original state and questions. The module's interface is `pseudonymize(state, questions) -> (state, questions, restore)`, where `restore(answers: dict) -> dict` takes and returns the JSON form of the answers. Add tests in `packages/backfire/tests/test_pseudonymize_hook.py` with a stand-in module injected into `sys.modules`: the adapter receives the stand-in's output, the result carries the restored answers, the record digests the originals, a stand-in failure sends no provider request, `pseudonymize=False` skips it, and the operator file's `pseudonymize` is rejected.

**Checkpoint**: Both builds can be produced, and the judge can call a pseudonymization module.

---

## Phase 3: User Story 1 - Judge student records without revealing who they are about (Priority: P1) 🎯 MVP

**Goal**: A work build's judgments reach the provider with pseudonyms only, and
results come back with the agent's own text.

**Independent Test**: A built work server against feature 005's recording fake
provider, with a synthetic roster: no identifier in any request, restored
labels in results, stable pseudonyms, and every fail-closed case (quickstart
step 4).

- [ ] T004 [P] [US1] Implement `packages/backfire/src/backfire_education/roster.py`: read `education.toml` and the roster CSV as [contracts/configuration.md](contracts/configuration.md) and [contracts/pseudonymization.md](contracts/pseudonymization.md#roster) define, derive given names by the contract's rule, and return the identifier values by kind with the contract's precedence; every failure is `backend_not_configured` naming the path. Tests in `packages/backfire/tests/test_education_roster.py`: byte-order mark, extra columns, missing `name` column, empty name, non-UTF-8, relative roster path, unknown key, given names for three- and four-syllable names and compound surnames, no one-syllable given names, shared given names, non-Hangul names.
- [ ] T005 [P] [US1] Implement `packages/backfire/src/backfire_education/table.py`: the mapping table of [contracts/pseudonymization.md](contracts/pseudonymization.md#mapping-table), under `$XDG_DATA_HOME/verbose-broccoli/backfire/`, with the random key, HMAC-SHA256 digests, per-prefix counters, the `flock` on `pseudonyms.lock`, temporary-file-and-rename writes with mode `0600`, directory mode `0700`, the owner and mode checks and the 1 MiB budget. Tests in `packages/backfire/tests/test_education_table.py`: same pseudonym across reloads, distinct pseudonyms, numbers never reused, no identifier text in the file, two processes assigning at once without loss or duplicates, an interrupted write leaving the old table and no temporary file, the budget, a malformed table, and wrong mode or owner.
- [ ] T006 [US1] Implement `packages/backfire/src/backfire_education/pseudonymize.py` with `pseudonymize(state, questions)` per [contracts/pseudonymization.md](contracts/pseudonymization.md): detection with one longest-first expression of roster values, `phonenumbers.PhoneNumberMatcher(text, "KR")` and the contract's email expression; overlap resolution; replacement in every string and object key of the state and in each question's JSON form, rebuilt with its own class; `pseudonym_conflict` for colliding keys or labels; and `restore` for question keys, `choice`, `probabilities` keys and `legend` values. Tests in `packages/backfire/tests/test_education_pseudonymize.py`: particles, given names alone, longest match, overlaps, phone formats and non-phone numbers (dates, ranges, scores), emails, keys in nested state, each question type, conflicts, restoration of each answer type, pseudonym-like input sent as is, and no names in raised errors (depends on T004, T005).
- [ ] T007 [P] [US1] Add `packages/backfire/src/backfire_education/__init__.py` and `packages/backfire/src/backfire_education/config.toml` with `pseudonymize = true`, `provider = "education"` and `[providers.education]` holding the same values as `[providers.hive]` in `packages/backfire/src/backfire/config.toml`; update `packages/backfire/tests/test_no_provider_names.py` so the guard allows exactly the two shipped profile files.
- [ ] T008 [US1] Add `packages/backfire/tests/test_education_e2e.py`: build a work plugin into a temporary directory, install it offline with `uv sync --frozen --no-dev --extra education` the way feature 005's `packages/backfire/tests/test_load.py` installs built copies, and run its `backfire serve-mcp` over stdio with a temporary `XDG_CONFIG_HOME` and `XDG_DATA_HOME`, a synthetic roster, a test credential and feature 005's `FakeProvider` through `BACKFIRE_TEST_PROVIDER_BASE_URL`. Check that the server lists the eleven tools (FR-003) and that a roster edited between two calls takes effect at the second (FR-012). Cover SC-001 to SC-004 as [quickstart.md](quickstart.md#4-pseudonymization-against-a-recording-provider) lists them, with `backfire_classify`, `backfire_verify` and `backfire_find` calls whose labels or candidates name students (depends on T002, T003, T006, T007).

**Checkpoint**: User Story 1 works offline end to end.

---

## Phase 4: User Story 2 - Build a backfire server per plugin (Priority: P2)

**Goal**: The work plugin declares backfire and works alone; the code plugin is
unchanged; each plugin's provider can change on its own.

**Independent Test**: Quickstart steps 2 and 3, the plugin layout test, and the
profile-selection tests.

- [ ] T009 [P] [US2] Declare the `backfire` stdio server in `plugins/work/mcp.json` with the same command as `plugins/code/mcp.json`, and add Backfire to the description in `plugins/work/plugin.json`. Update `scripts/plugin_skills_test.ts` so the work plugin must declare `backfire`, and add a check that `plugins/work/skills/backfire/reference/tools.md` and `LICENSE` equal the code plugin's copies.
- [ ] T010 [P] [US2] Add tests in `packages/backfire/tests/test_education_selection.py` that load profiles with each build's shipped file: replacing `[providers.education]` in an operator file changes the work build's profile and not the code build's, replacing `[providers.hive]` does the reverse, a top-level `provider` line selects for both, and the work build reads its credential from `education.env`, including through a symbolic link to `hive.env`.
- [ ] T011 [US2] Coordinator: write `plugins/work/skills/backfire/` as a vendored copy of `plugins/code/skills/backfire/` (`SKILL.md`, `reference/tools.md`, `LICENSE`, `upstream.json`) whose data-handling bullet and `references/verbose-broccoli.md` state what the work build sends, what it replaces and cannot detect, and the advisory limits (FR-014), with `upstream.json` recording the local changes.

**Checkpoint**: Both plugins build, install and declare their own backfire.

---

## Phase 5: User Story 3 - Know how well judgments work on education tasks (Priority: P3)

**Goal**: A recorded two-arm measurement on synthetic education cases.

**Independent Test**: The runner's offline test, then one on-demand run.

- [ ] T012 [P] [US3] Write `scripts/backfire/fixtures/education-v1.jsonl` and `scripts/backfire/fixtures/education-roster-v1.csv` as [contracts/measurement.md](contracts/measurement.md#set) defines: synthetic Korean education cases with one clear expected result each, meeting every coverage rule there. The writer does not implement T006.
- [ ] T013 [P] [US3] Implement `packages/backfire/src/backfire_tools/acceptance/measure_education.py` as [contracts/measurement.md](contracts/measurement.md#runner) defines, and test it offline in `packages/backfire/tests/test_measure_education.py` with a scripted judge: output lines, per-tool and per-arm accuracy, failed calls counted as wrong, differing cases listed, the temporary directory removed on success, failure and interruption, and the key only ever linked, never copied (depends on T003).
- [ ] T014 [US3] On demand, after the user's go-ahead and after T012 is committed: run the measurement with `--runs 3` and return its output to the coordinator, who records the summary in [research.md](research.md#results) (depends on T006, T012, T013).

**Checkpoint**: The measurement is recorded.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T015 [P] Coordinator: update `docs/backfire.md` for the per-plugin build command and the work build's setup (`education.env`, `education.toml`, the roster CSV, the mapping table), what the work build sends and replaces, what it cannot detect, the user's step of turning off training in the Claude and ChatGPT account settings, the rule against private personal records narrowed to the code build, profile selection per plugin, and the `pseudonym_conflict` row.
- [ ] T016 [P] Coordinator: update `docs/architecture.md`'s Backfire section for the per-plugin build and the `backfire_education` package.
- [ ] T017 [P] Coordinator: add `phonenumbers` 9.0.40 (Apache-2.0) and the work plugin's copy of the jev skill to `licenses/THIRD_PARTY_NOTICES.md`.
- [ ] T018 [P] Coordinator: mark FR-015 and the student-data assumption in `specs/005-jev-decision-backend/spec.md` as superseded by feature 011 (FR-015 of 011).
- [ ] T019 Run `deno task docs:generate` and commit the regenerated `docs/reference/` files (depends on T009).
- [ ] T020 On demand, after the user's go-ahead: the client check of [quickstart.md](quickstart.md#5-client-check-live-with-the-users-go-ahead) in Codex CLI and Claude Code (SC-006). Also find out, from each client's documentation or a per-invocation run, how it names two servers called `backfire` from two plugins, and record it as unverified if only an installation could show it; return the outcomes to the coordinator for [research.md](research.md#results) (depends on T008, T009, T011).
- [ ] T021 Coordinator: scan the repository for the ten names and schools of the operator's EduOK list without writing them anywhere, and record only the outcome in [research.md](research.md#results) (SC-008).
- [ ] T022 Run quickstart steps 1 to 4, `deno task test:backfire-slow`, `deno task check` and `deno task verify`, and report the results (depends on every task above except T014 and T020).

---

## Dependencies & Execution Order

- T001 first. T002 and T003 depend on T001 and can run in parallel.
- US1: T004, T005 and T007 in parallel after T001; T006 after T004 and T005;
  T008 after T002, T003, T006 and T007.
- US2: T009 and T010 after T002 and T007; T011 any time after T001.
- US3: T012 any time; T013 after T003; T014 after T006, T012 and T013, with
  the user's go-ahead.
- Polish: T015 to T018 any time; T019 after T009; T020 after T008, T009 and
  T011; T022 last.

## Parallel Example: first wave

```text
Worker A: T001, then T002 and T003 (packages/backfire/pyproject.toml, uv.lock, deno.json, backfire/config.py, failures.py, judge.py, backfire_tools/build.py, their tests)
Worker B: T004, T005, T007, then T006 (packages/backfire/src/backfire_education/, its tests, test_no_provider_names.py)
Worker C: T012 (scripts/backfire/fixtures/education-*)
Coordinator: T011, T015 to T018
```

## Implementation Strategy

1. MVP: Phases 1 to 3, which make the work build safe and testable offline.
2. Then User Story 2's declarations and skill, so the work plugin is complete.
3. Then the documentation, the on-demand client check and the measurement,
   each with the user's go-ahead.
