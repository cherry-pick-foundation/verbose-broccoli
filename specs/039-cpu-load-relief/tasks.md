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
  the `turborepo` script, and ignore `.turbo/` (FR-001 to FR-004, FR-007).
  - By main (Claude Code).
- [x] T003 Add `scripts/turbo-cache-test.ts` (`npm run test:turbo-cache`,
  task `//#test:turbo-cache`) for each kind of input (FR-006, SC-002).
  - By main (Claude Code). The first version hashed standard error too, and
    the test failed: under the test's Node permission flags, `npm --version`
    printed a warning with its process ID. The fingerprint now hashes
    standard output only.
  - The first measurement (T005) replayed nothing: Turborepo's package task
    logs (`packages/<name>/.turbo/`) were not ignored, so they became inputs
    of every root task. Fixed in 65d0ac9 (ignore `.turbo/` at any depth),
    with a test that fails under the old rule.
- [x] T004 Remove each declaration in turn and confirm a test fails
  (SC-002).
  - Without `doc-regions#test`'s inputs, the repository-file test failed;
    without `globalDependencies`, the installed-environment test; without
    `VERBOSE_BROCCOLI_TOOLCHAIN` or `UV_*` in `globalEnv`, the program and
    configuration test. The other tests passed each time.
- [x] T005 Measure the CPU time of a second `npm run verify` on an unchanged
  tree before (at 1eef330's configuration) and after, on the efficiency
  cores, one verify at a time (SC-001, FR-005).
  - By main. A repeat verify on an unchanged tree: 228.7 s wall and 545.1 s
    CPU before; 5.0 s wall and 9.9 s CPU after (at c2cb5a7), with 30 of 38
    tasks replayed and VERIFIED read from the same run's summary
    (research.md D9). Of 1eef330's 43 tasks, 29 are cached; with the new
    test, 30 of 44, and after the merge of `develop` da52d3a, which added
    the uncached `//#test:reference-library`, 30 of 45; after the merge of
    `develop` 279b29f, whose new `//#test:secrets-refresh` is cached, 31 of
    46.
- [x] T006 Update the command reference and the architecture note for the
  cache.
  - By main, in 592012b (`npm run doc-regions:update` for the reference).

## Phase 2: Scheduler review (User Story 3)

- [x] T007 Review System76's scheduler and its GNOME Shell extension and
  record it in `security/` (FR-008).
  - Worker: Codex `gpt-6.1-sol` at `xhigh`, started with `worker-start
    --agent codex --model gpt-6.1-sol --effort xhigh`; its status line
    showed "GPT-6.1-Sol xhigh". Backfire's `jev_decide` (provider
    `openrouter`, model `typesafe/jev-1.13`) returned `invalid_response`, so
    the orchestrator asked the develop session, and the user chose the model
    without another judgment.
  - Result: `security/system76-scheduler-8651bbf.md`, reviewing commit
    8651bbf against release 2.0.2: not acceptable as shipped, 6 medium and 1
    low findings; the small focus extension supports GNOME 40 to 44 only, and
    only Pop Shell declares GNOME 50. No build, install or sudo command ran.
- [x] T008 Put the review's findings to the user and record the install
  decision (SC-004).
  - 2026-10-01, through the develop session: do not install; the scheduler
    leaves scope, and the CPU rule stays the fix for load spikes. Whether
    Turborepo stays is decided in CHE-74 from T005's figures.

## Phase 3: Finish

- [x] T009 Merge `develop`, run `npm run verify`, pass the develop merge
  review by a provider other than Claude Code, commit the review record and
  finish with `git flow feature finish cpu-load-relief`.
  - Split review: the change against `develop` passes 1,000 lines, about 850
    of them the scheduler record. Kept as one feature: the record is
    Markdown that no code depends on, the user's brief and CHE-73 hold both
    parts, and the code change is about 450 lines.
  - Reviewer: Copilot `auto` at the `balance` tier, chosen with Jev
    (`jev_decide`, provider `openrouter`, model `typesafe/jev-1.13`):
    probability 0.69, confidence 0.65 (Copilot `intelligence` 0.25, Cursor
    and Grok 0.02 each, Antigravity 0.01). Claude Code and Codex both
    implemented parts, so neither was a candidate.
  - `npm run doc-regions:prepare -- --base develop --max-evidence-chars
    12000` printed four `jev_verify` requests (Jev, `openrouter`). One claim
    came back contradicted: the `docs/architecture.md` paragraph on `verify`
    and the cache, judged on truncated evidence (`needs_diff`). Rechecked
    against the full `turbo.json`, `scripts/toolchain.sh`, `.gitignore` and
    the `turborepo` script, its three new sentences were verified and the
    unchanged first one was unsupported by that evidence, so the paragraph
    stands. `npm run doc-regions:audit` reported 20 warnings, all about the
    constitution's existing layout, which this feature does not change.
  - Review (Copilot `auto`, `balance` tier, routed to `gpt-6-luna`), range
    1eef330 to 4da153c: 1 medium finding, 0 high, 0 low. Edits inside an
    installed environment left task hashes unchanged, because only npm's
    hidden lockfiles and each distribution's `METADATA` were hashed. Fixed by
    hashing the installed files themselves (research.md D4), with the
    installed-environment test extended to package files and a native
    program; that test fails with the previous declarations.
  - Follow-up reviewer: a second fresh Copilot `auto` session at the
    `balance` tier (routed to `gpt-6-luna`), chosen with Jev (0.71,
    confidence 0.65), reviewed 1eef330 to 74e18aa: 1 medium finding, 0 high,
    0 low. The entry-point scripts in the uv environments' `bin/`, such as
    the `pytest` launcher, were left out of the hash. Fixed by hashing them,
    with `.pth` files, `direct_url.json` and `pyvenv.cfg`, in
    `scripts/toolchain.sh` with the worktree's path replaced (research.md
    D4); the extended test fails with the previous script. The reviewer
    asked twice for access outside the worktree: to search the parent folder
    (declined) and to resolve the interpreters' links (allowed once).
  - Third reviewer: a fresh Copilot `auto` session at the `balance` tier,
    chosen with Jev (0.62, confidence 0.56), reviewed 1eef330 to c2137d3: 1
    medium finding, 0 high, 0 low. Links in `node_modules`, such as the
    `.bin/tsc` launcher, were not hashed. Fixed by listing every entry of the
    installed environments with its type, permissions and link target. The
    same sweep found that ESLint, clean-code and dependency-cruiser walk
    folders and so read Git-ignored files, now declared as their inputs, and
    that `//#test:plugin-skills` checks for absent folders, which Turborepo
    cannot hash; it is now uncached (research.md D2, D4, D5). The new and
    extended tests fail without these declarations.
  - Fourth reviewer: a fresh Copilot `auto` session at the `balance` tier,
    chosen with Jev (0.56, confidence 0.50), reviewed 1eef330 to 9a948aa: 1
    medium finding, 0 high, 0 low. `NODE_OPTIONS` reached tasks without
    being hashed: Turborepo passes a built-in list of variables even in
    strict mode. Fixed by hashing the ones that can change a result here
    (research.md D3), with a test case that fails without it.
  - No fifth review: the fourth fix only adds variable names to the hashed
    list, which can cause extra cache misses but never a replay, so it does
    not change the implementation materially (AGENTS.md, "Review").
  - 2026-10-01: `develop` moved to da52d3a (CHE-76, reference library);
    merged in a9fe379. Conflicts: `turbo.json`, where CHE-76's new
    `//#test:reference-library` stays uncached with its reason (research.md
    D5), and the generated command reference, regenerated. After reviewing
    CHE-76's `mise.toml` change (the checksum-pinned Caddy 2.11.4 and a
    doctor check), ran `mise trust --yes mise.toml` and `npm ci
    --ignore-scripts --no-audit --no-fund --prefix plugins/work`; the
    project's tools, Caddy included, were already installed.
  - Handoff, 2026-10-01 before a reboot: caching is done, reviewed four
    times and VERIFIED at 3fa1020 (39 of 39); a repeat verify takes 5.0 s and
    9.9 s CPU against 228.7 s and 545.1 s before. Next: merge `develop` again
    after CHE-77's finish, verify, commit the develop merge review record,
    ask the develop session for the finish slot, finish, and close CHE-73.
  - Resumed after the reboot: `develop` moved to 279b29f (CHE-77, provider
    secrets); merged. Conflicts in `turbo.json`, `tsconfig.json` and the
    generated command reference. CHE-77's `//#test:secrets-refresh` is
    cached: it runs Node with a fake `bws` and a temporary home and passes
    only `PATH`, `HOME` and `XDG_CONFIG_HOME` (research.md D6). After
    reviewing CHE-77's `mise.toml` change (the pinned `bws` 2.1.0), ran
    `mise trust --yes mise.toml`, `mise install --locked` for the project's
    tools (all already installed) and `npm ci --ignore-scripts --no-audit
    --no-fund --prefix plugins/work`.
