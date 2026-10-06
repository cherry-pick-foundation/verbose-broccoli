# Bug Assessment: jev-mcp gate refuses Claude Code tool-use metadata

- **Slug**: jev-mcp-client-metadata
- **Created**: 2026-10-06
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-94> (Linear issue
  CHE-94, read with `orca linear issue CHE-94 --json`; host `linear.app`,
  allowlisted), plus root's immutable synthetic receipt and the original
  report (paths below)
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

CHE-94, "Registered jev-mcp calls refuse client tool-use metadata": the
registered jev-mcp privacy gate rejects Claude Code's tool-use metadata before
forwarding the tool request. A synthetic reproduction showed that
`claudecode/toolUseId` and `claudecode/agentId` are refused while a control
request and an integer progress token pass. Registered Codex refusals are also
reported; their exact cause is unconfirmed.

Original report (2026-10-06, develop's clean-architecture session): in a Claude
Code session every call to the registered `jev-mcp` server returned "Privacy
gate rejected the call." at once, even a one-line `jev_noul` call, while the
same calls through the same gate code from an in-process FastMCP client passed.

Receipts, all outside the repository and immutable:

- `~/.local/state/verbose-broccoli/workspaces/develop/coordinator-takeover/attempt-20261006t121621z/gate-metadata-synthetic-reproduction.json`
  (six synthetic middleware cases, zero model calls, zero private registry
  reads: plain and integer-progress controls forwarded; `claudecode/toolUseId`,
  `claudecode/agentId`, string progress and boolean progress refused).
- `~/.local/state/verbose-broccoli/workspaces/develop/clean-architecture-structure/attempt-20261005T201530Z/gate-claude-code-meta-bug.md`
  and its `scripts/gate_meta_test.py` (read in full before relying on it).

## Symptom

Claude Code adds its own keys to the `_meta` of every `tools/call`; the gate's
allowlist does not know them, so it returns the fixed refusal and never
forwards the call. Expected: documented client metadata is accepted and
discarded, and nothing from it reaches the hidden upstream.

## Reproduction

1. Build the proxy over the synthetic fixture (`tests/fixture_server.py`) with
   a synthetic registry, as `tests/test_proxy.py` does.
2. Call `echo` with `meta={"claudecode/toolUseId": "toolu_synthetic"}`.
3. The result is the fixed refusal. The same call with no `_meta`, or with an
   integer `progressToken`, succeeds.

No model call and no private registry read is needed.

## Suspected Code Paths

- `packages/education-privacy-gate/src/education_privacy_gate/__main__.py:87-102`
  (at develop `87e9834`) — `on_call_tool` raises `GateError` for any `_meta`
  key outside `_CONNECTION_META`, `progressToken` and the log-level key. This
  is the refusal.
- `__main__.py:111-112` — `meta.clear()` empties the request's `_meta` after the
  check. This matters: FastMCP's proxy forwards the inbound request's
  application `_meta` to the backend
  (`fastmcp/server/providers/proxy.py:173-189`, `_forwardable_request_meta`),
  so the clear is what keeps frontend metadata off the upstream.
- `docs/jev-mcp.md:175-178` — states that other application `_meta` keys
  reject.
- `tests/test_proxy.py:333-337` and `543-551` — existing negative cases for a
  private `_meta` key and string progress tokens; they must keep passing.

Evidence about what clients send (read-only `grep -a` of installed binaries, no
user configuration read):

- Claude Code (`@anthropic-ai/claude-code` binary, 2.x): the strings
  `claudecode/toolUseId`, `claudecode/agentId`, `claudecode/agentType`,
  `claudecode/isObserver`, `claudecode/remoteToolCall`, and
  `anthropic/requestId`. Its tool-call meta is built as
  `{...mcpRequestMeta, <progress key>, "claudecode/toolUseId": id,
  ...requestId meta, ...event-link meta, ...agent meta}`; the agent meta
  carries `claudecode/agentId`, optionally `agentType` and `isObserver`. These
  keys come from the binary, not from public documentation; other keys from the
  event-link function were not resolved.
- Codex 0.160.0: no MCP `_meta` key was confirmed. The binary holds
  `x-codex-turn-metadata` (also an HTTP header name) and `codex/imageDetail`;
  whether either is sent as tool-call `_meta` is not established. **The Codex
  refusal stays unconfirmed; this fix makes no Codex claim.**

## Root Cause Hypothesis

A closed allowlist of `_meta` keys written against the MCP SDK's own keys only.
Claude Code uses the MCP-permitted vendor-prefixed `_meta` namespace
(`claudecode/…`, `anthropic/…`), so each of its calls trips the check. The
check exists to keep frontend metadata off the upstream, but `meta.clear()`
already guarantees that, so refusing is stricter than the protection needs.
Confidence: high for the Claude Code refusal (reproduced; the code path is
direct); not applicable for Codex (unconfirmed).

## Proposed Remediation

**Preferred**: accept `_meta` keys in the client vendor namespaces
`claudecode/` and `anthropic/`, whatever their values, and keep everything
else as is: the existing `meta.clear()` discards them before forwarding; other
unknown keys, string or boolean progress tokens and bad log levels still
refuse. About 5 changed lines in `on_call_tool` plus a module constant, one
sentence in `docs/jev-mcp.md`, and the module docstring. Use `str.startswith`
with a tuple; no new dependency.

**Alternatives**:

- Accept exactly the five observed `claudecode/*` names plus
  `anthropic/requestId`. Stricter, but Claude Code added keys between versions
  and one unresolved key group exists, so the next release could repeat the
  refusal.
- Drop the key check entirely and rely on `meta.clear()`. Smallest, but it
  weakens the deliberate refusal of unknown application metadata, which the
  user's earlier decision and the existing tests keep.

**Files likely to change**:

- `packages/education-privacy-gate/src/education_privacy_gate/__main__.py`
- `packages/education-privacy-gate/tests/test_proxy.py`
- `docs/jev-mcp.md` (the sentence at lines 175-178 that says other `_meta`
  keys reject)

**Tests to add or update**:

- Through the full proxy and fixture upstream: a call with
  `claudecode/toolUseId` and `claudecode/agentId` values succeeds, and the
  upstream's `request_meta` contains none of those keys nor their values. It
  must fail on the old code.
- Middleware level: `anthropic/requestId` accepted; a near-miss prefix
  (`claudecode` without slash, `xclaudecode/…`), a private unprefixed key,
  string and boolean progress tokens still refuse.
- Keep all existing negative and masking cases unchanged.

## Risks & Considerations

- A client could put registered names inside a `claudecode/…` value. The value
  is cleared before forwarding and never logged, restored or relayed; the test
  checks a registered-looking value does not reach the upstream.
- Accepting a namespace is a small widening of an input allowlist at the trust
  boundary; the user should see this in the review. Its protection is the
  existing `meta.clear()`, which this change must not move or weaken.
- No claim about Codex. If Codex's refusing key is later found, it needs its
  own evidence.
- The fix covers the gate. Registered Claude Code activation (the registered
  server running the new code) is outside this worktree.

## Open Questions

- [NEEDS CLARIFICATION: exact `_meta` keys the registered Codex sends; no
  evidence yet, and no private input may be read to get it.]
