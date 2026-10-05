# Feature Specification: Coordinator compaction continuity

**Feature Branch**: `feature/compaction-continuity`
**Created**: 2026-10-05
**Status**: Specified
**Linear issue**: CHE-88
**Input**: Restore standing notes and coordinator state after compaction; count session compactions and notify the user at configurable thresholds.

## User Scenarios & Testing

### User Story 1 - Recover current rules and work (Priority: P1)

A coordinator gets the complete standing notes and its current state on a fresh start and after compaction, so decisions and live ownership survive.

**Why this priority**: Lost notes caused coordinators to drift from the user's decisions.
**Independent Test**: Synthetic notes with a middle and end marker and mutable state are restored completely for both clients.

**Acceptance Scenarios**:

1. **Given** complete notes and state, **when** a session starts, resumes, clears or compacts, **then** the complete content is restored or an explicit full re-read instruction identifies every source.
2. **Given** missing state, **when** the hook runs, **then** it reports the absence and a coordinator can establish state without the hook writing private files.
3. **Given** a narrow worker in the same worktree, **when** it starts, **then** it receives neither the coordinator checkpoint contents nor ownership of its state.

### User Story 2 - Request a fresh coordinator (Priority: P2)

The user is notified when the current coordinator reaches its configured compaction count. The coordinator saves state and starts no new work while the user starts a replacement.

**Why this priority**: Context restoration alone does not prevent degradation over repeated compactions.
**Independent Test**: Separate synthetic transcripts reach main's first and develop/feature's second compaction without counting other sessions.

**Acceptance Scenarios**:

1. **Given** an owned session below threshold, **when** it compacts, **then** no restart notification appears.
2. **Given** an owned session at threshold, **when** it compacts, **then** it is told to update state and start no new work, and the desktop user receives a fresh-session notification.
3. **Given** a new coordinator replacing an old one, **when** it explicitly claims the state, **then** only its own transcript counts apply.
4. **Given** a worker that does not own state, **when** its transcript reaches threshold, **then** it neither receives a coordinator stop instruction nor triggers a coordinator notification.

### User Story 3 - Keep coordinator messages useful (Priority: P2)

Develop sends main questions and user-relevant outcomes. Main answers by convention, relays user decisions, and does not repeat verification or reply to routine status.

**Why this priority**: Routine exchanges consumed attention without advancing the work.
**Independent Test**: Inspect the short judgment rule for questions, merges, user blocks, finished features and acknowledgment-only heartbeats.

### Edge Cases

Missing or unreadable notes, state or transcripts must be named without inventing content or counts. Oversized context must require complete source reads rather than silently lose the middle. Notification failure must leave the save-state instruction visible. Subdirectory launches must resolve the worktree root. Malformed input must not produce private-data writes. A clear/new session must not inherit a durable counter. Transcript format changes are a documented compatibility limit.

## Requirements

### Functional Requirements

- **FR-001**: Restore complete standing notes and coordinator state after compaction and on startup/resume/clear in both supported clients; preserve existing Ponytail hooks.
- **FR-002**: Keep notes and state paths in one configuration place, ready for notes to move into the project.
- **FR-003**: Keep one mutable state per worktree coordinator, overwritten in place with decisions, holds/reasons, live owners, questions and next steps. Fresh coordinators explicitly claim it; hooks never claim or write it for workers.
- **FR-004**: Count the current session's compactions from the input transcript, without persistent counters or mixing other sessions.
- **FR-005**: Central thresholds initially equal main 1, develop 2 and feature orchestrators 2.
- **FR-006**: At threshold instruct the owning coordinator to save state and start no new work, then notify the desktop user to start a fresh session; never restart, kill or impose a time cap.
- **FR-007**: Narrow workers cannot own another coordinator's state or trigger its restart notification.
- **FR-008**: Missing sources and failed notifications remain visible; no private files, sealed continuity copies, hash manifests or network writes are produced by the hook.
- **FR-009**: Add the short main/develop judgment rule. Heartbeats need acknowledgment only.
- **FR-010**: Codex memories remain globally disabled; add no project override or global change.

### Key Entities

Standing notes are configured complete instruction sources. Coordinator state is one mutable worktree file with an explicit client/session owner. A session transcript supplies compaction events for that session. Thresholds determine when its coordinator asks for replacement.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Both clients restore all synthetic notes/state markers, including the middle and end, or explicitly require every full source read.
- **SC-002**: Main's first and develop/feature's second compaction produce the save-state instruction and notification; below-threshold sessions and narrow workers do not.
- **SC-003**: Replacing a coordinator and starting a separate session do not inherit the old session's count or grant worker ownership.
- **SC-004**: Acceptance leaves notes/state/transcripts unchanged and makes no private-data or external-service writes.

## Assumptions

The Linux desktop already provides notifications. Missing notification support is reported in context. Hook definitions are loaded by fresh client sessions after integration; this feature does not activate external clients. The coordinator explicitly records its client session owner in state after startup, as agreed with develop on 2026-10-05. A narrow worker never claims it. Completed tests and paid outputs keep normal immutable receipt storage.
