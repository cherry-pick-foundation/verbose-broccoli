# Implementation Plan: Backfire Provider Choice by Credit

**Branch**: `feature/backfire-provider-credit` | **Date**: 2026-09-30 |
**Spec**: [spec.md](spec.md) | **Linear issue**: CHE-46

## Summary

Backfire's configurations name an ordered list of profiles instead of one.
A wrapper provider, which replaces today's `_ProfileProvider`, builds the
profile in use lazily, reads its credit through CodexBar right before first
use when the profile names a CodexBar provider, and on an insufficient-balance
status re-sends the same judgment to the next profile. PyModel's
`JevProvider.evaluate` keeps retries, time limits and redaction; backfire's
profile loader keeps validation and key loading.

## Technical Context

**Language/Version**: Python 3.14.4, uv 0.11.32 or later.

**Primary Dependencies**: jev-judge-mcp 0.6.0 (PyModel) and
system-one-adapter 0.2.1, unchanged; CodexBar's command-line tool
(`codexbar`), installed and security-reviewed by CHE-45, run as a
subprocess. No new Python dependency.

**Testing**: pytest in `packages/backfire/tests`, run by
`npm run test:backfire` and `npm run verify`. Providers are the existing
loopback `FakeProvider`; CodexBar is a stand-in executable on a temporary
`PATH` that prints a saved JSON fixture.

**Constraints**: no real keys, balances or provider calls in tests; keys
reach CodexBar only as environment variables; `test_no_provider_names.py`
keeps the name of the default provider out of `src/` except in the two
shipped `config.toml` files.

## Constitution Check

- **VII, reuse order**: CodexBar is used unchanged as a command; PyModel's
  retry loop, status errors (`JevProvider._status_error`) and redaction are
  reused; the new code is glue: an order loop, a JSON reading of two fields
  and a status match. Pass.
- **Product and Data Boundaries**: fixtures are synthetic CodexBar JSON with
  made-up amounts; no key, balance, student record or account identity is
  committed. Pass.
- **Workflow**: spec, plan, tasks, analysis, implementation by a Codex
  worker, a fresh Claude Code review of the code and a fresh Codex review of
  the records, then `git flow feature finish`. Pass.

## Design

### Configuration

Both modes read one shipped configuration,
`packages/backfire/src/backfire/config.toml`;
`packages/backfire/src/backfire_education/config.toml` is deleted, and
education mode differs only in pseudonymization and the response cache.
Until CHE-51 adds the Cloudflare and Vercel profiles, it becomes:

```toml
order = ["openrouter", "hive"]

[providers.openrouter]   # the table CHE-41 added, plus codexbar
api = "jev"
jev_provider = "openrouter"
credential = "OPENROUTER_API_KEY"
credential_file = "../providers/openrouter.env"
codexbar = "openrouter"

[providers.hive]
# existing fields
insufficient_balance = [405]
```

The Jev-on-Vercel profile and `vercel.py` are deleted (FR-013).
The operator file accepts `order` and `providers`; `provider` is no longer
read. Both plugins read it, as today.
`config.load_profile` becomes `config.load_profiles`, which returns the
validated profiles in order and still defers key loading.

| Field | Meaning |
| --- | --- |
| `order` | Profile names to try, first to last |
| `codexbar` | Optional CodexBar provider ID; its credit is read before first use |
| `insufficient_balance` | Optional HTTP statuses that mean the balance is used up; default `[402]` |

### Flow

1. The provider factory loads and validates the profiles and returns the
   wrapper; nothing is sent yet.
2. On a judgment, the wrapper pseudonymizes once in education mode, then
   takes the profile in use. If none is built yet, it builds the next one
   in the order: loads its key, reads its credit when it has `codexbar`,
   and on no credit logs a skip, closes it and moves on.
3. The judgment goes to that profile's provider through PyModel's
   `evaluate`. On a `ProviderError` whose text begins
   `<provider label> <status>:` with a status in the profile's
   `insufficient_balance`, the wrapper advances the order under a lock, but
   only if no concurrent judgment already advanced it, logs the switch and
   re-sends the same judgment.
4. The answer's `provider` is replaced by the profile's name, then the
   education restore runs as today.
5. With no profile left, the judgment fails with `no_credit`.

PyModel's `evaluate` re-raises a copy of each provider error with redacted
text and without the `status` attribute, so the status is read from the
text PyModel's `_status_error` writes (`"{label} {status}: {body}"`).
Backfire's general-model provider today raises `"backfire profile request
failed"` for an HTTP error; it will call `self._status_error(status, ...)`
instead, so the Hive status appears in the same form.

### CodexBar reading

`codexbar usage --provider <id> --format json`, with an environment of
only `PATH`, `HOME` and `<credential>=<key>`, a 30-second limit and output
captured. The minimal environment follows CHE-45's security review of
CodexBar 0.69.0: one provider per call, only its own key, and none of the
variables that reroute keys or switch sources (`OPENROUTER_API_URL`,
`OPENROUTER_MANAGEMENT_API_KEY`, `CODEXBAR_CONFIG` and others). CodexBar's
raw output can hold account identity, so backfire never logs or returns
it. The output is an array of provider reports; backfire reads the
report whose `provider` is the ID and treats it as no credit when:

- `usage.primary`, `usage.secondary` or `usage.tertiary` has
  `usedPercent >= 100`; or
- `usage.providerCost.balance` is a number `<= 0`; or, without that field,
- a `usage.details` row labelled "Remaining" in a section titled
  "Credits", or labelled "Available balance", holds a dollar amount
  `<= 0` (CodexBar formats these as `$1,234.56`).

Anything else, including an `error` in the report, a non-zero exit with
unreadable output, a missing executable or a timeout, is unknown credit and
the profile is used.

Source evidence, CodexBar at commit `25bba9b` (version 0.69.1):
`Sources/CodexBarCLI/CLIPayloads.swift:4-18` (report fields),
`Sources/CodexBarCore/UsageFetcher.swift:178-196,369-371` (usage keys),
`Sources/CodexBarCore/ProviderCostSnapshot.swift:17-18` (`balance`),
`Sources/CodexBarCore/Plugins/ProviderPluginSnapshotMapper.swift:292-315`
(plugin `cost.balance` to `providerCost.balance`),
`Sources/CodexBarCore/Resources/Plugins/openrouter.js:76,314-352`
(balance, key-limit window, "Credits"/"Remaining" row) and
`Sources/CodexBarCore/Resources/Plugins/vercel.js:35-47` ("Team
credits"/"Available balance" row); `docs/cli.md` (JSON uses
`usage.details`; exit code non-zero when a provider fetch fails).

### Insufficient-balance statuses

- Hive: 405 when the organization's balance is exhausted, from Hive's
  documentation as recorded in `specs/005-jev-decision-backend/research.md`
  ("Status evidence for failure classes").
- Cloudflare Workers AI: 402 with code 2021, "Insufficient balance",
  observed on 2026-09-30 (`specs/021-chat-jev-ultrafast/research.md` on
  the CHE-41 branch).
- OpenRouter: 402 for insufficient credits, per OpenRouter's API error
  documentation; the default `[402]` covers it.
- Vercel AI Gateway: no insufficient-balance status was observed; its
  free-tier refusals were 403 and 429, which stay ordinary errors. The
  default `[402]` applies.

### Files and own-code estimate

| File | Change | Own lines (estimate) |
| --- | --- | --- |
| `packages/backfire/src/backfire/config.py` | `load_profiles` with `order` | +20 / -10 |
| `packages/backfire/src/backfire/credit.py` | new: run and read CodexBar | +50 |
| `packages/backfire/src/backfire/providers.py` | order wrapper, status error | +50 / -25 |
| `packages/backfire/src/backfire/failures.py` | `no_credit` message | +4 |
| `packages/backfire/src/backfire/config.toml` | shared `order`, new fields | +6 / -10 |
| `packages/backfire/src/backfire_education/config.toml` | deleted; both modes share one file | whole file |
| `packages/backfire/src/backfire/vercel.py`, `tests/test_vercel.py` | deleted (FR-013) | whole files |
| `packages/backfire/tests/` | new and updated tests, JSON fixtures | about +450 |
| `docs/backfire.md`, `licenses/THIRD_PARTY_NOTICES.md` | order, CodexBar, switch, error; Vercel port removed | about +60 / -40 |

The first implementation pass measured about 940 changed lines of code,
tests, docs and `turbo.json`, with about 250 lines of own non-test code;
deleted files count as about one line each under the `AGENTS.md` split
review. The final size is recorded in `report.md`.

### Parallel work

CHE-41 (feature-chat-jev-ultrafast) merged into `develop` at `65f3ea3`
while this feature was in progress. It adds the `openrouter` profile and
moves key files to `providers/`, touching `config.toml`, `config.py`,
`test_config.py` and `docs/backfire.md`; this branch merges `develop` after
the first implementation pass and keeps both changes. CHE-44 and CHE-45
touch `AGENTS.md`, tooling and skills. CHE-51 starts from `develop` after
this feature merges.

### Live checks

CHE-45 installed CodexBar 0.69.0 on 2026-09-30 (`~/.local/bin/codexbar`).

1. One judgment through backfire with the shipped configuration, whose
   order starts with OpenRouter: it makes one CodexBar read of the
   OpenRouter credit (CodexBar calls OpenRouter's key and credits
   endpoints, not Jev) and one OpenRouter Jev call, and confirms that the
   result names the `openrouter` profile.

No Hive, Vercel or Cloudflare Jev call is planned. The report counts every
live call, including the Hive calls made by `jev_decide` for worker choice.

## Workers

- Implementation: one Codex worker for `packages/backfire/` (T002-T006,
  T012).
- Research for CHE-51's model choice: one Claude Code worker
  (`research.md`).
- `docs/backfire.md` and the Spec Kit records: the coordinator.
- Review before the develop merge: a fresh Claude Code reviewer for the
  code, a fresh Codex reviewer for the coordinator's docs and records.

Models and efforts are chosen with backfire's `jev_decide` and recorded in
`tasks.md`.
