# Bug Fix: jev-mcp gate refuses Claude Code tool-use metadata

- **Slug**: jev-mcp-client-metadata
- **Fixed**: 2026-10-06
- **Assessment**: ./assessment.md
- **Status**: applied
- **Spec-Kit-Task**: T001 (this bug's commit trailer; T002 is the cold-call
  bug, `../jev-mcp-cold-calls/`). Both fixes touch the same two source files,
  so one code commit carries both trailers.

## Summary

The gate's `_meta` allowlist now also accepts keys with the `claudecode/` or
`anthropic/` prefix, whatever their value. The existing `meta.clear()` still
runs before the call is forwarded, so none of these keys or values reach the
hidden upstream. Other unknown keys, string or boolean progress tokens and bad
log levels still refuse with the fixed text.

Line numbers in the assessment refer to develop `87e9834`, before the fix.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/education-privacy-gate/src/education_privacy_gate/__main__.py` | modified | New `_CLIENT_META_PREFIXES`; the key check ignores prefixed keys; module docstring updated. |
| `packages/education-privacy-gate/tests/test_proxy.py` | added test | `test_client_vendor_meta_is_accepted_and_discarded` (both client modes). |
| `docs/jev-mcp.md` | modified | The sentence on `_meta` names the accepted prefixes. |

## Diff Highlights (optional)

```python
_CLIENT_META_PREFIXES = ("claudecode/", "anthropic/")
...
{key for key in meta if not key.startswith(_CLIENT_META_PREFIXES)}
- _CONNECTION_META
- {"progressToken", LOG_LEVEL_META_KEY}
```

## Tests Added or Updated

- `test_proxy.py::test_client_vendor_meta_is_accepted_and_discarded[legacy|auto]`
  — through the full proxy and the fixture upstream, a call carrying
  `claudecode/toolUseId`, `claudecode/agentId` (value a registered-looking
  name), `claudecode/isObserver` and `anthropic/requestId` succeeds, and the
  upstream's `request_meta` holds none of those keys or values. Near-miss keys
  (`claudecode`, `xclaudecode/toolUseId`) and a prefixed key next to a private
  key still get the fixed refusal. It fails on the old code (both modes).
- Existing negative cases stay unchanged and pass:
  `test_frontend_meta_never_reaches_backend`,
  `test_sdk_logging_levels[unsupported]`,
  `test_restore_errors_refusals_and_no_files`.

## Local Verification

Evidence directory (authoritative, outside the repository):
`~/.local/state/verbose-broccoli/workspaces/feature-jev-mcp-client-fixes/jev-mcp-client-fixes/ctx_c55c1f0e1fe2/`.
All commands ran under `systemd-run --user --scope -q -p CPUWeight=20 nice -n
10 taskset -c 4-7`.

- Pre-fix (old code, test changes only): `uv run --frozen --offline --no-sync
  --package education-privacy-gate pytest -p no:cacheprovider
  packages/education-privacy-gate/tests/test_proxy.py -k "vendor_meta or
  concurrent_first or cold_schema" -q` → exit 1, 4 failed, 1 passed
  (`pre-fix-tests.log`; it holds the tail of that output).
- Post-fix, same command → exit 0, 5 passed (`post-fix-new-tests.log`).
- Whole package: same pytest over `packages/education-privacy-gate/tests` →
  exit 0, 196 passed (`post-fix-package-tests.log`).
- No model call, no private registry read, no user-scope client config read;
  the fixtures are synthetic.

## Deviations from Assessment

None for this bug. The assessment's Codex note stands: no Codex `_meta` key was
confirmed, so nothing here claims to fix Codex.

## Follow-ups

- Registered activation: the registered `jev-mcp` server must run the merged
  code before a real Claude Code session is accepted. Not performed here; no
  real Claude Code session was started (a real call would reach the provider).
- A Codex refusal, if it persists after this, needs its own evidence of the
  rejected key; `x-codex-turn-metadata` is a string in the Codex binary but is
  not shown to be a tool-call `_meta` key.
