# Feature Specification: Governance Policies of 2026-09-27

**Feature Branch**: `feature/governance-policies`

**Created**: 2026-09-27

**Status**: Draft

**Input**: On 2026-09-27 the user made eight governance decisions, recorded in
the brief `briefs/2026-09-27-governance-policies.md` outside the repository:

1. Orca first: when Orca already offers a capability, use it instead of
   building it into the Code or Work plugins.
2. Connect an app through Orca when Orca supports it; use a plugin marketplace
   only for apps Orca does not support.
3. The final independent review happens only after implementation, when a
   branch merges into `develop` (favoring speed) or `main` (favoring accuracy).
   For ordinary commits the implementer re-reviews its own diff. The reviewer
   stays a fresh agent from the other provider that gets only the scope and
   requirements.
4. After the `develop` merge review, a content-free review-record commit with
   the trailers `Reviewed-by` and `Reviewed-commit` goes on the feature
   branch tip, and the git-flow feature-finish hook refuses the finish unless
   the tip is such a commit whose parent is the reviewed commit.
5. Releases and hotfixes are finished by hand, so the constitution's finishing
   procedure gets a "review before merge" step instead of a hook.
6. The main agent chooses each worker's and reviewer's model, reasoning effort
   and time budget, case by case, from the code plugin's backfire judgments
   (the local jev setup until backfire works). No mapping table from
   difficulty to model exists or may be added.
7. The Conventional Commits type of the commit that changes the constitution
   decides its version bump, once per commit: a breaking mark raises the first
   digit and needs the user's approval, `feat` the middle digit, `docs` or
   `fix` the last digit.
8. `AGENTS.md` holds only rules that always need an agent's judgment; anything
   a hook, check, tool output or one-time configuration can enforce goes into
   that mechanism.

A later addendum the same day added one decision. `orca worktree create --name
feature/x` turns the `/` into `-` and adds only Orca's single global branch
prefix, and Orca's command line has no per-worktree branch option. So the
agent picks the git flow type through the worktree name, and Orca's setup
script, which runs for every new worktree before agents start, renames the new
worktree's branch mechanically (`release-<rest>` to `release/<rest>`,
`hotfix-<rest>` to `hotfix/<rest>`, anything else to `feature/<name>` with a
leading `feature-` removed). Folder names keep the flat convention. The glue is
removed once Orca's command line offers a branch option.

## Clarifications

### Session 2026-09-27

- Q: Should the commit-message check refuse trailers other than
  `Spec-Kit-Task`, `Reviewed-by`, `Reviewed-commit` and `Co-Authored-By`? → A:
  No. Any trailer is accepted; the four named ones must always pass.
- Q: When a commit changes the constitution but leaves its version unchanged,
  what should the check do? → A: Refuse it. Every commit that changes the
  constitution bumps its version exactly once, so only `feat`, `docs`, `fix`
  or a breaking commit can change the constitution.

## User Scenarios & Testing *(mandatory)*

The actors are the user, who owns the repository and its decisions, and the
coding agents (Claude Code and Codex) that implement, review, commit and finish
branches under the repository's rules.

### User Story 1 - A feature reaches `develop` only after a recorded merge review (Priority: P1)

An agent finishing a feature into `develop` must show that a fresh reviewer
looked at exactly the commit being merged. The agent records the review as a
content-free commit on the feature branch tip that names the reviewer and the
reviewed commit. The feature finish refuses to run unless that record is the
tip and nothing changed after the review.

**Why this priority**: It turns decision 3's merge-time review and decision 4's
evidence rule from agent memory into a check that cannot be skipped by
forgetting. It is the main behavior change of this feature.

**Independent Test**: In a scratch repository with the committed git-flow
settings and hook, attempt `git flow feature finish` with and without a valid
review record at the feature tip, and compare branch and worktree state before
and after each refused attempt.

**Acceptance Scenarios**:

1. **Given** a feature whose tip is an ordinary commit, **When** the agent runs
   the finish from the `develop` worktree, **Then** the finish is refused with a
   message that asks for a review-record commit, and no branch, worktree or
   index changes.
2. **Given** a feature whose tip is a content-free commit with one
   `Reviewed-by` and one `Reviewed-commit` trailer naming the tip's parent,
   and verification passes, **When** the agent runs the finish, **Then**
   `develop` gets the usual no-fast-forward merge whose second parent is the
   review-record commit.
3. **Given** a review record whose `Reviewed-commit` names a commit other than
   its parent, **When** the agent runs the finish, **Then** the finish is
   refused and nothing changes.
4. **Given** a tip commit that carries both trailers but also changes files,
   **When** the agent runs the finish, **Then** the finish is refused because the
   record is not content-free.
5. **Given** a tip commit missing either trailer, or carrying either trailer
   more than once or with an empty value, **When** the agent runs the finish,
   **Then** the finish is refused.
6. **Given** a valid review record followed by `develop` being merged into the
   feature, **When** the agent runs the finish, **Then** the finish is refused,
   because the reviewed commit is no longer the one being merged.

---

### User Story 2 - Every commit message follows Conventional Commits, and constitution versions follow the commit type (Priority: P1)

When an agent or the user creates a commit in this repository, the commit
message is checked before the commit is recorded. The header must follow
Conventional Commits 1.0.0. Trailers are accepted, including the repository's own. When
the commit changes the constitution, its version must rise by exactly the one
step that the commit type calls for.

**Why this priority**: Decision 7 makes version bumps mechanical, and decision 8
moves enforceable rules out of `AGENTS.md` into mechanisms. Without a check,
both depend on each agent remembering them.

**Independent Test**: In a scratch repository installed the same way as a real
worktree, attempt commits with valid and invalid headers, with each accepted
trailer, with Git's default merge message, and with each kind of constitution
version change; observe which commits are recorded.

**Acceptance Scenarios**:

1. **Given** the check is installed, **When** a commit message's header is not
   `type(scope)!: description` in Conventional Commits form (for example
   `Update files`), **Then** the commit is refused and the message explains
   why.
2. **Given** the check is installed, **When** a commit message has a valid
   header and any of the trailers `Spec-Kit-Task`, `Reviewed-by`,
   `Reviewed-commit` or `Co-Authored-By`, **Then** the commit is recorded.
3. **Given** the check is installed, **When** Git creates a merge commit with
   its default message (as `git flow feature finish` and the hand-finished
   release and hotfix merges do), **Then** the commit is recorded.
4. **Given** the constitution is at version `X.Y.Z`, **When** a `feat` commit
   sets it to `X.(Y+1).0`, a `docs` or `fix` commit sets it to `X.Y.(Z+1)`, or
   a breaking commit sets it to `(X+1).0.0`, **Then** the commit is recorded.
5. **Given** the constitution is at version `X.Y.Z`, **When** a commit changes
   the version by any other step (skipping a number, raising the wrong digit,
   lowering it, or using another commit type), **Then** the commit is refused
   and the message states the expected version.
6. **Given** the constitution is at version `X.Y.Z`, **When** a commit changes
   the constitution's text but leaves the version at `X.Y.Z`, **Then** the
   commit is refused.
7. **Given** a fresh worktree created by Orca, **When** Orca's setup finishes,
   **Then** the check is active in that worktree, and the repository's doctor
   check fails when the installation is missing or differs.

---

### User Story 3 - Agents get the new review, model-choice and version rules from the right place (Priority: P2)

Agents read their standing rules from `AGENTS.md`, the constitution and the
text `deno task workflow` prints. After this feature, each source states the
2026-09-27 decisions that belong to it, and none contradicts them.

**Why this priority**: The mechanisms in stories 1 and 2 cover what can be
enforced; the remaining rules need judgment and must reach agents in words.

**Independent Test**: Read `AGENTS.md`, the constitution and the output of
`deno task workflow` in REVIEW mode, and check each against the decisions.

**Acceptance Scenarios**:

1. **Given** `AGENTS.md`, **When** an agent reads it, **Then** it finds exactly
   three new rules: the implementer re-reviews its own diff before each commit;
   a review before merging into `develop` favors speed and one before merging
   into `main` favors accuracy; and the main agent chooses each worker's and
   reviewer's model, reasoning effort and time budget from the code plugin's
   backfire judgments. Nothing else in `AGENTS.md` changes.
2. **Given** the constitution, **When** an agent reads Governance, **Then** the
   version rule is decision 7's commit-type rule, and the old rule ("principle
   changes raise the draft minor version, wording corrections the patch
   version") is gone.
3. **Given** the constitution, **When** an agent reads the release and hotfix
   finishing procedure, **Then** it includes a review before merge, by a fresh
   reviewer from the other provider, before the merge into `main` is staged.
4. **Given** the constitution amendment is committed, **When** its version is
   compared with the previous one, **Then** the bump matches the amendment
   commit's type under decision 7.
5. **Given** `deno task workflow` selects REVIEW mode, **When** an agent reads
   its instructions, **Then** they say the implementer re-reviews its own diff
   before committing and the independent review happens at the merge into
   `develop` or `main`; they no longer ask for a separate diff review of each
   change.

---

### User Story 4 - A reader at HEAD can learn the procedures from the documentation (Priority: P3)

A reader who has not seen this conversation opens `docs/architecture.md` and
the generated reference and learns how reviews are timed and recorded, how a
feature is finished, and how commit messages are checked.

**Why this priority**: Documentation follows the behavior; it has no effect of
its own but keeps later agents from relying on memory.

**Independent Test**: Read the updated sections and run the reference drift
check.

**Acceptance Scenarios**:

1. **Given** `docs/architecture.md`, **When** a reader looks up the review,
   git-flow and commit procedures, **Then** each describes the behavior this
   feature delivers, including what stays manual.
2. **Given** the generated reference files, **When** the drift check runs,
   **Then** it passes with the new or changed commands listed.

---

### User Story 5 - A new Orca worktree gets its git flow branch name without manual renaming (Priority: P2)

An agent creates a worktree with Orca and chooses the git flow type through
the worktree name, for example `feature-governance-policies`, `release-1.0` or
`hotfix-1.0`. Before any agent starts in it, Orca's setup renames the new
worktree's branch to the git flow form, so `git flow feature finish` and the
constitution's branch rules work without a manual rename.

**Why this priority**: Without it, every new worktree needs a hand rename
before git flow accepts its branch, as happened for this feature. It does not
change review or commit rules, so it ranks below stories 1 and 2.

**Independent Test**: In scratch repositories, run the setup's branch-naming
step in freshly created worktrees with each kind of name, and in worktrees that
have commits, an upstream, a git flow name already, or `develop` or `main`
checked out; then run it a second time.

**Acceptance Scenarios**:

1. **Given** a just-created worktree whose name is `release-1.0`, **When**
   setup runs, **Then** its branch is `release/1.0`.
2. **Given** a just-created worktree whose name is `hotfix-1.0`, **When** setup
   runs, **Then** its branch is `hotfix/1.0`.
3. **Given** a just-created worktree whose name is `governance-policies` or
   `feature-governance-policies`, **When** setup runs, **Then** its branch is
   `feature/governance-policies`.
4. **Given** a worktree whose branch has its own commits beyond its base, has
   an upstream, or is already in git flow form, **When** setup runs, **Then**
   the branch keeps its name.
5. **Given** a worktree on `develop` or `main`, **When** setup runs, **Then**
   nothing is renamed.
6. **Given** setup has already renamed a branch, **When** setup runs again,
   **Then** nothing changes.
7. **Given** any of the cases above, **When** setup finishes, **Then** the
   worktree folder keeps its name and no other branch or worktree changes.

---

### Edge Cases

- The feature branch is checked out in no worktree, or its worktree has
  uncommitted changes: the existing refusals still apply, before or after the
  review-record check.
- The review record is itself a merge commit: refused, because a record has
  exactly one parent.
- `Reviewed-commit` holds an abbreviated or otherwise ambiguous commit name:
  accepted only if it resolves to exactly the tip's parent.
- The trailer tokens differ only in letter case (`Reviewed-By`): Git treats
  trailer keys case-insensitively; the hook follows Git.
- A commit carries a `BREAKING CHANGE` footer instead of `!`: the
  commit-message check treats it as a breaking mark, as Conventional Commits
  1.0.0 does. The repository's own trailer tokens use `-` and never look like
  `BREAKING CHANGE`.
- A commit adds the constitution for the first time, or deletes it: there is no
  previous version to compare, so the version rule does not apply.
- The constitution version line is missing or malformed after the change: the
  commit is refused.
- An amended commit (`git commit --amend`): a commit-message hook is not told
  that the commit is an amend, so the constitution rule compares the amended
  content with the commit being replaced. An amend that changes only the
  header type is not re-checked; this limit is documented.
- Commits made with `--no-verify`: the check cannot stop them; the constitution
  already forbids bypassing hooks.
- A worktree whose checkout predates this feature (for example another feature
  branch that has not merged `develop` yet): the shared installation points at
  a check the checkout does not contain, and commits there proceed unchecked
  until that branch merges `develop`.
- The git flow name that setup would give a new worktree's branch already
  exists: setup stops with a message naming both branches and renames nothing.
- A worktree name is exactly `release-` or `hotfix-` (nothing after the
  prefix), or the resulting name is not a valid Git branch name: setup stops
  with a message and renames nothing.
- The worktree is on a detached HEAD: setup renames nothing.
- Deno is not on the `PATH` of the process that runs Git: the check still finds
  the runtime the way Orca's setup does, or refuses the commit with a clear
  message instead of passing silently.

## Requirements *(mandatory)*

### Functional Requirements

**Feature finish and merge review (decisions 3 and 4)**

- **FR-001**: The feature-finish hook MUST refuse the finish unless the feature
  branch tip is a review-record commit: exactly one parent, the same tree as
  that parent, exactly one non-empty `Reviewed-by` trailer and exactly one
  `Reviewed-commit` trailer.
- **FR-002**: The hook MUST refuse the finish unless the `Reviewed-commit`
  value resolves to the review-record commit's parent.
- **FR-003**: Every refusal MUST leave branches, worktrees, the index and
  working files unchanged, and MUST name the failed condition and what to do
  next.
- **FR-004**: The hook MUST keep its existing checks (run from a clean
  `develop` worktree, `develop` is an ancestor of the feature, the feature is
  checked out in a clean worktree, and verification passes there).
- **FR-005**: A successful finish MUST keep the existing merge shape: a
  no-fast-forward merge with Git's default message whose parents are `develop`
  and the review-record commit, and whose tree is the reviewed tree.

**Commit-message check (decisions 7 and 8)**

- **FR-006**: A commit-message check MUST run for every commit created in a
  set-up worktree and refuse messages whose header does not follow
  Conventional Commits 1.0.0.
- **FR-007**: The check MUST accept the trailers `Spec-Kit-Task`,
  `Reviewed-by`, `Reviewed-commit` and `Co-Authored-By`, and MUST NOT refuse a
  commit for carrying other trailers.
- **FR-008**: The check MUST accept Git's default merge messages, so that
  git-flow feature finishes and hand-finished release and hotfix merges are
  not refused.
- **FR-009**: When a commit changes `.specify/memory/constitution.md`, the
  check MUST refuse it unless the new version is the previous version raised
  by exactly one step of the kind the commit type calls for: breaking (`!` in the header or a `BREAKING CHANGE`
  footer) raises the first digit and resets the others; `feat` raises the
  middle digit and resets the last; `docs` or `fix` raises the last digit. A
  version change under any other type MUST be refused.
- **FR-010**: A commit that changes the constitution but leaves its version
  unchanged MUST be refused, whatever its type.
- **FR-011**: Orca's setup MUST install the check for each worktree, and
  `deno task doctor` MUST fail when it is not installed as the repository
  expects, in the same way both already handle the git-flow configuration.
- **FR-012**: The check MUST reuse an existing upstream commit linter when one
  fits, following the root `AGENTS.md` reuse order; locally written code is
  limited to the constitution version rule and the installation glue.

**Rules for agents (decisions 3, 5, 6, 7 and 8)**

- **FR-013**: `AGENTS.md` MUST gain exactly the three rules the brief lists,
  with the first two under "Review"; no other `AGENTS.md` text changes.
- **FR-014**: The constitution's Governance section MUST replace the old
  version rule with decision 7, including that a breaking bump needs the
  user's approval.
- **FR-015**: The constitution's release and hotfix finishing procedure MUST
  add a review before merge by a fresh reviewer from the other provider, given
  only the scope and requirements, favoring accuracy, before the merge into
  `main` is staged.
- **FR-016**: The constitution amendment MUST bump the version by decision 7
  according to the type of the commit that makes it, and its Sync Impact Report
  MUST record the change.
- **FR-017**: `deno task workflow` in REVIEW mode MUST describe decision 3
  (self-review of the diff before each commit; the independent review at merge
  time) instead of a separate diff review per change, and the affected tests
  and snapshots MUST match.

**Documentation**

- **FR-018**: `docs/architecture.md` MUST describe the review timing and
  record, the feature-finish checks, the commit-message check and its
  installation, and what stays manual.
- **FR-019**: The generated files in `docs/reference/` MUST be regenerated and
  pass the drift check.

**This feature's own merge**

- **FR-020**: This feature's merge into `develop` MUST receive a merge review
  and a review-record commit even though `develop`'s hook does not yet require
  it.

**Branch names for new worktrees (addendum)**

- **FR-021**: Orca's setup MUST rename the branch checked out in the worktree
  being set up to its git flow form, derived from the worktree name: a name
  starting with `release-` gives `release/<rest>`, one starting with `hotfix-`
  gives `hotfix/<rest>`, and any other name gives `feature/<name>` after one
  leading `feature-` is removed.
- **FR-022**: Setup MUST rename only when the branch was just created by Orca
  (no commits of its own beyond its base and no upstream) and is not already in
  git flow form; it MUST NOT rename `develop`, `main` or any branch other than
  the one checked out in the worktree being set up.
- **FR-023**: Running setup again MUST change nothing, and worktree folder
  names MUST NOT change.
- **FR-024**: When the target branch name already exists or is not a valid
  branch name, setup MUST stop with a message and rename nothing.
- **FR-025**: The repository MUST record that this renaming is temporary glue
  to be removed once Orca's command line offers a branch option for
  `orca worktree create`.

### Key Entities

- **Review-record commit**: A content-free commit at the feature branch tip.
  Attributes: its single parent, the `Reviewed-by` trailer (who reviewed) and
  the `Reviewed-commit` trailer (what was reviewed, equal to the parent).
- **Commit message**: A Conventional Commits header (type, optional scope,
  optional breaking mark, description), optional body, and trailers.
- **Constitution version**: The `X.Y.Z` value on the constitution's version
  line, compared between a commit and its parent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the automated finish tests, 100% of refusal cases (no record,
  wrong reviewed commit, record with file changes, missing or duplicate
  trailers, merge after review) leave all branches and worktrees unchanged, and
  the valid case produces the expected merge.
- **SC-002**: In the automated commit tests, every accepted and refused case in
  User Story 2 behaves as specified, including all four trailers and Git's
  default merge message.
- **SC-003**: The commit-message check adds no more than 2 seconds to a commit
  on the development machine.
- **SC-004**: `AGENTS.md` differs from `develop` by exactly three added rules
  and nothing else.
- **SC-005**: `deno task verify` passes on the final feature tree, and the
  reference drift check reports no difference.
- **SC-006**: A fresh Orca worktree has the commit-message check active and
  `deno task doctor` passing without manual steps.
- **SC-007**: In the automated branch-naming tests, every case in User Story 5
  gives the expected branch name, and a second run changes no reference.

## Assumptions

- "Content-free" means the commit's tree equals its parent's tree.
- `Reviewed-by` is free text naming the reviewer (for example provider, model
  and effort); the hook checks only that it is present once and not empty.
- Hand-finished release and hotfix merges keep Git's default merge message, so
  the commit-message check treats them like feature merges.
- Setting the repository's local Git hook path is the "one-time configuration"
  decision 8 refers to and the installation brief item D asks for; it is not a
  saved client configuration of Claude Code or Codex.
- The constitution amendment commit uses the type that fits the amendment (a
  new rule is `feat`); decision 7 then fixes the version.
- The marketplace-plugin proposal for decision 2 is reported to the user and
  changes nothing outside the repository without approval.
- Automatic versions for plugins and products are out of scope; the user has
  not decided them.
- `feature/005-backfire-mcp` is not touched.
- A new worktree's branch has "no commits of its own beyond its base" when its
  tip is already on another branch, such as the `develop` or `main` it was
  created from.
- The worktree name is the name of the worktree's folder, which is how Orca
  names it.
- Turning off Orca's `autoRenameBranchFromWork` setting, which can rename a
  branch after an agent's first work and undo git flow names, is proposed to
  the user and not applied without approval.
