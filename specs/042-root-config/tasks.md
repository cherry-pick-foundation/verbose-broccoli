# Tasks: Root Configuration Boundaries

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

## Phase 1: Tool configs into their owners (User Story 2)

- [x] T001 Snapshot each tool's effective settings before the change (Ruff
  `--show-settings` for 11 sample files, Prettier's resolved options for 9)
  (FR-008).
  - By main (Claude Code, Sonnet at high effort; chosen with two Jev
    judgments, agent `claude` 0.90 with confidence 0.89 and model
    `claude_sonnet_high` 0.44 with confidence 0.36; a probability is not
    evidence of correctness). The estimated difficulty was difficult.
- [x] T002 Fold `.cz.toml` into `[tool.commitizen]` and `ruff.toml` into
  `[tool.ruff]` in `pyproject.toml` with `src = ["packages/*/src"]`; point the
  five packages' `extend` at it; fold `.prettierrc.js` into `package.json`;
  update their tests (FR-003).
  - Effective settings equal before and after (research.md D2).
- [x] T003 Move `mise.toml` and `mise.lock`, `lefthook.yml`, `.ls-lint.yml` and
  `.dependency-cruiser.json` into `.config/`; update every consumer (FR-004,
  FR-006).
  - Each tool's own test passes (research.md D1).

## Phase 2: One source for versions and setup (User Story 1)

- [x] T004 Add the `setup` task and doctor checks to `.config/mise.toml`;
  make `orca.yaml` and `check.yml` call it; remove the tool lists and the
  repeated steps; make `wiki-consistency:install` call `backfire:install`
  (FR-001, FR-002).
  - A shared composite action prepares mise for both workflows.
- [x] T005 Remove the `required-version` copies of uv and the other pins in
  `docs-check.yml` and prose; add the doctor check `uv-version` (FR-001).
  - `uv_build` ranges stay (research.md D6).

## Phase 3: Turborepo graph (User Story 3)

- [x] T006 Replace the `tools/none` workspace entry; remove the root Python
  umbrella tasks and the Python test commands from `turbo.json`; add each
  package's `test` and `check` tasks (FR-007, FR-009).
  - `verbose-broccoli-python#check` stays as the Python fan-out because
    Turborepo would otherwise run `uv check` (research.md D4).
- [x] T007 Add `scripts/root-config-test.ts` (`npm run test:root-config`) for
  layout, pins, setup consumers and the graph, and extend
  `scripts/turbo-cache-test.ts` for the moved test commands (SC-002 to SC-004).
  - Seven mutation checks each made the right test fail (research.md D7).

## Phase 4: Commit-message rules (User Story 4)

- [x] T008 Compare commitlint, `cz check` and the pull-request pattern with
  measured results (research.md D9).
- [x] T008a The user's decision on who owns the commit-message rules; apply it
  (FR-010).
  - On 2026-10-02 the user chose option A: commitlint owns the commit-message
    rules, commitizen only bumps the constitution version, and the
    pull-request title pattern stays. No commit-message tool changed.

## Phase 5: Close

- [x] T009 Update `docs/architecture.md`, the generated command reference and
  the other consumers' prose.
- [x] T010 `npm run verify` on the result; commit the feature record.
  - At 3ec4d54 (the implementation), `npm run verify` exited 0 and printed
    VERIFIED from the same run's Turbo summary: 47 tasks successful, 6 cached,
    3 min 55 s. A first run failed on `//#doctor`: editing the packages'
    `pyproject.toml` made uv rebuild the editable installs, so `uv-workspace`
    reported an outdated environment until `mise run setup` (here `npm run
    backfire:install`) ran again. After the merge, run `mise run setup` in each
    other worktree.
  - Diff against the base 872acea: 47 files, 1,461 lines added and 658
    removed, 2,119 in all; counting each of the four whole-file deletions as
    one line, 1,735. About 560 lines are these records. It is over 1,000, so
    splitting was considered and not done: the moves, their consumers, the
    setup task and the graph edit the same files (`package.json`,
    `turbo.json`, the tests) and none of the parts passes verification alone;
    the largest block, the 282 lines of Ruff rules, is moved text that counts
    twice (removed and added).
  - Observed difficulty by `npm run workflow`: very difficult (51 changed
    files); the estimate before the work was difficult.
- [ ] T011 Develop merge review by a provider other than Claude Code; resolve
  findings; the review-record commit last.
  - First reviewer, chosen with Jev (`typesafe/jev-1.13` through OpenRouter, no
    escape): Cursor `auto`, probability 0.55, confidence 0.49 (Codex
    `gpt-6.1-sol` and `gpt-6-luna`, Copilot `auto` at two tiers and
    Antigravity `gemini-3.8-flash-high` were the others; Grok was out for its
    free cap). It read the diff, then its free requests were refused ("You've
    hit your usage limit", reset 2026-10-16, while Orca's tracker still showed
    0% used) before it wrote a report; the dispatch was stopped, and its
    review does not count.
  - Replacement, chosen with Jev after the user limited starts to Orca's
    native worker start (Cursor, Copilot and Grok out): Codex `gpt-6.1-sol` at
    `high`, probability 0.66, confidence 0.62 (Codex `gpt-6.1-sol` at
    `xhigh` 0.07, `gpt-6-luna` at `xhigh` 0.14, two Antigravity models 0.02
    and 0). A probability is not evidence of correctness.
- [ ] T012 Merge `develop`, verify, finish into `develop` when the finish slot
  is granted.
