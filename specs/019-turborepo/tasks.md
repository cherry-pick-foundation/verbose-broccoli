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

## Phase 4: The real change (2026-09-29)

The user made the trial the real change: merge `develop`, remove Deno
completely, apply the governance wording and finish into `develop`. The
selection was redone on the merged tree
([evidence/selected-sites-full-removal.md](evidence/selected-sites-full-removal.md)).

- [x] T013 Main: merge `develop` 8ce9b2a (`cfbb1c7`), resolving 16 conflicts;
  a fresh Codex review (R2) checks the resolution.
- [ ] T008 [P] The clean-code skill on Node (D16): its own `package.json`,
  lock and `.npmrc`, Node built-ins, `node:test`, the Node run command in
  `SKILL.md`, and the repository files that run or copy it.
- [ ] T009a [P] The non-test scripts without the shim and `@std/fs`, and the
  doctor without Deno.
- [ ] T010 [P] Test suites group A without the shim.
- [ ] T011 [P] Test suites group B without the shim, including develop's
  `scripts/ruff_test.ts`.
- [ ] T012 [P] Python follow-ups: the work build's `backfire` source, the Ruff
  findings, the separator comment, and the newer lock versions (FR-013).
- [ ] T009b After T008 to T012: remove the preload, `@deno/shim-deno`,
  `@std/fs` and `deno.json`; port develop's Ruff tasks; no Deno in
  `orca.yaml` or the workflows; regenerate the references.
- [ ] T014 Main: the governance wording in `AGENTS.md` and the constitution,
  and the selected prose in `README.md`, `docs/architecture.md` and
  `docs/backfire.md`.
- [ ] T015 Main: `npm run verify`; a fresh Claude Code reviewer for the Codex
  code and a fresh Codex reviewer for main's changes; the review record;
  `git flow feature finish`; CHE-32 to Done.

## Dependencies

T001 and T002 start together. T003, T004 and T005 start after T001. T006
follows T003 (it describes the final commands). T007 comes last.
