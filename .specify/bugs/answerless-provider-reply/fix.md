# Bug Fix: A provider reply without an answer is reported as malformed_output

- **Slug**: answerless-provider-reply
- **Fixed**: 2026-09-29
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

A 2xx reply that carries no answer is now `provider_error` instead of
`malformed_output`: a body that is not JSON or not a JSON object, a Chat
Completions reply whose `choices` is missing, null, not a list or empty, and a
Responses API reply whose `output` is missing, null or not a list. A provider
that sends HTTP 200 before the model finishes, and later writes an error
object into the body, is now reported as the provider's failure. A Codex worker
(`gpt-6-luna`, effort `max`) implemented the change in `0eb9b8b`.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/backfire/src/backfire/provider.py` | modified | `ProfileProvider.request`: the two body checks raise `provider_error`, and a new check for the answer container runs after the model, usage and thinking-evidence capture, just before the `malformed_output` check. |
| `packages/backfire/tests/test_provider.py` | modified | One new test and four updated tests; see below. |
| `specs/005-jev-decision-backend/contracts/judgment.md` | modified | Error table: the `provider_error` row names success replies without an answer; "No choices" leaves the `malformed_output` row. |
| `docs/backfire.md` | modified | Troubleshooting table: `provider_error` also covers a success status with no answer in the reply. |

## Diff Highlights (optional)

```python
if self.api == "responses":
    if not isinstance(output, list):
        raise JudgmentError("provider_error")
elif not isinstance(choices, list) or not choices:
    raise JudgmentError("provider_error")
if (self.api != "responses" and not isinstance(message, dict)) or call.usage is None:
    raise JudgmentError("malformed_output")
```

Because the check runs after the capture, a reply without an answer that
still names its model or reports usage keeps them in the session record. The
provider's billed tokens stay visible there.

## Tests Added or Updated

- `test_provider.py::test_answerless_provider_error_body_is_sanitized_and_not_retried`
  — the test provider answers HTTP 200 with eight spaces and then
  `{"status_code":500,"message":"Internal Server Error"}`, the body observed in
  the assessment's step 8. The call is `provider_error`, is sent once, and the
  reply text appears neither in the error nor in the output. Before the fix it
  was `malformed_output`.
- `test_provider.py::test_response_failures_are_fixed_and_never_retried` —
  `empty_choices`, `missing_choices` and `null_choices` now expect
  `provider_error`, and these cases check that the record fields keep the
  reported model, usage, reasoning tokens and thinking evidence.
- `test_provider.py::test_malformed_envelopes_fail_without_raw_diagnostics` —
  invalid JSON, `[]`, `null` and a non-list `choices` expect `provider_error`;
  `{"choices": [null]}` still expects `malformed_output`.
- `test_provider.py::test_inherited_responses_route_keeps_adapter_handling` —
  a new `missing_output` case expects `provider_error`; the `incomplete` case
  (empty `output`) still expects `truncated_output`.

## Local Verification

- Commands run: `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/backfire
  --frozen --offline --no-sync pytest packages/backfire/tests/test_provider.py
  -q` with `provider.py` from `712c3ed` (before the fix) → `18 failed, 102
  passed`; the same on `0eb9b8b` → `120 passed`.
- `deno task verify --task CHE-22 --base 2262815` with a plan covering these
  files, on `0eb9b8b` → workflow `VERIFIED`, exit code 0; the backfire suite
  reported `1351 passed, 3 deselected`. `node` 24.19.0 from `mise` was first on
  `PATH`, because the `mise` shim has no default version in this shell.
- Manual checks: the coordinator reviewed the diff before the commit.

## Deviations from Assessment

- The assessment counted an empty Responses `output` list as "no answer". A
  Responses reply with status `incomplete` (for example at
  `max_output_tokens`) has an empty `output`, and the adapter reports it as
  `truncated_output`. The first implementation turned that case into
  `provider_error`, which the review caught. So for the Responses API only a
  missing, null or non-list `output` is `provider_error`; the contract says
  so.
- The assessment placed the new check with the body checks. It runs later,
  after the model, usage and thinking capture, so the record keeps what the
  provider reported.

## Follow-ups

- The document judgment step still fails while the provider has an episode of
  server errors; the caller reruns it later. The failure now names the
  provider.
