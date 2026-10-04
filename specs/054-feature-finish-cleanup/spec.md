# Feature Specification: Post-merge Feature Cleanup

**Feature Branch**: `feature/finish-cleanup`

**Created**: 2026-10-05

**Status**: In review

**Linear issue**: CHE-87

**Input**: Prompt safe cleanup after a successful feature finish.

## User Scenarios & Testing

### User Story 1 - Clean up a finished feature safely (Priority: P1)

After a successful feature merge, the operator gets the source branch tip and
worktree path with instructions to settle and close idle feature sessions,
remove only the completed clean worktree through Orca, and restore the branch
at its recorded tip if Orca deleted it.

**Why this priority**: The current finish leaves cleanup to notes outside the
repository, so that procedure can disappear with those notes.

**Independent Test**: Finish two synthetic features with git-flow-next and
check each hook output against its branch tip and worktree; force a merge-commit
failure and verify cleanup instructions do not appear or remove the source.

**Acceptance Scenarios**:

1. **Given** a successful finish that retains the source branch and worktree,
   **When** git-flow runs its post-finish hook, **Then** output names the exact
   source branch tip and worktree and gives the safe Orca cleanup steps.
2. **Given** a failed finish, **When** git-flow runs the post-finish hook,
   **Then** it emits no cleanup prompt and leaves the source branch and worktree
   for inspection.
3. **Given** a missing branch tip or source worktree, **When** the hook runs,
   **Then** it warns and asks for inspection without removing anything.

## Requirements

### Functional Requirements

- **FR-001**: Every successful feature finish MUST print the exact retained
  source branch tip and its worktree path.
- **FR-002**: The prompt MUST direct the operator to settle workers first, close
  only idle feature sessions and terminals, and preserve active or unsettled
  workers, unrelated tabs, dirty or unmerged worktrees, and source evidence.
- **FR-003**: The prompt MUST require recording the source tip before removal,
  using Orca to remove only the completed clean worktree, and recreating the
  source branch at that tip if Orca deleted it.
- **FR-004**: The hook MUST not run cleanup instructions after an unsuccessful
  feature finish and MUST never remove sessions, terminals, branches, or
  worktrees itself.
- **FR-005**: If it cannot resolve the source tip or worktree state, the hook
  MUST tell the operator to inspect and preserve it, and MUST NOT print a
  worktree removal command unless the source worktree exists and is clean.
- **FR-006**: The existing git-flow-next shared hook path and test harness MUST
  be used without changing upstream code or adding dependencies.

## Success Criteria

- **SC-001**: A real git-flow feature finish prints each successful source
  branch's exact retained tip and worktree instructions.
- **SC-002**: A failed finish prints no cleanup prompt and retains its source
  branch and worktree.
- **SC-003**: Existing git-flow regression checks and the focused new cases pass.

## Assumptions

- git-flow-next 2.1.0 invokes the configured `post-flow-feature-finish` hook
  after finish, exposes `EXIT_CODE`, and prints hook output.
- The hook cannot prove live Orca worker settlement, so cleanup remains a
  deliberate operator action.
- `.gitflow` continues retaining the local feature branch by default; if a
  finish configuration removes it, the hook must fail safe and request manual
  inspection.
