# Bug Fix: Total evidence is unbounded in document judgments

- **Slug**: doc-evidence-budget
- **Fixed**: 2026-10-07
- **Assessment**: ./assessment.md
- **Status**: applied
- **Spec-Kit-Task**: T002 (fix). T001 is the preserved assessment; T003 is the
  verification in `test.md`; T004, integration and acceptance, belongs to root.

## Summary

`prepare` now packs the already split evidence items, in diff order, into
groups of at most `--max-evidence-chars` characters in total, and passes those
groups to the unchanged `verify_requests`. Every group is paired with every
claim, so each claim meets each evidence item in exactly one request, and no
evidence byte or ID is dropped or changed. An item is never larger than the
limit (it was chunked to the limit already), so a group can always hold at
least one item.

Line numbers in the assessment refer to develop `fae0c02`, before the fix.

## Task record

| Field | Value |
|-------|-------|
| Task | T002 (fix) |
| Worker | Claude Code, `claude-sonnet-5-5`, medium effort, as chosen by four gated Jev calls before this dispatch |
| Dispatch | `ctx_1315de1bb7a6` (task `task_437aa5fda1a2`) |
| Base | develop `fae0c0260e6b28799448caf9be9964f73d2417fa` |
| Checkpoint | First reporting checkpoint, not a time cap; no blocker. Evidence directory: `~/.local/state/verbose-broccoli/workspaces/feature-doc-evidence-budget/doc-evidence-budget-fix/ctx_1315de1bb7a6/` |
| Provider calls | 0 by this worker. The four model-choice calls were made before the dispatch. |

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/doc-regions/src/doc_regions/requests.py` | modified | `prepare` packs evidence into budgeted groups (about 10 lines); one comment updated. `verify_requests`, `claim_batches`, the claim bounds and the schemas are unchanged. |
| `packages/doc-regions/src/doc_regions/__main__.py` | modified | `--max-evidence-chars` gets a one-line `help` saying it bounds the evidence in one request. |
| `packages/doc-regions/tests/test_requests.py` | added and updated tests | See below. |

## Contract notes for the caller

- Claim and unit IDs now appear in several `jev_verify` requests, once per
  evidence group. Each answer judges the claim against that group only. The
  caller must combine only the returned formal verdicts; a subject-demoted
  relation flag stays an unsupported result for review and is not a verdict.
  This change builds requests only; it adds no provider call and no combining
  code.
- With a limit smaller than the diff, one change now yields more requests
  (about the diff size divided by the limit, times the claim batches). Live
  acceptance and its call count stay outside this fix.
- The 249-item cap of `verify_requests` still applies to one group, so a group
  of more than 249 evidence items still stops the command with the same error.
  A budget that holds that many tiny items is the only way to reach it.
- `docs/architecture.md` (line 922 onward) still says the option "splits" the
  agent regions and does not mention the total bound. That file is outside this
  task's edit scope; root should add one sentence.

## Tests Added or Updated

- Added `test_prepare_bounds_total_evidence_in_every_request`: three changed
  sources, limits of 500, 2,000 and the exact size of the first two items.
  Every request is within its limit, every request carries the same claims,
  evidence IDs are unique, and the joined evidence text equals the unbounded
  run. Fails on the old code.
- Added `test_prepare_packs_evidence_up_to_the_exact_budget`: a limit equal to
  two items' sizes holds both; one character less splits them. Fails on the
  old code.
- Updated `test_prepare_root_diff_schema_determinism_and_read_only`: with
  `max_evidence_chars=80` the evidence now spans several requests, each at most
  80 characters, and the unit IDs repeat once per request. The old assertions
  encoded the bug (one request with all the evidence). Fails on the old code.
- Updated `test_prepare_rejects_more_than_249_evidence_items`: it used a
  1-character limit to make over 249 items in one group; that limit now makes
  one group per item. It now uses 250 small files and a large limit, so the
  same error is still covered.
- Unchanged and passing: the claim-count, claim-character, rename, schema,
  Hangul and CLI tests.

## Local Verification

See `test.md`.

## Deviations from Assessment

- None in design. The assessment's size estimate (10-25 source lines) held:
  about 10 source lines. The tests grew more than estimated because two
  existing tests asserted the old single-group behavior.

## Follow-ups

- Root: add the total-evidence sentence to `docs/architecture.md`.
- The provider's true token limit is still unknown; a limit that suits one
  provider route is not shown to suit another. Live acceptance is outside this
  record.
