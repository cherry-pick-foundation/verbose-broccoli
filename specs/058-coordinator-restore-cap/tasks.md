# Tasks

- [ ] T001 Select and validate client-specific restore bounds.
- [ ] T002 Verify synthetic red-green restoration, boundaries, UTF-8 sizing and existing isolation behavior.
- [ ] T003 Run full verification on the current integration base and obtain independent other-provider review.
- [ ] T004 Commit and integrate through normal workflow; record final verification and ledger ticks.

2026-10-06: T001/T002 implementation and focused checks delivered uncommitted; develop owns final ticks. T003/T004 remain open: full verification slot, independent review and integration are not yet granted. Evidence is retained at ~/.local/state/verbose-broccoli/workspaces/feature-coordinator-restore-cap/coordinator-restore-cap/ctx_fcaad18aacf8/.

2026-10-06: develop accepted the scoped implementation and ran full verification on frozen index tree 9a480068388593ed1499a8bbb545ffa78ebbde23 at base 568c97d. Turbo 3KHes1S9K9OdBRv2TNQucpoX9kq reports 46 successful tasks (41 executed, 5 cached), zero failures and every task exit 0. Independent review and integration remain open; source/config/tests are unchanged after that run. Root evidence: ~/.local/state/verbose-broccoli/workspaces/develop/coordinator-restore-cap/attempt-20261005t162640z/.
