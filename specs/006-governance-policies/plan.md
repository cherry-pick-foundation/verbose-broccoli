# Implementation Plan: Governance Policies of 2026-09-27

**Branch**: `feature/governance-policies` | **Date**: 2026-09-27 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/006-governance-policies/spec.md`

## Summary

Turn the user's 2026-09-27 governance decisions into mechanisms where they can
be enforced and into short rules where they need judgment:

- The git-flow feature-finish hook requires a review-record commit at the
  feature tip whose parent is the reviewed commit (decision 4).
- A `commit-msg` hook runs commitlint with the Conventional Commits preset and
  one local plugin rule that ties constitution version bumps to the commit type
  (decision 7). Orca's setup installs it through `core.hooksPath`, and `deno
  task doctor` checks that setting.
- Orca's setup renames a new worktree's branch to its git flow form from the
  worktree name (addendum item G).
- `deno task workflow` REVIEW guidance, three `AGENTS.md` rules, the
  constitution amendment and `docs/architecture.md` state the review timing,
  model choice and version rules (decisions 3, 5, 6, 7 and 8).

## Technical Context

**Language/Version**: POSIX shell for Git and git-flow hooks and the setup
step; TypeScript on Deno 2.9.6 for the commitlint rule and tests; an `.mjs`
commitlint config (research R1).

**Primary Dependencies**: Git 2.53.0; git-flow-next 2.1.0 (unchanged);
`@commitlint/cli` 21.2.3, `@commitlint/config-conventional` 21.2.3 and
`conventional-changelog-conventionalcommits` 10.4.0 from npm, pinned in
`deno.json` and `deno.lock`; Orca 1.4.215's `orca.yaml` setup script.

**Storage**: None. Git objects, refs and the repository's local Git config
only.

**Testing**: `deno test` suites that drive real Git (and the real git-flow
binary) in temporary repositories, as `scripts/git_flow_test.ts` does; unit
tests for the version rule; the existing workflow and doctor suites.

**Target Platform**: The development machine (Linux) inside Orca worktrees.

**Project Type**: Repository automation under `scripts/`.

**Performance Goals**: The commit hook adds at most 2 seconds per commit
(commitlint alone measured about 0.15 seconds, R1).

**Constraints**: Refusals change no branch, worktree, index or file; hooks are
never bypassed; git-flow-next's source stays unchanged; locally written code is
limited to the version rule and hook glue (root `AGENTS.md` reuse order).

**Scale/Scope**: Four scripts or hooks, one commitlint config, three test
files, edits to `deno.json`, `orca.yaml`, `scripts/doctor.ts`,
`scripts/workflow.ts`, `AGENTS.md`, the constitution and
`docs/architecture.md`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Status |
| --- | --- |
| I. Proven dependencies | PASS. commitlint's packages are pure JavaScript; versions are pinned and the probe ran on the selected Deno (R1). The new host requirement is only the existing Git. |
| II. Working capabilities | PASS. Each behavior is tested through real Git, git-flow and hook invocations, not by inspecting files. |
| V. Observable acceptance | PASS. Tests cover positive, negative and boundary cases and compare refs and worktrees before and after refusals. The amend limit (R3) is recorded, not hidden. |
| VII. Minimum implementation, reuse order | PASS. Upstream commitlint owns parsing and header rules; Git owns trailer parsing and ref checks. Local code is one plugin rule, two hook scripts and one setup script. |
| VIII. No new exceptions | PASS. No rule exception is claimed. |
| IX. Layout | PASS. All automation stays under `scripts/`; no package or plugin changes. |
| Workflow: git flow, hooks, commits | PASS. The finish stays `git flow feature finish` from `develop`; the review step for releases and hotfixes is manual, as decision 5 requires. |
| Governance: version | The amendment commit's type decides the bump under the new rule (decision 7); planned as `feat` from 0.21.0 to 0.22.0. |

Re-check after design: unchanged; no violations.

## Project Structure

### Documentation (this feature)

```text
specs/006-governance-policies/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── review-record.md
│   ├── commit-message.md
│   └── worktree-branch.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
AGENTS.md                                  # three rules (main)
.specify/memory/constitution.md            # amendment (main)
docs/architecture.md                       # procedures (main)
docs/reference/commands.md                 # regenerated (main)
deno.json, deno.lock                       # imports and tasks (main)
orca.yaml                                  # setup: branch name, hooksPath (main)
scripts/
├── git-flow-hooks/pre-flow-feature-finish # review-record checks
├── git_flow_test.ts                       # finish tests
├── git-hooks/commit-msg                   # new: runs commitlint
├── commitlint.config.mjs                  # new: preset + plugin rule wiring
├── constitution_version.ts                # new: version rule
├── commit_msg_test.ts                     # new: rule unit tests + real commits
├── worktree-branch.sh                     # new: branch rename for setup
├── worktree_branch_test.ts                # new: rename tests (test:worktree-branch)
├── doctor.ts, doctor_test.ts              # core.hooksPath check
└── workflow.ts, workflow_test.ts          # REVIEW guidance
```

**Structure Decision**: Everything is repository automation, so it stays in
`scripts/` (constitution IX). Hooks without a runtime extension follow the
existing `scripts/git-flow-hooks/` style. The branch-naming script is named
with `.sh` because Orca's setup calls it as a script, not as a hook.

## Work Split and Ownership

Main (Claude Code) owns shared files, installs, Git operations, integration
and repository prose; Codex workers implement code in disjoint files through
Orca orchestration, per `.claude/rules/claude-code.md`.

1. **Main, first**: `deno.json` (imports; the `commitlint`,
   `test:commit-msg` and `test:worktree-branch` tasks, both tests added to
   `test`; `doctor` allowed to run `git`; `typecheck` including
   `scripts/constitution_version.ts`), `deno install` to update `deno.lock`, and
   `orca.yaml`.
2. **Workers in parallel**, each with exact files:
   - finish hook and its tests (US1);
   - commit-message check, doctor check and their tests (US2);
   - branch-naming script and its tests (US5);
   - workflow REVIEW text and its tests (US3, code part).
3. **Main, in parallel with workers**: `AGENTS.md`, constitution amendment and
   `docs/architecture.md` (US3, US4).
4. **Main, last**: set `core.hooksPath` for the repository, commit in logical
   groups (the constitution commit last, so the new hook checks its bump),
   `deno task docs:generate`, `deno task verify`.

Model, reasoning effort and time budget for each worker come from the local
advisor's judgments (R6), chosen per worker when it is started.

## Review and Finish

- Each implementer re-reviews its own diff before each commit; main reviews
  Codex workers' changes before integrating them.
- Merge review for `develop` (favoring speed), by fresh reviewers from the
  other provider who get only the scope and requirements: a Claude Code
  reviewer for the Codex-implemented code, and a Codex reviewer for the
  prose main wrote.
- After findings are resolved and verification passes, add the review-record
  commit (`git commit --allow-empty`, with `Reviewed-by` and
  `Reviewed-commit`), then finish with `git flow feature finish
  governance-policies` from the `develop` worktree. `develop`'s hook predates
  this feature and does not yet require the record (FR-020).

## Complexity Tracking

No constitution violations to justify.
