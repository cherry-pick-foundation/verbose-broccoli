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

The shipped code-plugin configuration becomes:

```toml
order = ["hive", "openrouter", "vercel"]

[providers.hive]
# existing fields
insufficient_balance = [405]

[providers.vercel]
# existing fields
codexbar = "vercel"

[providers.openrouter]   # the same table CHE-41 adds, plus codexbar
api = "jev"
jev_provider = "openrouter"
credential = "OPENROUTER_API_KEY"
credential_file = "../providers/openrouter.env"
codexbar = "openrouter"
```

The education configuration becomes:

```toml
order = ["education", "openrouter"]

[providers.education]
# existing fields, the same as the code plugin's hive profile
insufficient_balance = [405]

[providers.openrouter]
# the same table as the code plugin's openrouter profile
```

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

`codexbar usage --provider <id> --format json`, with the process
environment plus `<credential>=<key>`, a 30-second limit and output
captured. The output is an array of provider reports; backfire reads the
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
| `packages/backfire/src/backfire/config.toml`, `backfire_education/config.toml` | `order`, new fields | +6 / -2 |
| `packages/backfire/tests/` | new and updated tests, JSON fixtures | about +250 |
| `docs/backfire.md` | order, CodexBar, switch, error | about +40 / -15 |

About 130 lines of own non-test code and about 450 changed lines in all,
well under the 1,000-line split review.

### Parallel work

CHE-41 (feature-chat-jev-ultrafast) adds the `openrouter` profile and moves
key files to `providers/`; both touch the same `config.toml`,
`config.py` and `test_config.py`. If CHE-41 is on `develop` before the
implementation starts, merge `develop` first; otherwise the later finisher
merges and keeps both changes. This branch adds CHE-41's `openrouter`
table unchanged except for `codexbar`, so the merge keeps one copy. CHE-44
and CHE-45 touch `AGENTS.md` and skills only.

### Live checks

Only after CHE-45 reports CodexBar installed:

1. One CodexBar read for OpenRouter and one for Vercel (credit endpoints,
   not Jev calls), to confirm the real report shape and the Vercel skip.
2. One short OpenRouter judgment through backfire with the operator order
   set to `openrouter` alone, to confirm the result names the profile.

No Hive, Vercel or Cloudflare Jev call is planned. The report counts every
live call, including the Hive calls made by `jev_decide` for worker choice.

## Workers

- Implementation: one Codex worker for `packages/backfire/` (T002-T006).
- `docs/backfire.md` and the Spec Kit records: the coordinator.
- Review before the develop merge: a fresh Claude Code reviewer for the
  code, a fresh Codex reviewer for the coordinator's docs and records.

Models and efforts are chosen with backfire's `jev_decide` and recorded in
`tasks.md`.
