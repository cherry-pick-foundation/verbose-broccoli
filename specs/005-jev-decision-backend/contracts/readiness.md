# Readiness Report Contract

## Invocation

`uv --directory <plugin root>/backfire run --frozen --offline --no-sync
backfire ready`; the repository's `deno task backfire:ready` runs the same
command for `packages/backfire/`. It needs the copy's installed environment
([mcp-server.md](mcp-server.md#entry-commands)), the credential and network
access, and makes real, billed judgments.

## Checks

1. Configuration: the profile selection and the selected profile are valid
   ([provider-profile.md](provider-profile.md)); the profile's credential file
   exists, is non-empty and has mode 0600; the record directory can be created,
   locked and written.
2. Installation: this copy's `.venv` matches `uv.lock` and
   `.python-version`, and imports `backfire` from this component's
   `src/backfire/`; `src/backfire/UPSTREAM.md` names the ported revision.
3. One judgment through the in-process judge as a direct caller
   ([judgment.md](judgment.md#request)): a Noul question with a known answer.
4. Tool path: a short MCP session through `serve-mcp`, including the MCP
   boundary, that lists the tools and calls `backfire_noul` and `backfire_extract` once
   each, then checks that both calls left tool-call records whose input digests
   match.

## Output

JSON on stdout, then a short human summary on stderr. `requested` repeats the
selected profile: its name as `provider`, its `api`, its `base_url` as
`endpoint`, its `model` and its `thinking.requested`. With the Hive profile:

```json
{
  "requested": {
    "provider": "hive",
    "api": "openai",
    "endpoint": "https://api-cdn.thehive.ai/api/v3",
    "model": "deepseek-ai/deepseek-v4.1-flash",
    "thinking": "on"
  },
  "confirmed": {
    "provider": "hive",
    "model": "deepseek-ai/deepseek-v4.1-flash",
    "thinking": "on"
  },
  "unconfirmed": [],
  "tool_checks": [
    {"tool": "tools/list", "passed": true, "detail": "11 tools"},
    {"tool": "backfire_noul", "passed": true, "detail": "expected verdict, record digest matches"},
    {"tool": "backfire_extract", "passed": true, "detail": "verbatim value, record digest matches"}
  ],
  "sample": {"question": "noul", "answer": 0.99, "latency_ms": 3400},
  "versions": {
    "jev_mcp_port": "0.9.0 ported from a1fcc1e47fc696614f081e23a66ff48a890f22fd",
    "mcp": "2.2.0",
    "rfc8785": "0.1.4",
    "system_one_adapter": "0.2.1",
    "typesafe_sdk": "0.7.1",
    "openai": "<from uv.lock>",
    "python": "3.14.4",
    "uv": "0.11.32",
    "prompt_sha256": "<digest of the adapter prompt text>"
  }
}
```

## Confirmation rules

- `confirmed.provider` is set only when the profile's `base_url` answered the
  request.
- `confirmed.model` is the `model` field of the provider's response to that
  request. If the provider omits it or names a different model, it is absent
  and `unconfirmed` holds the reason.
- `confirmed.thinking` is `on` only when that response showed the thinking
  evidence the profile names (for Hive, a non-empty `reasoning_content` or a
  positive `usage.reasoning_tokens`). Otherwise it is absent and `unconfirmed`
  holds `{"item": "thinking", "reason": "<what was missing>"}`. When the
  profile requests thinking `off`, `requested.thinking` is `off`, thinking is
  not a confirmation item, and it appears in neither `confirmed` nor
  `unconfirmed`.
- When `BACKFIRE_TEST_PROVIDER_BASE_URL` is set, the report says so.
- Every requested item that could not be confirmed appears in `unconfirmed`
  with a reason; nothing is marked confirmed because configuration says so.

## Exit status

0 when every item is confirmed and every tool check passed; 1 otherwise. A
missing credential or installation exits 1 before any network call, with the
corrective action in the summary.
