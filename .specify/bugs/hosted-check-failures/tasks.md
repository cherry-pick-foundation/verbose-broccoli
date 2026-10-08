# Hosted check repair tasks

- T001: isolate credit-offers test time zone and import-time configuration.
- T002: install the existing locked lychee in Documentation references and
  retain a failing workflow regression case.
- T003: record assessment, fix and verification through the Spec Kit bug extension.

2026-10-08: T001 and T002 implemented; both failures reproduced before the fix
and passed afterward. Full verification passed with system Git; T003 records the results. CEO review
and the review-record commit come next.

- T004: prepare the reviewed CodexBar host archive for Checks, retain doctor's
  version requirement, reproduce the clean-environment failure and add a
  workflow regression case (WHA-18).

2026-10-08: Engineer (Codex, harness-assigned) implemented T004. Clean doctor
failed only CodexBar before preparation and passed afterward; regression
failed before the workflow fix and passed afterward. All 46 full checks passed; final
unchanged-snapshot verification follows this record update. Commit and publish
only on feature/hosted-check-fixes, then hand off to the configured Claude
Reviewer stage and a Watchdog monitor of PR #2.
