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
- [x] T008 [P] The clean-code skill on Node (D16): its own `package.json`,
  lock and `.npmrc`, Node built-ins, `node:test`, the Node run command in
  `SKILL.md`, and the repository files that run or copy it.
  - 2026-09-29: Codex (`gpt-6-luna`, max; `ctx_2c8fdfc5e607`, follow-up
    `ctx_5c8c1bbba4e7`). Main's review found a Deno-only glob option and two
    `assertRejects` predicates that checked nothing; the follow-up fixed them
    and moved the root clean-code scripts to Node. Main added
    `plugins/code/package.json` (D18) and the root ESLint pins.
- [x] T009a [P] The non-test scripts without the shim and `@std/fs`, and the
  doctor without Deno.
  - 2026-09-29: Codex (`ctx_ca1466821c39`, follow-up `ctx_4d6c8fdaf61e`). The
    import-boundary check reads `package.json` (D18); the follow-up restored
    full file modes and shortened the ENOENT checks.
- [x] T010 [P] Test suites group A without the shim.
  - 2026-09-29: Codex (`ctx_56ff46a59f12`). Fixtures write `package.json`
    (D18); Main checked that the builtin stubs in `docs_test.ts` intercept.
- [x] T011 [P] Test suites group B without the shim, including develop's
  `scripts/ruff_test.ts`.
  - 2026-09-29: Codex (`ctx_726431586fcb`, follow-up `ctx_9ca4b5c123cc`). The
    follow-up restored the doctor's Node permission-denial tests, the Ruff
    test's `/tmp` directory and one fixture's string export.
- [x] T012 [P] Python follow-ups: the work build's `backfire` source, the Ruff
  findings, the separator comment, and the newer lock versions (FR-013).
  - 2026-09-29: Codex (`gpt-6-luna`, max; `ctx_fa4fecc8e747`). Four packages
    moved to develop's newer versions; `typesafe-sdk` stays 0.7.1 (the FR-013
    exception). Main reran the slow and load, ready and entry tests on the new
    pins; they pass.
- [x] T009b After T008 to T012: remove the preload, `@deno/shim-deno`,
  `@std/fs` and `deno.json`; port develop's Ruff tasks; no Deno in
  `orca.yaml` or the workflows; regenerate the references.
  - 2026-09-29: Codex (`ctx_72723d51a683`). Also: test files in the type
    check, no per-skill install in setup or CI, row X169 (batch 23). Main
    reran `npm run check` (27 of 27) and `npm run verify` with Deno hidden
    from `PATH` (VERIFIED). Next: T015's reviews.
- [x] T014 Main: the governance wording in `AGENTS.md` and the constitution,
  and the selected prose in `README.md`, `docs/architecture.md` and
  `docs/backfire.md`.
  - 2026-09-29: Main: constitution 2.2.0 in `b1f8fff` (feat, confirmed by the
    user, D17) and the prose in `d5eb6be`. Only dated history still names
    Deno.
- [x] T016 [P] Review fixes F1: `backfire:install` syncs the whole workspace;
  the doctor requires Node.js 24.12 (D19), reports the direct npm
  dependencies and checks Turborepo; the commit-msg tests run the real
  `commitlint` script; test helpers fail on a killed child (rows V01, V05,
  V07, V13, V24, V26 in
  [evidence/review-findings.md](evidence/review-findings.md)).
  - 2026-09-29: Codex (`ctx_23530a8e0236`). Both the hook and the
    `commitlint` script need `--disable-warning=SecurityWarning`, because
    Node passes the permission flags to npm's children; Main added braces to
    the hook line for ShellCheck.
- [x] T017 [P] Review fixes F2: review routing for the new tooling files, the
  IO-package rule for installed packages, the `docs` directory guard, the
  Deno-era evidence filter, and test helpers (V02, V03, V04, V13, V14).
  - 2026-09-29: Codex (`ctx_70ef84e524cf`). Each fix has a case that failed
    before it.
- [x] T018 [P] Review fixes F3: the build test compares built locks with the
  root lock, the dead separator branch in doc-regions goes, three stale
  `pyproject.toml` comments go, and the root constraints keep only what is
  needed (V09, V10, V11, V15, D20).
  - 2026-09-29: Codex (`ctx_3a05d4d03026`). All 78 locked versions stayed
    the same; the build test rejected an injected 99.99.99 pin.
- [ ] T015 Main: `npm run verify`; a fresh Claude Code reviewer for the Codex
  code and a fresh Codex reviewer for main's changes; the review record;
  `git flow feature finish`; CHE-32 to Done.
  - 2026-09-29: Main: three Claude Code reviewers (CR1 to CR3, Opus 5.5 at
    high effort) and one Codex reviewer (R3) reviewed `9d8af61`; backfire
    batch 24 selected the findings to fix (T016 to T018) and D19 to D21
    decided three more. Next: review the fixes, verify, record the review.

## Dependencies

T001 and T002 start together. T003, T004 and T005 start after T001. T006
follows T003 (it describes the final commands). T007 comes last.
