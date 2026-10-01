# Bug Fix: Wiki check's phone rule flags numbers inside Slack links

- **Slug**: wiki-phone-links
- **Fixed**: 2026-10-02
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

`phone.yml`'s pattern now skips a number right after `://w` (a Slack link
host) or after a Slack timestamp query key (`?thread_ts=`, `&ts=`, `latest=`,
`oldest=`). Other phone numbers in text, link paths and code still match,
including one glued to a letter, to `w` or to `ts=` outside a link.

## Changes

| File                                                   | Change     | Notes                                                            |
| ------------------------------------------------------ | ---------- | ---------------------------------------------------------------- |
| `packages/wiki-consistency/vale/styles/wiki/phone.yml` | modified   | Lookbehinds `(?<!://w)` and a query-key lookbehind added.        |
| `packages/wiki-consistency/tests/test_rules.py`        | added test | `test_phone_rule_skips_digits_in_a_link_host_but_not_page_text`. |

## Tests Added or Updated

- The new test writes a Slack-style link (host `w1012345678-iwc1…`, query
  `thread_ts=1712345678.123456`), a `latest=1712345678%2E123456` link, and phone
  numbers in plain text, glued to a letter, after `ts=` outside a link, in code
  and in a `/w010-…` link path; it expects five phone findings, one per such line. With `phone.yml` from `3d4613f` it fails.

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
