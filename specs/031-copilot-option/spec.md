# Feature Specification: Copilot as a Reviewer and a Model-Choice Option

**Feature Branch**: `feature/copilot-option`

**Created**: 2026-09-30

**Status**: In progress

**Linear issue**: CHE-60

**Input**: Linear issue CHE-60, "Add GitHub Copilot as a reviewer and a
model-choice option", and the develop session's brief of 2026-09-30. The user
added the GitHub Copilot CLI 1.0.88 to this laptop on the Copilot Free plan.
GitHub bills Copilot usage in AI credits; the free plan's monthly allowance
equals about 50 chat or agent requests, and the Copilot CLI draws from it.
The user decided the same day to use Copilot as a reviewer and as a
model-choice candidate, to read its allowance with CodexBar's Copilot provider
after a short security check of that provider, and to start Copilot workers
through an Orca terminal, since Orca's model catalog does not cover the
Copilot CLI.

## Clarifications

### Session 2026-09-30

The develop session answered for the user.

- Q: The constitution, the text `npm run workflow` prints and
  `docs/architecture.md` repeat AGENTS.md's "other provider (Claude Code or
  Codex)". Change only AGENTS.md? → A: Change the phrase in all four places
  to name a provider other than the implementer's (Claude Code, Codex or
  Copilot); keep the Copilot preference in AGENTS.md only; raise the
  constitution from 2.4.0 to 2.5.0 with commitizen in a `feat` commit.
- Q: The security check passed with one low finding: CodexBar sends any
  GitHub token it gets. Which token does it get? → A: A token from GitHub's
  device login with the OAuth app and `read:user` scope that CodexBar's own
  Copilot login uses, saved unprinted in
  `~/.config/verbose-broccoli/providers/copilot.env` (mode 600).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Copilot's allowance is evidence for model choice (Priority: P1)

An orchestrator choosing a worker with the code plugin's `model-choice` skill
reads Copilot's remaining allowance with CodexBar, the same way it reads the
other providers' limits, and offers Copilot models as candidates.

**Independent Test**: Run the documented `codexbar usage --provider copilot`
call under its limits and get the allowance without account identity in the
output that goes into evidence.

**Acceptance Scenarios**:

1. **Given** the security check of CodexBar's Copilot provider passed, **When**
   an orchestrator follows `references/model-choice.md`, **Then** it runs one
   Copilot `usage` call with only the Copilot credential and strips account
   identity before the output goes into evidence.
2. **Given** the check fails, **When** the feature ends, **Then** the
   reference does not allow the Copilot call and the report says why.
3. **Given** an orchestrator builds candidates, **When** it lists Copilot's
   models, **Then** it takes them from the Copilot CLI and is told that the
   small allowance suits small tasks and reviews.

### User Story 2 - Copilot can give the final review (Priority: P1)

AGENTS.md's review rule names the providers generally (Claude Code, Codex,
Copilot) and prefers Copilot for a feature's final review when Claude Code
and Codex both implemented parts of it.

**Independent Test**: Read the review rule; it names three providers and the
Copilot preference in one short change.

### User Story 3 - Copilot workers start through a terminal (Priority: P2)

An orchestrator starts a Copilot worker with `orca-ide terminal create
--command "copilot --model <model> ..."`, waits for the TUI, and hands it a
task with `worker-start --terminal`.

**Independent Test**: One short worker on a trivial task sends a heartbeat,
runs `check`, and sends `worker_done`; the requests it used are counted.

### Edge Cases

- The Copilot allowance is used up: the candidate is dropped until it resets,
  like any other window at 100% used.
- CodexBar cannot read the allowance: the failure is evidence, not a guess.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A read-only security check of CodexBar 0.69.0's Copilot provider
  code path (credential source, network destinations, storage and output)
  MUST precede any use of `codexbar usage --provider copilot`, with evidence
  for each finding.
- **FR-002**: Only if the check passes, `references/model-choice.md` MUST
  allow the Copilot `usage` call under the same limits as the other
  providers: one provider per call, only the `usage` command, only the
  Copilot credential, no account identity in messages or logs.
- **FR-003**: `references/model-choice.md` MUST add Copilot as a candidate:
  its models as the Copilot CLI lists them, its remaining allowance from
  CodexBar as evidence, and the guidance that its small allowance suits small
  tasks and reviews.
- **FR-004**: AGENTS.md's review rule MUST name the providers generally
  (Claude Code, Codex, Copilot) and prefer Copilot for the final review when
  Claude Code and Codex both implemented parts of a feature, in a small
  change.
- **FR-005**: One Copilot worker MUST complete a trivial task end to end
  through the terminal path (heartbeat, `check`, `worker_done`), with the
  requests it used counted.
- **FR-006**: The develop session MUST receive proposed launch steps for
  `~/.claude/rules/worker-dispatch.md`; this feature does not edit that file.

## Success Criteria *(mandatory)*

- **SC-001**: The security check report states pass or fail with evidence.
- **SC-002**: The model-choice reference and AGENTS.md changes pass
  `npm run verify`.
- **SC-003**: The test worker's result and request count are recorded in
  `tasks.md`.

## Assumptions

- CodexBar stays at the reviewed 0.69.0 release; a new release needs a new
  check.
- The Copilot CLI stays at 1.0.88 for the test; its model list is read at
  choice time, never written into the repository.
