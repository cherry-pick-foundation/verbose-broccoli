# Bug Verification: Model choice offers Grok after its free usage cap is hit

- **Slug**: model-choice-grok-free-cap
- **Tested**: 2026-10-01
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: pass

## Summary

The corrected guidance, run against today's real log, prints the entry that
explains the refusals.

## Checks Performed

| Check | Command / Action | Result | Notes |
| ----- | ---------------- | ------ | ----- |
| Guidance against the real log | The `grep \| jq` line from the skill | pass | `2026-10-01T13:11:58.698Z grok-4.7 1012248/1000000`: Grok counts as unavailable for `grok-4.7` until about 2026-10-02T13:11Z. |
| Repository check | `npm run verify` | pass | VERIFIED; 39 of 39 tasks successful. |
