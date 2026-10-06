# Bug Fix: jev-mcp gate refuses Codex tool-call metadata

- **Slug**: jev-mcp-codex-metadata
- **Fixed**: 2026-10-06
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The gate's `_meta` check now also ignores the seven exact keys Codex 0.160.0
sends. The existing `meta.clear()` still runs before forwarding, so no key or
value reaches the hidden upstream. Unknown and near-miss keys, string progress
tokens and bad log levels still refuse with the fixed text.

Line numbers in the assessment refer to develop `677216d`.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/education-privacy-gate/src/education_privacy_gate/__main__.py` | modified | New `_CODEX_META` set, subtracted in the key check; module docstring updated. |
| `packages/education-privacy-gate/tests/test_proxy.py` | added test | `test_codex_meta_is_accepted_and_discarded` (both client modes). |

## Diff Highlights

```python
_CODEX_META = {"callId", "threadId", "sessionId", "windowId", "itemId",
               "x-codex-turn-metadata", "codex_bridge_mcp_call_id"}
...
- _CONNECTION_META
- _CODEX_META
```

## Tests Added or Updated

- `test_proxy.py::test_codex_meta_is_accepted_and_discarded[legacy|auto]` —
  through the full proxy and fixture upstream, a call carrying all seven keys
  (sentinel values, one a registered-looking name) plus an integer progress
  token succeeds, and the upstream's `request_meta` holds none of those keys
  or values. A raw boolean progress token
  beside a known key (legacy mode) and seven near-miss or foreign cases
  (`callid`, `call_id`, `codex/callId`, `codex_apps`, `sandbox-state`, a known
  key beside a private key, a string progress token) get the fixed refusal, and a plain call
  afterwards still works. Fails on the old source.
- Boolean progress stays covered by the existing
  `test_continuations_and_raw_boolean_progress_are_blocked`, because the SDK
  client coerces a boolean token before sending. My first run of the new test
  included a boolean case and failed for that reason; that log is kept in
  `attempt-1-superseded/`.

## Local Verification

Evidence directory (authoritative, outside the repository):
`~/.local/state/verbose-broccoli/workspaces/feature-jev-mcp-client-fixes/jev-mcp-codex-metadata/ctx_53add5db93d0/`.
All commands ran under `systemd-run --user --scope -q -p CPUWeight=20 nice -n
10 taskset -c 4-7`.

- Old source, new test: `uv run --frozen --offline pytest tests/test_proxy.py
  -k codex_meta -q` in the package → exit 1, 2 failed (`focused-red.log`).
- Fixed source, same command → exit 0, 2 passed (`focused-green.log`).
- Package suite → exit 0, 198 passed (`package-tests-final.log`; run before a
  docstring-only reflow).
- After the reflow: `ruff check` and `ruff format --check` on the package
  (`uv run --project tools/ruff --frozen --offline --no-sync ruff ...`) → exit
  0; the meta/logging/progress subset → 16 passed (`focused-final.log`). Two
  earlier `ruff check` runs failed on E501 in my docstring; their logs are
  kept (`ruff-check-attempt1.log`, `ruff-check-attempt2.log`).
- `npm run workflow` before and after; policy graph exit 0. The impact graph
  does not support Python files and returned an error (kept).
- No full `npm run verify` yet: no slot has been granted.
- No model call, no private registry read; fixtures are synthetic.

## Deviations from Assessment

None.

## Follow-ups

- Native Codex acceptance is not shown; it needs a registered server on the
  merged code and a native call (root's decision, paid).
- A later Codex release may add keys; that needs new evidence.
