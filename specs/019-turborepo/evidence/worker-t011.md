# CHE-32 T011 worker report

## Changed files and selected rows

- `scripts/doctor_test.ts`: X009, X035, X057, X074, X095, X123, X156.
- `scripts/workflow_test.ts`: X013, X110, X145.
- `scripts/git_flow_test.ts`: X005, X056, X071, X094, X103, X153.
- `scripts/ruff_test.ts`: X018, X033, X034, X044, X080.
- `scripts/workflow_verify_test.ts`: X019, X051, X076.
- `scripts/workflow_graph_test.ts`: X022, X069, X111.
- `scripts/workflow_plan_test.ts`: X027, X114. The coordinator reclassified X114 from `leave` to `must_change` during the task; the fixture now uses `package.json` with the same exports map.
- `scripts/worktree_branch_test.ts`: X023.

The tests use Node built-ins for file, process, temp-directory and test APIs. Fake `uv`, `git`, `npm`, and check programs now use Node arguments and exit handling. The workflow verification fixture also uses Node commands and checks `node_version` evidence. The graph test's `readFile` monkeypatch preserves Node's overload type with `typeof fs.readFile`.

## Doctor test purpose changes

T009a removed Deno checks from the doctor, so these selected test cases now cover the remaining Node and Quarto behavior:

- `root task permits relocated and symlinked runtimes` now checks that the direct Node CLI works from an empty `HOME`.
- `missing, relative, non-executable and wrong-identity paths fail before report creation` now checks invalid Quarto paths and wrong Quarto versions.
- `standalone aliases pass but .venv and Quarto runtime paths are refused` now checks a valid Quarto alias, `.venv` refusal, and a wrong Quarto identity.
- The version-probe test replaces its wrong Deno version fixture with a wrong Quarto version fixture.
- `CLI rejects invalid flags and missing runtime/report permissions` now checks invalid CLI flags and successful report writing; Deno permission-denial checks no longer apply.

No unrelated tests were skipped. The selected Deno-only cases were adapted to Node or Quarto behavior as allowed by the task. Baseline counts in `report.md` were doctor 16, Git Flow 20, workflow 56, and worktree-branch 3; the Ruff suite from develop adds one case. Doctor now reports 17 because the existing Ruff-environment case used `Deno.test` and is now registered through `node:test`.

## Selected rows left unchanged

- X032 stays `leave`: the two `Deno.FileInfo` strings in `scripts/workflow_graph_test.ts:338` and `:450` are test fixture source text covered by that row.
- X146 stays `leave`: the `.deno/cache/consumer.ts` literal in `scripts/workflow_plan_test.ts` preserves the scanner-exclusion case.
- No other selected row was left unchanged.

## Unselected sites

No unselected Deno or `@std/fs` site in these files needs a change. The required residual scan found only the two X032 `Deno.FileInfo` strings above; it found no `@std/fs` imports. The remaining `.deno/cache` literal is X146 and remains unchanged per its `leave` row.

## Verification

| Command | Exit | Result |
| --- | ---: | --- |
| `npm run test:workflow` | 0 | 56 passed, 0 failed. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission '--allow-fs-read=*' '--allow-fs-write=*' --allow-child-process --test scripts/workflow_test.ts scripts/workflow_plan_test.ts scripts/workflow_verify_test.ts scripts/workflow_graph_test.ts` | 0 | 47 passed, 0 failed without the preload. |
| `npm run test:doctor` | 0 | 17 passed, 0 failed. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission '--allow-fs-read=*' '--allow-fs-write=*' --allow-child-process --test scripts/doctor_test.ts` | 0 | 17 passed, 0 failed without the preload. |
| `npm run test:git-flow` | 1 | 19 passed, 1 failed. The final fixture fails because the copied root `package.json` still preloads `scripts/deno_shim.ts`, which X071 removes from the fixture. T009b will remove the root preload; the coordinator directed us to leave the fixture commitlint setup unchanged until then. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission '--allow-fs-read=*' '--allow-fs-write=*' --allow-child-process --test scripts/git_flow_test.ts` | 1 | Same 19/20 result and missing `scripts/deno_shim.ts` fixture failure. |
| `npm run test:worktree-branch` | 0 | 3 passed, 0 failed. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission '--allow-fs-read=*' --allow-fs-write=/tmp --allow-child-process --test scripts/worktree_branch_test.ts` | 0 | 3 passed, 0 failed without the preload. |
| `npm run test:ruff` | 1 | The root package has no `test:ruff` script yet; T009b owns that script change. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission '--allow-fs-read=*' '--allow-fs-write=*' --allow-child-process --test scripts/ruff_test.ts` | 0 | 1 passed, 0 failed without the preload. |
| `./node_modules/.bin/biome format scripts/doctor_test.ts scripts/workflow_test.ts scripts/git_flow_test.ts scripts/ruff_test.ts scripts/workflow_verify_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/worktree_branch_test.ts` | 0 | Checked all 8 files; no fixes needed. |
| `./node_modules/.bin/biome lint --error-on-warnings scripts/doctor_test.ts scripts/workflow_test.ts scripts/git_flow_test.ts scripts/ruff_test.ts scripts/workflow_verify_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/worktree_branch_test.ts` | 0 | Checked all 8 files; three informational `useTemplate` diagnostics remain in the Ruff fixture. |
| `npx tsc --ignoreConfig --noEmit --allowImportingTsExtensions --erasableSyntaxOnly --module Preserve --moduleResolution Bundler --target ESNext --types node --skipLibCheck scripts/doctor_test.ts scripts/workflow_test.ts scripts/git_flow_test.ts scripts/ruff_test.ts scripts/workflow_verify_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/worktree_branch_test.ts` | 0 (initially 2) | The first run flagged the `readFile` monkeypatch's overloaded type at `workflow_graph_test.ts:467`; preserving `typeof fs.readFile` fixed it, and the rerun passed all 8 test files and imports. |
| `rg -n '\bDeno\b|@std/fs' scripts/doctor_test.ts scripts/workflow_test.ts scripts/git_flow_test.ts scripts/ruff_test.ts scripts/workflow_verify_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/worktree_branch_test.ts` | 0 | Only the two allowed X032 fixture references matched. |
| `git diff --check` | 0 | No whitespace errors. |
| `npm run workflow -- --task CHE-32-T011 --graph policy` | 0 | Static import policy passed with no violations. |
| `deno task workflow` | 0 | Workflow instructions loaded; final workspace state remains in REVIEW mode. |
| `deno task verify` | 1 | One run stopped before checks with `EXECUTION_FAILED: Code changed during skill scope selection`; after rerunning workflow, the next run completed checks but stopped at `docs:check`. It reported only `docs/reference/commands.md` as stale, still documenting removed `--deno`; fail-fast interrupted parallel suites. T009a's report confirms T009b owns documentation regeneration. |

The installed Biome CLI rejects `--check` for `biome format` (exit 1); the supported `biome format <files>` command above passed. The latest combined verify log is `/home/choi-eunchang/workspaces/verbose-broccoli/develop/.git/worktrees/feature-turborepo/workflow/91beb6b6-bccc-4add-aa95-70fb7a6e63da.log`.

## Follow-up

The coordinator requested three corrections:

- `scripts/doctor_test.ts` (X074): retained Node's `--permission` flag and permission list, while removing only the shim preload. Restored the `deniedRun`, `deniedRead`, and `deniedWrite` cases, the write-only grant for the successful report case, and the original test name. The `--deno` CLI case remains replaced by `--node`; the empty-`HOME` test still passes its environment separately.
- `scripts/ruff_test.ts` (X018): the temporary directory prefix is `/tmp/ruff-test-`, independent of `TMPDIR`.
- `scripts/workflow_graph_test.ts` (X111): the `plugins/demo` fixture uses `exports: './src/api.ts'`. `npm run test:workflow` passes with this export shape, so the `./api` subpath is not needed. The other package fixture's `{'.': './src/api.ts'}` remains unchanged.

X032 and X146 remain `leave`; no other unselected site needs a change. The earlier doctor note about Deno permission-denial checks still applies; this follow-up restores coverage for Node's permission model.

| Follow-up command | Exit | Result |
| --- | ---: | --- |
| `npm run test:doctor` | 0 | 17 passed, 0 failed, including the restored Node permission cases. |
| `npm run test:workflow` | 0 | 56 passed, 0 failed; the string package export fixture passes. |
| `npm run test:worktree-branch` | 0 | 3 passed, 0 failed. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission '--allow-fs-read=*' --allow-fs-write=/tmp --allow-child-process --test scripts/ruff_test.ts` | 0 | 1 passed, 0 failed; test uses `/tmp` without the preload. |
| `npx tsc --ignoreConfig --noEmit --allowImportingTsExtensions --erasableSyntaxOnly --module Preserve --moduleResolution Bundler --target ESNext --types node --skipLibCheck scripts/doctor_test.ts scripts/workflow_test.ts scripts/git_flow_test.ts scripts/ruff_test.ts scripts/workflow_verify_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/worktree_branch_test.ts` | 0 | All 8 test files and imports type-checked. |
| `./node_modules/.bin/biome format scripts/doctor_test.ts scripts/workflow_test.ts scripts/git_flow_test.ts scripts/ruff_test.ts scripts/workflow_verify_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/worktree_branch_test.ts` | 0 | No fixes needed. |
| `./node_modules/.bin/biome lint --error-on-warnings scripts/doctor_test.ts scripts/workflow_test.ts scripts/git_flow_test.ts scripts/ruff_test.ts scripts/workflow_verify_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/worktree_branch_test.ts` | 0 | Three informational `useTemplate` diagnostics remain in the Ruff fixture. |
| `git diff --check` | 0 | No whitespace errors. |
| `rg -n '\bDeno\b|@std/fs' scripts/doctor_test.ts scripts/workflow_test.ts scripts/git_flow_test.ts scripts/ruff_test.ts scripts/workflow_verify_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/worktree_branch_test.ts` | 0 | Only the two X032 fixture references matched. |
| `npm run workflow -- --task CHE-32-T011-followup --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph impact --file scripts/doctor_test.ts` | 0 | Pre-edit impact scan passed. |
| `npm run workflow -- --task CHE-32-T011-followup --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph impact --file scripts/ruff_test.ts` | 0 (initially 1) | Retry passed after a transient code-snapshot change error. |
| `npm run workflow -- --task CHE-32-T011-followup --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph impact --file scripts/workflow_graph_test.ts` | 0 | Pre-edit impact scan passed. |
| `npm run workflow -- --task CHE-32-T011-followup --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph policy` | 0 | No import-policy violations after edits. |
| `deno task workflow` | 0 | Final workflow instructions loaded. |

Git Flow's existing 19/20 failure and the missing `test:ruff` npm script remain assigned to T009b, as directed. The combined `deno task verify` was not rerun in this follow-up; the previous task's workflow required coordinator review after two consecutive failures, and its latest log records the T009b-owned stale generated documentation.
