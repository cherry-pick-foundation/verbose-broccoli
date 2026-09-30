# Feature Specification: Session Selection for the Wiki Vaults

**Feature Branch**: `feature/session-wiki`

**Created**: 2026-09-30

**Status**: Draft

**Linear issue**: CHE-47

**Own-code limit**: 560, a temporary setting for the old own-code check, which
the user abolished on 2026-09-30 in favor of the 1,000-line splitting review;
CHE-44 removes the check. The line keeps the check's required prefix. The
feature adds 507 net lines of own code, all in `session_select.py`. Its whole
change is 2,378 added lines against `develop` (1,073 records, documents and
data, 738 tests, 567 script and configuration); the user agreed not to split
it, because the rule, the tool and the procedure depend on one another.

**Input**: Linear issue CHE-47, "Select local Claude Code and Codex sessions
with backfire and record them in the Wiki vaults", and the develop session's
task brief of 2026-09-30. The user decided that every session Claude Code and
the Codex CLI keep on this laptop, Orca worker sessions included, is a
candidate for the Wiki vaults: about 165 Claude Code sessions
(`~/.claude/projects`, 580 MB) and about 1,312 Codex sessions
(`~/.codex/sessions`, 4.9 GB); the plan gives the files counted on
2026-09-30. OMP sessions are out of scope, and sessions still running wait until
they end. SpecStory's command-line tool renders the sessions to Markdown,
used unchanged with cloud sync off after a security review. Selection runs
mechanical filters, a secret scan before any text leaves the laptop, and
backfire classification in education mode; the user approves the list before
anything is admitted with the work plugin's `wiki-raw-import` skill.

This feature is stage 1: the constitution change, the SpecStory adoption and
the selection procedure. Stage 2, the import and the page writing across the
four vaults, runs afterwards in an Orca folder workspace on the vaults folder.

## Clarifications

### Session 2026-09-30

- Q: Where does the rendered text go? → A: The staging folder is
  `~/.cache/verbose-broccoli/sessions/` (`$XDG_CACHE_HOME` when set), mode
  `0700`, because it holds student data; everything in it can be rebuilt
  from the original session files.
- Q: May a session that holds student data go to a vault other than `work`?
  → A: No, only to `work`. A session holds student data when backfire's
  roster finds a student, guardian or school name in it; that check runs on
  this laptop before any text is sent.
- Q: How are Orca worker sessions weighed? → A: They are classified like the
  others, from their task and their final report. The catalog says a worker
  session has no lasting value unless it holds a lesson or decision that Git
  and the Spec Kit records do not keep. The develop session answered from the
  user's earlier choice to include all sessions.
- Q: The first sample returned 34% `review` results. How is that cut? → A:
  Sharpen the catalog so clear `none` cases, such as Orca worker sessions and
  sessions without a decision or lesson, pass without the user; keep
  backfire's auto-accept threshold; hold back Codex's own approval reviews
  before classification like the sessions with possible secrets and those
  without a user message; re-test on a fresh sample; run the full
  classification at the start of stage 2 with a fresh render. The user
  accepted the re-test's 19% `review` rate.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sessions may be raw evidence in any vault (Priority: P1)

An agent that admits a rendered Claude Code or Codex session into the `code`
or `default` vault finds the constitution, the skill and the vault schema
template allow it, as they already do for the `chat` and `work` vaults.

**Why this priority**: Without the rule change, stage 2 could admit sessions
only into `chat` and `work`.

**Independent Test**: Read constitution principle VI, the `wiki-raw-import`
skill and its schema template; each says exported Claude Code and Codex
sessions are raw evidence in any vault they belong to, and ChatGPT exports
keep their current rule.

**Acceptance Scenarios**:

1. **Given** the amended constitution, **When** an agent reads principle VI,
   **Then** exported Claude Code and Codex sessions are Raw evidence in any
   vault they belong to, and other conversation records are still not.
2. **Given** the constitution change, **When** its commit is checked,
   **Then** the version rises from 2.3.0 to 2.4.0 for a `feat` commit.

### User Story 2 - SpecStory renders sessions without network use (Priority: P1)

The user installs SpecStory's command-line tool on this laptop from a pinned,
reviewed release and renders sessions to a staging folder outside every
repository and vault, with nothing sent to specstory.com or any analytics
service.

**Why this priority**: Sessions hold student data and possibly secrets; the
converter must not leak them.

**Independent Test**: The security report names every network path and file
write with evidence and gives the command lines that avoid them; the pinned
install resolves to the reviewed release's checksum.

**Acceptance Scenarios**:

1. **Given** the security review's verdict is pass, **When** the tool is
   installed, **Then** it is the reviewed version, pinned with a reviewed lock.
2. **Given** the documented command line, **When** SpecStory renders a
   project's sessions, **Then** Markdown lands only in the staging folder and
   cloud sync, analytics and the version check stay off.

### User Story 3 - A repeatable selection procedure (Priority: P1)

An agent in stage 2 follows one reference file of the `wiki-raw-import` skill
to render, filter, scan, digest and classify the sessions, and to hand the
user a list for approval.

**Why this priority**: It is the feature's main deliverable.

**Independent Test**: The procedure's glue passes tests on synthetic session
fixtures, and a sample run on real sessions reports its backfire call count
and tokens.

**Acceptance Scenarios**:

1. **Given** synthetic sessions, one of them changed in the last hour,
   **When** the procedure runs, **Then** the recent session is left out.
2. **Given** a rendered session with a secret, **When** the scan runs,
   **Then** the session is held back and never sent to backfire.
3. **Given** digests, **When** they are classified, **Then** each gets one
   catalog label with its confidence, and "review" answers are listed for the
   user.
4. **Given** a sample of real sessions, **When** the procedure runs, **Then**
   the user receives the number of backfire calls, the tokens and an estimate
   for the whole set before the full run.

### Edge Cases

- A session whose project folder no longer exists (163 of 258 Codex project
  paths on 2026-09-30).
- Orca worker sessions, whose results already live in Git and the Spec Kit
  records.
- A session that holds student data and would also suit another vault.
- A digest over backfire's 2,000-character item limit.
- A session with no user message.
- A session that Codex started by itself to review an agent's action (half
  of the digests on 2026-09-30).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Constitution principle VI MUST allow exported Claude Code and
  Codex sessions as Raw evidence in any vault they belong to; ChatGPT exports
  stay Raw evidence in the `chat` and `work` vaults, and other conversation
  records in none.
- **FR-002**: The constitution change MUST be a `feat` commit that raises the
  version from 2.3.0 to 2.4.0 and records the decision in Governance.
- **FR-003**: The `wiki-raw-import` skill, its schema template and
  `docs/architecture.md` MUST state the rule of FR-001. The four vaults' own
  `AGENTS.md` files change in stage 2.
- **FR-004**: Before SpecStory is installed, a read-only security review of
  the pinned release's source MUST report its network use, telemetry, cloud
  sync defaults and every file it reads and writes, with evidence per finding.
- **FR-005**: SpecStory and the secret scanner MUST be pinned the way CHE-44
  pins tools: mise with a reviewed lock.
- **FR-006**: The procedure MUST write every rendered session, digest and
  result to a staging folder outside every repository and outside every
  vault's `raw/`.
- **FR-007**: Mechanical filters MUST run before the scan and the
  classification; they MUST leave out sessions still running, sessions
  without a user message, and the approval reviews that Codex starts by
  itself to judge an agent's action.
- **FR-008**: A secret scan MUST run on the rendered text; a session with a
  finding MUST NOT be sent to backfire.
- **FR-009**: Classification MUST use backfire in education mode on a
  per-session digest of at most 2,000 characters, in batches, against a
  catalog of the `code`, `work`, `default` and `chat` vaults plus "no lasting
  value".
- **FR-010**: "Review" answers MUST stay open for the user, and the user MUST
  approve the final list before any raw import.
- **FR-011**: A sample run MUST report the backfire call count and tokens,
  with an estimate for the whole set, before all sessions are classified.
- **FR-012**: A session in which backfire's roster finds a student, guardian
  or school name MUST be offered only to the `work` vault; the check runs
  locally before any text is sent. A match counts only at a word start, and
  a Latin-letter match only as a whole word, because on 2026-09-30 one
  two-syllable given name also occurred inside common Korean words in 433
  sessions.
- **FR-013**: Orca worker sessions MUST be classified from their task and
  final report, under the catalog rule of the clarification above.
- **FR-014**: Tests MUST use synthetic fixtures only. No student name, session
  content or secret enters the repository, Linear or Orca messages.

### Key Entities

- **Rendered session**: SpecStory's Markdown for one session, in the staging
  folder.
- **Digest**: a bounded excerpt of one rendered session sent for
  classification.
- **Catalog**: the vault labels and their descriptions that carry the
  classification decision.

## Success Criteria *(mandatory)*

- **SC-001**: The constitution, skill, template and architecture document
  agree on FR-001.
- **SC-002**: The security report gives a verdict with evidence for every
  finding, and SpecStory is installed only after a pass.
- **SC-003**: The procedure's glue passes its tests, and `npm run verify`
  passes on the merged result.
- **SC-004**: The user has the sample run's call count, tokens and estimate.

## Assumptions

- The raw evidence for a session is SpecStory's Markdown rendering, after
  its own secret redaction, not the original JSONL log.
- Nothing is admitted into a real vault in this feature.
