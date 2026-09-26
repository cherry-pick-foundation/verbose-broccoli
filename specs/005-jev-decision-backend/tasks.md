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
their code: `deno test` for the server, and pytest through `uv run --frozen`
for the endpoint. Offline tests run in `deno task check`; live tests run only
on demand.

**Organization**: Setup and the first gates, then the foundational backend with
its gates, then one phase per user story, then polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete
  task)
- **[Story]**: The user story the task belongs to (US1, US2, US3)
- Paths are relative to the repository root.

## Conventions for Every Task

- Use `$HOME/.deno/bin/deno` when `deno` is not on `PATH`.
- A **gate** task or an on-demand run records its evidence in
  [research.md](research.md) under a dated heading. A failed gate stops every
  task that depends on it ([Dependencies](#dependencies--execution-order))
  until the plan is revised.
- `plugins/code/backfire/upstream/` changes only by the seven recorded changes of
  [research.md](research.md#tool-source-jev-mcp-090-copied--2026-09-26); every
  change updates `upstream/upstream.json`, and T007's guard test must pass.
- **On demand** tasks need network access and Hive credit, and some need
  signed-in Codex CLI and Claude Code; they are never part of
  `deno task check`.
- Installing into saved client configuration and posting upstream issues need
  the user's separate approval.
- FR-001 and SC-008 also depend on a separate client-installation feature;
  this feature's client runs use per-invocation registration, except T062,
  which runs against the installed package once that feature has passed.

---

## Phase 1: Setup and First Gates

**Purpose**: Seal the held-out set before any implementation, confirm Hive's
settings, create the component scaffolding and prove its packaging.

**⚠️ T001 must finish before any task from T003 on starts.**

- [ ] T001 Gate 1: as a worker who will not implement this feature, write the held-out general set `heldout-v1` to `$XDG_DATA_HOME/verbose-broccoli/backfire-eval/heldout-v1.jsonl` (at least ten cases per tool and four per language, English and Korean, synthetic, exactly one decision unit per case, in the case format of [contracts/evaluation.md](contracts/evaluation.md#case-format)), and commit only `scripts/backfire/fixtures/heldout-v1.seal.json` with its SHA-256, case count and per-tool and per-language counts. Implementers never open the data file.
- [ ] T002 [P] Gate 2, settings part (on demand): write `scripts/backfire/probe_hive.ts`, which reads `HIVE_API_KEY` from `$XDG_CONFIG_HOME/verbose-broccoli/backfire/hive.env` and sends to Hive's chat completions one request with `max_tokens: 32768`, `response_format: {"type": "json_object"}` and `chat_template_kwargs: {"thinking": true}`, one with an invalid key and one with an unknown model, plus a burst above five requests per second; it prints only statuses, the response model, reasoning evidence and token counts. Run it and record in [research.md](research.md#hive-request-behavior--2026-09-26) which of 200, 401, 400 and 429 were observed; 405 stays documented-only and is covered offline by T049. The benchmark part of gate 2 is T058.
- [ ] T003 Copy `src/index.ts`, `src/lib.ts`, `src/provider.ts`, `package.json` and `LICENSE` of `jkudish/jev-mcp` at revision `a1fcc1e47fc696614f081e23a66ff48a890f22fd` unchanged into `plugins/code/backfire/upstream/`, check their SHA-256 against the table in [research.md](research.md#tool-source-jev-mcp-090-copied--2026-09-26), and write `plugins/code/backfire/upstream/upstream.json` with the source URL, revision, license and each file's original SHA-256.
- [ ] T004 [P] Apply recorded changes 1 to 3 and 7 to `plugins/code/backfire/upstream/src/index.ts`: import `./lib.ts` and `./provider.ts`; open the regex worker source with `const { parentPort, workerData } = require("node:worker_threads");`; export `server` and remove the final `server.connect(new StdioServerTransport())`, its ready log line and the unused `StdioServerTransport` import; and apply change 7: name the server `backfire` and the eleven tools `backfire_<suffix>` in registrations, the results' `tool` field, descriptions and error messages, leaving comments unchanged. Change nothing else.
- [ ] T005 [P] Apply recorded change 4 to `plugins/code/backfire/upstream/src/lib.ts`: `ensureUniqueIds` keeps the next suffix per base id so that shared ids take linear time, with identical ids and order. Add `plugins/code/backfire/server/upstream_lib_test.ts`, which compares the result with the original function (kept inside the test) on duplicate-id inputs and checks that 100,000 items sharing one id finish within one second.
- [ ] T006 [P] Apply recorded change 5 to `plugins/code/backfire/upstream/src/provider.ts`: keep the compatible-endpoint branch (lines 331 to 382 at the revision) and the helpers it calls, remove the TypeSafe, Vercel, OpenRouter and Cloudflare branches and the `@jkudish/jev-agent-tools` import, and make provider resolution require `JEV_PROVIDER=compatible` with `JEV_API_BASE_URL` and `JEV_API_KEY`, keeping the upstream error text for a missing variable.
- [ ] T007 Record the diff of changes 1 to 5 and 7 in `plugins/code/backfire/upstream/upstream.json` and add `plugins/code/backfire/server/upstream_record_test.ts`, which recomputes each copied file's diff against the recorded originals and fails when a file differs from its record or a file is added or removed (depends on T004 to T006).
- [ ] T008 [P] Create `plugins/code/backfire/deno.json` with `nodeModulesDir: "none"` and imports pinned exactly: `@modelcontextprotocol/sdk/` to `npm:/@modelcontextprotocol/sdk@1.30.1/`, `zod` to `npm:zod@4.6.5`, `@typesafe-ai/sdk` to `npm:@typesafe-ai/sdk@0.6.0` and `canonicalize` to `npm:canonicalize@5.0.0`, plus the `@std` modules the server needs; generate `plugins/code/backfire/deno.lock` with Deno's default minimum dependency age left on.
- [ ] T009 [P] Create the endpoint project: `plugins/code/backfire/backend/pyproject.toml` (package `backfire_backend` under `src/`, `system-one-adapter[openai]==0.2.1`, Starlette, Uvicorn, and pytest as a development dependency), `plugins/code/backfire/backend/.python-version` with `3.14.4`, and `plugins/code/backfire/backend/uv.lock` that pins `typesafe-sdk` 0.7.1.
- [ ] T010 Create `plugins/code/backfire/bin/backfire` (POSIX `sh`) with the commands of [contracts/mcp-server.md](contracts/mcp-server.md#entry-commands): it checks `deno` 2.9.6 and `uv`; `install` runs `uv sync --frozen` for `backend/` into `$XDG_CACHE_HOME/verbose-broccoli/backfire/venv` and `deno install --frozen` with the component's `deno.json`; `serve-mcp` and `ready` run `plugins/code/backfire/server/main.ts` and `server/ready.ts` with `--frozen --cached-only` and the narrowest permissions that pass the tests, and exit non-zero with a message naming `bin/backfire install` when the environment or cached modules are missing (depends on T008, T009).
- [ ] T011 [P] Update the repository configuration: `biome.json` excludes `plugins/code/backfire/upstream`; `deno.json` adds the tasks `backfire:install` and `backfire:ready` (calling `bin/backfire`), `backfire:eval` (running `scripts/backfire/evaluate.ts`), `test:backfire` (the component's `deno test` with its own config, then `uv run --frozen pytest` in `plugins/code/backfire/backend`) and `test:backfire-slow` (the deadline tests), adds `test:backfire` to the `test` dependencies, and grants the docs tasks read access to any new documented inputs.
- [ ] T012 [P] Add sections to `licenses/THIRD_PARTY_NOTICES.md` for the copied `jev-mcp` 0.9.0 source (MIT, revision, the seven recorded changes and where `upstream.json` records them), the vendored `backfire` skill (MIT, from upstream `skills/jev`) and `system-one-adapter` 0.2.1 (MIT).
- [ ] T013 Gate 4, packaging: with `DENO_DIR` and `XDG_CACHE_HOME` pointing at empty temporary directories, run `plugins/code/backfire/bin/backfire install`; show that `deno install --frozen` succeeds from `plugins/code/backfire/deno.lock` under Deno's default minimum dependency age and that `uv sync --frozen` installs Python 3.14.4 and the lock; write the first `plugins/code/backfire/server/main.ts`, which imports the copied `server` and connects it to the SDK's stdio transport; add `plugins/code/backfire/server/load_test.ts`, which runs `bin/backfire serve-mcp` (and so `--cached-only`) against those directories with the transport environment of [contracts/mcp-server.md](contracts/mcp-server.md#session-lifecycle) and any port, checks the server version that the copied source reads from `package.json` through `createRequire`, and lists eleven tools over stdio; run `deno check` on the copied files and either pass it or exclude them from type checking with the reason recorded (depends on T007, T010).

**Checkpoint**: Held-out set sealed, Hive settings confirmed, packaging proven.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The endpoint, the server with its MCP boundary and records, the
test doubles, and the gates that prove them. Every user story needs this
backend.

**⚠️ No user story work can begin until this phase and its gates pass.**

### Endpoint (Python)

- [ ] T014 [P] Implement `plugins/code/backfire/backend/src/backfire_backend/config.py`: the XDG paths of [contracts/configuration.md](contracts/configuration.md), and the credential check (file present, non-empty, mode exactly 0600, owned by the operator), which yields `backend_not_configured` with a message naming the path; add the test-only variable `BACKFIRE_TEST_HIVE_BASE_URL`, which points provider calls at a scripted provider, to [contracts/configuration.md](contracts/configuration.md) as test-only. Tests: `plugins/code/backfire/backend/tests/test_config.py`.
- [ ] T015 [P] Implement `plugins/code/backfire/backend/src/backfire_backend/failures.py`: the error types, statuses and fixed messages of [contracts/system-one-endpoint.md](contracts/system-one-endpoint.md#error-responses), the Hive status mapping (401, 400, 405, 429, other statuses), and the TypeSafe SDK `RetryPolicy` of [research.md](research.md#one-retry-layer-and-one-deadline--2026-09-26) (429 and connect-phase failures only, at most four attempts, `Retry-After` within the remaining time). Tests: `plugins/code/backfire/backend/tests/test_failures.py`.
- [ ] T016 [P] Implement `plugins/code/backfire/backend/src/backfire_backend/validate.py`: answer checks without rescaling (sums within `0.01 + 1e-12`, all-zero rejection, both placeholder fallbacks rejected, a returned 0.5 kept) and the request limits (option limit 150 and a provisional cell limit of 300, the 60-item, five-class request that passed on 2026-09-26, until T036 sets both), failing before any provider call. Tests: `plugins/code/backfire/backend/tests/test_validate.py`, including the Score values of [research.md](research.md#answer-validation-without-rescaling--2026-09-26).
- [ ] T017 Implement `plugins/code/backfire/backend/src/backfire_backend/hive.py`: the `AsyncOpenAIProvider` subclass that sends `max_tokens` 32768, JSON-object output, `chat_template_kwargs: {"thinking": true}` and a request timeout, checks empty choices or content, refusals, completion tokens at the limit, missing usage, missing model and missing reasoning evidence, and fills a per-request context with Hive's model, reasoning evidence and usage. Add the in-process scripted provider `plugins/code/backfire/backend/tests/fake_provider.py`. Tests: `plugins/code/backfire/backend/tests/test_hive.py` (depends on T002, T015).
- [ ] T018 Implement `plugins/code/backfire/backend/src/backfire_backend/endpoint.py`: the Starlette app of [contracts/system-one-endpoint.md](contracts/system-one-endpoint.md): the token checked before the body, 404 for other paths and methods, the adapter client settings of [data-model.md](data-model.md#backend-configuration), the 80 s outer deadline, cancellation when the caller disconnects, the `X-Judgment-Metadata` header on every response after authentication, and no file writes. Tests: `plugins/code/backfire/backend/tests/test_endpoint.py` (depends on T014 to T017).
- [ ] T019 Implement `plugins/code/backfire/backend/src/backfire_backend/__main__.py` with the `serve` command: it binds `127.0.0.1` on a free port, prints `{"port": <n>}` as one line, logs only to stderr, reads the token from `BACKFIRE_ENDPOINT_TOKEN`, and cancels in-flight calls and exits when its standard input ends. Tests: `plugins/code/backfire/backend/tests/test_main.py` spawns it, reads the port, calls it and closes its input (depends on T018).
- [ ] T020 Gate 9, endpoint part: `plugins/code/backfire/backend/tests/test_adapter_wiring.py` shows that prompted mode carries the questions and schema in the messages, that per-request metadata stays separate under concurrent requests, and that the adapter's debug objects never reach logs, error bodies or the `X-Judgment-Metadata` header (depends on T017, T018).

### Server (TypeScript)

- [ ] T021 [P] Implement `plugins/code/backfire/server/records.ts`: the per-session file under `$XDG_STATE_HOME/verbose-broccoli/backfire/records/` with an exclusive lock, rotation at 10 MiB, the directory lock with the 50 MiB budget and oldest-unlocked deletion, RFC 8785 digests through `canonicalize`, and the tool-call and judgment record writers of [data-model.md](data-model.md#record-files). Tests: `plugins/code/backfire/server/records_test.ts` (budget across rotation, two sessions writing, a killed writer, an interrupted final line, a write failure).
- [ ] T022 [P] Implement `plugins/code/backfire/server/decisions.ts`: the decision units of [data-model.md](data-model.md#decision-units), `other` for values outside the vocabulary, and no caller-supplied field read. Tests: `plugins/code/backfire/server/decisions_test.ts` with one result per tool.
- [ ] T023 [P] Add the test doubles in `plugins/code/backfire/server/testing/`: `scripted_endpoint.ts`, a System One endpoint that answers from a script and can stall, fail with a status, or return malformed or oversized bodies; and `fake_provider.ts`, an OpenAI-compatible provider for tests that run the real endpoint. Tests: `plugins/code/backfire/server/testing/doubles_test.ts`.
- [ ] T024 Implement `plugins/code/backfire/server/endpoint.ts`: start the endpoint from the synced environment's Python with the environment of [contracts/mcp-server.md](contracts/mcp-server.md#session-lifecycle), read its port line, report an unexpected exit, and stop it by closing its input, then SIGTERM after 2 s and SIGKILL after 2 s more. Tests: `plugins/code/backfire/server/endpoint_test.ts` with the real endpoint (depends on T019).
- [ ] T025 Apply recorded change 6 to `plugins/code/backfire/upstream/src/provider.ts`: hand each request's payload, response, `X-Judgment-Metadata` header or abort to the judgment writer in `plugins/code/backfire/server/records.ts`, with `calls_in_flight` from the boundary's open calls, and fail the request when the record cannot be written; update `plugins/code/backfire/upstream/upstream.json`. Tests: `plugins/code/backfire/server/judgment_record_test.ts` (fields, `cancelled`, `transport_failed`, a write failure turning into a tool error) (depends on T007, T021, T023).
- [ ] T026 Complete `plugins/code/backfire/server/main.ts`, begun in T013: the session start (record file, endpoint child, transport environment), the import of the copied `server`, and the MCP boundary of [contracts/mcp-server.md](contracts/mcp-server.md#mcp-boundary) around the SDK's stdio transport (tool-call records, dropped late responses, the 118 s deadline with its fixed `deadline_exceeded` result, `record_write_failed`, shutdown on input end, output failure, endpoint exit, SIGTERM or SIGINT). Add the test-only variables `BACKFIRE_TEST_ENDPOINT_URL` and `BACKFIRE_TEST_ENDPOINT_TOKEN`, which make the server use an external endpoint instead of starting one, to [contracts/mcp-server.md](contracts/mcp-server.md) as test-only (depends on T013, T022, T024, T025).
- [ ] T027 Test the MCP boundary in `plugins/code/backfire/server/boundary_test.ts`, driving `main.ts` over stdio: messages pass unchanged, one tool-call record per call including local-only `backfire_extract` results, tool errors and the SDK's argument errors, a completed response held back until after its cancellation and then dropped, a message over 10 MiB ending the session, and `record_write_failed` (depends on T023, T026).

### Fixtures and gates

- [ ] T028 [P] Write `scripts/backfire/fixtures/known-answers-v1.jsonl` per [contracts/evaluation.md](contracts/evaluation.md#coverage): for every tool a normal, boundary and failure case, both languages where the tool takes free text, a 30-candidate `backfire_find`, a Korean `backfire_classify`, a prompt-injection `backfire_screen`, the four `backfire_extract` cases, a duplicate-id tool error and a single-candidate `backfire_find` that must fail with `invalid_request`; the limit-size cases follow in T044 after gate 3.
- [ ] T029 Gate 5, capture: write `scripts/backfire/capture_upstream.ts`, which installs `@jkudish/jev-mcp` 0.9.0 into a temporary directory with `npm ci --ignore-scripts` from the package's own `package-lock.json` at revision `a1fcc1e47fc696614f081e23a66ff48a890f22fd`, records the Node and npm versions with the fixtures, runs it on Node 22 or later with `JEV_PROVIDER=compatible` and `JEV_MCP_MAX_ATTEMPTS=1` against `scripted_endpoint.ts`, and stores its `tools/list` and the result of every argument set in `known-answers-v1.jsonl` under `scripts/backfire/fixtures/upstream-0.9.0/`; run it once and commit the fixtures (depends on T023, T028).
- [ ] T030 Gate 5, fidelity: `plugins/code/backfire/server/fidelity_test.ts` runs `main.ts` against the same `scripted_endpoint.ts` and requires the tool list (names, descriptions, input schemas) and every result and error text to equal the captured fixtures after mapping `jev_` to `backfire_` and `jev-mcp` to `backfire`, including the four `backfire_extract` cases (depends on T026, T029).
- [ ] T031 Gate 6, bounded work: `plugins/code/backfire/server/bounded_work_test.ts` sends each tool an input at the 10 MiB message limit, including `backfire_verify` with 100,000 evidence items sharing one id, with `scripted_endpoint.ts` answering at once, and requires each call to reach its judgment call within 5 s; record the times in [research.md](research.md) (depends on T026).
- [ ] T032 Conditional, only if T031 fails: move each tool call into its own worker in `plugins/code/backfire/server/main.ts` and a new `plugins/code/backfire/server/call_worker.ts`, terminating the worker at the deadline, record the decision in [research.md](research.md#one-retry-layer-and-one-deadline--2026-09-26), and rerun the tests that drive `main.ts`: T013's load test and T027, T030, T031, T033, T034 and T035 (depends on T031).
- [ ] T033 Gate 7, lifecycle: `plugins/code/backfire/server/lifecycle_test.ts` shows that when the client's input ends during a call or while idle, when the client is killed, or when it dies during start, the server and the endpoint are gone within 5 s and the provider call is cancelled; that a killed server leaves no endpoint after 2 s; and that two concurrent sessions do not interfere (depends on T026).
- [ ] T034 Gate 8, deadline: `plugins/code/backfire/server/deadline_test.ts`, run by `test:backfire-slow`, shows that `backfire_extract` with 31 timed-out patterns and one matching pattern against a stalled provider fails with the transport's error before 118 s, that a call stalled past 118 s gets `deadline_exceeded` and its provider request is cancelled while another call in the same session still answers, and that cancelling during pattern matching makes no provider call (depends on T026).
- [ ] T035 Gate 9, tool part: `plugins/code/backfire/server/score_boundary_test.ts` shows that the adapter's Score at the three-level boundaries (`{0: 0, 1: 0.005, 2: 1}` and `{0: 0, 1: 0, 2: 0.99}`) passes the copied `backfire_review` and `backfire_gate` (depends on T026).
- [ ] T036 Gate 3, request limits (on demand): write `scripts/backfire/probe_limits.ts`, which builds synthetic requests in which every question has one obvious known answer (for a Choice, one relevant option among unrelated ones) and sends each three times through the endpoint: one Choice of 150, 200 and 250 options, and each tool's upstream maximum request from the table in [research.md](research.md#tool-source-jev-mcp-090-copied--2026-09-26), with `backfire_verify`, which has no upstream cap, at the largest cell count of the other tools; set the option and cell limits in `plugins/code/backfire/backend/src/backfire_backend/validate.py` to the largest sizes at which the known answer has the highest probability in every answer and every run finishes within 60 s, and record the runs in [research.md](research.md#request-size-limits--2026-09-26) (depends on T019).
- [ ] T037 [P] Gate 11: update `.github/workflows/check.yml` to install the pinned uv and the Python version from `plugins/code/backfire/backend/.python-version` before `deno task check`, and run `test:backfire-slow` in the same job; hosted runs stay open until the repository has a remote again (depends on T011).

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
- [ ] T039 [P] [US1] `plugins/code/backfire/server/gate_flow_test.ts` drives `bin/backfire serve-mcp` with the real endpoint and `fake_provider.ts`: `backfire_gate` on the incomplete rename returns every rubric and claim distribution, an action that is not `auto`, the contradicted claim, and the model; the session starts with the call's client and stops with it; the tool-call record's digest matches the input, and changing any one field of the input changes it (US1 scenarios 1, 2, 4 and 5).
- [ ] T040 [P] [US1] Vendor the upstream skill into `plugins/code/skills/backfire/` (`SKILL.md`, `reference/tools.md`, `LICENSE`, `upstream.json`) with the four recorded changes of [research.md](research.md#agent-facing-documentation--2026-09-26), write `plugins/code/skills/backfire/references/verbose-broccoli.md` with the statements FR-014 and FR-017 require.
- [ ] T041 [US1] Implement the evaluation runner core in `scripts/backfire/evaluate.ts` with the command line `<set> [--client claude|codex] [--runs <n>] [--tool <name>]`: stage `plugins/code` alone in a temporary directory, drive a set through a direct MCP session with the staged `serve-mcp` or through Claude Code or Codex with the registrations of [contracts/mcp-server.md](contracts/mcp-server.md#client-registration-for-acceptance), give each run its own `XDG_STATE_HOME`, check every call's record digest and the per-tool mutation checks, keep the 256 MiB cache budget and remove the run directory at the end, on failure and on interruption, and for the `heldout` set verify `scripts/backfire/fixtures/heldout-v1.seal.json` before the first run. Tests: `scripts/backfire/evaluate_test.ts` for staging, the budget, cleanup and a seal mismatch.
- [ ] T042 [US1] On demand: run `deno task backfire:eval -- known-answers --tool backfire_gate --client claude` and `--client codex`, and record the outcome in [research.md](research.md).

**Checkpoint**: MVP: `backfire_gate` works through the code plugin with recorded,
digest-bound verdicts.

---

## Phase 4: User Story 2 - Use Every Judgment Tool on Real Content (Priority: P2)

**Goal**: All eleven tools answer typed judgments in English and Korean,
including maximum-size requests, through the same backend.

**Independent Test**: In both clients, run the versioned known-answer set, with
normal, boundary and failure cases for every tool through the real tool path;
every case returns its expected result.

- [ ] T043 [P] [US2] Implement the metrics of [contracts/evaluation.md](contracts/evaluation.md#metrics) in `scripts/backfire/metrics.ts`: correctness, the FR-003 contract check of every answer in a result, accuracy, the automatic decisions and automatic approvals of [contracts/evaluation.md](contracts/evaluation.md#automatic-decisions-and-approvals), the automatic-decision rate over the tools that have an automatic decision, accuracy of automatic decisions, per-tool and per-language accuracy, and ECE over ten bins. Tests: `scripts/backfire/metrics_test.ts` with every fixed-input case the contract lists.
- [ ] T044 [P] [US2] Add the limit-size cases to `scripts/backfire/fixtures/known-answers-v1.jsonl`, one request at the limits that must succeed and one just over them that must fail with `request_limit_exceeded` for each tool whose upstream maximum exceeds the limits, and recapture their upstream fixtures with `scripts/backfire/capture_upstream.ts` (depends on T036).
- [ ] T045 [P] [US2] Write `scripts/backfire/fixtures/classify-60-v1.jsonl`: one 60-item `backfire_classify` case, 30 English and 30 Korean items over five classes, each with its expected class.
- [ ] T046 [US2] `plugins/code/backfire/server/tools_flow_test.ts` drives `bin/backfire serve-mcp` with the real endpoint and `fake_provider.ts`: a 30-candidate `backfire_find` puts the relevant candidate first with every candidate scored, a Korean classification returns its class, `backfire_screen` recommends blocking or review for injected instructions and passes harmless text, `backfire_extract` returns a Korean value exactly as written, and a request over the limits fails before any provider call and never returns a partial answer set (FR-005, FR-018).
- [ ] T047 [US2] Implement the `benchmark` set in `scripts/backfire/evaluate.ts` per [contracts/evaluation.md](contracts/evaluation.md#sets): download JevBench's public hard tier from the pinned revision into the cache, check its SHA-256, send each decision through the staged endpoint, and report correctness, invalid answers, ECE and the median and 95th-percentile times. Tests: `scripts/backfire/benchmark_test.ts` with a local copy of a three-item sample and a hash mismatch.
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

- [ ] T049 [P] [US3] `plugins/code/backfire/backend/tests/test_faults.py`: every error type and status of [contracts/system-one-endpoint.md](contracts/system-one-endpoint.md#error-responses), including 405, missing credential, `Retry-After` that does not fit, connect and read failures, 5xx, truncation at `max_tokens`, malformed output, refusal, all-zero and off-sum distributions, a missing model and missing reasoning evidence; at most four attempts, no retry of other failures, and a valid low-confidence or negative verdict returned once without a new request.
- [ ] T050 [P] [US3] `plugins/code/backfire/server/faults_test.ts`: each endpoint error reaches the agent as the tool error text of release 0.9.0 with no judgment, a missing credential names the file, the model in every request stays the pinned one, and wrong or foreign tokens never reach the provider.
- [ ] T051 [US3] Implement `plugins/code/backfire/server/ready.ts` and `bin/backfire ready` per [contracts/readiness.md](contracts/readiness.md): configuration and installation checks, one Noul judgment through the endpoint, the tool path through `serve-mcp` with record digests, requested and confirmed facts with reasons for anything unconfirmed, the sample latency, the versions including the copied revision, the report of `BACKFIRE_TEST_HIVE_BASE_URL` when set, and the exit codes. Tests: `plugins/code/backfire/server/ready_test.ts` with `fake_provider.ts`.
- [ ] T052 [P] [US3] Write `scripts/backfire/fixtures/safety-v1.jsonl`: at least five cases for each safety category of SC-009, split between English and Korean, one decision unit each.
- [ ] T053 [P] [US3] Implement the credential and privacy scan in `scripts/backfire/scan.ts` per [contracts/evaluation.md](contracts/evaluation.md#run-protocol), reporting paths and counts only. Tests: `scripts/backfire/scan_test.ts` (the placeholder passes, a planted synthetic key is found) and `plugins/code/backfire/server/privacy_test.ts` (a planted request string, synthetic identifiers and the key value never appear in records, logs, endpoint errors or headers).
- [ ] T054 [US3] On demand: on a machine where Deno, uv, Python and the Hive key are already installed, time the setup of [docs/backfire.md](../../docs/backfire.md) through a passing `plugins/code/backfire/bin/backfire ready`, then run `deno task backfire:eval -- safety --runs 3`, and record the time and outcomes in [research.md](research.md) (SC-007, FR-011, SC-009).
- [ ] T055 [US3] On demand: in two Orca tabs with the staged `backfire` server registered, run the four session checks of [quickstart.md](quickstart.md#8-sessions-in-real-clients-fr-010) (concurrent calls, closing one tab, `kill -9` of a client during a long call, cancelling a call) and record the outcomes in [research.md](research.md) (FR-010).

**Checkpoint**: Faults fail closed, sessions clean up, readiness reports
requested and confirmed facts.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Operator documentation, final measurements and acceptance.

- [ ] T056 [P] Write `docs/backfire.md`: installation, the credential file, readiness, what is sent to Hive, the advisory nature of the tools, and troubleshooting by error type.
- [ ] T057 Update `docs/architecture.md` for the code package's `backfire` server, its component layout and the copied upstream directory, link `docs/backfire.md` from it, and run `deno task docs:generate` (depends on T056).
- [ ] T058 On demand: run `deno task backfire:eval -- benchmark --runs 3`, check that every benchmark response carried reasoning evidence (gate 2), and record SC-001 and SC-002 in [research.md](research.md).
- [ ] T059 On demand, final acceptance: verify the held-out seal, run `deno task backfire:eval -- heldout --runs 3`, repeat the other criteria as [contracts/evaluation.md](contracts/evaluation.md#thresholds) lists, and replace `artifacts/jev-decision-backend/acceptance.json` in one atomic write.
- [ ] T060 Only with the user's approval: post upstream issues for `jev-mcp` (the ESM `eval` worker under Deno, the quadratic `ensureUniqueIds`, stdin end of input ignored) and `system-one-adapter` (request options, issues #45 to #48).
- [ ] T061 Run the offline parts of [quickstart.md](quickstart.md), then `deno task test:backfire-slow`, `deno task check` and `deno task verify`, and report the results to the coordinator, who adds the session's handoff lines under the last task worked on.
- [ ] T062 Blocked until the separate client-installation feature installs the code package through each client's plugin mechanism, and run only with the user's approval, because installing changes saved client configuration: add an `--installed` mode to `scripts/backfire/evaluate.ts` that drives the client's installed code package instead of a staged registration; with the code package installed alone in Codex CLI and in Claude Code, run `deno task backfire:eval -- known-answers --installed --client claude` and `--client codex`, check that only the code plugin's `backfire` server offers the eleven tools in each client, and record the outcomes in [research.md](research.md); FR-001 and SC-008 close only when both clients pass.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: T001 first; nothing from T003 on starts before it. T002 runs any
  time before T017. T003 before T004 to T006; T007 after them; T010 after T008
  and T009; T013 after T007 and T010.
- **Phase 2**: needs T013. Endpoint: T014 to T016 in parallel, then T017, T018,
  T019, then T020. Server: T021 to T023 in parallel; T024 after T019; T025
  after T007, T021 and T023; T026 after T013, T022, T024 and T025; T027 after
  T026. Gates: T029 after T023 and T028; T030 after T026 and T029; T031, T033,
  T034 and T035 after T026; T032 only if T031 fails; T036 after T019; T037
  after T011.
- **User stories**: need every Phase 2 gate. US1, US2 and US3 can then proceed
  in parallel; US2's T044 needs T036; T047 needs T041 and T043; on-demand runs
  need T041, and T058 needs T047.
- **Polish**: T056 any time after T038, and T057 after T056; T058 and T059
  after all stories; T061 last among the tasks that wait for no other feature;
  T062 after the client-installation feature has passed.

### Gate Consequences

| Gate | Task | Stops when it fails |
| --- | --- | --- |
| 1 | T001 | All implementation (T003 on) |
| 2 | T002, T058 | T017 (settings); final acceptance (benchmark evidence) |
| 3 | T036 | T044 and the limit-size cases |
| 4 | T013 | Phase 2 and later |
| 5 | T029, T030 | User stories |
| 6 | T031 | User stories, until T032 passes |
| 7 | T033 | User stories |
| 8 | T034 | User stories |
| 9 | T020, T035 | User stories |
| 10 | T041, T042 | Client runs (T042, T048, T055) |
| 11 | T037 | Hosted CI acceptance only |

### Within Each Story

- Tests come with their code in the same task.
- Fixtures before the runs that use them; offline tests before on-demand runs.

### Parallel Opportunities

- Phase 1: T002 with everything; T004 to T006 together; T008, T009, T011 and
  T012 together.
- Phase 2: the endpoint track (T014 to T020) and the server track (T021 to
  T023) run side by side until T024; T028 any time; T031, T033, T034 and T035
  together after T026.
- Stories: T039 and T040; T043, T044 and T045; T049, T050, T052 and T053.

---

## Parallel Example: User Story 1

```bash
Task: "T039 [US1] gate_flow_test.ts in plugins/code/backfire/server/"
Task: "T040 [US1] Vendor the upstream skill into plugins/code/skills/backfire/"
```

## Parallel Example: User Story 2

```bash
Task: "T043 [US2] Metrics in scripts/backfire/metrics.ts"
Task: "T044 [US2] Limit-size cases in scripts/backfire/fixtures/known-answers-v1.jsonl"
Task: "T045 [US2] scripts/backfire/fixtures/classify-60-v1.jsonl"
```

## Parallel Example: User Story 3

```bash
Task: "T049 [US3] plugins/code/backfire/backend/tests/test_faults.py"
Task: "T050 [US3] plugins/code/backfire/server/faults_test.ts"
Task: "T052 [US3] scripts/backfire/fixtures/safety-v1.jsonl"
Task: "T053 [US3] scripts/backfire/scan.ts and privacy tests"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1, with the held-out set sealed first.
2. Phase 2, until every gate passes.
3. Phase 3: `backfire_gate` through the code plugin.
4. **Stop and validate** with T039 offline and T042 in both clients.

### Incremental Delivery

1. Setup, gates and foundation: the backend answers offline.
2. US1: gated completion claims (MVP).
3. US2: every tool, both languages, maximum sizes.
4. US3: fault handling, readiness and privacy.
5. Polish: documentation, benchmark and final acceptance.

### Parallel Team Strategy

After Phase 2, one worker per story; the endpoint (Python) and server
(TypeScript) tracks of Phase 2 can already go to two workers.

---

## Notes

- [P] tasks touch different files and depend on no incomplete task.
- Each task is sized for one worker and names its files.
- Commit after each task or logical group with a `Spec-Kit-Task: Txxx` trailer.
- Stop at any checkpoint to validate independently.
