# Bug Assessment: Total evidence is unbounded in document judgments

- **Slug**: doc-evidence-budget (generated for this automated intake)
- **Created**: 2026-10-07
- **Source**: pasted clean-architecture report relayed through Orca
- **Tracking**: [CHE-96](https://linear.app/verbose-broccoli/issue/CHE-96)
- **Verdict**: valid
- **Severity**: medium

## Report (summarized)

The S2b producer prepared 66 `jev_verify` requests, each carrying 108,948
combined evidence characters. All 66 retained client results reported
`OpenRouter decisions API 400`. Splitting the evidence into four parts per
request produced 264 non-error judgments; those paid results remain retained.
This intake makes no new provider retry of those requests.

## Symptom

`--max-evidence-chars` bounds each evidence item, while every generated request
still receives the entire evidence set. Large changes therefore need manual
splitting before their document judgments can complete.

## Reproduction

The saved synthetic reproduction creates a temporary Git repository with one
document and three changed source files. It calls the current `prepare`
function at `fae0c02` with `max_evidence_chars=500`. Exit 0: one verify request,
6,411 combined evidence characters, largest item 500 characters, zero
judgment-provider calls. The temporary repository is disposable; the script,
result and exit receipt remain in persistent state.

Authoritative evidence: `$XDG_STATE_HOME/verbose-broccoli/workspaces/develop/
doc-evidence-budget-intake/attempt-20261007t005236z/`, using the standard state
root when the variable is unset, empty or relative. The original failed and
split S2b results remain under `workspaces/feature-clean-architecture/slices/s2b/`
in the same project state namespace.

## Suspected Code Paths

- `packages/doc-regions/src/doc_regions/requests.py:183-199`: `prepare`
  splits each file diff, accumulates all chunks, then passes one complete
  evidence group to `verify_requests`.
- `packages/doc-regions/src/doc_regions/requests.py:61-87`: `verify_requests`
  bounds claims and answer cells, but repeats the group's full evidence in
  every claim batch.
- `packages/doc-regions/src/doc_regions/__main__.py:32-44`: the command passes
  the requested evidence limit into `prepare`.

## Root Cause Hypothesis

Confidence is high for the missing aggregate bound: the synthetic reproduction
and the current builder agree. The provider's exact token limit is unknown;
35,000-character evidence parts answered the producer's case, which is a
measurement of that case and does not guarantee future provider acceptance.

## Proposed Remediation

**Preferred**: group the already split evidence under the caller's aggregate
budget before passing groups to the existing `verify_requests` function.
Keep every document claim associated with every evidence group, retain all
bytes and their IDs, and preserve deterministic ordering. Keep the existing
claim bounds, tool payloads and published helper interfaces. The caller must
combine only the returned formal verdicts; a subject-demoted relation flag
remains an unsupported result requiring review.

Expected local change: about 10–25 source lines and 15–30 test lines of
integration glue using the existing group interface and test runner. This is
an estimate for later implementation, not a size cap or a repair already made.

**Files likely to change**: `packages/doc-regions/src/doc_regions/requests.py`
and `packages/doc-regions/tests/test_requests.py`; the existing command
explanation only if the option's documented scope needs clarification.

**Tests to add**: multiple small diff items whose total exceeds the budget;
the exact budget boundary; oversized individual items; and lossless,
deterministic claim/evidence coverage across generated groups. Keep the
claim-count, claim-character and rename tests. Coordinate the package with
clean-architecture's later S5 move before a source worker edits it.

## Risks & Considerations

[CHE-62](https://linear.app/verbose-broccoli/issue/CHE-62) is complete for claim
batching and rename pairing. Its assessment and verification explicitly left
aggregate evidence unbounded. This is that separate follow-up; CHE-62 was not
reopened and its implemented bounds are preserved.

Evidence partitioning can change a judgment's context. No evidence may be
silently dropped, and a result from one part cannot stand for an unjudged part.
More groups can mean more calls; live acceptance stays outside verification
and reports its count. Failed original results contain no model or billing
metadata, so no such outcome is inferred.

Jev verified all four supplied intake claims with no contradiction or
unsupported result. The synthetic reproduction itself used zero provider
calls; its separate public evidence-verification judgment used one.

## Open Questions

No user decision blocks this assessment. The implementation must choose a
lossless grouping and result-combination contract before changing request
semantics. Runtime repair, its regression, independent review and feature
finish remain pending; no repair worker has been dispatched.
