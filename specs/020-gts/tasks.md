---

description: "Task list for TypeScript lint and format with gts"
---

# Tasks: TypeScript Lint and Format with gts

**Input**: Design documents from `specs/020-gts/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md)

**Tests**: `scripts/gts_test.ts` checks the configuration with synthetic
input (FR-008); the existing suites prove unchanged behavior (FR-006).

**Organization**: Main (Claude Code) owns the Spec Kit records, reviews
each Codex worker's diff and runs the merge. Codex workers (`gpt-6-luna`,
max effort) implement T001 to T007. A fresh Claude Code reviewer gives the
merge review of the code; a fresh Codex reviewer reviews the coordinator's
records.

**Private data**: No task writes a student name or record into the
repository or into Orca or Linear messages.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Tooling and configuration (US1, US2)

- [x] T001 [US1] Pin `gts` 7.0.0 in the root `package.json` and
  `package-lock.json`, remove `@biomejs/biome` and `biome.json`, and add
  `eslint.config.js`, `.prettierrc.js` and `eslint.ignores.js` as
  [research.md](research.md) R1, R4 and R6 decide, with the `domain/`
  globals ban (FR-001, FR-002, FR-004, FR-005, FR-007).
- [x] T002 [US1] Run `gts lint .` in the `lint` task and Prettier's check on
  JSON and YAML in `format:check`, with the writing forms in `lint:fix` and
  `format`; drop `biome.json` from the `docs:*` tasks and `scripts/docs.ts`
  (FR-003, FR-004).
- [x] T003 [US1] Add `scripts/gts_test.ts`, a `test:gts` task and its
  Turborepo entry in the `test` dependencies, and list the file in
  `tsconfig.json`: a floating promise, a formatting deviation and a JSON
  formatting deviation fail; a compliant file passes; a file in a vendored
  path is not checked. The banned global in a `domain/` file is tested in
  `scripts/clean_architecture_test.ts` (FR-008).
- [x] T004 [P] [US2] Name gts and its version in `docs/architecture.md`
  instead of Biome, and regenerate `docs/reference/` with
  `npm run docs:generate` (FR-009).

Commit Phase 1 before T005.

- 2026-09-29: A Codex worker (`gpt-6-luna`, max effort, dispatch
  `ctx_af067201a830`) did T001 to T004 in `196a138`. Its three questions
  widened the scope: `scripts/workflow_files.ts` derived its exclusions from
  `biome.json` and now reads `eslint.ignores.js` (same file set, with
  `node_modules/` excluded explicitly); the existing `domain/` ban test in
  `scripts/clean_architecture_test.ts` now runs ESLint, so `test:gts` has no
  domain case; `scripts/docs.ts`, `scripts/docs_test.ts`,
  `scripts/workflow.ts` and `scripts/workflow_graph.ts` stopped naming
  Biome; and gts runs without Node's permission model (research.md R8).

## Phase 2: Mechanical reformat (US1, US2)

- [x] T005 [US1] Run the writing forms of the formatters and commit only
  their output as `style: apply gts format`, with no hand edits (FR-006).
  - 2026-09-29: The same worker committed `9befb6d`. The coordinator
    reproduced it by running `gts fix .` and the `format` task's Prettier
    steps on a copy of `196a138`: no difference (SC-004).

## Phase 3: Hand fixes (US1)

- [x] T006 [US1] Fix the remaining findings other than `node:test`'s
  floating promises without changing behavior, as research.md R3 decides
  (FR-006).
- [x] T007 [US1] Put `void` in front of each top-level `node:test`
  `test(...)` call that gts's `no-floating-promises` rule flags, in a commit
  of its own (FR-006, spec.md clarification).
  - 2026-09-29: The same worker committed T006 in `6abe3f5` (`process`
    imported from `node:process` in two `.mjs` files, two
    `eslint-disable-next-line` comments with reasons in `scripts/docs.ts`,
    one obsolete `biome-ignore` comment removed) and T007 in `51414cf`
    (175 `void test(...)` calls in 17 files; every changed line is a
    `test(` call). `npm run verify -- --task che-36 --base 7e18ad4` passed
    on `51414cf` (workflow phase VERIFIED, 28 check tasks). No Python file
    changed, so the Python suites cannot change; they passed with backfire
    1,364 (3 deselected), doc-regions 106 and wiki-consistency 291. The
    Node suites hold 175 top-level tests, 174 on `develop` plus the new
    `test:gts`.

## Phase 4: Verification and review

- [ ] T008 Run `npm run verify`; compare the suites' test counts with
  `develop` (SC-001 to SC-004).
- [ ] T009 Merge `develop`, fix new findings, verify, move CHE-36 to In
  Review, run the merge review, resolve findings, commit the review record
  and run `git flow feature finish gts` in the `develop` worktree; then move
  CHE-36 to Done with one completion comment (SC-001).
  - 2026-09-29: `develop` had not moved from `7e18ad4`, so no merge was
    needed yet. The document judgment step (`doc-regions:prepare -- --base
    develop --max-evidence-chars 20000`) sent 229 units in 10
    `backfire_verify` requests, which used 784,691 input and 117,985 output
    tokens. No unit was contradicted. The changed `docs/architecture.md`
    unit (30-60) was verified. The 19 units flagged for review describe
    `AGENTS.md`, the README, the plugin packages and the commit hook, which
    this feature does not change, so they stand. `doc-regions:audit`
    reported the same 19 MemoryLint `boundary` warnings on the constitution
    as earlier features; they are reported, not acted on.
  - 2026-09-29: Merge review, first round. The code reviewer is a fresh
    Claude Code worker on `claude-sonnet-5-5` at medium effort, which
    `backfire_decide` preferred (0.45) over high effort (0.25) for a
    speed-favoring review; the records reviewer is a fresh Codex worker
    (`gpt-6-luna`, max effort; dispatch `ctx_870eacabd100`). Both reviewed
    the records commit then at the tip, which is `32923dc` after the reword
    below.
  - 2026-09-29: The code reviewer (dispatch `ctx_9250a97dfe0c`) approved
    after fixes with one major finding: `scripts/gts_test.ts` has no
    `domain/` case, so FR-007's ban looked untested. It does not stand: the
    ported test in `scripts/clean_architecture_test.ts`, which `npm test`
    runs, failed when the coordinator removed the ban from a copy of
    `eslint.config.js`. The records reviewer requested changes: one major
    finding, that Git read only T004 as a trailer of the first
    implementation commit because blank lines separated its four
    `Spec-Kit-Task` lines, and one minor finding, that plan.md and T003
    placed the `domain/` case in the new test. The coordinator reworded that
    commit's message with a scripted `git rebase -i 7e18ad4` that only
    rewords it; all eight rebased commits kept their trees, and the hashes
    above are the new ones (`196a138` was `728c785`). The coordinator also
    corrected plan.md and T003.
