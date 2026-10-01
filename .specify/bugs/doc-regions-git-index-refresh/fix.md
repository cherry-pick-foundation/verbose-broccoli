# Bug Fix: doc-regions test fails when Git refreshes its index

- **Slug**: doc-regions-git-index-refresh
- **Fixed**: 2026-10-01
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

`unchanged()` in `packages/doc-regions/tests/conftest.py` now skips files under
`.git/`. It still hashes every work-tree file, so a change `prepare` makes
there is still caught. Linear issue: CHE-75.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/doc-regions/tests/conftest.py` | modified | `hashes()` skips paths with a `.git` component. |
| `packages/doc-regions/tests/test_requests.py` | modified | New regression test. |

## Tests Added or Updated

- `test_requests.py::test_unchanged_ignores_git_files_but_not_the_work_tree`
  — rewriting `.git/index` inside the block passes; changing `doc.md` fails.
  Before the fix it failed on the `.git/index` hash; after, it passes.
- The other users of `unchanged()` (`test_audit.py`, `test_requests.py`) guard
  work-tree files only; the 111 doc-regions tests pass.

## Local Verification

- `pytest packages/doc-regions/tests scripts/doc_sources_test.py`: 111 passed.

## Deviations from Assessment

None.

## Follow-ups

None.
