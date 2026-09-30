# Tasks: Backfire Provider Choice by Credit

**Input**: [spec.md](spec.md) and [plan.md](plan.md) in
`specs/025-backfire-provider-credit/`

**Tests**: required; every behavior in the spec has a pytest case in
`packages/backfire/tests/`.

**Format**: `[ID] [P?] [Story] Description`; `[P]` tasks touch different
files and can run in parallel.

## Phase 1: Setup

- [X] T001 Check `develop` for CHE-41's `openrouter` profile and shared key
  folder; if it has landed, merge `develop` into the feature branch before
  T002. Coordinator.

## Phase 2: Foundation

- [ ] T002 [US1] [US2] [US3] Replace `provider` with `order` in
  `packages/backfire/src/backfire/config.py` (`load_profiles` returns the
  validated profiles in order; the operator file accepts `order` and
  `providers`; every name must resolve; `codexbar` must be a non-empty
  string and `insufficient_balance` a list of HTTP status integers when
  present), and in both shipped `config.toml` files as plan.md
  "Configuration" shows: the code plugin's order Hive, OpenRouter, Vercel
  with an `openrouter` profile; the education order `education`, then
  `openrouter`; Hive's `insufficient_balance = [405]`; `codexbar` on the
  Vercel and OpenRouter profiles. Update `tests/test_config.py` and
  `tests/test_no_provider_names.py` for the new shape; the education
  profiles stay equal to the code plugin's Hive and OpenRouter profiles.
- [ ] T003 [P] [US1] Add `packages/backfire/src/backfire/credit.py`: run
  `codexbar usage --provider <id> --format json` with the profile's key in
  the environment variable named by `credential`, a 30-second limit, and
  read the report as plan.md "CodexBar reading" says; return no credit,
  credit or unknown. Tests in `tests/test_credit.py` with a stand-in
  `codexbar` on a temporary `PATH` and synthetic JSON fixtures kept in
  that test file for a zero and a positive OpenRouter
  `providerCost.balance`, a capped OpenRouter key at 100% used, a zero and a
  positive Vercel "Available balance" row, a report with `error`, and bad
  output, a non-zero exit, a timeout and a missing executable. A test
  checks that the key is passed only in the environment.

## Phase 3: User Stories 1-3, the order wrapper (P1)

- [ ] T004 [US1] [US2] [US3] In `packages/backfire/src/backfire/providers.py`,
  replace `_ProfileProvider` with the order wrapper of plan.md "Flow":
  lazy build, credit read before first use, skip, switch on an
  `insufficient_balance` status read from PyModel's `"{label} {status}:"`
  text, one advance for concurrent failures, the result's `provider` set
  to the profile name, logs for skip and switch, and `no_credit` when no
  profile is left. Make `_OpenAIProvider` raise
  `self._status_error(status, ...)` for HTTP errors. Add `no_credit` to
  `failures.py`. Keep education pseudonymization once per judgment.
- [ ] T005 [US1] [US2] [US3] Tests in `tests/test_provider.py` (or a new
  `tests/test_order.py`): skip on no credit with no request to the skipped
  provider; unknown credit uses the profile; mid-run switch re-sends the
  judgment and later judgments go to the new profile; a switch target
  with no credit is skipped; other errors such as 401, 400 and exhausted
  retries do not switch; `no_credit` after the last profile; concurrent
  failures advance once; the result names the profile; education mode
  uses only its own order, and on a switch from its first to its second
  profile the second provider receives only pseudonymized text, the
  judgment is pseudonymized once and the answer is restored;
  the Hive-style profile switches on 405 through `_OpenAIProvider`.
- [ ] T006 Run `npm run test:backfire`, `npm run lint` and
  `npm run format:check` for the package, fix findings, and commit with
  `Spec-Kit-Task` trailers.

## Phase 4: User Story 4, documentation (P2)

- [ ] T007 [US4] Update `docs/backfire.md`: "Select a provider" describes
  `order`, the shipped orders, `codexbar` and `insufficient_balance`;
  a short section on CodexBar (what it reads, when, keys only in the
  environment, what happens when it is missing); the switch; the result's
  `provider` field; and `no_credit` in "Troubleshoot errors". Coordinator.

## Phase 5: Acceptance and finish

- [ ] T008 After CHE-45 reports CodexBar installed, confirm the command
  line and the real report shape for OpenRouter and Vercel, and run the
  plan's live checks; record each call in `report.md`. Coordinator.
- [ ] T009 Analysis of spec, plan and tasks; `npm run verify` on the
  feature; record the change size. Coordinator.
- [ ] T010 Move CHE-46 to In Review and the board to in-review; fresh
  Claude Code review of the code and fresh Codex review of the docs and
  records; resolve findings; review-record commit. Coordinator.
- [ ] T011 Merge `develop`, `npm run verify`, check `develop` has not moved,
  `git flow feature finish backfire-provider-credit`; CHE-46 to Done with
  one completion comment; board to completed. Coordinator.

## Dependencies

T001 before T002. T002 and T003 can run in parallel; T004 needs both;
T005 follows T004; T007 can run any time after the Clarifications are
recorded. T008 waits for CHE-45's CodexBar install. T009 to T011 run in
order after the rest.

## Ledger

- 2026-09-30: coordinator wrote spec, plan and tasks; asked the user the
  default order, the education order and when credit is read. `jev_decide`
  chose Codex `gpt-6-luna` at xhigh for T002-T006 (confidence 0.39; one
  Hive call).
- 2026-09-30: the user chose the code order Hive, OpenRouter, Vercel; the
  education order Hive, then a new OpenRouter education profile; credit
  read before first use and at each switch. CHE-41 was not on `develop`
  yet, so T001 found nothing to merge; this branch adds its `openrouter`
  table.
