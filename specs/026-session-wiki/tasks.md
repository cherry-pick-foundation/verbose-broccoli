# Tasks: Session Selection for the Wiki Vaults

**Input**: [spec.md](spec.md), [plan.md](plan.md)

Tests use synthetic fixtures only. `[P]` marks tasks that can run in
parallel.

## Phase 1: The rule (User Story 1)

- [x] T001 [US1] Amend constitution principle VI and Governance so exported
  Claude Code and Codex sessions are Raw evidence in any vault they belong
  to; raise the version to 2.4.0 in a `feat` commit (FR-001, FR-002).
- [x] T002 [P] [US1] State the rule in `docs/architecture.md`,
  `docs/examples/wiki/AGENTS.md`, the `wiki-raw-import` skill and its schema
  template (FR-003).

## Phase 2: The tools (User Story 2)

- [x] T003 [P] [US2] Review SpecStory CLI 2.15.1 and betterleaks 1.9.0
  read-only: network use, telemetry, cloud sync defaults, files read and
  written, release checksums and attestations; write
  `security/specstory.md` with evidence per finding (FR-004).
- [x] T004 [US2] After a pass, pin both tools in a root `mise.toml` with a
  reviewed `mise.lock`, trust this worktree's file, install them, and add
  `MISE_*` to `turbo.json`'s pass-through variables (FR-005).

## Phase 3: The procedure (User Story 3)

- [x] T005 [P] [US3] Write the catalog,
  `references/session-catalog.json` (FR-009, FR-013).
- [ ] T006 [P] [US3] Implement `scripts/session_select.py` with `render`,
  `digest` and `classify`, and its tests on synthetic fixtures (FR-006 to
  FR-012, FR-014).
- [ ] T007 [US3] Write `references/session-selection.md` and point the skill
  to it (FR-006 to FR-010).
- [ ] T008 [US3] Run the procedure on a small sample of real sessions and
  send the user the backfire call count, the tokens and an estimate for the
  whole set (FR-011).

## Phase 4: Finish

- [ ] T009 Merge `develop`, run `npm run verify`, pass the develop merge
  review by the other provider, commit the review record and finish with
  `git flow feature finish session-wiki`.

## Notes

- 2026-09-30, sample run (T008) on this laptop, counts only: SpecStory
  rendered 1,467 session files offline in 4.5 minutes and skipped 20 still
  running; they are 1,427 distinct sessions, since Codex can write one
  session into several files. betterleaks found 53 possible secrets in 21
  sessions, which were held back; 81 sessions had no user message. That left
  1,325 digests. A random 64 went to backfire in education mode in 2 calls
  with 53,536 input and 15,327 output tokens in 55 seconds: 45 `none`, 10
  `default`, 6 `work`, 2 `code`, 1 `chat`, and 22 `review` decisions. The
  estimate for all digests is about 22 calls, 1.1 million input and 0.32
  million output tokens and 10 minutes.
- The first sample attempt failed after backfire answered, because the
  script read MCP result fields under names the installed `mcp` 2.2.0 does
  not use; the tests had used an injected fake. The roster check first
  tagged 42% of digests as student data, because one two-syllable given name
  also occurs inside common Korean words; counting word-start matches only
  gives 16%.
