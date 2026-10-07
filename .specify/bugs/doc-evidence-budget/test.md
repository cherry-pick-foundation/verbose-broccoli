# Bug Verification: Total evidence is unbounded in document judgments

- **Slug**: doc-evidence-budget
- **Tested**: 2026-10-07
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified offline (narrow and affected tests); full `npm run verify` and live provider acceptance not run
- **Spec-Kit-Task**: T003 (verification). T004 integration and acceptance belongs to root.

## Summary

Against the old `requests.py` (develop `fae0c02`) three tests fail; with the
fix all 35 tests in `test_requests.py` pass. The saved synthetic reproduction,
run with `max_evidence_chars=500`, gave one request of 6,411 evidence
characters before the fix and 15 requests of at most 500 after it, with the
same evidence bytes and zero model calls. No provider was called, so these
results do not show that a provider accepts the new request sizes.

## Task record

| Field | Value |
|-------|-------|
| Task | T003 (verification) |
| Worker | Claude Code, `claude-sonnet-5-5`, medium effort |
| Dispatch | `ctx_1315de1bb7a6` (task `task_437aa5fda1a2`) |
| Checkpoint | First reporting checkpoint, not a time cap; reached with no blocker |
| Provider calls | 0 |

## Checks Performed

Evidence directory (authoritative, outside the repository):
`~/.local/state/verbose-broccoli/workspaces/feature-doc-evidence-budget/doc-evidence-budget-fix/ctx_1315de1bb7a6/`.
Every command ran under `systemd-run --user --scope -q -p CPUWeight=20 nice -n 10
taskset -c 4-7`.

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| New tests, old code | `pytest -p no:cacheprovider packages/doc-regions/tests/test_requests.py -q` with the new tests and the old `requests.py` | fail, as expected | exit 1: 3 failed, 32 passed (`red-old-code.log`). Failed: `test_prepare_root_diff_schema_determinism_and_read_only`, `test_prepare_bounds_total_evidence_in_every_request`, `test_prepare_packs_evidence_up_to_the_exact_budget`. |
| New tests, fixed code (first run) | same command, fixed `requests.py` | fail | exit 1: 1 failed, 34 passed (`green-test-requests.log`). My updated 249-item test used a 1-character limit, which now makes one group per item. I changed the test, not the code (see `fix.md`). |
| New tests, fixed code | same command | pass | exit 0: 35 passed (`green-test-requests-2.log`). |
| Reproduction, fixed code | `reproduction-after-fix.py`: the saved reproduction with its final assertion reversed (sizes at most the limit) | pass | exit 0; 15 requests, sizes 500, 500, 500, 500, 137 for each of three files, largest item 500, 0 model calls (`reproduction-after-fix.json`). Before: 1 request, 6,411 characters. |
| Ruff lint | `uv run --project tools/ruff --frozen --offline --no-sync ruff check --no-cache packages/doc-regions` | pass | exit 0 after one fix (an unused variable in my test; the first run exited 1, `ruff-check.log`; second run `ruff-check-2.log`). |
| Ruff format | `ruff format --check --no-cache packages/doc-regions` | pass | 13 files already formatted (`ruff-format-2.log`). |
| doc-regions suite | `npm run test:doc-regions` | pass | exit 0; 136 passed (`test-doc-regions.log`). |
| Shared Wiki caller | `npm run test:wiki-consistency` | pass | exit 0; 574 passed, 3 warnings, 316 s (`test-wiki-consistency.log`). `wiki_consistency.requests` calls `verify_requests` unchanged. |
| Policy graph | `npm run workflow -- --task doc-evidence-budget-fix --base fae0c02… --plan <root ownership plan> --graph policy` | pass | exit 0 (`policy-graph.json`). The selector for TypeScript impact does not accept Python, so callers were traced by search: `verify_requests` is called by `prepare` and by `wiki_consistency/requests.py` (lines 441 and 493); `max_evidence_chars` only by `prepare` and `__main__.py`. |

What the new tests cover: several small diff items whose total passes the
limit (500, 2,000, and an exact two-item size); the exact boundary (limit equal
to two items packs both, one less splits them); an item larger than the limit
(chunked, each chunk alone or packed within the limit); every request carrying
the same claims, unique evidence IDs and byte-identical joined evidence in
diff order; the unchanged claim-count, claim-character, rename, schema, Hangul
and CLI tests; and the 249-item error for one group.

## Not performed

- `npm run verify` (full): no full-check slot was granted to this worker.
- Any provider call. The 66 failed S2b requests and 264 paid split judgments
  were not replayed. Provider acceptance of the new request sizes is unproven.
- A CLI `prepare` run on the real repository diff.
- Independent review: root's fresh other-provider reviewer owns it.

## Residual Risks

- Evidence partitioning changes a judgment's context: a claim answered
  `unsupported` against one group may be supported by another group. The caller
  must combine formal verdicts only and treat a subject-demoted relation flag
  as an unsupported result needing review. This fix adds no combining code.
- Claim and unit IDs repeat across requests, once per evidence group; more
  groups mean more provider calls.
- `docs/architecture.md` line 922 onward does not yet mention the total bound.
- The provider's true limit is unpublished; the limit is characters, not tokens.

## Recommendation

Ready for root's integration, full verification slot and independent review.
Close the bug only after those and a counted live acceptance.
