# Implementation Plan: ShellCheck

**Branch**: `feature/shellcheck` | **Date**: 2026-09-29 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/016-shellcheck/spec.md`

## Summary

Run ShellCheck 0.11.0 on the repository's own shell scripts in `deno task
check`:

- `tools/shellcheck/` is a uv project whose `uv.lock` pins `shellcheck-py`
  0.11.0.1, the PyPI wheels of the official ShellCheck 0.11.0 binary.
  `deno task doctor` checks its environment, and Orca's setup script syncs it.
- A `lint:shell` task lists the scripts with `git ls-files` and runs
  ShellCheck on them; `check` depends on it.
- A root `.shellcheckrc` turns on the four optional checks of FR-005.
- The three owned scripts get their findings fixed: one default finding
  (SC2086 in the finish hook's intended word splitting) and about 80
  `require-variable-braces` findings.

## Technical Context

**Language/Version**: POSIX `sh` scripts; TypeScript on Deno 2.9.6 for the
doctor; TOML and JSON configuration.

**Primary Dependencies**: `shellcheck-py` 0.11.0.1 (MIT wrapper; ShellCheck
itself is GPL-3.0 and runs only as a development tool) through uv 0.11.32.

**Storage**: None.

**Testing**: `deno task test:doctor`, `test:git-flow`, `test:worktree-branch`
and `test:commit-msg`; `deno task lint:shell`, `check` and `verify`.

**Target Platform**: The development machine (Linux x86_64); `shellcheck-py`
also ships macOS and Windows wheels.

**Project Type**: Repository checks.

**Performance Goals**: None.

**Constraints**: `.specify/` stays in its upstream form. CHE-29 (Ruff, on
`feature/python-ruff`) also adds a check to `deno task check`, and CHE-27
was changing code when this plan was written; whichever feature finishes
later merges `develop` and keeps every change. CHE-27's merge into `develop`
(`7e4c92b`) was merged into this branch at `66c4a78` (tasks.md, T006). Spec number 015 is taken by `feature/vault-topics`.

**Scale/Scope**: About ten files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Status |
| --- | --- |
| I. Proven dependencies | PASS. ShellCheck 0.11.0 is pinned through `uv.lock`. |
| II. Working capabilities | PASS. The check runs in `check` and `verify`. |
| III. Sources and ownership | PASS. No data changes. |
| IV. Current needs | PASS. The user's decision of 2026-09-29. |
| V. Observable acceptance | PASS. A clean run, a failing synthetic script and the doctor with and without the environment. |
| VI. Wiki layers and storage | Not affected. |
| VII. One owner, minimum implementation | PASS. Reuse order 1: ShellCheck from its locked wheel, uv, `git ls-files`; the only local code is the task line, the configuration and the doctor's one environment check. |
| IX. Layout | PASS. The pinned tool goes under `tools/`, next to `tools/spec-kit/`. |
| Governance | PASS. The constitution does not change. |
| Workflow | PASS. Spec Kit flow, git flow feature branch, merge-time review. |

Re-check after design: unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/016-shellcheck/
├── spec.md
├── plan.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
tools/shellcheck/{pyproject.toml,.python-version,uv.lock}  # pinned ShellCheck
.shellcheckrc                                              # optional checks
deno.json                                                  # lint:shell, check, doctor description
scripts/doctor.ts, scripts/doctor_test.ts                  # environment check
orca.yaml                                                  # setup sync
scripts/worktree-branch.sh                                 # findings fixed
scripts/git-flow-hooks/pre-flow-feature-finish             # findings fixed
scripts/git-hooks/commit-msg                               # findings fixed
docs/reference/commands.md                                 # regenerated
docs/architecture.md                                       # checks and tool paragraphs
```

**Structure Decision**: The research, data-model, contract and quickstart
documents are left out. The one choice to research, the pinned package, is
recorded in the spec's Assumptions, and there is no interface or data change.

## Work Split and Ownership

- A Codex implementer (`gpt-6-luna` at `max`, terminal path) owns every
  source file above except `docs/architecture.md`.
- Main (Claude Code) owns the Spec Kit records and `docs/architecture.md`,
  reviews the implementer's diff, and integrates.

## Review and Finish

- The merge review for `develop` favors speed: a fresh Claude Code reviewer
  for the Codex-written code and a fresh Codex reviewer (`gpt-6-luna` at
  `max`) for the documents, each given only the scope and requirements.
- Then the review-record commit, a check that `develop` has not moved, and
  `git flow feature finish shellcheck` in the `develop` worktree.

## Complexity Tracking

No constitution violations to justify.
