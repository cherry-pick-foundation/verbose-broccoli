# CHE-32 T010 worker report

Scope: the coordinator confirmed that `scripts/ruff_test.ts` belongs to T011, so this report covers T010's four owned test files.

## Changed files and selected rows

- `scripts/wiki_raw_import_test.ts`: X015, X043, X064, X160. Deno filesystem and process calls and `@std/fs` imports now use Node built-ins. Its recursive fixture walk uses `readdir` with `recursive` and `withFileTypes`.
- `scripts/docs_test.ts`: X003, X039, X062, X070, X079, X106, X121, X147. Deno APIs and `@std/fs` imports now use Node built-ins. Child fixtures run under Node without importing the shim; test stubs use Node's built-in module synchronization.
- `scripts/clean_architecture_test.ts`: X004, X040, X108, X157. Deno APIs now use Node built-ins, and config fixtures use `package.json` with the same `imports` and `exports` fields read by the updated checker.
- `scripts/commit_msg_test.ts`: X014, X045, X072, X096, X100, X154. Deno APIs, environment reads, shim loading and fixture setup now use Node built-ins. The copied repository fixture runs commitlint with a Node-only `NODE_OPTIONS` value.

No selected rows in these four files were left unchanged. There are no selected `leave` rows in these files. `scripts/ruff_test.ts` was not edited or tested by this dispatch per the coordinator's direction; T011 owns it.

## Test cases with a changed purpose

- `scripts/clean_architecture_test.ts`: the former unsupported Deno `scopes` case is now `architecture: package exports cannot escape their plugin root`. Node package manifests have no Deno `scopes` field; the selected case now checks the equivalent package-config boundary behavior introduced by D18. The alias and member-alias-conflict cases kept their behavior and now write `package.json` fixtures.
- `scripts/docs_test.ts`: `references: local and PR check entrypoints agree without Node actions` no longer expects Deno install/version commands. It checks Node 24.19, `npm ci --ignore-scripts`, and `npm run docs:check` instead. Other reference tests keep their purpose.

No Deno relocation, `DENO_DIR`, or permission-flag doctor fixtures were present in the four owned files.

## Unselected sites and remaining combined-check issue

No unselected site in the four owned files needs a change. The combined check still finds generated `docs/reference/commands.md` stale at line 93, where it documents the removed `--deno` option. This file is outside T010 ownership; T009a's report says T009b will refresh `docs/reference/*.md` after the workers finish.

The coordinator also directed that the combined verification wait until all workers finish. The `deno task workflow` run recorded `npm run check` exit 1 only at `//:docs:check`, which reports `docs/reference/commands.md` as changed and suggests `npm run docs:generate`; see workflow log `91beb6b6-bccc-4add-aa95-70fb7a6e63da`. At that point the workflow reported three consecutive failures and said the main agent must review this log and replan before another repair attempt.

## Verification

| Command | Exit | Result |
| --- | ---: | --- |
| `npm run test:wiki-raw-import` | 0 | 43 passed, 0 failed. |
| `npm run test:docs` | 0 | 14 passed, 0 failed, including the final rerun after the typed stub change. |
| `npm run test:clean-architecture` | 0 | 4 passed, 0 failed after T009a's D18 package-config scan landed. |
| `npm run test:commit-msg` | 0 | 5 passed, 0 failed. The copied commit hook's Node probe and commitlint fixture run without the Deno shim. |
| `npx tsc --ignoreConfig --noEmit --allowImportingTsExtensions --erasableSyntaxOnly --module Preserve --moduleResolution Bundler --target ESNext --types node --skipLibCheck scripts/wiki_raw_import_test.ts scripts/docs_test.ts scripts/clean_architecture_test.ts scripts/commit_msg_test.ts` | 0 | All four files and their imports type-checked. The first run exited 2 on the generic Node `readFile` stub; the helper now uses `GetParametersFromProp` and `GetReturnFromProp` from the existing mock library. |
| `./node_modules/.bin/biome check scripts/wiki_raw_import_test.ts scripts/docs_test.ts scripts/clean_architecture_test.ts scripts/commit_msg_test.ts` | 0 | All four files passed. |
| `rg -n '\bDeno\b|@std/fs' scripts/wiki_raw_import_test.ts scripts/docs_test.ts scripts/clean_architecture_test.ts scripts/commit_msg_test.ts` | 1 | No matches. |
| `git diff --check -- scripts/wiki_raw_import_test.ts scripts/docs_test.ts scripts/clean_architecture_test.ts scripts/commit_msg_test.ts` | 0 | No whitespace errors. |
| `npm run workflow -- --task CHE-32-T010 --graph impact --file scripts/wiki_raw_import_test.ts` | 0 | Policy passed. |
| `npm run workflow -- --task CHE-32-T010 --graph impact --file scripts/docs_test.ts` | 0 | Rechecked after the type-safe stub change; policy passed. |
| `npm run workflow -- --task CHE-32-T010 --graph impact --file scripts/clean_architecture_test.ts` | 0 | Policy passed after T009a's package-config update. |
| `npm run workflow -- --task CHE-32-T010 --graph impact --file scripts/commit_msg_test.ts` | 0 | Policy passed. |
| `npm run workflow -- --task CHE-32-T010 --graph policy` | 0 | No import-policy violations. |
| `npm run workflow -- --task CHE-32-T010` | 0 | Loaded current task instructions after the report was added; combined verification remains deferred until all workers finish. |
| `deno task workflow` | 0 | Loaded current workflow instructions; it reported the prior combined `npm run check` failure described above. |
| `npm run check` (recorded by workflow run `91beb6b6-bccc-4add-aa95-70fb7a6e63da`) | 1 | Failed only at `//:docs:check` because `docs/reference/commands.md` is stale; T009b owns regeneration. |

Earlier attempts were rerun after fixes: the first `npm run test:wiki-raw-import` exited 1 with 42/43 passing because a local variable shadowed the Node `symlink` import; the first `npm run test:docs` exited 1 because the fixture passed Deno's symlink options object to Node; the first `npm run test:clean-architecture` exited 1 with 1/4 passing before T009a's package-manifest scan landed; and the first listed `npx tsc` command exited 2 because the generic Node `readFile` stub type was too broad. The final runs above passed after these fixes and T009a's D18 update.

`npm run verify` was not run because the repository workflow defers combined verification until all workers finish.

The read-only ponytail complexity check of these four owned file diffs found no complexity-only cuts; it does not replace the coordinator's review.
