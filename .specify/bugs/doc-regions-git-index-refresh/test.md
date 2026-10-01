# Bug Verification: doc-regions test fails when Git refreshes its index

- **Slug**: doc-regions-git-index-refresh
- **Tested**: 2026-10-01
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The regression test fails without the fix and passes with it, and the full
check passes. Linear issue: CHE-75.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Regression test before the fix | `pytest packages/doc-regions/tests/test_requests.py -k unchanged_ignores` | pass | Failed on the `.git/index` hash, as intended. |
| Regression test after the fix | the same command | pass | 1 passed. |
| doc-regions suite | `npm run test:doc-regions` equivalent | pass | 111 passed. |
| Full check | `npm run verify` | pass | Workflow `VERIFIED`. |

## Residual Risks

- The original flake was timing dependent and was never observed directly; the
  deterministic test covers the mechanism, not the timing.

## Recommendation

Close the bug once the branch is merged into `develop`.
