# Feature Specification: Root Configuration Boundaries

**Feature Branch**: `feature/root-config`

**Created**: 2026-10-01

**Status**: In progress

**Linear issue**: CHE-74

**Input**: Linear issue CHE-74, "Root configuration: one owner per concern,
setup in one place, and fewer root files", its 2026-10-01 comment (Turborepo
stays), the first point of CHE-50 (one source for tool versions), and the
develop session's brief of 2026-10-01. The repository root held 26 tracked
files, and several facts were written in more than one of them: worktree setup
three times (`orca.yaml`, `.github/workflows/check.yml`, and the
`backfire:install` and `wiki-consistency:install` scripts), tool versions from
`mise.toml` copied into `orca.yaml` and `check.yml`, one check declared in up
to four places, and the commit-message convention held by commitlint,
commitizen and a hand-written pattern in `.github/workflows/pr-title.yml`.

The user decided on 2026-10-01:

1. One owner per concern. The mise file owns the environment: tool versions,
   one `setup` task and the doctor checks. `orca.yaml` keeps only Orca's own
   steps and calls the setup task; GitHub's check workflow calls it too;
   doctor hints point to it. Tool configs own code rules. `package.json` owns
   each command once. `turbo.json` owns only the check graph.
2. Turborepo stays (CHE-73: 31 of 46 tasks cached; a repeat full check took
   5.0 s and 9.9 s of CPU against 228.7 s and 545.1 s). Each Python package
   gets its own `test` and `check` tasks; the umbrella tasks on the root
   Python project and the `tools/none` workspace placeholder go. The five
   Python test commands are removed from `turbo.json`; those tasks run the
   `package.json` scripts like the other root tasks.
3. Fold `.cz.toml` and `ruff.toml` into `pyproject.toml`, `.prettierrc.js`
   into `package.json`, and move `mise.toml`, `mise.lock`, `lefthook.yml`,
   `.ls-lint.yml` and `.dependency-cruiser.json` into `.config/`. Ruff's
   `src` becomes `["packages/*/src"]`. No compatibility copy stays.
4. The files that their tools or editors read only at the root stay there.
5. This feature takes CHE-50's first point; CHE-50 keeps the weekly update
   and its security question.
6. Before proposing one owner for commit-message rules, compare commitizen's
   `cz check`, commitlint and the pull-request title pattern.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One place for the environment (Priority: P1)

A person or agent prepares a worktree, or GitHub prepares a runner, by running
one mise task. Every tool version is written once, in the mise file and its
lock.

**Why this priority**: Updating a tool used to mean editing a dozen files, and
the copies already differed.

**Independent Test**: Search the repository for each pinned version; run
`mise run setup` and `npm run doctor`.

**Acceptance Scenarios**:

1. **Given** `.config/mise.toml`, **When** every tool's pinned version is
   searched for in `orca.yaml`, the workflows, the Python projects and the
   scripts, **Then** none repeats it.
2. **Given** `orca.yaml` and `check.yml`, **When** they are read, **Then**
   each calls `mise run setup` and neither lists tools, installs or syncs.
3. **Given** a failing doctor check about an environment, **When** its hint is
   read, **Then** it names `mise run setup`.

---

### User Story 2 - Fewer root files, every tool still finds its config (Priority: P1)

The root holds only files that a tool or editor reads there. Each moved config
is found by its tool, and the rules the tools enforce are unchanged.

**Why this priority**: It is the point of the move; a config a tool no longer
finds silently turns its rules off.

**Independent Test**: Compare each tool's effective settings before and after;
run each tool's own synthetic test.

**Acceptance Scenarios**:

1. **Given** the moves, **When** the tracked root files are listed, **Then**
   they are exactly the files in FR-005.
2. **Given** `[tool.ruff]` in `pyproject.toml`, **When** Ruff's effective
   settings for sample files in every package, the scripts and the plugins are
   compared with the `ruff.toml` they came from, **Then** they are equal except
   for the intended `src`.
3. **Given** the key in `package.json`, **When** Prettier resolves its
   configuration for sample files, **Then** the options equal the old file's.
4. **Given** each moved config, **When** its tool's test and its check run,
   **Then** they pass, and a rule violation is still reported.

---

### User Story 3 - Per-package Turborepo tasks (Priority: P1)

Each Python package has its own `test` and `check` tasks. `turbo.json` holds
the check graph and no command that `package.json` already holds.

**Why this priority**: Per-package tasks hash only the package's own files,
and the graph shows the package boundaries.

**Independent Test**: `turbo run check --dry=json` lists each package's `test`
and `check` with the dependency between them; a synthetic change to one
package reruns only that package's tasks.

**Acceptance Scenarios**:

1. **Given** the graph, **When** it is listed, **Then** every Python package
   has `<package>#test` and `<package>#check`, `<package>#check` depends on
   `<package>#test`, and no `verbose-broccoli-python#test` exists.
2. **Given** `turbo.json`, **When** it is read, **Then** no `command` repeats a
   test command of `package.json`.
3. **Given** a change to one package's source, **When** the hashes are
   compared, **Then** only that package's tasks and the tasks that read it
   change.

---

### User Story 4 - One owner for commit-message rules (Priority: P2)

The user reads a comparison of the three rule sets and decides which tool owns
the commit-message rules.

**Why this priority**: Replacing a tool can weaken a rule; the user decides.

**Independent Test**: Read [research.md](research.md), D9.

**Acceptance Scenarios**:

1. **Given** the comparison, **When** it is read, **Then** each rule of
   commitlint, `cz check` and the pull-request pattern is listed with a
   measured accept or reject for the same messages.
2. **Given** the user's decision, **When** it arrives, **Then** it is recorded
   in `tasks.md`; until then no commit-message tool changes.

**Outcome**: on 2026-10-02 the user chose to keep commitlint for commit
messages, commitizen only for the constitution version bump and the current
pull-request title pattern; no tool changed (research.md, D9).

### Edge Cases

- A tool finds a stale config at its old place: no old file stays.
- `uv sync` run from `.config/`: tasks run from the repository root.
- A worktree whose mise config is untrusted: `mise doctor project` refuses to
  run, which is the visible failure.
- A changed root `package.json` script: it is an input of every Python test
  task, so the task reruns.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each tool version appears once, in `.config/mise.toml` and
  `.config/mise.lock`. `required-version` copies of the uv version, and the
  copies in `orca.yaml`, the workflows and prose, are removed.
- **FR-002**: `.config/mise.toml` has one `setup` task that installs the
  locked tools and every dependency tree; `orca.yaml` and `check.yml` call
  it; doctor hints for environments point to it.
- **FR-003**: `[tool.commitizen]` and `[tool.ruff]` live in `pyproject.toml`
  and `prettier` in `package.json`; Ruff's `src` is `["packages/*/src"]`.
- **FR-004**: `mise.toml`, `mise.lock`, `lefthook.yml`, `ls-lint.yml` and
  `dependency-cruiser.json` live in `.config/`; each is found by its tool
  natively or through a path the tool already accepts.
- **FR-005**: The tracked root files are `package.json`, `package-lock.json`,
  `pyproject.toml`, `uv.lock`, `.python-version`, `.npmrc`, `turbo.json`,
  `orca.yaml`, `tsconfig.json`, `eslint.config.js`, `eslint.ignores.js`,
  `.editorconfig`, `.gitignore`, `.shellcheckrc`, `.gitflow`, `LICENSE`,
  `README.md` and `AGENTS.md`.
- **FR-006**: Every consumer of a moved file reads the new place; no
  compatibility copy stays.
- **FR-007**: Each Python package has `test` and `check` tasks; the root
  Python umbrella tasks, the `tools/none` placeholder and the Python test
  commands in `turbo.json` are gone, and the member tests run the
  `package.json` scripts.
- **FR-008**: The effective rules of Ruff, Prettier, ls-lint, dependency-cruiser,
  commitizen, commitlint and the doctor checks are unchanged.
- **FR-009**: A cached task still never hides a change to a file it reads
  (feature 039); moving a command into `package.json` adds that file to the
  task's inputs.
- **FR-010**: The commit-message rule sets are compared with measured results;
  no existing requirement is weakened without the user's decision.
- **FR-011**: `npm run verify` passes only on the exit status and the same
  run's Turborepo summary.

## Success Criteria *(mandatory)*

- **SC-001**: No pinned tool version is found outside the mise file and lock,
  except the `uv_build` backend range (research.md, D6).
- **SC-002**: The root tracked files equal FR-005's list.
- **SC-003**: Every tool's effective settings match before and after, and each
  tool's own test passes.
- **SC-004**: The check graph matches User Story 3 and the new tests fail with
  the old arrangement.
- **SC-005**: `npm run verify` prints VERIFIED.
- **SC-006**: The rule-set comparison exists and the user's decision is
  recorded.

## Assumptions

- The hosted GitHub workflows cannot be run here; they are checked by reading
  and by the same commands run locally. That acceptance stays open.
- The develop session writes to Linear; this feature only reports.
