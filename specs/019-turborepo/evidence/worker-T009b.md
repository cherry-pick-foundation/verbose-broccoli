# CHE-32 T009b worker report

Assumption: root dependencies already provide the versions used by the
Clean Code skill. The coordinator confirmed that the root package pins the
same ESLint, TypeScript ESLint, and TypeScript versions as the skill lock, so
setup and check workflows do not install a second `node_modules` tree inside
the plugin.

## Files changed and selected rows

| File | Rows | Change |
| --- | --- | --- |
| `package.json` | `P:task:doctor`, `P:task:format`, `P:task:format:check`, `P:task:lint`, `P:task:lint:fix`, `P:task:test:ruff`, `P:task:wiki-consistency:install`, `W2:package.json#devDependencies`, X078, X087, X093, X117, X133, X166 | Removed every root shim preload and the two Deno dependencies; added Ruff to lint and formatting; added the Node Ruff suite; synced the uv workspace in the wiki-consistency installer; removed Deno-only filesystem grants. |
| `package-lock.json` | `W2:package.json#devDependencies` | Regenerated with `npm install`; the shim and `@std/fs` are gone. |
| `turbo.json` | X099, X119, X135, `P:task:test` / `P:task:test:ruff` | Removed `DENO_DIR`, updated the doctor description to Node and Ruff, and added the Ruff suite to the root test graph. |
| `tsconfig.json` | `W2:tsconfig.json#files`, X067 | Removed the shim entry, added all 15 root `scripts/*_test.ts` files and the Clean Code test, and enabled `skipLibCheck`. |
| `biome.json` | X107, X140 | Removed `.deno`, `deno.lock`, and the Deno restricted-global entry. |
| `.gitignore` | X165 | Removed the Deno section. |
| `deno.json` | `W2:deno.json` | Deleted the root Deno configuration. |
| `scripts/deno_shim.ts` | `W2:scripts/deno_shim.ts`, X030, X073, X150 | Deleted the shim. |
| `orca.yaml` | X090, X104, X120, X137 | Removed Deno lookup, PATH entry, and install; setup keeps root npm and uv environment installation before `npm run doctor`. |
| `.github/workflows/check.yml` | X086, X116, X128, X164 | Removed Deno download and install. |
| `.github/workflows/docs-check.yml` | X085, X115, X129, X163 | Removed Deno download and install. |
| `.github/workflows/audit.yml` | X084, X127, X162 | Removed Deno download; audits the root and Clean Code locks with `npm audit`. |
| `docs/reference/commands.md` | X122, X149 | Regenerated with Node and Ruff doctor details and the new command list. |
| `scripts/backfire/fixtures/upstream-0.9.0/README.md` | X169 | Replaced the Deno Biome invocation with the root Biome executable. The coordinator assigned X169 to this task after the residual scan. |
| `scripts/cli_contract_test.ts.snapshot` | X142, coordinator assignment | Updated only the workflow help defaults to match Node's double-quoted output. `scripts/cli_contract_test.ts` was not changed. |
| `specs/019-turborepo/evidence/worker-T009b.md` | — | Added this report. |

`docs/reference/plugins.md` was regenerated but remained unchanged. The selected
`P:task:test` row needed no `package.json` edit because its script already runs
`turbo run test`; the new root `test:ruff` dependency is in `turbo.json`.

## Permission scope changes

All existing Node permission flags remain, apart from Deno-only reads removed
from `doctor`, `docs:generate`, and `docs:check`: the resolved Deno executable,
`deno.json`, `deno.lock`, and `$HOME/.deno/bin/deno`. Removing the preload did
not require changing any other permission flag. The new Ruff script uses
`--allow-fs-read=*`, `--allow-fs-write=/tmp`, and `--allow-child-process`,
matching its prior read, temporary-write, and uv subprocess needs.

## Selected rows left unchanged

- `P:task:test`: the root script already dispatches through Turborepo; the
  test graph now includes Ruff.
- X032: the two `Deno.FileInfo` source strings in
  `scripts/workflow_graph_test.ts:338,450` remain fixture text.
- X146: the `.deno/cache/consumer.ts` path in
  `scripts/workflow_plan_test.ts:159` remains a scanner-exclusion fixture.
- No Deno matches appeared in `AGENTS.md` or the constitution in the required
  residual scan; those governance files remain outside this task.

No other unselected site needs a change. The initial residual scan found the
fixture README command; the coordinator added X169 and assigned its narrow
replacement to this task. The final scan found only X032 and X146.

## Review R2 findings

Finding 1 is resolved: root Deno config, preload, and dependencies are removed;
Orca setup and all three workflows no longer download, install, or run Deno.
The final residual scan has only the two listed test-fixture rows.

Finding 3 is resolved: `turbo.json` now says the doctor verifies Node and Ruff,
and `docs/reference/commands.md` was regenerated with that description.

The coordinator reviewed the first failed combined check and approved removing
per-skill installs from Orca, `check.yml`, and `docs-check.yml`; those installs
created a `node_modules/.bin/acorn` resource that `test:plugin-skills` rejects.
That generated directory was removed. The audit workflow still runs `npm
audit` against the skill lock; `npm audit --prefix
plugins/code/skills/clean-code` passes without an installed skill-local tree.

Before the snapshot correction, the workflow help entry contained
`(Default: 'workspace')` and `(Default: 'HEAD')`. After it, those two strings
are `(Default: \"workspace\")` and `(Default: \"HEAD\")`. The first direct
snapshot-update attempt omitted the suite's permission flags and failed; the
normal command with `--test-update-snapshots` and the existing permissions
passed all 14 tests.

## Verification commands and results

| Command | Exit | Result |
| --- | ---: | --- |
| `npm run workflow` | 0 | Loaded the initial execution instructions. |
| `npm run workflow -- --task CHE-32-T009b --base HEAD --graph impact --file package.json` | 1 | Workflow impact supports code files, not `package.json`. |
| `npm run workflow -- --task CHE-32-T009b --base HEAD --graph impact --file scripts/ruff_test.ts` | 0 | Import policy passed. |
| `npm run workflow -- --task CHE-32-T009b --base HEAD --graph policy` | 0 | No import-policy violations. |
| `npm run workflow -- --task CHE-32-T009b --base HEAD` | 0 | Re-run after scope updates and before verification. |
| `npm install` | 0 | Removed five packages; zero vulnerabilities. |
| `npm run typecheck` | 0 | All entry points and 16 test files type-checked. |
| `npm run docs:generate` | 0 | Generated both reference files; repeated after final edits. |
| `npm run docs:check` | 0 | Both generated references pass; repeated after final generation. |
| `npm run test:git-flow` | 0 | 20 passed. |
| `npm run test:ruff` | 0 | 1 passed. |
| `npm run test:plugin-skills` | 1, then 0 | First run rejected the temporary skill-local `node_modules`; passed after coordinator-directed cleanup. |
| `npm ci` | 0 | Installed 359 root packages; zero vulnerabilities. |
| `npm ci --ignore-scripts --no-audit --no-fund --prefix plugins/code/skills/clean-code` | 0 | Temporary setup probe; its generated `node_modules` was removed after `test:plugin-skills` exposed the plugin resource boundary. |
| `npm ls` | 0 | Root dependency tree is clean. |
| `npm ls --prefix plugins/code/skills/clean-code` | 0 | The skill lock resolves cleanly. |
| `npm audit --prefix plugins/code/skills/clean-code` | 0 | Zero vulnerabilities; works without skill-local `node_modules`. |
| `npm run test:cli-contract` | 1, then 0 | First run had 13/14 passing because the workflow defaults changed quote style; passed 14/14 after X142 snapshot update. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test --test-update-snapshots scripts/cli_contract_test.ts` | 1 | Direct attempt lacked the permission flags and failed unrelated child-process cases. |
| `NODE_OPTIONS=--disable-warning=SecurityWarning node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --test --test-update-snapshots scripts/cli_contract_test.ts` | 0 | Updated only the two workflow default strings; 14 passed. |
| `node_modules/.bin/biome format --write scripts/backfire/fixtures/upstream-0.9.0/metadata.json scripts/backfire/fixtures/upstream-0.9.0/tools-list.json` | 0 | No fixture files needed formatting changes. |
| `npm run check` | 1, 1, then 0, 0 | The first failure was the temporary skill-local tree; the second was the workflow snapshot. Both full reruns passed with `Tasks: 27 successful, 27 total`; final run time was 2m23.26s. |
| `npm run verify -- --task CHE-32-T009b --base HEAD` | 0 | Workflow loop recorded `VERIFIED`; it is rerun after this report is written. |
| `rg -n -i '\\bdeno\\b|deno_shim|shim-deno|@std/fs' --glob '!specs/**' --glob '!.specify/**' --glob '!licenses/**' --glob '!**/*.lock' .` | 0 | Only the two X032 strings and X146 path remain. |
| `git diff --check -- .github/workflows/audit.yml .github/workflows/check.yml .github/workflows/docs-check.yml .gitignore biome.json deno.json docs/reference/commands.md docs/reference/plugins.md orca.yaml package-lock.json package.json scripts/backfire/fixtures/upstream-0.9.0/README.md scripts/cli_contract_test.ts.snapshot scripts/deno_shim.ts tsconfig.json turbo.json` | 0 | No whitespace errors. |

GitHub-hosted workflow execution was not available locally; their YAML passed
the repository's Prettier check in `npm run check`.
