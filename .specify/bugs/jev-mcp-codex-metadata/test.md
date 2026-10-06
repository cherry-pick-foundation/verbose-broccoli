# Bug Verification: jev-mcp gate refuses Codex tool-call metadata

- **Slug**: jev-mcp-codex-metadata
- **Tested**: 2026-10-06
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified (synthetic reproduction; no native Codex run, see Residual Risks)

## Summary

A call carrying the seven exact Codex keys is accepted and reaches the
synthetic upstream with none of those keys or values; on the old source the
same call got the fixed refusal. Near-miss and foreign keys and a string
progress token still refuse, the raw boolean progress token still refuses,
and a plain call afterwards still works. Full repository verification passes
on the fixed tip.

## Checks Performed

Evidence directory (authoritative, outside the repository):
`~/.local/state/verbose-broccoli/workspaces/feature-jev-mcp-client-fixes/jev-mcp-codex-metadata/ctx_53add5db93d0/`.
Every batch command ran under `systemd-run --user --scope -q -p CPUWeight=20
nice -n 10 taskset -c 4-7`.

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (pre-fix) | New test with the old source: `uv run --frozen --offline pytest tests/test_proxy.py -k codex_meta -q` in the package | fail, as expected | exit 1, 2 failed (`round2c/red.log`). |
| Reproduction (post-fix) | Same command with the fix | pass | 2 passed; the subset `-k "meta or progress or logging"` gave 16 passed (`round2c/focused.log`). |
| Package suite | `uv run --frozen --offline pytest tests -q` at the fixed tip | pass | exit 0, 198 passed (`package-tests-tip.log`; run before the last comment and boolean-case edits), subset rerun after them as above. |
| Lint | `uv run --project tools/ruff --frozen --offline --no-sync ruff check --no-cache` and `ruff format --check` on the package | pass | exit 0 (`round2c/ruff-*.log`). Two earlier checks failed on E501 in my docstring; logs kept. |
| Full verification | `npm run verify` at `8424490`, base `677216d` | pass | exit 0 at 2026-10-06T14:54:39Z; same-run summary: 46 tasks, every exit code 0, 4 cached (`verify/npm-run-verify.log`, `verify/turbo-run-summary.json`). |

## Output Excerpts

```text
old source: 2 failed, 34 deselected   (exit 1)
fixed:      16 passed, 182 deselected (exit 0)
verify:     Tasks: 46 successful, 46 total (exit 0)
```

## Residual Risks

- **No native Codex run.** Codex was refused before a provider, model or usage
  could be observed in the native receipts
  (`~/.local/state/verbose-broccoli/workspaces/develop/jev-mcp-native-acceptance/ctx_ef419915b588`).
  This fix is verified against Codex 0.160.0 source (tag `rust-v0.160.0`,
  commit `a956835d020762cb2b570053af06f643a11c0ecc`) and a synthetic MCP
  client. Native Codex acceptance is not claimed; it needs the registered
  server on the merged code and a native call.
- A later Codex release may add keys and refuse again.
- The CLI binary was not tested against this source; the key list is read
  from source, not from a captured live request.
- Accepted values are discarded by the existing `meta.clear()`; the test
  checks a registered-looking value does not reach the upstream.
- Unretained history: my first run of the new test failed on a boolean
  progress case the SDK client coerces; that log is in `attempt-1-superseded/`.

## Recommendation

Close the code part after the merge into `develop` and an other-provider
review. Native Codex acceptance stays open until root decides on a native call.
