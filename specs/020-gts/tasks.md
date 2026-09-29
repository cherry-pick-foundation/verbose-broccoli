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
max effort) implement T001 to T006. A fresh Claude Code reviewer gives the
merge review of the code; a fresh Codex reviewer reviews the coordinator's
records.

**Private data**: No task writes a student name or record into the
repository or into Orca or Linear messages.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Tooling and configuration (US1, US2)

- [ ] T001 [US1] Pin `gts` 7.0.0 in the root `package.json` and
  `package-lock.json`, remove `@biomejs/biome` and `biome.json`, and add
  `eslint.config.js`, `.prettierrc.js` and `eslint.ignores.js` as
  [research.md](research.md) R1, R4 and R6 decide, with the `domain/`
  globals ban (FR-001, FR-002, FR-004, FR-005, FR-007).
- [ ] T002 [US1] Run `gts lint .` in the `lint` task and Prettier's check on
  JSON and YAML in `format:check`, with the writing forms in `lint:fix` and
  `format`; drop `biome.json` from the `docs:*` tasks and `scripts/docs.ts`
  (FR-003, FR-004).
- [ ] T003 [US1] Add `scripts/gts_test.ts`, a `test:gts` task and its
  Turborepo entry in the `test` dependencies, and list the file in
  `tsconfig.json`: a floating promise, a formatting deviation, a banned
  global in a `domain/` file and a JSON formatting deviation fail; a
  compliant file passes; a file in a vendored path is not checked (FR-008).
- [ ] T004 [P] [US2] Name gts and its version in `docs/architecture.md`
  instead of Biome, and regenerate `docs/reference/` with
  `npm run docs:generate` (FR-009).

Commit Phase 1 before T005.

## Phase 2: Mechanical reformat (US1, US2)

- [ ] T005 [US1] Run the writing forms of the formatters and commit only
  their output as `style: apply gts format`, with no hand edits (FR-006).

## Phase 3: Hand fixes (US1)

- [ ] T006 [US1] Fix the remaining findings without changing behavior, as
  research.md R3 and the clarification decide (FR-006).

## Phase 4: Verification and review

- [ ] T007 Run `npm run verify`; compare the suites' test counts with
  `develop` (SC-001 to SC-004).
- [ ] T008 Merge `develop`, fix new findings, verify, move CHE-36 to In
  Review, run the merge review, resolve findings, commit the review record
  and run `git flow feature finish gts` in the `develop` worktree; then move
  CHE-36 to Done with one completion comment (SC-001).
