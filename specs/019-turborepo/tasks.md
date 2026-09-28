---

description: "Task list for the Turborepo trial"
---

# Tasks: Turborepo trial

**Input**: Design documents from `specs/019-turborepo/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [evidence/selected-sites.md](evidence/selected-sites.md)

**Tests**: The existing suites are the tests: they move to Node.js and
`node:test` (TypeScript) or run through the root uv workspace (Python), and
`test_load`, `test_ready`, `test_entry` and the doctor tests guard the
built plugins and environments. No new test files.

**Organization**: Codex implementers (`gpt-6-luna` at `max`) own T001 to
T005; main (Claude Code) owns T006 and T007, the records and the report.
Every task changes only the sites that
[evidence/selected-sites.md](evidence/selected-sites.md) marks SELECT.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Foundations (US1, US2, US3)

- [ ] T001 [P] [US1] Node.js and Turborepo foundation: root `package.json`,
  `package-lock.json`, `.npmrc`, `turbo.json`, `tsconfig.json` and the
  preload `scripts/deno_shim.ts`; the selected `deno.json`, `deno.lock` and
  `.gitignore` sites; the non-erasable construct in
  `plugins/code/skills/clean-code/scripts/cli.ts` (D1 to D5, D8, D9).
- [ ] T002 [P] [US3] One uv workspace: root `pyproject.toml`,
  `.python-version` and `uv.lock`; `uv_build` for the three packages; the
  selected sites in `packages/*`, `ready.py`, `build.py` and their tests; the
  selected line of the work plugin's `wiki-consistency` skill (D6, D7, D10).

## Phase 2: Scripts and tests on Node.js (US1, US2)

- [ ] T003 [US2] After T001: the non-test scripts, hooks, `orca.yaml`, the
  GitHub workflows, the evidence schema and the regenerated
  `docs/reference/*.md`.
- [ ] T004 [P] [US2] After T001: `scripts/clean_architecture_test.ts`,
  `cli_contract_test.ts`, `commit_msg_test.ts`, `docs_test.ts`,
  `doctor_test.ts`, `git_flow_test.ts` and `plugin_skills_test.ts` on
  `node:test` and `node:child_process`, at their selected sites.
- [ ] T005 [P] [US2] After T001: `scripts/wiki_raw_import_test.ts`,
  `workflow_graph_test.ts`, `workflow_plan_test.ts`,
  `workflow_skills_test.ts`, `workflow_test.ts`, `workflow_verify_test.ts`
  and `worktree_branch_test.ts`, likewise.

## Phase 3: Documents, verification and report (US4)

- [ ] T006 [US4] Main: the selected prose sites in `docs/architecture.md`
  (S137) and `docs/backfire.md` (S139).
- [ ] T007 [US4] Main: `npm run check` and the separate `test_load`,
  `test_ready`, `test_entry` and doctor runs; check time on the base commit
  and the branch; `backfire_review` of each patch, `backfire_gate` on the
  final diff with the real check output, `backfire_verify` on the report's
  claims; [report.md](report.md) and the report to the develop session.

## Dependencies

T001 and T002 start together. T003, T004 and T005 start after T001. T006
follows T003 (it describes the final commands). T007 comes last.
