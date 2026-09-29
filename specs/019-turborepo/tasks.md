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

- [x] T001 [P] [US1] Node.js and Turborepo foundation: root `package.json`,
  `package-lock.json`, `.npmrc`, `turbo.json`, `tsconfig.json` and the
  preload `scripts/deno_shim.ts`; the selected `deno.json`, `deno.lock` and
  `.gitignore` sites; the non-erasable construct in
  `plugins/code/skills/clean-code/scripts/cli.ts` (D1 to D5, D8, D9).
  - 2026-09-29: Codex (`gpt-6-luna`, max; Orca `ctx_5f605f713fcd`, follow-up
    `ctx_d5f18292255a` for the npm `workspaces` glob, D13). Main added
    `agentGuidance: false`, the uv `--directory ../..` member commands and
    three script scopes during integration; a fresh Codex review (R1) found
    no issue in them.
- [x] T002 [P] [US3] One uv workspace: root `pyproject.toml`,
  `.python-version` and `uv.lock`; `uv_build` for the three packages; the
  selected sites in `packages/*`, `ready.py`, `build.py` and their tests; the
  selected line of the work plugin's `wiki-consistency` skill (D6, D7, D10).
  - 2026-09-29: Codex (`ctx_2942d13d0eac`, follow-up `ctx_d0d092470e4c` for
    the virtual root). Three sites T002 raised with failing output were
    classified must-change (batches 6 to 8); root lock versions equal the
    old locks.

## Phase 2: Scripts and tests on Node.js (US1, US2)

- [x] T003 [US2] After T001: the non-test scripts, hooks, `orca.yaml`, the
  GitHub workflows, the evidence schema and the regenerated
  `docs/reference/*.md`.
  - 2026-09-29: Codex (`ctx_172d358fb14b`, follow-ups `ctx_eb72e175dee5` and
    `ctx_4856af3ef36d`). Added the hex (D14) and lock (D12) sites.
- [x] T004 [P] [US2] After T001: `scripts/clean_architecture_test.ts`,
  `cli_contract_test.ts`, `commit_msg_test.ts`, `docs_test.ts`,
  `doctor_test.ts`, `git_flow_test.ts` and `plugin_skills_test.ts` on
  `node:test` and `node:child_process`, at their selected sites.
  - 2026-09-29: Codex (`ctx_74fac3e2d664`, follow-ups `ctx_f0c2a398ecae` and
    `ctx_bd553bb7f891`). Snapshots moved to node:test (D15); seven test
    sites were classified from failing output (batches 11 to 16).
- [x] T005 [P] [US2] After T001: `scripts/wiki_raw_import_test.ts`,
  `workflow_graph_test.ts`, `workflow_plan_test.ts`,
  `workflow_skills_test.ts`, `workflow_test.ts`, `workflow_verify_test.ts`
  and `worktree_branch_test.ts`, likewise.
  - 2026-09-29: Codex (`ctx_2456fec939ad`, follow-up `ctx_bdc377f518d2` for
    the millisecond rounding difference, batch 17).

## Phase 3: Documents, verification and report (US4)

- [x] T006 [US4] Main: the selected prose sites in `docs/architecture.md`
  (S137) and `docs/backfire.md` (S139).
  - 2026-09-29: Main edited only the selected lines; the four S150 lines
    followed after R1 and a new classification (batch 18).
- [x] T007 [US4] Main: `npm run check` and the separate `test_load`,
  `test_ready`, `test_entry` and doctor runs; check time on the base commit
  and the branch; `backfire_review` of each patch, `backfire_gate` on the
  final diff with the real check output, `backfire_verify` on the report's
  claims; [report.md](report.md) and the report to the develop session.
  - 2026-09-29: Main: `npm run check` passed; timings, reviews, gate and
    report in [report.md](report.md). Next: the user decides whether to
    merge; a merge needs the selection redone on the moved `develop`.

## Dependencies

T001 and T002 start together. T003, T004 and T005 start after T001. T006
follows T003 (it describes the final commands). T007 comes last.
