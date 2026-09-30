# Feature Specification: Backfire Provider Choice by Credit

**Feature Branch**: `feature/backfire-provider-credit`

**Created**: 2026-09-30

**Status**: Planned

**Linear issue**: CHE-46

**Input**: Linear issue CHE-46, "Backfire picks a provider with remaining
credit and switches when one runs out", and the develop session's task brief
of 2026-09-30. Backfire sends every judgment to one fixed provider profile,
chosen by `provider = "hive"` in `packages/backfire/src/backfire/config.toml`.
When that provider runs out of credit, every judgment fails; Vercel AI Gateway
and Cloudflare Workers AI both refused Jev on 2026-09-30 for lack of a paid
balance. The user decided on 2026-09-30 that backfire picks its profile
automatically: profiles are tried in a configured order; before a profile is
used, backfire reads its provider's remaining credit through the CodexBar
command-line tool (steipete/CodexBar, MIT, used unchanged) and skips a
profile whose provider reports a zero balance or a used-up limit; CodexBar
reads no balance for Hive or Cloudflare, so for them only the provider's own
"insufficient balance" answer counts; and when a provider gives that answer
during a run, backfire moves to the next profile. Own code stays small glue on
backfire's profile loader and PyModel's provider and retry classes.

## Clarifications

### Session 2026-09-30

The develop session relayed the user's answers.

- Q: What is the code plugin's default order? → A: Hive, then OpenRouter,
  then Vercel. Hive keeps today's answers; OpenRouter runs TypeSafe's Jev
  and has paid credit; Vercel goes last. No Cloudflare profile ships.
- Q: Which profiles may education mode use? → A: Hive, then OpenRouter. An
  OpenRouter education profile is added so education judgments keep working
  when Hive runs out; the user accepted that pseudonymized text may then go
  to OpenRouter and TypeSafe. Pseudonymization applies on every education
  profile, and the switch path is tested with it in place.
- Q: When is credit read? → A: Once per server process, right before a
  profile is first used and again at each switch; no per-call reads and no
  timer. If CodexBar is missing or fails, the profile is used and the log
  says so.
- Decided without a question and confirmed: each result's `provider` field
  names the profile that answered, and every skip and switch is logged.

Later the same day the user replaced the first two answers, in three
messages the develop session relayed:

- Order: Cloudflare, Vercel, OpenRouter, Hive, for both modes.
- One set of rules for every plugin: both modes read one order and one set
  of profiles from one configuration, so the two cannot drift; only
  pseudonymization and the response cache differ. The user approved
  pseudonymized student text going to Cloudflare, Vercel and
  OpenRouter/TypeSafe. The chat plugin has no backfire server, so nothing is
  built for it here.
- Cloudflare runs one of Cloudflare's own Workers AI models standing in for
  Jev, within the free allowance of 10,000 neurons a day, through
  system-one-adapter on Cloudflare's OpenAI-compatible endpoint. Jev on
  Cloudflare answered 402 on 2026-09-30, so there is no Jev profile there.
  Models that need paid billing are excluded.
- Vercel uses only its free credit, which refills regularly. Its free tier
  refused Jev on 2026-09-30, so Vercel also runs a free-tier model standing
  in for Jev through system-one-adapter on Vercel's OpenAI-compatible
  endpoint.
- The user picks the Cloudflare and Vercel models from researched options.
- The skip and switch rules stay; a used-up free allowance or free credit
  counts as insufficient balance.

After the research ([research.md](research.md)), the user decided:

- Measure all seven candidates (Cloudflare: Gemma 4 26B A4B, gpt-oss-120b,
  gpt-oss-20b, Qwen3 30B A3B; Vercel: gpt-oss-120b, gpt-oss-20b, Gemini 2.5
  Flash-Lite) on the full 111-decision set before choosing, then run only
  function checks on the chosen models. This work, the Cloudflare and Vercel
  profiles, the account-ID fill and the text-based switch on Cloudflare's
  code 3036 move to a new feature, Linear CHE-51, which starts from
  `develop` after this one merges.
- Delete backfire's Jev-on-Vercel provider (`vercel.py`) and its profile.
- Until CHE-51 adds its profiles, the shared order is OpenRouter, then Hive.
- The offer search in `packages/credit-offers` moving onto backfire is a
  separate feature too; it is out of scope here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A profile without credit is skipped (Priority: P1)

An agent asks backfire for a judgment. The first profile in the order belongs
to a provider that CodexBar reports as having a zero balance or a used-up
limit. Backfire does not send the judgment there; it uses the next profile
in the order, and the result says which profile answered.

**Why this priority**: It is the user's decision and prevents a failed call
to a provider known to be empty.

**Independent Test**: With a synthetic order of two profiles, a stand-in
`codexbar` that prints saved CodexBar JSON with a zero balance for the first,
and a local fake provider for the second, one judgment reaches only the
second provider and its result names the second profile.

**Acceptance Scenarios**:

1. **Given** CodexBar reports a zero balance for the first profile's
   provider, **When** a judgment runs, **Then** the first provider receives
   no request, the second answers, the result names the second profile, and
   the log records the skip.
2. **Given** CodexBar reports a used-up limit (a rate window at 100% used)
   for the first profile's provider, **When** a judgment runs, **Then** the
   first profile is skipped the same way.
3. **Given** CodexBar reports a positive balance, **When** a judgment runs,
   **Then** the first profile answers.
4. **Given** CodexBar is missing, times out, fails or prints output backfire
   cannot read, **When** a judgment runs, **Then** the first profile is used
   and the log says its credit is unknown.
5. **Given** a profile names no CodexBar provider, **When** it is chosen,
   **Then** CodexBar is not run for it.

### User Story 2 - A provider that runs out mid-run hands over (Priority: P1)

A profile is in use and its provider answers "insufficient balance" to a
judgment. Backfire sends the same judgment to the next profile in the order
and keeps using that profile for later judgments in the session.

**Why this priority**: It is the user's decision, and it is the only
protection for providers that CodexBar cannot read, such as Hive.

**Independent Test**: With two local fake providers, the first answering its
profile's insufficient-balance status, one judgment gets its answer from the
second provider; a second judgment goes straight to the second.

**Acceptance Scenarios**:

1. **Given** the provider in use answers a status its profile lists as
   insufficient balance, **When** a judgment runs, **Then** the same judgment
   is sent to the next profile, whose answer is returned and named in the
   result, and the log records the switch.
2. **Given** a switch happened, **When** the next judgment runs, **Then** it
   goes to the new profile without trying the earlier one again.
3. **Given** the next profile names a CodexBar provider, **When** backfire
   switches to it, **Then** its credit is read first and it is skipped if it
   has none.
4. **Given** the last profile in the order answers insufficient balance or
   every remaining profile is skipped, **When** a judgment runs, **Then** the
   judgment fails with an error that says no profile in the order has credit.
5. **Given** a provider answers any other error, such as an invalid key, a
   bad request or retries that ran out, **When** a judgment runs, **Then**
   backfire does not switch and returns that error as today.
6. **Given** several judgments are in flight when the provider runs out,
   **When** each gets the insufficient-balance answer, **Then** backfire
   moves on by one profile only, and each judgment is re-sent to it.

### User Story 3 - Both modes share one order (Priority: P1)

The work plugin runs backfire with `--education`, which pseudonymizes
question text before it leaves. It reads the same order and profiles as the
code plugin, from one configuration, so the two cannot drift; only
pseudonymization and the response cache differ.

**Why this priority**: The user wants one set of provider rules for every
plugin, and a switch in education mode must still send only pseudonymized
text.

**Independent Test**: Education mode loads the same order and profiles as
the code plugin; a switch from its first profile to its second sends the
second provider only pseudonymized text.

**Acceptance Scenarios**:

1. **Given** education mode, **When** its profiles are loaded, **Then** they
   are the shared order and profiles.
2. **Given** education mode and a switch, **When** the judgment is re-sent,
   **Then** the next provider receives only pseudonymized text, the
   judgment is pseudonymized once, and the replacement text is restored in
   the answer as before.

### User Story 4 - The operator guide explains the order (Priority: P2)

An operator reads `docs/backfire.md` to learn the default order, how to
change it, how CodexBar is used and what a skip or switch looks like.

**Why this priority**: The guide is the only operator documentation.

**Independent Test**: The guide names the order key, the shipped orders,
the two new profile fields, CodexBar's role and limits, and the new error.

**Acceptance Scenarios**:

1. **Given** the updated guide, **When** an operator wants another order,
   **Then** the guide shows the operator-file key that sets it.

### Edge Cases

- A profile that the order names but no configuration defines is a
  configuration error (`backend_not_configured`), found when the profiles
  are loaded.
- A missing or invalid key file is a configuration error, as today, and is
  not treated as a lack of credit.
- Both plugins read the one operator file, as they do today for
  `provider`; an operator `order` replaces the shared order of both, and the
  guide says so.
- Credit is read at most once per profile per server process, right before
  that profile is first used; backfire never returns to a skipped or
  exhausted profile within the process. A new client session starts a new
  process and starts again from the top of the order.
- CodexBar receives the profile's key only as an environment variable named
  by the profile's `credential`; backfire never writes it to CodexBar's
  configuration file, a command line or a log.
- The insufficient-balance answer is recognized by HTTP status only. Hive
  documents 405 for an exhausted balance; Cloudflare answered 402 on
  2026-09-30; 402 (Payment Required) is the default for other profiles.
  The answers for a used-up Cloudflare free allowance and Vercel free
  credit are in research.md; CHE-51 handles them with its profiles.
- PyModel's optional response cache keys entries by provider name; the
  name becomes the profile's name, so answers from different profiles are
  kept apart.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The shipped configurations MUST list profiles in an `order`
  array instead of a single `provider`. The operator file MAY set its own
  `order`, which replaces the shipped one, and MAY add or replace profiles
  as today. Every name in the order MUST resolve to a valid profile.
- **FR-002**: A profile MAY name a CodexBar provider in a `codexbar` field.
  Right before such a profile is first used, backfire MUST run CodexBar's
  `usage` command for that one provider with JSON output, in an
  environment that holds only `PATH`, `HOME` and the profile's key under the
  variable named by `credential`, and MUST NOT log or return CodexBar's raw
  output, which can hold account identity. These are limits from CHE-45's
  security review of CodexBar.
- **FR-003**: Backfire MUST skip the profile when CodexBar's report for that
  provider shows a used-up limit (any rate window at 100% or more used) or a
  balance of zero or less. The balance is `usage.providerCost.balance` when
  present, else the dollar amount in the provider's balance row of
  `usage.details`.
- **FR-004**: When CodexBar cannot be run, exceeds its time limit, exits
  with an error, or prints a report with no usable limit or balance,
  backfire MUST use the profile and log that its credit is unknown.
- **FR-005**: A profile MAY list the HTTP statuses that mean insufficient
  balance in an `insufficient_balance` array; the default is `[402]`. When
  the provider in use answers one of them, backfire MUST send the same
  judgment to the next usable profile in the order and use that profile
  for the rest of the process.
- **FR-006**: Any other failure MUST NOT cause a switch and MUST be returned
  as it is today.
- **FR-007**: When no profile in the order is left to try, the judgment
  MUST fail with a new backfire error, `no_credit`, whose message says that
  no profile in the order has credit.
- **FR-008**: Each result's `provider` field MUST name the profile that
  answered, and every skip and switch MUST be logged with the profile names
  and never a key.
- **FR-009**: Both modes MUST read one shipped configuration with one
  order and one set of profiles. Education mode MUST pseudonymize each
  judgment once before any attempt, whichever profile answers, and keeps
  PyModel's response cache off.
- **FR-012**: The shipped order MUST be OpenRouter, then Hive. CHE-51 puts
  the Cloudflare and Vercel profiles in front of them.
- **FR-013**: Backfire's Jev-on-Vercel provider (`vercel.py`), its profile
  and its tests MUST be removed, with its entry in the third-party notices.
- **FR-010**: Tests MUST use saved CodexBar JSON built from its documented
  format and synthetic keys, never real balances or keys, and MUST NOT
  call a real provider.
- **FR-011**: `docs/backfire.md` MUST describe the order, the two profile
  fields, CodexBar's role and limits, the switch, and the `no_credit` error.

### Key Entities

- **Order**: the ordered list of profile names both modes try.
- **Profile**: an existing provider profile with two new optional fields,
  `codexbar` and `insufficient_balance`.
- **Credit report**: CodexBar's JSON for one provider; backfire reads only
  the rate windows' used percentages and the balance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tests show a skip for a zero balance and for a used-up limit,
  no skip for a positive or unknown credit, a mid-run switch that re-sends
  the judgment, no switch for other errors, the `no_credit` failure, one
  switch for concurrent failures, and education mode on the shared order
  with pseudonymized text after a switch.
- **SC-002**: `npm run verify` reports VERIFIED on the feature merged with
  the current `develop`.
- **SC-003**: The report states the feature's measured change size
  against `develop` and, for a change of 1,000 lines or more, the result of
  the `AGENTS.md` split review.
- **SC-004**: Live checks are limited to short OpenRouter checks and the
  fewest Hive, Vercel and Cloudflare calls a check needs, and the report
  counts every live call.

## Assumptions

- CHE-45 installed CodexBar 0.69.0 on the development laptop on
  2026-09-30 as `~/.local/bin/codexbar`, from the release tarball with its
  SHA-256 checked, and tested `codexbar usage --provider openrouter
  --format json` and `--provider vercel` with the keys from
  `providers/*.env`. Its security review allows one `--provider` per call
  (never `all`, `both` or `--status`), only the `usage` command, only the
  provider's own key, no CodexBar configuration file, and no account
  identity in messages or logs. Tests use a stand-in executable that
  prints saved JSON.
- CodexBar's source at commit 25bba9b of 2026-09-28 (version 0.69.1,
  one patch release after the installed 0.69.0) reports an OpenRouter
  balance in `usage.providerCost.balance` for keys without a spending cap
  and in the "Credits" section's "Remaining" row, and a key limit as
  `usage.primary.usedPercent`; it reports a Vercel AI Gateway balance only
  in the "Team credits" section's "Available balance" row.
- Backfire keeps no state between server processes; the order restarts for
  each client session.
