# Feature Specification: Kebab-case file names

**Feature Branch**: `feature/kebab-file-names`

**Created**: 2026-09-30

**Status**: Draft

**Linear issue**: CHE-63

**Input**: Linear issue CHE-63, "Name every file and folder in kebab-case and
check it", and the brief with which the `develop` session started this
feature on 2026-09-30.

The user decided on 2026-09-30 that file and folder names are kebab-case
only: lowercase letters, digits and hyphens, such as `workflow-plan.ts`. They
chose "new files and rename old": every new name is kebab-case, existing
repository names are renamed where the language or format allows it, and an
upstream naming check makes the rule hold without an agent's judgment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A non-kebab name fails the check (Priority: P1)

A contributor who adds `scripts/new_tool.ts` or `docs/NewPage.md` sees
`npm run verify` fail and name the file, so the rule holds without anyone
reading the diff for it.

**Why this priority**: It is what makes the rule hold.

**Independent Test**: Add a file named `Bad_Name.md` in a scratch copy of the
worktree and run the naming check.

**Acceptance Scenarios**:

1. **Given** a tracked or new file or folder whose name is not kebab-case and
   not on the exception list, **When** `npm run verify` runs, **Then** it
   fails and names the path.
2. **Given** the repository after the renames, **When** `npm run verify`
   runs, **Then** the naming check passes.

---

### User Story 2 - Existing names follow the rule (Priority: P1)

A reader of the repository finds every file and folder in kebab-case, except
the short list of names a language, tool or standard fixes, and every
reference to a renamed file still works.

**Why this priority**: It is the user's decision for existing names.

**Independent Test**: List every tracked path with `git ls-files` and compare
each name with the check's rules; run `npm run verify`.

**Acceptance Scenarios**:

1. **Given** the renamed tree, **When** the naming check runs, **Then** it
   reports no path.
2. **Given** the renamed tree, **When** `npm run verify` runs, **Then** every
   import, script, configuration entry, generated document and live link
   still resolves.

---

### User Story 3 - Vault pages follow the rule (Priority: P2)

An agent that writes a Wiki page in any of the four vaults reads in the
vault's schema that page and folder names are kebab-case.

**Why this priority**: The rule covers the vaults, but only the schemas
change here; raw sources keep their original names.

**Independent Test**: Read the naming line in the schema template and in the
`AGENTS.md` of the `default`, `chat`, `code` and `work` vaults.

**Acceptance Scenarios**:

1. **Given** a vault schema, **When** an agent reads its Wiki rules, **Then**
   it states that files and folders under `wiki/` are named in kebab-case,
   and that raw sources keep their original names.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The naming check MUST be ls-lint, used unchanged and pinned
  once in the repository's mise configuration and its lock, after a
  read-only security review by a reviewer from a provider other than the
  implementer's finds no standing high-severity problem for the planned use.
- **FR-002**: `npm run verify` MUST run the naming check over the repository
  tree and fail on any file or folder name that is not kebab-case and not an
  exception.
- **FR-003**: Exceptions MUST be only names that a language, tool or
  standard fixes, each listed with its reason in the check's configuration:
  Python modules and packages, `AGENTS.md`, `SKILL.md`, `README.md`,
  `LICENSE`, and any name an external tool looks up by exact spelling,
  proved by a file and line or a command.
- **FR-004**: Every other non-kebab name tracked in the repository MUST be
  renamed with `git mv`, and every reference updated: imports, scripts,
  configuration, documents, skills, links in records where they point at a
  current path, and generated files through their generators.
- **FR-005**: The renames MUST land in one commit, right after the newest
  `develop` is merged, in a finish slot the `develop` session grants.
- **FR-006**: The Wiki schema template and the four vault schemas MUST state
  that files and folders under `wiki/` are named in kebab-case; raw sources
  keep their original names. The `work` vault's schema changes only after
  CHE-61 (student pages renamed to `s-<number>.md`) has finished.

### Key Entities

- **Exception**: a name the check allows although it is not kebab-case,
  with the language, tool or standard that fixes it.
- **Rename**: one path moved with `git mv`, with every reference to it
  updated.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The naming check reports 0 paths on the merged result, inside
  `npm run verify`, which passes.
- **SC-002**: A scratch file named `Bad_Name.md` makes the check fail.
- **SC-003**: Every exception in the configuration has a reason.
- **SC-004**: The template and all four vault schemas carry the naming rule.

## Assumptions

- Records in `specs/` and `.specify/` are repository files, so their names
  follow the rule; their prose keeps the paths it mentioned at the time, and
  only links that point at a renamed current file are updated.
- Spec Kit's and vendored upstream files need no separate exception: their
  non-kebab names are all Python modules, `README.md`, `SKILL.md` or
  `LICENSE`.
- The five other running features (CHE-47, CHE-51, CHE-57, CHE-60, CHE-61)
  already name new files in kebab-case; the renames wait for a finish slot so
  that `develop` does not move under them.
