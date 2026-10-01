# Bug Fix: Wiki check's phone rule flags numbers inside Slack links

- **Slug**: wiki-phone-links
- **Fixed**: 2026-10-02
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

`phone.yml`'s pattern now skips a number only in a full Slack shape: a digit group
of a host `w<digits>-iwc<digits>.slack.…`, or a `thread_ts`, `ts`, `latest` or
`oldest` query value shaped `<10 digits>.<6 digits>` (or `%2E`). Other phone
numbers in text, link paths and code still match.

## Changes

| File                                                   | Change     | Notes                                                                   |
| ------------------------------------------------------ | ---------- | ----------------------------------------------------------------------- |
| `packages/wiki-consistency/vale/styles/wiki/phone.yml` | modified   | Three negative lookaheads (two host digit groups, one timestamp value). |
| `packages/wiki-consistency/tests/test_rules.py`        | added test | `test_phone_rule_skips_slack_link_numbers_but_not_other_phones`.        |

## Tests Added or Updated

- The new test writes six Slack links to skip (both host digit groups, a
  scheme-less host, a `thread_ts` value, a `latest` value with `%2E`, a `ts`
  value with `%2e`) and six cases that must be
  reported: plain text, a number glued to a letter, `thread_ts` and `ts` values
  that are not timestamps, code, and a `/w010-…` link path. With `phone.yml` from `3d4613f` it fails.

## Local Verification

See `test.md`.

## Deviations from Assessment

- None.

## Follow-ups

- The 2 "page rule date" findings in the work vault stay open; they are outside
  this bug.
- Model-choice evidence: Jev (OpenRouter `typesafe/jev-1.13`) chose Claude
  (0.65, confidence 0.57), then Sonnet medium (0.85, confidence 0.83); the
  implementer was Claude Sonnet 5.5.
