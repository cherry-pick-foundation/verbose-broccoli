# Bug Assessment: doc-regions test fails when Git refreshes its index

- **Slug**: doc-regions-git-index-refresh
- **Created**: 2026-10-01
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-75> (Linear issue
  CHE-75, read with `orca linear issue CHE-75`; host `linear.app`, allowlisted)
- **Verdict**: valid
- **Severity**: low

## Report (verbatim or summarized)

CHE-75: `packages/doc-regions/tests/test_requests.py::test_prepare_excludes_judged_documents_and_empty_evidence_has_no_verify`
failed once in a full `npm run verify` under load and passed on the runs before
and after.

## Symptom

The test's `unchanged()` check sees a change in the temporary repository
although no tracked file changed.

## Reproduction

The failure is timing dependent and was not reproduced as such. Deterministic
form: write to `.git/index` inside an `unchanged(repository)` block; before the
fix the check fails with a differing `.git/index` hash
(`test_unchanged_ignores_git_files_but_not_the_work_tree`).

## Suspected Code Paths

- `packages/doc-regions/tests/conftest.py` (`unchanged`, `hashes`) hashes every
  file under the root with `root.rglob("*")`, including `.git/index`.
- `packages/doc-regions/src/doc_regions/requests.py:148` runs `git diff` on the
  working tree, and Git may rewrite its index during that command.

## Root Cause Hypothesis

Git refreshes the stat data in `.git/index` during `git diff` when file times
have changed. That rewrite changes the index hash without any change to the
work tree. Confidence: high for the mechanism's fit with the intermittent
failure; the rewrite itself was not observed.

## Proposed Remediation

**Preferred**: make `hashes()` skip paths under `.git/`.

**Alternatives**: run `git diff` with `GIT_OPTIONAL_LOCKS=0` in the source.
This changes product code for a test-only problem, so it was not chosen.

**Files likely to change**:
- `packages/doc-regions/tests/conftest.py`
- `packages/doc-regions/tests/test_requests.py`

**Tests to add or update**:
- A test that changes `.git/index` inside the checked block (passes) and a work
  tree file (still fails).

## Risks & Considerations

- Other tests using `unchanged()` guard tracked and untracked work-tree files;
  none of them checks `.git/`, so they guard the same things as before.

## Open Questions

- None.
