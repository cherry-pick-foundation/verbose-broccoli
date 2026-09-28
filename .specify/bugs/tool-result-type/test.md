# Bug Verification: Backfire tool results lack resultType

- **Slug**: tool-result-type
- **Tested**: 2026-09-28
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

A tool call in the 2026-07-28 envelope now gets a valid result instead of
`Handler returned an invalid result`, and the boundary's deadline reply
validates against that version's schema. The two new tests fail on the source
before the fix and pass after it. The full repository check passes on the
branch after `develop` (`67074dd`) was merged into it.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (pre-fix) | The two new tests with `server.py` and `boundary.py` checked out from `3c42b16`: `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/backfire --frozen --offline --no-sync pytest packages/backfire/tests/test_boundary.py::test_protocol_2026_tool_result_is_complete packages/backfire/tests/test_boundary.py::test_protocol_2026_deadline_reply_validates -q` | fail, as expected | `2 failed`: the call gets the JSON-RPC error `-32603 Handler returned an invalid result`, and the deadline reply fails validation with `CallToolResult.resultType Field required`. |
| Reproduction (post-fix) | the same command on `8678398` | pass | `2 passed in 1.77s`. |
| Older protocol versions | `test_messages_pass_unchanged_and_every_call_is_recorded_before_reply` and `test_deadline_cancels_work_and_session_still_serves`, in the package suite below | pass | 2025-11-25 handler results are unchanged; the SDK client on 2025-11-25 reads a boundary reply that carries `resultType`. |
| Package suite | `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/backfire --frozen --offline --no-sync pytest packages/backfire/tests -m 'not slow' -q` on `49d50b6` | pass | `1236 passed, 3 deselected`. |
| Regression suite, lint, type-check | `deno task verify --task CHE-16 --base 3c42b16` on `8678398`, and again on `49d50b6` (the fix merged with `develop` `67074dd`) | pass | Workflow `VERIFIED`, exit code 0 both times, with `node` 24.19.0 from `mise` on `PATH`. |

## Output Excerpts

```text
FAILED packages/backfire/tests/test_boundary.py::test_protocol_2026_tool_result_is_complete
FAILED packages/backfire/tests/test_boundary.py::test_protocol_2026_deadline_reply_validates
2 failed in 1.85s

2 passed in 1.77s

1236 passed, 3 deselected in 64.73s (0:01:04)
```

## Residual Risks

- No live client has called the fixed server. Claude Code 2.1.283 is billed
  to run and is left to CHE-9's own check after the merge; Codex CLI, on an
  older protocol version, has not been rerun either.
- The boundary's error replies lack the `_meta` server-info stamp that the
  SDK adds to 2026-07-28 results; whether Claude Code needs it is unverified.

## Recommendation

Close the bug once the branch is merged into `develop`: the protocol failure
no longer reproduces in the tests that use protocol 2026-07-28, and the full
check passes.
