# Judgment Contract

The judge answers one judgment request inside its caller's process
([research.md](../research.md#python-package--2026-09-27)). Its callers are the
ported tools, inside the server, and three direct callers: the readiness check,
the gate 3 request-limit probe and the benchmark runner. There is one judge
implementation for all of them. It replaces the local System One endpoint of
the two-runtime design: there is no HTTP endpoint, session token, port line or
metadata header.

## Request

A request is the `state` and `questions` of
[data-model.md](../data-model.md#judgment-request), with the caller's deadline
and, inside the server, the session's record file. A tool's request takes the
deadline of its tool call from the MCP boundary; a direct caller sets a
deadline 118 s after the judgment starts and passes no record file. The judge
sends them with the selected profile's model
([provider-profile.md](provider-profile.md)) to `system-one-adapter` 0.2.1's
asynchronous client, which uses the profile-driven provider subclass. Before
any provider call:

- the adapter validates the questions;
- the judge checks the request size limits: a Choice with more options than the
  option limit, or a request with more answer cells than the cell limit, fails
  with `request_limit_exceeded`. The test-only
  `BACKFIRE_TEST_REQUEST_LIMITS=<options>,<cells>` replaces both limits for the
  gate 3 probe only;
- the judge loads the configuration and the credential; any problem fails with
  `backend_not_configured`.

## Result

`{model, answers, usage}` as defined in
[data-model.md](../data-model.md#judgment-response-and-error-response), where
`model` is the model the provider's response names:

```json
{
  "model": "deepseek-ai/deepseek-v4.1-flash",
  "answers": {
    "is_urgent": {"type": "noul", "noul": 0.93},
    "department": {
      "type": "choice",
      "choice": "billing",
      "confidence": 0.955,
      "probabilities": {"billing": 0.97, "shipping": 0.01, "returns": 0.02}
    }
  },
  "usage": {"input_tokens": 761, "output_tokens": 1469}
}
```

The judge also fills the call's judgment metadata, which the judgment record
takes ([data-model.md](../data-model.md#judgment-record)): `attempts`,
`latency_ms`, `thinking_evidence` (true when the response showed the thinking
evidence the profile names, null without a provider response) and
`reasoning_tokens` (or null). The metadata holds no other field and no text.

## Errors

A failed judgment raises an error whose text, which the agent sees as the
tool's error, is `<type>: <message>`. The message is fixed per type and names
the cause and the corrective action; it never contains request content, the
provider's or the adapter's error text, credentials or headers. No error
returns an answer or a default.

| Type | Cause |
| --- | --- |
| `invalid_request` | A question fails the adapter's schema |
| `request_limit_exceeded` | A Choice has more options than the option limit, or the request more cells than the cell limit |
| `backend_not_configured` | The configuration, the selected profile or the credential file is missing or invalid ([provider-profile.md](provider-profile.md), [configuration.md](configuration.md)) |
| `credential_rejected` | The provider answered 401, or a status the profile's `statuses` maps to this type |
| `balance_exhausted` | The provider answered a status the profile's `statuses` maps to this type (Hive: 405) |
| `request_rejected` | The provider answered 400, as Hive does for an unsupported setting or model, or a status the profile maps to this type |
| `rate_limited` | The provider answered 429, or a status the profile maps to this type, on the last allowed attempt, or its `Retry-After` does not fit the time left |
| `provider_unavailable` | Connection failures on every allowed attempt, or a read error or timeout after the request was sent |
| `provider_error` | Any other status, including 403, 404, 422 and every 5xx unless the profile maps it |
| `truncated_output` | The adapter's finish-reason check failed, or completion tokens reached the `max_tokens` that the profile's `request` sets |
| `malformed_output` | No choices, empty content, missing usage, or output that fails the adapter's answer schema (missing or extra labels, values outside [0, 1], not JSON) |
| `refused` | The response carries a refusal |
| `invalid_distribution` | A Choice or Score sum off by more than 0.01, or an all-zero distribution |
| `thinking_not_confirmed` | The profile requests thinking, and the response shows none of the thinking evidence the profile names |
| `model_not_confirmed` | The response names no model |

Standard statuses keep the meaning of the TypeSafe SDK's error classes, and
the selected profile's `statuses` overrides only those whose meaning differs
at its provider. For the Hive profile, 405 and 429 are documented by Hive, and
401 (invalid key) and 400 (unknown model, strict JSON schema) were observed on
2026-09-26 ([research.md](../research.md#hive-request-behavior--2026-09-26)).

## Retries and time

- The adapter's retry policy is the only retry layer: the TypeSafe SDK's
  `RetryPolicy` with at most four attempts in total, including the first.
- Retried: 429 and any status the profile maps to `rate_limited`, and
  connection failures before the request reached the provider. `Retry-After`
  is honored; backoff otherwise starts at 1 s and doubles with jitter. A wait
  that would not fit the time left ends the request with the last error.
- Never retried: read errors and timeouts after the request was sent, every
  other status, and every answer failure (`truncated_output`,
  `malformed_output`, `refused`, `invalid_distribution`,
  `thinking_not_confirmed`, `model_not_confirmed`).
- A valid answer is final, whatever its confidence or outcome.
- The time left is what remains of the caller's deadline, for a tool the
  call's 118 s deadline ([mcp-server.md](mcp-server.md#deadline)); each
  attempt's timeout and every retry wait stay within it.

## Cancellation

When the caller cancels the judgment, for a tool when the client cancels the
call or at its deadline, the judge cancels the provider request and any
pending retry and returns nothing; with a record file, the judgment record
shows `cancelled`. Charges already incurred at the provider are
not reversed.
