# Tasks: CPU Load Relief

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

## Phase 1: Caching with declared inputs (User Stories 1 and 2)

- [x] T001 Read what Turborepo hashes for every task in the check graph and
  what each task runs and reads; record the decision per task
  (research.md D1 to D6; FR-001).
  - By main (Claude Code).
- [x] T002 In `turbo.json`, cache every task D6 lists, keep D5's tasks
  uncached with the reason in their description, declare
  `doc-regions#test`'s outside files, name the installed records in
  `globalDependencies`, and hash the fingerprint and the behavior-changing
  variables in `globalEnv`; add `scripts/toolchain.sh`, pass its output from
  the `turborepo` script, and ignore `/.turbo/` (FR-001 to FR-004, FR-007).
  - By main (Claude Code).
- [x] T003 Add `scripts/turbo-cache-test.ts` (`npm run test:turbo-cache`,
  task `//#test:turbo-cache`) for each kind of input (FR-006, SC-002).
  - By main (Claude Code). The first version hashed standard error too, and
    the test failed: under the test's Node permission flags, `npm --version`
    printed a warning with its process ID. The fingerprint now hashes
    standard output only.
- [x] T004 Remove each declaration in turn and confirm a test fails
  (SC-002).
  - Without `doc-regions#test`'s inputs, the repository-file test failed;
    without `globalDependencies`, the installed-environment test; without
    `VERBOSE_BROCCOLI_TOOLCHAIN` or `UV_*` in `globalEnv`, the program and
    configuration test. The other tests passed each time.
- [ ] T005 Measure the CPU time of a second `npm run verify` on an unchanged
  tree before (at 1eef330's configuration) and after, on the efficiency
  cores, one verify at a time (SC-001, FR-005).
- [ ] T006 Update the command reference and the architecture note for the
  cache.

## Phase 2: Scheduler review (User Story 3)

- [ ] T007 Review System76's scheduler and its GNOME Shell extension and
  record it in `security/` (FR-008).
  - Worker: Codex `gpt-6.1-sol` at `xhigh`, started with `worker-start
    --agent codex --model gpt-6.1-sol --effort xhigh`; its status line
    showed "GPT-6.1-Sol xhigh". Backfire's `jev_decide` (provider
    `openrouter`, model `typesafe/jev-1.13`) returned `invalid_response`, so
    the orchestrator asked the develop session, and the user chose the model
    without another judgment.
- [ ] T008 Put the review's findings to the user and record the install
  decision (SC-004).

## Phase 3: Finish

- [ ] T009 Merge `develop`, run `npm run verify`, pass the develop merge
  review by a provider other than Claude Code, commit the review record and
  finish with `git flow feature finish cpu-load-relief`.
