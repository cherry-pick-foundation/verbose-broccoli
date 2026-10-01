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
- [x] T006 Run one model choice for a sample task across all agents and
  record its evidence and answer (SC-001).
  - The sample is this feature's develop merge reviewer, chosen in two
    `jev_decide` steps through `serve-mcp --profile openrouter`; both answers
    named provider `openrouter`, model `typesafe/jev-1.13`. The evidence gave
    the difficulty from `npm run workflow -- --base develop` (difficult: 16
    files, 511 changed lines, mostly prose) and every candidate's usage on
    2026-10-01 at 15:55 KST: Codex weekly 67% used; Copilot Chat 2.1% (4 of
    200 credits); Grok weekly 0%; Cursor monthly 0% (free plan, `auto`
    only); Antigravity unknown. Claude Code implemented the feature, so the
    other-provider rule (`AGENTS.md`, "Review") kept it out of the
    candidates; its usage (session 8%, weekly 47%) was read but not given.
  - Agent: Copilot (probability 0.44, confidence 0.36; Grok 0.22, Codex
    0.20, Cursor 0.08, Antigravity 0.03). Tier: `fast` (probability 0.49,
    confidence 0.40; balance 0.28, efficiency 0.21).

## Phase 4: Finish

- [ ] T007 Merge `develop`, run `npm run verify`, pass the develop merge
  review by a provider other than Claude Code, commit the review record and
  finish with `git flow feature finish model-choice-free-agents`.
  - `develop` 870cc81 merged in b1f6118 without conflicts. The first full
    `npm run verify` failed only in the known `.git/index` race of
    `packages/doc-regions/tests/test_requests.py::test_prepare_excludes_judged_documents_and_empty_evidence_has_no_verify`
    (noted in feature 031); the rerun printed VERIFIED (37 of 37).
  - `doc-regions:prepare --base develop --max-evidence-chars 12000` gave 4
    `jev_verify` requests over 268 units and 1 `jev_classify`: none
    contradicted, 40 verified, 228 unsupported within the evidence cap. The
    units this feature changed were verified, except the constitution's long
    git flow paragraph, which was unsupported. `doc-regions:audit` reports
    19 warnings that constitution rules belong in `AGENTS.md` and one false
    warning that `scripts/workflow.ts` does not exist, as for feature 031;
    they are reported to the user without changing either file.
  - Reviewer: Copilot `auto` at the `fast` tier (routed to `gpt-5.6-luna`),
    started through the terminal path; it used 1.91 AI credits in about 90
    seconds. It reviewed b1f6118 and found 2 medium findings: T006 was not
    recorded, and the reference still offered Cursor's named models on the
    free plan. Both are resolved after b1f6118.
  - Follow-up reviewer: a fresh Copilot `auto` session at the `fast` tier
    (routed to `gpt-5.6-luna`), chosen with Jev (agent: Copilot, probability
    0.48, confidence 0.40; tier: `fast`, 0.80, 0.76) for the easy fix range
    b1f6118 to f23a4e0; it used 1.44 AI credits. When it asked to read the
    worktrees' parent folder, the request was declined and it was told to
    stay in the worktree. It found 1 medium finding: T006 said every
    candidate's usage was given and that Claude Code was left out, which
    read as missing evidence. T006 now says why Claude Code was not a
    candidate; the change touches only this file.
