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

## WHA-18 verification

Node 24.19.0 was used for the reproduction and checks. A process environment
containing only the home directory, selected tool PATH, TZ=UTC, an absolute
scratch XDG_CONFIG_HOME and explicit mise trust/installation settings ran
`mise exec -- npm run doctor`. The selected PATH excluded host CodexBar and
used system Git. Existing locked tools and dependency environments were
reused; this was not a fresh installation of every repository dependency.

Before preparation, doctor exited 1 with only `FAIL codexbar`; all 15 other
entries passed. Executing the actual new workflow shell block downloaded the
reviewed release, passed its SHA-256 check and extracted the complete bundle.
After adding its directory to PATH, doctor exited 0 and all 16 entries passed.
The final run used the unchanged original CodexBar version check.

The new workflow regression failed before the preparation step was added
and passed afterward. `npm run test:root-config` passed 10 tests;
`npm run test:mise-doctor` passed its negative diagnostic case. The first full
verification found a counted-space lint error in the new test expression;
that expression was corrected, and the targeted ESLint and regression checks
passed before repeating full verification.

Independent review is owned by this task's configured Claude Reviewer stage.
No merge or provider usage call is part of this repair. Hosted execution must
be observed separately after publishing the commit to the existing PR branch.

All 46 checks passed in Turbo run `3KP2ApqmWuHpoa5dWAZV0rPSLWa`
(5 cached), including doctor. Workflow then rejected the changed snapshot
because this verification record was edited during the run. Completion
requires a fresh unchanged-snapshot `npm run verify` after the record update.
The full check command uses a scratch symlink to `/usr/bin/git` first on PATH,
matching the earlier repair's workaround for Paperclip Git-helper diagnostics.

The read-only complexity pass found no unnecessary dependency, framework or
installer. Locally owned code adds 9 workflow lines and 30 test lines; the
remaining changes are pins, comments and bug records. The patch stays below
the repository's 1,000-line split-review threshold.
