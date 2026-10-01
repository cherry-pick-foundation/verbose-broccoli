# Bug Fix: doc-regions prepare builds jev_verify requests too large for OpenRouter

- **Slug**: doc-request-batches
- **Fixed**: 2026-10-02
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

`verify_requests` now closes a request at 110 claims or 12,000 claim characters
(or the cell rule, whichever is first). `prepare` lists changes with `-M
--name-status`, so a rename is one rename diff.

## Changes

| File                                               | Change     | Notes                                                               |
| -------------------------------------------------- | ---------- | ------------------------------------------------------------------- |
| `packages/doc-regions/src/doc_regions/requests.py` | modified   | `MAX_CLAIMS`, `MAX_CLAIM_CHARS`, `claim_batches`; `-M` rename diff. |
| `packages/doc-regions/tests/test_requests.py`      | added test | Claim bounds and the rename diff.                                   |
| `docs/architecture.md`                             | modified   | One sentence on the request bounds.                                 |

## Tests Added or Updated

- `test_verify_bounds_claim_characters_and_count` (106 long claims, 224 short
  claims, oversized claims, with 1 and 12 evidence items).
- `test_prepare_keeps_a_rename_as_one_small_diff`.

## Local Verification

See `test.md`.

## Deviations from Assessment

- None.

## Follow-ups

- If a live request shows the true limit, change the two constants.
