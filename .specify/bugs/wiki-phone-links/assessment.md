# Bug Assessment: Wiki check's phone rule flags numbers inside Slack links

- **Slug**: wiki-phone-links
- **Created**: 2026-10-02
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-58> (Linear CHE-58,
  read with `orca linear issue CHE-58 --comments --json`; host `linear.app`)
- **Verdict**: valid
- **Severity**: medium

## Report (summarized)

Since the Wiki page rules moved to Vale, `wiki-consistency check --wiki work`
reported 106 "page rule phone" findings in the work vault, all inside Slack
message links. Expected: phone numbers in page text are still caught; numbers
inside Slack-style link targets are not.

## Symptom

A link such as `[m](https://w1012345678-iwc1.slack.com/archives/C1/p1)` is
reported as a phone number.

## Reproduction

At `3d4613f`, with a scratch page and the repository's Vale config
(`vale --config packages/wiki-consistency/vale/.vale.ini --no-global --output=line`):
a link host `w1012345678-iwc1.slack.com` and a link to
`example.invalid/010-0000-0000` are both reported, as is the text
`call 010-1234-5678`.

## Suspected Code Paths

- `packages/wiki-consistency/vale/styles/wiki/phone.yml` — `scope: raw` reads
  link targets on purpose. `tests/test_rules.py`
  (`test_privacy_and_time_rules_check_code_and_link_targets`) requires a phone in
  a link target and in code to stay a finding. The lookbehind blocked only a
  digit before the number, so digits after a letter (`w1012345678`) matched.
- The caller `rules.py:_run` runs Vale and filters front matter, `sources:` and
  Cog lines only; it has no part in this match.

## Root Cause Hypothesis

The pattern's `0?1[016789]` start can begin right after a letter, and its end
accepts a `.` before more digits. Slack hosts (`w<digits>-iwc…`) and the
`thread_ts=<10 digits>.<6 digits>` query value both match. Confidence: high;
the work vault's 106 findings drop to 0 with the change below.

## Proposed Remediation

**Preferred**: in `phone.yml`, change the lookbehind to `(?<![0-9A-Za-z])` and
the lookahead to `(?![0-9]|\.[0-9])`. This keeps Vale's `scope: raw` and the
existing decision that a phone in a link target is still a finding.

**Alternatives**: a narrower Vale scope (e.g. `text & ~link`) would also stop
`tel:` and `example.invalid/010-…` links being reported, which contradicts the
existing test. Not chosen.

**Tests**: one synthetic page with a Slack-style link (host and `thread_ts`)
and a real phone in text; it fails without the change.

## Risks & Considerations

- A phone number written directly after an ASCII letter (`ID010-1234-5678`) or
  directly before `.<digit>` is no longer reported. Hangul before the number
  still counts as a boundary.

## Open Questions

- None. The issue's wording "numbers inside link targets are not [reported]"
  is read as "Slack-style link numbers"; the existing test keeps a phone-shaped
  link path reported.
