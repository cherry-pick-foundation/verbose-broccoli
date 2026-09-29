---

description: "Task list for the Jev Ultrafast web agent and the API credit offer search"
---

# Tasks: Jev Ultrafast web agent and API credit offer search

**Input**: Design documents from `specs/021-chat-jev-ultrafast/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: FR-015 requires offline tests: the Vercel path against a stub, both
browser modes with stubbed `orca` and CDP calls, and the search with stubbed
HTTP, Jev and notification. No test calls a paid service.

**Organization**: Main (Claude Code) owns the Spec Kit records, the skills,
the documents, the constitution and the notices (T011-T013), reviews each
Codex worker's diff, and runs the merge. Codex workers (`gpt-6-luna`, max
effort) implement T001-T010 in two waves: wave 1 is T001-T006
(`packages/jev-ultrafast/` and the shared integration files), wave 2 is
T007-T010 (`packages/credit-offers/`). A fresh Claude Code reviewer gives
the merge review of the code; a fresh Codex reviewer reviews main's prose.

**Line budget**: The user's rule of 2026-09-30: report the net new lines of
locally written code (patch lines inside the upstream copy count; upstream
copies and tests do not) and stop to ask before going over 300. The plan
expects about 200.

**Keys**: No task reads, prints or commits a key. The user has no key yet
(2026-09-30), so the live provider check is not part of this feature.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US4)

---

## Phase 1: Upstream copy and integration (blocks US2 and US3)

- [x] T001 [US2] Copy Jev Ultrafast at `1231850a0bf1a0c0341fe408ef1668dbbfdfac46`
  into `packages/jev-ultrafast/`: `LICENSE`, `jev_ultrafast/` as
  `src/jev_ultrafast/` (all modules, `snapshot.js`, `static/`),
  `tests/test_agent.py`, `examples/run.py`, `examples/flights.py` (imported by
  `test_agent.py`), `scripts/check_guards.py`. Adapt
  upstream's `pyproject.toml` to the workspace (uv_build with `module-root =
  "src"`, same runtime dependencies, same `jev` script; the dev group holds
  only the workspace's `pytest==9.1.1`, because upstream's `pytest<9` cannot
  share the lock and its `ruff` and `pillow` serve files not copied) and check
  that a built wheel contains `snapshot.js` and `static/`. Write
  `packages/jev-ultrafast/UPSTREAM.md` with the source URL, revision, each
  copied file's original SHA-256 and a differences section. Add
  `test:jev-ultrafast` to `package.json` and its `turbo.json` task in the
  pattern of `doc-regions#test`, add the package to `ruff.toml`'s `src`, keep
  the copied upstream files out of the repository's Ruff, gts and Prettier
  checks (they keep upstream's style; new local files are checked), and update
  `uv.lock`. Upstream's `tests/test_agent.py` passes unchanged (FR-001).

## Phase 2: User Story 2 - Choose the provider for Jev calls (P1)

**Goal**: Jev calls go to TypeSafe or Vercel AI Gateway, chosen by
configuration.

**Independent Test**: `npm run test:jev-ultrafast` with stub providers.

- [x] T002 [US2] Add `packages/jev-ultrafast/src/jev_ultrafast/providers.toml`
  and patch `model.py` as [contracts/providers.md](contracts/providers.md)
  specifies: one function selects the provider from `JEV_PROVIDER` and sends
  the request; `choose()` calls it instead of the fixed TypeSafe address;
  `post_json()` may gain only an optional headers argument. Record each
  difference in `UPSTREAM.md` (FR-002, FR-003, FR-004, FR-005).
- [x] T003 [US2] Add `packages/jev-ultrafast/tests/test_providers.py` with
  `httpx.MockTransport` stubs: the Vercel request's URL, headers and body;
  the answer conversion (choice with and without confidence, other types
  unchanged, usage keys, model); the TypeSafe request equal to
  upstream's; `choose()` through the Vercel stub end to end; a missing key and
  an unknown provider failing before any request with no key in the message;
  a malformed Vercel answer rejected by `validate_choice()` (FR-015).

## Phase 3: User Story 3 - Web agent in Orca's built-in browser (P2)

**Goal**: The web agent opens, uses and closes its own Orca tab by default.

**Independent Test**: upstream's `scripts/check_guards.py` passes in an Orca
tab it opens and closes.

- [x] T004 [US3] Patch `packages/jev-ultrafast/src/jev_ultrafast/browser.py`
  as [contracts/orca-browser.md](contracts/orca-browser.md) specifies, with
  `JEV_BROWSER=chrome` keeping upstream's behavior; record each difference in
  `UPSTREAM.md` (FR-006).
- [x] T005 [US3] Add `packages/jev-ultrafast/tests/test_orca_browser.py` with
  stubbed `orca` commands, daemon calls and CDP calls: Orca mode opens one
  tab, sets `BU_CDP_WS`, attaches to the listed page, and closes that tab and
  stops the daemon on `close()` and on a failed start; Chrome mode issues
  upstream's `Target.createTarget` and `Target.closeTarget`; an unknown
  `JEV_BROWSER` value fails (FR-015).
- [x] T006 [US3] Live check without model calls: run
  `packages/jev-ultrafast/scripts/check_guards.py` in Orca mode from this
  worktree, then confirm with `orca tab list --worktree current --json` that
  no tab is left. Touch no tab the run did not open. Report the output.
  - 2026-09-30: Codex (`gpt-6-luna`, max) did T001-T006; commit `953ad4c`.
    44 offline tests pass; `check_guards.py` passed 21 guards in an Orca tab
    and left no tab. Patch: 82 net lines in `model.py` and `browser.py`, plus
    15 in `providers.toml` and 3 in `pyproject.toml`.

## Phase 4: User Story 1 - Hear about a new free API credit offer (P1)

**Goal**: A run notifies only for new offers that cost nothing and state no
time limit.

**Independent Test**: `npm run test:credit-offers`, then the live runs in
[quickstart.md](quickstart.md).

- [x] T007 [US1] Create `packages/credit-offers/` (`pyproject.toml` depending
  on the workspace's `jev-ultrafast`, console script `credit-offers`,
  `src/credit_offers/__init__.py`, `src/credit_offers/tracker.toml`) as
  [contracts/credit-offers-cli.md](contracts/credit-offers-cli.md) and
  [research.md](research.md) R5-R7 specify. Use `httpx` (already a
  dependency) for requests, `jev_ultrafast.model` for the Jev call and
  `validate_choice()`, and `notify-send` for the notification. Add
  `test:credit-offers`, its `turbo.json` task, the `ruff.toml` source root and
  the `uv.lock` update (FR-008-FR-011).
- [x] T008 [US1] Add `packages/credit-offers/tests/test_credit_offers.py`:
  block boundaries (default end, `--end`, `--hours` that does not divide 24);
  same commit at both ends exits 1 without fetching the index; new-slug
  detection; `status` and `expiry_date` filtering without a Jev call; one Jev
  request with one question per candidate; strong, excluded and invalid
  answers; exit statuses 0, 1, 2 and 3; `--notify` calling `notify-send` once
  and only with strong offers; no file written; no key in any output
  (FR-015).
- [x] T009 [US1] Live runs without a key, as
  [quickstart.md](quickstart.md) describes, on one past block with no new
  offer and one with candidates; report exit statuses, `jev_calls` and
  timing (SC-002). Use a temporary empty `0600` env file in the scratch area,
  not the user's configuration folder.
- [x] T010 [US1] Test notification: send one notification through the
  package's notification function with a sample offer whose title says it is
  a test; report the command and its exit status.
  - 2026-09-30: Codex (`gpt-6-luna`, max) did T007-T010 and one review round
    (answered-call count, per-offer question instructions, R6 wording);
    commit `be2835a`. 11 offline tests pass. Live runs with an empty key
    file: the 2026-09-29 12:00-18:00 KST block exited 1 with `jev_calls=0`;
    the 2026-09-28 00:00-06:00 block exited 3 naming `AI_GATEWAY_API_KEY`
    before any request. The first attempts hit GitHub's unauthenticated
    limit (HTTP 403, exit 3). The test notification exited 0. Lines: 146 in
    `__init__.py`, 4 in `tracker.toml`, 32 in `pyproject.toml`; the feature
    totals 282 of the 300-line budget.

## Phase 5: Skills, documents and governance (main)

- [x] T011 [P] Add `plugins/chat/skills/web-agent/SKILL.md` and
  `plugins/chat/skills/credit-offers/SKILL.md` (run commands, provider
  selection, the `0600` credential file, Orca and Chrome modes, one browser
  job at a time, the scroll and screenshot limit, the search's period and
  exit statuses), and update `plugins/chat/plugin.json`'s description
  (FR-007).
- [x] T012 Amend constitution principle IX for the chat package's skills and
  record the decision in Governance; version 2.2.0 to 2.3.0 in a `feat`
  commit (FR-014).
- [x] T013 Update `docs/architecture.md` (chat package, the two packages,
  provider and browser notes), regenerate `docs/reference/` and the
  mechanical regions, and add Jev Ultrafast and the jev-agent-tools request
  format to `licenses/THIRD_PARTY_NOTICES.md` (FR-014).
  - 2026-09-30: after merging `develop` (CHE-43 keeps notices only for
    copied upstream code), the notices keep the Jev Ultrafast entry and drop
    the jev-agent-tools entry, since no jev-agent-tools file is copied;
    research R2 still names that source.

## Phase 6: User Story 4 - A schedule taken from history (P2)

- [x] T014 [US4] Recompute the interval from
  [offer-history.tsv](offer-history.tsv) with the command in
  [quickstart.md](quickstart.md) and confirm it equals research R9's 6.349
  hours (FR-013, SC-004).
  - 2026-09-30: recomputed `145 6.349`, equal to research R9.

## Phase 7: Acceptance, automation and finish

- [x] T015 Run `npm run workflow` and `npm run verify` on the combined result;
  report the line count against the 300-line budget.
  - 2026-09-30: merged `develop` (`63fe2fd`) and resolved the notices
    conflict; `npm run verify -- --task che41-final --base develop` passed
    (`VERIFIED`) at `495878b`. The document judgment step
    (`doc-regions:prepare -- --base develop --max-evidence-chars 20000`)
    sent 236 units in 12 `backfire_verify` requests and one
    `backfire_classify` request on the development profile, which used
    993,708 input and 207,009 output tokens. One target unit was out of
    date and was corrected: the architecture guide said the live provider
    check waits for the user's key, but Vercel's free tier refuses Jev. The
    3 contradicted units are in `AGENTS.md` ("Reuse Before Implementing"),
    report-only, and go to the user. The other 16 units flagged for review
    describe the constitution, `AGENTS.md`, the README and unchanged
    sections, and stand. Of the 7 new architecture units, the classifier
    suggested 2 as mechanical candidates without auto-accepting them; both
    describe choices, not facts a generator reads, so they stay agent-written.
    `doc-regions:audit` reported the same 19 MemoryLint `boundary` warnings
    on the constitution as earlier features. Lines: 282 of 300.
- [ ] T016 Describe the automation (name, `0 */6 * * *` in `Asia/Seoul`,
  the `develop` worktree, the precheck command with `--notify`, the agent
  prompt, the provider, the empty `0600` credential file it needs) and ask
  the user through `orca orchestration ask`; after approval and the finish,
  create it with `orca automations create` and confirm it with `orca
  automations show` (FR-012). Approved 2026-09-30: no agent session (the
  precheck ends with `; exit 1`), credential file created empty.
- [ ] T017 Merge review by fresh reviewers, review-record commit, merge
  `develop` in and verify, `git flow feature finish`, `npm run verify` on the
  merged `develop`, and CHE-41 through In Review to Done with one completion
  comment.

## Dependencies & Execution Order

- T001 blocks T002-T006. T002 and T004 edit different files and can run in
  parallel inside wave 1; T003 follows T002, T005 follows T004, T006 follows
  T004.
- T007-T010 (wave 2) follow T002, because the search calls the provider
  function; T008 follows T007, T009 and T010 follow T007.
- T011-T014 are main's and can run while the workers work.
- T015 follows T001-T014; T016 and T017 follow T015, and the automation is
  created only after the finish, so its precheck runs merged code.

## Parallel Example

```text
Wave 1 worker: T001 → (T002 → T003) and (T004 → T005 → T006)
Main, meanwhile: T011, T012, T013, T014
Wave 2 worker: T007 → T008 → T009 → T010
```

## Implementation Strategy

US2 first, because every Jev call depends on it; then US1, the user's
requested outcome; US3 adds the browser default; US4 is already in the
records and is only checked.
