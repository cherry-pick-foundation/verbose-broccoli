# Bug Assessment: hosted checks depend on local setup

- **Slug**: hosted-check-failures
- **Created**: 2026-10-08
- **Source**: WHA-7 and WHA-8 task descriptions
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

The hosted Checks job fails credit-offers tests in UTC with XDG_CONFIG_HOME
set. Documentation references cannot find lychee on a fresh runner.

## Symptom

Tests assume a Korean local time zone and no configuration root. Documentation
references installs uv alone, while automatic installation is disabled.

## Reproduction

Run `TZ=UTC XDG_CONFIG_HOME=/synthetic/config uv run --frozen --offline
--no-sync --package credit-offers pytest
packages/credit-offers/tests/test_credit_offers.py -q`.
Before changes: 43 failed, 23 passed. The default boundary assertion, explicit
boundary validation and the frozen proxy environment assertion all fail.

Use an empty mise data directory and a PATH without host lychee. Trust
`.config/mise.toml`, install only `aqua:astral-sh/uv` with `mise install
--locked`, then run `mise exec -- npm run doc-regions:check` with
MISE_EXEC_AUTO_INSTALL=false, matching the documentation runner.

## Suspected Code Paths

- `packages/credit-offers/tests/test_credit_offers.py` fixes END at +09:00,
  expects noon for local rounding, and expects GATE.env to be None.
- `packages/credit-offers/src/credit_offers/__init__.py` converts boundaries
  to the local zone and reads XDG_CONFIG_HOME at import time.
- `.github/workflows/docs-check.yml` installs only uv.
- `.github/actions/prepare-mise/action.yml` disables automatic installation.
- `.config/mise.toml` already pins lychee 0.24.2; `.config/mise.lock` already
  supplies its Linux x64 archive checksum.

## Root Cause Hypothesis

Confidence: high. Both checks rely on host setup that a clean hosted runner
lacks. Production boundary and configuration behavior is intentional.

## Proposed Remediation

**Preferred**: set and restore the test process time zone in an autouse
fixture using time.tzset. In the frozen-proxy test, explicitly unset
XDG_CONFIG_HOME, reload the module and restore its GATE object. Keep the
separate absolute, unset, relative and empty configuration cases.

Install lychee alongside uv using the existing locked mise command in the
documentation workflow. Retain the existing tool pin and reviewed lock rather
than duplicating or changing them. Add a workflow regression assertion.

**Files likely to change**:
- `packages/credit-offers/tests/test_credit_offers.py`
- `.github/workflows/docs-check.yml`
- `scripts/root-config-test.ts`
- `.specify/bugs/hosted-check-failures/assessment.md`, `fix.md`, `test.md`

**Tests to add or update**:
- Keep all existing boundary and proxy assertions; demonstrate failure before
  fixture isolation and success under UTC and other host zones afterward.
- Assert the documentation workflow installs uv and lychee through locked mise.
- Repeat the fresh-tool-directory documentation command after locked install.

## Risks & Considerations

Time zone changes must restore both the environment and C runtime state.
Import-time GATE changes must restore module state. No production code, new
tool adoption or pin update is needed; existing security review is in
`specs/023-upstream-tooling/security/r1-mise.md`.

## Open Questions

None. The existing pin and Linux lock entry settle the tool choice.

## WHA-18: remaining doctor failure in PR #2

Checks run 37742618550 at commit 253bd49 reports `FAIL codexbar`; all
other doctor entries pass. No credit-offer test is named as failing.
`.config/mise.toml` requires CodexBar 0.69.0, but `[tasks.setup]` installs
only `[tools]` entries and dependency trees. CodexBar is a separate host
tool, absent from `.github/workflows/check.yml` runner preparation.

A clean process environment on Node 24.19.0, with TZ=UTC, an absolute
XDG_CONFIG_HOME and PATH excluding host CodexBar, reproduces doctor exit 1
with only CodexBar failing. Reuse the reviewed release and checksum from
`specs/024-model-choice/plan.md`, R7, and prepare the complete upstream archive
on the runner. Preserve the original doctor check. No new tool adoption,
provider usage, credential access or dependency is needed.

## WHA-23: the remaining failure is the Node launcher

The failed job log for Checks run 37744368251 at 9fa468f identifies
`credit-offers#test`, with two failed and 64 passed cases. The real-gate
end-to-end and upstream-error cases both fail because
`_node_command` invokes `mise which node` from `/`, which exits 1.
The workflow installs Node 24.19.0 directly on PATH, while mise has no global
Node pin. Its successful CodexBar preparation does not address that launcher.
The gate's startup failure appears to its caller as a closed connection.

The earlier reproduction used the server's mise wrapper, which supplies a
global Node configuration. Excluding the host CodexBar binary did not exclude
that global configuration, so doctor passed while the integration failure
remained hidden. The job log marks credit-offers as the failing Turbo task;
doctor is not the reported cause.

An isolated home and XDG_CONFIG_HOME, TZ=UTC, Node 24.19.0 and checksum-verified
mise 2026.9.16 reproduce both failures. The PATH contains selected runner tools
and system tools, not the server mise wrapper or host agent tools. Existing
locked tools and dependency environments are reused, rather than claiming a
fresh installation of every dependency.

The clean run also reveals jev-ultrafast's unset-configuration assertion
inheriting XDG_CONFIG_HOME. Its separate absolute/unset/relative/empty storage
cases already specify the intended behavior. Apply the same explicit unset
and module-state restoration used by credit-offers.

The full restricted-PATH run then exposed three Wiki PDF test failures
(`test_convert_supported_files_and_pass_through`,
`test_unreadable_revisions_record_the_reason` and
`test_pdf_retains_content_stream_order_once`): `pdftotext` was absent.
The official ubuntu26/20260927.149 image manifest has no Poppler package,
and the Checks workflow does not install it. Poppler is already adopted:
`specs/050-wiki-quarto-text/tasks.md` records the existing pdftotext-raw
path and regression. Prepare this existing host dependency on the runner;
do not bypass PDF conversion tests.
