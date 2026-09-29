# Feature Specification: Own-Code Limit per Feature

**Feature Branch**: `feature/own-code-limit`

**Created**: 2026-09-30

**Status**: Draft

**Linear issue**: CHE-42

**Input**: Linear issue CHE-42, "Limit each feature to 300 net new lines of
own code unless the user approves more", and the develop session's task brief
of 2026-09-30. The user ruled on 2026-09-30 that a feature branch may add at
most 300 net lines of the repository's own code against its merge base with
`develop`, counting neither tests nor copied upstream code, unless the
feature's records hold the user's approval for a stated larger number. The
repository's own non-test code had grown from about 5,600 lines on 2026-09-27
to about 21,300 on 2026-09-30, against the "Reuse Before Implementing" order in
`AGENTS.md`. A check enforces the rule in `npm run verify` and in the develop
merge path. It identifies copied upstream code from records that exist or are
required anyway, not from a hand-kept exclusion list; it defines tests from the
repository's existing layout; it reuses an existing line counter and Git; and
its own code counts toward its own limit. It must not fail `develop` itself,
and it must treat the backfire rebuild's vendored jev-judge-mcp files (CHE-39)
as upstream copies through their existing upstream record.

## Clarifications

### Session 2026-09-30

- Q: Some copied upstream files carry a small local patch; the backfire
  rebuild had two, 411 code lines together. Does a patched copy count in full
  as own code (A), not at all (B), or only its patch lines (C)? → A: A. A
  file counts as an upstream copy only while its bytes match an upstream
  SHA-256 in its record, so a patched copy counts in full as the feature's own
  code. The definitions of code (GitHub Linguist's programming languages),
  tests (under a `tests/` folder or named `*_test.*` or `*.test.*`) and
  approval (a line the branch adds to its Spec Kit records naming the
  approved number) stand. The user added that the backfire rebuild (CHE-39)
  is switching from copied jev-judge-mcp files to the published package, so
  its copied files will disappear. The develop session relayed the answer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A feature over the limit fails verification (Priority: P1)

An agent works on a feature branch and runs `npm run verify` before it
finishes. The check measures how many lines of the repository's own code the
branch adds, net, against its merge base with `develop`. Over 300, the check
fails, and so does the feature finish, which runs the same verification.

**Why this priority**: It is the user's rule and the purpose of the feature.

**Independent Test**: On a scratch branch from `develop`, add a source file
with 301 own-code lines; the check fails and names the net count and the
limit. Remove one line; the check passes.

**Acceptance Scenarios**:

1. **Given** a branch whose own code grows by 301 net lines, **When**
   `npm run verify` runs, **Then** it fails, and the check's output names the
   own-code size at the merge base and on the branch, the net change (301) and
   the limit (300).
2. **Given** a branch whose own code grows by exactly 300 net lines, **When**
   the check runs, **Then** it passes.
3. **Given** a branch that adds 400 own-code lines and deletes 150, **When**
   the check runs, **Then** it reports a net change of 250 and passes.
4. **Given** `develop` itself with a clean worktree, **When** the check runs,
   **Then** the net change is 0 and it passes.

---

### User Story 2 - The user's recorded approval raises the limit (Priority: P1)

The user approves a larger size for one feature. The feature's records state
the approved number, and the check uses it as that branch's limit.

**Why this priority**: Without it, a feature the user has approved could not
be finished.

**Independent Test**: On the scratch branch over the limit, add an approval
line for 450 to the feature's spec; the check passes and names the approval's
file. Change the approval to 320 with a net change of 400; it fails again.

**Acceptance Scenarios**:

1. **Given** a branch with a net change of 400 whose records gain the line
   `**Own-code limit**: 450, approved by the user on 2026-09-30`, **When**
   the check runs, **Then** it passes and names 450 as the limit and the file
   that holds the approval.
2. **Given** an approval line that already exists at the merge base, such as
   one in an earlier feature's spec, **When** the check runs, **Then** it does
   not raise this branch's limit.
3. **Given** an approval for a number at or below 300, **When** the check
   runs, **Then** the limit stays 300.

---

### User Story 3 - Tests and upstream copies do not count (Priority: P2)

A feature adds tests, or vendors upstream files recorded with their upstream
SHA-256 hashes. Neither counts toward the limit.

**Why this priority**: The rule counts only code the repository owns; without
this, vendoring upstream code, which the reuse order prefers, would be
punished.

**Independent Test**: On a scratch branch, add a 500-line test file and a
500-line source file whose SHA-256 is recorded in an upstream record; the net
change is 0. Change one byte of the vendored file; its lines count as own
code.

**Acceptance Scenarios**:

1. **Given** a branch that adds files under a `tests/` folder or named like
   `*_test.ts` or `*.test.js`, **When** the check runs, **Then** those lines
   do not count.
2. **Given** a branch that adds a file whose SHA-256 appears in an upstream
   record in the same tree, **When** the check runs, **Then** its lines do not
   count.
3. **Given** the backfire rebuild branch, whose vendored jev-judge-mcp files
   are listed with their upstream SHA-256 in
   `packages/backfire/src/jev_judge_mcp/UPSTREAM.md`, **When** the check runs
   there, **Then** every vendored file whose bytes match its recorded hash is
   treated as an upstream copy.
4. **Given** Markdown, JSON, YAML, TOML or other files that hold no program
   code, **When** the check runs, **Then** they do not count.
5. **Given** a copied upstream file with a local patch, whose bytes no longer
   match its recorded hash, **When** the check runs, **Then** all its code
   lines count as own code.

---

### User Story 4 - The user sees the own-code size (Priority: P3)

The user wants to know how much own code the repository holds and how much a
branch adds. The check's output gives both, and the feature's records keep
the size of `develop` on 2026-09-30 as a baseline.

**Why this priority**: The numbers help the user judge requests, but the limit
works without them.

**Independent Test**: Run the check on `develop`; its output names the
own-code size, which equals the baseline recorded in this feature's records
while `develop` is unchanged.

**Acceptance Scenarios**:

1. **Given** any branch, **When** the check runs, **Then** its output names
   the own-code size at the merge base, on the branch and the net change.
2. **Given** this feature's records, **When** the user reads them, **Then**
   they find the own-code size of `develop` at 0bc0c63 as counts only, and
   this feature's own net change.

### Edge Cases

- A branch renames or moves a file: the file counts at both ends, so the net
  change reflects only content changes.
- The worktree has uncommitted or untracked, not ignored, files: they count,
  so `npm run verify` before a commit measures the work in progress.
- The merge base cannot be found, for example because no `develop` branch
  exists: the check fails and says so; it never passes silently.
- The line counter's environment is missing: the check fails and names the
  command that installs it.
- `develop` moves and is merged into the feature: the merge base moves too,
  so the net change counts only the feature's own work.
- A net decrease passes.
- Symbolic links, binary files and files the line counter does not recognize
  do not count.
- An upstream record lists a hash whose file is missing: nothing happens.
- The check itself runs on `develop`, `main`, a release or a hotfix branch:
  each is measured against its merge base with `develop`, and `develop` and
  `main`, which have nothing beyond that merge base, pass.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `npm run verify` MUST run the own-code check through
  `npm run check`. The feature finish hook already runs `npm run verify`, so
  the check also guards the merge into `develop`; the hook itself does not
  change.
- **FR-002**: The check MUST compute the net change as the own-code size of
  the worktree (tracked files plus untracked files Git does not ignore) minus
  the own-code size of the merge base of `HEAD` and `develop`.
- **FR-003**: The own-code size MUST be the sum of code lines, as the pinned
  line counter counts them (neither blank nor comment lines), over files that
  are code, are not tests and are not upstream copies.
- **FR-004**: A file MUST count as code only when the line counter assigns it
  a language that GitHub Linguist's language data classes as `programming`;
  the check keeps no list of languages of its own.
- **FR-005**: A file MUST count as a test when its path has a `tests`
  directory, or its name ends in `_test.<extension>` or `.test.<extension>`.
  These patterns cover every test file in the current layout: the `tests/`
  folders of the Python packages and the code plugin, `scripts/*_test.ts` and
  `scripts/*_test.py`, and the clean-code skill's `clean_code_test.ts`.
- **FR-006**: A file MUST count as an upstream copy when its SHA-256 appears
  in an upstream record of the same tree. Upstream records are the files named
  `UPSTREAM.md` or `upstream.json`, and Spec Kit's install manifests
  `.specify/integrations/*.manifest.json`. A file whose bytes differ from
  every recorded hash, such as a patched upstream copy, is own code in full.
  The check keeps no list of excluded files of its own.
- **FR-007**: The limit MUST be 300 net lines. A line matching
  `**Own-code limit**: <number>` that the branch adds, relative to the merge
  base, to a file under `specs/`, `.specify/bugs/` or `.specify/assessments/`
  MUST raise the limit to the largest such number. Lines that exist at the
  merge base MUST NOT.
- **FR-008**: When the net change exceeds the limit, the check MUST exit with
  a failure and name the sizes, the net change, the limit and how to record
  the user's approval. Otherwise it MUST pass and print the same numbers.
- **FR-009**: The check MUST NOT fail `develop` itself: with a clean worktree
  on `develop`, the net change is 0.
- **FR-010**: The check MUST reuse an existing line counter pinned like the
  repository's other tools, and Git; it MUST NOT count lines itself. It MUST
  NOT write to the repository or the Git index, and it MUST remove any
  temporary files it creates.
- **FR-011**: The check MUST fail, not pass, when it cannot measure: no merge
  base with `develop`, a missing line counter environment, or a counter error.
- **FR-012**: This feature's own net change, measured by the check itself,
  MUST stay within 300 lines, and the feature's records MUST report it and
  the own-code size of `develop` at 0bc0c63 as counts only.
- **FR-013**: The runtime doctor and the Orca setup script MUST cover the
  line counter's environment the way they cover the repository's other pinned
  tools, and `docs/architecture.md` MUST describe the check.

### Key Entities

- **Own-code size**: the code lines of one tree that are code, not tests and
  not upstream copies.
- **Net change**: the worktree's own-code size minus the merge base's.
- **Upstream record**: a file named `UPSTREAM.md` or `upstream.json`, or a
  Spec Kit install manifest, that records upstream SHA-256 hashes.
- **Approval line**: a line the branch adds to its Spec Kit records, stating
  the own-code limit the user approved for that feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a scratch branch 301 net own-code lines over its merge base,
  `npm run verify` fails; at 300 it passes.
- **SC-002**: The same over-limit branch passes after it adds an approval line
  for a larger number, and fails again when the approved number is below the
  net change.
- **SC-003**: `npm run verify` passes on `develop` and on this feature branch.
- **SC-004**: Measured on the backfire rebuild branch at 8a1d2f0, which holds
  the vendored jev-judge-mcp files, every file whose bytes match its recorded
  hash contributes 0 own-code lines. The rebuild's later switch to the
  published package removes those files, so this is checked once, on that
  commit; synthetic tests cover a patched copy.
- **SC-005**: This feature's own net change, as the check reports it, is at
  most 300 lines.
- **SC-006**: The feature's records hold the own-code size of `develop` at
  0bc0c63 as counts only.

## Assumptions

- "Code" means program code: the issue's figure of about 21,300 lines is
  close to the 21,049 non-blank lines of the repository's non-test Python,
  TypeScript, JavaScript, shell and PowerShell files at 0bc0c63, vendored
  copies included. GitHub Linguist classes exactly those as programming languages and
  Markdown, JSON, YAML, TOML, CSV, SVG and plain text as data, markup or
  prose.
- The approval line is written by the agent that received the user's
  approval, as with other user decisions in the records. The check cannot
  verify who approved; the develop merge review can.
- Upstream copies without recorded hashes, such as Ponytail's hook modules and
  Spec Kit's extension scripts, count as own code in the baseline. They count
  on a branch only when the branch changes them, and recording their hashes is
  outside this feature.
- The feature finish runs `npm run verify` in the feature worktree after
  `develop` has been merged into the feature, so the merge base there is the
  `develop` tip.
