# Bug Fix: Backfire tool results lack resultType

- **Slug**: tool-result-type
- **Fixed**: 2026-09-28
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Every tool result backfire sends now carries `"resultType": "complete"`, as
protocol 2026-07-28 requires. The handler's results get it in
`create_server()`'s `invoke()`, and the SDK drops it again for older protocol
versions, so their wire output is unchanged. The boundary's own
`deadline_exceeded` and `record_write_failed` replies get it in
`error_response()`; they bypass the SDK, so clients on every version receive
the field there.

The line numbers in the assessment's Suspected Code Paths refer to develop
`969979d`, before the fix.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/backfire/src/backfire/server.py` | modified | `invoke()` adds `resultType` to success and error results; comment updated. |
| `packages/backfire/src/backfire/boundary.py` | modified | `error_response()` adds `resultType`. |
| `packages/backfire/tests/test_boundary.py` | modified | Two 2026-07-28 tests, a legacy wire check, the `server()` helper's `call_seconds` option, and the updated `record_write_failed` reply. |
| `packages/backfire/tests/test_boundary_core.py` | modified | The deadline test's record digest includes `resultType`. |

## Diff Highlights (optional)

The result stays a dict, not `types.CallToolResult`. The typed model would add
`isError: false` to successful results on every version, which the port's
upstream results do not have.

The subprocess tests' `server()` helper can now shorten `CALL_SECONDS` in the
server process. It writes the setting into the `sitecustomize.py` that the
stream probe already uses.

## Tests Added or Updated

- `test_boundary.py::test_protocol_2026_tool_result_is_complete` — starts
  `python -m backfire serve-mcp`, sends a `backfire_noul` call in the
  2026-07-28 envelope (no `initialize`; the version, client info and
  capabilities in `params._meta`), and checks that the reply is a result with
  `resultType: "complete"`. Before the fix the reply is the JSON-RPC error
  `Handler returned an invalid result`.
- `test_boundary.py::test_protocol_2026_deadline_reply_validates` — the same
  envelope with a stalled scripted judge and a 0.05-second deadline; the
  `deadline_exceeded` reply must equal its own
  `serialize_server_result("tools/call", "2026-07-28", ...)` output.
- `test_boundary.py::test_messages_pass_unchanged_and_every_call_is_recorded_before_reply`
  — its 2025-11-25 results must have no `resultType` and no `isError: false`.
- `test_boundary.py::test_record_write_failure_withholds_result_and_session_recovers`
  and `test_boundary_core.py::test_deadline_cancels_work_and_session_still_serves`
  — expect `resultType` in the boundary's replies. The second one reads that
  reply through the SDK's own client on a 2025-11-25 session, so the older
  client accepts the extra field.

## Local Verification

Reported by the implementing Codex worker (`gpt-6-luna`, max effort; Orca
dispatch `ctx_8c8b51c9b865`):

- `test_protocol_2026_tool_result_is_complete` on the unchanged source: 1
  failed with `Handler returned an invalid result`; after the fix: 1 passed.
- `pytest packages/backfire/tests -m 'not slow'`: 1236 passed, 3 deselected.
- `deno task verify --task CHE-16 --base 3c42b16`: `VERIFIED`, with Node 24
  from `mise` on `PATH`.

The coordinator's own verification is in [test.md](test.md).

## Deviations from Assessment

None.

## Follow-ups

- The boundary's error replies have no `_meta` server-info stamp, which the
  SDK adds to 2026-07-28 results it serializes; see the assessment's risks.
- Claude Code 2.1.283 has not called the fixed server yet. CHE-9's live
  client check reruns its Claude Code half after this merges.
