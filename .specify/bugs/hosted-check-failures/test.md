# Bug Verification: hosted checks depend on local setup

- **Slug**: hosted-check-failures
- **Tested**: 2026-10-08
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

Both original failures were reproduced before the fixes and passed afterward.
Full repository verification passed with the system Git executable on PATH.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| UTC reproduction before fix | `TZ=UTC XDG_CONFIG_HOME=/synthetic/config uv run --frozen --offline --no-sync --package credit-offers pytest packages/credit-offers/tests/test_credit_offers.py -q` | expected failure | 43 failed, 23 passed. |
| Same UTC command after fix | Same command | pass | 66 passed. |
| Other host zone and config root | Same pytest command with TZ=America/New_York and XDG_CONFIG_HOME=relative/config | pass | 66 passed. |
| Workflow regression before fix | `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test --test-name-pattern='documentation references installs' scripts/root-config-test.ts` | expected failure | Missing lychee in the locked installation. |
| Root configuration suite after fix | `npm run test:root-config` | pass | 9 passed. |
| Python lint and format | `uv run --project tools/ruff --frozen --offline --no-sync ruff check --no-cache packages/credit-offers/tests/test_credit_offers.py` and equivalent `ruff format --check` | pass | No findings or formatting changes. |
| Clean tool reproduction | Empty mise data/cache/state roots; PATH with node, npm, mise and system tools, excluding host lychee; MISE_EXEC_AUTO_INSTALL=false; trust repository config and locked-install uv alone | expected failure | Real documentation command failed with missing lychee. |
| Clean tool check after fix | Locked-install uv and lychee, then `mise exec -- npm run doc-regions:check` | pass | `{"problems": []}`. |
| Full repository checks | `mise exec -- npm run verify` with a scratch-directory symlink to `/usr/bin/git` first on PATH | pass | Exit 0; workflow VERIFIED from the same-run Turbo summary. |
| Read-only document audit | `mise exec -- npm run doc-regions:audit` | report only | 20 existing constitution placement warnings; governing rules retained. |

## Output Excerpts

```text
43 failed, 23 passed
66 passed
{"problems": []}
verify exit: 0
```

## Residual Risks

The default full verification run stopped on Paperclip Git-helper diagnostics
in stdout/stderr comparisons. Suppressing Node warnings did not remove those
diagnostics. Using system Git passed without changing tests or bypassing hooks.
The fixes have not yet run on GitHub; publication still needs Main's privacy
approval. Local mise 2026.10.2 exercised the existing reviewed tool lock.

Document preparation with `--base develop --max-evidence-chars 12000` produced
11 judgment requests covering 335 existing document units. They were not sent;
the CEO owns that merge-review step. No governing document was changed.

## Recommendation

Send the branch to the configured CEO review stage. The CEO adds the independent
review record; Main authorizes GitHub publication after the privacy scan.
