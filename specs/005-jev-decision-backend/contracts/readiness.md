# Readiness Report Contract

## Invocation

`<plugin root>/backfire/bin/backfire ready`; the repository's `deno task backfire:ready` calls
it. It needs the installed cache, the credential and network access, and makes
real, billed judgments.

## Checks

1. Configuration: the credential file exists, is non-empty and has mode 0600;
   the record directory can be created, locked and written.
2. Installation: the Python environment matches `uv.lock` and
   `.python-version`; the server's npm packages are in Deno's cache as the
   component's `deno.lock` pins them; `deno` is 2.9.6; the files in `upstream/`
   match the hashes that `upstream/upstream.json` records for the copy.
3. One judgment through the local endpoint: a Noul question with a known answer.
4. Tool path: a short MCP session through `serve-mcp`, including the MCP
   boundary, that lists the tools and calls `backfire_noul` and `backfire_extract` once
   each, then checks that both calls left tool-call records whose input digests
   match.

## Output

JSON on stdout, then a short human summary on stderr:

```json
{
  "requested": {
    "provider": "hive",
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
    "jev_mcp_source": "0.9.0 at a1fcc1e47fc696614f081e23a66ff48a890f22fd",
    "mcp_sdk": "1.30.1",
    "zod": "4.6.5",
    "typesafe_js_sdk": "0.6.0",
    "canonicalize": "5.0.0",
    "deno": "2.9.6",
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

- `confirmed.provider` is set only when the Hive endpoint answered the request.
- `confirmed.model` is the `model` field of Hive's response to that request. If
  Hive omits it or names a different model, it is absent and `unconfirmed`
  holds the reason.
- `confirmed.thinking` is `on` only when that response carried a non-empty
  `reasoning_content` or a positive `usage.reasoning_tokens`. Otherwise it is
  absent and `unconfirmed` holds `{"item": "thinking", "reason": "<what was
  missing>"}`.
- Every requested item that could not be confirmed appears in `unconfirmed`
  with a reason; nothing is marked confirmed because configuration says so.

## Exit status

0 when every item is confirmed and every tool check passed; 1 otherwise. A
missing credential or installation exits 1 before any network call, with the
corrective action in the summary.
