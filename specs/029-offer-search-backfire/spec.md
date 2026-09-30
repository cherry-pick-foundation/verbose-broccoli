# Feature Specification: Offer Search Through Backfire

**Feature Branch**: `feature/offer-search-backfire`

**Created**: 2026-09-30

**Status**: Planned

**Linear issue**: CHE-49

**Input**: Linear issue CHE-49, "Route the chat plugin's credit-offer search
through backfire's shared provider order", and the develop session's task
brief of 2026-09-30. The chat plugin's 6-hour credit-offer search
(`packages/credit-offers`, feature 021) makes one Jev judgment per run and
sends it to OpenRouter through `jev_ultrafast.model`. The user decided on
2026-09-30 that every plugin follows backfire's one shared provider order
(feature 025, CHE-46: today OpenRouter, then Hive; CHE-51 adds Cloudflare and
Vercel at the front), so the offer search sends its judgment through
backfire. The web agent (`packages/jev-ultrafast`) stays on OpenRouter,
because each of its steps needs the real Jev.

## Clarifications

### Session 2026-09-30

The develop session answered.

- Q: Backfire reads each profile's key from the file its `credential_file`
  names (`packages/backfire/src/backfire/config.toml`), so `--env-file` for
  provider keys and `JEV_PROVIDER` have no effect once the search uses
  backfire. Should the Orca precheck still pass the provider key files?
  → A: No. The precheck passes only `github.env` and drops `JEV_PROVIDER`.
  The final command goes to the develop session for approval after the
  finish.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The search's judgment follows backfire's order (Priority: P1)

The scheduled search finds new offers in a 6-hour block and asks for one
judgment. The judgment goes through backfire, so it uses the first profile in
backfire's order that has credit, and moves to the next profile when a
provider answers that the balance is insufficient.

**Why this priority**: It is the user's decision and the whole feature.

**Independent Test**: With backfire's provider factory replaced by a fake,
run the search on a block with candidates and check that the fake received
one judgment with the same state and questions as before, and that the
exit status and printed lines are unchanged.

**Acceptance Scenarios**:

1. **Given** a block with one qualifying and one excluded candidate, **When**
   the search runs, **Then** backfire receives one judgment with one choice
   question per candidate, the search prints one line per candidate and
   `jev_calls=1`, and exits 0.
2. **Given** a block whose candidates are all judged excluded, **When** the
   search runs, **Then** it exits 1.
3. **Given** a block with no candidate, **When** the search runs, **Then** it
   sends no judgment, prints `jev_calls=0` and exits 1.

### User Story 2 - Failures keep status 3 (Priority: P1)

When backfire cannot give a valid answer, the search ends with status 3 and
a message that names the failure without any key, as before.

**Why this priority**: The Orca precheck reads status 3 as an error to look
at; a changed status would hide failures or raise false alarms.

**Independent Test**: Make the fake provider raise each failure, or return
an invalid answer, and check status 3 and the message.

**Acceptance Scenarios**:

1. **Given** a missing or unreadable key file, no profile with credit, a
   provider error or a timeout, **When** the search judges, **Then** it exits
   3 and prints the failure and `jev_calls=0`, as a failed request does
   today.
2. **Given** an answer that is not a valid choice over `qualifies` and
   `excluded`, **When** the search validates it, **Then** it exits 3.

### User Story 3 - The operator runs it without provider key files (Priority: P2)

The operator runs the search by hand or from the Orca automation with only
the optional `github.env`; the skill and the architecture document say so.

**Acceptance Scenarios**:

1. **Given** the `credit-offers` skill, **When** the operator reads the Run
   section, **Then** it shows a command without `JEV_PROVIDER` or a provider
   key file and says backfire reads its own keys.

### Edge Cases

- Backfire switches profiles during the judgment: this is still one judgment,
  so the search prints `jev_calls=1`.
- CodexBar is missing from `PATH`: backfire treats credit as unknown and uses
  the profile, as feature 025 defines.
- Argument errors exit 2 before backfire is touched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The search MUST send its judgment through backfire's library
  (`backfire.providers.provider_factory`) and MUST contain no provider code
  of its own. It depends on the `backfire` workspace package instead of
  `jev-ultrafast`.
- **FR-002**: The judgment MUST keep its meaning: the same state (each
  candidate's slug, title, provider, category, amount and source URL), one
  choice question per candidate with the same `qualifies` and `excluded`
  criteria and instructions, and one judgment per run.
- **FR-003**: The search MUST send PyModel's default model name
  (`jev-latest`), as backfire's server does by default.
- **FR-004**: Each answer MUST be validated with PyModel's upstream
  `validate_choice` over `qualifies` and `excluded`; an invalid answer ends
  with status 3.
- **FR-005**: Exit statuses MUST stay: 0 at least one strong offer
  (notified with `--notify`), 1 no strong offer, 2 invalid arguments, 3 a
  tracker, GitHub, backfire, validation or notification failure. No message
  may show a key.
- **FR-006**: The search MUST NOT use backfire's education mode; the offers
  are public data.
- **FR-007**: The search MUST NOT read `JEV_PROVIDER` or provider keys from
  its environment; `GITHUB_TOKEN` from `github.env` stays optional.
- **FR-008**: The `credit-offers` skill and `docs/architecture.md` MUST
  describe the new run command and that backfire reads the provider keys.
- **FR-009**: After the develop session approves it, the Orca automation
  "Free API credit offers" MUST run the precheck with only `github.env`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `npm run test:credit-offers` passes offline, with cases for
  statuses 0, 1, 2 and 3 on the backfire path.
- **SC-002**: A live run on a past block with at least one candidate goes
  through backfire and prints `jev_calls=1`; the report states the number
  of provider calls.
- **SC-003**: The automation's precheck is the approved command.
- **SC-004**: `packages/credit-offers` names no provider, URL or key
  variable for Jev.

## Assumptions

- Feature 021's contract (`specs/021-chat-jev-ultrafast/contracts/`) stays
  as the record of that feature; this spec records the change.
- The develop worktree's virtual environment already holds `backfire`, so
  the automation's `uv run --no-sync` can import it after the lock file
  changes.
