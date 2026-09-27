---
description: "Task list for the Jev-style decision backend of the code plugin"
---

# Tasks: Jev-Style Decision Backend for the Code Plugin

**Input**: Design documents from `specs/005-jev-decision-backend/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/),
[quickstart.md](quickstart.md)

**Tests**: Requested. The spec's acceptance scenarios and success criteria,
constitution V and the plan's testing layers require them. Tests come with
their code: pytest suites through `uv run --frozen`, run by
`deno task test:backfire`. Offline tests run in `deno task check`; live tests
run only on demand.

**Organization**: Setup and the first gates, then the foundational backend with
its gates, then one phase per user story, then polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete
  task)
- **[Story]**: The user story the task belongs to (US1, US2, US3)
- Paths are relative to the repository root.

## Conventions for Every Task

- Use `$HOME/.deno/bin/deno` when `deno` is not on `PATH`.
- A **gate** task or an on-demand run reports its evidence to the coordinator,
  who records it in [research.md](research.md) under a dated heading; where a
  task says to record something in research.md, the worker returns it and the
  coordinator writes it, because research.md is a shared file. A failed gate
  stops every task that depends on it
  ([Dependencies](#dependencies--execution-order)) until the plan is revised.
- backfire is one Python package ([research.md](research.md#python-package--2026-09-27)).
  The ported tools keep `jev-mcp` 0.9.0's behavior except for the recorded
  differences that `packages/backfire/src/backfire/UPSTREAM.md` lists; any
  other difference is a defect, and the fidelity suite (T030) guards it. The
  MCP server uses the official MCP Python SDK (`mcp`), pinned in `uv.lock`.
- All backfire code lives in `packages/backfire/`, a standard Python project
  with the src layout: the runtime package `src/backfire/`, the unshipped
  development and release programs in `src/backfire_tools/`, and the pytest
  suites in `tests/`; only the evaluation fixtures live in
  `scripts/backfire/fixtures/`.
  The repository has no `plugins/code/backfire/`; a code plugin that contains
  the component exists only as the output of `deno task backfire:build` (T068).
- No file under `packages/backfire/src/` other than
  `src/backfire/config.toml` names a provider; provider-specific values
  belong in a provider profile, one `[providers.<name>]` table of `config.toml`
  ([contracts/provider-profile.md](contracts/provider-profile.md)); there is no
  file per provider.
- **On demand** tasks need network access and provider credit, and some need
  signed-in Codex CLI and Claude Code; they are never part of
  `deno task check`.
- Installing into saved client configuration and posting upstream issues need
  the user's separate approval.
- FR-001 and SC-008 also depend on a separate client-installation feature;
  this feature's client runs use per-invocation registration, except T062,
  which runs against the installed package once that feature has passed.

---

## Phase 1: Setup and First Gates

**Purpose**: Seal the held-out set before any implementation, confirm the
selected provider profile's settings, create the component scaffolding and its
build, and prove its packaging.

**⚠️ T001 must finish before any task from T003 on starts.**

- [X] T001 Gate 1: as a worker who will not implement this feature, write the held-out general set `heldout-v1` to `$XDG_DATA_HOME/verbose-broccoli/backfire-eval/heldout-v1.jsonl` (at least ten cases per tool and four per language, English and Korean, synthetic, exactly one decision unit per case, in the case format of [contracts/evaluation.md](contracts/evaluation.md#case-format)), and commit only `scripts/backfire/fixtures/heldout-v1.seal.json` with its SHA-256, case count and per-tool and per-language counts. Implementers never open the data file.
  - 2026-09-27 handoff: a non-implementing worker wrote the data file (110 cases, 10 per tool, 5 per tool and language) and the seal. The coordinator checked the seal's SHA-256 and counts against the data file without reading its content, and committed the seal with the case format in research.md ("Evaluation expectations") and contracts/evaluation.md. Next: T041 verifies the seal before the first held-out run.
- [X] T002 [P] Gate 2, settings part (on demand): write `packages/backfire/src/acceptance/probe_provider.ts` and `packages/backfire/src/backfire_backend/config.toml` holding `provider = "hive"` and the `[providers.hive]` table of [contracts/provider-profile.md](contracts/provider-profile.md#format). The probe reads a `config.toml` with `@std/toml`, takes the provider named on its command line or else the file's `provider`, reads that table's `credential` variable from `$XDG_CONFIG_HOME/verbose-broccoli/backfire/<name>.env`, and sends to `<base_url>/chat/completions` of a profile whose `api` is `openai` one request with the profile's `model` and `request` fields, one with an invalid key and one with an unknown model, plus a burst above the profile's `rate_limit_per_second`, or no burst, reported as not applicable, when the profile has none; it prints only statuses, the response model, the thinking evidence the profile names and token counts, and names no provider in its code. Run it with the `hive` profile, and record in [research.md](research.md#hive-request-behavior--2026-09-26) which of 200, 401, 400 and 429 were observed; 405 stays documented-only and is covered offline by T049. The benchmark part of gate 2 is T058.
  - 2026-09-27 handoff: the probe now reads one `config.toml` (shipped `provider = "hive"` with a `[providers.hive]` table using `reasoning_effort = "medium"`), `profiles/` is gone, and the rerun is recorded in research.md ("Gate 2 probe, settings part"). Reviewed by the coordinator and committed after T008.
- [X] T003 Copy `src/index.ts`, `src/lib.ts`, `src/provider.ts`, `package.json` and `LICENSE` of `jkudish/jev-mcp` at revision `a1fcc1e47fc696614f081e23a66ff48a890f22fd` unchanged into `packages/backfire/src/upstream/`, check their SHA-256 against the table in [research.md](research.md#tool-source-jev-mcp-090-copied--2026-09-26), and write `packages/backfire/src/upstream/upstream.json` with the source URL, revision, license and each file's original SHA-256.
- [X] T004 [P] Apply recorded changes 1 to 3 and 7 to `packages/backfire/src/upstream/src/index.ts`: import `./lib.ts` and `./provider.ts`; open the regex worker source with `const { parentPort, workerData } = require("node:worker_threads");`; export `server` and remove the final `server.connect(new StdioServerTransport())`, its ready log line and the unused `StdioServerTransport` import; and apply change 7: name the server `backfire` and the eleven tools `backfire_<suffix>` in registrations, the results' `tool` field, descriptions and error messages, leaving comments unchanged. Change nothing else.
- [X] T005 [P] Apply recorded change 4 to `packages/backfire/src/upstream/src/lib.ts`: `ensureUniqueIds` keeps the next suffix per base id so that shared ids take linear time, with identical ids and order. Add `packages/backfire/src/server/upstream_lib_test.ts`, which compares the result with the original function (kept inside the test) on duplicate-id inputs and checks that 100,000 items sharing one id finish within one second.
- [X] T006 [P] Apply recorded change 5, and change 1's import of `./lib.ts`, to `packages/backfire/src/upstream/src/provider.ts`: keep the compatible-endpoint branch (lines 331 to 382 at the revision) and the helpers it calls, remove the TypeSafe, Vercel, OpenRouter and Cloudflare branches and the `@jkudish/jev-agent-tools` import, and make provider resolution require `JEV_PROVIDER=compatible` with `JEV_API_BASE_URL` and `JEV_API_KEY`, keeping the upstream error text for a missing variable.
- [X] T007 Record the diff of changes 1 to 5 and 7 in `packages/backfire/src/upstream/upstream.json` and add `packages/backfire/src/server/upstream_record_test.ts`, which recomputes each copied file's diff against the recorded originals and fails when a file differs from its record or a file is added or removed (depends on T004 to T006).
- [X] T008 [P] Create `packages/backfire/deno.json` with `nodeModulesDir: "none"` and imports pinned exactly: `@modelcontextprotocol/sdk/` to `npm:/@modelcontextprotocol/sdk@1.30.1/`, `zod` to `npm:zod@4.6.5`, `@typesafe-ai/sdk` to `npm:@typesafe-ai/sdk@0.6.0` and `canonicalize` to `npm:canonicalize@5.0.0`, plus the `@std` modules the server, the build and the acceptance tooling need, including `@std/toml` for the probe; the package does not join the root Deno workspace; generate `packages/backfire/deno.lock` with Deno's default minimum dependency age left on.
  - 2026-09-27 handoff (T003 to T008): a worker, restarted once after an Orca restart, pinned `packages/backfire/deno.json` and `deno.lock` (plus `diff` 8.0.4 for the guard test), copied the five upstream files with matching hashes, applied changes 1 to 5 and 7 (change 1 also covers `provider.ts`), and added both tests, which pass; the coordinator reviewed the diffs. Open for T013: `deno check` reports 135 type errors in the copied `index.ts`, to be passed or excluded with the reason recorded.
- [X] T009 [P] Create the endpoint project: `packages/backfire/pyproject.toml` (package `backfire_backend` under `src/`, `system-one-adapter[openai]==0.2.1`, Starlette, Uvicorn, and pytest as a development dependency), `packages/backfire/.python-version` with `3.14.4`, and `packages/backfire/uv.lock` that pins `typesafe-sdk` 0.7.1.
- [X] T010 Create `packages/backfire/src/bin/backfire` (POSIX `sh`) with the commands of [contracts/mcp-server.md](contracts/mcp-server.md#entry-commands): it finds the component root from its own path, two levels up, so it runs the same from `packages/backfire/` and from a built plugin's `backfire/`; it depends on no inherited variable, resolving `PATH`, `HOME` and the XDG directories and finding `deno` and `uv` as [contracts/mcp-server.md](contracts/mcp-server.md#runtime-requirements) describes; it checks `deno` 2.9.6 and `uv`; `install` first removes environments whose recorded component root no longer exists, then runs `uv sync --frozen` for the component's Python project into this copy's environment `$XDG_CACHE_HOME/verbose-broccoli/backfire/venv/<copy id>/`, records the component root in its `component-root` file, and runs `deno install --frozen` with the component's `deno.json` ([contracts/mcp-server.md](contracts/mcp-server.md#entry-commands)); `serve-mcp` and `ready` use that environment and run the component's `src/server/main.ts` and `src/server/ready.ts` with `--frozen --cached-only` and the narrowest permissions that pass the tests, and exit non-zero with a message naming `src/bin/backfire install` when the environment or cached modules are missing (depends on T008, T009).
- [X] T011 [P] Update the repository configuration: `biome.json` excludes `packages/backfire/src/upstream`, which also removes it from the Clean Code file selection (`scripts/workflow_files.ts` reuses Biome's exclusions); `deno.json` adds the tasks `backfire:build` (running `packages/backfire/src/build.ts`), `backfire:install` and `backfire:ready` (calling `packages/backfire/src/bin/backfire`), `backfire:eval` (running `packages/backfire/src/acceptance/evaluate.ts`), `test:backfire` (the component's `deno test` with its own config over `packages/backfire/src/` except `deadline_test.ts`, then `uv run --frozen pytest` in `packages/backfire`, whose default project environment `packages/backfire/.venv/` is the test environment) and `test:backfire-slow` (only `deadline_test.ts`), adds `test:backfire` to the `test` dependencies, grants the docs tasks read access to any new documented inputs, and adds `.venv/` to `.gitignore`. Both test tasks run offline after the preparation that T037 names; a missing environment fails with a message naming that preparation.
  - 2026-09-27 handoff (T009 to T011): workers wrote the Python project (setuptools 80.9.0, exact pins, typesafe-sdk held at 0.7.1, config.toml as package data), the entry script and the repository tasks; a follow-up made test:backfire and test:backfire-slow parse under Deno's task shell and added a test that runs them. The coordinator changed run_entry to exec Deno so the server receives SIGTERM and SIGINT (reviewed by a Codex worker). Open: serve-mcp and ready use a first narrow permission set that T013 and T051 adjust; the docs tasks also allow `$HOME/.deno/bin/deno` because Orca's shells miss `~/.deno/bin` (a `~/.bash_profile` fix awaits the user's approval); test:backfire-slow waits for T034.
- [ ] T012 [P] Add sections to `licenses/THIRD_PARTY_NOTICES.md` for the copied `jev-mcp` 0.9.0 source (MIT, revision, the seven recorded changes and where `upstream.json` records them), the vendored `backfire` skill (MIT, from upstream `skills/jev`) and `system-one-adapter` 0.2.1 (MIT).
  - 2026-09-27 handoff: the `jev-mcp` source and `system-one-adapter` sections are committed with the `packages/backfire/` paths. Next: add the skill's section when T040 vendors it.
- [X] T063 Write the distribution build `packages/backfire/src/build.ts` per [contracts/mcp-server.md](contracts/mcp-server.md#distribution-build), reusing `@std/fs` for walking and copying: `deno task backfire:build -- <output>` refuses an existing `<output>` and any `<output>` inside `plugins/` or `packages/`; writes into a sibling `<output>.partial-<random>` within the 16 MiB budget; copies `plugins/code/` unchanged and the listed runtime files of `packages/backfire/` to `backfire/` with their relative paths; never writes a link; renames the partial directory to `<output>` on success and prints the path; and removes only its partial directory on failure, SIGINT or SIGTERM. Tests: `packages/backfire/src/build_test.ts` builds into a temporary directory and checks that everything outside `<output>/backfire/` equals `plugins/code/`; that `<output>/backfire/` holds `src/bin/backfire` and every listed runtime file present in the package, and no `*_test.ts`, `src/server/testing/`, `src/acceptance/`, `build.ts`, `tests/` or `__pycache__/`; that the output holds no link; that an existing output and an output inside `plugins/` are refused; that a build exceeding a lowered test budget and a build sent SIGTERM while it runs both leave neither `<output>` nor a partial directory; and that the repository has no `plugins/code/backfire/` (depends on T003, T010, T011).
  - 2026-09-27 handoff: a worker wrote `build.ts` (132 lines over `@std/fs`) and six tests, including a rejected source link, the rule the coordinator added to the contract; the coordinator reviewed it and built a plugin (all runtime files present, everything else equal to `plugins/code/`, no links). Next: T013.
- [X] T013 Gate 4, packaging, in two parts. The fresh-cache install run is on demand and needs network access, and its outcome is reported for research.md: build the code plugin with `deno task backfire:build` into a temporary directory outside the repository; with `DENO_DIR` and `XDG_CACHE_HOME` pointing at empty temporary directories, run the built `backfire/src/bin/backfire install`; show that `deno install --frozen` succeeds from the built copy of `deno.lock` under Deno's default minimum dependency age and that `uv sync --frozen` installs Python 3.14.4 and the lock. The offline part: write the first `packages/backfire/src/server/main.ts`, which imports the copied `server` and connects it to the SDK's stdio transport; add `packages/backfire/src/server/load_test.ts`, which builds the plugin into a temporary directory, runs that copy's `backfire/src/bin/backfire install` offline (`UV_OFFLINE=1`) from the caches that T037's preparation fills, runs its `serve-mcp` (and so `--cached-only`) under an empty environment (`env -i`) with the transport environment of [contracts/mcp-server.md](contracts/mcp-server.md#session-lifecycle) and any port, checks the server version that the copied source reads from `package.json` through `createRequire`, lists eleven tools over stdio, checks that the built copy's environment imports `backfire_backend` from the built copy and stays unchanged after `packages/backfire/src/bin/backfire install` and after removing another built copy, and removes its copies and their environments at the end; run `deno check` on the copied files and either pass it or exclude them from type checking with the reason recorded (depends on T007, T010, T063).
  - 2026-09-27 handoff: a worker wrote the first `main.ts` and `load_test.ts` and ran the fresh-cache install; the coordinator reviewed them and recorded gate 4 and the type-check exclusion of the copied `index.ts` in research.md ("Gate 4, packaging"). No launcher permission change was needed. Phase 1 is complete; next are the Phase 2 tracks.

Tasks T003 to T008, T013 and T063 were completed in TypeScript on 2026-09-27
and are superseded by Phase 1b, which removes that code (T064); T002, T009,
T010 and T011 are reworked there for the Python package, and the coordinator
revises T012's notices when the port lands.

**Checkpoint**: Held-out set sealed, the `hive` profile's settings confirmed,
the build and its packaging proven.

---

## Phase 1b: Python Package

**Purpose**: Replace the TypeScript component with one Python package on the
official MCP Python SDK, port the eleven tools, and prove the packaging again
([research.md](research.md#python-package--2026-09-27)).

- [X] T064 Replace the TypeScript component with the Python package skeleton: delete `packages/backfire/deno.json`, `deno.lock`, `src/upstream/`, the TypeScript files of `src/server/`, `src/build.ts`, `src/build_test.ts` and `src/acceptance/*.ts`; rename the package `backfire_backend` to `backfire`, moving `__init__.py` and `config.toml` to `packages/backfire/src/backfire/`, and add the empty package `packages/backfire/src/backfire_tools/` with its subpackage `acceptance/`; in `pyproject.toml` name the project `backfire`, find both packages under `src/`, pin `mcp==2.2.0` (the official MCP Python SDK), `rfc8785==0.1.4` and `system-one-adapter[openai]==0.2.1`, drop Starlette and Uvicorn, keep the `typesafe-sdk` 0.7.1 constraint, relax `[tool.uv] required-version` to `>=0.11.32`, ship `config.toml` and `UPSTREAM.md` as package data, and regenerate `uv.lock`; remove the Biome exclusion of `packages/backfire/src/upstream`; update `packages/backfire/tests/test_package.py` to check the pinned versions of `mcp`, `rfc8785`, `system-one-adapter` and `typesafe-sdk`. In the same task, update the root `deno.json` tasks for the Python package, running code through `uv run --project packages/backfire --frozen --offline --no-sync`, which keeps the repository root as the working directory: `backfire:build` runs `python -m backfire_tools.build`; `backfire:eval` runs `python -m backfire_tools.acceptance.evaluate`; `backfire:ready` runs `backfire ready`; `backfire:install` runs `uv sync --project packages/backfire --frozen`, which also installs the test tools; `test:backfire` drops the Deno steps, keeps a missing-preparation message that names `deno task backfire:install`, and runs the pytest suites except those marked `slow`; `test:backfire-slow` runs only the `slow` suites; regenerate `docs/reference/` with `deno task docs:generate`; `backfire:build`, `backfire:ready` and `backfire:eval` work once T068, T066 with T051, and T041 add their modules. Afterwards no `.ts` file and no `src/upstream/` remain under `packages/backfire/`, and `deno task verify` passes.
  - 2026-09-27 handoff: a Codex worker removed the TypeScript component, renamed the package `backfire`, pinned `mcp` 2.2.0 and `rfc8785` 0.1.4, relaxed uv to `>=0.11.32` and switched the root tasks to uv; the coordinator reviewed it and revised the jev-mcp and adapter notices. Next: T065, T066 and T069 in parallel.
- [X] T065 [P] Port T002's probe to `packages/backfire/src/backfire_tools/acceptance/probe_provider.py`, reading `packages/backfire/src/backfire/config.toml` with the standard library's `tomllib`, with unchanged behavior and printed fields; tests in `packages/backfire/tests/test_probe_provider.py`; run it once live and report the output for research.md (depends on T064).
  - 2026-09-27 handoff: a Codex worker ported the probe with 45 offline tests and ran it once live (200, 401, 400, 429); the coordinator reviewed it and recorded the run in research.md. Next: nothing; T058 is the benchmark part of gate 2.
- [X] T066 [P] Replace the `sh` launcher with the standard entry of [contracts/mcp-server.md](contracts/mcp-server.md#entry-commands): delete `packages/backfire/src/bin/`; add the console command `backfire` to `pyproject.toml`'s `[project.scripts]` and write `packages/backfire/src/backfire/__main__.py` with the `serve-mcp` and `ready` subcommands, which fail with a clear "not implemented yet" message until T072 and T051 fill them, so that `backfire` and `python -m backfire` run the same code. Tests: `packages/backfire/tests/test_entry.py` runs `uv run --frozen --offline --no-sync backfire --help` and `python -m backfire --help` in `packages/backfire/` and checks both list the two subcommands (depends on T064).
  - 2026-09-27 handoff: a Codex worker added the `backfire` console command with placeholder `serve-mcp` and `ready` subcommands and removed `src/bin/`; the coordinator reviewed it. Next: T072 and T051 fill the subcommands.
- [X] T067 Merged into T064 on 2026-09-27: T064 removes the files the old tasks ran, so it also switches the tasks and `deno task verify` passes after it.
- [X] T068 [P] Write the distribution build `packages/backfire/src/backfire_tools/build.py` per [contracts/mcp-server.md](contracts/mcp-server.md#distribution-build) with the standard library, replacing T063's TypeScript build, and its tests in `packages/backfire/tests/test_build.py` with the checks T063 lists, adapted to the Python file list (depends on T064, T066).
  - 2026-09-27 handoff: a Codex worker wrote the standard-library build with 22 tests carrying over T063's checks and built a plugin once by hand through `deno task backfire:build`; the coordinator reviewed it. Next: T072 installs and serves built copies.
- [X] T069 Port `jev-mcp` 0.9.0's `src/lib.ts` to `packages/backfire/src/backfire/lib.py`, with `ensure_unique_ids` in linear time and a test that compares it with the original quadratic function (kept inside the test) and runs 100,000 items sharing one id within one second; write `packages/backfire/src/backfire/patterns.py`, which runs a pattern with Python `re` in a child process killed after 1,000 ms, the child also ending itself with a timer at that limit; define the judge interface ([contracts/judgment.md](contracts/judgment.md#request)): `state` and `questions`, the caller's deadline, and the session's record file when the caller is a tool, with a scripted stand-in for tests; and write `packages/backfire/src/backfire/UPSTREAM.md` with the source, the revision, the original SHA-256 of `src/index.ts` and `src/lib.ts` from research.md, the license and the recorded differences. Tests: `packages/backfire/tests/test_lib.py` and `test_patterns.py` (depends on T064).
  - 2026-09-27 handoff: a Codex worker ported `lib.ts` (2,274 helper cases and 32 constants match upstream), wrote the pattern child, the judge interface, the scripted stand-in and `UPSTREAM.md`; the coordinator reviewed it, captured upstream's `tools/list` and error texts from a local 0.9.0 build, and recorded difference 4 and the shared tool-module shape. Next: T068, T070 and T071.
- [X] T070 [P] Port the tools `jev_verify`, `jev_screen`, `jev_noul`, `jev_find`, `jev_classify` and `jev_decide` from `jev-mcp` 0.9.0's `src/index.ts` into `packages/backfire/src/backfire/tools/` (one module per tool) as `backfire_<suffix>`, keeping each description, input schema (as the JSON Schema that `tools/list` publishes), question design, decision logic, result format and error text, with the judge interface of T069. Every tool module, in both T070 and T071, has the same shape, which T072 registers: `NAME`, `TITLE`, `DESCRIPTION`, `INPUT_SCHEMA` and `EXECUTION` as upstream's `tools/list` publishes them after the name mapping, and `async def call(arguments, judge, *, deadline, record_file)`, which receives validated arguments and returns `(text, is_error)` as upstream's handler returns its content, raising an exception whose message is the tool error text where upstream throws. T070 also writes `packages/backfire/src/backfire/tools/__init__.py`, which holds only `text(payload)`, upstream's `JSON.stringify(payload, null, 2)` with every number written as ECMAScript writes it (through `rfc8785`, as `lib.py` does). Tests: `packages/backfire/tests/test_tools_part1.py` with the scripted judge (depends on T069).
  - 2026-09-27 handoff: a Codex worker ported six tools with `tools/__init__.py` (`text`) and `tools/answers.py` (shared answer checks and the `provider` and `model` constants); 48 cases captured from a local 0.9.0 build match except for recorded difference 5; the coordinator reviewed it. Next: T072 registers the tools.
- [X] T071 [P] Port the tools `jev_rerank`, `jev_compare`, `jev_extract`, `jev_review` and `jev_gate` the same way into `packages/backfire/src/backfire/tools/`, with `backfire_extract` running its patterns through `patterns.py` and describing them as Python regular expressions (recorded difference 1). Tests: `packages/backfire/tests/test_tools_part2.py`, including the four `backfire_extract` cases (depends on T069).
  - 2026-09-27 handoff: a Codex worker ported five tools; 91 cases captured from a local 0.9.0 build match exactly; the coordinator reviewed it and made the `backfire_extract` pattern description self-contained. Next: T072 registers the tools.
- [X] T072 Gate 4, packaging, for the Python package: write `packages/backfire/src/backfire/server.py` and fill `__main__.py`'s `serve-mcp`, which serves the eleven tools on the MCP Python SDK's low-level stdio server as the server `backfire` with the package's version, registering each tool module of T070 and T071, checking each call's arguments against its `INPUT_SCHEMA` with `jsonschema` (pinned directly in `pyproject.toml` at the locked version) and answering invalid arguments with the tool error of recorded difference 4, and turning an exception from `call` into a tool error with its message, as upstream's SDK does; add `packages/backfire/tests/test_load.py`, which builds the plugin into two temporary directories with `backfire_tools.build`, installs each copy offline (`uv sync --frozen --no-dev` with `UV_OFFLINE=1`) from the prepared caches, starts one copy with the `uv` command of [contracts/mcp-server.md](contracts/mcp-server.md#declaration) under an empty environment (`env -i`, `uv` given by its absolute path), checks the server name and version and the eleven tool names, checks that each copy's `.venv` imports `backfire` from its own copy and still does after the other copy is removed, and checks that after installing and one served session a copy differs from the build output only in `.venv/` and `__pycache__/` directories under `src/backfire/` ([contracts/configuration.md](contracts/configuration.md#never-written)); and, on demand, install a built copy with an empty uv cache (`UV_CACHE_DIR`) and uv Python directory (`UV_PYTHON_INSTALL_DIR`), showing that `uv sync --frozen --no-dev` provides Python 3.14.4 and installs the lock. Report both parts for research.md (depends on T066, T068, T070, T071).
  - 2026-09-27 handoff: a Codex worker wrote the low-level MCP server with the argument check, `serve-mcp` with a placeholder judge, and the load test, and ran the fresh-cache install; the coordinator reviewed it, approved `egg_base = ".venv"` and recorded gate 4 in research.md. Phase 1b is complete; next is Phase 2 (T014 to T016, T021, T022 and T023 in parallel).

**Checkpoint**: The Python package serves the eleven ported tools from a built
plugin, and its packaging is proven.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The judge, the MCP boundary and records, the test doubles, and the
gates that prove them. Every user story needs this backend.

**⚠️ No user story work can begin until this phase and its gates pass.**

### Judge (Python)

- [X] T014 [P] Implement `packages/backfire/src/backfire/config.py`: the XDG paths of [contracts/configuration.md](contracts/configuration.md); the profile selection and loading of [contracts/provider-profile.md](contracts/provider-profile.md) (TOML read with the standard library's `tomllib`: the shipped `config.toml`, and the operator's `config.toml` whose `provider` replaces the shipped selection and whose provider tables add or replace shipped tables whole; every key rule; the not-supported-yet failure for `api = "anthropic"`; and the test-only `BACKFIRE_TEST_PROVIDER_BASE_URL`); raise `requires-python` in `pyproject.toml` to `>=3.11`, since `tomllib` needs it, and regenerate `uv.lock`; and the credential check of the selected profile's `<name>.env` (file present, non-empty, mode exactly 0600, owned by the operator, holding the profile's `credential` variable). Each failure yields `backend_not_configured` with a message naming the path or profile. Tests: `packages/backfire/tests/test_config.py`, including a second, test-only provider table in an operator `config.toml` under a temporary `XDG_CONFIG_HOME`; an absent operator file, which leaves the shipped selection; an operator table that replaces a shipped table whole; invalid files, selections and tables, including an unknown top-level key, a selection naming no configured provider and one with `api = "anthropic"`; and `packages/backfire/tests/test_no_provider_names.py`, which fails when any file under `packages/backfire/src/` other than `src/backfire/config.toml` contains `hive`, ignoring case, other than inside the word `archive` (depends on T064).
  - 2026-09-27 handoff: a Codex worker wrote `load_profile()`, `load_credential(profile)` and `xdg_path(kind)` with 125 tests and raised the Python floor to 3.11; the coordinator reviewed it, limited `statuses` keys to 400-599 in provider-profile.md and aligned the T065 probe. Next: T017 and T018 use them.
- [X] T015 [P] Implement `packages/backfire/src/backfire/failures.py`: the error types and fixed messages of [contracts/judgment.md](contracts/judgment.md#errors), the mapping from the TypeSafe SDK's error classes to those types, with the selected profile's `statuses` overrides applied first, and the SDK's `RetryPolicy` of [contracts/judgment.md](contracts/judgment.md#retries-and-time) (429 and statuses the profile maps to `rate_limited`, plus connect-phase failures only, at most four attempts, `Retry-After` within the time left). Tests: `packages/backfire/tests/test_failures.py`, with the overrides in the shipped `config.toml`'s `[providers.hive]` table (405 is `balance_exhausted` and fails at once) and a different override given in the test, which maps a status to `rate_limited` and is retried (depends on T064).
  - 2026-09-27 handoff: a Codex worker wrote `JudgmentError(error_type, detail=None)`, `map_error` and `retry_policy` with 84 tests; the coordinator reviewed it, limited profile status overrides to 400-599 and recorded the `detail` rule in judgment.md. Next: T017 and T018 use them.
- [X] T016 [P] Implement `packages/backfire/src/backfire/validate.py`: answer checks without rescaling (sums within `0.01 + 1e-12`, all-zero rejection, both placeholder fallbacks rejected, a returned 0.5 kept) and the request limits (option limit 150 and a provisional cell limit of 300, the 60-item, five-class request that passed on 2026-09-26, until T036 sets both), failing before any provider call. Tests: `packages/backfire/tests/test_validate.py`, including the Score values of [research.md](research.md#answer-validation-without-rescaling--2026-09-26) (depends on T064).
  - 2026-09-27 handoff: a Codex worker wrote `validate_request` (the adapter's question schema plus the provisional limits) and `validate_answers` with 61 tests; the coordinator reviewed it and noted the private adapter import in research.md. Next: T018 calls both; T036 sets the final limits.
- [X] T017 Implement `packages/backfire/src/backfire/provider.py`: the `AsyncOpenAIProvider` subclass, used when the profile's `api` is `openai`, that sends the profile's `model` and `request` fields (for `hive`: `max_tokens` 32768, JSON-object output and `reasoning_effort: "medium"`) to `base_url` with a timeout within the time left, keeps the adapter's own request and finish-reason handling, and checks empty choices or content, refusals, completion tokens at the `max_tokens` the profile's request sets, missing usage, missing model and missing thinking evidence at the profile's paths, and fills the call's judgment metadata with the reported model, thinking evidence and usage. Add the in-process scripted provider `packages/backfire/tests/fake_provider.py`. Tests: `packages/backfire/tests/test_provider.py`, with the `hive` profile and with the test-only profile, whose different model, request fields and nested token path (`completion_tokens_details.reasoning_tokens`) the same code must send and read (depends on T002, T014, T015).
  - 2026-09-27 handoff: a Codex worker wrote `ProfileProvider(profile, api_key)`, `ProviderCall(deadline)` and the `provider_call` context variable, with `tests/fake_provider.py` and 119 tests; the coordinator reviewed it and noted the private adapter helpers in research.md. Next: T018 installs a `ProviderCall` per judgment and fills `latency_ms`.
- [X] T018 Implement `packages/backfire/src/backfire/judge.py`, the in-process judge of [contracts/judgment.md](contracts/judgment.md): the adapter client settings of [data-model.md](data-model.md#backend-configuration), the configuration and credential read for each judgment, the request limits before any provider call, the time left from the caller's deadline for every attempt and retry wait, cancellation of the provider request and pending retry, the `<type>: <message>` errors, the per-call judgment metadata, and, when the caller passes a record file, the judgment record written through `records.py` before the result reaches the tool, with the payload digest's `model` taken from the selected profile or null when configuration fails first ([data-model.md](data-model.md#digests)), failing the judgment when the record cannot be written. Tests: `packages/backfire/tests/test_judge.py` with `fake_provider.py`, including a direct judgment with its own deadline that writes no record (depends on T014 to T017, T021).
  - 2026-09-27 handoff: a Codex worker wrote the in-process judge with 34 tests; `serve-mcp` now uses it, the result carries `metadata`, and `RecordFile.calls_in_flight` is the session's open calls, which T026 maintains. Switching to the real judge made T072's load test send one live judgment with synthetic inputs through the operator's credential; the worker isolated that test and added `tests/conftest.py`, which gives every test temporary `XDG_CONFIG_HOME` and `XDG_STATE_HOME`. Next: T020 and T026.
- [X] T019 Removed on 2026-09-27: the in-process judge has no serve command or endpoint process.
- [X] T020 Gate 9, judge part: `packages/backfire/tests/test_adapter_wiring.py` shows that prompted mode carries the questions and schema in the messages, that per-call judgment metadata stays separate under concurrent judgments, and that the adapter's debug objects never reach logs, errors or records (depends on T017, T018).
  - 2026-09-27 handoff: a Codex worker added five wiring tests (prompted questions and schema, separate metadata under concurrency, no adapter debug data in results, logs, errors or records), all passing; the coordinator reviewed them. Gate 9 closes with T035.

### Server (Python)

- [X] T021 [P] Implement `packages/backfire/src/backfire/records.py`: the per-session file under `$XDG_STATE_HOME/verbose-broccoli/backfire/records/` with an exclusive lock, rotation at 10 MiB, the directory lock with the 50 MiB budget and oldest-unlocked deletion, RFC 8785 digests through `rfc8785`, and the tool-call and judgment record writers of [data-model.md](data-model.md#record-files). Tests: `packages/backfire/tests/test_records.py` (budget across rotation, two sessions writing, a killed writer, an interrupted final line, a write failure) (depends on T064).
  - 2026-09-27 handoff: a Codex worker wrote `RecordFile(directory)` (the session writer that `record_file` now carries, closable and a context manager) with both record writers and 18 tests; the coordinator reviewed it. Next: T018 writes judgment records through it and updates the `record_file` annotation in judge.py; T026 creates one per session.
- [X] T022 [P] Implement `packages/backfire/src/backfire/decisions.py`: the decision units of [data-model.md](data-model.md#decision-units), `other` for values outside the vocabulary, and no caller-supplied field read. Tests: `packages/backfire/tests/test_decisions.py` with one result per tool (depends on T064).
  - 2026-09-27 handoff: a Codex worker wrote the decision units for all eleven tools with 145 tests; the coordinator checked them against data-model.md. Next: T021 and T026 write them into tool-call records.
- [X] T023 [P] Add the test doubles: extend T069's scripted stand-in into `packages/backfire/tests/scripted_judge.py`, a judge that answers from a script, writes each request's `state` and `questions` in order to a file the test names, and can stall, fail with any judgment error, or return malformed answers, and the test-only `BACKFIRE_TEST_JUDGE_SCRIPT=<path>` with which the server uses it instead of the real judge; add the variable to [contracts/mcp-server.md](contracts/mcp-server.md) as test-only through the coordinator. Tests: `packages/backfire/tests/test_doubles.py` (depends on T069).
  - 2026-09-27 handoff: a Codex worker extended the scripted judge (file scripts, ordered request capture, errors, stalls) and the `BACKFIRE_TEST_JUDGE_SCRIPT` hook in `serve-mcp`, with 33 tests; the coordinator reviewed it and added the variable to mcp-server.md. Next: T026, T027 and T030 drive the server with it.
- [X] T024 Removed on 2026-09-27: there is no endpoint child to start or stop.
- [X] T025 Removed on 2026-09-27: the judge writes the judgment records (T018); there is no copied transport to hook.
- [X] T026 Complete `packages/backfire/src/backfire/server.py` and add `packages/backfire/src/backfire/boundary.py`: the session start (record file), the bounded line reader given to the SDK's `stdio_server` as its input stream, which ends the session when a line passes 10 MiB before its newline, the MCP boundary of [contracts/mcp-server.md](contracts/mcp-server.md#mcp-boundary) around the MCP Python SDK's stdio streams (tool-call records, dropped late responses, the 118 s deadline that cancels the call's task with its fixed `deadline_exceeded` result, `record_write_failed`), and shutdown on input end, output failure, a message over 10 MiB, SIGTERM or SIGINT, cancelling open calls and killing pattern children (depends on T018, T021, T022, T023, T072).
  - 2026-09-27 handoff: a Codex worker wrote `boundary.py` (bounded line reader, tool-call records, deadline, cancellation, late-response dropping, `record_write_failed`, shutdown) and wired it into `server.py` with 16 focused cases; the coordinator reviewed it (999 package tests pass). Next: T027, T030, T031, T033, T034 and T035.
- [X] T027 Test the MCP boundary in `packages/backfire/tests/test_boundary.py`, driving `python -m backfire serve-mcp` over stdio with the scripted judge: messages pass unchanged, one tool-call record per call including local-only `backfire_extract` results, tool errors, invalid arguments (a tool error with upstream's prefix) and JSON-RPC errors, a completed response held back until after its cancellation and then dropped, a line over 10 MiB ending the session, whether it has no newline, is valid JSON padded with whitespace, or carries a large argument, and `record_write_failed` (depends on T023, T026).
  - 2026-09-27 handoff: a Codex worker added seven boundary tests (unchanged messages, one record per call, late responses dropped, lines over 10 MiB, `record_write_failed`), passing four runs in a row; the coordinator reviewed them.

### Fixtures and gates

- [X] T028 [P] Write `scripts/backfire/fixtures/known-answers-v1.jsonl` per [contracts/evaluation.md](contracts/evaluation.md#coverage): for every tool a normal, boundary and failure case, both languages where the tool takes free text, a 30-candidate `backfire_find`, a Korean `backfire_classify`, a prompt-injection `backfire_screen`, the four `backfire_extract` cases, a duplicate-id tool error and a single-candidate `backfire_find` that must fail with `invalid_request`; the limit-size cases follow in T044 after gate 3.
  - 2026-09-27 handoff: a worker wrote 67 cases (all eleven tools, English and Korean, normal, boundary and failure, plus the required special cases) and checked them without any model against the pinned upstream schemas and result shapes; the coordinator reviewed them. Next: T029 captures the upstream results for every argument set.
- [X] T029 Gate 5, capture: write `packages/backfire/src/backfire_tools/acceptance/capture_upstream.py` and `packages/backfire/src/backfire_tools/acceptance/scripted_endpoint.py`, a scripted System One endpoint on the standard library's HTTP server; the capture fetches the source tree of `jkudish/jev-mcp` at revision `a1fcc1e47fc696614f081e23a66ff48a890f22fd` into a temporary directory, runs `npm ci --ignore-scripts` from its own `package-lock.json` and the package's own build (`npm run build`), records the Node and npm versions with the fixtures, runs `node dist/index.js` on Node 22 or later with `JEV_PROVIDER=compatible` and `JEV_MCP_MAX_ATTEMPTS=1` against the scripted endpoint, and stores its `tools/list`, and for every argument set in `known-answers-v1.jsonl` each judgment request the endpoint received (`state` and `questions`, in order), the scripted answers and the result, under `scripts/backfire/fixtures/upstream-0.9.0/`; run it once and commit the fixtures (depends on T028).
  - 2026-09-27 handoff: a Codex worker wrote the capture and the scripted endpoint with 13 tests and captured all 67 cases (43 judgment requests); the coordinator reviewed it and recorded the capture in research.md. Next: T030 compares the port with these fixtures.
- [X] T030 Gate 5, fidelity: `packages/backfire/tests/test_fidelity.py` runs `python -m backfire serve-mcp` with the scripted judge answering from the captured script and requires the tool list (names, descriptions, input schemas), the judgment requests that the scripted judge wrote (`state` and `questions`, in order, and none for local-only cases), and every result and error text to equal the captured fixtures after mapping `jev_` to `backfire_` and `jev-mcp` to `backfire` and applying the recorded differences of `UPSTREAM.md`, including the four `backfire_extract` cases; each case that a recorded difference changes is listed with the difference (depends on T026, T029).
  - 2026-09-27 handoff: a Codex worker replayed all 67 captured cases; the replay found the `tools/list` order and the `isError: false` envelope, which the coordinator fixed in `server.py` (commit 2868bfb); all 136 checks now pass repeatedly. Gate 5 passes.
- [ ] T031 Gate 6, bounded blocking: `packages/backfire/tests/test_bounded_work.py` sends each tool an input at the 10 MiB message limit, including `backfire_verify` with 100,000 evidence items sharing one id and `backfire_extract` with slow patterns, with the scripted judge answering at once, and measures the server's longest event-loop stall as the worst lag of a 100 ms interval timer running in the server; it requires that lag to stay under 1 s for every tool, so the 118 s deadline and cancellations fire on time. Pattern children run outside the event loop and are measured by gate 8. Report the lags for research.md (depends on T026).
  - 2026-09-27 handoff: dispatched to a Codex worker after T026 (commit b76a197). Next: the coordinator reviews and commits it.
- [ ] T032 Conditional, only if T031 fails: move the stalling preparation off the event loop (a thread or a process) in the affected tool, pass T031's measurement, record the decision in [research.md](research.md#one-retry-layer-and-one-deadline--2026-09-26), and rerun the tests that drive the server: T072's load test and T027, T030, T031, T033, T034 and T035 (depends on T031).
  - 2026-09-27 handoff: gate 6 failed (`backfire_verify` stalled 0.83-1.19 s; argument validation took about 1 s of it); dispatched to a Codex worker to move the validation off the event loop. Next: the coordinator reviews it and records the decision.
- [X] T033 Gate 7, lifecycle: `packages/backfire/tests/test_lifecycle.py` shows that when the client's input ends during a call or while idle, when the client is killed, or when it dies during start, the server and any pattern child are gone within 5 s and the provider call is cancelled; that a killed server leaves no pattern child after its 1,000 ms limit; and that two concurrent sessions do not interfere (depends on T026).
  - 2026-09-27 handoff: a Codex worker added nine lifecycle tests (client end of input and death, death during start, provider cancellation, pattern children, concurrent sessions), passing three runs in a row; the coordinator reviewed them. Gate 7 passes.
- [X] T034 Gate 8, deadline: `packages/backfire/tests/test_deadline.py`, marked `slow` and run by `test:backfire-slow`, shows that `backfire_extract` with 31 timed-out patterns and one matching pattern against a stalled provider ends with a specific judgment error or `deadline_exceeded` before 120 s, that a call stalled past 118 s gets `deadline_exceeded` and its provider request is cancelled while another call in the same session still answers, and that cancelling during pattern matching kills the pattern child and makes no provider call (depends on T026).
  - 2026-09-27 handoff: a Codex worker added three slow deadline tests; `backfire_extract` with 31 timed-out patterns against a stalled provider and a call stalled past 118 s both ended with `deadline_exceeded` at about 118.1 s with the provider request cancelled, and cancelling during pattern matching killed the child without a provider call; both slow runs passed. Gate 8 passes, and the workflow's slow step (T037) now has tests.
- [X] T035 Gate 9, tool part: `packages/backfire/tests/test_score_boundary.py` shows that the adapter's Score at the three-level boundaries (`{0: 0, 1: 0.005, 2: 1}` and `{0: 0, 1: 0, 2: 0.99}`) passes the ported `backfire_review` and `backfire_gate` (depends on T026).
  - 2026-09-27 handoff: a Codex worker added four MCP cases in which the adapter's Score at the two three-level boundaries passes the real `backfire_review` and `backfire_gate`; all pass; the coordinator reviewed them. Gate 9 passes (with T020).
- [X] T036 Gate 3, request limits (on demand): write `packages/backfire/src/backfire_tools/acceptance/probe_limits.py`, which builds synthetic requests in which every question has one obvious known answer (for a Choice, one relevant option among unrelated ones) and sends each three times through the judge with the test-only `BACKFIRE_TEST_REQUEST_LIMITS` set to the probed sizes, with answer validation and a 118 s deadline per judgment still active and no judgment record ([contracts/judgment.md](contracts/judgment.md#request)): one Choice of 150, 200 and 250 options, and each tool's upstream maximum request from the table in [research.md](research.md#tool-source-jev-mcp-090-copied--2026-09-26), with `backfire_verify`, which has no upstream cap, at the largest cell count of the other tools; and requests of 4, 8 and 16 questions taken from the JevBench public hard tier, because hard questions answered eight per call on 2026-09-27 took up to 60 s and more often came back wrong ([research.md](research.md#judgment-quality-probes--2026-09-27)); score each hard-tier answer against the tier's expected answer, and report per size and run the correct, wrong and invalid answers and the latency, next to the same questions asked one per request; set the option and cell limits in `packages/backfire/src/backfire/validate.py` to the largest sizes at which the known answer has the highest probability in every answer and every run and that finish within 60 s, from the synthetic requests only (the user's decision of 2026-09-27: the hard-tier batches are quality guidance for T040, not a limit), rerun T016's limit-rejection tests with the final limits, and report the runs for [research.md](research.md#request-size-limits--2026-09-26) (depends on T018).
  - 2026-09-27 handoff: a Codex worker wrote the probe and ran it live (57 judgments); by the user's decisions the synthetic requests set the limits at 250 options and 672 cells, and the hard batches are T040 guidance; the coordinator recorded gate 3 in research.md and updated the limits in the plan and data model. Next: T044 adds the limit-size known-answer cases.
- [X] T037 [P] Gate 11: update `.github/workflows/check.yml` to install the pinned uv and the Python version from `packages/backfire/.python-version`, and extend its preparation step, before `deno task check`, with `deno task backfire:install`, which makes `packages/backfire/.venv` for the server and the tests, so the checks then run without downloads; run `test:backfire-slow` in the same job; the fresh-cache installation of gate 4 stays a separate test; hosted runs stay open until the repository has a remote again (depends on T066, T067).
  - 2026-09-27 handoff: a Codex worker added checksum-pinned uv 0.11.32, the pinned Python, `deno task backfire:install` and the slow-test step to the workflow, checked locally; the coordinator reviewed it. The slow step exits 5 until T034 adds slow tests, so do not push the branch before T034. Hosted runs stay open until the branch is pushed (the repository has an `origin` again).

**Checkpoint**: Gates 3 to 9 and 11 pass; the backend answers through the real
tool path offline.

---

## Phase 3: User Story 1 - Gate a Completion Claim with a Typed Judgment (Priority: P1) 🎯 MVP

**Goal**: An agent calls `backfire_gate` through the code plugin and gets
probabilities, the tool's action and the answering model, with a verdict record
bound to the exact input.

**Independent Test**: In Codex CLI and in Claude Code, each with only the code
plugin registered, call `backfire_gate` on a synthetic incomplete rename with one
supported and one contradicted claim: the action is `review` or `escalate`, the
claims' top verdicts are verified and contradicted, and the result names the
answering model.

- [ ] T038 [US1] Declare the stdio server `backfire` in `plugins/code/mcp.json` per [contracts/mcp-server.md](contracts/mcp-server.md#declaration), change the code package's expected MCP servers to `["backfire"]` in `scripts/plugin_skills_test.ts`, and regenerate `docs/reference/` with `deno task docs:generate`.
- [ ] T039 [P] [US1] `packages/backfire/tests/test_gate_flow.py` drives `backfire serve-mcp` in `packages/backfire/` with the real judge and `fake_provider.py`: `backfire_gate` on the incomplete rename returns every rubric and claim distribution, an action that is not `auto`, the contradicted claim, and the model; the session starts with the call's client and stops with it; the tool-call record's digest matches the input, and changing any one field of the input changes it (US1 scenarios 1, 2, 4 and 5).
- [ ] T040 [P] [US1] Vendor the upstream skill into `plugins/code/skills/backfire/` (`SKILL.md`, `reference/tools.md`, `LICENSE`, `upstream.json`) with the four recorded changes of [research.md](research.md#agent-facing-documentation--2026-09-26), write `plugins/code/skills/backfire/references/verbose-broccoli.md` with the statements FR-014 and FR-017 require, and with the measured weak spots of [research.md](research.md#judgment-quality-probes--2026-09-27): a verdict can be confidently wrong, a response with a small arithmetic error can be judged fully correct, and multi-step lookups among distractors fail most often, so numbers and test results are checked by running them.
- [ ] T041 [US1] Implement the evaluation runner core in `packages/backfire/src/backfire_tools/acceptance/evaluate.py` with the command line `<set> [--client claude|codex] [--runs <n>] [--tool <name>]`: stage the code plugin alone by building it into a temporary directory with `backfire_tools.build` (T068) and running the install command in the staged copy's `backfire/` before serving, drive a set through a direct MCP session with the staged copy's declared `uv` command or through Claude Code or Codex with the registrations of [contracts/mcp-server.md](contracts/mcp-server.md#client-registration-for-acceptance), give each run its own `XDG_STATE_HOME`, check every call's record digest and the per-tool mutation checks, keep the 256 MiB cache budget and remove the run directory, the staged copy and the staged copy's environment at the end, on failure and on interruption, and for the `heldout` set verify `scripts/backfire/fixtures/heldout-v1.seal.json` before the first run. Tests: `packages/backfire/tests/test_evaluate.py` for staging, the budget, cleanup and a seal mismatch.
- [ ] T042 [US1] On demand: run `deno task backfire:eval -- known-answers --tool backfire_gate --client claude` and `--client codex`, and record the outcome in [research.md](research.md) (depends on T041, T043, T051).

**Checkpoint**: MVP: `backfire_gate` works through the code plugin with recorded,
digest-bound verdicts.

---

## Phase 4: User Story 2 - Use Every Judgment Tool on Real Content (Priority: P2)

**Goal**: All eleven tools answer typed judgments in English and Korean,
including maximum-size requests, through the same backend.

**Independent Test**: In both clients, run the versioned known-answer set, with
normal, boundary and failure cases for every tool through the real tool path;
every case returns its expected result.

- [ ] T043 [P] [US2] Implement the metrics of [contracts/evaluation.md](contracts/evaluation.md#metrics) in `packages/backfire/src/backfire_tools/acceptance/metrics.py`: correctness, the FR-003 contract check of every answer in a result, accuracy, the automatic decisions and automatic approvals of [contracts/evaluation.md](contracts/evaluation.md#automatic-decisions-and-approvals), the automatic-decision rate over the tools that have an automatic decision, accuracy of automatic decisions, per-tool and per-language accuracy, and ECE over ten bins. Tests: `packages/backfire/tests/test_metrics.py` with every fixed-input case the contract lists.
- [ ] T044 [P] [US2] Add the limit-size cases to `scripts/backfire/fixtures/known-answers-v1.jsonl`, one request at the limits that must succeed and one just over them that must fail with `request_limit_exceeded` for each tool whose upstream maximum exceeds the limits, and recapture their upstream fixtures with `packages/backfire/src/backfire_tools/acceptance/capture_upstream.py` (depends on T036).
- [ ] T045 [P] [US2] Write `scripts/backfire/fixtures/classify-60-v1.jsonl`: one 60-item `backfire_classify` case, 30 English and 30 Korean items over five classes, each with its expected class.
- [ ] T046 [US2] `packages/backfire/tests/test_tools_flow.py` drives `backfire serve-mcp` in `packages/backfire/` with the real judge and `fake_provider.py`: a 30-candidate `backfire_find` puts the relevant candidate first with every candidate scored, a Korean classification returns its class, `backfire_screen` recommends blocking or review for injected instructions and passes harmless text, `backfire_extract` returns a Korean value exactly as written, and a request over the limits fails before any provider call and never returns a partial answer set (FR-005, FR-018).
- [ ] T047 [US2] Implement the `benchmark` set in `packages/backfire/src/backfire_tools/acceptance/evaluate.py` per [contracts/evaluation.md](contracts/evaluation.md#sets): download JevBench's public hard tier from the pinned revision into the cache, check its SHA-256, send each decision through the staged package's judge as a direct caller with a 118 s deadline per judgment and no judgment record, and report correctness, invalid answers, ECE and the median and 95th-percentile times. Tests: `packages/backfire/tests/test_benchmark.py` with a local copy of a three-item sample and a hash mismatch.
- [ ] T048 [US2] On demand: run `deno task backfire:eval -- known-answers --client claude` and `--client codex`, then `deno task backfire:eval -- classify-60 --runs 3`, and record the outcomes in [research.md](research.md) (SC-003, SC-004).

**Checkpoint**: All eleven tools pass their known-answer cases.

---

## Phase 5: User Story 3 - Fail Closed and Stay Observable (Priority: P3)

**Goal**: Every failure is explicit and diagnosable, nothing keeps running
after a session, and one readiness check confirms the setup.

**Independent Test**: Inject each fault of User Story 3: every affected call
fails with an explicit reason and no answer, other sessions keep working,
nothing is left running, and the readiness check reports success or the
specific failure.

- [ ] T049 [P] [US3] `packages/backfire/tests/test_faults.py`: every error type and status of [contracts/judgment.md](contracts/judgment.md#errors), including the `hive` profile's status override (405), an invalid profile selection or profile, missing credential, `Retry-After` that does not fit, connect and read failures, 5xx, truncation at the profile's `max_tokens` while the finish reason reads `stop`, malformed output, refusal, all-zero and off-sum distributions, a missing model and missing thinking evidence; at most four attempts, no retry of other failures, and a valid low-confidence or negative verdict returned once without a new request.
- [ ] T050 [P] [US3] `packages/backfire/tests/test_server_faults.py`: each judgment error reaches the agent as its `<type>: <message>` tool error with no judgment, a missing credential names the file, and the model in every request stays the pinned one.
- [ ] T051 [US3] Implement `packages/backfire/src/backfire/ready.py` and fill `__main__.py`'s `ready` per [contracts/readiness.md](contracts/readiness.md): configuration and installation checks, one Noul judgment through the judge as a direct caller with a 118 s deadline and no judgment record, the tool path through `serve-mcp` with record digests, requested and confirmed facts with reasons for anything unconfirmed, the sample latency, the versions including the ported revision, the report of `BACKFIRE_TEST_PROVIDER_BASE_URL` when set, and the exit codes. Tests: `packages/backfire/tests/test_ready.py` with `fake_provider.py`.
- [ ] T052 [P] [US3] Write `scripts/backfire/fixtures/safety-v1.jsonl`: at least five cases for each safety category of SC-009, split between English and Korean, one decision unit each.
- [ ] T053 [P] [US3] Implement the credential and privacy scan in `packages/backfire/src/backfire_tools/acceptance/scan.py` per [contracts/evaluation.md](contracts/evaluation.md#run-protocol), reporting paths and counts only. Tests: `packages/backfire/tests/test_scan.py` (the placeholder passes, a planted synthetic key is found) and `packages/backfire/tests/test_privacy.py` (a planted request string, synthetic identifiers and the key value never appear in records, logs or judgment errors).
- [ ] T054 [US3] On demand: on a machine where Deno (for the repository's tasks), uv, Python and the selected provider's key are already installed, time the setup of `docs/backfire.md` (T056) through a passing `backfire ready`, run with the declared `uv` command, of a code plugin built with `deno task backfire:build`, then run `deno task backfire:eval -- safety --runs 3`, and record the time and outcomes in [research.md](research.md) (SC-007, FR-011, SC-009) (depends on T056).
- [ ] T055 [US3] On demand: in two Orca tabs with the staged `backfire` server registered, run the four session checks of [quickstart.md](quickstart.md#8-sessions-in-real-clients-fr-010) (concurrent calls, closing one tab, `kill -9` of a client during a long call, cancelling a call) and record the outcomes in [research.md](research.md) (FR-010).

**Checkpoint**: Faults fail closed, sessions clean up, readiness reports
requested and confirmed facts.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Operator documentation, final measurements and acceptance.

- [ ] T056 [P] Write `docs/backfire.md`: building the code plugin, installation, provider profiles and their selection, the credential file, readiness, what is sent to the selected provider, the advisory nature of the tools, and troubleshooting by error type.
- [ ] T057 Update `docs/architecture.md` for the code package's `backfire` server: the `packages/backfire/` package outside the root Deno workspace, the build that copies it into a distributed code plugin, provider profiles and the port's upstream record; replace its rule that a package under `packages/` needs a shared use and root workspace registration with constitution IX's rule; link `docs/backfire.md` from it, and run `deno task docs:generate` (depends on T056).
- [ ] T058 On demand: run `deno task backfire:eval -- benchmark --runs 3`, check that every benchmark response carried the thinking evidence the selected profile names (gate 2), and record SC-001 and SC-002 in [research.md](research.md).
- [ ] T059 On demand, final acceptance: verify the held-out seal, run `deno task backfire:eval -- heldout --runs 3`, repeat the other criteria as [contracts/evaluation.md](contracts/evaluation.md#thresholds) lists, and replace `artifacts/jev-decision-backend/acceptance.json` in one atomic write.
- [ ] T060 Only with the user's approval: post upstream issues for `jev-mcp` (the ESM `eval` worker under Deno, the quadratic `ensureUniqueIds`, stdin end of input ignored) and `system-one-adapter` (request options, issues #45 to #48).
- [ ] T061 Run the offline parts of [quickstart.md](quickstart.md), then `deno task test:backfire-slow`, `deno task check` and `deno task verify`, and report the results to the coordinator, who adds the session's handoff lines under the last task worked on.
- [ ] T062 Blocked until the separate client-installation feature installs the code package through each client's plugin mechanism, and run only with the user's approval, because installing changes saved client configuration: add an `--installed` mode to `packages/backfire/src/backfire_tools/acceptance/evaluate.py` that drives the client's installed code package, which that feature installs from a code plugin built with `deno task backfire:build`, instead of a staged registration; with the code package installed alone in Codex CLI and in Claude Code, run `deno task backfire:eval -- known-answers --installed --client claude` and `--client codex`, check that only the code plugin's `backfire` server offers the eleven tools in each client, and record the outcomes in [research.md](research.md); FR-001 and SC-008 close only when both clients pass.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: T001 first; nothing from T003 on starts before it. T002 runs any
  time before T014, T015 and T017. The TypeScript tasks T003 to T008, T013 and
  T063 are complete and superseded by Phase 1b.
- **Phase 1b**: T064 first; then T065, T066 and T069 in parallel; T068
  after T066; T070 and T071 in parallel after T069; T072 after T066, T068, T070
  and T071.
- **Phase 2**: needs T072. Judge: T014 to T016 in parallel, then T017; T018
  after T014 to T017 and T021; T020 after T017 and T018. Server: T021 and T022
  in parallel; T023 after T069; T026 after T018, T021, T022, T023 and T072;
  T027 after T023 and T026. Gates: T029 any time after T028; T030 after T026
  and T029; T031, T033, T034 and T035 after T026; T032 only if T031 fails; T036
  after T018; T037 after T064 and T066.
- **User stories**: need every Phase 2 gate. US1, US2 and US3 can then proceed
  in parallel; US2's T044 needs T036; T047 needs T041 and T043; on-demand runs
  need T041, T043 (correctness and the FR-003 check) and T051 (the readiness
  report whose versions every run records), so US1's T042 waits for those two
  tasks from US2 and US3; T054 needs T056; and T058 needs T047.
- **Polish**: T056 any time after T038, and T057 after T056; T058 and T059
  after all stories; T061 last among the tasks that wait for no other feature;
  T062 after the client-installation feature has passed.

### Gate Consequences

| Gate | Task | Stops when it fails |
| --- | --- | --- |
| 1 | T001 | All implementation (T003 on) |
| 2 | T002, T065, T058 | T017 (settings); final acceptance (benchmark evidence) |
| 3 | T036 | T044 and the limit-size cases |
| 4 | T072 | Phase 2 and later |
| 5 | T029, T030 | User stories |
| 6 | T031 | User stories, until T032 passes |
| 7 | T033 | User stories |
| 8 | T034 | User stories |
| 9 | T020, T035 | User stories |
| 10 | T041, T042 | Client runs (T042, T048, T055) |
| 11 | T037 | Hosted CI acceptance only |
| 12 | T030 | User stories: every `backfire_extract` case matches upstream or is listed as a recorded difference |

### Within Each Story

- Tests come with their code in the same task.
- Fixtures before the runs that use them; offline tests before on-demand runs.

### Parallel Opportunities

- Phase 1b: T065, T066 and T069 together after T064; T070 and T071
  together after T069.
- Phase 2: the judge track (T014 to T020) and the server track (T021 to T023)
  run side by side until T026; T029 any time; T031, T033, T034 and T035
  together after T026.
- Stories: T039 and T040; T043, T044 and T045; T049, T050, T052 and T053.

---

## Parallel Example: User Story 1

```bash
Task: "T039 [US1] test_gate_flow.py in packages/backfire/tests/"
Task: "T040 [US1] Vendor the upstream skill into plugins/code/skills/backfire/"
```

## Parallel Example: User Story 2

```bash
Task: "T043 [US2] Metrics in packages/backfire/src/backfire_tools/acceptance/metrics.py"
Task: "T044 [US2] Limit-size cases in scripts/backfire/fixtures/known-answers-v1.jsonl"
Task: "T045 [US2] scripts/backfire/fixtures/classify-60-v1.jsonl"
```

## Parallel Example: User Story 3

```bash
Task: "T049 [US3] packages/backfire/tests/test_faults.py"
Task: "T050 [US3] packages/backfire/tests/test_server_faults.py"
Task: "T052 [US3] scripts/backfire/fixtures/safety-v1.jsonl"
Task: "T053 [US3] packages/backfire/src/backfire_tools/acceptance/scan.py and privacy tests"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1, with the held-out set sealed first, and Phase 1b.
2. Phase 2, until every gate passes.
3. Phase 3: `backfire_gate` through the code plugin, plus T043 and T051,
   which the live run T042 needs.
4. **Stop and validate** with T039 offline and T042 in both clients.

### Incremental Delivery

1. Setup, gates and foundation: the backend answers offline.
2. US1: gated completion claims (MVP).
3. US2: every tool, both languages, maximum sizes.
4. US3: fault handling, readiness and privacy.
5. Polish: documentation, benchmark and final acceptance.

### Parallel Team Strategy

In Phase 1b, two workers port the tools side by side (T070, T071); in Phase 2,
the judge and server tracks can go to two workers; after Phase 2, one worker
per story.

---

## Notes

- [P] tasks touch different files and depend on no incomplete task.
- Each task is sized for one worker and names its files.
- Commit after each task or logical group with a `Spec-Kit-Task: Txxx` trailer.
- Stop at any checkpoint to validate independently.
