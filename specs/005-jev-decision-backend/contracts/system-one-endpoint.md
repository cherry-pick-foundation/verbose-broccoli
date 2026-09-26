# Local System One Endpoint Contract

The endpoint is the server's child process and exists only inside one client
session. The copied transport is its only intended caller.

## Lifetime

- The server starts it with `backfire_backend serve` from the synced environment,
  with its standard input a pipe from the server and the session token in
  `BACKFIRE_ENDPOINT_TOKEN`.
- It binds a free `127.0.0.1` port, prints `{"port": <n>}` as one line on its
  standard output, and then logs only to stderr (status codes, error types and
  timings).
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
call.

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
request content, Hive's or the adapter's error text, credentials or headers.
The copied transport shows the first 200 characters of this body to the agent,
as release 0.9.0 does. Every error after authentication carries the
`X-Judgment-Metadata` header.

| Status | Type | Cause |
| --- | --- | --- |
| 400 | `invalid_request` | Body is not JSON, or a question fails the adapter's schema |
| 401 | `unauthorized` | Missing or wrong session token |
| 422 | `request_limit_exceeded` | A Choice has more options than the option limit, or the request more cells than the cell limit |
| 502 | `backend_not_configured` | Credential file missing, empty or readable by group or others |
| 502 | `credential_rejected` | Hive answered 401 |
| 502 | `balance_exhausted` | Hive answered 405 |
| 502 | `request_rejected` | Hive answered 400, as it does for an unsupported setting or model |
| 502 | `rate_limited` | Hive answered 429 on the last allowed attempt, or its `Retry-After` does not fit the remaining time |
| 502 | `provider_unavailable` | Connection failures on every allowed attempt, or a read error or timeout after the request was sent |
| 502 | `provider_error` | Any other status, including 403, 404, 422 and every 5xx |
| 502 | `truncated_output` | Completion tokens reached `max_tokens` |
| 502 | `malformed_output` | No choices, empty content, missing usage, or output that fails the adapter's answer schema (missing or extra labels, values outside [0, 1], not JSON) |
| 502 | `refused` | The response carries a refusal |
| 502 | `invalid_distribution` | A Choice or Score sum off by more than 0.01, or an all-zero distribution |
| 502 | `thinking_not_confirmed` | The response carries neither reasoning content nor reasoning tokens |
| 502 | `model_not_confirmed` | The response names no model |
| 504 | `deadline_exceeded` | No valid answer within 80 s of receipt |

Status evidence: 405 and 429 are documented by Hive; 401 (invalid key) and 400
(unknown model, strict JSON schema) were observed on 2026-09-26
([research.md](../research.md#hive-request-behavior--2026-09-26)).

## Retries and deadline

- The adapter's retry policy is the only retry layer: the TypeSafe SDK's
  `RetryPolicy` with at most four attempts in total, including the first.
  The transport runs with `JEV_MCP_MAX_ATTEMPTS=1`.
- Retried: 429, and connection failures before the request reached Hive.
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
`cancelled`. Charges already incurred at Hive are not reversed.

## Judgment metadata

The endpoint keeps no records. The `X-Judgment-Metadata` header
([data-model.md](../data-model.md#judgment-response-and-error-response)) gives
the transport what it cannot see in the body, and the transport writes the
judgment record ([data-model.md](../data-model.md#judgment-record)).
