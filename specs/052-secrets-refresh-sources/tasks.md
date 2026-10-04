# Tasks: Multi-source Secrets Refresh

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contract](contracts/operator-config.md).

All checkboxes remain unticked; develop owns final ticks. Implementer: Codex gpt-6.1-sol, medium effort, dispatch ctx_e5e054c599a1; selection supplied by coordinator (Jev probability 0.69, confidence 0.64). Initial estimate 45 minutes is advisory.

## Phase 1: Specification and design

- [ ] T001 Define stories, FR-001 through FR-012, outcomes and checklist in spec.md and checklists/requirements.md.
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: drafted and checked against dispatch; develop quality review remains.
- [ ] T002 Record research, reuse/owned-code estimate, model, contract and placeholder quickstart in plan.md, research.md, data-model.md, contracts/operator-config.md and quickstart.md (all FRs, especially FR-011/FR-012).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: design complete; no new dependency or live inventory.
- [ ] T003 Generate this tasks.md and analyze spec/plan/tasks consistency before implementation (all FRs/SCs).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: read-only consistency analysis covered 12 FRs and four SCs with no unmapped task, unresolved input or critical conflict; reported through Orca before script edits. Spec Kit helper writes outside the exact file scope were not run.

## Phase 2: User Story 1 - Sources and preflight

- [ ] T004 [US1] Extend scripts/secrets-refresh-test.ts fake bws for per-source responses, environments and early token refusal; implement scripts/secrets-refresh.ts configuration/token/fetch validation (FR-001 to FR-004, FR-010/FR-011; SC-001 to SC-003).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: schema validation, all-token preflight and all-source collection implemented and exercised offline; no live files read.

## Phase 3: User Stories 2 and 3 - Mappings and safe publication

- [ ] T005 [US2] Extend scripts/secrets-refresh.ts and scripts/secrets-refresh-test.ts for aliases, preserved bytes/line endings, duplicate variables and exact content (FR-005/FR-006; SC-001/SC-002).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: aliases, exact content, mapped positions/endings and unmapped bytes covered, including a bare non-assignment line. Depends on T004.
- [ ] T006 [US3] Extend the same script/tests for fixed target kinds, lexical/canonical/inode aliases, parent checks and all-temp-before-rename publication (FR-007 to FR-010; SC-001 to SC-003).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: path/kind/alias safeguards and prepare-before-rename behavior covered; preparation failure preserves originals. Depends on T004/T005.

## Phase 4: Documentation and worker checks

- [ ] T007 Update docs/backfire.md and docs/architecture.md secrets sections and append a dated command-use note to specs/041-provider-secrets/security/bws-2.1.0.md (FR-011/FR-012).
  - Owner: Codex gpt-6.1-sol, medium.
- [ ] T008 Run offline test:secrets-refresh, narrow lint/type checks and workflow; review diff and make authorized local Conventional Commit with task/attribution trailers (SC-004).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: 63/63 offline cases, ESLint, TypeScript, workflow/policy and diff-whitespace checks passed; synthetic multi-source regression fails against HEAD baseline as expected. Full verify and independent review remain held for coordinator. Logs: ~/.local/state/verbose-broccoli/workspaces/feature-secrets-refresh-sources/secrets-refresh-sources/attempts/ctx_e5e054c599a1/. Depends on T004-T007.

## Phase 5: Coordinator acceptance

- [ ] T009 Run serialized full npm run verify and documentation judgments; obtain fresh independent other-provider review, resolve findings and record acceptance (SC-004).
  - Owner: Coordinator/develop; not implementer approval.
- [ ] T010 Finish into develop, update final ticks and relay operator-file replacement to main.
  - Owner: Develop. Live setup, refresh, push and merge are outside the worker scope.

## Dependencies and strategy

T001 -> T002 -> T003 -> T004 -> T005 -> T006 -> T007 -> T008 -> T009 -> T010. No further workers or parallel file ownership. Source collection is the first useful slice; mapping and path safeguards are required before operational use.
