# Tasks: Wiki container naming

**Input**: [plan.md](plan.md), [spec.md](spec.md), [paths contract](contracts/paths.md).
Root owns final task ticks after integration; unchecked boxes do not erase evidence.

## Phase 1: Setup

- [ ] T001 Record approved scope and plan in specs/057-wiki-container-naming/spec.md and plan.md.
  2026-10-05: coordinator Codex gpt-6.1-sol/medium, selected by root's retained Jev choices (agent .53/.41, group .74/.68, model .79/.76, effort .55/.47). Child Run run_bc97b0bfd11f; parent task_3ba8c261ed23/ctx_0944eec65615. Setup receipt inspected: unchanged setup and all 16 doctor checks passed.

## Phase 2: Foundation

- [ ] T002 Trace builders/callers and run exact-file workflow; record evidence in specs/057-wiki-container-naming/research.md.

## Phase 3: User Story 1 - Supported paths (P1)

Independent test: all four names run below llm-wiki without the former link.

- [ ] T003 [US1] Update synthetic paths and four-name regression cases in packages/wiki-consistency/tests/test_instance.py, test_main.py, conftest.py, scripts/wiki-raw-import-test.ts and plugins/work/skills/wiki-raw-import/scripts/session_select_test.py.
- [ ] T004 [US1] Update builders and stage guard in packages/wiki-consistency/src/wiki_consistency/instance.py and plugins/work/skills/wiki-raw-import/scripts/raw_import.py, session_select.py; run focused checks.

## Phase 4: User Story 2 - Terminology and readiness (P2)

Independent test: current instructions use the chosen names and readiness lists remaining consumers.

- [ ] T005 [US2] Update synthetic terminology in packages/wiki-consistency/tests/test_text.py and plugins/work/skills/grammatical-competence/scripts/grammatical_competence_test.py, and Wiki-domain prose in AGENTS.md, plugins/work/AGENTS.md, docs/architecture.md, docs/examples/wiki/AGENTS.md, plugins/work/skills/wiki-raw-import/{SKILL.md,assets/AGENTS.md,references/session-selection.md,references/session-catalog.json}, plugins/work/skills/wiki-consistency/SKILL.md, plugins/work/skills/grammatical-competence/{SKILL.md,references/procedure.md}, plugins/code/skills/model-choice/references/model-choice.md and current .specify/memory/constitution.md with its normal pyproject.toml fix/PATCH version bump.
- [ ] T006 [US2] Inspect active/installed consumer metadata without protected content and record readiness in specs/057-wiki-container-naming/record.md.

## Phase 5: Verification and integration

  2026-10-05: three runtime literals changed; old code failed 17 path, four staging and four check-CLI cases, plus all four import-CLI cases. Pinned-mise affected suites passed 646 tests; raw-import passed 49 tests. Current wording and synthetic helper names updated; no data or private source touched.

- [ ] T007 Run affected checks, document judgments/audit and root-granted full verification; retain evidence referenced by specs/057-wiki-container-naming/record.md.
  2026-10-05: document check passed. Two gated verify calls covered 24 changed units (16 verified, eight unsupported, no contradicted); unchanged broad units were not repeated. One classification call left the path paragraph agent-written; MemoryLint reported 21 constitution placement warnings, retained/report-only.

- [ ] T008 Obtain fresh other-provider final assessment and record reviewer evidence in specs/057-wiki-container-naming/tasks.md; create content-free review-record tip after committing record.md.
  2026-10-05: fresh Jev chose Claude Code claude-sonnet-5-5/medium (.68 probability, .59 confidence), no escape or contradiction. Native full-ID support and current usage retained in attempt evidence; independent review still required.

- [ ] T009 Root finishes into develop, verifies and ticks only specs/057-wiki-container-naming/tasks.md.

## Dependencies and execution order

T001 → T002 → T003 → T004; T005/T006 follow the trace and can be separate disjoint
work, but coordinator handles this small scope locally. T007 follows both stories,
then T008 and root's T009. Synthetic regression precedes builder edits.

## Implementation strategy

Use existing builders, preserve all behavior besides the selected container,
then current prose and read-only readiness. No new runtime implementation.
Authoritative evidence and paid results:
`~/.local/state/verbose-broccoli/workspaces/feature-wiki-container-naming/che-90/ctx_0944eec65615/`.
