# Bug Assessment: jev-mcp gate refuses Codex tool-call metadata

- **Slug**: jev-mcp-codex-metadata
- **Created**: 2026-10-06
- **Source**: Linear issue CHE-94 (`https://linear.app/verbose-broccoli/issue/CHE-94`,
  host `linear.app`, allowlisted; not refetched here, the earlier
  `../jev-mcp-client-metadata/assessment.md` records it), plus root's
  immutable synthetic receipt and the native receipts named below
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

CHE-94 stays the one generic issue. The Claude Code half is repaired
(`../jev-mcp-client-metadata/`). A registered Codex call still got the fixed
refusal: the native acceptance run showed Claude succeeded through
`typesafe/jev-1.13` on OpenRouter, while Codex was refused before a provider,
model or usage could be observed.

Receipts, all outside the repository and immutable:

- `~/.local/state/verbose-broccoli/workspaces/develop/jev-mcp-native-acceptance/ctx_18bbc79c6eb4`
  and `.../ctx_ef419915b588` (the public native receipts).
- `~/.local/state/verbose-broccoli/workspaces/develop/coordinator-takeover/attempt-20261006t121621z/codex-metadata-synthetic-refusal.json`
  (zero model calls, zero private registry reads; an empty `_meta` control
  forwarded; `callId`, `threadId`, `sessionId` and `x-codex-turn-metadata`
  each alone were refused and not forwarded).

## Symptom

Codex 0.160.0 adds its own keys to the `_meta` of every `tools/call`. The gate
allows only MCP SDK keys, `progressToken`, the log level and the
`claudecode/`/`anthropic/` prefixes, so every Codex call is refused with the
fixed text and never forwarded. Expected: Codex's own keys are accepted and
discarded.

## Reproduction

1. Build the proxy over the synthetic fixture with a synthetic registry, as
   `tests/test_proxy.py` does.
2. Call `echo` with `meta={"callId": "call_synthetic"}`.
3. The result is the fixed refusal; the same call with no `_meta` succeeds.

## Suspected Code Paths

- `packages/education-privacy-gate/src/education_privacy_gate/__main__.py:93-100`
  (at develop `677216d`) — the key check refuses any `_meta` key outside the
  known set. `meta.clear()` just after it keeps frontend metadata off the
  upstream.
- Codex source, read-only cache
  `~/.cache/verbose-broccoli/workspaces/main/codex-src/codex` at tag
  `rust-v0.160.0`, commit `a956835d020762cb2b570053af06f643a11c0ecc`
  (paths under `codex-rs/`):
  - `core/src/mcp_tool_call.rs:1314-1367` `build_mcp_tool_call_request_meta`
    always inserts `callId`, and `x-codex-turn-metadata`
    (`core/src/client.rs:164`) when turn metadata exists. It also inserts
    connector-only keys (`MCP_TOOL_CODEX_APPS_META_KEY`, plugin id,
    confirmation policies) only for the Codex Apps server or when approval
    metadata names a plugin or connector.
  - `core/src/mcp_tool_call.rs:1403-1435` `with_mcp_tool_call_ids_meta` always
    inserts `threadId` and `sessionId`, and `windowId` / `itemId` when the call
    has an origin (constants at `:1257-1260`).
  - `rollout-trace/src/mcp.rs:10,36-63` adds `codex_bridge_mcp_call_id` when
    rollout tracing is enabled.
  - `core/src/mcp_tool_call.rs:847-896` adds the sandbox-state key only when
    the server advertises that capability. This tools-only gate does not.

## Root Cause Hypothesis

A closed allowlist written for the SDK keys and Claude Code's namespaces
omits the keys Codex sends on every call. Confidence: high (the synthetic
refusal and the source agree key by key). Not shown: which of the optional
keys the native Codex run carried; the receipt records the refusal only.

## Proposed Remediation

**Preferred**: add one constant `_CODEX_META` with the seven exact Codex keys
(`callId`, `threadId`, `sessionId`, `windowId`, `itemId`,
`x-codex-turn-metadata`, `codex_bridge_mcp_call_id`) and subtract it in the
key check. `meta.clear()` still runs before forwarding, so every key and value
is discarded. About 14 changed source lines. Do not add the sandbox-state key
(capability not advertised) or the connector, account and plugin keys, and do
not accept a generic `codex` namespace.

**Alternatives**: accept a `codex/` prefix or drop the key check. Both are
wider than the evidence supports; Codex sends unprefixed names.

**Files likely to change**:
- `packages/education-privacy-gate/src/education_privacy_gate/__main__.py`
- `packages/education-privacy-gate/tests/test_proxy.py`

**Tests to add or update**:
- Through the full proxy and fixture upstream: a call carrying all seven keys
  (identifying sentinel values, one holding a registered-looking name) succeeds
  and the upstream's `request_meta` holds none of the keys or values. It must
  fail on the old source.
- Near-miss and foreign keys (`callid`, `call_id`, `codex/callId`,
  `codex_apps`, `sandbox-state`, a known key beside a private key) and a
  string progress token still refuse, and a plain call after them succeeds.
  Boolean progress stays covered by the existing raw-wire test, because the
  SDK client coerces a boolean token before it is sent.

## Risks & Considerations

- A small widening of an input allowlist at the trust boundary; its protection
  is the existing `meta.clear()`, which this change must not move or weaken.
- The key list comes from one Codex tag. A later Codex release may add keys
  and refuse again; that needs new evidence.
- Native Codex acceptance is not shown by this fix; it needs a registered
  server on the merged code and a native call.

## Open Questions

- [NEEDS CLARIFICATION: native Codex acceptance after the repair; root decides
  when and whether to spend a paid call.]
