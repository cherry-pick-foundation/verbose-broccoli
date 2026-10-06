# Bug Assessment: jev-mcp gate refuses concurrent first tool calls

- **Slug**: jev-mcp-cold-calls
- **Created**: 2026-10-06
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-95> (Linear issue
  CHE-95, read with `orca linear issue CHE-95 --json`; host `linear.app`,
  allowlisted), plus root's immutable synthetic receipt and the original
  report
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

CHE-95, "Fresh jev-mcp gate refuses concurrent first tool calls": four
concurrent first tool calls through a fresh gate can refuse three; one warm-up
call followed by the same concurrency passes. A local stdio fixture showed 1/4
cold successes against 4/4 warm, with zero model calls and no private registry
reads. The ticket says the cause is not established and warns against
inferring a schema-cache race from the symptom.

Receipts (immutable, outside the repository):

- `~/.local/state/verbose-broccoli/workspaces/develop/coordinator-takeover/attempt-20261006t121621z/gate-cold-call-synthetic-reproduction.json`
- original note `…/clean-architecture-structure/attempt-20261005T201530Z/gate-claude-code-meta-bug.md`
  ("second finding": three of four concurrent first calls refused, "likely
  while the gate fetched tool schemas").

## Symptom

On a fresh gate, concurrent `tools/call` requests that arrive before any
`tools/list` through the gate mostly get the fixed refusal. After one
successful call or one `tools/list`, all concurrent calls pass.

## Reproduction

1. Build the proxy over `tests/fixture_server.py` with a synthetic registry.
2. Open a frontend `Client(proxy)` and, without calling `list_tools()`, run
   four `echo` calls with `asyncio.gather`.
3. Three or four results are `is_error`. The existing tests never see this:
   their `connected()` helper calls `client.list_tools()` first
   (`tests/test_proxy.py:79`), which fills the gate's schema cache.

My own run of that scenario (a scratch script, synthetic only) printed
`cold [True, True, True, False]` and `warm [False, False, False, False]`,
matching root's receipt.

## Suspected Code Paths

- `packages/education-privacy-gate/src/education_privacy_gate/__main__.py:114-121`
  (at develop `87e9834`) — on the first call, `self.schemas is None`, so the
  gate runs `async with self.client: await self.client.list_tools()` on its
  own `Client`.
- `__main__.py:232-246` — `build_proxy` hands that same `client` to
  `PrivacyGate` and to `create_proxy`.
- `fastmcp/client/transports/stdio.py:98-124` (installed fastmcp 4.0.10) —
  `StdioTransport.connect` keeps one kept-alive session per transport and
  records the `TransportOptions` it was built for. If a second client asks for
  different options while a session is active, it raises `RuntimeError("This
  stdio transport has a live session built for different connection options
  and another client is still using it…")`.
- `fastmcp/server/providers/proxy.py:101-115` — proxy backend clients are
  built with `PROXY_TRANSPORT_OPTIONS` (a forwarding session class); the
  gate's own `Client` uses the default options.
- `__main__.py:169-179` — `on_list_tools` fills `self.schemas` through the
  proxy path, which is why a prior `tools/list` hides the bug.

## Root Cause Hypothesis

Not a race on the schema cache. The gate's schema fetch uses a second client on
the same stdio transport with different connection options than the proxy's
own backend clients. While the gate's cold-start session is active, the proxy's
concurrent backend connections get the transport's "different connection
options" `RuntimeError`, which the gate maps to the fixed refusal. I confirmed
this by turning the fixed refusal into a traceback in a scratch script (zero
model calls): the failing calls raise that exact `RuntimeError` from
`ProxyProvider._list_tools`, raised under `call_next`. Once the cache is warm
the gate's client is never used, so only proxy clients (one option set) touch
the transport. Confidence: high.

## Proposed Remediation

**Preferred**: stop opening a second client. On a cold cache, have the gate
obtain schemas through the proxy's own path: `await
context.fastmcp_context.fastmcp.list_tools()`, which runs `on_list_tools` (the
existing code that rejects output schemas and fills `self.schemas`), then fail
closed if the cache is still empty. This removes the gate's `client`
attribute and constructor argument (now unused), the `async with self.client`
block and the duplicate output-schema check. Net code goes down; no new
dependency.

**Alternatives**:

- Build the gate's client from `proxy.client_factory` so it shares the proxy's
  options. Keeps a second fetch path and the output-schema check twice.
- Serialize cold calls with a lock. Treats the symptom, not the cause, and
  would still conflict with a concurrent proxy `tools/list`.

**Files likely to change**:

- `packages/education-privacy-gate/src/education_privacy_gate/__main__.py`
- `packages/education-privacy-gate/tests/test_proxy.py` (new cold test;
  `PrivacyGate(None)` call sites lose the argument)

**Tests to add or update**:

- Four concurrent first `echo` calls through the full proxy with no warm-up,
  all succeeding and restoring correctly; it must fail on the old code.
- Cold first call with an upstream that advertises an output schema still
  refuses (fail-closed preserved).
- Keep every existing test; the shared `connected()` helper keeps its warm-up,
  so the new test uses its own cold connection.

## Risks & Considerations

- The proxy's `list_tools()` from inside a middleware call must not recurse or
  skip `on_list_tools`; verify with the cold test and the output-schema test.
- Schemas still come from the pinned upstream only; no schema from the caller
  is trusted.
- Masking, per-call stand-ins and error text are untouched.
- Metadata isolation is unaffected (CHE-94 is separate and changes a different
  block of the same function; the two edits are in different lines).

## Open Questions

- None blocking. Whether the registered Claude Code or Codex sessions send
  concurrent cold calls in practice is not established; the synthetic cause is.
