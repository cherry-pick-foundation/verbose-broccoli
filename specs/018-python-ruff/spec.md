# Feature Specification: Python Ruff Check

**Feature Branch**: `feature/python-ruff`

**Created**: 2026-09-29

**Status**: Draft

**Linear issue**: CHE-29

**Input**: Linear issue CHE-29, "Check Python code with Ruff configured from
the Google Python style guide", and the develop session's task brief of
2026-09-29. The user decided on 2026-09-29 that the repository checks its
Python code against the
[Google Python style guide](https://google.github.io/styleguide/pyguide.html)
with Ruff. Ruff is pinned like the other tools, configured from the guide
(including its docstring convention), and run by `deno task check` and
`deno task verify`; what it reports in repository-owned code is fixed.
Vendored upstream code keeps its upstream form. A rule the codebase cannot
meet without a large rewrite is left out and recorded with its reason.

## Clarifications

### Session 2026-09-29

The develop session relayed this answer from the user.

- Q: Does the check also run Ruff's formatter in check mode, or only the
  linter? → A: Both. The checks run the linter and the formatter's check
  mode at 80 columns. The one mechanical reformat is its own commit,
  separate from the hand fixes, so reviewers can read them apart.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The checks catch Python style problems (Priority: P1)

An agent changes Python code in the repository and runs the repository
checks before it finishes. The checks fail when the change breaks a rule of
the Google guide that the configuration enforces, and they pass on the
current code.

**Why this priority**: It is the user's decision and the purpose of the
feature.

**Independent Test**: Run `deno task check` on the feature branch; it
passes. Then check a synthetic Python file that breaks a selected rule; the
Ruff step fails and names the rule.

**Acceptance Scenarios**:

1. **Given** the feature branch, **When** `deno task verify` runs, **Then**
   the Ruff step runs over every repository-owned Python file and reports
   nothing.
2. **Given** a public function without a docstring, a line one column over
   the limit, imports out of the guide's order, or code the formatter would
   change in repository-owned code,
   **When** the checks run, **Then** they fail and name the rule and the
   file.
3. **Given** a line exactly at the limit, or a test function without a
   docstring, **When** the checks run, **Then** they pass.
4. **Given** a Python file in vendored upstream code, **When** the checks
   run, **Then** Ruff does not check it.

---

### User Story 2 - The rule set is traceable (Priority: P2)

A reader who wonders why a rule is on or off finds the reason next to the
configuration: the guide section or the guide's linter configuration that
selects it, or the reason it is left out.

**Why this priority**: The user asked that left-out rules be recorded with
their reason, and later changes to the rule set need that record.

**Independent Test**: Read the configuration; every selected rule group and
every left-out or exempted rule has a one-line reason naming its source.

**Acceptance Scenarios**:

1. **Given** the configuration, **When** a reader looks up a selected rule
   group, **Then** a comment names the guide section or linter setting it
   comes from.
2. **Given** a rule the guide implies but the codebase does not meet,
   **When** a reader looks it up, **Then** the configuration says it is left
   out and why.

### Edge Cases

- A new Python file anywhere outside the excluded vendored paths is checked
  without further setup.
- Packages require different Python versions (3.11, 3.13 and 3.14); each
  file is checked against the version its own package or script header
  declares, so version-dependent rules do not misfire.
- Python files in ignored folders, such as `.venv/`, are not checked.
- Features finished into `develop` while this one is open may add Python
  code; the final merge of `develop` into this branch brings that code under
  the check, and its findings are fixed before the finish.
- The check runs offline from the locked install, like the other checks.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Ruff MUST be pinned to one exact version with a lock file and
  installed and checked for drift the same way the repository pins its other
  Python tools; `deno task doctor` MUST fail when the install is missing or
  out of sync.
- **FR-002**: The configuration MUST derive from the Google Python style
  guide: its 80-column line limit, 4-space indentation, Google docstring
  convention, import formatting and naming rules, and the lint rules of the
  `pylintrc` that the guide's section 2.1 tells readers to run, as far as
  Ruff implements them as stable rules. Where the guide's text requires
  something, it decides over the `pylintrc`; where the text leaves a choice
  to the author, the `pylintrc`'s setting applies. Rules that neither source
  asks for are not selected.
- **FR-003**: The checks MUST also run Ruff's formatter in check mode with
  the same 80-column limit. The one mechanical reformat of existing code
  MUST be its own commit, holding no hand fixes.
- **FR-004**: `deno task check`, and so `deno task verify`, MUST run the
  Ruff check over every repository-owned Python file, fail on any finding,
  write no files, and need no network.
- **FR-005**: Vendored upstream code MUST be excluded by path and keep its
  upstream form. Today that is Spec Kit's bundled extensions under
  `.specify/`.
- **FR-006**: Every finding in repository-owned code MUST be fixed without
  changing behavior; the existing test suites MUST still pass.
- **FR-007**: A rule that the codebase cannot meet without a large rewrite
  MUST be left out, and every left-out rule and every per-file or per-line
  exemption MUST carry its reason in the configuration. A large rewrite is a
  fix that changes behavior or a public name, or restructures a function,
  such as splitting it; adding docstrings, wrapping lines, reordering
  imports, renaming local names and similar local edits are not.
- **FR-008**: Acceptance MUST show a positive, a negative and a boundary case
  for the configuration and the exclusion of vendored code, with synthetic
  input, and the repository's test task MUST run it.
- **FR-009**: The documents that list the repository's tools and checks MUST
  name the Ruff check and its pinned version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `deno task verify` passes on the feature branch after the final
  merge of `develop`, with the Ruff step among the checks it ran.
- **SC-002**: The acceptance cases of FR-008 fail when the configuration is
  broken, for example when an exclusion covers all files, and pass on the
  committed configuration.
- **SC-003**: The Python test suites pass with the same test counts as
  before the fixes.
- **SC-004**: Every rule group, left-out rule and exemption in the
  configuration has a stated reason.

## Assumptions

- "Pinned like the other tools" follows Spec Kit's pattern: a uv project
  under `tools/` whose `uv.lock` pins the tool, checked by `deno task
  doctor`.
- Test functions and special methods need no docstrings, as the guide's
  `pylintrc` exempts names such as `test.*` and `__.*__` from its docstring
  check.
- Ruff's preview rules are not used; they are unstable and would make each
  update of the pinned version harder to review.
- The constitution and `AGENTS.md` do not change; the rule set lives in the
  Ruff configuration.
