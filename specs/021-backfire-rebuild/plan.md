# Implementation Plan: Backfire Rebuilt From jev-judge-mcp

**Branch**: `feature/backfire-rebuild` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/021-backfire-rebuild/spec.md`

## Summary

Backfire's tools, argument handling, questions, decision logic and results
come from a vendored copy of PyModel's jev-judge-mcp 0.6.0 instead of
backfire's port of jev-mcp 0.9.0. The copy keeps its upstream form; backfire
attaches to it only through the seams the upstream already offers:
`Runtime(provider_factory=..., regex_executor=...)`, the `JevTool` and
`Toolset` registry, and the SDK's `MCPServer` overrides that PyModel's own
server uses. Backfire's judge (provider profiles, system-one-adapter,
CHE-33 retries, pseudonymization, judgment records) becomes the provider
behind that seam; its boundary (records, 10 MiB limit, 118-second deadline,
cancellation) wraps the upstream stdio transport. Three narrow patches go
into the vendored copy: linear duplicate-ID handling, a bounded line length
in the stdio reader, and the off-loop work that CHE-38 needs. `backfire_noul`
is rewritten onto the upstream tool framework, and `backfire_extract` runs
patterns with the `regex` library's own timeout (the user's answer).

## Technical Context

**Language/Version**: Python 3.14.4 (the uv workspace's interpreter); the
backfire package's floor rises from 3.11 to 3.12, the upstream's floor.

**Primary Dependencies**: `mcp` 2.2.0 (its `MCPServer`), the vendored
jev-judge-mcp 0.6.0 subset, `system-one-adapter[openai]` 0.2.1 and
`typesafe-sdk` 0.7.1 (unchanged), plus the upstream's runtime needs
`pydantic-settings` 2.x and `httpx` 0.28.x, and `regex` 2026.9.29 for
`backfire_extract`. All pinned exactly in `packages/backfire/pyproject.toml`
and `uv.lock`.

**Storage**: unchanged: backfire's JSONL records under
`$XDG_STATE_HOME/verbose-broccoli/backfire/records`, profiles and
credentials under `$XDG_CONFIG_HOME/verbose-broccoli/backfire/`.

**Testing**: pytest through `npm run test:backfire` (and
`test:backfire-slow`); the vendored upstream tests that cover the vendored
modules run in the same suite; `npm run verify` for everything.

**Target Platform**: Linux (the development laptop, 8 cores) and the
repository's checks; Codex CLI and Claude Code start the server over stdio.

**Project Type**: an MCP server package inside a uv workspace, shipped in
the code and work plugin builds.

**Performance Goals**: no event-loop stall of 1 second or more for any tool
with a 10 MiB message and 16 busy processes; simple regex patterns never
time out under 80 busy processes (spec SC-003, SC-004).

**Constraints**: vendored files keep their upstream form except recorded
changes; vendor and provider details stay in configuration; no private
records or student data in fixtures; billed provider calls only in the final
live check (at most 15).

**Scale/Scope**: about 8,100 upstream lines vendored (62 modules), about
5,000 lines of backfire source of which the port (about 3,400 lines) is
removed, and about 15,000 lines of backfire tests to keep, adapt or remove.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. Proven dependencies | New dependencies are pinned in `pyproject.toml` and `uv.lock`. | Pass |
| II. Working capabilities | The spec makes tool results and error texts acceptance criteria only where it names them (upstream equality, recorded changes). | Pass |
| IV. Current needs | jev-judge-mcp is an open-source upstream, not an earlier project of the user; the old port is removed, not reused. | Pass |
| V. Observable acceptance | Synthetic fixtures only; positive, negative and boundary cases per tool; protocol service after bad input; failing-before tests for CHE-37 and CHE-38; unperformed checks recorded. | Pass |
| VI. Storage | Records stay in the XDG state namespace with their budget. | Pass |
| VII. Minimum implementation | Reuse order followed: upstream source vendored, seams used before patches, three narrow patches, glue only for backfire's own services. No compatibility copy of the port is kept. | Pass |
| IX. Layout | Source under `packages/backfire/src/`; the vendored copy is a module of the existing package, so no fourth plugin or new package. | Pass |
| Product boundaries | No private records, credentials or student data in fixtures, snapshots or reports; repository prose in English. | Pass |
| Workflow | Spec Kit flow, `npm run workflow`/`verify`, Codex workers implement, Claude Code reviews, git flow finish with a review record. | Pass |

Re-check after Phase 1 design: unchanged, all pass. No complexity
exceptions.

## Project Structure

### Documentation (this feature)

```text
specs/021-backfire-rebuild/
├── plan.md              # This file
├── research.md          # The evaluation copy plus Phase 0 decisions
├── data-model.md        # Registry, call context, upstream record
├── quickstart.md        # Validation guide
├── contracts/
│   ├── tools.md         # Tool list, names, order and result framing
│   ├── provider-seam.md # How judge() serves the upstream Runtime
│   └── upstream-record.md
└── tasks.md             # $speckit-tasks output
```

### Source Code (repository root)

```text
packages/backfire/
├── pyproject.toml                 # + jev_judge_mcp module, new pins, Python >=3.12
├── src/
│   ├── jev_judge_mcp/             # NEW: vendored jev-judge-mcp 0.6.0 subset
│   │   ├── LICENSE                # upstream MIT license, unchanged
│   │   ├── THIRD_PARTY_NOTICES.md # upstream notice for jev-mcp 0.5.0 text
│   │   ├── UPSTREAM.md            # revision, files, hashes, every change
│   │   ├── domain/ policy/ validation/ extract/ providers/ tools/
│   │   └── cache.py errors.py ids.py limits.py serialize.py stdio.py ...
│   ├── backfire/
│   │   ├── __main__.py            # serve-mcp and ready, unchanged commands
│   │   ├── server.py              # REWRITTEN: MCPServer subclass + boundary + stdio
│   │   ├── registry.py            # NEW: renamed upstream tools + backfire_noul
│   │   ├── noul.py                # REWRITTEN from tools/noul.py onto JevTool
│   │   ├── jev_provider.py        # NEW: JevProvider over judge()
│   │   ├── regex_executor.py      # NEW: RegexExecutor on the regex library (CHE-37)
│   │   ├── boundary.py            # kept; BoundedLineReader removed
│   │   ├── decisions.py           # updated to the new result fields
│   │   ├── ready.py               # updated to the rebuilt server
│   │   ├── judge.py config.py config.toml failures.py provider.py
│   │   │   records.py validate.py # kept
│   │   ├── tools/ lib.py patterns.py UPSTREAM.md   # REMOVED (the port)
│   ├── backfire_education/        # unchanged
│   └── backfire_tools/            # build.py copies jev_judge_mcp;
│                                  # acceptance/capture_upstream.py REMOVED
└── tests/
    ├── upstream/                  # NEW: vendored upstream tests for the subset
    └── test_*.py                  # kept, adapted, or removed with the port
scripts/backfire/fixtures/upstream-0.9.0/   # REMOVED (port captures)
licenses/THIRD_PARTY_NOTICES.md             # jev-judge-mcp credit replaces jev-mcp's
plugins/{code,work}/skills/backfire/        # tool references checked and updated
docs/backfire.md docs/architecture.md       # updated
```

**Structure Decision**: the vendored copy is one more module of the
existing `backfire` package (`packages/backfire/src/jev_judge_mcp/`), so its
imports stay unchanged, the plugin build copies it by module name like
`backfire_education`, and no new workspace package is needed. Module names
in `backfire/` above are the plan's; a worker may merge two small glue
modules if the result is simpler, but not split the vendored tree.

## Design

### 1. What is vendored

The vendored subset is the import closure of `jev_judge_mcp.tools` and
`jev_judge_mcp.stdio` at `fd6829c`: 62 modules, about 8,100 lines (listed
in `research.md`, R1), plus `LICENSE` and `THIRD_PARTY_NOTICES.md`. The
server entry point, installer, command-line tools, HTTP transport, doctor,
calibration, hooks and packaged skills are not vendored. Unused provider
modules inside the closure (TypeSafe, OpenRouter, Cloudflare, compatible)
stay unchanged; backfire never selects them (FR-006).

### 2. Seams before patches

| Need | Upstream seam used | Upstream patch |
| --- | --- | --- |
| Backfire's judgments | `Runtime(provider_factory=...)` returns a `JevProvider` whose `evaluate` calls `judge()` | none |
| `regex` library matching (CHE-37) | `Runtime(regex_executor=...)` | `extract/executor.py`: `match_all` takes the compile step as a parameter, default `re.compile`, so the regex executor reuses the one candidate pipeline |
| `backfire_` names | backfire builds renamed `JevTool` copies (definition name, tool-name tokens in descriptions, the payload's `tool` value) and passes them to `Toolset` | none |
| `backfire_noul` | a new `JevTool` defined with `define()` and the upstream validators | none |
| Server name, records, deadline | an `MCPServer` subclass modelled on PyModel's `JevMCPServer` (credited), run inside backfire's `Boundary` | none |
| 10 MiB message limit | none | `stdio.py`: bounded line read; an overlong line ends the session as today (`message_limit_exceeded`) |
| Linear duplicate IDs (FR-005) | none | `ids.py`: remember the next suffix per base ID; same IDs and order |
| CHE-38 off-loop work | none where a step is inside upstream code | narrow patches that move the measured synchronous steps (for example line parsing, argument parsing, result serialization) into worker threads |

Every patch and every file not taken is listed in `jev_judge_mcp/UPSTREAM.md`
(contract in `contracts/upstream-record.md`); a test compares each vendored
file with its recorded upstream hash.

### 3. Provider seam

`contracts/provider-seam.md` defines it. In short: the server sets a
per-call context (absolute deadline, record file) when the boundary starts a
call; the provider's `evaluate` reads it, converts the upstream's wire
questions and calls `judge()`, and returns an `Evaluation` with the judge's
answers, usage and confirmed model and the provider name `compatible`, the
value backfire reports today. Judgment failures become upstream
`ProviderError`s (`ProviderConfigError` for `backend_not_configured`) whose
text is backfire's fixed `<type>: <message>`. The upstream retry loop is not
used, so CHE-33's retries in `judge()` stay the only retry owner. The
upstream `Settings` is built with its defaults only
(`Settings.model_construct()`), so `JEV_*` environment variables have no
effect on backfire.

### 4. Server

`backfire serve-mcp` opens the record file, builds the `Toolset` from the
renamed tools plus `backfire_noul`, and runs the `MCPServer`'s low-level
server inside `Boundary.run` over the vendored `stdio_streams()`. Tool
listing and dispatch follow `JevMCPServer` (including the `arguments: null`
error and the notification handlers). Stop signals, session end and
exit status stay as today. Logging goes to stderr.

### 5. CHE-37

The new `RegexExecutor` runs each field's search in a thread
(`anyio.to_thread.run_sync`, abandoned on cancellation) with
`concurrent=True`, and gives the whole field one second of `regex`'s own
timeout, which counts process CPU time; the remaining budget is carried
across the candidate pipeline's repeated searches. A `regex` timeout maps to
the upstream `Timeout` result, a compile error to `Invalid`, so result
fields, caps and reason texts stay the upstream's. Tests use `(a|aa)+$` on
60 `a` characters and a `b`. The failing-before test is written against the
rebuilt server with PyModel's process pool, before the executor changes.

### 6. CHE-38

First a measurement: the bounded-work test (10 MiB per tool over real
stdio, 100 ms loop sampling) runs on the rebuilt server with upstream
behaviour, idle and with 16 busy processes, and a profile names each
synchronous step over about 20 ms. The `backfire_verify` case, with 100,000
identical evidence IDs, fails before the fix (PyModel's quadratic IDs). The
fix makes IDs linear and moves the named steps off the event loop. The
boundary's input digest also moves off the loop if the profile names it.

### 7. Records, readiness, build

`decisions.py` maps each tool's new result fields onto its fixed decision
vocabulary and adds `backfire_score`; records keep their format. `ready.py`
drives the rebuilt server with synthetic calls. `build.py` copies
`jev_judge_mcp` into both builds, license files included.

### 8. What is removed

The port's `backfire/tools/`, `lib.py`, `patterns.py`, `UPSTREAM.md`,
`backfire_tools/acceptance/capture_upstream.py`, the captured
`scripts/backfire/fixtures/upstream-0.9.0/`, and the tests that cover only
them. Before a file goes, the worker lists its importers with
`npm run workflow -- --graph impact` or `rg` and removes or adapts each.

## Implementation phases and ownership

The coordinator (Claude Code) owns Spec Kit records, repository prose
(`docs/`, skills, `licenses/`), integration and commits. Codex workers
(`gpt-6-luna`, `max` effort) implement, each in a disjoint file scope:

1. **Vendor** (one worker): the vendored subset, license files, upstream
   record and its hash test, new pins, the vendored upstream tests, and the
   repository checks' exclusions for vendored files.
2. **Rebuild** (one worker, after 1): provider seam, tool registry and noul,
   server and stdio bound, port removal, and the server-level tests.
3. **Adapt** (one worker, after 2): decisions, readiness, build, and every
   remaining backfire test adapted to the rebuilt server.
4. **Load fixes** (one worker, after 2, parallel with 3): CHE-37 and CHE-38,
   each test failing first, then the fixes and load measurements.
5. **Coordinator**: documents and skills, the three full verify runs, the
   live check, the develop merge review and the finish.

## Complexity Tracking

No constitution violations to justify.
