# Implementation Plan: Turborepo trial

**Branch**: `feature/turborepo` | **Date**: 2026-09-29 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/019-turborepo/spec.md`

## Summary

Move the repository's tooling to Turborepo 2.11.5 on the trial branch:

- A root `package.json`, `package-lock.json` and `.npmrc` replace the root
  `deno.json` and `deno.lock`; its scripts and a root `turbo.json` replace the
  Deno tasks, and `npm run check` runs `turbo run check`.
- TypeScript runs on Node.js 24.19 with type stripping. A two-line preload
  sets `globalThis.Deno` from `@deno/shim-deno`; only the call sites the shim
  cannot serve are rewritten ([research.md](research.md), D1 and D2).
- A root `pyproject.toml`, `.python-version` and `uv.lock` make `backfire`,
  `doc-regions` and `wiki-consistency` one uv workspace that Turborepo
  discovers with `futureFlags.experimentalPythonWorkspaces`. The packages
  build with `uv_build`; readiness, the doctor and the plugin build follow
  the shared lock and environment (D6, D7).
- Only the sites that `backfire_classify` marks `must_change` or `delete` are
  edited ([evidence/classify.json](evidence/classify.json)).

## Technical Context

**Language/Version**: TypeScript on Node.js 24.19 (type stripping); Python
3.14.4 through uv 0.11.32; POSIX `sh` hooks; JSON, TOML and YAML
configuration.

**Primary Dependencies**: `turbo` 2.11.5, `@deno/shim-deno` 0.19.2 and
Prettier from npm; the JSR packages already in use through npm aliases on
`npm.jsr.io`; the npm packages already pinned in `deno.json`; `uv_build`.

**Storage**: None.

**Testing**: `node:test` for the TypeScript suites; pytest for the Python
packages; `npm run check` (`turbo run check`) and `npm run verify`.

**Target Platform**: The development machine (Linux x86_64). The GitHub
workflows change where they must but are not run.

**Project Type**: Repository tooling.

**Performance Goals**: None; the report compares check wall-clock time.

**Constraints**: `AGENTS.md`, the constitution, the user's global tools,
Linear and other worktrees stay unchanged. CHE-29 (`feature/python-ruff`)
changes Python lint settings and tasks, and CHE-26
(`feature/vault-rule-checks`) changes wiki-consistency checks; the report
names the overlaps. The shipped clean-code skill stays on Deno (D5).

**Scale/Scope**: About 60 files, set by the classification.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Status |
| --- | --- |
| I. Proven dependencies | PASS. npm packages pinned in `package-lock.json`, Python packages in the root `uv.lock`. |
| II. Working capabilities | PASS on the trial branch when `npm run check` passes; the trial is not merged. |
| III. Sources and ownership | PASS. No data changes. |
| IV. Current needs | PASS. The user's decision of 2026-09-29. |
| V. Observable acceptance | PASS. The existing suites, `test_load`, `test_ready`, `test_entry`, the doctor tests and the Turborepo check run on the branch. |
| VI. Wiki layers and storage | Not affected. |
| VII. One owner, minimum implementation | PASS. Reuse order 1 and 2: Node.js built-ins, the shim, Turborepo, uv; local code is the preload, task definitions and the rewritten call sites. |
| IX. Layout | CHECK. "A package joins a toolchain workspace ... only when it has executable code for that toolchain" holds: the uv workspace has the three Python packages only. "Do not require one repository-wide runtime ... or composition entry point" names runtime and composition for plugins; Turborepo is a development task runner, and the report asks the user to confirm. |
| Governance | CHECK. The constitution and `AGENTS.md` name `deno task workflow` and `deno task verify`; the trial proposes wording and does not edit them. |
| Workflow | PASS. Spec Kit flow; `deno task workflow` guides the work until the trial replaces it, then `npm run workflow`. |

Re-check after design: unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/019-turborepo/
├── spec.md
├── plan.md
├── research.md
├── tasks.md
├── report.md            # the trial report
└── evidence/            # backfire judgments and check logs
```

### Source Code (repository root)

The classification sets the exact list; the owners are:

```text
package.json, package-lock.json, .npmrc, turbo.json   # new root tooling
scripts/deno_shim.mjs                                  # preload
tsconfig.json                                          # tsc replaces deno check
pyproject.toml, .python-version, uv.lock               # root uv workspace
packages/*/pyproject.toml, packages/*/uv.lock          # uv_build; locks removed
packages/backfire/src/backfire/ready.py, backfire_tools/build.py
packages/*/tests/*                                     # selected test changes
scripts/*.ts, scripts/commitlint.config.mjs            # selected call sites
scripts/git-hooks/commit-msg, scripts/git-flow-hooks/pre-flow-feature-finish
orca.yaml, .github/workflows/*.yml, .gitignore, biome.json
docs/architecture.md, docs/backfire.md, docs/reference/*.md (regenerated)
deno.json, deno.lock                                   # removed at the root
```

**Structure Decision**: No data model, contracts or quickstart: the trial
changes tooling, not interfaces. The report is the deliverable.

## Work Split and Ownership

- Codex implementers (`gpt-6-luna` at `max`, terminal path), one per
  disjoint file scope in [tasks.md](tasks.md). Each changes only the sites
  listed for its task.
- Main (Claude Code) owns the Spec Kit records, the report and the
  documentation prose, reviews each diff with `backfire_review` and by
  reading it, commits, and runs the final checks and `backfire_gate`.

## Review and Finish

The trial ends with the report to the develop session. No develop merge
review, review record or `git flow feature finish` is part of this feature;
merging is the user's separate decision.

## Complexity Tracking

| Item | Why | Simpler alternative rejected |
| --- | --- | --- |
| Deno kept for the shipped clean-code skill | The skill's users run it with Deno (D5) | Moving it changes what users install; the user decides |
