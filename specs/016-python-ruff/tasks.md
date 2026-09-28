---

description: "Task list for the Python Ruff check"
---

# Tasks: Python Ruff Check

**Input**: Design documents from `specs/016-python-ruff/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md)

**Tests**: `scripts/ruff_test.ts` checks the configuration with synthetic
input (FR-008); the existing Python suites prove unchanged behavior (FR-006).

**Organization**: Main (Claude Code) owns the Spec Kit records, reviews
each Codex worker's diff and commits, and runs the merge. Codex workers
(`gpt-6-luna`, max effort) implement T001 to T009. A fresh Claude Code
reviewer gives the merge review of the code; a fresh Codex reviewer reviews
the coordinator's records.

**Private data**: No task writes a student name or record into the
repository or into Orca or Linear messages.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Tooling and configuration (US1, US2)

- [ ] T001 [US1] Add `tools/ruff/pyproject.toml` and `tools/ruff/uv.lock`
  pinning Ruff 0.16.9 and uv 0.11.32, like `tools/spec-kit/` (FR-001).
- [ ] T002 [US1] Check the `tools/ruff` environment in `scripts/doctor.ts`
  with a case in `scripts/doctor_test.ts`, name it in the `doctor` task's
  description in `deno.json`, and sync it in `orca.yaml`'s setup script
  (FR-001).
- [ ] T003 [US2] Write the root `ruff.toml` from the Google guide and its
  `pylintrc` as [research.md](research.md) decides, with a one-line reason
  per rule group, left-out rule and exemption; extend it from each
  package's `pyproject.toml`; add `[*.py] indent_size = 4` to
  `.editorconfig`; exclude `.specify/`; fill research.md's rule table
  (FR-002, FR-005, FR-007).
- [ ] T004 [US1] Run `ruff check` in the `lint` task, `ruff format --check`
  in `format:check`, and the writing forms in `lint:fix` and `format`, all
  offline and without a cache directory (FR-003, FR-004).
- [ ] T005 [US1] Add `scripts/ruff_test.ts` and a `test:ruff` task in the
  `test` dependencies: a public function without a docstring and an
  81-column line fail, an 80-column line and an undocumented test function
  pass, unformatted code fails the format check, and a file under
  `.specify/` is excluded (FR-008).
- [ ] T006 [P] [US1] Name the Ruff check and version in
  `docs/architecture.md` and regenerate `docs/reference/` with
  `deno task docs:generate` (FR-009).

Commit Phase 1 before T007.

## Phase 2: Mechanical reformat (US1)

- [ ] T007 [US1] Run the `format` task's Ruff step and commit only its
  output as `style(python): apply ruff format`, with no hand edits
  (FR-003).

## Phase 3: Hand fixes (US1)

- [ ] T008 [P] [US1] Fix the remaining findings in `packages/backfire/`
  without changing behavior (FR-006, FR-007).
- [ ] T009 [P] [US1] Fix the remaining findings in `packages/doc-regions/`,
  `packages/wiki-consistency/`, `scripts/*.py` and
  `plugins/work/skills/wiki-raw-import/scripts/raw_import.py` without
  changing behavior (FR-006, FR-007).

## Phase 4: Verification and review

- [ ] T010 Run `deno task verify`; compare the Python suites' test counts
  with `develop` (SC-001 to SC-004).
- [ ] T011 Merge `develop`, fix new findings, verify, move CHE-29 to In
  Review, run the merge review, resolve findings, commit the review record
  and run `git flow feature finish python-ruff` in the `develop` worktree;
  then move CHE-29 to Done with one completion comment (SC-001).
