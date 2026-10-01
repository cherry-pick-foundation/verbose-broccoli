# Bug Fix: Wiki check's phone rule flags numbers inside Slack links

- **Slug**: wiki-phone-links
- **Fixed**: 2026-10-02
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

`phone.yml`'s pattern now needs no ASCII letter before the number and no
`.<digit>` after it. Slack link hosts and `thread_ts` values stop matching; real
phone numbers in text, link paths and code still match.

## Changes

| File                                                   | Change     | Notes                                                            |
| ------------------------------------------------------ | ---------- | ---------------------------------------------------------------- |
| `packages/wiki-consistency/vale/styles/wiki/phone.yml` | modified   | Lookbehind `(?<![0-9A-Za-z])`; lookahead `(?![0-9]\|\.[0-9])`.   |
| `packages/wiki-consistency/tests/test_rules.py`        | added test | `test_phone_rule_skips_digits_in_a_link_host_but_not_page_text`. |

## Tests Added or Updated

- The new test writes a Slack-style link (host `w1012345678-iwc1…`, query
  `thread_ts=1712345678.123456`) and the text `Call 010-1234-5678.`; it expects
  one phone finding, on the text line. With `phone.yml` from `3d4613f` it fails.

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
