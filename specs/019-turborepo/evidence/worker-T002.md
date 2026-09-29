# CHE-32 T002 worker report

Assumption: compare dependency package/version pairs and exclude the root workspace's virtual project entry. The three base locks contain 78 unique dependency pairs; the root lock preserves all 78 with no old-only pair and adds only `verbose-broccoli-python==0.1.0` as its virtual workspace entry.

## Changes

- New root `pyproject.toml`, `.python-version` (`3.14.4`) and `uv.lock` establish the non-package uv workspace, required uv version, shared Python floor and constraints.
- `packages/backfire/pyproject.toml` changes sites S168, S175 and `W:packages/backfire/pyproject.toml#build-system` to `uv_build`; its existing `typesafe-sdk==0.7.1` constraint remains unchanged. `packages/doc-regions/pyproject.toml` changes S166, S170 and its build-system row. `packages/wiki-consistency/pyproject.toml` changes S167, S171, its build-system row and its workspace source row.
- Deleted the selected package locks: `W:packages/backfire/uv.lock`, `W:packages/doc-regions/uv.lock`, and `W:packages/wiki-consistency/uv.lock`.
- `packages/backfire/src/backfire/ready.py` changes S177, S189 and `F:T002:ready.py:90-101` to check the root workspace venv in the repository and a component-local venv in a built copy.
- `packages/backfire/src/backfire_tools/build.py` changes S184, S123 and `F:T002:build.py:103-110`. It exports workspace pins, temporarily adds them as uv constraints while locking each copy offline, restores the copied pyproject bytes, and selects only modules present in each Backfire copy.
- `packages/backfire/tests/test_build.py` changes `F:T002:test_build.py:107-118`, the selected `F:py_venv` rows at 58-70 and 72-106, and S113. `packages/backfire/tests/test_ready.py` changes S174 and S187. The selected usage messages change at S112 in `test_education_e2e.py`, S114 in `test_load.py`, and S111 in `packages/doc-regions/src/doc_regions/regions.py`; `packages/doc-regions/tests/test_regions.py` changes S110.
- This report is `specs/019-turborepo/evidence/worker-T002.md`.

## Selected sites left unchanged

- `S173` in `packages/backfire/tests/test_load.py` still checks each built copy's own `.venv`. The test passed and verifies imports, serving, independence and no writes outside that venv.
- The selected `F:py_venv` rows at 135-189 and 190-230 in `packages/backfire/tests/test_build.py` remain unchanged because the copied work package installs and offline check still pass with standalone locks; the complete focused build suite passed.
- `F:py_venv:packages/wiki-consistency/src/wiki_consistency/search.py:31-34` and `:58-79` still use the package-local `node_modules`. The path resolved to an existing qmd executable in the repository and in a built work copy after its documented npm install.
- `S202` in `plugins/work/skills/wiki-consistency/SKILL.md` remains byte-for-byte unchanged. From the built skill directory, `npm ci --offline --ignore-scripts --no-audit --no-fund --prefix ../../wiki-consistency` succeeded.
- The three package-local `.python-version` files remain unchanged. The review row `W:packages/backfire/pyproject.toml#constraints` also remains unchanged, as required for Backfire's own `typesafe-sdk` pin.

`uv_build` rejected the full Backfire module list when a build copy omitted `backfire_tools` or `backfire_education`, reporting that the corresponding `src/<module>/__init__.py` was missing. This contradicted the earlier toy probe; the builder now changes only the module-name value in the copied pyproject, preserving every other byte.

The first lock attempt used `UV_CONSTRAINT`, which `uv lock` did not apply; its copies selected newer versions than the workspace. The final builder temporarily adds exported pins to `tool.uv.constraint-dependencies`, runs `uv lock --offline`, then restores the copied pyproject. Rebuilt code and work copies installed the expected root pins, including Starlette 0.52.1, OpenAI 3.19.2, PyJWT 2.15.0 and sse-starlette 3.4.11.

## Verification

Commands below ran from the repository root unless a working directory is stated.

| Command | Result |
| --- | --- |
| `uv lock` | exit 0 |
| `uv lock --check` | exit 0; resolved 79 lock entries |
| `uv sync --locked --all-packages --extra education` | exit 0; checked 74 packages |
| `uv sync --project . --check --frozen --offline --all-packages --extra education` | exit 0; checked 74 packages, no changes |
| `uv run --frozen --offline --no-sync --package backfire pytest packages/backfire/tests -m 'not slow'` | exit 0; 1,355 passed, 3 deselected |
| `uv run --frozen --offline --no-sync --package backfire pytest packages/backfire/tests/test_build.py` | exit 0; 32 passed |
| `uv run --frozen --offline --no-sync --package backfire pytest packages/backfire/tests/test_load.py` | exit 0; 1 passed |
| `uv run --frozen --offline --no-sync --package doc-regions pytest packages/doc-regions/tests && uv run --frozen --offline --no-sync --package doc-regions python scripts/doc_sources_test.py` | exit 0; 105 pytest tests passed and the source check exited 0 |
| `uv run --frozen --offline --no-sync --package wiki-consistency pytest packages/wiki-consistency/tests` | exit 0; 169 passed |
| `uv build --wheel --out-dir /tmp/feature-turborepo-t002-wheels` in each package directory | exit 0 for Backfire, doc-regions and wiki-consistency; wheels contain the configured modules and package data |
| `npm run backfire:build -- code /tmp/feature-turborepo-t002-verify-6eC4jQ/code-plugin` | exit 0 |
| `npm run backfire:build -- work /tmp/feature-turborepo-t002-verify-6eC4jQ/work-plugin` | exit 0 |
| `uv sync --frozen --offline --no-dev` in the built code `backfire/` directory | exit 0 |
| `uv sync --frozen --offline --no-dev --extra education` in the built work `backfire/` directory | exit 0 |
| `npm ci --offline --ignore-scripts --no-audit --no-fund --prefix ../../wiki-consistency` in the built work `skills/wiki-consistency/` directory | exit 0 |
| `UV_OFFLINE=1 uv sync --project ../../doc-regions --frozen --no-dev` in the built work skill directory | exit 0 |
| `UV_OFFLINE=1 uv sync --project ../../wiki-consistency --frozen --no-dev` in the built work skill directory | exit 0 |
| `uv run --project ../../wiki-consistency --frozen --offline --no-sync python -c 'from wiki_consistency.search import _qmd_path; path=_qmd_path(); print(path); print(path.is_file())'` in the built work skill directory | exit 0; qmd path exists |
| `XDG_CONFIG_HOME=/tmp/feature-turborepo-t002-verify-6eC4jQ/empty-config uv --directory /tmp/feature-turborepo-t002-verify-6eC4jQ/code-plugin/backfire run --frozen --offline --no-sync backfire ready` | exit 1 after the offline installation check passed; no temporary credential existed, so no provider request was sent |
| `XDG_CONFIG_HOME=/tmp/feature-turborepo-t002-verify-6eC4jQ/empty-config uv --directory /tmp/feature-turborepo-t002-verify-6eC4jQ/work-plugin/backfire run --frozen --offline --no-sync backfire ready` | exit 1 after the offline installation check passed; no temporary credential existed, so no provider request was sent |
| `git diff --check` | exit 0 |

`deno task workflow`, `deno task verify` and `npm run verify` each exited 1 in `scripts/workflow.ts` with `EXECUTION_FAILED: Deno.Command is not a constructor`. `scripts/deno_shim.ts` is outside this task's ownership and is part of the concurrent T001 migration; the failure was escalated to the coordinator. No T002-owned change appears necessary for this failure.

The shared worktree also contains changes from other tasks. T002 changes are limited to the owned paths listed above; I did not modify, stage or revert the concurrent files.

## T002b addendum: virtual root workspace

Removed the root `[project]` table and `[tool.uv].package = false` from
`pyproject.toml`, retaining the uv constraints and workspace and Turborepo
name. Regenerated `uv.lock`; the 78 remaining package/version pairs have the
same sorted-pair SHA-256 as the T002 lock after excluding its virtual root
entry: `7bbf23169a7066b9d89bdb46f926b7b1794862f3bd6cbd103e552fd362fcfa15`.
The regenerated lock has no `verbose-broccoli-python` package entry.

`node_modules/.bin/turbo ls` now exits 0 and lists `backfire`, `doc-regions`,
the synthetic `verbose-broccoli-python` root and `wiki-consistency`; it reports
neither the root-name collision nor the concurrent npm workspace collision.
This addendum changes only the root `pyproject.toml`, root `uv.lock`, and this
report; no pre-existing selected-site row applies to these root files.

| Command | Result |
| --- | --- |
| `deno task workflow` | exit 1; warns that `tools/none` is missing, then reports `EXECUTION_FAILED: Deno.Command is not a constructor` in the concurrent Node shim |
| `deno task verify` | exit 1; same `tools/none` warning and `Deno.Command` shim failure |
| `uv lock` | exit 0; resolved 78 packages and removed `verbose-broccoli-python` 0.1.0 |
| `uv lock --check` | exit 0; resolved 78 packages |
| `uv sync --locked --all-packages --extra education` | exit 0; checked 74 packages |
| `uv run --frozen --offline --no-sync --package doc-regions pytest -p no:cacheprovider packages/doc-regions/tests scripts/doc_sources_test.py` | exit 0; 107 passed |
| `node_modules/.bin/turbo ls` | exit 0; lists the four expected packages without a collision |

The before-lock comparison excluded the T002 root entry, and the after-lock
comparison included every entry:

```sh
uv run --frozen --offline --no-sync python -c 'import hashlib,tomllib; from pathlib import Path; pairs=sorted({(p["name"],p["version"]) for p in tomllib.loads(Path("uv.lock").read_text())["package"] if p["name"]!="verbose-broccoli-python"}); data="\n".join(f"{name}=={version}" for name,version in pairs); print(len(pairs),hashlib.sha256(data.encode()).hexdigest()); print(pairs[0],pairs[-1])'
uv run --frozen --offline --no-sync python -c 'import hashlib,tomllib; from pathlib import Path; pairs=sorted({(p["name"],p["version"]) for p in tomllib.loads(Path("uv.lock").read_text())["package"]}); data="\n".join(f"{name}=={version}" for name,version in pairs); print(len(pairs),hashlib.sha256(data.encode()).hexdigest()); print("root-entry",[(name,version) for name,version in pairs if name=="verbose-broccoli-python"])'
```

Both comparison commands exited 0 and gave 78 pairs with the hash above; the
after-lock comparison found no root entry. There are no selected sites left
unchanged or unselected changes needed for this addendum. The existing
workflow failure remains outside T002b ownership in `scripts/deno_shim.ts`.
