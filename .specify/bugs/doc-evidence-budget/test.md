# Bug Verification: Total evidence is unbounded in document judgments

- **Slug**: doc-evidence-budget
- **Tested**: 2026-10-07
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified offline (narrow and affected tests); one generated evidence part accepted live by the provider (see "Live acceptance"); root's full `npm run verify` passed at source commit b18d2a1 (see "Source full verification"); independent review, merge and combined develop verification still pending
- **Spec-Kit-Task**: T003 (verification). T004 integration and acceptance belongs to root.

## Summary

Against the old `requests.py` (develop `fae0c02`) three tests fail; with the
fix all 35 tests in `test_requests.py` pass. The saved synthetic reproduction,
run with `max_evidence_chars=500`, gave one request of 6,411 evidence
characters before the fix and 15 requests of at most 500 after it, with the
same evidence bytes and zero model calls. The source worker itself made 0
provider calls. Root later made one live call (see "Live acceptance"); the
offline results alone do not show that a provider accepts the new request sizes.

## Task record

| Field | Value |
|-------|-------|
| Task | T003 (verification) |
| Worker | Claude Code, `claude-sonnet-5-5`, medium effort (model decision probability .99, confidence .97; effort medium .91, confidence .90; original first 30-minute checkpoint .62, confidence .56, not a cap) |
| Dispatch | `ctx_1315de1bb7a6` (task `task_437aa5fda1a2`) |
| Checkpoint | First reporting checkpoint, not a time cap; reached with no blocker |
| Provider calls | 0 by this worker; one by root later (see "Live acceptance") |

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

- `npm run verify` (full): not performed by this worker; no full-check slot
  was granted to it. See "Source full verification" for root's later run.
- Any provider call by this worker. The original 66 failed and 264 paid split
  results were not replayed.
- A CLI `prepare` run on the real repository diff.
- Independent review: root's fresh other-provider reviewer owns it.

## Source full verification

Root, not this worker, ran the full `npm run verify` at the exact source commit
`b18d2a10ef3347b694b72941b66ce19ffcee4780`. It exited 0, all 45 task exits
were 0 (42 executed, 3 cached), and the summary ID is
`3KLdK4Oop8DkR7Bnz9yaLfMsmSx`. This is retained source evidence, not a new run
for any later documentation commit: `source-full-proof.json` and
`source-full-turbo-summary.json` under
`~/.local/state/verbose-broccoli/workspaces/develop/doc-evidence-budget-fix/attempt-20261007t013919z/`.
The independent final review, the merge and the combined `develop`
verification are still pending.

## Live acceptance

Root later forwarded only the first newly generated public synthetic request
(of 6 generated) through the sole registered, always-gated `jev-mcp`. Its
`evidence.text` totals 500 characters. The route was OpenRouter,
`typesafe/jev-1.13`; the response was normal and not an error, with 1,002 input
and 128 output tokens, client call count 1. This is protocol acceptance for one
evidence part. It is not full-corpus semantic validation and does not guarantee
that every size-bounded input avoids provider errors. The heading had low
confidence and the full-fixture claim was unsupported (subject-demoted,
.16 same_subject), which is accurate for that part only. Evidence: root's
`attempt-20261007t013919z/` under
`~/.local/state/verbose-broccoli/workspaces/develop/doc-evidence-budget-fix/`
(`live-acceptance-proof.json`). No further paid probe is required.

## Docs follow-through

The operator explanation is done in `docs/architecture.md` (T002/T003). It was
written by a fresh Claude Code `claude-sonnet-5-5` worker at low effort with a
first 5-minute checkpoint (not a time cap), one tuple chosen at probability .57
(confidence .47), all requirements supported. Checks: `doc-regions:check` and
`git diff --check`.

## Residual Risks

- Evidence partitioning changes a judgment's context: a claim answered
  `unsupported` against one group may be supported by another group. The caller
  must consider every group's formal verdict and action for each repeated
  claim ID, so a verified result in one group cannot hide a contradiction or
  an unresolved review from another. Unsupported is silence. A
  subject-demoted relation flag is an unsupported result needing review, not
  a formal contradiction. When a claim stands, the caller records a reason or
  disposition. This fix adds no aggregation algorithm and no combining code.
- Claim and unit IDs repeat across requests, once per evidence group; more
  groups mean more provider calls.
- One live part is not full acceptance: other size-bounded inputs may still
  meet provider errors.
- The provider's true limit is unpublished; the limit is characters, not tokens.

## Recommendation

Ready for root's integration. The full `npm run verify` and the independent
review remain root-owned and pending; close the bug only after them.
