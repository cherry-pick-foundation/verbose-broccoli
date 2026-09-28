# Implementation Plan: Python Ruff Check

**Branch**: `feature/python-ruff` | **Date**: 2026-09-29 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/018-python-ruff/spec.md`

## Summary

Add Ruff 0.16.9, configured from the Google Python style guide and its
`pylintrc`, to the repository checks, and make the existing Python code pass:

- `tools/ruff/` pins Ruff with a uv lock; `doctor` and Orca's setup script
  handle it like `tools/spec-kit/`.
- A root `ruff.toml` holds the rule set with a one-line reason per rule
  group, left-out rule and exemption; the three packages extend it so each
  keeps its own Python version.
- The existing `lint` and `format:check` tasks also run `ruff check` and
  `ruff format --check`, so `deno task check` and `deno task verify` run
  them; `lint:fix` and `format` run the writing forms.
- One commit holds only the mechanical `ruff format` output. Later commits
  fix the remaining findings by hand.
- A small Deno test checks the configuration with synthetic input.

The research, including the rule table, is in [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11, 3.13 and 3.14 (by package); TypeScript
on Deno 2.9.6 for tasks, `doctor` and the test.

**Primary Dependencies**: Ruff 0.16.9 through uv 0.11.32.

**Storage**: None.

**Testing**: `deno task check` and `deno task verify`; the Python suites
(`test:backfire`, `test:doc-regions`, `test:wiki-consistency`) keep their
counts; a new Deno test for the configuration.

**Target Platform**: The development machine (Linux) and Orca worktrees.

**Project Type**: Repository checks.

**Performance Goals**: None beyond the existing check run.

**Constraints**: Offline and read-only in the checks (`--no-cache`, no
`.ruff_cache/` left behind); no preview rules; vendored upstream code
excluded, not edited.

**Scale/Scope**: 120 tracked Python files, 115 outside `.specify/`. About
99 files reformatted once; a few hundred hand fixes, mostly docstrings for
public API and lines over 80 columns.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Proven Dependencies**: Ruff is pinned to one version with hashes in
  `uv.lock`. Pass.
- **V. Observable Acceptance**: The Deno test covers a positive, a negative
  and a boundary case plus the vendored-code exclusion with synthetic input;
  the Python suites keep their counts. Pass.
- **VII. Minimum Implementation and reuse order**: Ruff and its Black-style
  formatter are reused as they are; the only local code is task wiring, a
  `doctor` line and the test. The mapping from `pylintrc` reuses
  `pylint-to-ruff` and Ruff's own pylint table rather than a hand-made list.
  Pass.
- **IX. Layout**: The tool's environment goes under `tools/`, the test under
  `scripts/`. Pass.
- **Development workflow**: Spec Kit records here; the develop merge review
  and `git flow feature finish` follow the constitution. Pass.

Post-design re-check: no change.

## Project Structure

### Documentation (this feature)

```text
specs/018-python-ruff/
├── spec.md
├── plan.md
├── research.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
tools/ruff/pyproject.toml, uv.lock      # new: pinned Ruff
ruff.toml                               # new: the rule set
packages/*/pyproject.toml               # [tool.ruff] extend
.editorconfig                           # [*.py] indent_size = 4
deno.json                               # lint, lint:fix, format, format:check,
                                        # doctor description, test task
scripts/doctor.ts, scripts/doctor_test.ts
scripts/ruff_test.ts                    # new: configuration test
orca.yaml                               # uv sync --locked --project tools/ruff
docs/architecture.md, docs/reference/*  # tool list; generated tables
packages/**/*.py, scripts/*.py,
plugins/work/skills/wiki-raw-import/scripts/raw_import.py   # fixes
```

## Commits

1. Tooling and configuration, with the Deno test and documents (`build` or
   `feat`, as the diff decides).
2. `style(python): apply ruff format` — only the formatter's output, taken
   with the final configuration, no hand edits.
3. Hand fixes, grouped by package, each keeping behavior and tests.

The checks pass only after the last commit; the commit hook checks messages,
not the checks, so the intermediate commits are allowed.

## Validation

1. `uv sync --locked --project tools/ruff`, then `deno task doctor` passes;
   with `tools/ruff/.venv` removed, it fails and names the repair command.
2. `deno task lint` and `deno task format:check` report nothing.
3. `deno task test` runs the configuration test and the Python suites; the
   suites' counts match `develop`.
4. `deno task verify` passes after the final merge of `develop`.
