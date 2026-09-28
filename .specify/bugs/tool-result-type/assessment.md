# Bug Assessment: Backfire tool results lack resultType

- **Slug**: tool-result-type
- **Created**: 2026-09-28
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-16> (Linear issue
  CHE-16, read with `orca linear issue CHE-16 --json`; host `linear.app`,
  allowlisted)
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

CHE-16, "Backfire tool calls fail in Claude Code: tool results lack
resultType": no backfire tool call succeeds in Claude Code 2.1.283, while
Codex CLI works. Claude Code lists all 11 tools, but any call, for example
`backfire_classify`, fails with `Handler returned an invalid result`. Claude
Code uses MCP protocol 2026-07-28, whose `CallToolResult` requires a
`resultType` field. backfire's server returns tool results as a plain dict
without it, on purpose, and the pinned `mcp==2.2.0` validates results for that
protocol version and rejects the dict. Expected: tool results, including the
error replies the boundary builds, are valid under protocol 2026-07-28 and
still accepted by clients on older versions; a test that uses 2026-07-28 fails
without the fix. Feature 011's live client check (T020, CHE-9) found the bug.

## Symptom

Every `tools/call` from a client using protocol 2026-07-28 gets the JSON-RPC
error `-32603 Handler returned an invalid result` instead of the tool's
result, even when the judgment itself succeeded. Clients on protocol
2025-11-25 and older get the results as before.

## Reproduction

Protocol 2026-07-28 has no `initialize` handshake. Each request carries the
version in `params._meta["io.modelcontextprotocol/protocolVersion"]`, next to
`io.modelcontextprotocol/clientInfo` and
`io.modelcontextprotocol/clientCapabilities`. An `initialize` that proposes
2026-07-28 is answered with 2025-11-25, so a handshake-based test does not
reach the bug.

1. In a worktree at develop `969979d`, run `deno task backfire:install`.
2. Pipe these lines into `XDG_STATE_HOME=<temporary directory>
   packages/backfire/.venv/bin/backfire serve-mcp`:

   ```json
   {"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientInfo":{"name":"t","version":"1"},"io.modelcontextprotocol/clientCapabilities":{}}}}
   {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"nope","arguments":{},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientInfo":{"name":"t","version":"1"},"io.modelcontextprotocol/clientCapabilities":{}}}}
   ```

3. Observed on 2026-09-28: `tools/list` succeeds with `"resultType":"complete"`
   in its result. The `tools/call` for an unknown tool, which needs no
   judgment backend, gets `{"code":-32603,"message":"Handler returned an
   invalid result"}`, and stderr logs a pydantic error: `CallToolResult.resultType
   Field required`. The same call after an `initialize` handshake for
   2025-11-25 returns the expected `isError` result.

The same check without a server: in the backfire environment,
`serialize_server_result("tools/call", "2026-07-28", {"content": [...]})`
from `mcp_types.methods` raises `CallToolResult.resultType Field required`
with or without `isError`. With `"resultType": "complete"` added it passes,
and for 2025-11-25 the same function drops `resultType` from its output.

## Suspected Code Paths

- `packages/backfire/src/backfire/server.py:59-62` — `invoke()` returns
  `{"content": [...]}` or `{..., "isError": True}` without `resultType`. The
  comment says this is on purpose: a `CallToolResult` would add `isError:
  false` and `resultType`, which upstream jev-mcp's results do not have.
- `packages/backfire/.venv/lib/python3.14/site-packages/mcp/server/runner.py:377-386`
  (`mcp` 2.2.0, `_serialize`) — for spec methods it runs
  `serialize_server_result` for the request's protocol version and turns a
  validation failure into `Handler returned an invalid result`. Its later
  step that fills a missing `resultType` for 2026-07-28 runs only after that
  validation, so it never helps a core method's result.
- `packages/backfire/src/backfire/boundary.py:72-76` — `error_response()`
  builds the `deadline_exceeded` and `record_write_failed` replies itself and
  writes them past the SDK's serializer, also without `resultType`. A client
  on 2026-07-28 would receive an invalid result there too.
- `packages/backfire/src/backfire/boundary.py:170, 186` — `Boundary.call()`
  returns `types.CallToolResult(content=[], is_error=True)`. The typed model
  already sets `resultType: "complete"`, and for legacy versions the SDK drops
  it, so this path is not affected.

## Root Cause Hypothesis

backfire was written against the handshake protocol versions, where a result
without `resultType` is valid and the SDK passes the dict through as given.
`mcp` 2.2.0 also serves protocol 2026-07-28, in which `resultType` is a
required field of every result, and it validates core results against that
version's schema before sending them. The deliberate plain dict therefore
fails validation for every modern-protocol tool call. Confidence: high; the
failure reproduces over stdio and in the serializer alone.

## Proposed Remediation

**Preferred**: Add `"resultType": "complete"` to the dict that `invoke()`
returns, for both success and error results, and update the comment. The SDK
keeps it for 2026-07-28 and drops it for older versions, so older clients see
the same bytes as before and upstream fidelity on the legacy wire is kept. Add
the same field to `error_response()`. Those replies bypass the SDK, so older
clients would receive the extra field. `mcp` 2.2.0's legacy result models
accept and drop unknown fields (the surface models use `extra="ignore"`, as
`serialize_server_result`'s docstring in `mcp_types/methods.py` says), and
the issue reports that older clients ignore it; Codex CLI is the older client
to confirm this with.

**Alternatives**:
- Return `types.CallToolResult` from `invoke()`. It adds `isError: false` to
  successful results on every version, which changes the legacy wire output
  that the port keeps equal to upstream.
- In the boundary, send `resultType` only for calls whose request carried the
  modern `_meta` protocol-version key. Older clients would then get
  byte-identical error replies, at the cost of a per-call flag and a second
  shape for each error reply.

**Files likely to change**:
- `packages/backfire/src/backfire/server.py`
- `packages/backfire/src/backfire/boundary.py`
- tests under `packages/backfire/tests/`, and any existing test that compares
  a whole boundary error reply

**Tests to add or update**:
- A test that talks to the server with requests in the 2026-07-28 envelope,
  over stdio as Claude Code does, calls a tool and gets a valid result with
  `resultType: "complete"`. It must fail on develop `969979d`.
- A 2026-07-28 test for a boundary error reply, such as `deadline_exceeded`
  with a stalled scripted judge, that checks the reply validates against the
  2026-07-28 `CallToolResult` schema.
- A check that a 2025-11-25 session still gets the same tool results as
  before, without `isError: false` added and without `resultType` from the
  SDK path.

## Risks & Considerations

- The SDK also stamps `_meta["io.modelcontextprotocol/serverInfo"]` on
  2026-07-28 results it serializes. The boundary's own error replies will not
  have it; `serialize_server_result` does not require it, but whether Claude
  Code expects it is unverified.
- `result_digest` in tool-call records is the digest of the wire result, so
  records of modern-protocol calls will digest a result that includes
  `resultType`. Records of legacy calls do not change.
- Only a live call from Claude Code 2.1.283 proves the fix end to end. That
  check is billed; CHE-9 reruns its own Claude Code check after this merges.

## Open Questions

- None.
