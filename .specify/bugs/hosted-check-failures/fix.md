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

## WHA-18: prepare the missing CodexBar host tool

`.config/mise.toml` now supplies the previously reviewed CodexBar release
version and Linux x86_64 archive checksum as runner inputs. The Checks workflow
reads those inputs, downloads the release, checks SHA-256 before extraction,
and adds the extracted directory to GITHUB_PATH. The binary, symlink and
resource bundle stay together. The existing doctor check is unchanged.

`scripts/root-config-test.ts` asserts that preparation precedes checks, uses
the configured pins, verifies the checksum before extracting, and exposes
the complete archive directory. Its pin-duplication check includes CodexBar.
The new regression test fails on the prior workflow and passes after the fix.

## WHA-23: resolve a native Node installed outside mise

The gate launcher keeps its neutral-directory mise lookup. If that lookup
exits unsuccessfully, it reuses `shutil.which("node")` to find the runtime
on PATH, retaining the existing absolute-file validation. The child still
runs from `/` with the same upstream entry, environment, privacy middleware,
and error boundary. This extends the previously documented PATH fallback
to runners with mise present but no globally configured Node.

Five focused resolver cases cover successful mise lookup, failed mise lookup
with native Node on PATH, and missing, relative or nonexistent fallback paths.
Four failed before the production fix and all five pass afterward. Existing
real-gate integration cases exercise the actual upstream process.

jev-ultrafast's unset-configuration test now explicitly unsets XDG_CONFIG_HOME
before reloading the module and restores its GATE object afterward. Its
assertions and separate storage-environment cases remain unchanged.

Files changed are the gate launcher, its proxy tests, jev-ultrafast provider
tests, the Checks workflow, root configuration tests, and the four existing hosted-check bug records. The workflow now installs the already adopted Poppler utilities through
Ubuntu apt before checks. A new workflow regression requires preparation
before checks and fails on the prior workflow. No workflow pin, dependency,
check, hook or privacy control was removed. The implementation
adds three net production lines, four workflow lines and 62 net test lines before records; the
change is below the 1,000-line split-review threshold.
