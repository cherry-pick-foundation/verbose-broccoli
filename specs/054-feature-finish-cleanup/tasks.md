# Tasks: Post-merge Feature Cleanup

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Owner**: Feature orchestrator, supervised by develop. The coordinator owns
full verification, independent review, final task ticks, and feature finish.

## Implementation and checks

- [x] T001 Add the real git-flow finish regression, including repeated success
  and failed finish cases, in `scripts/git-flow-test.ts`.
- [x] T002 Add `scripts/git-flow-hooks/post-flow-feature-finish` and the three
  standard Spec Kit records.
- [ ] T003 Run focused tests and checks, inspect output and Git state, review the
  diff, and commit the scoped changes with this task trailer.
  - Owner: feature orchestrator. Full `npm run verify` requires the develop
    coordinator's serialized slot grant.
- [ ] T004 Obtain a fresh cross-provider review, resolve findings, run full
  verification, then finish into develop and update final task ticks.
  - Owner: develop coordinator. Not completed by the implementer.

## Handoff

The focused regression failed before the hook because successful finish output
had no cleanup prompt. Successful repeated finishes, a failed merge commit, and
a missing retained tip are now covered. Next, rerun the focused harness, check
shell lint and whitespace, rerun workflow with the same task, base and file
plan, inspect actual output and refs/worktrees, then complete T003.
The unrelated `.codex/config.toml` edit remains untouched. Durable worker state
is under `~/.local/state/verbose-broccoli/workspaces/feature-finish-cleanup/CHE-87/ctx_4a587a43107d/`.
