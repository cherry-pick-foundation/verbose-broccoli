# Bug Verification: doc-regions prepare builds jev_verify requests too large for OpenRouter

- **Slug**: doc-request-batches
- **Tested**: 2026-10-02
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The two new tests fail with `requests.py` from `c0b630b` and pass with the fix.
No live provider call was made (0 paid calls), so the 110-claim and
12,000-character bounds are the reported successes, not a measured limit.

## Checks Performed

| Check                 | Command / Action                                                                | Result | Notes                                                                                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New tests, old code   | `pytest packages/doc-regions/tests/test_requests.py` with the old `requests.py` | fail   | 3 failed (claim bounds with 1 and 12 evidence items; rename diff). The rename-into-excluded-path test was added after the first review and fails against `c0b630b` the same way. |
| New tests, fixed code | `npm run test:doc-regions`                                                      | pass   | 116 passed.                                                                                                                                                                      |
| Full check            | `npm run verify`                                                                | pass   | Summary: 47 of 47 tasks successful, 3 cached; exit 0.                                                                                                                            |

## Residual Risks

- The size limit is in characters, not provider tokens (review 3), and the tests also assert the refused sizes as literals.
- Total evidence is not bounded (see the assessment's risks).
- The provider's true limit is unpublished. If a request of up to 110 claims
  and 12,000 characters is still refused, lower `MAX_CLAIMS` or
  `MAX_CLAIM_CHARS` in `requests.py`.

## Recommendation

Close the bug after the final review.
