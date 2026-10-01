# Feature Specification: CPU Load Relief

**Feature Branch**: `feature/cpu-load-relief`

**Created**: 2026-10-01

**Status**: In progress

**Linear issue**: CHE-73

**Input**: Linear issue CHE-73, "Cut local CPU load: Turborepo caching with
declared inputs and a foreground scheduler", and the develop session's brief
of 2026-10-01. On 2026-10-01 the laptop (Intel Core Ultra 7 258V:
performance cores 0-3, efficiency cores 4-7) passed a load average of 9 while
several worktrees ran `npm run verify`, and typing in Orca stuttered. Every
task in `turbo.json` had `cache: false`, so every verify reran every check.
The user decided the same day:

1. Turn on Turborepo caching where each task's inputs can be declared
   exactly, including files outside its package, generated files and
   external programs or their versions, with tests that prove a change to
   each kind of input reruns the task. Keep `cache: false`, with the reason,
   where they cannot. Feature 019's requirement holds: a cached result never
   hides a change to a file the task reads
   ([019 FR-008](../019-turborepo/spec.md); its decision D8 chose no caching
   with confidence 0.40).
2. Batch work runs in a low-weight systemd scope on the efficiency cores.
   The develop session already wrote this rule in
   `~/.claude/rules/worker-dispatch.md`, "CPU on this laptop"; this feature
   only follows it.
3. Review System76's scheduler (pop-os/system76-scheduler), which raises the
   focused window's priority, with its GNOME Shell extension, before the
   user decides whether to install it. It runs as a root service built from
   source; the user runs any sudo command.

After the review, the user decided the same day not to install the
scheduler and dropped it from scope; the CPU rule in decision 2 stays the fix
for load spikes. The review and the decision stay recorded here (User Story
3). The user will decide in CHE-74 whether Turborepo stays, from this
feature's count of cacheable tasks and its warm-cache measurements
([research.md](research.md), D5 and D9).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A repeat verify reuses unchanged results (Priority: P1)

An agent runs `npm run verify` a second time on an unchanged tree, or in
another worktree whose inputs for a task are the same, and Turborepo replays
that task's result instead of running it again.

**Why this priority**: It is the CPU saving the user asked for.

**Independent Test**: Run `npm run verify` twice on an unchanged tree and
compare the second run's CPU time before and after the change.

**Acceptance Scenarios**:

1. **Given** a verify that passed, **When** it runs again on the same tree,
   **Then** every cached task is replayed and the run prints VERIFIED.
2. **Given** another worktree on this machine with the same inputs for a
   task, **When** it verifies, **Then** it replays that task from the shared
   cache.

---

### User Story 2 - No cached result hides a change (Priority: P1)

A change to anything a cached task reads makes Turborepo run that task
again.

**Why this priority**: The user made it the condition for caching.

**Independent Test**: In a copy of the repository, change one input of each
kind and check that the hashes of the tasks that read it change.

**Acceptance Scenarios**:

1. **Given** a cached task, **When** a repository file it reads changes,
   including one outside its package or not yet tracked by Git, **Then** its
   hash changes.
2. **Given** a cached task, **When** an installed dependency environment
   changes, **Then** its hash changes.
3. **Given** a cached task, **When** the version of a program it runs, the
   Git configuration outside the repository, or a hashed environment
   variable changes, **Then** its hash changes.
4. **Given** a task whose inputs cannot be declared, **When** the
   configuration is read, **Then** it has `cache: false` and its description
   says why.

---

### User Story 3 - The scheduler decision (Priority: P2)

The user reads a security review of System76's scheduler and its GNOME
Shell extension and decides whether to install it.

**Why this priority**: It is a separate, optional relief that needs the
user's sudo password.

**Independent Test**: Read the review record and the user's recorded
decision.

**Acceptance Scenarios**:

1. **Given** the review, **When** it is read, **Then** it says what runs as
   root, what network access exists, what it changes, how to uninstall, and
   whether the extension supports GNOME Shell 50.
2. **Given** the review's findings, **When** they are put to the user,
   **Then** the user's decision is recorded in `tasks.md`.

**Outcome**: the review
([security/system76-scheduler-8651bbf.md](security/system76-scheduler-8651bbf.md))
found the scheduler not acceptable as shipped (6 medium, 1 low findings), and
its small GNOME extension supports GNOME 40 to 44 only. The user decided not
to install it.

### Edge Cases

- A task fails: Turborepo caches only successful tasks, so a failure is
  never replayed as a pass.
- An empty, misnamed folder: Turborepo does not hash folders, so the name
  check stays uncached.
- A worktree that has not installed its environments: its installed records
  differ or are missing, so its hashes differ.
- Before this feature merges, `develop` does not ignore `.turbo/cache/`; runs
  during development use a worktree-local cache folder so `develop` gains no
  untracked files.
- Turborepo writes task logs into each package's `.turbo/` folder; they must
  be ignored, or they become inputs of every root task.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every task that `npm run verify` runs MUST either be cached
  with all its inputs declared, or have `cache: false` with the reason in its
  description.
- **FR-002**: A cached task's hash MUST change when a repository file it
  reads changes, tracked or not, inside or outside its package.
- **FR-003**: A cached task's hash MUST change when an installed dependency
  environment it uses changes (the root and wiki-consistency npm trees, the
  root uv environment and the tool environments under `tools/`).
- **FR-004**: A cached task's hash MUST change when the version of a program
  outside the repository that it runs changes, when the Git configuration
  outside the repository changes, or when an environment variable that can
  change a tool's behavior changes.
- **FR-005**: `npm run verify` MUST still pass only on the exit status and
  the same run's Turborepo summary.
- **FR-006**: Tests MUST show, for each kind of input in FR-002 to FR-004,
  that a change changes the hash of the tasks that read it.
- **FR-007**: The cache MUST stay local: no remote cache, and its folder
  ignored by Git.
- **FR-008**: The scheduler review MUST be recorded the way
  `specs/034-kebab-file-names/security/ls-lint-2.3.1.md` is, and the user's
  install decision recorded; no agent runs sudo.

## Success Criteria *(mandatory)*

- **SC-001**: The CPU time (user plus system) of a second `npm run verify` on
  an unchanged tree, measured before and after on the same machine, drops.
- **SC-002**: The new tests pass, and each fails when its declaration is
  removed.
- **SC-003**: `npm run verify` prints VERIFIED.
- **SC-004**: The scheduler review exists and the user's decision is
  recorded.

## Assumptions

- The operating system's base programs (`sh`, coreutils, findutils, `sed`,
  `timeout`, `xargs`) come with Ubuntu 26.04 and do not change task results;
  they are not hashed.
- Per-user npm and uv configuration does not change results: the tasks run uv
  offline from installed environments (`--frozen --offline --no-sync`) and
  install npm and uv script dependencies only from lock files with integrity
  hashes.
- Every worktree on this machine is the user's own; any of their agents can
  already edit any worktree, so a shared local cache adds no new writer.
