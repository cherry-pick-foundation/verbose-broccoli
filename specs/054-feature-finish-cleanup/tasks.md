# Tasks: Post-merge Feature Cleanup

**Input**: [spec.md](spec.md), [plan.md](plan.md).

**Owner**: Feature orchestrator, supervised by develop. The coordinator owns
full verification, independent review, final task ticks, and feature finish.

## Implementation and checks

- [x] T001 Add the real git-flow finish regression, including repeated success
      and failed finish cases, in `scripts/git-flow-test.ts`.
- [x] T002 Add `scripts/git-flow-hooks/post-flow-feature-finish` and the three
      standard Spec Kit records.
- [x] T003 Run focused tests and checks, inspect output and Git state, review the
      diff, and commit the scoped changes with this task trailer.
  - Owner: feature orchestrator. Full `npm run verify` requires the develop
    coordinator's serialized slot grant.
- [x] T004 Obtain a fresh cross-provider review, resolve findings, run full
      verification, then finish into develop and update final task ticks.
  - Owner: develop coordinator. Not completed by the implementer.

## Handoff

The focused git-flow suite passes 25/25 on develop `22996c2`. Document checks
record 11 successful verification requests (333 claims; no contradictions),
34 target-document review flags for unchanged or weakly evidenced claims, 19
report-only review flags, and 21 MemoryLint warnings. The changed git-flow
architecture statement was checked against both hook files. Receipts are under
`~/.local/state/verbose-broccoli/workspaces/feature-finish-cleanup/task_ac135e0aee30/ctx_ae01c79acc0f/attempt-16/`.
The fresh reviewer choice is Claude Code `claude-sonnet-5-5` at medium effort
(Jev probability 0.42, confidence 0.34), from the user's own Claude account.
2026-10-05: Finished into develop as `c5bde2a`, with independent review record
`3208a64` of `59cb5d9`. Source, guarded finish and merged develop each passed
46/46 verification tasks (41 executed, 5 cached), including 25/25 Git-flow
cases. Root receipts are in XDG state at
`verbose-broccoli/workspaces/develop/finish-cleanup-verify/attempt-20261005t094149z/`.
No implementation work remains; source branch `3208a64` is retained.
