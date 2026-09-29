# CHE-32 T008: clean-code on Node.js

At original T008 completion, T009b owned the root `clean-code`, `clean-code:scope`, and `test:clean-code` scripts, so that worker left `package.json` unchanged. This follow-up applies the two requested root script changes.

## Files changed and selected rows

| File | Selected rows | Change |
| --- | --- | --- |
| `plugins/code/skills/clean-code/SKILL.md` | X089, X118, X134, X168 | Document Node.js 24.12.0+, official Node feature references, and user-facing Node commands. |
| `plugins/code/deno.json` | W2 | Deleted the Deno plugin manifest. |
| `plugins/code/skills/clean-code/deno.json`, `deno.lock` | W2 | Deleted the skill's Deno config and lock. |
| `plugins/code/skills/clean-code/scripts/clean_code.ts` | X028, X059, X066 | Replaced Deno file/process APIs and `@std/fs` glob with Node built-ins. |
| `plugins/code/skills/clean-code/scripts/cli.ts` | X060 | Replaced Deno argument and exit-code APIs with `process`. |
| `plugins/code/skills/clean-code/scripts/clean_code_test.ts` | X029, X036 | Moved tests to `node:test` and Node filesystem/temp-directory APIs. |
| `scripts/plugin_skills_test.ts` | X010, X042, X063 | Replaced Deno and `@std/fs` test APIs with Node built-ins. |
| `scripts/cli_contract_test.ts` | X016, X046, X075, X082, X101, X113, X131, X151 | Replaced Deno APIs; run Clean Code with Node and install/run its copied skill independently. |
| `scripts/cli_contract_test.ts.snapshot` | X142 | Removed the stale Deno option from the doctor help snapshot. |
| `scripts/workflow_skills.ts` | X024, X054, X081, X092, X112, X132, X143 | Run Clean Code with Node and replace Deno filesystem and environment APIs. |
| `scripts/workflow_skills_test.ts` | X002, X038, X068 | Replaced Deno APIs and shim-based child execution with Node. |
| `plugins/code/skills/clean-code/package.json` | D16 | Added a self-contained Node package with the requested pinned dependencies and Node engine. |
| `plugins/code/skills/clean-code/package-lock.json` | D16 | Added the npm lock generated from the skill manifest. |
| `plugins/code/skills/clean-code/.npmrc` | D16 | Added the JSR registry and `allow-remote=root` settings. |

## Selected rows left unchanged

None. The clean-code help text did not change, so its snapshot entry stayed byte-for-byte the same; X142's stale doctor help line was removed.

## Unselected site for T009b

`docs/reference/commands.md:93` still contains `--deno <path> - Absolute path to standalone Deno.` The combined workflow check reports `changed=[docs/reference/commands.md]` and recommends `npm run docs:generate`. I left this generated file untouched because it is outside T008 ownership. The coordinator confirmed T009b regenerates `docs/reference/*.md` after every other task and asked me to report this failure as expected.

No other unselected site required a T008 code change based on the checks below.

## Package and commands

The skill package pins `eslint` 10.10.0, `typescript-eslint` 8.70.0, `typescript` 6.0.3, and `@typescript-eslint/utils` 8.70.0. It keeps `@cliffy/command` 1.2.1, `@std/assert` 1.0.19, and `@std/path` 1.1.6 as npm JSR aliases. The `@std/fs` import was removed because it needs Deno's global at runtime.

The skill requires Node.js 24.12.0 or later: [TypeScript type stripping](https://nodejs.org/download/release/v24.19.0/docs/api/typescript.html) became stable in 24.12.0, [`import.meta.main`](https://nodejs.org/download/release/v24.19.0/docs/api/esm.html) was added in 24.2.0, and [`fsPromises.glob`](https://nodejs.org/download/release/v24.19.0/docs/api/fs.html) became stable in 24.0.0.

Root script lines handed to T009b at original T008 completion (updated below in Follow-up):

```json
"clean-code": "node plugins/code/skills/clean-code/scripts/clean_code.ts",
"clean-code:scope": "npm run clean-code -- --scope",
"test:clean-code": "node --test plugins/code/skills/clean-code/scripts/clean_code_test.ts"
```

## Help text

Clean-code help text was identical before and after:

```text
Usage: clean-code

Description:

  Check the mechanically selected Clean Code subset from the target workspace root.

Options:

  -h, --help  - Show this help.
  --scope     - Report the shared skill/checker file scope only.
```

The doctor help text before the snapshot update was:

```text
Usage: doctor

Description:

  Check runtime identities, versions and locked dependencies.

Options:

  -h, --help          - Show this help.
  --deno      <path>  - Absolute path to standalone Deno.
  --quarto    <path>  - Absolute path to Quarto.
  --report    <path>  - Create a new JSON report; requires write permission.
```

After the update, the doctor help text was:

```text
Usage: doctor

Description:

  Check runtime identities, versions and locked dependencies.

Options:

  -h, --help          - Show this help.
  --quarto    <path>  - Absolute path to Quarto.
  --report    <path>  - Create a new JSON report; requires write permission.
```

The coordinator authorized this snapshot-only doctor update after the first CLI contract run exposed the stale entry.

## Verification

Commands and exit codes:

| Command | Exit | Result |
| --- | ---: | --- |
| `npm install --package-lock-only --prefer-offline --ignore-scripts --no-audit --no-fund --prefix plugins/code/skills/clean-code` | 0 | Generated the skill lock without creating skill-local `node_modules`. |
| `node --test plugins/code/skills/clean-code/scripts/clean_code_test.ts` | 0 | 35 passed. |
| `npm run test:plugin-skills` | 0 | 3 passed. |
| `npm run test:cli-contract` | 0 | Final of three runs; 14 passed, including the copied-skill install and scope run. The first two runs exited 1 on conversion-related CLI expectations and the stale doctor snapshot; corrected, with the snapshot update authorized. |
| `node --test scripts/workflow_skills_test.ts` | 0 | 9 passed. |
| `node_modules/.bin/biome format --write plugins/code/skills/clean-code/scripts/clean_code.ts plugins/code/skills/clean-code/scripts/cli.ts plugins/code/skills/clean-code/scripts/clean_code_test.ts scripts/plugin_skills_test.ts scripts/cli_contract_test.ts scripts/workflow_skills.ts scripts/workflow_skills_test.ts plugins/code/skills/clean-code/package.json` | 0 | Formatted the changed code and manifest files. |
| `node_modules/.bin/biome check plugins/code/skills/clean-code/scripts/clean_code.ts plugins/code/skills/clean-code/scripts/cli.ts plugins/code/skills/clean-code/scripts/clean_code_test.ts scripts/plugin_skills_test.ts scripts/cli_contract_test.ts scripts/workflow_skills.ts scripts/workflow_skills_test.ts plugins/code/skills/clean-code/package.json plugins/code/skills/clean-code/package-lock.json` | 0 | Checked 8 files; no fixes needed. |
| `node plugins/code/skills/clean-code/scripts/clean_code.ts --scope` | 0 | 33 candidates; 0 selected, 33 excluded, 0 errors. |
| `t008_tmpdir=$(mktemp -d /tmp/clean-code-t008.XXXXXX)` | 0 | Created the external-copy directory. |
| `cp -a plugins/code/skills/clean-code/. "$t008_tmpdir/"` | 0 | Copied the complete skill outside the repository. |
| `npm ci --prefix "$t008_tmpdir" --prefer-offline --ignore-scripts --no-audit --no-fund` | 0 | Installed 108 packages. |
| `node "$t008_tmpdir/scripts/clean_code.ts" --scope` | 0 | Ran successfully from the external copy. |
| `find plugins/code -type d -name node_modules -print` | 0 | No output; confirmed no dependencies landed inside `plugins/code`. |
| `rg -n 'Deno|deno' plugins/code` | 1 | No matches. |
| `git diff --check -- plugins/code/skills/clean-code/SKILL.md plugins/code/skills/clean-code/scripts/clean_code.ts plugins/code/skills/clean-code/scripts/cli.ts plugins/code/skills/clean-code/scripts/clean_code_test.ts plugins/code/skills/clean-code/deno.json plugins/code/skills/clean-code/deno.lock plugins/code/deno.json scripts/plugin_skills_test.ts scripts/cli_contract_test.ts scripts/cli_contract_test.ts.snapshot scripts/workflow_skills.ts scripts/workflow_skills_test.ts` | 0 | No whitespace errors. |
| `npm run workflow -- --task CHE-32-T008 --base 9bef254e64fc1fff5e67dfd6acd3998d5d194038 --graph policy` | 0 | Final run passed with no policy errors. |
| `deno task workflow` | 0 wrapper; 1 internal docs check | The final legacy wrapper run recorded `docs:check` exit 1 for the expected stale generated line at `docs/reference/commands.md:93`; coordinator assigned regeneration to T009b. Earlier, the pre-edit run passed, one post-scope run exited 1 because the shared evidence schema required `node_version`, and a later run passed after T009a handled that record. |

The plugin-local `node_modules` check and `rg` result above are expected: the copied package resolves dependencies from the repository root in-repo, and no Deno references remain under `plugins/code`. Per coordinator direction, use `npm run workflow` for the final workflow entry point; the legacy `deno task workflow` run above only records the existing generated-doc failure.

## Status at original T008 completion

At that point, T009b still needed to apply the root script lines above. The coordinator owns generated documentation and combined repository verification after all CHE-32 workers finish.

## Follow-up

The requested Node API fixes and root script integration are complete.

| File | Selected rows | Change |
| --- | --- | --- |
| `plugins/code/skills/clean-code/scripts/clean_code.ts` | X028, X066 | Removed the unsupported `followSymlinks` option; Node glob does not descend into symlinked directories, and the `isSymbolicLink()` filter remains. |
| `scripts/plugin_skills_test.ts` | X010 | Replaced the ignored `@std/assert` predicate with Node `assert.rejects` matching the `ENOENT` code. |
| `scripts/workflow_skills_test.ts` | X002 | Replaced the ignored predicate with Node `assert.rejects` matching `ENOENT`. |
| `scripts/cli_contract_test.ts` | X082, X131 | Removed the Clean Code help and invalid-argument special cases so both use `npm run` like the other commands. The snapshot did not change. |
| `package.json` | X087, X117, X133, X166 | Changed only `clean-code` and `test:clean-code` to Node with filesystem permission flags. Left `clean-code:scope` and every other script/preload unchanged. |

The final root scripts are:

```json
"clean-code": "node --permission --allow-fs-read=* plugins/code/skills/clean-code/scripts/clean_code.ts",
"clean-code:scope": "npm run clean-code -- --scope",
"test:clean-code": "node --permission --allow-fs-read=* --allow-fs-write=* --test-isolation=none --test plugins/code/skills/clean-code/scripts/clean_code_test.ts"
```

`test:clean-code` uses `--test-isolation=none`, so it needs no child-process permission. A trial with `--allow-fs-write=/tmp` failed because Node requires full filesystem read and write permission for `fs.symlink`; `--allow-fs-write=*` is the smallest passing flag set for the existing test. Node has no environment permission flag, so there is no `--allow-env` equivalent.

No follow-up requested edit was skipped. The scope script and unrelated root scripts remain unchanged as requested. The known unselected generated-doc site remains `docs/reference/commands.md:93`, where the stale `--deno` doctor option awaits T009b's `npm run docs:generate`; the prior combined check evidence and coordinator direction are recorded above. No other unselected site was found to require change.

Follow-up verification commands and exit codes:

| Command | Exit | Result |
| --- | ---: | --- |
| `npm run workflow -- --task CHE-32-T008-followup --base HEAD --graph impact --file plugins/code/skills/clean-code/scripts/clean_code.ts` | 0 | Initial impact graph passed. |
| `npx tsc --ignoreConfig --noEmit --allowImportingTsExtensions --erasableSyntaxOnly --module Preserve --moduleResolution Bundler --target ESNext --types node --skipLibCheck plugins/code/skills/clean-code/scripts/clean_code.ts plugins/code/skills/clean-code/scripts/clean_code_test.ts scripts/plugin_skills_test.ts scripts/cli_contract_test.ts scripts/workflow_skills.ts scripts/workflow_skills_test.ts` | 0 | Passed twice, including after formatting. |
| `npm run test:clean-code` running `node --permission --allow-fs-read=* --allow-fs-write=/tmp --test-isolation=none --test plugins/code/skills/clean-code/scripts/clean_code_test.ts` | 1 | Narrow write permission failed at the symlink test with `fs.symlink API requires full fs.read and fs.write permissions`. |
| `npm run test:clean-code` running `node --permission --allow-fs-read=* --allow-fs-write=* --test-isolation=none --test plugins/code/skills/clean-code/scripts/clean_code_test.ts` | 0 | All 35 tests passed; no child-process permission was needed. |
| `npm run clean-code:scope` | 0 | 33 candidates, 0 selected, 33 excluded, 0 errors. |
| `npm run test:plugin-skills` | 0 | 3 passed. |
| `npm run test:cli-contract` | 0 | 14 passed; help snapshot unchanged. |
| `node --test scripts/workflow_skills_test.ts` | 0 | 9 passed. |
| `node_modules/.bin/biome check package.json plugins/code/skills/clean-code/scripts/clean_code.ts scripts/plugin_skills_test.ts scripts/cli_contract_test.ts scripts/workflow_skills_test.ts` | 1 | Reported one formatting difference in `scripts/cli_contract_test.ts`. |
| `node_modules/.bin/biome format --write scripts/cli_contract_test.ts` | 0 | Applied the requested formatting. |
| `node_modules/.bin/biome check package.json plugins/code/skills/clean-code/scripts/clean_code.ts plugins/code/skills/clean-code/scripts/cli.ts plugins/code/skills/clean-code/scripts/clean_code_test.ts scripts/plugin_skills_test.ts scripts/cli_contract_test.ts scripts/workflow_skills.ts scripts/workflow_skills_test.ts` | 0 | Checked 8 files; no fixes needed. |
| `git diff --check -- package.json plugins/code/skills/clean-code/scripts/clean_code.ts scripts/plugin_skills_test.ts scripts/cli_contract_test.ts scripts/workflow_skills_test.ts specs/019-turborepo/evidence/worker-T008.md` | 0 | No whitespace errors. |
| `npm run workflow -- --task CHE-32-T008-followup --base HEAD --graph policy` | 0 | Final policy graph passed with no errors. |

The coordinator still owns the full combined `npm run verify` and T009b's generated-doc refresh.
