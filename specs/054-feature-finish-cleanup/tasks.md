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

The original focused run passed 22/22, plus ShellCheck, Prettier, and whitespace
checks. Its receipt remains under
`~/.local/state/verbose-broccoli/workspaces/feature-finish-cleanup/CHE-87/ctx_06b1cefdf48e/attempt-05/`.
The feature branch now includes develop at `00ae841`. The develop coordinator
owns full verification, final task ticks, the review record, and feature finish.
