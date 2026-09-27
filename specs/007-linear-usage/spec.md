# Feature Specification: Linear Usage Through Orca

**Feature Branch**: `feature/linear-usage`

**Created**: 2026-09-27

**Status**: Draft

**Linear issue**: CHE-5

**Input**: On 2026-09-27 the user decided how this repository uses Linear. The
brief `briefs/2026-09-27-linear-and-documents.md`, section 1, outside the
repository, records the facts checked that day and eleven decisions:

1. Use Linear only through Orca (`orca linear` and Orca's `orca-linear`
   skill). No marketplace Linear plugin and none of the Spec Kit community
   catalog's Linear extensions (Linear Integration, Linear Weave, MAQA Linear
   Integration).
2. Archive, never delete. Set the team's auto-archive period to 1 month.
3. A Linear issue is a to-do entry per feature or bug: one issue per feature,
   no sub-issues. `tasks.md` stays the detailed task record.
4. No separate code wiki; the root `AGENTS.md` "Records" rule stands. Record
   only the decisions, lessons and bug causes the repository does not already
   hold: bugs in `.specify/bugs/<slug>/` through the Spec Kit bug extension,
   feature decisions in that feature's `specs/` directory, cross-feature
   lessons in `AGENTS.md` or `plugins/<name>/AGENTS.md` (judgment rules only).
   Cite the issue ID so the original can be found in Linear's archive. Do not
   copy issue originals into a Wiki instance's `raw/`.
5. Link the issue when creating the worktree (`--linear-issue`) and write the
   issue ID as one line in the spec. No commit trailer and no issue ID in
   branch names; commits reach the issue through `Spec-Kit-Task`, `tasks.md`
   and the spec. The bug assess command already records an issue URL in
   `assessment.md`.
6. Merging into `develop` counts as done. Write the record on the feature
   branch, move the issue to In Review for the `develop` merge review, merge,
   then move it to Done with one completion comment that gives the merge
   commit and the record location instead of a PR link. The record comes
   before the review because the finish hook needs the review record at the
   tip.
7. Only the main agent creates issues, after searching for similar ones.
   Workers report out-of-scope bugs to it through Orca messages.
8. No active-issue monitoring for now; a failed creation at the limit is the
   signal.
9. Privacy: one line in the root `AGENTS.md`, for example "Treat Linear issues
   and comments as writing to an external service: never put operational data
   such as student records, or secret values, in them."
10. Keep the single team and add the labels `code`, `work` and `chat`; leave
    the free plan's second team slot unused.
11. Do not use Linear features Orca lacks; the rare label or project creation
    happens in Linear's UI.

The brief also asks the plan to decide where each rule lives so agents
actually read it: the root `AGENTS.md` takes only rules that always need an
agent's judgment, and anything a tool, check or printed workflow text can carry
goes there instead. Any `AGENTS.md` line beyond the privacy line needs the
user's approval. Changes outside the repository (the auto-archive period, the
three labels, Codex's cached `linear` plugin) are proposed, not applied without
approval.

Facts from the brief, checked on 2026-09-27: Linear's free plan counts only
non-archived issues toward its 250-issue limit and keeps archived issues
without limit; above the limit no new issue can be created; deleted issues are
restorable for 30 days and then removed for good; closed issues are archived
after the team's auto-archive period. The workspace is `verbose-broccoli`, its
one team is `cherry-pick-foundation` with the key `CHE`, and its states are
Backlog, Todo, In Progress, In Review, Done, Canceled and Duplicate. Orca
1.4.215's `orca linear` reads, searches, creates and updates issues, comments,
attaches links and reads archived issues, but cannot archive or delete issues,
create labels or projects, or use Linear documents, cycles or milestones.

## Clarifications

### Session 2026-09-27

- Q: The brief's worktree command has no `--linear-issue`. Should one issue per
  feature be created now for this feature and the three features started with
  it, and each worktree linked? → A: Yes. The main agent searched for similar
  issues, found none, created CHE-5 (Linear usage), CHE-6 (repository document
  consistency), CHE-7 (Wiki storage and raw documents) and CHE-8 (Wiki document
  consistency) with the Feature label in In Progress, linked this worktree with
  `orca worktree set` and created the other three worktrees with
  `--linear-issue`.
- Q: Should Codex's cached, not enabled `linear` plugin be removed? → A: Yes.
  Its cache folder was moved to the trash. Codex refreshed every cached plugin
  of the `openai-curated-remote` marketplace on 2026-09-27, so the folder may
  return; it stays unused because `~/.codex/config.toml` does not enable it.
- Q: Besides the privacy line, should the root `AGENTS.md` carry the rule on
  who writes to Linear? It needs judgment each time, and it must reach
  workers, whom Orca's bundled `orca-linear` skill tells to create parented
  follow-up issues. → A: Yes, as one line under "Records": "Only the main
  agent writes to Linear. It creates one issue per feature or bug, without
  sub-issues, after searching for similar ones; other agents report
  out-of-scope bugs to it through Orca messages."

### Session 2026-09-28

- The develop session reported that the labels `code`, `work` and `chat` now
  exist in team `CHE`, created in Linear's UI at the user's request, and that
  CHE-7 and CHE-8 carry `work`. Issues already combine labels, for example
  CHE-9 with Feature, `code` and `work`.

## User Scenarios & Testing *(mandatory)*

The actors are the user, who owns the repository, the Linear workspace and
their decisions; the main agent (the orchestrator of a feature, Claude Code or
Codex), which owns Linear writes; and worker agents, which implement tasks
under the main agent's supervision through Orca.

### User Story 1 - Each feature or bug is one Linear issue that the repository can find (Priority: P1)

When work on a new feature or bug starts, the main agent searches Linear for a
similar issue, creates one issue if none exists, links the new worktree to it,
and writes the issue ID as one line in the spec. From then on the issue, the
worktree and the Spec Kit record point at each other without trailers or
branch-name conventions.

**Why this priority**: Everything else (completion, records, archive lookups)
depends on each feature having exactly one findable issue.

**Independent Test**: Start a feature in a new worktree: `orca linear issue
--current` in that worktree returns the issue, the spec has exactly one Linear
line with the same ID, and no commit trailer or branch name carries it.

**Acceptance Scenarios**:

1. **Given** a new feature and no similar issue in Linear, **When** the main
   agent starts it, **Then** exactly one issue exists for it, the worktree was
   created linked to that issue, and the feature's spec names the issue ID in
   one line.
2. **Given** a similar issue already exists, **When** the main agent starts
   the work, **Then** it reuses or links that issue instead of creating a
   second one.
3. **Given** a worktree created without a link, **When** the main agent
   notices (Orca reports no linked issue), **Then** it links the existing
   worktree to the issue without recreating the worktree.
4. **Given** a worker finds a bug outside its task, **When** it reports the
   bug, **Then** it sends an Orca message to the main agent and creates no
   issue itself; the main agent decides whether to create a Bug issue, without
   making it a sub-issue.

---

### User Story 2 - Merging into `develop` completes the issue in a fixed order (Priority: P1)

When a feature is ready, the main agent writes its record on the feature
branch, moves the issue to In Review, runs the `develop` merge review, adds the
review-record commit, finishes the feature into `develop`, and then moves the
issue to Done with one completion comment that names the merge commit and the
record location.

**Why this priority**: The completion flow is the only regular Linear write
besides creation; getting its order wrong blocks the finish (the finish hook
requires the review record at the tip) or leaves Linear out of date.

**Independent Test**: Finish this feature: during its merge review CHE-5 is In
Review; after the finish it is Done with exactly one completion comment naming
the merge commit hash on `develop` and `specs/007-linear-usage/`, and no PR
link.

**Acceptance Scenarios**:

1. **Given** a feature whose implementation is verified, **When** the main
   agent prepares the merge, **Then** the record is committed on the feature
   branch before the merge review, and the issue is In Review during the
   review.
2. **Given** the finish into `develop` succeeded, **When** the main agent
   completes the issue, **Then** the issue is Done and has exactly one
   completion comment with the merge commit and the record location.
3. **Given** the Linear update fails after a successful finish, **When** the
   main agent retries, **Then** the finish is not repeated, no second
   completion comment is posted, and the pending Linear step is recorded in
   `tasks.md` until it succeeds.
4. **Given** an issue already Done or Canceled, **When** completion runs,
   **Then** its state is not moved backward.

---

### User Story 3 - Nothing private reaches Linear (Priority: P1)

Every agent treats Linear issues and comments as writing to an external
service and never puts operational data, such as student records, or secret
values into them.

**Why this priority**: Linear is a hosted service outside the user's machine;
a leak cannot be taken back by archiving, and the constitution forbids
publishing restricted data.

**Independent Test**: The root `AGENTS.md` contains the privacy line; every
issue body and comment written during features 007 to 010 contains no
operational data or secret values.

**Acceptance Scenarios**:

1. **Given** a bug whose evidence includes a student record or a secret,
   **When** the main agent writes the issue, **Then** the issue describes the
   bug without that data and points to the repository record instead.
2. **Given** private data was written to Linear by mistake, **When** an agent
   notices, **Then** it reports this to the user at once, and the user decides
   how to remove it.

---

### User Story 4 - The free plan keeps working without deleting anything (Priority: P2)

Closed issues leave the active count by archiving, never by deletion, so the
free plan's 250-issue limit is not reached in ordinary use and old issues stay
findable in Linear's archive.

**Why this priority**: The limit blocks all new issues when reached, and a
deletion loses the original after 30 days; but the limit is far away (four
active issues on 2026-09-27), so this matters less than the daily flow.

**Independent Test**: The team's auto-archive period reads 1 month; no agent
workflow deletes an issue; an archived issue is still readable with `orca
linear list-issues --include-archived`.

**Acceptance Scenarios**:

1. **Given** a Done issue older than the auto-archive period, **When** Linear
   archives it, **Then** it no longer counts toward the limit and the
   repository's citation of its ID still finds it through the archive.
2. **Given** issue creation fails because the limit is reached, **When** the
   main agent sees the failure, **Then** it reports this to the user and
   deletes nothing.

---

### User Story 5 - Linear is reached only through Orca (Priority: P2)

Agents use Linear through Orca's commands and skill only. No Claude Code or
Codex marketplace Linear plugin is enabled, and no Spec Kit Linear extension is
installed.

**Why this priority**: The user's Orca-first decision keeps one integration
path, visible in Orca, and avoids extensions that bypass it; nothing is
enabled today, so this story mostly keeps it that way.

**Independent Test**: Claude Code's and Codex's saved configurations enable no
Linear plugin, `.specify/extensions.yml` lists no Linear extension, and the
repository documents Orca as the only Linear path.

**Acceptance Scenarios**:

1. **Given** a session that needs Linear, **When** the agent looks for a way to
   reach it, **Then** the repository points it to `orca linear` and the
   `orca-linear` skill.
2. **Given** a Linear capability Orca lacks (archiving, deleting, labels,
   projects, documents, cycles, milestones), **When** it seems needed, **Then**
   the agent asks the user to do it in Linear's UI instead of adding another
   integration.

---

### User Story 6 - A reader at HEAD can learn how the repository uses Linear (Priority: P3)

A person or agent who has not seen the 2026-09-27 discussion can learn from the
repository which Linear team and labels exist, how issues relate to features,
bugs and records, and what happens at completion.

**Why this priority**: The rules that run by themselves still need one
explanation for readers; it has no effect on the daily flow.

**Independent Test**: The repository's architecture documentation has a
Linear section that answers those questions and points to the places that
carry each rule.

**Acceptance Scenarios**:

1. **Given** a new session at HEAD, **When** it reads the documentation,
   **Then** it can tell where each Linear rule lives and why.

### Edge Cases

- The main agent is not running in an Orca terminal, or Orca is not running:
  the Linear step waits; nothing falls back to another integration.
- Orca reports an unconfirmed Linear write: follow the `orca-linear` skill's
  replay or read-back rule, so no issue or completion comment is duplicated.
- Two features turn out to be one: the later issue is marked Duplicate, not
  deleted.
- A feature is abandoned: its issue is moved to Canceled, not deleted, and the
  spec keeps the ID.
- A feature started before this one (`feature/005-backfire-mcp`) has no issue:
  it is not retrofitted unless the user asks.
- Orca's bundled `orca-linear` skill advises parented follow-up issues and PR
  links at completion: in this repository no sub-issues are created and the
  completion comment names the merge commit instead of a PR.
- A worker in a Linear-linked worktree can reach `orca linear` too: the rule
  that only the main agent writes to Linear must reach workers as well.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Agents MUST use Linear only through Orca's `orca linear`
  commands and `orca-linear` skill. No marketplace Linear plugin is enabled
  for Claude Code or Codex, and no Spec Kit catalog Linear extension is
  installed.
- **FR-002**: Each feature and each bug MUST have exactly one Linear issue in
  team `CHE`, without sub-issues. `tasks.md` stays the detailed task record.
- **FR-003**: Only the main agent MUST create Linear issues or change their
  state, and only after searching for similar ones. Other agents MUST report
  out-of-scope bugs to the main agent through Orca messages.
- **FR-004**: A feature's worktree MUST be linked to its issue when it is
  created (or linked afterwards when that was missed), and the feature's spec
  MUST name the issue ID in exactly one line. Commits MUST NOT carry an issue
  trailer and branch names MUST NOT carry the issue ID.
- **FR-005**: A bug's record MUST stay in `.specify/bugs/<slug>/` through the
  Spec Kit bug extension, whose assessment records the issue URL.
- **FR-006**: Completion MUST follow this order: the record is committed on
  the feature branch; the issue moves to In Review; the `develop` merge review
  and the review-record commit follow; the feature is finished into `develop`;
  the issue moves to Done with exactly one completion comment naming the merge
  commit and the record location. No PR link is used.
- **FR-007**: Repository records MUST hold only the decisions, lessons and bug
  causes the repository does not already hold, cite the issue ID, and never
  copy issue originals into a Wiki instance's `raw/`.
- **FR-008**: Agents MUST NOT delete Linear issues. Closed issues leave the
  active count through Linear's auto-archive, set to 1 month.
- **FR-009**: The team `CHE` MUST remain the only team, with the labels `code`,
  `work` and `chat` next to the Feature, Bug and Improvement labels.
- **FR-010**: There MUST be no active-issue monitoring. When issue creation
  fails at the plan's limit, the main agent reports it to the user and deletes
  nothing.
- **FR-011**: The root `AGENTS.md` MUST contain one line telling agents to
  treat Linear issues and comments as writing to an external service and never
  to put operational data such as student records, or secret values, in them.
- **FR-012**: Each rule above MUST live where agents read it when it applies.
  The root `AGENTS.md` takes only rules that always need judgment; any line
  beyond FR-011's and the one the user approved (see Clarifications) needs
  the user's approval. Rules a tool, check, printed workflow text or
  configuration can carry go there.
- **FR-013**: Linear features Orca lacks MUST NOT be used through other
  integrations; label, project and team-setting changes happen in Linear's UI.
  Changes outside the repository (the auto-archive period, the three labels,
  saved client configuration) are applied only after the user's approval.
- **FR-014**: The repository's architecture documentation MUST describe the
  Linear usage and point to where each rule lives.

### Key Entities

- **Linear issue**: the to-do entry for one feature or bug in team `CHE`, with
  an ID such as `CHE-5`, one type label (Feature, Bug or Improvement), a state,
  and at most one completion comment.
- **Worktree link**: Orca's metadata tying a worktree to one issue, set at
  creation or afterwards.
- **Spec line**: the one line in a feature's `spec.md` that names its issue
  ID.
- **Record**: the repository's durable account of a feature or bug
  (`specs/<feature>/`, `.specify/bugs/<slug>/`, `AGENTS.md` lessons) that cites
  the issue ID.
- **Completion comment**: the single comment on a finished feature's issue
  naming the merge commit and the record location.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Features 007 to 010 each have exactly one issue (CHE-5 to CHE-8),
  each of their worktrees reports its issue as linked, and each spec names its
  issue in exactly one line.
- **SC-002**: When this feature is finished, CHE-5 was In Review during the
  merge review and afterwards is Done with exactly one completion comment
  naming the merge commit on `develop` and `specs/007-linear-usage/`.
- **SC-003**: A walkthrough by an agent that has read only the repository at
  HEAD finds, for each of the four Linear moments (start a feature, report a
  bug, complete a feature, need a missing Linear feature), the rule that
  applies, in a place that agent reads at that moment.
- **SC-004**: The root `AGENTS.md` gains exactly the two approved Linear lines
  (privacy, and who writes to Linear) and no other.
- **SC-005**: No Linear plugin is enabled in Claude Code's or Codex's saved
  configuration, and `.specify/extensions.yml` lists no Linear extension.
- **SC-006**: After the user applies the proposed settings, the team's
  auto-archive period reads 1 month and the labels `code`, `work` and `chat`
  exist; no issue was deleted.

## Assumptions

- The user's 2026-09-27 decisions authorize the main agent's Linear writes
  named here: creating issues, linking worktrees, moving issue states and
  posting one completion comment. Any other Linear write needs the user's
  approval, as the constitution's rule on external messages requires.
- The labels `code`, `work` and `chat` mark the plugins an issue concerns, next
  to its one type label; an issue can carry more than one of them, and one
  about repository-wide tooling carries none. The brief names the labels
  without saying how they are applied; the issues labeled on 2026-09-28
  follow this reading.
- Orca 1.4.215's `orca linear` behaves as the brief records; a later Orca that
  archives issues or creates labels does not change these rules without the
  user's decision.
- The auto-archive period and labels are set by the user in Linear's UI, since
  Orca cannot set them and no Linear API key is configured. The labels exist
  since 2026-09-28; the auto-archive period is not visible through Orca.
- The separate web wiki the user plans (Quarto pages published with
  Docusaurus) and the Wiki features 009 and 010 are unaffected, except that
  issue originals never enter a Wiki's `raw/`.
