# CHE-32 task F3 worker report

## Changes

- `packages/backfire/tests/test_build.py` — V09. Parse each built lock with stdlib `tomllib` and require its package name/version pairs to exist in the root lock.
- `packages/doc-regions/src/doc_regions/__main__.py` — V10. Remove the obsolete extra-separator handling.
- `packages/doc-regions/tests/test_requests.py` — V10. Remove `test_cli_accepts_deno_task_separator` as requested. The only remaining documented `--` is in `npm run doc-regions:prepare -- --base ...`; npm consumes it before invoking the CLI.
- `packages/backfire/pyproject.toml`, `packages/doc-regions/pyproject.toml`, `packages/wiki-consistency/pyproject.toml` — V11. Delete the stale install-metadata comments.
- `pyproject.toml` — V15/D20. Keep only `typesafe-sdk==0.7.1` and `magika<=0.6.3`, with one-line reasons.
- `uv.lock` — V15/D20. Update only the recorded constraints; package versions did not change.
- `specs/019-turborepo/evidence/worker-F3.md` — V09, V10, V11, V15/D20. This report.

## Regression evidence

For V09, a temporary `uv` wrapper changed the `typesafe-sdk` version in each temporary built lock to `99.99.99` after `uv lock`. Before the assertion was added, the focused test accepted the bad locks: 2 passed, exit 0. With the root-lock comparison, the same injected mismatch failed in both build variants: 2 failed, exit 1, each on the new assertion. This confirms the prior test missed the bad-pin case and the revised test catches it.

V10 explicitly requires deleting the Deno-era acceptance test, so no replacement test that passes an extra separator was added. The final doc-regions suite passed. The documented npm form remains valid because npm strips its forwarding separator.

The first full backfire run had four readiness failures. The exact workspace `uv sync --check` reported no changes, the four failing cases passed in isolation, and the final full run passed. No environment sync was needed.

## Commands and results

| Command | Exit | Result |
| --- | ---: | --- |
| `PATH=/tmp/che32-f3-uv-mutator:$PATH npm run test:backfire -- -k test_build_preserves_plugin_and_copies_only_runtime` before V09 assertion | 0 | Fault-injected bad pins accepted; 2 passed. |
| Same focused command after V09 assertion | 1 | Fault-injected bad pins rejected; 2 failed on the new assertion. |
| `npm run test:doc-regions` | 0 | 106 passed. |
| `npm run test:wiki-consistency` | 0 | 263 passed. |
| `npm run test:backfire` (first full run) | 1 | 1,360 passed, 4 readiness failures, 3 deselected. |
| `npm run test:backfire -- -k 'test_ready_runs_configuration_check or test_ready_confirms_direct_and_server_tool_paths_with_fake_provider or test_missing_credential_fails_before_any_provider_request'` | 0 | 4 passed. |
| `npm run test:backfire` (final full run) | 0 | 1,364 passed, 3 deselected. |
| `uv lock` | 0 | Resolved 78 packages. |
| `uv lock --check` | 0 | Resolved 78 packages. |
| HEAD-to-current `uv.lock` package name/version comparison (`tomllib`; exact command below) | 0 | 78 pairs before and after; no pair changed. |
| `uv run --project tools/ruff --frozen --offline --no-sync ruff check --no-cache packages/backfire/tests/test_build.py packages/doc-regions/src/doc_regions/__main__.py packages/doc-regions/tests/test_requests.py` | 0 | All checks passed. |
| `uv run --project tools/ruff --frozen --offline --no-sync ruff format --check --no-cache packages/backfire/tests/test_build.py packages/doc-regions/src/doc_regions/__main__.py packages/doc-regions/tests/test_requests.py` before formatting | 1 | Found a trailing blank line after the removed test. |
| `uv run --project tools/ruff --frozen --offline --no-sync ruff format --no-cache packages/doc-regions/tests/test_requests.py` | 0 | Removed trailing blank lines left by the deleted test. |
| `uv run --project tools/ruff --frozen --offline --no-sync ruff format --check --no-cache packages/backfire/tests/test_build.py packages/doc-regions/src/doc_regions/__main__.py packages/doc-regions/tests/test_requests.py` after formatting | 0 | All three files formatted. |
| `git diff --check -- packages/backfire/tests/test_build.py packages/doc-regions/src/doc_regions/__main__.py packages/doc-regions/tests/test_requests.py packages/backfire/pyproject.toml packages/doc-regions/pyproject.toml packages/wiki-consistency/pyproject.toml pyproject.toml uv.lock` | 0 | No whitespace errors. |
| `rg -n --glob '*.py' --glob '*.md' --glob '*.json' --glob '*.ts' --glob '*.toml' --glob '!specs/**' 'doc-regions.*--|prepare.*--base|test_cli_accepts_deno_task_separator|extra.?separator|deno task separator' packages/doc-regions docs scripts package.json` | 0 | Found only the Deno-era direct test and npm forwarding syntax; npm strips its separator. |
| `uv sync --locked --all-packages --extra education --dry-run` | 0 | Would make no changes. |
| `uv sync --check --frozen --offline --all-packages --extra education` | 0 | Would make no changes. |
| `uv sync --project /home/choi-eunchang/workspaces/verbose-broccoli/feature-turborepo --check --frozen --offline --all-packages --extra education` from `packages/backfire` | 0 | Would make no changes. |
| `uv run --frozen --offline --no-sync --package backfire python -c 'from backfire.ready import _installation_problem, _versions; print(_installation_problem(_versions()))'` | 0 | Printed `None`. |
| `npm run workflow -- --task CHE-32-F3 --base 9d8af619b55c858e797d609ce660cc283c164c3e --graph impact --file packages/backfire/tests/test_build.py` | 1 | Analyzer reports Python files are unsupported code files. |
| `npm run workflow -- --task CHE-32-F3 --base 9d8af619b55c858e797d609ce660cc283c164c3e --graph impact --file packages/doc-regions/src/doc_regions/__main__.py` | 1 | Analyzer reports Python files are unsupported code files. |
| `npm run workflow -- --task CHE-32-F3 --base 9d8af619b55c858e797d609ce660cc283c164c3e --graph policy` | 0 | Static import policy passed with no violations. |
| Final `npm run workflow -- --task CHE-32-F3 --base 9d8af619b55c858e797d609ce660cc283c164c3e` | 0 | Final snapshot recorded in REVIEW mode. |

Workflow impact scans for the Python test and CLI files exited 1 because those paths are unsupported code files for that analyzer. The final workflow's Ponytail review trigger names TypeScript files outside F3 ownership; they are left to the coordinator. `npm run verify` was not run, as the task instructions prohibit it.

Exact lock comparison command:

```sh
python3 - <<'PY'
import subprocess, tomllib
from pathlib import Path
before_text = subprocess.run(
    ['git', 'show', 'HEAD:uv.lock'], check=True, capture_output=True, text=True
).stdout
before = {(p['name'], p['version']) for p in tomllib.loads(before_text)['package']}
after = {(p['name'], p['version']) for p in tomllib.loads(Path('uv.lock').read_text())['package']}
print(f'before pairs: {len(before)}; after pairs: {len(after)}')
print(f'changed: {sorted(before ^ after)}')
raise SystemExit(before != after)
PY
```

Output: `before pairs: 78; after pairs: 78`, `changed: []` (exit 0).

The temporary fault-injection wrapper ran the real `/home/choi-eunchang/.local/bin/uv` and, after successful `uv lock`, applied this command to the temporary built lock:

```sh
sed -i '/name = "typesafe-sdk"/,/^\[\[package\]\]/{s/version = "[^"]*"/version = "99.99.99"/;}' "$PWD/uv.lock"
```
