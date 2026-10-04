# Tasks: Multi-source Secrets Refresh

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contract](contracts/operator-config.md).

Develop completed the repository task checks on 2026-10-04. Implementer: Codex gpt-6.1-sol, medium effort, dispatch ctx_e5e054c599a1; selection supplied by coordinator (Jev probability 0.69, confidence 0.64). Initial estimate 45 minutes was advisory. Live operator setup and the first refresh remain with main.

## Phase 1: Specification and design

- [x] T001 Define stories, FR-001 through FR-012, outcomes and checklist in spec.md and checklists/requirements.md.
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: drafted against the dispatch; the independent review inspected the complete records, and develop completed the quality checklist.
- [x] T002 Record research, reuse/owned-code estimate, model, contract and placeholder quickstart in plan.md, research.md, data-model.md, contracts/operator-config.md and quickstart.md (all FRs, especially FR-011/FR-012).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: design complete; no new dependency or live inventory.
- [x] T003 Generate this tasks.md and analyze spec/plan/tasks consistency before implementation (all FRs/SCs).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: read-only consistency analysis covered 12 FRs and four SCs with no unmapped task, unresolved input or critical conflict; reported through Orca before script edits. Spec Kit helper writes outside the exact file scope were not run.

## Phase 2: User Story 1 - Sources and preflight

- [x] T004 [US1] Extend scripts/secrets-refresh-test.ts fake bws for per-source responses, environments and early token refusal; implement scripts/secrets-refresh.ts configuration/token/fetch validation (FR-001 to FR-004, FR-010/FR-011; SC-001 to SC-003).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: schema validation, all-token preflight and all-source collection implemented and exercised offline; no live files read.

## Phase 3: User Stories 2 and 3 - Mappings and safe publication

- [x] T005 [US2] Extend scripts/secrets-refresh.ts and scripts/secrets-refresh-test.ts for aliases, preserved bytes/line endings, duplicate variables and exact content (FR-005/FR-006; SC-001/SC-002).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: aliases, exact content, mapped positions/endings and unmapped bytes covered, including a bare non-assignment line. Depends on T004.
- [x] T006 [US3] Extend the same script/tests for fixed target kinds, lexical/canonical/inode aliases, parent checks and all-temp-before-rename publication (FR-007 to FR-010; SC-001 to SC-003).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: path/kind/alias safeguards and prepare-before-rename behavior covered; preparation failure preserves originals. Depends on T004/T005.

## Phase 4: Documentation and worker checks

- [x] T007 Update docs/backfire.md and docs/architecture.md secrets sections and append a dated command-use note to specs/041-provider-secrets/security/bws-2.1.0.md (FR-011/FR-012).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: required sections and the dated note were committed and independently reviewed; historical security evidence was preserved.
- [x] T008 Run offline test:secrets-refresh, narrow lint/type checks and workflow; review diff and make authorized local Conventional Commit with task/attribution trailers (SC-004).
  - Owner: Codex gpt-6.1-sol, medium. 2026-10-04: 63/63 offline cases, ESLint, TypeScript, workflow/policy and diff-whitespace checks passed; synthetic multi-source regression fails against the pre-change baseline as expected. Commit e310990d648684f3bd926b60f05df1f8357e37ee; coordinator acceptance is recorded under T009. Logs: ~/.local/state/verbose-broccoli/workspaces/feature-secrets-refresh-sources/secrets-refresh-sources/attempts/ctx_e5e054c599a1/. Depends on T004-T007.

## Phase 5: Coordinator acceptance

- [x] T009 Run serialized full npm run verify and documentation judgments; obtain fresh independent other-provider review, resolve findings and record acceptance (SC-004).
  - 2026-10-04: Antigravity Gemini 3.8 Flash Medium reviewed exact e310990, found no actionable defects, and independently passed 63 offline cases, lint and typecheck. Full verification summary 3KDg1hWTcNKFId3lmXe4fl2ZvRO and finish-hook summary 3KDjJhIp1fZgnvQzBb4J1SRo7Ob each record 47 task exits zero (42 executed, five cached). Four changed documentation paragraphs were verified; unchanged and report-only findings have explicit dispositions, without a whole-corpus verification claim.
  - Jev's completion gate remains recorded as escalated (safe_to_apply 0.27, composite 0.6495). Main accepted repository completion after inspecting the exact before/after run receipts, unchanged hashes and independent review; the successful call was not repeated. Durable review, judgment and run evidence is under $XDG_STATE_HOME/verbose-broccoli/workspaces/feature-secrets-refresh-sources/secrets-refresh-sources/ (default ~/.local/state/).
- [x] T010 Finish into develop, update final ticks and relay operator-file replacement to main.
  - 2026-10-04: git-flow finished locally at c51e1b69625a106a71033ed74ae60cc6afd3c443, preserving the feature branch/worktree. Review record cff7bca2fd25252095d355d94bc06fc02ae5daf0 has the reviewed source's identical tree; generated Codex configuration was restored only through its ownership receipt. The feature card is completed and main received the operator-file handoff. No push or live setup/refresh was performed; those remain outside the worker scope.

## Dependencies and strategy

T001 -> T002 -> T003 -> T004 -> T005 -> T006 -> T007 -> T008 -> T009 -> T010. No further workers or parallel file ownership. Source collection is the first useful slice; mapping and path safeguards are required before operational use.
