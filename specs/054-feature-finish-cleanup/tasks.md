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

The feature orchestrator updated the hook after review: it withholds the Orca
removal command unless the source worktree exists and is clean, quotes the
selector with Git, and names `orca-ide`. Regression coverage now includes dirty,
missing, unreadable and absent worktrees, quoted paths, and missing or failed
finish status. Focused checks pass 22/22; ShellCheck, Prettier and whitespace
checks pass. Workflow remains in review mode because `.codex/config.toml` is
preserved outside the declared scope. Next, the develop coordinator runs full
verification on the frozen commit after the serialized slot is granted, obtains
fresh independent review, and owns feature finish and final task ticks. T003
remains unchecked for the coordinator's final ledger update. Current retry state is under
`~/.local/state/verbose-broccoli/workspaces/feature-finish-cleanup/CHE-87/ctx_06b1cefdf48e/`.
