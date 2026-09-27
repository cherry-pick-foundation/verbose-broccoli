# Local System One Endpoint Contract

The endpoint is the server's child process and exists only inside one client
session. The copied transport is its only intended caller.

## Lifetime

- The server starts it with `backfire_backend serve` from the synced environment,
  with its standard input a pipe from the server and the session token in
  `BACKFIRE_ENDPOINT_TOKEN`.
- It binds a free `127.0.0.1` port, prints `{"port": <n>, "model": <model>}`
  as one line on its standard output, where `<model>` is the selected
  profile's model or null when the selection or the profile is invalid
  ([provider-profile.md](provider-profile.md)), and then logs only to stderr
  (status codes, error types and timings).
- It exits when its standard input ends, which happens when the server exits
  for any reason; it cancels its in-flight provider calls first. It writes no
  files.

## Address and authentication

- `POST http://127.0.0.1:<port>/v1/systemone`, where `<port>` is the port the
  endpoint reported at start.
- Header `Authorization: Bearer <token>`, where `<token>` is the session's
  random token. The token is checked before the body is read. A missing or
  different token, including another session's, gets 401 `unauthorized` and
  no provider call.
- Any other path or method gets 404.
- Trust boundary: the token keeps other OS accounts and other sessions out.
  Processes of the operator's own account can read the child's environment and
  the key file; that account is trusted.

## Request

`Content-Type: application/json`, body as defined in
[data-model.md](../data-model.md#judgment-request). The adapter validates the
questions, and the endpoint checks the request size limits, before any provider
call. The test-only `BACKFIRE_TEST_REQUEST_LIMITS=<options>,<cells>` replaces
both limits for the gate 3 probe, which starts its own endpoint; the server
never passes it to the endpoint it starts.

## Success response

HTTP 200 with `{model, answers, usage}` as defined in
[data-model.md](../data-model.md#judgment-response-and-error-response):

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

with the header
`X-Judgment-Metadata: {"attempts":1,"latency_ms":3412,"thinking_evidence":true,"reasoning_tokens":1022}`.

## Error responses

Body: `{"error": {"type": "<type>", "message": "<cause and corrective action>"}}`.
The message is fixed per type and may name an HTTP status; it never contains
request content, the provider's or the adapter's error text, credentials or
headers.
The copied transport shows the first 200 characters of this body to the agent,
as release 0.9.0 does. Every error after authentication carries the
`X-Judgment-Metadata` header.

| Status | Type | Cause |
| --- | --- | --- |
| 400 | `invalid_request` | Body is not JSON, or a question fails the adapter's schema |
| 401 | `unauthorized` | Missing or wrong session token |
| 422 | `request_limit_exceeded` | A Choice has more options than the option limit, or the request more cells than the cell limit |
| 502 | `backend_not_configured` | Profile selection or profile invalid, or credential file missing, empty or readable by group or others |
| 502 | `credential_rejected` | The provider answered 401, or a status the profile's `statuses` maps to this type |
| 502 | `balance_exhausted` | The provider answered a status the profile's `statuses` maps to this type (Hive: 405) |
| 502 | `request_rejected` | The provider answered 400, as Hive does for an unsupported setting or model, or a status the profile maps to this type |
| 502 | `rate_limited` | The provider answered 429, or a status the profile maps to this type, on the last allowed attempt, or its `Retry-After` does not fit the remaining time |
| 502 | `provider_unavailable` | Connection failures on every allowed attempt, or a read error or timeout after the request was sent |
| 502 | `provider_error` | Any other status, including 403, 404, 422 and every 5xx unless the profile maps it |
| 502 | `truncated_output` | The adapter's finish-reason check failed, or completion tokens reached the `max_tokens` that the profile's `request` sets |
| 502 | `malformed_output` | No choices, empty content, missing usage, or output that fails the adapter's answer schema (missing or extra labels, values outside [0, 1], not JSON) |
| 502 | `refused` | The response carries a refusal |
| 502 | `invalid_distribution` | A Choice or Score sum off by more than 0.01, or an all-zero distribution |
| 502 | `thinking_not_confirmed` | The profile requests thinking, and the response shows none of the thinking evidence the profile names |
| 502 | `model_not_confirmed` | The response names no model |
| 504 | `deadline_exceeded` | No valid answer within 80 s of receipt |

Standard statuses keep the meaning of the TypeSafe SDK's error classes, and
the selected profile's `statuses` overrides only those whose meaning differs
at its provider ([provider-profile.md](provider-profile.md)). For the Hive profile, 405 and 429
are documented by Hive, and 401 (invalid key) and 400 (unknown model, strict
JSON schema) were observed on 2026-09-26
([research.md](../research.md#hive-request-behavior--2026-09-26)).

## Retries and deadline

- The adapter's retry policy is the only retry layer: the TypeSafe SDK's
  `RetryPolicy` with at most four attempts in total, including the first.
  The transport runs with `JEV_MCP_MAX_ATTEMPTS=1`.
- Retried: 429 and any status the profile maps to `rate_limited`, and
  connection failures before the request reached the provider.
  `Retry-After` is honored; backoff otherwise starts at 1 s and doubles with
  jitter. A wait that would not fit the remaining time ends the request with
  the last error.
- Never retried: read errors and timeouts after the request was sent, every
  other status, and every answer failure (`truncated_output`,
  `malformed_output`, `refused`, `invalid_distribution`,
  `thinking_not_confirmed`, `model_not_confirmed`).
- A valid answer is final, whatever its confidence or outcome.
- Every request ends within 80 s of receipt: an outer timeout interrupts an
  attempt still in flight, since the retry policy's budget only stops further
  retries. The transport's deadline is 82 s, so the endpoint's answer or error
  always arrives first.

## Cancellation

When the caller closes the connection, the endpoint cancels the provider call
and any pending retry and sends nothing; the transport records the judgment as
`cancelled`. Charges already incurred at the provider are not reversed.

## Judgment metadata

The endpoint keeps no records. The `X-Judgment-Metadata` header
([data-model.md](../data-model.md#judgment-response-and-error-response)) gives
the transport what it cannot see in the body, and the transport writes the
judgment record ([data-model.md](../data-model.md#judgment-record)).
