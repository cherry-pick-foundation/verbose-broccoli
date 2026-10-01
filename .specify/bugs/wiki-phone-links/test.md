# Bug Verification: Wiki check's phone rule flags numbers inside Slack links

- **Slug**: wiki-phone-links
- **Tested**: 2026-10-02
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The new test fails with the old pattern and passes with the new one. On the real
work vault, the phone findings fall from 106 to 0.

## Checks Performed

| Check                 | Command / Action                                                                                              | Result | Notes                                                                                                                      |
| --------------------- | ------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------- |
| New test, old pattern | `uv run … pytest packages/wiki-consistency/tests/test_rules.py -k slack_link` with `phone.yml` from `3d4613f` | fail   | Slack link lines are reported.                                                                                             |
| New test, new pattern | same, with the fix                                                                                            | pass   |                                                                                                                            |
| Rule tests            | `pytest packages/wiki-consistency/tests/test_rules.py`                                                        | pass   | 103 passed; existing link-target and code phone cases still pass.                                                          |
| Work vault, read only | `rules.check` on the work vault; counts by rule only                                                          | pass   | Phone findings 106 to 0. Two `date` findings remain (out of scope). No page was changed; no names or numbers were printed. |
| Full check            | `npm run verify`                                                                                              | pass   |                                                                                                                            |

## Residual Risks

- Not run: the full `wiki-consistency check` (link checks) on the work vault; its
  62 broken source links are a content problem, not part of this bug.
- A phone-shaped number that exactly fits a Slack host or timestamp shape is not
  reported.

- Known limits from the last review, not fixed because Vale's regex cannot see
  link structure: a scheme-less `//w…-iwc….slack.…` host, a first host group over
  20 digits, a Slack host written inside another link's path, and a code span
  holding a full `ts=<10 digits>.<6 digits>` shape are not reported or are
  reported wrongly. A fix would need Markdown link parsing, not a rule change.

## Recommendation

Close the bug: `npm run verify` passed (exit 0) at `e1ce91b`, which holds the rule and test (later commits change records only).
