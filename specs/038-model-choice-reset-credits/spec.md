# Feature Specification: Reset Credits in Model Choice

**Feature Branch**: `feature/model-choice-reset-credits`

**Created**: 2026-10-01

**Status**: In progress

**Linear issue**: CHE-72

**Input**: Linear issue CHE-72, "Weigh usage-limit reset credits in model
choice", and the develop session's brief of 2026-10-01. CodexBar's Codex usage
reports `usage.codexResetCredits`: `availableCount` and `credits[]` with
`title`, `reset_type`, `status`, `granted_at` and `expires_at`. On 2026-10-01
it showed 2 available full resets, expiring 2026-10-22 and 2026-10-29; Claude
reported none. The user decided the same day:

- Reset credits are evidence for the model choice.
- Only the user spends reset credits. Agents use a limit fully, then stop and
  report to the develop session.
- Judgments use Jev only (the reference's pinned Jev profile).
- Account identity is stripped from CodexBar output; credit IDs are not
  needed in the evidence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Backfire sees reset credits (Priority: P1)

An orchestrator choosing a worker with the code plugin's `model-choice` skill
gives backfire Codex's reset-credit count and expiry dates, so Codex is not
steered away from early while it holds unused resets that expire.

**Independent Test**: Run one model choice for a sample task; its evidence
names the reset-credit count and expiry dates, and its answer names the
`openrouter` provider and a Jev model.

**Acceptance Scenarios**:

1. **Given** Codex reports `availableCount` 2, **When** an orchestrator follows
   `references/model-choice.md`, **Then** the evidence gives the count and each
   available credit's `expires_at`, and no account identity or credit ID.
2. **Given** a provider reports no reset credits (Claude), **When** the
   evidence is built, **Then** it says "none reported".

### Edge Cases

- A candidate's window is 100% used while credits exist: it is still dropped
  until its `resetsAt`, because only the user spends a credit.
- `usage.codexResetCredits` is missing for Codex: the evidence says "none
  reported"; nobody guesses.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `references/model-choice.md`, "Usage limits", MUST name reset
  credits as evidence with their source fields (`usage.codexResetCredits`,
  `availableCount`, `title`, `reset_type`, `status`, `granted_at`,
  `expires_at`) and give a command that reads them without account identity
  or credit IDs.
- **FR-002**: The reference MUST tell the orchestrator to give backfire the
  count and the expiry dates, and to report "none reported" for providers
  without credits.
- **FR-003**: The reference MUST say that only the user spends reset credits
  and that agents use a limit fully, then stop and report to the develop
  session; a credit does not keep a full window's candidate.

## Success Criteria *(mandatory)*

- **SC-001**: A sample model choice records reset credits in its evidence and
  `openrouter` with a Jev model in its answer.
- **SC-002**: `npm run verify` prints VERIFIED.

## Assumptions

- CodexBar 0.69.0 keeps the `codexResetCredits` field names.
