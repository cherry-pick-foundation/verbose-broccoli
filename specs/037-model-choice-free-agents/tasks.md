# Tasks: Free-Quota Agents in Model Choice

**Input**: [spec.md](spec.md), [plan.md](plan.md)

`[P]` marks tasks that can run in parallel.

## Phase 1: Jev-only judgments (User Story 1)

- [x] T001 Cherry-pick CHE-69's backfire `serve-mcp --profile` commit
  (93c5f5d) unchanged, with CHE-69's orchestrator's agreement (FR-004).
  - 7544e42 on this branch, made with `git cherry-pick -x`.

## Phase 2: Readiness tests (User Story 2)

- [x] T002 Start one worker per new agent on a trivial task; confirm
  heartbeat, `check` and `worker_done` (FR-009). The user switched
  Antigravity and Cursor on in Orca's agent settings first; Grok was on.
  Each choice ran `jev_decide` through `serve-mcp --profile openrouter` and
  answered with provider `openrouter`, model `typesafe/jev-1.13`; the
  evidence gave the difficulty (very easy) and the agent's usage.
  - Antigravity: `gemini-3.8-flash-low`, effort `low` (probability 0.96,
    confidence 0.96), started with `worker-start --agent antigravity --model
    --effort`; requested and effective launch matched. Heartbeat, `check` and
    `worker_done` passed; `worker-release` closed the terminal. Usage stays
    unknown.
  - Grok: `grok-4.7`, effort `low` (probability 1.00, confidence 0.99).
    `worker-start --agent grok --model` failed with `invalid_argument`, so it
    ran through the terminal path with `grok -m grok-4.7 --reasoning-effort
    low --permission-mode bypassPermissions`. Grok first asked whether to
    trust the repository's folder (it named the main worktree); answered
    `y`. The status line showed "Grok 4.7 (low) · always-approve".
    Heartbeat, `check` and `worker_done` passed in 13 seconds with about
    23.4k tokens; the weekly window stayed at 0%. `worker-release` retained
    the terminal (`external_terminal`), so it was closed with `/quit` and
    `terminal close`.
  - Cursor: Jev escaped with `investigate` (probability 0.33, confidence
    0.22), since the free plan's allowed models were unknown. The user chose
    `composer-2.5`; Cursor refused it ("Named models unavailable. Free plans
    can only use Auto."). That worker was stopped with `worker-stop` and the
    task retried with `--model auto`, which passed heartbeat, `check` and
    `worker_done`; `worker-release` closed the terminal. The monthly window
    stayed at 0%.
- [x] T003 Add the launch notes for Antigravity, Grok and Cursor to
  `~/.claude/rules/worker-dispatch.md` after a dated backup (FR-010).
  - Backup `worker-dispatch.md.bak-che70-20261001T064514Z`; a new section,
    "Antigravity, Grok and Cursor workers", holds the steps above.

## Phase 3: The rules (User Stories 1 to 3)

- [x] T004 [P] In `references/model-choice.md` and the skill's description:
  the three candidates, their catalogs, usage reads and launch paths;
  difficulty and usage in the evidence; Jev-only judgments; MiniMax Code
  only as `mcode exec`; student data on Claude Code and Codex only
  (FR-001 to FR-006).
  - 04c0a9e, by main (Claude Code). `docs/backfire.md` documents
    `serve-mcp --profile`; CHE-69's orchestrator leaves that paragraph to
    this feature.
- [x] T005 [P] Let Antigravity, Grok and Cursor give develop merge reviews in
  `AGENTS.md`, the constitution (2.6.0, `feat`), `scripts/workflow.ts` with
  its test, and `docs/architecture.md`; make the printed difficulty sentence
  point to the model choice (FR-007, FR-008).
  - 323d954, by main (Claude Code). The user chose develop merge reviews
    only; release and hotfix reviews keep Claude Code, Codex or Copilot.
    `npm run verify` printed VERIFIED (37 of 37 tasks).
- [ ] T006 Run one model choice for a sample task across all agents and
  record its evidence and answer (SC-001).

## Phase 4: Finish

- [ ] T007 Merge `develop`, run `npm run verify`, pass the develop merge
  review by a provider other than Claude Code, commit the review record and
  finish with `git flow feature finish model-choice-free-agents`.
