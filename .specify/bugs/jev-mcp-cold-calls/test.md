# Bug Verification: jev-mcp gate refuses concurrent first tool calls

- **Slug**: jev-mcp-cold-calls
- **Tested**: 2026-10-06
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified (synthetic reproduction; no native-client run, see Residual Risks)

## Summary

Four concurrent first calls through a fresh gate now all succeed without a
warm-up: the old code refused three of four (`cold [True, True, True, False]`),
the fixed code refuses none (`cold [False, False, False, False]`). The traced
cause, a second client on the shared stdio transport with different connection
options, is gone because the gate no longer opens one. The full repository
verification passes on the repaired tip.

## Checks Performed

Evidence directory (authoritative, outside the repository):
`~/.local/state/verbose-broccoli/workspaces/feature-jev-mcp-client-fixes/jev-mcp-client-fixes/ctx_c55c1f0e1fe2/`.
Every batch command ran under `systemd-run --user --scope -q -p CPUWeight=20
nice -n 10 taskset -c 4-7`.

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Cause trace | `cold-diagnosis-scratch.py` (prints the exception the gate maps to its refusal) on the old code | reproduced | `RuntimeError: This stdio transport has a live session built for different connection options and another client is still using it`, in `ProxyProvider._list_tools`. Root's receipt (1 of 4 cold calls passed) and my run (1 of 4) agree. |
| Reproduction (pre-fix) | `cold-repro.py` with the old source on `PYTHONPATH` (a `git archive` copy of develop `87e9834`) | fail, as expected | `cold [True, True, True, False]`, `warm [False, False, False, False]` (`pre-fix-cold-repro-old-code.log`). |
| Reproduction (post-fix) | `cold-repro.py` on the fixed source | pass | `cold [False, False, False, False]`, `warm [False, False, False, False]`, exit 0 (`post-fix-cold-repro.log`). |
| New tests, old code | `pytest ... test_proxy.py -k "vendor_meta or concurrent_first or cold_schema" -q` | fail, as expected | `test_concurrent_first_calls_need_no_warm_up` and the no-output-schema case of `test_cold_schema_fetch_refuses_output_schemas` failed (`pre-fix-tests.log`). |
| New tests, fixed code | same command | pass | `5 passed`; the cold test also passed in 5 repeated runs (`post-fix-cold-repeat.log`). |
| Fail-closed preserved | `test_cold_schema_fetch_refuses_output_schemas[schema]`, `test_preflight_cleanup_and_recovery`, restore/refusal tests | pass | A cold call with an advertised output schema forwards nothing and leaves the cache empty. |
| Package suite | `pytest ... packages/education-privacy-gate/tests -q` | pass | exit 0, `196 passed` (`post-fix-package-tests.log`). |
| Full verification, attempt 1 | `npm run verify` at `eb2448e` | fail | exit 1, ruff `E501` only, from my comment line (`npm-run-verify.log`). |
| Full verification, attempt 2 | `npm run verify` at `f865b1e`, base `87e9834` | pass | exit 0; 46 tasks, every task exit code 0 (`verify-2/turbo-run-summary.json`). |

## Output Excerpts

```text
old code: cold [True, True, True, False]   warm [False, False, False, False]
fixed:    cold [False, False, False, False] warm [False, False, False, False]
verify-2: Tasks: 46 successful, 46 total (exit 0)
```

## Residual Risks

- **No native client was run.** The reproduction is a synthetic stdio
  fixture, as the issue's own reproduction was. Whether the registered Claude
  Code or Codex sessions issue concurrent cold calls is not established.
- The race-free behavior rests on FastMCP 4.0.10's transport (pinned in
  `pyproject.toml`). A later FastMCP release should keep the cold test.
- My first scratch run on the fixed code used a debug wrapper that made every
  call fail at an unrelated check; I deleted that one misleading log and kept
  the clean script (`cold-repro.py`).

## Recommendation

Close the bug after the merge into `develop`; a concurrent cold-call check
from a native client is optional and not required for this fix.

## Follow-through (2026-10-06, appended; earlier text unchanged)

- The source repair merged into `develop` at
  `677216dbec51742164c8c915431a0081fddfede0` (reviewed source `f55651b`,
  review record `3b44646`); source and merged full verification each passed
  46/46, exit 0.
- The native acceptance receipts
  (`~/.local/state/verbose-broccoli/workspaces/develop/jev-mcp-native-acceptance/ctx_18bbc79c6eb4`
  and `.../ctx_ef419915b588`) show a registered Claude Code call succeeding
  through `typesafe/jev-1.13` on OpenRouter; Codex was refused before a
  provider could be observed. The receipts do not show that refusal's cause;
  the assessed cause is the metadata allowlist tracked in
  `../jev-mcp-codex-metadata/`. No native concurrent cold-call check is
  claimed.
