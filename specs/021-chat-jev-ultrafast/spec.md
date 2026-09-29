# Feature Specification: Jev Ultrafast web agent and API credit offer search for the chat plugin

**Feature Branch**: `feature/chat-jev-ultrafast`

**Created**: 2026-09-30

**Status**: Draft

**Linear issue**: CHE-41

**Input**: Linear issue CHE-41, "Chat plugin: adopt Jev Ultrafast with Vercel
AI Gateway for a scheduled API credit promotion search", with the user's
decisions of 2026-09-30 and the brief with which the orchestrator of the
`develop` worktree started this feature. The chat plugin gets a Jev-based web
agent by adopting Browser Use's Jev Ultrafast
(<https://github.com/browser-use/jev-ultrafast>, MIT) as an upstream
dependency with the smallest patch. The patch adds provider selection for its
Jev calls, with TypeSafe and Vercel AI Gateway as providers and vendor details
in configuration; the Vercel request format follows the Vercel carrier of
`jkudish/jev-mcp` 0.9.0. The first use is a scheduled search for API credit
offers, run as an Orca automation on the user's laptop, that notifies the
user only when a strong offer appears and saves nothing. Two refinements
reached this feature on 2026-09-30 through the `develop` session, both user
decisions: a strong offer is one that costs nothing (free credits, unlimited
free usage) and states no time limit or end date, which replaces the earlier
"high multiplier" top-up bonus; and Jev Ultrafast uses Orca's built-in
browser by default instead of launching its own Chrome, again with the
smallest patch, keeping plain Chrome as a fallback only if the patch stays
small.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hear about a new free API credit offer (Priority: P1)

The user wants to know, without checking any site, when a new API credit
offer appears that costs nothing to claim and states no time limit or end
date. Every few hours the laptop looks at the offers that appeared since the
last look and shows a desktop notification only when at least one such offer
is among them. Nothing is written to disk.

**Why this priority**: It is the feature's first use and the result the user
asked for.

**Independent Test**: Run the search over a past period that contains a known
qualifying offer and over one that contains only excluded offers; the first
shows a notification naming the offer, the second shows none.

**Acceptance Scenarios**:

1. **Given** an offer that first appeared in the tracker during the last
   period, costs nothing and states no time limit or end date, **When** the
   scheduled search runs, **Then** the user gets one desktop notification
   naming the offer's title, provider, amount and source link.
2. **Given** new offers in the period that all state an end date, a trial
   period or a required payment, **When** the search runs, **Then** no
   notification appears and no agent session starts.
3. **Given** no new offer in the period, **When** the search runs, **Then**
   it ends without a Jev call and without a notification.
4. **Given** any run, **When** it ends, **Then** no file, record or cache
   entry has been written by the search.

---

### User Story 2 - Choose the provider for Jev calls (Priority: P1)

An operator chooses whether Jev Ultrafast's Jev calls go to TypeSafe or to
Vercel AI Gateway, whose monthly $5 credit covers light use. The providers'
addresses, headers, model names and credential variable names live in
configuration, not in code, and credentials stay in a file only the user can
read.

**Why this priority**: The offer search and the web agent both depend on
Jev calls, and the user chose Vercel AI Gateway to keep them within its free
monthly credit.

**Independent Test**: With a stub server standing in for each provider,
select each provider in turn and check that the request has that provider's
address, headers and body, and that the answer reaches the caller in the
same form for both.

**Acceptance Scenarios**:

1. **Given** the Vercel provider is selected and its key is set, **When**
   Jev Ultrafast makes a Jev call, **Then** the request goes to Vercel AI
   Gateway's evaluation-model endpoint in the format of jev-mcp 0.9.0's
   Vercel carrier, and the answer is converted to TypeSafe's answer form.
2. **Given** the TypeSafe provider is selected, **When** a Jev call is made,
   **Then** the request is the one upstream Jev Ultrafast sends today.
3. **Given** the selected provider's key is missing, or the provider name is
   unknown, **When** a Jev call is attempted, **Then** it fails before any
   network request with a message that names the missing variable or the
   unknown provider and never contains a key.
4. **Given** a provider answer that is malformed, **When** Jev Ultrafast
   validates it, **Then** no browser action runs and no offer is reported.

---

### User Story 3 - Run the web agent in Orca's built-in browser (Priority: P2)

An agent working in an Orca worktree asks the Jev Ultrafast web agent to
reach a goal on a web page. By default the agent opens its own tab in Orca's
built-in browser, works only in that tab, and closes it at the end. With an
explicit setting it uses plain Chrome as upstream does.

**Why this priority**: It makes the chat plugin's web agent usable where the
user works, without a separate Chrome, but the first use does not need a
browser.

**Independent Test**: With no model calls, open a tab through the patched
browser layer, read the page's controls, type into a field, click, and close
the tab; then confirm the tab is gone and no other tab was touched.

**Acceptance Scenarios**:

1. **Given** Orca is running, **When** the web agent starts, **Then** it
   opens a new tab in the current worktree through Orca and attaches only to
   that tab.
2. **Given** the web agent finishes or fails, **When** it closes, **Then**
   its tab is closed and its browser connection process has stopped.
3. **Given** the Chrome setting, **When** the web agent starts, **Then** it
   behaves as upstream Jev Ultrafast does.

---

### User Story 4 - A schedule taken from history (Priority: P2)

The user can see why the search runs at its interval: the past offers that
meet the definition, when each first appeared, the average interval between
them, and how long they stayed listed.

**Why this priority**: The user set the interval rule; the records make the
choice checkable.

**Independent Test**: Recompute the average from the recorded data and
compare it with the recorded interval.

**Acceptance Scenarios**:

1. **Given** the feature records, **When** a reader opens them, **Then** they
   find the data, the definition of a strong offer, the calculation and the
   chosen interval.

### Edge Cases

- The tracker or GitHub is unreachable, or GitHub's rate limit for
  unauthenticated requests is used up: the run fails without a notification
  and says why; Orca records it as a skipped run.
- The tracker's index names an offer that has since been removed: only offers
  still listed as active at the end of the period count.
- The laptop sleeps through one or more scheduled times: the next run looks
  only at the latest full period, so offers that first appeared in the missed
  periods are not reported.
- The provider rejects the key or returns an error: no offer is reported and
  the error names the provider but not the key.
- Orca is not running, or `orca` is not on `PATH`, when the web agent starts
  in Orca mode: it stops with a message that says so and suggests the Chrome
  setting.
- Another session uses Orca's browser at the same time: the web agent never
  attaches to a tab it did not open; browser jobs run one at a time.
- Orca's tab is not drawn on screen: screenshots and mouse-wheel scrolling can
  stall there (seen in testing on 2026-09-30); the skill documents this, and
  the patch leaves upstream's scrolling unchanged (user decision).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST contain Jev Ultrafast from its upstream
  revision `1231850a0bf1a0c0341fe408ef1668dbbfdfac46`, with a record of that
  revision, each copied file's original hash and every difference from
  upstream with its reason.
- **FR-002**: Jev Ultrafast's Jev calls MUST go to the provider selected by
  configuration: TypeSafe or Vercel AI Gateway. Each provider's address,
  headers, model name and credential variable name MUST come from a
  configuration file.
- **FR-003**: The Vercel request and answer conversion MUST follow jev-mcp
  0.9.0's Vercel carrier, which that release takes from its locked dependency
  `@jkudish/jev-agent-tools` 0.1.2.
- **FR-004**: With no provider selected, Jev calls MUST behave as upstream
  does (TypeSafe).
- **FR-005**: Credentials MUST stay in a file with mode `0600` outside the
  repository and MUST NOT appear in output, errors, records or commits. The
  skills tell the user how to create the file with that mode; uv passes it to
  the process, and the feature's code never reads or writes the file.
- **FR-006**: By default the web agent MUST use Orca's built-in browser: open
  its own tab through Orca, attach only to that tab through the tab's own
  browser control address, and close the tab through Orca. A setting MUST
  select upstream's Chrome behavior instead.
- **FR-007**: The chat plugin MUST gain skills for the web agent and for the
  offer search, each stating how to run it, what it needs, and its limits.
- **FR-008**: The offer search MUST read the public freetokens tracker over
  plain HTTP, without a browser, and find the offers that first appeared in
  the tracker's offer index during the latest full period.
- **FR-009**: The search MUST drop offers that are not active or that state an
  end date, and MUST ask Jev, in one call per run, whether each remaining
  offer costs nothing to claim and states no time limit or end date.
- **FR-010**: The search MUST notify the user with a desktop notification
  only when at least one offer passes, and MUST write nothing to disk.
- **FR-011**: The search MUST print how many Jev calls it made, so paid calls
  can be counted.
- **FR-012**: An Orca automation MUST run the search on the laptop every 6
  hours, starting an agent session only when the search finds a strong offer.
  It MUST be created only after the user approves its description.
- **FR-013**: The feature records MUST hold the offer history data, the
  definition of a strong offer, the average-interval calculation and the
  observed listing durations.
- **FR-014**: The repository's documents and constitution MUST describe the
  chat plugin's new skills.
- **FR-015**: Tests MUST not call paid services; the Vercel path is tested
  against a stub.

### Key Entities

- **Offer**: one tracker entry: slug, title, provider, category, amount text,
  end date (or none), source link, status.
- **Block**: the time range a run looks at; the latest full 6-hour block of
  the day in the user's time zone.
- **Provider**: a named Jev endpoint with protocol, address, headers, model
  and credential variable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a past period with a known qualifying offer, one run
  produces one notification naming it; for a period with none, no
  notification appears. Until the user adds a key, this is checked with a
  stub provider standing in for Jev.
- **SC-002**: A run with no new offers finishes in under 30 seconds and makes
  no Jev call; a run with candidates makes exactly one Jev call.
- **SC-003**: At the schedule of 4 runs a day, Jev calls stay below 125 a
  month, well inside Vercel's $5 monthly credit at its listed Jev price.
- **SC-004**: The recorded average interval can be recomputed from the
  recorded data to the same value.
- **SC-005**: Every difference from upstream Jev Ultrafast is listed in its
  record, and the offline tests cover both providers and both browser modes.

## Assumptions

- The freetokens tracker (<https://github.com/luongnv89/freetokens>, MIT)
  stays public and keeps its generated `index.json` with an end-date field.
  Its history is the source for both the schedule and the search, so the
  "appearance" of an offer means its first appearance in the tracker's
  index, not the provider's own launch date.
- The desktop notification uses the laptop's GNOME notification service
  through `notify-send`.
- On 2026-09-30 the user had no Vercel or TypeSafe key yet and chose to skip
  the live provider check: the Vercel path is tested against a stub, and the
  credential file (`~/.config/verbose-broccoli/chat/jev.env`, mode `0600`,
  holding `AI_GATEWAY_API_KEY` or `TYPESAFE_API_KEY`) stays documented for
  later. Until the key exists, a scheduled search that has candidates fails
  closed and Orca records a skipped run; the test notification exercises the
  notification path with a sample offer.
- The user's 2026-09-30 rule applies: the feature reports its net new lines
  of locally written code, counting neither upstream copies nor tests, and
  asks before going over 300.
- The chat plugin's skills run in local Codex CLI or Claude Code sessions,
  including Orca automations, from the repository's uv workspace. Shipping a
  self-contained chat plugin build is out of scope.
- The browser patch does not change how Jev Ultrafast scrolls or takes
  screenshots: on 2026-09-30 the user chose to keep upstream's mouse-wheel
  scrolling and to document that scroll steps and screenshots can time out
  unless the tab is on screen. The web agent's text helper (for typing
  values) keeps upstream's separate configuration.
- `packages/backfire` is out of scope; CHE-39 adds a Vercel provider there.
