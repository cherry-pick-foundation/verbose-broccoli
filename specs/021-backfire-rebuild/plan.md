# Implementation Plan: Backfire Rebuilt on jev-judge-mcp

**Branch**: `feature/backfire-rebuild` | **Date**: 2026-09-29, redesigned 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/021-backfire-rebuild/spec.md`

## Summary

Backfire becomes a thin layer over the published `jev-judge-mcp==0.6.0`.
Its entry point builds PyModel's `JevMCPServer` from PyModel's `Toolset`,
`Runtime` and `TOOLS`, adds `jev_noul`, and runs PyModel's `serve()`. It
plugs in only through PyModel's own arguments: `provider_factory` (backfire
profiles: Hive through system-one-adapter, or a Jev provider through
PyModel's `resolve_provider` or the ported Vercel provider, wrapped by
pseudonymization in the work plugin). `jev_extract` keeps PyModel's own
regex worker pool (the user dropped the `regex` library on 2026-09-30).
Everything else backfire owned goes: the port, the boundary, records,
readiness, size limits, extra Hive checks, acceptance tools, the plugin
build tool and the vendored copy. What needs PyModel's code (CHE-38, and
CHE-37 if its rerun shows false time-outs) is prepared as a patch and a
pull-request text for PyModel.

## Technical Context

**Language/Version**: Python 3.14.4 (the uv workspace's interpreter);
backfire's floor is Python 3.12, PyModel's.

**Primary Dependencies**: `jev-judge-mcp` 0.6.0 (PyPI, MIT), `mcp` 2.2.0,
`system-one-adapter[openai]` 0.2.1, `typesafe-sdk` 0.7.1, and
`phonenumbers` for the education extra; all pinned in
`packages/backfire/pyproject.toml` and `uv.lock`.

**Storage**: profiles in the shipped `config.toml` files and the operator's
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml`; keys in `0600`
credential files; the education mapping table as today. No records.

**Testing**: pytest through `npm run test:backfire`; local stubs for every
provider; `npm run verify` for everything.

**Target Platform**: Linux; Codex CLI and Claude Code start the server over
stdio from the repository checkout.

**Project Type**: glue around a published MCP server library.

**Performance Goals**: simple regex patterns never time out with 80 busy
processes; every tool except the known CHE-38 case keeps event-loop stalls
under 1 second with 16.

**Constraints**: no edit or copy of PyModel's code; about 300 to 500 lines
of own code outside tests and pseudonymization, reported against
`develop`; vendor details in configuration; no private data in fixtures;
billed calls only in the final live checks.

**Scale/Scope**: from about 4,500 own lines (with the partly done first
design in the worktree) down to about 500, plus the pseudonymization module.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. Proven dependencies | `jev-judge-mcp` pinned in `pyproject.toml` and `uv.lock`. | Pass |
| II. Working capabilities | CHE-38's fix in PyModel is recorded as open, not counted as done. | Pass |
| V. Observable acceptance | Stubs for each provider, CHE-37's load numbers, the CHE-38 known failure recorded, unperformed checks recorded. | Pass |
| VII. Minimum implementation | Reuse order: the published dependency and its extension points, one ported 60-line provider, glue only. Code the user no longer needs is removed. | Pass |
| IX. Layout | Source stays in `packages/backfire/src/`; plugins name repository paths; no new package. | Pass |
| Product boundaries | No private data in fixtures; the held-out file outside the repository stays untouched. | Pass |
| Workflow | Spec Kit flow, Codex workers implement, Claude Code reviews, git flow finish with a review record. | Pass |

Re-check after Phase 1 design: unchanged, all pass.

## Project Structure

### Documentation (this feature)

```text
specs/021-backfire-rebuild/
├── plan.md  research.md  data-model.md  quickstart.md  tasks.md
├── contracts/
│   ├── tools.md           # server identity and tool list
│   └── provider-seam.md   # profiles, provider factory, pseudonymization
└── upstream/              # prepared PyModel contribution
    ├── pymodel.patch
    └── pull-request.md
```

### Source Code (repository root)

```text
packages/backfire/
├── pyproject.toml          # jev-judge-mcp==0.6.0; no vendored module
├── src/
│   ├── backfire/
│   │   ├── __main__.py     # serve-mcp [--education]
│   │   ├── config.py       # profile and key-file loading, simplified
│   │   ├── config.toml     # shipped Hive profile and an unselected Vercel profile
│   │   ├── failures.py     # JudgmentError only
│   │   ├── providers.py    # provider factory: Hive, Jev profiles, education wrapper
│   │   ├── vercel.py       # Vercel provider ported from jev-agent-tools 0.1.2
│   │   └── noul.py         # jev_noul on PyModel's tool framework
│   └── backfire_education/ # the pseudonymization module, unchanged
└── tests/                  # rewritten and small
plugins/code/mcp.json plugins/work/mcp.json        # start packages/backfire
plugins/work/skills/wiki-consistency/SKILL.md      # packages/ paths
plugins/{code,work}/skills/backfire/               # jev_ names
packages/doc-regions/ packages/wiki-consistency/   # jev_ tool names
docs/backfire.md docs/architecture.md licenses/THIRD_PARTY_NOTICES.md
```

Removed: `packages/backfire/src/jev_judge_mcp/` and
`packages/backfire/tests/upstream/` (the vendored copy and its tests),
`boundary.py`, `decisions.py`, `judge.py`, `provider.py`, `ready.py`,
`records.py`, `registry.py`, `server.py`, `validate.py`, `jev_provider.py`
(its code moves into `providers.py`), `packages/backfire/src/backfire_tools/`,
`scripts/backfire/fixtures/`, the port (already removed in the worktree),
and the tests of all of these. Module names are the plan's; a worker may
merge small modules if the result is simpler.

## Design

### 1. Entry point

`backfire serve-mcp [--education]` follows PyModel's own `server.main()`
for the stdio path: `load_settings()`, the startup gates that apply,
`configure_logging`, then `JevMCPServer(toolset=Toolset(Runtime(settings,
provider_factory=...), (*TOOLS, NOUL)), log_level=...)`,
`freeze_startup_heap()`, `anyio.run(serve, server, settings)`, and PyModel's
exit sequence. `--education` selects the education configuration
(pseudonymization on, the education profile), which today the work build
copies from `backfire_education/config.toml`.

### 2. Profiles and providers

`config.py` reads the shipped configuration (code or education) and the
operator's file as today, selects a profile, and reads its key from a
`0600` file owned by the user: by default `<profile>.env` in backfire's
configuration directory, or the `credential_file` path the profile names
(the Vercel profile names the chat plugin's `jev.env`). Two kinds:

- **Hive (general model)**: a `JevProvider` subclass whose `_send` asks
  system-one-adapter with the profile's address, model, key and extra
  request fields, and returns PyModel's `Evaluation`. PyModel's
  `JevProvider.evaluate` retries it (408, 429, 5xx); CHE-33's rule adds one
  case: a normal-looking reply without an answer counts as a retryable
  failure. CHE-33's existing test for that case is kept and adapted.
- **Jev**: `jev_provider = "typesafe" | "openrouter" | "cloudflare" |
  "compatible"` builds PyModel `Settings` from the profile (provider name,
  key, address or account) with `Settings.model_construct()` and calls
  PyModel's `resolve_provider`; `"vercel"` builds backfire's Vercel
  provider.

With `--education`, the factory wraps the chosen provider: pseudonymize
state and questions, call the inner provider, restore the answers.
Configuration errors raise PyModel's `ProviderConfigError` with backfire's
`backend_not_configured` text naming the profile or file, so PyModel
reports them per call.

### 3. Vercel provider

A subclass of PyModel's `HttpProvider`, like its `compatible` provider,
ported from jev-agent-tools 0.1.2's `transports/vercel.js`
([research.md](research.md) R11): one POST of `{state, questions}` to the
profile's address with the gateway headers, Noul questions sent as
`boolean` and answers mapped back, confidence from
`providerMetadata.typesafe.confidence`, usage from `inputTokens` and
`outputTokens`, the model defaulting to `typesafe-ai/jev`. Credited with
its MIT notice in the module and in `licenses/THIRD_PARTY_NOTICES.md`.

### 4. `jev_noul`

Worker B's `noul.py` becomes `jev_noul`: jev-mcp 0.9.0's definition,
questions and decision logic on PyModel's `define`, `JevTool`,
`ToolResult` and `frame`. PyModel's argument compiler has no
`exclusiveMinimum`, so the published schema drops that keyword (the
description already says "Must exceed 0.5") and a `Refinement` on
`auto_accept` enforces it.

### 5. CHE-37

`jev_extract` keeps PyModel's default `ProcessRegexExecutor` (a warmed
pool of worker processes running Python's `re`). CHE-37's heavy-load
reproduction (80 busy processes, simple and runaway patterns, including
right after a runaway pattern killed a worker) is rerun against it through
backfire's server. If simple patterns never time out falsely, the record
says the warmed pool resolves CHE-37; if they do, the smallest fix (for
example counting only the worker's own CPU time for the one-second limit)
goes into the PyModel contribution with a test that fails before it.

### 6. CHE-38 and the upstream contribution

`test_bounded_work.py` keeps its 10 MiB per-tool cases over real stdio and
its 1-second check, marks the `jev_verify` case as an expected failure
naming CHE-38, and checks every other tool, `jev_noul` included. A worker
clones PyModel at `v0.6.0` under `/tmp`, writes the fixes (linear
`ensure_unique_ids`, a bounded stdin line, `exclusiveMinimum` in the
argument compiler, moving the measured synchronous steps off the event
loop, and CHE-37's fix if its numbers call for one) with PyModel-style tests,
runs PyModel's suite, checks that the `jev_verify` case passes against the
patched package, and stores `upstream/pymodel.patch` and
`upstream/pull-request.md` in this feature. Nothing is published.

### 7. Plugins and consumers

Both `mcp.json` files run `uv --directory ${PLUGIN_ROOT}/../../packages/backfire
run --frozen --offline --no-sync backfire serve-mcp`, the work plugin with
`--education`. The wiki-consistency skill's commands use the repository's
`packages/` from its folder. The doc-regions and wiki-consistency request
builders use `jev_` names. `package.json` and `turbo.json` lose the build,
ready and evaluation scripts.

## Implementation phases and ownership

1. **Core** (Codex worker): `packages/backfire` (source, tests,
   `pyproject.toml`), `uv.lock`, the backfire scripts in `package.json` and
   `turbo.json`, `scripts/backfire/`; CHE-37's load numbers; the
   bounded-work known failure.
2. **Upstream patch** (Codex worker, parallel with 1): the PyModel
   contribution under `specs/021-backfire-rebuild/upstream/`, built in a
   `/tmp` clone.
3. **Plugins and consumers** (Codex worker, after 1): `plugins/*/mcp.json`,
   the wiki-consistency skill paths, the doc-regions and wiki-consistency
   request builders and their tests, and `scripts/` checks that name the
   build or the tools.
4. **Coordinator**: specs, `docs/`, the backfire skills' prose,
   `licenses/`, the three verify runs, the live checks (Hive, then one
   Vercel judgment), the own-code count, the merge review and the finish.

## Complexity Tracking

No constitution violations to justify.
