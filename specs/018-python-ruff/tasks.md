---

description: "Task list for the Python Ruff check"
---

# Tasks: Python Ruff Check

**Input**: Design documents from `specs/018-python-ruff/`

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

- [x] T001 [US1] Add `tools/ruff/pyproject.toml` and `tools/ruff/uv.lock`
  pinning Ruff 0.16.9 and uv 0.11.32, like `tools/spec-kit/` (FR-001).
- [x] T002 [US1] Check the `tools/ruff` environment in `scripts/doctor.ts`
  with a case in `scripts/doctor_test.ts`, name it in the `doctor` task's
  description in `deno.json`, and sync it in `orca.yaml`'s setup script
  (FR-001).
- [x] T003 [US2] Write the root `ruff.toml` from the Google guide and its
  `pylintrc` as [research.md](research.md) decides, with a one-line reason
  per rule group, left-out rule and exemption; extend it from each
  package's `pyproject.toml`; add `[*.py] indent_size = 4` to
  `.editorconfig`; exclude `.specify/`; fill research.md's rule table
  (FR-002, FR-005, FR-007).
- [x] T004 [US1] Run `ruff check` in the `lint` task, `ruff format --check`
  in `format:check`, and the writing forms in `lint:fix` and `format`, all
  offline and without a cache directory (FR-003, FR-004).
- [x] T005 [US1] Add `scripts/ruff_test.ts` and a `test:ruff` task in the
  `test` dependencies: a public function without a docstring and an
  81-column line fail, an 80-column line and an undocumented test function
  pass, unformatted code fails the format check, and a file under
  `.specify/` is excluded (FR-008).
- [x] T006 [P] [US1] Name the Ruff check and version in
  `docs/architecture.md` and regenerate `docs/reference/` with
  `deno task docs:generate` (FR-009).

- [x] T012 [US1] Use `extend-exclude` in `ruff.toml` so Ruff keeps its
  default excludes; make `scripts/ruff_test.ts` also show that a
  non-vendored file is still checked, so an over-broad exclusion fails the
  test; and give `scripts/doc_sources_test.py` the same target version as
  `scripts/doc_sources.py` (FR-005, FR-008, SC-002).
  - 2026-09-29: Done in `08f45d8`; the coordinator's review then asked to
    keep all Markdown out of the formatter, done in `70dc0da`.

Commit Phase 1 before T007.

- 2026-09-29: A Codex worker (`gpt-6-luna`, max effort, dispatch
  `ctx_4040a29dea40`) did T001 to T007: Phase 1 in `a2f3990`, Markdown kept
  out of Ruff in `172efca` (the clean-code references are vendored), Biome's
  format of the new test in `3f5814a`, and the format-only commit `d2c4e58`,
  which the coordinator reproduced by running the formatter on its parent.
  The Python suites kept their counts (backfire 1,345 passed and 3
  deselected, doc-regions 107, wiki-consistency 118); 813 lint findings
  remain for T008 and T009. The coordinator's review of Phase 1 added T012.

## Phase 2: Mechanical reformat (US1)

- [x] T007 [US1] Run the `format` task's Ruff step and commit only its
  output as `style(python): apply ruff format`, with no hand edits
  (FR-003).

## Phase 3: Hand fixes (US1)

- [x] T008 [P] [US1] Fix the remaining findings in `packages/backfire/`
  without changing behavior (FR-006, FR-007). Two workers split it:
  `src/` (370 findings) and `tests/` (253).
  - 2026-09-29: Two Codex workers (`gpt-6-luna`, max effort, dispatches
    `ctx_400d0b8760ed` and `ctx_e07adde9441e`) committed `ab7fbbd` (src)
    and `c9af5ac` (tests). The coordinator compared each file's syntax tree
    without docstrings, imports and `del … # Unused.` lines: the remaining
    differences are explicit `check=False`, a `None` environment default
    that became `""` before the same falsy check, `_ = endpoint.port`, one
    extracted test variable, two shortened test names and one unused test
    import. backfire kept 1,345 passed and 3 deselected. Each `noqa` names
    its reason, including `N818` on `MessageTooLarge`, a public name kept
    under FR-007.
- [x] T009 [P] [US1] Fix the remaining findings in `packages/doc-regions/`,
  `packages/wiki-consistency/`, `scripts/*.py` and
  `plugins/work/skills/wiki-raw-import/scripts/raw_import.py` without
  changing behavior (FR-006, FR-007). 190 findings.
  - 2026-09-29: A Codex worker (dispatch `ctx_ba2ca398cb9c`) committed
    `13e5b0a`; the same review found only explicit `check=False`, two
    private helpers imported by name instead of through their module, and
    two shortened test names. doc-regions 107, wiki-consistency 118 and
    wiki-raw-import 43 passed as before.

## Phase 4: Verification and review

- [ ] T010 Run `deno task verify`; compare the Python suites' test counts
  with `develop` (SC-001 to SC-004).
- [ ] T011 Merge `develop`, fix new findings, verify, move CHE-29 to In
  Review, run the merge review, resolve findings, commit the review record
  and run `git flow feature finish python-ruff` in the `develop` worktree;
  then move CHE-29 to Done with one completion comment (SC-001).
  - 2026-09-29: `develop` moved twice. The coordinator merged `3627cb2`
    (ShellCheck and others) in `42f59c2` and `07ebf47` (vault rule checks)
    in `a316dcb`, resolving Python conflicts by merging each file three
    ways with the base and `develop` versions run through the formatter,
    and keeping both tools in `deno.json`, `doctor`, `orca.yaml` and
    `docs/architecture.md`. `0c55984` fixed five findings in the first
    merge's new code; a Codex worker (dispatch `ctx_5432ee23678d`) fixes the
    second merge's. wiki-consistency now depends on backfire, so its
    environment needs `deno task wiki-consistency:install`; it then passed
    263 tests.
