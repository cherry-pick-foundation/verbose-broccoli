# Feature Specification: ShellCheck

**Feature Branch**: `feature/shellcheck`

**Created**: 2026-09-29

**Status**: Draft

**Linear issue**: CHE-30

**Input**: Linear issue CHE-30, "Check shell scripts with ShellCheck (Google
shell style guide)", and the brief with which the orchestrator of the
`develop` worktree started this feature on 2026-09-29. The user decided on 2026-09-29 that the repository checks run ShellCheck, which
the Google shell style guide
(<https://google.github.io/styleguide/shellguide.html>) recommends "for all
scripts, large or small". The git flow finish hook, the commit-msg hook and
`scripts/worktree-branch.sh` guard every feature finish, commit and new
worktree, and before this feature nothing linted them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Shell scripts are checked with every run of the checks (Priority: P1)

An agent that changes a repository-owned shell script runs `deno task check`
or `deno task verify`. ShellCheck reports any problem in the script, and the
check fails until it is fixed.

**Why this priority**: It is the user's decision and the purpose of the
feature.

**Independent Test**: Run `deno task check` on a clean tree, then again with
a script that ShellCheck rejects.

**Acceptance Scenarios**:

1. **Given** the repository's own shell scripts, **When** `deno task check`
   runs, **Then** ShellCheck checks each of them and passes.
2. **Given** a new, not yet committed `.sh` file with an unquoted variable,
   **When** the shell check runs, **Then** it fails and names the file and
   line.
3. **Given** Spec Kit's vendored scripts under `.specify/`, **When** the
   shell check runs, **Then** it does not check them, so their upstream form
   stays unchanged.

---

### User Story 2 - ShellCheck is pinned like the other tools (Priority: P2)

A new worktree gets the same ShellCheck version from a locked package, and
the runtime doctor reports a missing or stale environment with the command
that repairs it.

**Why this priority**: The check must give the same result in every
worktree.

**Independent Test**: Run `deno task doctor` with and without the synced
environment.

**Acceptance Scenarios**:

1. **Given** a worktree after Orca's setup script, **When** `deno task
   doctor` runs, **Then** it reports the ShellCheck environment as in sync.
2. **Given** a worktree without that environment, **When** `deno task
   doctor` runs, **Then** it fails and names `uv sync --locked --project
   tools/shellcheck`.

### Edge Cases

- A finding that flags intended behavior, such as the word splitting of a
  parent list in the finish hook, keeps the behavior; the fix avoids the
  construct or suppresses that one finding with its reason.
- Shell snippets inside `deno.json` tasks, `orca.yaml` and the GitHub
  workflows are not script files, and are not checked (Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: ShellCheck MUST be pinned to one exact version through a locked
  package, not a system install, and `deno task doctor` MUST fail with the
  repair command when its environment is missing or differs from the lock.
  Orca's setup script MUST create that environment in each worktree.
- **FR-002**: A Deno task MUST run ShellCheck on every repository-owned shell
  script: each `*.sh` file and each file in `scripts/git-hooks/` and
  `scripts/git-flow-hooks/`, tracked or untracked but not ignored. It MUST
  fail on any finding.
- **FR-003**: `deno task check`, and so `deno task verify`, MUST run that
  task.
- **FR-004**: The vendored scripts under `.specify/` MUST NOT be checked or
  changed.
- **FR-005**: A root ShellCheck configuration MUST turn on the optional checks
  that enforce Google guide rules: `require-variable-braces` ("prefer
  `"${var}"` over `"$var"`"), `quote-safe-variables` ("Always quote strings
  containing variables"), `avoid-nullary-conditions` ("explicitly use `-z` or
  `-n`") and `require-double-brackets` ("`[[ … ]]` is preferred over
  `[ … ]`", which ShellCheck applies to Bash and Ksh scripts only).
- **FR-006**: Every finding in the repository-owned scripts MUST be fixed
  without changing their behavior, and the existing tests of those scripts
  MUST pass.
- **FR-007**: Google guide rules that ShellCheck cannot enforce MUST be left
  out and recorded with their reason (Assumptions).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `deno task verify` passes on the feature branch, and its check
  run includes the shell check.
- **SC-002**: The shell check fails on a synthetic untracked script with a
  finding and passes again once the script is removed.
- **SC-003**: `deno task doctor` passes with the synced environment and fails
  with the repair command without it.
- **SC-004**: No file under `.specify/` changes.

## Assumptions

- The pinned package is `shellcheck-py`, whose wheels carry the official
  ShellCheck binary, in a uv project under `tools/shellcheck/`, the way
  `tools/spec-kit/` pins the Spec Kit CLI.
- These Google guide rules are left out, because ShellCheck or a small
  configuration cannot enforce them: Bash as the only language for
  executables and `#!/bin/bash` (the scripts are POSIX `sh`, and Git, git-flow
  and Orca's setup run them as such), two-space indentation, the 80-character
  line limit, file naming, function comments and `main`. The indentation rule
  needs a formatter such as shfmt, which the issue does not ask for.
- The guide's "When to use Shell" advice, to rewrite a script of more than
  100 lines or with non-straightforward control flow in a more structured
  language, is also left out. ShellCheck cannot check it, and moving the Git
  and git-flow hooks out of shell would rewrite them, which is outside this
  feature.
- Shell snippets inside `deno.json`, `orca.yaml` and `.github/workflows/` stay
  unchecked: ShellCheck reads script files, and extracting the snippets would
  need new glue code.
- The GitHub check workflow does not prepare the repository's other uv
  environments either (`tools/spec-kit`, `packages/doc-regions`,
  `packages/wiki-consistency`), so this feature leaves it as it is.
