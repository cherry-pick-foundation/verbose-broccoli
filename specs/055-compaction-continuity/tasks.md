# Tasks: Coordinator compaction continuity

Feature: CHE-88, spec055. Develop owns final task ticks. Unchecked boxes describe ownership gates, not proof that implementation is absent; progress notes record the current evidence.

## Phase 1: Setup and design

- [ ] T001 Check both installed clients' hook capability and write spec/plan/research/data-model/quickstart plus checklist under specs/055-compaction-continuity/.
  2026-10-05: Approved brief and all standing notes read fully; hook input/output and Codex context limit checked against official docs and version-matched source. Develop approved explicit session ownership in state. Native Codex gpt-6.1-sol/medium was selected through Jev typesafe/jev-1.13 (probability 0.68, confidence 0.63); receipts are in develop/compaction-continuity/attempt-20261005T0225Z under approved state storage. The 60-minute advisory checkpoint is not a stopping deadline.

## Phase 2: Foundation

- [ ] T002 Define central notes/state paths and thresholds in .config/coordinator-context.json and read-only hook input handling in scripts/coordinator-context.ts.

## Phase 3: User story 1 — restore context

- [ ] T003 [US1] Add full context/fallback and explicit coordinator ownership in scripts/coordinator-context.ts; test both clients, full content, source events, missing sources and unchanged files in scripts/coordinator-context-test.ts.
- [ ] T004 [US1] Register the hook in .codex/hooks.json and .claude/settings.json, preserving Ponytail; test native command definitions in scripts/coordinator-context-test.ts.

## Phase 4: User story 2 — compaction thresholds

- [ ] T005 [US2] Count owned-session compactions and issue threshold context plus desktop notification in scripts/coordinator-context.ts; test role thresholds, replacement/session separation, damaged transcripts and notification failure in scripts/coordinator-context-test.ts.

## Phase 5: User story 3 — useful coordination

- [ ] T006 [US3] Add the short main/develop message rule to AGENTS.md and verify no project memories override is introduced.

## Phase 6: Acceptance and integration

- [ ] T007 Register runnable checks in package.json/turbo.json and regenerate only the command table in docs/reference/commands.md; run narrow checks and full same-run verification.
- [ ] T008 Commit the feature records in specs/055-compaction-continuity/, run document prepare/audit, measure owned size and request independent native Claude /code-review plus Linear In Review through develop.
- [ ] T009 Align current develop, resolve review findings, renew verification/review as needed and create the content-free review-record tip; request develop's git flow finish.

2026-10-05 checkpoint: T002–T006 implementation is present; T007 narrow tests (2/2), scoped ESLint and TypeScript passed. Full verification, final document judgments and independent review remain unrun. Develop holds new work until CHE-86 privacy merges; next merge updated develop, rerun workflow and continue acceptance. Reviewer choice: Claude Code claude-sonnet-5-5 medium, Jev probability 0.88/confidence 0.85; no reviewer started.

## Dependencies and execution

T001 precedes T002; T002 precedes T003/T005. T004 consumes the hook; T006 is independent prose. T007 follows all implementation; T008 follows verification; T009 follows independent acceptance and current develop alignment. One coordinator implements this small change under workflow REVIEW. No implementation fan-out is needed. The independent reviewer has read-only ownership and receives neutral requirements.

## Continuity and evidence

The one mutable coordinator file is ~/.local/state/verbose-broccoli/workspaces/feature-compaction-continuity/session-state.md. Immutable attempt outputs are under ~/.local/state/verbose-broccoli/workspaces/feature-compaction-continuity/compaction-continuity/ctx_14adf1f5da09/. The exact-file workflow plan there adds only required Spec Kit design/checklist artifacts and the adopted agent-context generated file to develop's initial plan. The pre-existing generated .codex/config.toml change stays outside feature ownership.

2026-10-05 acceptance: Updated develop f868ec0 merged at 89c2dee through the authorized generated-table resolution. T007 full verification passed 46/46 in the same run after locked dependency setup; T008 current document judgments/disposition and measured size are recorded in plan.md. Next: independent native Claude built-in review, any affected fixes/checks, review-record tip and merge_ready to develop; final ticks remain develop-owned.

2026-10-05 follow-up: T003/T005 now include a leading spill/truncation full-read instruction and keep counts across repeated matching Codex metadata. Both regressions failed before their fixes and pass afterward; unclaimed/narrow-worker state remains outside coordinator threshold ownership. Next: verify this implementation and renew independent review with only current scope and requirements.

2026-10-05 follow-up verification: T007 passed again with all 46 tasks and the same run summary after the metadata/spill regression changes. The successful review-fix-04 verification and red/green regression receipts are immutable; next independent review uses the new committed snapshot.
