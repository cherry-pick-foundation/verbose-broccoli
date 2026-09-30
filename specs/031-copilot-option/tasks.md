# Tasks: Copilot as a Reviewer and a Model-Choice Option

**Input**: [spec.md](spec.md), [plan.md](plan.md)

`[P]` marks tasks that can run in parallel.

## Phase 1: Security check (User Story 1)

- [x] T001 Review CodexBar 0.69.0's Copilot provider code path read-only:
  credential sources, hosts called, what it stores and prints; evidence for
  each finding and a pass or fail verdict (FR-001).
  - Reviewer: Codex `gpt-daybreak-blue-latest`, effort `xhigh`, chosen by
    backfire `jev_decide` (probability 0.53, confidence 0.47).
  - Result: pass with limits, one low finding (CodexBar sends any token it
    gets, so it needs a dedicated `read:user` token):
    [security/codexbar-copilot.md](security/codexbar-copilot.md).

## Phase 2: The rules (User Stories 1 and 2)

- [x] T002 [P] After a pass, allow `codexbar usage --provider copilot` in
  `references/model-choice.md` under the other providers' limits (FR-002).
  - The user chose a token from GitHub's device login with CodexBar's own
    OAuth app and `read:user`, saved in
    `~/.config/verbose-broccoli/providers/copilot.env`. The call returned a
    monthly `Chat` window and "Credits used", with no account identity.
- [x] T003 [P] Add Copilot as a candidate in `references/model-choice.md` and
  the skill's description (FR-003).
- [x] T004 [P] Name Claude Code, Codex and Copilot as review providers and
  prefer Copilot when Claude Code and Codex both implemented a feature, in
  `AGENTS.md`; the same providers in the constitution (2.5.0, `feat`),
  `scripts/workflow.ts` with its test, and `docs/architecture.md` (FR-004).

## Phase 3: Launch (User Story 3)

- [x] T005 Start one Copilot worker through the terminal path on a trivial
  task; confirm heartbeat, `check` and `worker_done`; count the requests it
  used (FR-005).
  - Worker: Copilot `auto` with `--auto-tier efficiency`, chosen by backfire
    `jev_decide` (probability 0.78, confidence 0.73). A first pick,
    `claude-haiku-4.5`, fell back to Auto: the Free plan allows only Auto.
  - Result: heartbeat, `check` and `worker_done` in 41 seconds; Auto routed
    to `gpt-6-luna` at medium effort. It used 0.3 of the plan's 200 monthly
    AI credits (79.8k input tokens, 63.4k of them cached; 530 output).
    CodexBar's `Chat` window moved from 0% to 0.2%.
- [x] T006 Send the develop session the proposed launch steps for
  `~/.claude/rules/worker-dispatch.md` (FR-006).
  - Sent 2026-09-30: a "Copilot workers" section with the terminal path
    (`copilot --model auto --auto-tier <tier> --allow-all-tools
    --no-ask-user --no-auto-update`), declining the app install prompt with
    `n`, and closing the terminal after `worker_done`, since
    `worker-release` keeps a terminal Orca did not create.

## Phase 4: Finish

- [ ] T007 Merge `develop`, run `npm run verify`, pass the develop merge
  review by a provider other than Claude Code, commit the review record and
  finish with `git flow feature finish copilot-option`.
