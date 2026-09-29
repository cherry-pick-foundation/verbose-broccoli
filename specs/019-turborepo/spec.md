# Feature Specification: Turborepo, Node.js and a uv workspace

**Feature Branch**: `feature/turborepo`

**Created**: 2026-09-29

**Status**: In progress (the trial became the real change on 2026-09-29)

**Linear issue**: CHE-32

**Input**: Linear issue CHE-32, "Trial: move the monorepo to Turborepo, with
Node for TypeScript and a uv workspace for Python", and the brief with which
the orchestrator of the `develop` worktree started this trial on 2026-09-29.
The user chose to switch the repository's tooling to Turborepo, to move the
TypeScript side from Deno to Node.js, and to run the three Python packages
(`backfire`, `doc-regions`, `wiki-consistency`) as one native uv workspace
under Turborepo's experimental Python support. Backfire judgments select the
parts that must change, and only those change. The trial's outcome was a
report ([report.md](report.md)). On 2026-09-29 the user made it the real
change, relayed by the orchestrator of the `develop` worktree: remove Deno
completely, including the `@deno/shim-deno` preload and the shipped
clean-code skill's Deno runtime; merge `develop` and redo the selection on
that base; apply the governance wording to `AGENTS.md` and the
constitution; and finish the feature into `develop` through the normal
review path. The user kept Prettier for YAML and accepted the weaker Node
permission model with its losses listed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The checks run through Turborepo (Priority: P1)

An agent on the trial branch runs one command and gets every check that
`deno task check` runs today, now through Turborepo's task graph.

**Why this priority**: It is the trial's goal; without it there is nothing
to report.

**Independent Test**: On a clean trial worktree, run the Turborepo check and
compare its list of checks with `deno task check` at the base commit.

**Acceptance Scenarios**:

1. **Given** the trial branch with its environments set up, **When** the
   Turborepo check runs, **Then** it runs the runtime doctor, formatting,
   lint, shell lint, type check, plugin validation, the clean-code and
   clean-architecture checks, every test suite, the documentation check and
   the doc-regions check, and it passes.
2. **Given** a change that breaks one of those checks, **When** the Turborepo
   check runs again, **Then** it fails and names the failing check.
3. **Given** a second run with no change, **When** the Turborepo check runs,
   **Then** it gives the same result, and no cached result hides a change to
   a file that a check reads.

---

### User Story 2 - TypeScript tooling runs on Node.js (Priority: P1)

The repository's TypeScript scripts, tests, hooks and entry points run on
Node.js instead of Deno.

**Why this priority**: The user chose Node.js for the TypeScript side.

**Independent Test**: Run the TypeScript test suites and the workflow entry
point with Node.js on a machine path where the `deno` executable is hidden.

**Acceptance Scenarios**:

1. **Given** the trial branch, **When** the TypeScript test suites run,
   **Then** they run on Node.js and pass.
2. **Given** the commit-msg and git flow finish hooks, **When** they run,
   **Then** they use Node.js and the Turborepo check, not Deno.
3. **Given** the parts that still need Deno after the trial, **When** the
   report is read, **Then** it lists each of them with its reason.

---

### User Story 3 - Python packages form one uv workspace (Priority: P1)

The three Python packages share one root uv workspace and lock file, and
Turborepo discovers them as packages.

**Why this priority**: The user chose a native uv workspace for Python.

**Independent Test**: Sync the workspace from the root lock, list the
packages Turborepo discovers, run the three packages' tests, then build a
backfire plugin and check it.

**Acceptance Scenarios**:

1. **Given** the root lock, **When** the workspace is synced, **Then** the
   locked package versions equal today's per-package locks, unless the report
   names an intended upgrade.
2. **Given** the workspace, **When** Turborepo lists its packages, **Then**
   `backfire`, `doc-regions` and `wiki-consistency` appear, and their tests
   pass through Turborepo.
3. **Given** a built backfire plugin, **When** it is installed and checked,
   **Then** it installs offline, stays self-contained, writes nothing outside
   its own `.venv`, and its readiness check proves the server runs from that
   `.venv` (`test_load`, `test_ready` and `test_entry` pass).

---

### User Story 4 - The trial report (Priority: P2)

The develop session and the user get a report that lets them decide whether
to merge.

**Why this priority**: The report is the trial's deliverable.

**Independent Test**: Read the report in this feature's directory and check
each claim against its recorded evidence.

**Acceptance Scenarios**:

1. **Given** the report, **When** it is read, **Then** it names the changed
   files with lines added and removed, the locally owned code before and
   after, the sites backfire selected and the ones it left alone, the check
   results, check time before and after, what still depends on Deno, the
   open risks, and the governance wording the trial needs.
2. **Given** the backfire judgments, **When** the report cites them, **Then**
   each is kept as evidence in this feature's directory.

### Edge Cases

- A site that backfire marks for review, not for a change, stays unchanged
  and is listed as an open question.
- A check that cannot run on Node.js or through Turborepo is not dropped; the
  decision to drop it is the user's, and the report names it.
- Documents that name `deno task` commands, including `AGENTS.md` and the
  constitution, are governance: the trial does not edit `AGENTS.md` or the
  constitution, and sends the wording it needs to the develop session.
- Other features in flight change nearby files (Python lint settings and
  tasks in CHE-29, wiki-consistency checks in CHE-26); the report names the
  overlaps.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Candidate change sites MUST be listed with exact searches and
  with backfire's search by meaning, and classified with backfire against a
  written catalog. Only sites classified as must-change MAY change; sites
  marked for review stay unchanged and are reported as open questions.
- **FR-002**: Bounded design choices MUST be made with backfire's decision
  tool, each patch MUST get a backfire review, the final diff MUST pass
  through backfire's gate with real check output, and the report's claims
  MUST be verified with backfire. The judgments MUST be kept in this
  feature's directory, without secrets or student data.
- **FR-003**: A Turborepo task graph MUST run every check that `deno task
  check` runs at the base commit, and fail when any of them fails.
- **FR-004**: The repository's TypeScript scripts, tests and hooks MUST run
  on Node.js, reusing existing runtime and dependency functionality before
  any local code (AGENTS.md, "Reuse Before Implementing").
- **FR-005**: The three Python packages MUST be members of one root uv
  workspace with one committed lock file and a Turborepo package name, so
  that Turborepo's experimental Python support discovers them.
- **FR-006**: Built backfire plugins MUST still install offline, stay
  self-contained, write only into their own `.venv`, and pass the readiness
  check that proves the server runs from that `.venv`.
- **FR-007**: The runtime doctor MUST check the new environments (Node.js
  packages, Turborepo, the uv workspace) and name the repair command when
  one is missing or stale.
- **FR-008**: Turborepo MUST NOT reuse a cached result after a change to a
  file that the task reads.
- **FR-009**: The change MUST NOT change the user's global tools, Linear, or
  other features' worktrees. `AGENTS.md` and the constitution change only by
  the governance wording in the report, and a breaking constitution change
  needs the user's approval before its commit.
- **FR-011**: No part of the repository MAY require or invoke Deno: no
  `deno.json` or `deno.lock` files, no `@deno/shim-deno` or other Deno-API
  shim, and no Deno in the doctor, `orca.yaml` or the GitHub workflows. The
  shipped clean-code skill runs on Node.js, and its `SKILL.md` states what
  users must install.
- **FR-012**: The feature MUST include `develop`'s changes up to the merge
  base it finishes on, with the backfire selection redone on that base.
- **FR-010**: The report MUST contain the items of User Story 4 and be
  recorded in this feature's directory and sent to the develop session.

- **FR-013**: Where `develop`'s per-package locks held different versions of
  one package, the root `uv.lock` MUST use the newer one (openai 3.20.0,
  starlette 1.7.0, typesafe-sdk 0.7.2, pyjwt 2.15.1, sse-starlette 3.5.0 as
  of `develop` 8ce9b2a), so no package runs on an older version than it was
  tested with on `develop`, unless a test fails with it; any exception is
  recorded here with the failing test.
- **FR-014**: Biome stays the TypeScript linter and formatter in this
  feature; ESLint and Prettier rules for TypeScript (gts) come in CHE-36
  after this feature merges. Prettier formats YAML only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Turborepo check passes on the trial branch and runs the
  same set of checks as `deno task check` at the base commit.
- **SC-002**: `test_load`, `test_ready`, `test_entry` and the doctor tests
  pass on the trial branch.
- **SC-003**: The locked Python package versions on the trial branch equal
  those of the base commit's three per-package locks, or the report names
  each difference.
- **SC-004**: Every changed site has a must-change classification in the
  recorded backfire judgments.
- **SC-005**: The report gives the check's wall-clock time at the base
  commit and on the trial branch, measured on the same machine.

## Assumptions

- Node.js 24.19, npm 12.1 and uv 0.11.32 are the installed global tools, and
  the trial does not change them; Turborepo 2.11.5 is installed as a
  repository dependency.
- `tools/spec-kit` and `tools/shellcheck` stay separate uv projects; they are
  development tools, not packages, and are not workspace members.
- Scope, governance and check-removal questions are decided by the user
  through the develop session.
- The GitHub workflows are changed where they must be, but cannot be run
  locally; the report says so.
