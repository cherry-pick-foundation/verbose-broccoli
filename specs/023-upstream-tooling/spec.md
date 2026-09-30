# Feature Specification: Upstream Tools in Place of Own Tooling Code

**Feature Branch**: `feature/upstream-tooling`

**Created**: 2026-09-30

**Status**: Draft

**Linear issue**: CHE-44

**Input**: Linear issue CHE-44, "Replace own tooling code with upstream tools
used unchanged", and the develop session's task brief of 2026-09-30. On
2026-09-30 the user decided to replace pieces of the repository's own code
with existing upstream tools used unchanged, listed in the issue's table:
mise for the environment check, check-jsonschema or Ajv for the plugin
manifest check, commitizen for the constitution version, cog for the
reference documents, lefthook for the Git hooks, Vale for the Wiki page
rules, qmd's own command or MCP server for Wiki search, bagit-python's own
bag commands for the raw import, and, in part, Turborepo run summaries,
dependency-cruiser and import-linter for the workflow and verify tools and
the import-boundary check. Each tool is a pinned dependency (npm, PyPI, or a
version pinned through mise); a tool that cannot be one is an unmodified
local copy with its license notice and upstream record. The replaced code and
its unused tests go. Behaviour that only the old code had is listed for the
user instead of rebuilt. The develop session added on 2026-09-30, for the
user, that a security review of each candidate tool's source at the version
to be pinned gates its addition.

## Clarifications

### Session 2026-09-30

- Pending: the user's answers on mise installs, the constitution version
  check, Vale and the roster, the raw import record, the behaviours the
  swaps drop, and the security findings (asked through the develop session).
- Q: For the workflow and verify swaps, keep verify's own run record (task,
  base and plan, before/after snapshots, log hash, interrupted-run
  detection, the two-failure REVIEW threshold, the lock and the graph
  labels; about -208 own-code lines), or replace it (about -668)? → A:
  Replace it. `npm run verify` runs Turborepo with a run summary and passes
  on its exit status, which still gates the feature finish; the local run
  record, snapshots, log hashing, failure streak and lock go. `AGENTS.md`
  and the constitution change wherever they describe the verify evidence,
  and the Turborepo security controls stay (telemetry off, no update
  notifier, summaries kept out of commits). The develop session relayed the
  user's answer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repository checks run on upstream tools (Priority: P1)

An agent works on a feature and runs `npm run verify` before it finishes. The
environment check, the plugin manifest check, the reference-document drift
check, the commit-message hook and the constitution version step now run
upstream tools configured by the repository, and the repository no longer
owns the code that did this work.

**Why this priority**: These swaps are independent of other in-flight
features and remove most of the replaced code.

**Independent Test**: On the feature branch, `npm run verify` passes. For
each swap, break its input on purpose (a missing locked environment, a
manifest that violates its schema, a stale reference table, a commit message
that is not a Conventional Commit) and see the upstream tool fail and name
the problem.

**Acceptance Scenarios**:

1. **Given** a worktree whose pinned tools and locked environments match,
   **When** the environment check runs, **Then** it passes; **Given** one
   locked environment out of sync, a wrong tool version or the Git hooks not
   installed, **Then** it fails and names that item.
2. **Given** plugin manifests that match the vendored Agent Plugins schemas,
   **When** the manifest check runs, **Then** it passes; **Given** a
   manifest that violates its schema, **Then** it fails and names the file.
3. **Given** a change to a root task, a task description, a plugin manifest
   or the help text of a documented command, **When** the drift check runs
   without the refresh, **Then** it fails; after the refresh it passes, and
   the refresh changes nothing else.
4. **Given** a commit message that is not a Conventional Commit, **When** the
   commit is made, **Then** the commit-message hook refuses it.
5. **Given** a commit that changes the constitution, **When** its author
   prepares it, **Then** the constitution's version line is written by the
   upstream tool as the clarification decides.

---

### User Story 2 - Wiki tools run on upstream tools (Priority: P1)

The user's agents check Wiki pages, search the Wiki and admit raw documents.
The page rules are Vale rules, search goes through qmd's own interface, and
bags are made by bagit-python, with only glue code left in the repository.

**Why this priority**: These are the largest own-code pieces after the
workflow tools, and they are independent of CHE-42.

**Independent Test**: The Wiki consistency and raw import tests pass on
synthetic fixtures: a page with a phone number fails the page rules and the
message does not repeat the number; a search returns the expected page and
line; an admitted file becomes a valid bag with its source record, and a
rerun of an unchanged file adds no revision.

**Acceptance Scenarios**:

1. **Given** a synthetic page that breaks one page rule, **When** the Wiki
   check runs, **Then** it fails with the rule and the line, without the
   matched text; **Given** a page that follows every rule, **Then** it
   passes.
2. **Given** an index built from synthetic pages and evidence, **When** the
   request builder searches, **Then** it gets the hits it got before, with
   collection, path and line, through qmd's public interface only.
3. **Given** a selected synthetic original, **When** it is admitted, **Then**
   a read-only valid bag holds its copy and source record; **Given** the same
   unchanged original again, **Then** no revision is added; **Given** a
   changed original, **Then** a new revision of the same source is added.

---

### User Story 3 - Workflow and verify evidence on upstream tools (Priority: P2)

After CHE-42 merges its own-code check into `npm run verify`, the workflow
and verify tools take their check evidence from Turborepo run summaries, the
affected-files graph and import rules from dependency-cruiser's own command,
and Python import boundaries from import-linter. The difficulty scoring and
the skill triggers stay.

**Why this priority**: It depends on CHE-42, which changes the same verify
path, so it comes after the independent swaps.

**Independent Test**: `npm run workflow` and `npm run verify` give the same
modes, graph answers and verification results on the existing test cases,
and an import that breaks a boundary fails the check in TypeScript and in
Python.

**Acceptance Scenarios**:

1. **Given** a passing check run, **When** verify records evidence, **Then**
   the evidence comes from Turborepo's run summary.
2. **Given** an import from an inner layer to an outer one, or from a package
   into a plugin, **When** the import check runs, **Then** it fails and names
   the rule and the files.
3. **Given** a Python module that imports across a declared boundary,
   **When** the import check runs, **Then** it fails.

---

### User Story 4 - The user sees what each swap cost and saved (Priority: P1)

The user reads, per swap, the tool, its pinned version, its license, its
security review verdict, the removed files, the own-code lines removed and
added, and the behaviours that were dropped instead of rebuilt.

**Why this priority**: The user decides whether a dropped behaviour matters
and tracks the repository's own-code size.

**Independent Test**: The feature's records list every swap with these
facts, and the counts can be reproduced with the stated counter.

**Acceptance Scenarios**:

1. **Given** the finished feature, **When** the user reads its records,
   **Then** each swap names its tool, pin, license, review verdict, removed
   files and own-code change, and the total.
2. **Given** a dropped behaviour, **When** the user reads the records,
   **Then** it is listed with the swap that dropped it.

### Edge Cases

- A candidate tool's security review finds a high-severity problem: the tool
  is not added, and the finding goes to the user through the develop session.
- A tool cannot be pinned as a dependency: it is added as an unmodified local
  copy with its license notice and upstream record, and the records say why.
- A swap would need more own glue code than it removes, or substantial new
  local code: stop and report the missing capability and the options.
- Features that finish into `develop` while this one is open may touch the
  same files (CHE-39 changes the Wiki request builders, CHE-42 adds its check
  to verify, CHE-43 changes license notices); the final merge of `develop`
  keeps both sides.
- The Wiki vaults hold real student data: tests use synthetic fixtures, and
  any run of the new rules against the vaults is read-only and reports counts
  only.
- The checks keep working offline from the locked install and write nothing
  outside their caches and the files they own.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each replacement tool MUST be pinned to one exact version: an
  npm dependency in `package.json` and its lock, a PyPI dependency in a uv
  lock, or a tool version in the repository's mise configuration. A tool that
  cannot be pinned so is an unmodified local copy with its license notice and
  upstream record, and the records say why.
- **FR-002**: Before a tool is added, its license MUST be confirmed from its
  repository, and a read-only security review of its source at the pinned
  version MUST find no standing high-severity problem for the planned use.
  High and medium findings go to the user through the develop session.
- **FR-003**: The environment check MUST use mise's pinned tool versions and
  its project checks for the pinned tools, the locked uv and npm
  environments, the git-flow configuration and the installed Git hooks.
  Quarto stays a separately installed converter (constitution I).
- **FR-004**: The plugin manifest check MUST validate each plugin's
  `plugin.json` and, where present, `mcp.json` against the vendored Agent
  Plugins schemas with the chosen upstream validator, offline.
- **FR-005**: The reference documents MUST be cog-generated regions checked
  by the existing document drift check, from the root tasks and their
  descriptions, the plugin manifests and the help text of the repository's
  own commands.
- **FR-006**: The Git hooks MUST be declared in lefthook's configuration and
  installed by lefthook; the commit-message hook runs commitlint.
- **FR-007**: The constitution's version line MUST be written by commitizen
  as the clarification decides.
- **FR-008**: The Wiki page rules that a pattern can express MUST be Vale
  rules run by the Wiki check, whose failures never repeat the matched text;
  the roster rules follow the clarification.
- **FR-009**: Wiki search MUST use qmd's own command or MCP server, not its
  internal module. The search functions that the request builders call keep
  their names and results, because CHE-39 changes the request builders.
- **FR-010**: The raw import MUST make and validate bags with bagit-python's
  own interface as the clarification decides, keeping the source record that
  the Wiki check reads.
- **FR-011**: After CHE-42 merges, verify's check evidence MUST come from
  Turborepo run summaries, the affected-files graph and the import rules from
  dependency-cruiser's own command and configuration, and the Python import
  boundaries from import-linter. The difficulty scoring and the skill
  triggers stay.
- **FR-012**: Each swap MUST remove the replaced code and the tests that only
  it used, and keep the capability shown by existing tests or a new one.
- **FR-013**: `AGENTS.md`, `orca.yaml`'s setup, `turbo.json`, the docs and
  the skills MUST name the new commands wherever a replaced command was
  named.
- **FR-014**: The records MUST report the own-code change per swap and in
  total, counted as CHE-42 counts: code in programming languages, tests and
  unmodified upstream copies excluded, a patched copy counted in full.
- **FR-015**: Tools installed outside the repository (for example through
  mise) MUST be installed only after the user approves, through the develop
  session.

### Key Entities

- **Swap**: one piece of own code, its upstream replacement, the pin, the
  license, the review verdict, the removed files, the own-code change and the
  dropped behaviours.
- **Security review**: a read-only review of one tool's source at the pinned
  version, with evidence for every finding and a verdict for the planned use.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `npm run verify` reports VERIFIED on the merged result.
- **SC-002**: The repository's own code shrinks by the reported total, and
  every listed piece of own code is gone or reduced to named glue.
- **SC-003**: Every added tool has a confirmed license and a security review
  with no standing high-severity finding.
- **SC-004**: Every capability of a replaced piece is either shown working by
  a test or listed as dropped, with the user's answer on whether it matters.

## Assumptions

- The first wave (environment check, manifest check, constitution version,
  reference documents, Git hooks, Wiki page rules, Wiki search, raw import)
  does not depend on CHE-42; the workflow and verify swaps and the
  import-boundary check come after CHE-42 merges.
- The Wiki request builders (`requests.py`) stay unchanged; CHE-39 changes
  them.
- Own-code lines are counted with scc 4.1.0 on Linguist programming
  languages, as CHE-42 counts them; before CHE-42 merges, the count uses the
  same method by hand.
