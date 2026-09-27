---

description: "Task list for the 2026-09-27 governance policies"
---

# Tasks: Governance Policies of 2026-09-27

**Input**: Design documents from `specs/006-governance-policies/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. The root `AGENTS.md` asks for tests with every code change,
and each user story names an independent test.

**Organization**: Tasks are grouped by user story. Main (Claude Code) owns
shared files (`deno.json`, `deno.lock`, `orca.yaml`), installs, Git operations,
integration and repository prose; Codex workers own the code tasks marked in
the Worker Assignment section.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Shared configuration every worker's checks run through.

- [x] T001 Update `deno.json`: add imports `@commitlint/cli` →
  `npm:@commitlint/cli@21.2.3`, `@commitlint/config-conventional` →
  `npm:@commitlint/config-conventional@21.2.3` and
  `conventional-changelog-conventionalcommits` →
  `npm:conventional-changelog-conventionalcommits@10.4.0`; add the task
  `commitlint` (runs `npm:@commitlint/cli@21.2.3 --config
  scripts/commitlint.config.mjs`, frozen, cached-only, no prompt, with the
  narrowest permissions that let it read the message and run `git`), the task
  `test:commit-msg` (runs `scripts/commit_msg_test.ts`) and the task
  `test:worktree-branch` (runs `scripts/worktree_branch_test.ts`), both added to
  the `test` dependencies; allow the `doctor` task to run `git`; add
  `scripts/constitution_version.ts` to `typecheck`.
- [x] T002 Run `deno install` to pin the new packages in `deno.lock`, then
  confirm `deno install --frozen --cached-only --no-prompt` and `deno task
  --quiet commitlint --help` succeed (depends on T001).
- [x] T003 [P] Update `orca.yaml`'s setup script: right after `cd
  "$project_root"`, run `sh scripts/worktree-branch.sh`; next to `git config
  gitflow.shared.trustHooks true`, run `git config core.hooksPath
  scripts/git-hooks`. Check with `deno fmt --check orca.yaml`.

**Checkpoint**: Tasks and packages exist; workers can run their suites.

---

## Phase 2: Foundational (Blocking Prerequisites)

None. The stories share only the Phase 1 configuration.

---

## Phase 3: User Story 1 - A feature reaches `develop` only after a recorded merge review (Priority: P1) 🎯 MVP

**Goal**: The feature-finish hook refuses the finish unless the tip is a
review-record commit whose parent is the reviewed commit.

**Independent Test**: `deno task test:git-flow`, which drives the real
git-flow-next binary in temporary repositories
([contracts/review-record.md](contracts/review-record.md)).

- [x] T004 [US1] Extend `scripts/git_flow_test.ts`: give the fixture a helper
  that adds a valid review-record commit (`git commit --allow-empty` with one
  `Reviewed-by` and one `Reviewed-commit: <parent id>` trailer) and use it in
  the existing verification-failure and success tests, so each still reaches
  the check it tests; the success test asserts that the merge's second parent
  is the review-record commit and the merge tree equals the reviewed tree. Add
  refusal tests, each comparing the existing `snapshot()` before and after and
  matching the refusal text: tip without a record; `Reviewed-commit` naming a
  commit other than the parent; a record that also changes a file; missing
  `Reviewed-by`; missing `Reviewed-commit`; duplicate `Reviewed-by`; empty
  `Reviewed-by` value; a merge of `develop` into the feature after a valid
  record. Also show that an abbreviated `Reviewed-commit` that resolves to the
  parent is accepted, and that lower-case trailer keys are accepted. The new
  tests fail before T005.
- [x] T005 [US1] Extend `scripts/git-flow-hooks/pre-flow-feature-finish`
  (POSIX `sh`, no new runtime) with checks 5 to 8 of
  [contracts/review-record.md](contracts/review-record.md), placed after the
  existing worktree checks and before `deno task --quiet verify`, each refusing
  through the existing `fail` function with the condition and the next step;
  keep every existing check and message unchanged. `deno task test:git-flow`
  passes (depends on T004).

**Checkpoint**: US1 works on its own.

---

## Phase 4: User Story 2 - Every commit message follows Conventional Commits, and constitution versions follow the commit type (Priority: P1)

**Goal**: A `commit-msg` hook installed through `core.hooksPath` runs
commitlint with one local rule for the constitution version, and the doctor
checks the installation.

**Independent Test**: `deno task test:commit-msg` and `deno task test:doctor`
([contracts/commit-message.md](contracts/commit-message.md)).

- [x] T006 [P] [US2] Create `scripts/constitution_version.ts`: a pure function
  that takes the parsed commit's type and whether it is breaking (any
  `BREAKING CHANGE` note) plus the constitution text before and after, and
  returns commitlint's `[valid, message]` per the rules table in
  [contracts/commit-message.md](contracts/commit-message.md); and the async
  rule for commitlint that reads `HEAD:.specify/memory/constitution.md` and
  `:.specify/memory/constitution.md` with `git show` (honouring
  `GIT_INDEX_FILE`), treats a missing `HEAD` or a missing file on either side as
  not applicable, and calls the pure function. Unit tests for the pure function
  go in `scripts/commit_msg_test.ts`: every row of the table, including version
  line missing or malformed, two version lines, a skipped step, a lowered
  version, `refactor` changing the version, `refactor!` raising the major, and
  a text change without a version change.
- [x] T007 [US2] Create `scripts/commitlint.config.mjs` (spreads
  `@commitlint/config-conventional`, passes the
  `conventional-changelog-conventionalcommits` parser options as
  `parserPreset: {parserOpts}` per [research.md](research.md#r1-commit-message-linter),
  registers the rule from `scripts/constitution_version.ts` as
  `local/constitution-version` at error level) and the executable POSIX hook
  `scripts/git-hooks/commit-msg` (finds Deno at `$HOME/.deno/bin/deno`, then on
  `PATH`, else refuses with `Commit refused: Deno 2.9.6 was not found.`; runs
  `deno task --quiet commitlint --edit "$1"`) (depends on T006).
- [x] T008 [US2] Add real-commit tests to `scripts/commit_msg_test.ts`: in
  temporary repositories that contain copies of `deno.json`, `deno.lock`,
  `scripts/commitlint.config.mjs`, `scripts/constitution_version.ts` and
  `scripts/git-hooks/commit-msg` and set `core.hooksPath` to
  `scripts/git-hooks`, show that `Update files` is refused and nothing is
  recorded; a valid header with each of `Spec-Kit-Task`, `Reviewed-by`,
  `Reviewed-commit`, `Co-Authored-By` and `Signed-off-by` is recorded; `git
  merge --no-ff` with Git's default message is recorded; constitution commits
  with `feat` (minor), `docs` and `fix` (patch) and `feat!` (major) bumps are
  recorded; a wrong step, a `chore` bump and an unchanged version with changed
  text are refused with the expected version in the output; `git commit -a`
  uses the temporary index; and the hook refuses clearly when Deno cannot be
  found. Keep Deno's cache reachable when the test changes `HOME` (set
  `DENO_DIR` explicitly). Measure one hook run and assert it takes under 2
  seconds (depends on T007).
- [x] T009 [P] [US2] Extend `scripts/doctor.ts` and `scripts/doctor_test.ts`:
  the doctor runs `git config --get core.hooksPath` in the repository root,
  fails with `Git hooks are not installed; run git config core.hooksPath
  scripts/git-hooks.` unless the value is exactly `scripts/git-hooks`, and
  records the checked value in its report; follow the existing option pattern
  used for `gitFlow` so tests can point the doctor at a fake `git`. Tests cover
  the pass, unset and different-value cases.

**Checkpoint**: US2 works on its own; T017 then activates it for this
repository.

---

## Phase 5: User Story 3 - Agents get the new review, model-choice and version rules from the right place (Priority: P2)

**Goal**: `deno task workflow`, `AGENTS.md` and the constitution state the
2026-09-27 rules that need judgment.

**Independent Test**: Read the three sources and run `deno task test:workflow`.

- [x] T010 [P] [US3] In `scripts/workflow.ts`, replace the REVIEW action text
  with guidance for decision 3: main coordinates implementation and resolves
  the listed review reasons; before each commit the implementer or the
  orchestrator reviews the diff (as clarified by the user); the independent review by a fresh reviewer from the other provider
  happens when the branch merges into `develop` (favoring speed) or `main`
  (favoring accuracy), not for each change; no extra user approval is needed.
  Add a test in `scripts/workflow_test.ts` that the REVIEW instructions mention
  the pre-commit review and the merge-time review and no longer ask for a separate
  diff review of each change; update any snapshot that changes.
- [x] T011 [P] [US3] Add to `AGENTS.md` exactly the three rules from the brief:
  under "Review", "Before each commit, the implementer or the orchestrator
  reviews the diff." (as clarified by the user) and "A review before merging into `develop` favors speed; one before
  merging into `main` favors accuracy."; under "Workflow and verification",
  "The main agent chooses each worker's and reviewer's model, reasoning effort
  and time budget from the code plugin's backfire judgments." Change nothing
  else.
- [x] T012 [US3] Amend `.specify/memory/constitution.md`: in Governance,
  replace "Increment draft minor versions for principle changes and patch
  versions for wording corrections." with decision 7 (the commit type of the
  commit that changes the constitution decides the bump, once per commit;
  breaking raises the first digit and needs the user's approval, `feat` the
  middle, `docs` or `fix` the last; the commit-message hook enforces it) and
  record the 2026-09-27 decisions; in "Development Workflow and Quality Gates",
  add the review before merge to the release and hotfix finishing procedure
  and the review record to the feature finish; update the Sync Impact Report;
  set the version by decision 7 for the commit type used (planned `feat`,
  0.22.0). Commit it after T017 so the hook checks it.

---

## Phase 6: User Story 5 - A new Orca worktree gets its git flow branch name without manual renaming (Priority: P2)

**Goal**: Orca's setup renames a just-created worktree's branch to its git
flow form.

**Independent Test**: `deno task test:worktree-branch`
([contracts/worktree-branch.md](contracts/worktree-branch.md)).

- [x] T013 [US5] Create `scripts/worktree_branch_test.ts`: in temporary
  repositories with `main` and `develop`, create worktrees the way Orca does
  (`git worktree add -b <name> <folder> <base>`) and run `sh
  scripts/worktree-branch.sh` inside them. Cover `release-1.0` →
  `release/1.0`, `hotfix-1.0` (from `main`) → `hotfix/1.0`,
  `governance-policies` and `feature-governance-policies` →
  `feature/governance-policies`; no rename when the branch has its own commit,
  has an upstream, already has a git flow name, or is `develop` or `main`, or
  HEAD is detached; exit 1 without changes when the target exists, when the
  name is `release-` alone, or when the target is not a valid branch name; a
  second run changes no ref; folders, other branches and other worktrees never
  change (compare `for-each-ref` and `worktree list --porcelain`). The tests
  fail before T014.
- [x] T014 [US5] Create `scripts/worktree-branch.sh` (POSIX `sh`, Git only) per
  [contracts/worktree-branch.md](contracts/worktree-branch.md), with a comment
  that it is temporary glue to remove once `orca worktree create` offers a
  branch option. `deno task test:worktree-branch` passes (depends on T013).

---

## Phase 7: User Story 4 - A reader at HEAD can learn the procedures from the documentation (Priority: P3)

**Goal**: The documentation describes what this feature delivers.

**Independent Test**: Read the sections; `deno task docs:check` passes.

- [x] T015 [US4] Update `docs/architecture.md`: in "Git flow — 2026-09-27",
  the review-record requirement, the review record's format and what stays
  manual (the merge review itself; the release and hotfix review); a new
  section for the commit-message check (commitlint and its pinned versions,
  the constitution rule, `core.hooksPath`, Orca's setup, the doctor check, the
  amend limit); the branch naming in Orca's setup and when to remove it; and
  the review timing where the workflow is described.
- [x] T022 [US4] Remove `conversations` from the Raw folders in
  `docs/examples/wiki/AGENTS.md`, so it admits only
  `raw/{web,files,notes,assets}/` like constitution principle VI (addendum H,
  item 1).
- [x] T016 [US4] Run `deno task docs:generate` and confirm `deno task
  docs:check` passes; commit `docs/reference/` (depends on T001, T015).

---

## Phase 8: Polish and Integration

- [x] T017 Set `git config core.hooksPath scripts/git-hooks` for the repository
  (shared by all worktrees; worktrees without `scripts/git-hooks/` run no hook)
  and confirm `deno task doctor` passes and a bad header is refused here
  (depends on T007, T009).
- [x] T018 Run the quickstart checks and `deno task verify` on the combined
  result; rerun `deno task workflow` with the same task and base; repair until
  both pass. For SC-006, add a scratch worktree of this repository named
  `feature-setup-probe` with `git worktree add -b feature-setup-probe`, run
  `orca.yaml`'s setup script in it, confirm its branch became
  `feature/setup-probe`, `core.hooksPath` is `scripts/git-hooks` and `deno
  task doctor` passes there, then remove the worktree and its branch.
  - 2026-09-27: verify passed (VERIFIED); the setup probe renamed
    `feature-setup-probe` to `feature/setup-probe` with doctor PASS; the hook
    took 0.13 s and refused a `docs` constitution bump to 0.22.0. Next: T019.
- [x] T019 Merge review for `develop`, favoring speed: a fresh Claude Code
  reviewer for the Codex-implemented code and a fresh Codex reviewer for the
  prose main wrote, each given only the scope and the requirements; resolve
  actionable findings and rerun affected checks.
  - 2026-09-27: code review (Claude `claude-sonnet-5`, high) found nothing;
    prose review (Codex `gpt-6-luna`, high) found one should-fix, resolved in
    `585c447`. Next: T020, finish from the `develop` worktree.
- [ ] T020 Add the review-record commit at the feature tip and finish with `git
  flow feature finish governance-policies` from the `develop` worktree (FR-020);
  confirm the merge's parents and tree.
- [ ] T021 Outside the repository, propose without applying which installed
  marketplace plugins connect apps Orca supports (Linear first) and could be
  removed. (The user turned off Orca's `autoRenameBranchFromWork` setting on
  2026-09-27, so no proposal is needed for it.)

---

## Dependencies & Execution Order

- T001 → T002. T003 is independent.
- US1 (T004 → T005), US2 (T006 → T007 → T008; T009 independent), US3 code
  (T010) and US5 (T013 → T014) need T001 and T002 and can run in parallel.
- T011 and T015 (main's prose) run while workers work. T012 is written then but
  committed after T017.
- T016 needs T001 and T015; T017 needs T007 and T009.
- T018 needs all implementation tasks; T019 needs T018; T020 needs T019.
- T021 is independent of the repository work.

## Worker Assignment

| Worker | Tasks | Writable files |
| --- | --- | --- |
| Codex A | T004, T005, T010 | `scripts/git_flow_test.ts`, `scripts/git-flow-hooks/pre-flow-feature-finish`, `scripts/workflow.ts`, `scripts/workflow_test.ts`, `scripts/__snapshots__/` if a snapshot changes |
| Codex B | T006 to T009 | `scripts/constitution_version.ts`, `scripts/commitlint.config.mjs`, `scripts/git-hooks/commit-msg`, `scripts/commit_msg_test.ts`, `scripts/doctor.ts`, `scripts/doctor_test.ts` |
| Codex C | T013, T014 | `scripts/worktree-branch.sh`, `scripts/worktree_branch_test.ts` |
| Main | T001 to T003, T011, T012, T015 to T021 | shared files, prose, Git |

## Parallel Example

```text
After T002: start Codex A, B and C together; main writes T011, T012 and T015.
```

## Implementation Strategy

1. Setup (T001 to T003).
2. Workers A, B and C in parallel; main writes the prose.
3. Integrate, activate the hook (T017), commit in logical groups with
   `Spec-Kit-Task` trailers, the constitution commit last.
4. Verify, merge review, review record, finish.
