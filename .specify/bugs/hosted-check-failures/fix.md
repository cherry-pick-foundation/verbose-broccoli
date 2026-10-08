# Bug Fix: hosted checks depend on local setup

- **Slug**: hosted-check-failures
- **Fixed**: 2026-10-08
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Credit-offers tests now set and restore their local time zone. The frozen
proxy test explicitly unsets the configuration root before reloading the
module and restores GATE afterward. Documentation references installs its
existing pinned lychee through locked mise alongside uv.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/credit-offers/tests/test_credit_offers.py` | modified | Scoped Asia/Seoul fixture and explicit unset-config test setup. |
| `.github/workflows/docs-check.yml` | modified | Add lychee to the existing locked installation. |
| `scripts/root-config-test.ts` | added test | Assert both host tools are installed through locked mise. |

## Tests Added or Updated

Existing boundary and proxy assertions are retained. The UTC and absolute
configuration-root run failed 43 cases before the fix and passes all 66 after.
The new documentation workflow assertion fails before the workflow change and
passes afterward. Separate proxy configuration tests retain absolute, unset,
relative and empty cases.

## Local Verification

- UTC plus absolute configuration root: 66 passed.
- Ruff check and format check on the changed Python test: passed.
- Documentation workflow regression assertion: passed.
- Fresh mise tool directory with host lychee excluded from PATH: uv-only setup
  reproduced missing lychee; locked uv/lychee setup and the real
  `mise exec -- npm run doc-regions:check` passed with `{"problems": []}`.

## Deviations from Assessment

None. The existing `.config/mise.toml` pin and `.config/mise.lock` Linux x64
entry were sufficient and remain unchanged. No new dependency was adopted.

## Follow-ups

CEO review and review-record commit, then Main's privacy approval before any
GitHub publication. Hosted execution remains untested until publication.
