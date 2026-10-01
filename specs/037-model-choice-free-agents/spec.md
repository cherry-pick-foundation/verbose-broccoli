# Feature Specification: Free-Quota Agents in Model Choice

**Feature Branch**: `feature/model-choice-free-agents`

**Created**: 2026-10-01

**Status**: In progress

**Linear issue**: CHE-70

**Input**: Linear issue CHE-70, "Add free-quota agents to model choice,
chosen by difficulty and remaining usage with Jev judgments", and the develop
session's brief of 2026-10-01. The goal is to use the free quotas of the
locally installed agents beyond the Claude and Codex subscriptions. The user
decided the same day:

- Add Antigravity (`agy` 1.2.14), Grok (`grok` 1.0.46) and Cursor
  (`cursor-agent` 2026.09.28) as model-choice candidates, next to Codex,
  Claude Code, Copilot and OMP. All three are signed in.
- Choose model and reasoning effort dynamically from the task's difficulty and
  every candidate's remaining usage. The difficulty scale has five levels
  (very easy, easy, medium, difficult, very difficult); `npm run workflow`
  reports one for observed changes (policy `coding-difficulty/1`). There is
  still no fixed table from difficulty to a model.
- Model-choice judgments use Jev-family models only, never a general model
  such as DeepSeek. Backfire's shipped order is OpenRouter Jev, then Hive
  DeepSeek, so model-choice calls are pinned to the Jev profile.
- MiniMax Code (`mcode`) is used only in scripted runs (`mcode exec`),
  because Orca does not supervise it.

## Clarifications

### Session 2026-10-01

- Q: May Antigravity, Grok or Cursor give develop merge reviews? → A: Yes,
  all three (the user).
- Q: May they also give main merge reviews? → A: No; main merge reviews keep
  Claude Code, Codex or Copilot (the user).
- Q: Backfire's `serve-mcp --profile` option exists only on CHE-69's branch.
  → A: CHE-69's orchestrator expects its finish on 2026-10-02 and agreed that
  this feature cherry-picks its commit unchanged; neither feature edits those
  lines again without telling the other.
- Q: Jev escaped (`investigate`) on the Cursor readiness test's model, since
  the free plan's allowed models were unknown. → A: The user chose
  `composer-2.5`. Cursor refused it ("Named models unavailable. Free plans
  can only use Auto."), so the test ran on `auto`, the only model the free
  plan allows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Model choice weighs difficulty and usage with Jev only (Priority: P1)

An orchestrator choosing a worker with the code plugin's `model-choice` skill
gives backfire the task's difficulty and every candidate's remaining usage as
evidence, and the judgment runs on a Jev model only.

**Independent Test**: Run one model choice for a sample task; its evidence
names the difficulty level and each candidate's usage, and its answer names
the `openrouter` provider and a Jev model.

**Acceptance Scenarios**:

1. **Given** a task, **When** an orchestrator follows
   `references/model-choice.md`, **Then** the evidence states the task's
   difficulty level and the remaining usage, or "unknown", of every candidate.
2. **Given** OpenRouter has no credit, **When** the orchestrator calls
   backfire, **Then** the call fails instead of falling back to another
   profile, and the orchestrator asks the user.

### User Story 2 - Free-quota agents are candidates (Priority: P1)

The reference lists Antigravity, Grok and Cursor as candidates with their live
model catalogs, usage reads and launch paths, and each passed an Orca
readiness test.

**Independent Test**: For each agent, one worker on a trivial task sends a
heartbeat, runs `check`, and sends `worker_done`.

### User Story 3 - Free-quota agents may give develop merge reviews (Priority: P2)

AGENTS.md's review rule lets Antigravity, Grok or Cursor give a develop merge
review when it is not the implementer's provider; main merge reviews keep
Claude Code, Codex or Copilot.

**Independent Test**: Read the review rule and the texts that repeat it.

### Edge Cases

- A candidate's window is 100% used: the candidate is dropped until its
  reset, as for the other providers.
- A usage read fails or does not exist (Antigravity, OMP's providers): the
  evidence says "unknown"; nobody guesses.
- Cursor's free plan refuses named models: only `auto` is a Cursor candidate
  while the plan stays free.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `references/model-choice.md` MUST add Antigravity, Grok and
  Cursor as candidates, built from their live catalogs (`agy models`,
  `grok models` with the efforts in Grok's model cache, `cursor-agent
  models`), with each one's launch path.
- **FR-002**: The reference MUST read Grok's weekly and Cursor's monthly
  usage from `orca account list --json` with account identity removed, and
  treat Antigravity's usage as unknown.
- **FR-003**: The evidence MUST include the task's difficulty level; the
  reference keeps "no table from difficulty to a model".
- **FR-004**: Model-choice judgments MUST run on the Jev profile only
  (`backfire serve-mcp --profile openrouter`), and the orchestrator MUST check
  the answer's `provider` and `model`. When the Jev profile cannot answer, it
  asks the user instead of falling back.
- **FR-005**: The reference MUST say that MiniMax Code is not a candidate for
  workers, reviewers or orchestrators and runs only as `mcode exec`.
- **FR-006**: Tasks that read student data MUST keep only Claude Code and
  Codex candidates.
- **FR-007**: AGENTS.md MUST let Antigravity, Grok or Cursor give develop
  merge reviews; the constitution's develop merge sentence (a `feat` minor
  bump), the text `npm run workflow` prints with its test, and
  `docs/architecture.md` MUST say the same.
- **FR-008**: The difficulty sentence `npm run workflow` prints MUST say that
  the level is evidence for the model choice, not a model by itself.
- **FR-009**: Each new agent MUST pass an Orca readiness test (heartbeat,
  `check`, `worker_done`).
- **FR-010**: `~/.claude/rules/worker-dispatch.md` MUST gain the launch notes
  for the three agents, after a dated backup.

## Success Criteria *(mandatory)*

- **SC-001**: A sample model choice records difficulty and usage in its
  evidence and `openrouter` with a Jev model in its answer.
- **SC-002**: The readiness tests' results are recorded in `tasks.md`.
- **SC-003**: `npm run verify` prints VERIFIED.

## Assumptions

- The agents stay at the tested versions (agy 1.2.14, grok 1.0.46,
  cursor-agent 2026.09.28, Orca 1.4.218); their model lists are read at
  choice time, never written into the repository.
- Cursor stays on its free plan, which allows only `auto`.
