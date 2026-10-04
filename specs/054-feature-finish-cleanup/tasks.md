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

The feature worker completed implementation, focused checks, diff review and
commit `9468ac6` on 2026-10-05. The git-flow suite passed 20/20; ShellCheck,
Prettier and whitespace checks passed. Workflow ran against the fixed base and
declared files; it also reported the preserved generated `.codex/config.toml`
edit outside that exact scope. The coordinator owns the serialized full verify,
fresh cross-provider review, finish, and final task ticks. The worker cannot
prove its turn-context model/effort from this terminal; the dispatch choice was
Codex gpt-6-luna/medium. Durable evidence is under
`~/.local/state/verbose-broccoli/workspaces/feature-finish-cleanup/CHE-87/ctx_4a587a43107d/`.
