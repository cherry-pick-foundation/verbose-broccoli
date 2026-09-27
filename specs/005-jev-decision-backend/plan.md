# Implementation Plan: Jev-Style Decision Backend for the Code Plugin

**Branch**: `feature/005-backfire-mcp` | **Date**: 2026-09-26, revised the same
day and on 2026-09-27 for the `packages/backfire/` layout, for one Python
package and for the standard Python project layout | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/005-jev-decision-backend/spec.md`,
clarified on 2026-09-26, including the plan-revision clarifications.

## Summary

The code plugin gains one MCP server, `backfire`, that serves the eleven tools of
`jev-mcp` 0.9.0, renamed with the `backfire_` prefix, with that release's
arguments and results. The server is the plugin's own: one Python package,
`backfire`, on the official MCP Python SDK, with the tools ported from
`jev-mcp`'s TypeScript at the 0.9.0 revision and differing only at the recorded
points of [research.md](research.md#python-package--2026-09-27), chiefly that
`backfire_extract` takes Python patterns. The tools make each judgment in the
same process through TypeSafe's `system-one-adapter` 0.2.1, driving the model
of the selected provider profile; the shipped `hive` profile, the user's
selection, drives DeepSeek V4.1 Flash with medium reasoning effort on Hive. No
code names a provider. Besides the port, locally owned code is glue: the MCP
boundary (content-free tool-call and judgment records, the whole-call deadline,
cancellation and session shutdown), the in-process judge with an
OpenAI-compatible provider subclass configured by the profile, answer
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

**Language/Version**: Python 3.14.4 for the whole package (server, ported
tools, judge, build, readiness, acceptance tooling and tests), pinned in
`.python-version` (package floor 3.11, which `tomllib` needs); existing Deno 2.9.6 tasks for
repository automation call uv. No Deno or Node in the package; Node 22 or later
(host 24.19.0) and npm run only on demand, to capture the upstream fidelity
fixtures from `jev-mcp`'s own lockfile (T029).

**Primary Dependencies**: pinned in `packages/backfire/pyproject.toml` and
`uv.lock`: `mcp` 2.2.0 (the official MCP Python SDK, MIT),
`system-one-adapter[openai]` 0.2.1, which declares `typesafe-sdk>=0.7.0`
(tested and locked: 0.7.1), `rfc8785` 0.1.4 for canonical-JSON digests, and
pytest for tests. Ported source: `jev-mcp` at revision
`a1fcc1e47fc696614f081e23a66ff48a890f22fd` (MIT). uv installs each copy and
starts the server; nothing downloads while serving.

**Storage**: Files only. Config: the selected provider's credential file (mode
0600) and an optional operator `config.toml`. State: tool-call and judgment
records, one locked file per session written by the server, at most 50 MiB in
total, checked before every append. Environment: each component copy's own
`.venv`, made by the install command. Cache: the benchmark download with a
running evaluation's working directory (at most 256 MiB). Data: the sealed held-out set. Repository: one
replaced acceptance record under `artifacts/`. No database and no raw-request
archive.

**Testing**: Offline pytest suites run by `deno task check` through
`deno task test:backfire`: they drive the real server over MCP stdio with the
real judge in front of a scripted fake OpenAI-compatible provider, and check
tool fidelity against fixtures captured once from `jev-mcp` 0.9.0 on Node,
feeding the same scripted answers through a test-only judge. The deadline tests
wait out the real limits and run in `deno task test:backfire-slow`, in CI and
before completion, not in `deno task check`. Live acceptance through
`deno task backfire:eval` and `backfire ready`, which need network access and
provider credit.

**Target Platform**: The operator's Linux x86_64 host; Codex CLI 0.157.0 and
Claude Code 2.1.283 opened in Orca.

**Project Type**: An implementation package, `packages/backfire`, a standard
Python project with the src layout, that the code plugin distributes as its
Agent Plugins 1.0 stdio MCP server through a build step; the declaration starts
it with `uv run`, and one Python process serves each client session.

**Performance Goals**: Tracked goals, not pass/fail: a median of at most 5 s and
95% within 20 s per single-question judgment, and 60 questions within 60 s.

**Constraints**: 120 s per tool call: the MCP boundary answers
`deadline_exceeded` and cancels a call still open 118 s after its request, and
the judge's attempts and retry waits use only the time left; at most four
attempts including the first; the provider's rate limit (Hive: 5 requests per
second per account by default); the profile's `max_tokens` request field
(Hive: 32,768); Choice questions with at least 2 and at most 150 options and a
request cell limit, both fixed by feasibility; MCP messages up to 10 MiB; no
probability rescaling; no downloads at runtime; the client needs `uv` 0.11.32
or later on its `PATH`; no request content,
credentials or caller-supplied identifiers in records or logs.

**Scale/Scope**: One operator with a few concurrent sessions; eleven tools;
four evaluation sets plus the benchmark regression set.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

Checked against constitution **0.18.0** on 2026-09-26. Row IX was re-checked
against **0.20.0** on 2026-09-27; versions 0.19.0 and 0.20.0 changed only IX
and the Governance record.

| Principle | Design alignment |
| --- | --- |
| I. Proven dependencies and storage | uv 0.11.32 and Python 3.14.4 are disclosed with host versions, and the repository's automation stays on Deno 2.9.6; the component's `uv.lock` and `.python-version` pin the dependency graph and the interpreter; install, readiness and tests prove the entry points. The PGlite rule is untouched. |
| II. Working capabilities and data | Acceptance is functional: per-tool known answers in both clients, a 60-item classification, benchmark, safety and held-out sets, and tool fidelity against release 0.9.0. |
| III. Sources and ownership | No student or operational data is read or written; evaluation content is synthetic; the server is the only record writer. |
| IV. Capabilities from current needs | The capability is specified from the user's current needs; no earlier project is a source, and no user data is imported. |
| V. Observable acceptance | Normal, boundary and failure cases per tool; injected faults, client death, cancellation, interrupted record writes and readback of every digest; live checks that were not run are recorded as open. |
| VI. Wiki layers and storage | Not Wiki content. Config, state, cache and data are separated; cache cleanup never removes records or the held-out set. |
| VII. One owner and minimum implementation | The upstream tools are ported to Python with recorded differences instead of used as a dependency ([Complexity Tracking](#complexity-tracking)); the adapter (including its Score), the SDK retry policy, the MCP Python SDK, `rfc8785` and the skill are reused; other local code is glue. Records never exceed 50 MiB: the total is checked under a directory lock before every append, so the bound holds after sessions close or die, and interrupted writes and write failures have defined outcomes. Evaluation runs work within a 256 MiB cache budget, clean their working directory on success, failure and interruption, and replace one acceptance record. There is no archive writer. The generated plugin reference is refreshed by `docs:generate`. The build step copies a fixed list of files with the standard library and adds no packaging logic of its own. Provider-specific values are profile data, not code (FR-019). |
| VIII. Rule validity | No technical exception is claimed. |
| IX. Three plugin packages | All backfire code, including its acceptance tooling, is the implementation package `packages/backfire/`, a Python project with its source under `src/`, outside the root Deno workspace; the distributed copy installs from its own `uv.lock`. `plugins/code` declares the server in `mcp.json` and holds the skill; `deno task backfire:build` writes a code plugin with the component's runtime files to an output directory outside the source tree, so `plugins/code` holds no copy of or link to the package. Nothing imports the package from a plugin. Work and chat are unchanged; no repository-wide runtime is added. The evaluation fixtures stay under `scripts/backfire/fixtures/`. Acceptance runs the built package alone; installing the package in both clients belongs to a separate client-installation feature, and FR-001 stays open until the known-answer set also passes through the installed package. |
| Product and data boundaries | The session-bound server is a service the user selected explicitly, not an implied one; credentials never enter fixtures or reports; repository prose is English. |
| Development workflow | A git flow feature branch merged into `develop` with `--no-ff`, and `Spec-Kit-Task` trailers; filing upstream issues and changing live client configurations need the user's separate approval. |

Post-design re-check (after Phase 1, revised after two plan reviews, the
constitution 0.18.0 amendment, the plan revision of 2026-09-26 and the move to
`packages/backfire/` and the move to one Python package on 2026-09-27): the MCP
boundary and its deadline, the single record writer with its checked budget,
the removed archive and the bounded evaluation storage keep every row above;
the ported upstream logic is the one entry in Complexity Tracking.

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
│   ├── judgment.md                # in-process judgment: request, result, errors, retries
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
packages/backfire/                 # all backfire code: one Python project, outside the root Deno workspace
├── pyproject.toml                 # packages under src/, console command backfire, exact pins
├── .python-version                # exact interpreter pin
├── uv.lock
├── src/
│   ├── backfire/                  # the runtime package, the only one shipped
│   │   ├── __main__.py            # the backfire command: serve-mcp and ready
│   │   ├── server.py              # MCP server on the MCP Python SDK
│   │   ├── boundary.py            # MCP boundary: records, deadline, cancellation, shutdown
│   │   ├── tools/                 # the eleven tools, one module each, ported from jev-mcp 0.9.0 index.ts
│   │   ├── lib.py                 # ported lib.ts helpers, linear unique ids
│   │   ├── patterns.py            # backfire_extract pattern children with the 1,000 ms limit
│   │   ├── judge.py               # in-process judgment through system-one-adapter
│   │   ├── provider.py            # AsyncOpenAIProvider subclass driven by the profile
│   │   ├── validate.py            # answer checks, request limits
│   │   ├── failures.py            # error types, SDK error classes with profile overrides, retry policy
│   │   ├── config.py              # XDG paths, config.toml loading and selection, credential
│   │   ├── records.py             # record files, locks, budget, RFC 8785 digests
│   │   ├── decisions.py           # fixed-vocabulary decision units per tool
│   │   ├── ready.py               # readiness report
│   │   ├── config.toml            # shipped selection (hive) and one [providers.<name>] table per provider
│   │   └── UPSTREAM.md            # port source, revision, original hashes, recorded differences
│   └── backfire_tools/            # development and release programs, not shipped
│       ├── build.py               # writes the distributable code plugin
│       └── acceptance/            # gate probes, evaluation runner and upstream capture
│           ├── evaluate.py
│           ├── metrics.py
│           ├── scan.py
│           ├── probe_provider.py
│           ├── probe_limits.py
│           ├── capture_upstream.py
│           └── scripted_endpoint.py   # scripted System One endpoint for the upstream capture
└── tests/                         # pytest suites, the scripted provider and the test-only judge

plugins/code/
├── mcp.json                       # adds the stdio server "backfire", started with uv run
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
docs/architecture.md               # the package, its build and the port's upstream record
docs/reference/                    # regenerated plugin and command references
deno.json                          # tasks: backfire:build, backfire:install, backfire:ready, backfire:eval, test:backfire, test:backfire-slow
licenses/THIRD_PARTY_NOTICES.md    # jev-mcp (ported) and its skill, system-one-adapter
.github/workflows/check.yml        # installs the pinned uv and Python for test:backfire
```

A built code plugin, written by `deno task backfire:build -- <output>` and
never inside `plugins/` or `packages/`:

```text
<output>/                          # copy of plugins/code/
└── backfire/                      # runtime files of packages/backfire/ only
    ├── pyproject.toml, .python-version, uv.lock
    └── src/backfire/              # without __pycache__/
```

**Structure Decision**: Constitution IX puts reusable implementation packages,
including MCP servers, under `packages/<name>/src/`, and the user moved all
backfire code there on 2026-09-27
([research.md](research.md#component-location-and-distribution-build--2026-09-27))
and made it one Python package the same day
([research.md](research.md#python-package--2026-09-27)), with the standard
Python src layout. The package root holds only `pyproject.toml`,
`.python-version`, `uv.lock` and the pytest suites in `tests/`; every source
file is under `src/`, in the runtime package `backfire` or in the unshipped
`backfire_tools`. The repository has no `plugins/code/backfire/`:
`plugins/code/mcp.json` runs `uv --directory ${PLUGIN_ROOT}/backfire run
--frozen --offline --no-sync backfire serve-mcp`, whose directory exists in a
built code plugin, and the build copies only the project files and
`src/backfire/`. The same command serves `packages/backfire/` during
development and a built plugin, which `uv sync --frozen --no-dev` in its
`backfire/` directory prepares without repository tasks. The ported
tools record their upstream source and recorded differences in
`src/backfire/UPSTREAM.md`. Offline tests, including those of the acceptance
tooling, run through `deno task test:backfire`; live acceptance, which needs
provider credit and the sealed held-out set, runs only on demand. The
evaluation fixtures stay in `scripts/backfire/fixtures/`, and the held-out
general set stays outside the repository until final acceptance
([evaluation.md](contracts/evaluation.md)).

## Feasibility Gates for Tasks

These gates come first in `tasks.md`; a failed gate stops the dependent work.

1. A worker who does not implement the feature writes the held-out set and
   commits only its seal, before implementation starts.
2. Provider settings, run against the selected `hive` profile: its request
   options (`reasoning_effort: "medium"` with `max_tokens: 32768` and
   JSON-object output) are accepted (probes with the earlier thinking switch
   passed on 2026-09-26 and 2026-09-27; medium showed thinking evidence in the
   2026-09-27 quality probes), every benchmark response carries the thinking evidence the
   profile names, and the profile's 401, 400, 405 and 429 mappings hold.
3. Request limits: three runs each at 150, 200 and 250 options and at each
   tool's upstream maximum request, with `backfire_verify`, which has no claim
   cap, at the largest cell count of the other tools, fix the option limit and
   the cell limit as the largest sizes whose answers are correct and finish
   within 60 s at the judge in every run. The probe builds each request so
   that every question has one obvious known answer, which decides
   correctness. The known-answer and safety sets stay authoritative for each
   supported size: a failure there lowers the limits below that size. A
   single-candidate `backfire_find` is an explicit failure.
4. Packaging: in a code plugin built by `deno task backfire:build` outside the
   repository, `uv sync --frozen --no-dev` in `backfire/` makes the copy's
   `.venv` from `uv.lock` with the pinned interpreter, and the declared `uv`
   command serves the eleven tools without downloading. The fresh-cache
   install is a networked, on-demand run; the offline load test installs each
   built copy from prepared caches and starts the declared command with an
   empty inherited environment, `uv` found on the client's `PATH`, as Agent
   Plugins 1.0 clients may start servers.
5. Tool fidelity: `jev-mcp` 0.9.0 on Node (compatible provider, one attempt),
   answering from a scripted System One endpoint, and the Python server,
   answering from the same scripted answers through a test-only judge, return
   identical tool lists (names, descriptions, input schemas), send identical
   judgment requests (`state` and `questions`, in order; none for local-only
   cases), and return identical results and error texts, after mapping `jev_` to `backfire_` and the server
   name `jev-mcp` to `backfire` and applying the port's recorded differences,
   for every known-answer argument set, including the four `backfire_extract`
   cases; the captured Node requests and results become the fixtures of the
   offline fidelity suite.
6. Bounded blocking: at the 10 MiB message limit, no tool stalls the server's
   event loop for 1 s or more, measured as the worst lag of a 100 ms interval
   timer, including `backfire_verify` with 100,000 evidence items sharing one
   id, so the 118 s deadline and cancellations fire on time. `backfire_extract`'s
   pattern children run outside the event loop and belong to gate 8. If any
   tool fails this gate, its preparation moves off the event loop (research.md,
   "One retry layer and one deadline"), which must pass the same measurement,
   before dependent tasks continue.
7. Lifecycle: when the client's input ends during a call or while idle, when
   the client is killed, or when it dies during start, the server and any
   pattern child are gone within 5 s and the provider call is cancelled; a
   killed server leaves no pattern child after its 1,000 ms limit; concurrent
   sessions do not interfere.
8. Deadline: `backfire_extract` with 31 timed-out patterns and one matching
   pattern against a stalled provider ends with a specific judgment error or
   `deadline_exceeded` before 120 s (32 timed-out patterns took 32.0 s on Node
   on 2026-09-26); a call made to stall past 118 s gets `deadline_exceeded`,
   its provider request is cancelled, and another call in the same session
   still answers; cancelling during pattern matching kills the pattern child
   and makes no provider call.
9. Adapter wiring: prompted mode carries the questions and schema in the
   messages; per-call judgment metadata stays separate under concurrent calls;
   the adapter's debug objects never reach logs, errors or records; the
   adapter's Score at the three-level boundaries passes the ported
   `backfire_review` and `backfire_gate`.
10. Client isolation: the staged package, a code plugin built into a temporary
    directory, runs in Claude Code and Codex from a directory outside the
    repository with per-invocation registration; each
    client passes the record directory override to the server, writes each
    tool's arguments and result to its JSON event stream, and leaves no session
    files.
11. The hosted CI runner can install the pinned uv and Python for `test:backfire`;
    hosted runs remain unobserved until they happen.
12. Pattern language: every known-answer `backfire_extract` case gives the same
    result with Python `re` as upstream gives with JavaScript, or is listed in
    `UPSTREAM.md` with the difference it shows.

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
| About 2,100 lines of `jev-mcp` 0.9.0's tool logic are ported to Python and become locally owned code, where AGENTS.md prefers reuse (constitution VII) | The user chose one Python package on 2026-09-27; TypeSafe publishes the adapter only in Python, so one runtime means porting the tools or rewriting the adapter, and FR-013 requires the adapter unchanged | Two runtimes (a TypeScript copy plus a Python endpoint) need a local HTTP endpoint, a child process per session, a token, a metadata header, layered deadlines and two toolchains; TypeScript only rewrites the adapter and TypeSafe's formula; the npm package fails under Deno and offers no record hook |
