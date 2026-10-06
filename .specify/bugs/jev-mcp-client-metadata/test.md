# Bug Verification: jev-mcp gate refuses Claude Code tool-use metadata

- **Slug**: jev-mcp-client-metadata
- **Tested**: 2026-10-06
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified (synthetic reproduction; no native-client run, see Residual Risks)

## Summary

A call carrying `claudecode/toolUseId`, `claudecode/agentId`,
`claudecode/isObserver` and `anthropic/requestId` in `_meta` is accepted and
reaches the synthetic upstream with none of those keys or values; before the
fix the same call got the fixed refusal. Near-miss and unprefixed keys, string
and boolean progress tokens and bad log levels still refuse. The full
repository verification passes on the repaired tip.

## Checks Performed

Evidence directory (authoritative, outside the repository):
`~/.local/state/verbose-broccoli/workspaces/feature-jev-mcp-client-fixes/jev-mcp-client-fixes/ctx_c55c1f0e1fe2/`.
Every batch command ran under `systemd-run --user --scope -q -p CPUWeight=20
nice -n 10 taskset -c 4-7`.

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (pre-fix) | New tests with the old source: `uv run --frozen --offline --no-sync --package education-privacy-gate pytest -p no:cacheprovider packages/education-privacy-gate/tests/test_proxy.py -k "vendor_meta or concurrent_first or cold_schema" -q` | fail, as expected | exit 1; both `test_client_vendor_meta_is_accepted_and_discarded` cases failed (`pre-fix-tests.log` keeps the tail). |
| Reproduction (post-fix) | Same command at `7be03c3` | pass | exit 0, `5 passed` (`post-fix-new-tests.log`). |
| Negative/control cases | `test_frontend_meta_never_reaches_backend`, `test_sdk_logging_levels`, `test_restore_errors_refusals_and_no_files` in the package run | pass | Unprefixed `private` key, string progress token and unsupported log level still get the fixed text. |
| Package suite | `... pytest -p no:cacheprovider packages/education-privacy-gate/tests -q` at `7be03c3` | pass | exit 0, `196 passed` (`post-fix-package-tests.log`). |
| Proxy tests after the lint-only repair | `.../test_proxy.py -q` at `f865b1e` | pass | `34 passed` (`post-lint-fix-test-proxy.log`). |
| Lint | `uv run --project tools/ruff --frozen --offline --no-sync ruff check --no-cache packages/education-privacy-gate` and `ruff format --check` | pass | The first full verify failed once on `E501` in my comment; fixed in `f865b1e`. |
| Full verification, attempt 1 | `npm run verify` at `eb2448e` | fail | exit 1, `//#lint` E501 only; 28 of 39 tasks passed before it stopped (`npm-run-verify.log`, `turbo-run-summary-failed-attempt-1.json`). Kept, not overwritten. |
| Full verification, attempt 2 | `npm run verify` at `f865b1e`, base `87e9834` | pass | exit 0; same-run summary `3KK45u7nwAQPBb1rWxlYiZKP0Mw.json`: 46 tasks, every task exit code 0, 0 failed (`verify-2/`). |

## Output Excerpts

```text
pre-fix:  4 failed, 1 passed, 29 deselected   (exit 1)
post-fix: 5 passed, 29 deselected             (exit 0)
package:  196 passed in 49.53s                (exit 0)
verify-2: Tasks: 46 successful, 46 total      (exit 0)
```

## Residual Risks

- **No native client was run.** No real Claude Code session called the
  registered `jev-mcp` server with this code, because that server runs another
  checkout and a real call reaches the paid provider. The fix is verified
  against the key names found in the installed Claude Code binary and a
  synthetic MCP client, not against a live Claude Code call. The registered
  server must run the merged code, then a native Claude Code call confirms it.
- The `claudecode/` and `anthropic/` key names come from the binary, not from
  public documentation. A key in another namespace would still refuse.
- Registered Codex refusals are not addressed: no Codex `_meta` key was
  confirmed, and no claim is made.
- Accepted vendor-prefixed values are discarded by the existing `meta.clear()`;
  the test checks a registered-looking value in `claudecode/agentId` does not
  reach the upstream.

## Recommendation

Close the bug once the branch is merged into `develop` and the registered
server runs the merged code, with a native Claude Code call as the last
confirmation. Open a separate, evidence-backed issue if Codex still refuses.
