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

## WHA-23 verification

The requested `gh run view 37744368251 --log-failed` returned no output;
`gh api repos/cherry-pick-foundation/verbose-broccoli/actions/jobs/113202237438/logs`
supplied the actual failed job log. It reports two credit-offers integration
failures caused by `mise which node` exiting 1. CodexBar preparation succeeded.

Five resolver regression cases produced four failures and one pass before
the fix, and five passes afterward. A separate run injected the original
a974087 resolver into the integration child in memory, without modifying
the shared checkout: both existing credit-offers integration cases failed
under checksum-verified mise 2026.9.16 and Node 24.19.0. The fixed launcher
passed all 66 credit-offers cases in the same clean setup.

The setup uses an isolated home, absolute XDG_CONFIG_HOME, TZ=UTC and a
selected-tool PATH plus /usr/bin:/bin. It excludes the server mise wrapper,
global Node configuration and host agent tools. The exact reviewed mise
archive and checksum come from `.github/actions/prepare-mise/action.yml`.
Existing locked mise tools, uv dependency cache and repository environments
are reused. Quarto and CodexBar are selected because CI prepares them too.

A first full clean run stopped in raw-import tests: the isolated home's
empty uv cache could not satisfy their offline script dependencies. The next
run points UV_CACHE_DIR at the already prepared cache and supplies CI's
synthetic Git identity, without changing repository checks. The selected
PATH uses system Git, avoiding Paperclip helper diagnostics.

The clean run passed 66 credit-offers, 107 jev-ultrafast and 203 privacy-gate
cases. Doctor passed all 16 entries. Ruff check passed on all three changed
Python files. The jev-ultrafast unset-config case failed before its test
isolation update with XDG_CONFIG_HOME set.

Full verification and commit evidence are reported in the task handoff.
Independent review belongs to the configured Claude Reviewer stage.
GitHub publication still requires Main's privacy-scan comment on WHA-7
covering the eventual commit range. No merge or GitHub push was performed.

The next full run completed 571 Wiki cases but failed three PDF cases because
pdftotext was absent. Its actual result was 3 failed, 571 passed; no pass is
claimed for that run. The official runner manifest was read through
`gh api repos/actions/runner-images/contents/images/ubuntu/Ubuntu2604-Readme.md?ref=ubuntu26/20260927.149`.
It has no Poppler entry. The workflow now installs poppler-utils before checks.
After adding the prepared native pdftotext to the selected PATH, the evidence
suite passes; the new workflow case fails before preparation and passes after.
The server's already prepared Poppler executable is reused for local verification;
this is not a claim to reproduce the runner's exact Ubuntu package version.
Its actual converter version remains checked and recorded by existing tests.

The final verification command is `npm run verify -- --task WHA-23 --base a974087`,
run through checksum-verified mise with the clean environment described above.
The final exit status, same-run Turbo summary and commit are recorded on WHA-23.
