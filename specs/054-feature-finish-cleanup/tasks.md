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

The focused git-flow suite passes 25/25 on develop `22996c2`. Document checks
record 11 successful verification requests (333 claims; no contradictions),
34 target-document review flags for unchanged or weakly evidenced claims, 19
report-only review flags, and 21 MemoryLint warnings. The changed git-flow
architecture statement was checked against both hook files. Receipts are under
`~/.local/state/verbose-broccoli/workspaces/feature-finish-cleanup/task_ac135e0aee30/ctx_ae01c79acc0f/attempt-16/`.
Full verification, final task ticks, the review record, and feature finish
remain with the develop coordinator.
