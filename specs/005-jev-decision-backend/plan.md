# Implementation Plan: Jev-Style Decision Backend for the Code Plugin

**Branch**: `feature/005-backfire-mcp` | **Date**: 2026-09-26, revised the same
day and on 2026-09-27 for the `packages/backfire/` layout | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/005-jev-decision-backend/spec.md`,
clarified on 2026-09-26, including the plan-revision clarifications.

## Summary

The code plugin gains one MCP server, `backfire`, that serves the eleven tools of
`jev-mcp` 0.9.0, renamed with the `backfire_` prefix, with that release's
arguments and results. The server is
the plugin's own: it runs on Deno 2.9.6 and serves the tools from a copy of
`jev-mcp`'s TypeScript source at the 0.9.0 revision, changed only at seven
recorded points (research.md, "Tool source"). For each client session the
server starts a local System One endpoint as its child. The endpoint answers
with TypeSafe's `system-one-adapter` 0.2.1 driving the model of the selected
provider profile; the shipped `hive` profile, the user's selection, drives
DeepSeek V4.1 Flash with thinking mode on Hive. No code names a provider.
Locally owned code is glue: the server entry with its
MCP boundary (content-free tool-call and judgment records, the whole-call
deadline, cancellation and session shutdown), an OpenAI-compatible provider
subclass configured by the profile, answer
validation without rescaling, request size limits, failure classification with
the TypeSafe SDK's retry policy as the single retry layer, a readiness check,
an evaluation runner, and a build step. All of this code lives in the
implementation package `packages/backfire/`; the build step copies its runtime
files into a distributable code plugin, and the repository's `plugins/code`
holds only the server's declaration and the skill. The adapter's own answer
conversion, including its Score, is used unchanged. The upstream agent skill is
vendored with four narrow changes. Decisions and evidence are in
[research.md](research.md).

## Technical Context

**Language/Version**: TypeScript on Deno 2.9.6 for the MCP server, the copied
tool source, their tests, the build step and the evaluation runner, which drives
the server over MCP; Python 3.14.4 for the endpoint and its
tests, pinned
in `.python-version` (package floor 3.10); existing Deno 2.9.6 tasks for
repository automation. No Node at runtime or in the checks; Node 22 or later
(host 24.19.0) and npm run only once, to capture the upstream fidelity
fixtures from `jev-mcp`'s own lockfile (T029).

**Primary Dependencies**: server, pinned in `packages/backfire/deno.json` and
its `deno.lock`: `@modelcontextprotocol/sdk` 1.30.1, `zod` 4.6.5,
`@typesafe-ai/sdk` 0.6.0 and `canonicalize` 5.0.0, all from npm. Endpoint,
pinned in `uv.lock`: `system-one-adapter[openai]` 0.2.1, which declares
`typesafe-sdk>=0.7.0` (tested and locked: 0.7.1), Starlette, Uvicorn and
pytest. Copied source: `jev-mcp` at revision
`a1fcc1e47fc696614f081e23a66ff48a890f22fd` (MIT). uv and Deno install; neither
downloads while serving.

**Storage**: Files only. Config: the selected provider's credential file (mode
0600) and an optional profile selection. State:
tool-call and judgment records, one locked file per session written by the
server, at most 50 MiB in total, checked before every append. Cache: the
Python environment, Deno's module cache, and the benchmark download with a
running evaluation's working directory (at most 256 MiB). Data: the sealed
held-out set. Repository: one replaced acceptance record under `artifacts/`.
No database and no raw-request archive.

**Testing**: Offline suites run by `deno task check`: `deno test` drives the
real server over MCP stdio with the real endpoint in front of a scripted fake
OpenAI-compatible provider, and checks tool fidelity against fixtures captured
once from `jev-mcp` 0.9.0 on Node; pytest, through `uv run --frozen`, covers
the endpoint. The deadline tests wait out the real limits and run in
`deno task test:backfire-slow`, in CI and before completion, not in
`deno task check`. Live acceptance through `deno task backfire:eval` and `backfire ready`,
which need network access and provider credit.

**Target Platform**: The operator's Linux x86_64 host; Codex CLI 0.157.0 and
Claude Code 2.1.283 opened in Orca.

**Project Type**: An implementation package, `packages/backfire`, that the code
plugin distributes as its Agent Plugins 1.0 stdio MCP server through a build
step; the per-session server hosts a localhost endpoint child.

**Performance Goals**: Tracked goals, not pass/fail: a median of at most 5 s and
95% within 20 s per single-question judgment, and 60 questions within 60 s.

**Constraints**: 120 s per tool call: the endpoint ends every request within
80 s, the transport gives up at 82 s, and the MCP boundary answers
`deadline_exceeded` and cancels a call still open 118 s after its request; at
most four attempts including the first; the provider's rate limit (Hive: 5
requests per second per account by default); the profile's `max_tokens` request field (Hive:
32,768); Choice questions with at least 2 and at most
150 options and a request cell limit, both fixed by feasibility; MCP messages
up to 10 MiB; no probability rescaling; responses under 1 MB; no downloads at
runtime; Deno's default 24-hour minimum dependency age stays on; no request
content, credentials or caller-supplied identifiers in records or logs.

**Scale/Scope**: One operator with a few concurrent sessions; eleven tools;
four evaluation sets plus the benchmark regression set.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

Checked against constitution **0.18.0** on 2026-09-26. Row IX was re-checked
against **0.20.0** on 2026-09-27; versions 0.19.0 and 0.20.0 changed only IX
and the Governance record.

| Principle | Design alignment |
| --- | --- |
| I. Proven dependencies and storage | Deno 2.9.6 (the repository's runtime), uv 0.11.32 and Python 3.14.4 are disclosed with host versions; the component's `deno.lock`, `uv.lock` and `.python-version` pin both dependency graphs and the interpreter; install, readiness and tests prove the entry points, including the endpoint child. The PGlite rule is untouched. |
| II. Working capabilities and data | Acceptance is functional: per-tool known answers in both clients, a 60-item classification, benchmark, safety and held-out sets, and tool fidelity against release 0.9.0. |
| III. Sources and ownership | No student or operational data is read or written; evaluation content is synthetic; the server is the only record writer. |
| IV. Capabilities from current needs | The capability is specified from the user's current needs; no earlier project is a source, and no user data is imported. |
| V. Observable acceptance | Normal, boundary and failure cases per tool; injected faults, client death, cancellation, interrupted record writes and readback of every digest; live checks that were not run are recorded as open. |
| VI. Wiki layers and storage | Not Wiki content. Config, state, cache and data are separated; cache cleanup never removes records or the held-out set. |
| VII. One owner and minimum implementation | The upstream tool source is copied with seven recorded changes instead of used as a dependency ([Complexity Tracking](#complexity-tracking)); the adapter (including its Score), the SDK retry policy and the skill are reused; other local code is glue. Records never exceed 50 MiB: the total is checked under a directory lock before every append, so the bound holds after sessions close or die, and interrupted writes and write failures have defined outcomes. Evaluation runs work within a 256 MiB cache budget, clean their working directory on success, failure and interruption, and replace one acceptance record. There is no archive writer. The generated plugin reference is refreshed by `docs:generate`. The build step copies a fixed list of files with `@std/fs` and adds no packaging logic of its own. Provider-specific values are profile data, not code (FR-019). |
| VIII. Rule validity | No technical exception is claimed. |
| IX. Three plugin packages | All backfire code, including its acceptance tooling, is the implementation package `packages/backfire/`, with its source under `src/`. It has executable Deno code but keeps its own Deno configuration and lock outside the root Deno workspace, like the clean-code skill, because the distributed copy installs from its own lockfile. `plugins/code` declares the server in `mcp.json` and holds the skill; `deno task backfire:build` writes a code plugin with the component's runtime files to an output directory outside the source tree, so `plugins/code` holds no copy of or link to the package. Nothing imports the package from a plugin. Work and chat are unchanged; no repository-wide runtime is added. The evaluation fixtures stay under `scripts/backfire/fixtures/`. Acceptance runs the built package alone; installing the package in both clients belongs to a separate client-installation feature, and FR-001 stays open until the known-answer set also passes through the installed package. |
| Product and data boundaries | The session-bound server is a service the user selected explicitly, not an implied one; credentials never enter fixtures or reports; repository prose is English. |
| Development workflow | A git flow feature branch merged into `develop` with `--no-ff`, and `Spec-Kit-Task` trailers; filing upstream issues and changing live client configurations need the user's separate approval. |

Post-design re-check (after Phase 1, revised after two plan reviews, the
constitution 0.18.0 amendment, the plan revision of 2026-09-26 and the move to
`packages/backfire/` on 2026-09-27): the MCP
boundary and its deadline, the single record writer with its checked budget,
the removed archive and the bounded evaluation storage keep every row above;
the copied upstream source is the one entry in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/005-jev-decision-backend/
├── spec.md
├── plan.md                        # this file
├── research.md                    # Phase 0 decisions and evidence
├── data-model.md                  # Phase 1 entities and rules
├── quickstart.md                  # Phase 1 validation guide
├── contracts/
│   ├── system-one-endpoint.md     # local POST /v1/systemone contract
│   ├── mcp-server.md              # MCP entry, boundary and session lifecycle
│   ├── configuration.md           # credential and storage paths
│   ├── provider-profile.md        # provider profile format and selection
│   ├── readiness.md               # readiness report
│   └── evaluation.md              # evaluation sets, metrics and run protocol
├── checklists/requirements.md
└── tasks.md                       # Phase 2, created by speckit-tasks
```

### Source Code (repository root)

```text
packages/backfire/                 # all backfire code; not a root Deno workspace member
├── deno.json                      # pinned npm and @std imports, nodeModulesDir none
├── deno.lock
├── pyproject.toml                 # endpoint project: package backfire_backend under src/
├── .python-version                # exact interpreter pin
├── uv.lock
├── src/
│   ├── bin/backfire               # entry: serve-mcp | install | ready
│   ├── upstream/                  # jev-mcp 0.9.0 source, copied (MIT)
│   │   ├── package.json           # unchanged; read for the server version
│   │   ├── LICENSE
│   │   ├── upstream.json          # source, revision, original hashes, recorded diff
│   │   └── src/
│   │       ├── index.ts           # changes 1-3 and 7: .ts imports, require in the regex worker, exported server, names
│   │       ├── lib.ts             # change 4: linear ensureUniqueIds
│   │       └── provider.ts        # changes 5-6: compatible branch only, judgment recorder hook
│   ├── server/                    # locally owned TypeScript
│   │   ├── main.ts                # entry: MCP boundary, deadline, shutdown
│   │   ├── endpoint.ts            # endpoint child: start, port, token, stdin lifetime
│   │   ├── records.ts             # record files, locks, budget, RFC 8785 digests
│   │   ├── decisions.ts           # fixed-vocabulary decision units per tool
│   │   ├── ready.ts               # readiness report
│   │   ├── testing/               # scripted endpoint and fake provider for tests
│   │   └── *_test.ts              # offline tests, including tool fidelity
│   ├── backfire_backend/          # Python endpoint
│   │   ├── __main__.py            # serve: bind, report port, exit at stdin end
│   │   ├── endpoint.py            # POST /v1/systemone, deadline, cancellation, header
│   │   ├── provider.py            # AsyncOpenAIProvider subclass driven by the profile, response metadata
│   │   ├── validate.py            # answer checks, Score mean, request limits
│   │   ├── failures.py            # error types, SDK error classes with profile status overrides, SDK retry policy
│   │   ├── config.py              # XDG paths, profile selection and loading, credential
│   │   └── profiles/
│   │       ├── hive.toml          # the shipped provider profile
│   │       └── default.toml       # the shipped default selection: hive
│   ├── acceptance/                # gate probes, evaluation runner and upstream capture
│   │   ├── evaluate.ts
│   │   ├── metrics.ts
│   │   ├── scan.ts
│   │   ├── probe_provider.ts
│   │   ├── probe_limits.ts
│   │   ├── capture_upstream.ts
│   │   └── *_test.ts
│   ├── build.ts                   # writes the distributable code plugin
│   └── build_test.ts
└── tests/                         # pytest suites with a fake provider

plugins/code/
├── mcp.json                       # adds the stdio server "backfire"
└── skills/backfire/               # vendored upstream skill
    ├── SKILL.md                   # four recorded changes
    ├── reference/tools.md
    ├── references/verbose-broccoli.md
    ├── LICENSE
    └── upstream.json

scripts/backfire/fixtures/         # committed evaluation fixtures
├── known-answers-v1.jsonl
├── classify-60-v1.jsonl
├── safety-v1.jsonl
├── heldout-v1.seal.json
└── upstream-0.9.0/                # tool list and results captured from jev-mcp 0.9.0 on Node

artifacts/jev-decision-backend/acceptance.json  # final acceptance record
docs/backfire.md                # operator setup, readiness and troubleshooting
docs/architecture.md               # the package, its build and the copied upstream directory
docs/reference/                    # regenerated plugin and command references
deno.json                          # tasks: backfire:build, backfire:install, backfire:ready, backfire:eval, test:backfire, test:backfire-slow
biome.json                         # excludes packages/backfire/src/upstream/ like other imported code
licenses/THIRD_PARTY_NOTICES.md    # jev-mcp source and skill, system-one-adapter
.github/workflows/check.yml        # installs the pinned uv and Python for test:backfire
```

A built code plugin, written by `deno task backfire:build -- <output>` and
never inside `plugins/` or `packages/`:

```text
<output>/                          # copy of plugins/code/
└── backfire/                      # runtime files of packages/backfire/ only
    ├── deno.json, deno.lock, pyproject.toml, .python-version, uv.lock
    └── src/
        ├── bin/backfire
        ├── upstream/
        ├── server/                # without *_test.ts and testing/
        └── backfire_backend/
```

**Structure Decision**: Constitution IX puts reusable implementation packages,
including MCP servers, under `packages/<name>/src/`, and the user moved all
backfire code there on 2026-09-27
([research.md](research.md#component-location-and-distribution-build--2026-09-27)).
The package root holds only configuration and locks, which the Deno and uv
tools expect there, and the pytest suites; every source file, including the
`bin/backfire` entry, is under `src/`. The repository has no
`plugins/code/backfire/`: `plugins/code/mcp.json` points at
`${PLUGIN_ROOT}/backfire/src/bin/backfire`, which exists in a built code plugin,
and the build copies the runtime files without tests, test doubles, acceptance
tooling or the build itself. The same relative layout lets `src/bin/backfire`
run from `packages/backfire/` during development and from a built plugin,
whose `src/bin/backfire install` prepares it without repository tasks. The
copied upstream source stays in `src/upstream/` with its license and diff
record, apart from locally owned code in `src/server/` and
`src/backfire_backend/`, and the repository's formatter, linter and Clean Code
selection leave it byte-for-byte as recorded. Offline tests, including those of
the acceptance tooling, run through `deno task test:backfire`; live acceptance,
which needs provider credit and the sealed held-out set, runs only on demand. The
evaluation fixtures stay in `scripts/backfire/fixtures/`, and the held-out
general set stays outside the repository until final acceptance
([evaluation.md](contracts/evaluation.md)).

## Feasibility Gates for Tasks

These gates come first in `tasks.md`; a failed gate stops the dependent work.

1. A worker who does not implement the feature writes the held-out set and
   commits only its seal, before implementation starts.
2. Provider settings, run against the selected `hive` profile: its request
   options (`chat_template_kwargs: {"thinking": true}` with
   `max_tokens: 32768` and JSON-object output) are accepted (one probe passed
   on 2026-09-26), every benchmark response carries the thinking evidence the
   profile names, and the profile's 401, 400, 405 and 429 mappings hold.
3. Request limits: three runs each at 150, 200 and 250 options and at each
   tool's upstream maximum request, with `backfire_verify`, which has no claim
   cap, at the largest cell count of the other tools, fix the option limit and
   the cell limit as the largest sizes whose answers are correct and finish
   within 60 s at the endpoint in every run. The probe builds each request so
   that every question has one obvious known answer, which decides
   correctness. The known-answer and safety sets stay authoritative for each
   supported size: a failure there lowers the limits below that size. A
   single-candidate `backfire_find` is an explicit failure.
4. Packaging: in a code plugin built by `deno task backfire:build` outside the
   repository, the server's npm dependencies install with `--frozen` from the
   component's lockfile under Deno's default minimum dependency age, and
   `serve-mcp` runs with `--cached-only`; the copied source loads under Deno
   2.9.6, including the `createRequire` read of `package.json`, and either
   passes `deno check` or is excluded from type checking with the reason
   recorded; uv installs the pinned interpreter and lock. The fresh-cache
   install is a networked, on-demand run; the offline load test installs each
   built copy from prepared caches and serves it with an empty inherited
   environment, as Agent Plugins 1.0 clients may start servers.
5. Tool fidelity: with the same scripted endpoint, `jev-mcp` 0.9.0 on Node
   (compatible provider, one attempt) and the plugin's server on Deno return
   identical tool lists (names, descriptions, input schemas) and identical
   results and error texts, after mapping `jev_` to `backfire_` and the server
   name `jev-mcp` to `backfire`, for every known-answer argument set, including the
   four `backfire_extract` cases; the captured Node results become the fixtures of
   the offline fidelity suite.
6. Bounded blocking: at the 10 MiB message limit, no tool stalls the server's
   event loop for 1 s or more, measured as the worst lag of a 100 ms interval
   timer, including `backfire_verify` with 100,000 evidence items sharing one
   id after change 4, so the 118 s deadline and cancellations fire on time.
   The sequential pattern timeouts of `backfire_extract` are asynchronous
   waits and belong to gate 8. If any tool fails this gate, calls move into
   per-call workers (research.md, "One retry layer and one deadline"), which
   must pass the same measurement, before dependent tasks continue.
7. Lifecycle: when the client's input ends during a call or while idle, when
   the client is killed, or when it dies during start, the server and the
   endpoint are gone within 5 s and the provider call is cancelled; a killed
   server leaves no endpoint after 2 s; concurrent sessions do not interfere.
8. Deadline: `backfire_extract` with 31 timed-out patterns and one matching pattern
   against a stalled provider fails with the transport's error before 118 s
   (32 timed-out patterns took 32.0 s on Node on 2026-09-26); a call made to
   stall past 118 s gets `deadline_exceeded`, its provider request is
   cancelled, and another call in the same session still answers; cancelling
   during pattern matching makes no provider call.
9. Adapter wiring: prompted mode carries the questions and schema in the
   messages; per-request metadata stays separate under concurrent requests;
   the adapter's debug objects never reach logs, errors or the
   `X-Judgment-Metadata` header; the adapter's Score at the three-level boundaries
   passes the copied `backfire_review` and `backfire_gate`.
10. Client isolation: the staged package, a code plugin built into a temporary
    directory, runs in Claude Code and Codex from a directory outside the
    repository with per-invocation registration; each
    client passes the record directory override to the server, writes each
    tool's arguments and result to its JSON event stream, and leaves no session
    files.
11. The hosted CI runner can install the pinned uv and Python for `test:backfire`;
    hosted runs remain unobserved until they happen.

Outside this feature: installing the code package through each client's plugin
mechanism belongs to a separate client-installation feature. That feature
installs a code plugin built by `deno task backfire:build`, because the
repository's `plugins/code` declares the `backfire` server but does not contain
it. FR-001 and SC-008 also need the known-answer set to pass through that
installed package in both clients, which T062 runs once that feature has
passed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| About 2,500 lines of `jev-mcp` 0.9.0 TypeScript are copied into the repository with seven recorded changes, where AGENTS.md prefers a dependency (constitution VII) | The npm package does not fit: its `jev_extract` fails under Deno, its stdio server ignores the end of input, and it offers no hook for verdict records; it is also nine days old, with 0.8.0 and 0.9.0 about 26 hours apart | The npm package on Node needs a second JavaScript runtime and the relay around a black box; the npm package on Deno with a patched copy through `links` is still a patch, needs `node_modules` and waits out Deno's minimum age on every release; new tools would drop the validated question design (FR-013) |
