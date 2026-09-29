# Bug Fix: Provider failures in bursts leave units unjudged

- **Slug**: provider-error-bursts
- **Fixed**: 2026-09-29
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The existing TypeSafe SDK retry policy now also retries every 5xx status that
the profile does not map to another type, and the `provider_error` raised for
a success reply without an answer. A judgment caught by one of the provider's
short failures is sent again within its four attempts and its deadline,
instead of failing at once. A Codex worker (`gpt-6-luna`, effort `max`)
implemented the change; the coordinator reviewed it and committed it in
`a93f7d8` together with the document updates.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/backfire/src/backfire/failures.py` | modified | `retry_policy` starts from 429 plus 500-599; the profile's `statuses` still add `rate_limited` statuses and remove every other mapped status. The predicate, renamed `_retryable_failure`, also accepts `JudgmentError("provider_error")`. Attempts, backoff, `Retry-After` and the time budget are unchanged. |
| `packages/backfire/tests/test_failures.py` | modified, added tests | Policy-level cases for 5xx, the profile opt-out and `provider_error`. |
| `packages/backfire/tests/test_judge.py` | modified, added tests | Recovery and exhaustion through the real judge, with records. |
| `packages/backfire/tests/test_provider.py` | modified, added test | Replies without an answer are retried; the metadata capture that the earlier fix relies on keeps its own test. |
| `packages/backfire/tests/test_faults.py` | modified | 5xx rows expect four attempts. |
| `packages/backfire/tests/test_adapter_wiring.py` | modified | The debug leak check covers four retried attempts. |
| `specs/005-jev-decision-backend/spec.md` | modified | FR-007 allows retries of provider server errors, with a dated note. |
| `specs/005-jev-decision-backend/contracts/judgment.md` | modified | Error table and "Retries and time". |
| `specs/005-jev-decision-backend/contracts/provider-profile.md` | modified | The `statuses` row says which types are retried and how a profile opts a 5xx status out. |
| `specs/005-jev-decision-backend/research.md` | modified | New decision "Provider failures in bursts — 2026-09-29"; the 2026-09-26 retry decision is marked as superseded in part. |
| `docs/backfire.md` | modified | The `provider_error` troubleshooting row says these failures are retried first. |

## Diff Highlights (optional)

```python
def _retryable_failure(error: BaseException) -> bool:
    if isinstance(error, JudgmentError):
        return error.error_type == "provider_error"
    ...  # connect-phase check unchanged

statuses = {429, *range(500, 600)}  # profile overrides applied as before
```

`ProfileProvider.request` runs inside the adapter's retry loop and raises
`JudgmentError("provider_error")` only for a success reply without an answer,
so the predicate sees exactly that case. `map_error` gives other statuses such
as 403 the same type, but they arrive as SDK status errors, which the
predicate does not accept.

## Tests Added or Updated

- `test_failures.py::test_unoverridden_server_errors_have_four_total_attempts`
  (500, 599) and `test_provider_error_is_retried_four_times` — four attempts
  and three waits.
- `test_failures.py::test_profile_can_disable_server_error_retry` — a 503
  mapped to `request_rejected` is sent once.
- `test_failures.py::test_shipped_profile_non_retryable_statuses_fail_once` —
  now 400, 401, 403, 404, 405, 408 and 422; `test_typed_failures_are_never_retried`
  now excludes `provider_error`.
- `test_judge.py::test_judge_retries_server_error_and_records_success` — HTTP
  500, then a valid answer: the answer returns with `attempts` 2 in the result
  and the record, and the reply text stays out of the record.
- `test_judge.py::test_judge_records_fixed_provider_error_after_four_server_failures`
  — four 500 replies: `provider_error` after four requests, recorded with
  `attempts` 4, no reply text in the error, record or output.
- `test_judge.py::test_non_retryable_http_errors_have_fixed_text` (renamed
  from `test_provider_errors_have_fixed_text_and_no_retry`, without the 500
  case).
- `test_provider.py::test_answerless_provider_error_body_is_sanitized_and_retried`
  (renamed) — the padded HTTP 200 body from the earlier bug, then a valid
  answer: two requests, the answer returns, no reply text leaks.
- `test_provider.py::test_malformed_envelopes_follow_retry_policy_without_raw_diagnostics`
  (renamed) — invalid JSON, `[]`, `null` and a non-list `choices` are retried
  once and answered; `{"choices": [null]}` stays `malformed_output` after one
  request.
- `test_provider.py::test_answerless_responses_preserve_captured_metadata` —
  for empty, missing and null `choices`, one direct provider request keeps the
  reported model, usage, reasoning tokens and thinking evidence.
- `test_provider.py::test_other_response_failures_are_fixed_and_never_retried`
  (renamed), `test_sdk_status_mapping_and_one_retry_layer` and
  `test_inherited_responses_route_keeps_adapter_handling` (a Responses reply
  without `output` gets four attempts).
- `test_faults.py::test_http_faults_retry_rate_limits_and_server_errors`
  (renamed) and
  `test_adapter_wiring.py::test_real_adapter_debug_never_reaches_results_logs_errors_or_records`.

## Local Verification

- `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/backfire --frozen
  --offline --no-sync pytest` on `test_failures.py`, `test_judge.py`,
  `test_provider.py`, `test_faults.py` and `test_adapter_wiring.py`, with
  `failures.py` from `8605cf2` → `25 failed, 247 passed`; with the fix →
  `272 passed`. The worker ran this, and the coordinator repeated it on the
  same tree.
- `npm run verify -- --task CHE-33 --base 8605cf2` on the worker's final tree
  (the committed `a93f7d8`) → `VERIFIED`; the backfire suite reported `1363
  passed, 3 deselected` in 161.89 s, against `1351 passed, 3 deselected` in
  177.94 s before the change.
- Manual checks: the coordinator reviewed the diff before the commit and sent
  one correction: the worker had deleted the empty, missing and null
  `choices` cases, which also checked the metadata capture of the earlier
  fix; they came back as their own test.

## Deviations from Assessment

- `test_faults.py` and `test_adapter_wiring.py` also encoded the old rule and
  failed the first full check; the coordinator added them to the worker's
  scope.
- `data-model.md` needed no change: its retry rows state the attempt limit and
  the time budget, not which failures are retried.

## Follow-ups

- The live check made five billed calls, and none met a provider failure, so
  the retry path is covered by the local replay tests only (see `test.md`).
