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
- [x] T006 [P] [US3] Implement `scripts/session_select.py` with `render`,
  `digest` and `classify`, and its tests on synthetic fixtures (FR-006 to
  FR-012, FR-014).
- [x] T007 [US3] Write `references/session-selection.md` and point the skill
  to it (FR-006 to FR-010).
- [x] T008 [US3] Run the procedure on a small sample of real sessions and
  send the user the backfire call count, the tokens and an estimate for the
  whole set (FR-011).

## Phase 4: Finish

- [ ] T009 Merge `develop`, run `npm run verify`, pass the develop merge
  review by the other provider, commit the review record and finish with
  `git flow feature finish session-wiki`.
  - 2026-09-30 pause for a restart: `develop` (b9a0293) is merged and
    `npm run verify` is VERIFIED at da17737; no worker is running. Next:
    move CHE-47 to In Review, start the two develop merge reviewers named in
    the notes (their specs are in the ignored `.local/che47/`), resolve their
    findings, then the review record and the finish.

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
- The user asked to cut the review load before the full run. A sharper
  catalog (`none` as the expected label for routine work and Orca worker
  sessions, `default` no longer a fallback) and a fresh sample of 64 gave 8
  `review` decisions (12.5%, from 34%) with 2 calls, 53,757 input and 15,986
  output tokens: 58 `none`, 5 `default`, 1 `work`; all 19 Orca worker
  sessions passed as `none`. backfire's auto-accept threshold is unchanged.
  The four automatic `default` results were Codex's own approval reviews,
  which make up 661 of the 1,325 digests; the digest step now holds them
  back mechanically.
- Second re-test, with Codex's approval reviews held back: 677 of them, plus
  71 sessions without a user message and the same 21 with possible secrets,
  left 664 digests. A fresh random 64 took 2 calls with 47,514 input and
  15,673 output tokens: 52 `none`, 5 `work`, 4 `code`, 3 `default`, and 12
  `review` decisions (19%), 7 of them between `code` and `none`. All 43
  Orca worker sessions were labeled `none`. The estimate for the full run is
  about 12 calls, 0.5 million input and 0.16 million output tokens, 6
  minutes and 125 `review` results.
- Size against the merge base with `develop`, before the develop merge
  review: 2,378 added lines, of which 1,073 are records, documents and data
  (the security report alone is 406), 738 tests and 567 script and
  configuration. The feature is not split: the rule, the tool and the
  procedure depend on one another, and the script is the only own code.
- Workers, chosen with backfire (`jev_decide`, then the `model-choice`
  skill once `develop` brought it in): security review Claude Code Opus 5.5
  high (confidence 0.49); glue Codex gpt-6-luna xhigh (0.39); duplication
  check and trim, the same Codex worker reused (0.35); develop merge review
  of the code Claude Code Sonnet 5.5 medium (0.56) and of the records Codex
  gpt-6-luna medium (0.52).
- Before the develop merge review, `doc-regions:prepare --base develop
  --max-evidence-chars 12000` gave 7 `jev_verify` requests over 237 units:
  none contradicted, 227 accepted automatically (mostly unsupported within
  the evidence cap) and 10 flagged for review, each with at most 0.02
  probability of contradiction and "needs diff" as the missing evidence. The
  two flagged units this feature changed, the Wiki storage paragraph of
  `docs/architecture.md` and the constitution's Governance record, match the
  changed files and stand. `doc-regions:audit` (MemoryLint) reports 19
  warnings that constitution rules belong in `AGENTS.md`; they concern text
  that existed before this feature and the Sync Impact Report, and are
  reported to the user without changing either file.
- At the user's request, the glue worker compared each part of the script
  with SpecStory, betterleaks, backfire, PyModel, the mcp client and the
  standard library. None duplicated them: SpecStory's listing is per project
  and its index stores full text, its Claude provider needs an existing
  project folder, it has no reader for its own Markdown, backfire's span
  finder has no word-boundary rule, and PyModel's command line takes one
  request without backfire's education server. The trim left 551 lines and
  +496 net own code.
- Develop merge review, on the branch with CHE-44 and CHE-46 merged: the
  code reviewer (Claude Code Sonnet 5.5 medium) found 4 medium and 5 low
  issues, the records reviewer (Codex gpt-6-luna medium) 1 medium and 1 low.
  Fixed: secret findings matched on resolved paths, a missing or stale scan
  report refused, an empty roster refused, a SpecStory timeout, invalid
  Codex ids, a duplicate count, the session counts, and a trailing blank
  line; the security report gained an addendum on `--print` with source
  lines and the observed offline run. Accepted: the hard-linked mirror
  (SpecStory only reads it) and a missed overlapping roster match inside a
  rejected one, which the Korean and Latin cases in scope do not produce.
