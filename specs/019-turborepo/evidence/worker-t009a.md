# CHE-32 T009a worker report

## Changed files and selected rows

- `scripts/docs.ts`: X025, X047, X077, X083, X097, X102, X105, X130, X155.
- `scripts/doctor.ts`: X026, X049, X098, X124, X159.
- `scripts/workflow.ts`: X006, X041, X158.
- `scripts/workflow_files.ts`: X001, X037, X061.
- `scripts/workflow_git.ts`: X021, X031, X052.
- `scripts/workflow_graph.ts`: X020, X161.
- `scripts/workflow_plan.ts`: X007.
- `scripts/workflow_symbol.ts`: X008, X148.
- `scripts/workflow_verify.ts`: X012, X058, X125, X152.
- `scripts/validate_plugins.ts`: X011, X048.
- `scripts/clean_architecture.ts`: X017, X053, X065, X109, X139.
- `scripts/constitution_version.ts`: X050.
- `scripts/commitlint.config.mjs`: X055.
- `scripts/workflow-evidence.schema.json`: X126.

All selected rows for these files were changed. None were left unchanged.

X109 now scans `plugins/**/package.json` and `packages/**/package.json`, skips `node_modules`, and reads `name`, `imports`, and `exports` through `readPackageConfig()`. It retains the existing plugin/package directory fallback scan. This follows coordinator decision D18 and restores the `plugins/code` public API boundary using its new package manifest.

## API changes and compatibility

`doctor.ts` no longer accepts the `deno` option or `--deno`, probes a Deno executable or version, or returns a `deno` report field. Workflow evidence uses `context.node_version` instead of `context.deno_version`, and the schema matches. Existing evidence records without `node_version` are treated as stale in memory; the evidence file is neither rewritten nor deleted.

## Unselected sites and pending work

The target-file scan for `Deno`, `@std/fs`, and `deno_shim` returned no matches. No unselected code site in the owned files needs a change.

`npm run docs:check` reports only `docs/reference/commands.md` as changed; line 93 still documents the removed `--deno` option. This generated file is outside T009a ownership. The coordinator directed that T009b refresh `docs/reference/*.md` after all tasks finish, so it was left untouched.

## Verification

| Command | Exit | Result |
| --- | ---: | --- |
| `deno task workflow` | 0 | Workflow instructions loaded before and after the report. |
| `npm run workflow -- --task T009a --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph impact --file scripts/clean_architecture.ts` | 1 | Before D18 package config loading, policy reported five missing `plugins/code` public API edges. |
| `npm run workflow -- --task T009a --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph policy` | 0 | No import-policy violations after D18. |
| `npm run clean-architecture` | 0 | 63 files scanned; zero violations. |
| `npx tsc --noEmit -p .tsconfig-T009a.json` | 0 | Temporary tsconfig omitted `scripts/deno_shim.ts`; the file was removed after the check. |
| `npm run doctor` | 0 | Doctor passed. |
| `npm run docs:check` | 1 | Only `docs/reference/commands.md` is stale; T009b will regenerate it. |
| `npm run plugins:validate` | 0 | All three plugins passed. |
| `npm run lint` | 0 | Passed across the workspace. |
| `npm run format:check` | 0 | Passed across the workspace. |
| `./node_modules/.bin/biome lint --error-on-warnings scripts/docs.ts scripts/doctor.ts scripts/workflow.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_graph.ts scripts/workflow_plan.ts scripts/workflow_symbol.ts scripts/workflow_verify.ts scripts/validate_plugins.ts scripts/clean_architecture.ts scripts/constitution_version.ts scripts/commitlint.config.mjs scripts/workflow-evidence.schema.json` | 0 | All 14 target files passed. |
| `./node_modules/.bin/biome format scripts/docs.ts scripts/doctor.ts scripts/workflow.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_graph.ts scripts/workflow_plan.ts scripts/workflow_symbol.ts scripts/workflow_verify.ts scripts/validate_plugins.ts scripts/clean_architecture.ts scripts/constitution_version.ts scripts/commitlint.config.mjs scripts/workflow-evidence.schema.json` | 0 | All 14 target files passed. |
| `rg -n '\bDeno\b|@std/fs|deno_shim' scripts/docs.ts scripts/doctor.ts scripts/workflow.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_graph.ts scripts/workflow_plan.ts scripts/workflow_symbol.ts scripts/workflow_verify.ts scripts/validate_plugins.ts scripts/clean_architecture.ts scripts/constitution_version.ts scripts/commitlint.config.mjs scripts/workflow-evidence.schema.json` | 1 | No matches. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/doctor.ts` | 0 | Doctor ran without the preload. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/docs.ts check` | 1 | Same pending generated-docs difference as `npm run docs:check`. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/validate_plugins.ts` | 0 | Validation ran without the preload. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/clean_architecture.ts` | 0 | Architecture scan ran without the preload. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/workflow.ts --help` | 0 | Workflow CLI loaded without the preload. |
| `npm run workflow` | 0 | Workspace workflow exited 0 but reports that prior verification failed, was interrupted, or code changed during checks; it defers combined verification until workers finish. |
| `git diff --check -- scripts/docs.ts scripts/doctor.ts scripts/workflow.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_graph.ts scripts/workflow_plan.ts scripts/workflow_symbol.ts scripts/workflow_verify.ts scripts/validate_plugins.ts scripts/clean_architecture.ts scripts/constitution_version.ts scripts/commitlint.config.mjs scripts/workflow-evidence.schema.json` | 0 | No whitespace errors in the owned scripts. |
| `rg -n '[ \t]+$' specs/019-turborepo/evidence/worker-T009a.md` | 1 | No trailing whitespace in the report. |
| `test ! -e .tsconfig-T009a.json` | 0 | The temporary tsconfig was removed. |

At the time of the initial T009a report, no test suite or combined `npm run verify` was run because T010/T011 owned the converted tests. The follow-up below ran existing suites; combined verification remains deferred until all workers finish. A complexity-only ponytail review found no unnecessary abstraction or code to remove. Final review remains with the coordinator.

## Follow-up

Assumption: the five catches receive Node filesystem errors, so the requested `NodeJS.ErrnoException` cast is appropriate. The shorter casts passed typecheck and Biome.

Changed files and row coverage:

- `scripts/docs.ts`: X025, X047, X077, X083, X097, X102, X105, X130, X155. Replaced the ENOENT guard.
- `scripts/workflow_files.ts`: X001, X037, X061. Replaced the ENOENT guard.
- `scripts/workflow_git.ts`: X021, X031, X052. Replaced the ENOENT guard and restored both `mode: info.mode` properties.
- `scripts/workflow_verify.ts`: X012, X058, X125, X152. Replaced the ENOENT guard.
- `scripts/validate_plugins.ts`: X011, X048. Replaced the ENOENT guard.

No selected row was left unchanged. The two mode properties were unselected lines; they now preserve the full `st_mode` value as Deno and Node `lstat` do. No failing test required the mask: `npm run test:workflow` passed all 56 tests. No other unselected site in these files needs a change. The generated `docs/reference/commands.md` difference remains assigned to T009b as described above.

Follow-up commands and exit codes:

| Command | Exit | Result |
| --- | ---: | --- |
| `npm run workflow -- --task T009a-followup --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph impact --file scripts/docs.ts` | 0 | Pre-edit impact scan. |
| `npm run workflow -- --task T009a-followup --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph impact --file scripts/workflow_files.ts` | 0 | Pre-edit impact scan. |
| `npm run workflow -- --task T009a-followup --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph impact --file scripts/workflow_git.ts` | 0 | Pre-edit impact scan. |
| `npm run workflow -- --task T009a-followup --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph impact --file scripts/workflow_verify.ts` | 0 | Pre-edit impact scan. |
| `npm run workflow -- --task T009a-followup --base a60d899aff48f74419b8aa8ec --graph impact --file scripts/validate_plugins.ts` | 0 | Pre-edit impact scan. |
| `npm run typecheck` | 0 | Node typecheck passed with the requested casts. |
| `npx tsc --noEmit -p .tsconfig-T009a.json` | 0 | Temporary tsconfig omitted `scripts/deno_shim.ts`; it was removed after the check. |
| `./node_modules/.bin/biome lint --error-on-warnings scripts/docs.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_verify.ts scripts/validate_plugins.ts` | 0 | All five changed scripts passed. |
| `./node_modules/.bin/biome format scripts/docs.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_verify.ts scripts/validate_plugins.ts` | 1 | Initial check identified three one-line formatting adjustments. |
| `./node_modules/.bin/biome format --write scripts/docs.ts scripts/workflow_files.ts scripts/workflow_verify.ts` | 0 | Applied only the reported formatting changes. |
| `./node_modules/.bin/biome format scripts/docs.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_verify.ts scripts/validate_plugins.ts` | 0 | Final focused format check passed. |
| `npm run lint` | 0 | Passed; it still reports three non-blocking infos in unowned `scripts/ruff_test.ts`. |
| `npm run format:check` | 1, then 0 | Initial run caught the same formatting changes; rerun passed after formatting. |
| `npm run test:workflow` | 0 | 56 passed, 0 failed. |
| `npm run test:docs` | 0 | 14 passed, 0 failed. |
| `npm run test:plugin-skills` | 0 | 3 passed, 0 failed. |
| `npm run clean-architecture` | 0 | 63 files scanned; zero violations. |
| `npm run doctor` | 0 | Doctor passed. |
| `npm run plugins:validate` | 0 | All three plugins passed. |
| `npm run docs:check` | 1 | Only the generated command reference remains stale; T009b will regenerate it. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/doctor.ts` | 0 | No-preload run passed. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/docs.ts check` | 1 | Same pending generated-docs difference. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/validate_plugins.ts` | 0 | No-preload run passed. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/clean_architecture.ts` | 0 | No-preload run passed. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON scripts/workflow.ts --help` | 0 | No-preload run passed. |
| `npm run workflow -- --task T009a-followup --base a60d899aff48f74419b28b236081dba19b8aa8ec --graph policy` | 0 | No import-policy violations. |
| `deno task workflow` | 0 | Workflow instructions loaded after the follow-up edits. |
| `npm run workflow` | 0 | Workspace workflow completed; combined verification remains for the coordinator after workers finish. |
| `git diff --check -- scripts/docs.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_verify.ts scripts/validate_plugins.ts` | 0 | No whitespace errors in the changed scripts. |
| `rg -n "info\.mode & 0o777|typeof error === 'object'|'code' in error" scripts/docs.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_verify.ts scripts/validate_plugins.ts` | 1 | Neither the mode mask nor the longer guards remain. |
| `test ! -e .tsconfig-T009a.json` | 0 | Temporary tsconfig removed. |
