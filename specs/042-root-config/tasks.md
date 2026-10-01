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
- [ ] T008a The user's decision on who owns the commit-message rules; apply it
  (FR-010). Asked of the develop session on 2026-10-02; no commit tool changes
  before the answer.

## Phase 5: Close

- [x] T009 Update `docs/architecture.md`, the generated command reference and
  the other consumers' prose.
- [ ] T010 `npm run verify` on the result; commit the feature record.
- [ ] T011 Develop merge review by a provider other than Claude Code; resolve
  findings; the review-record commit last.
- [ ] T012 Merge `develop`, verify, finish into `develop` when the finish slot
  is granted.
