# Bug Fix: jev-mcp gate refuses concurrent first tool calls

- **Slug**: jev-mcp-cold-calls
- **Fixed**: 2026-10-06
- **Assessment**: ./assessment.md
- **Status**: applied
- **Spec-Kit-Task**: T002 (this bug's commit trailer; T001 is the client
  metadata bug, `../jev-mcp-client-metadata/`). Both fixes touch the same two
  source files, so one code commit carries both trailers.

## Summary

On a cold cache the gate now fetches the tool schemas through the proxy's own
`list_tools()` (which runs the existing `on_list_tools` check and fills the
cache) instead of opening a second `Client` on the shared stdio transport. The
second client had different connection options from the proxy's backend
clients, and FastMCP refuses that while one of them is active.

Line numbers in the assessment refer to develop `87e9834`, before the fix.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/education-privacy-gate/src/education_privacy_gate/__main__.py` | modified | Cold path calls `ctx.fastmcp.list_tools()` and fails closed if the cache stays empty; `PrivacyGate` no longer takes or stores a client; the duplicate output-schema check goes. |
| `packages/education-privacy-gate/tests/test_proxy.py` | added tests | Cold concurrent calls; cold schema fetch with and without an output schema; `connected()` gets `warm=True`; `PrivacyGate(None)` becomes `PrivacyGate()`. |

## Diff Highlights (optional)

```python
if self.schemas is None:
    await ctx.fastmcp.list_tools()   # on_list_tools fills self.schemas
    if self.schemas is None:
        raise GateError()
```

## Tests Added or Updated

- `test_proxy.py::test_concurrent_first_calls_need_no_warm_up` — four
  concurrent first calls through the full proxy, no warm-up, all succeed and
  restore. Fails on the old code. It passed in five repeated runs after the
  fix (`post-fix-cold-repro.log`, `post-fix-cold-repeat.log`).
- `test_proxy.py::test_cold_schema_fetch_refuses_output_schemas[None|schema]`
  — a cold first call forwards when the upstream has no output schema and
  refuses (nothing forwarded, cache stays empty) when it advertises one. The
  no-schema case fails on the old code.
- `connected(..., warm=True)` keeps the old warm-up for every existing test.

## Local Verification

Evidence directory (authoritative): `~/.local/state/verbose-broccoli/workspaces/feature-jev-mcp-client-fixes/jev-mcp-client-fixes/ctx_c55c1f0e1fe2/`.
All commands ran under the `systemd-run --user --scope -q -p CPUWeight=20 nice
-n 10 taskset -c 4-7` wrapper.

- `cold-repro.py` (synthetic scratch: fresh proxy over the fixture, four
  concurrent calls, with and without a warm-up) on the old code, run with the
  old source on `PYTHONPATH` → `cold [True, True, True, False]`, `warm [False,
  False, False, False]` (`pre-fix-cold-repro-old-code.log`).
- The same script on the fixed code → `cold [False, False, False, False]`,
  `warm [False, False, False, False]`, exit 0
  (`post-fix-cold-repro.log`).
- Root-cause trace (`cold-diagnosis-scratch.py`, which prints the exception the
  gate maps to its fixed refusal): `RuntimeError: This stdio transport has a
  live session built for different connection options and another client is
  still using it`, raised in `ProxyProvider._list_tools` under `call_next`.
- Pytest runs as in the metadata record: 5 passed (new tests), 196 passed (whole
  package).

## Deviations from Assessment

None in design. One note: the first scratch run on the fixed code replaced
`ToolResult` with a debug wrapper, which made every call fail at the gate's own
`type(result) is not ToolResult` check. That was my debug script, not the fix.
I deleted that single misleading log (`post-fix-cold-script.log`) and kept the
clean repro script.

## Follow-ups

- None required.
