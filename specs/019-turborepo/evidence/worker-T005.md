# T005 worker report

Assumption: the snapshot file stays unchanged because none of these seven test files call `assertSnapshot`.

## Changes

- `scripts/wiki_raw_import_test.ts` — selected sites `R:scripts/wiki_raw_import_test.ts:72`, `S043`, and `S073`.
- `scripts/workflow_graph_test.ts` — `S041`, `S056`, `S063`, `S107`, and `S159`.
- `scripts/workflow_plan_test.ts` — `S038`, `S064`, and `S156`.
- `scripts/workflow_skills_test.ts` — `S032`, `S052`, `S060`, `S116`, and `S144`.
- `scripts/workflow_test.ts` — `S033`, `S061`, and `S132`.
- `scripts/workflow_verify_test.ts` — `S037`, `S072`, `S119`, and `S163`.
- `scripts/worktree_branch_test.ts` — `S046` and `S071`.

Each selected Deno test registration now uses `node:test`. Selected child commands use `node:child_process`; repository TypeScript commands use Node with `scripts/deno_shim.ts`. Deno file, environment, and error APIs remain. The wiki fixture constructor now uses an erasable `home` field and assignment.

The nested plugin Deno-config fixtures under `S159` in the graph tests and `S156` in the plan tests remain unchanged. They cover nested plugin manifests still read by the current T003 code; root fixture configurations were changed to `package.json` where the code under test reads the root package. The leave/review `S154` sites in `scripts/workflow_test.ts` remain unchanged. No snapshot file was changed.

## Test counts and results

Base counts below are the requested number of textual `Deno.test(` registrations in `git show HEAD:<file>`. Node counts are from the test runner output.

| File | Base registrations | Node tests | Result |
| --- | ---: | ---: | --- |
| `scripts/wiki_raw_import_test.ts` | 26 | 43 | 43 passed |
| `scripts/workflow_graph_test.ts` | 9 | 9 | Included in workflow group; external failures below |
| `scripts/workflow_plan_test.ts` | 10 | 10 | Included in workflow group; external failures below |
| `scripts/workflow_skills_test.ts` | 9 | 9 | Included in workflow group; external failures below |
| `scripts/workflow_test.ts` | 20 | 20 | Included in workflow group; external failures below |
| `scripts/workflow_verify_test.ts` | 8 | 8 | Included in workflow group; external failures below |
| `scripts/worktree_branch_test.ts` | 3 | 3 | 3 passed |

The wiki file's 26 textual registrations include table-driven registrations that expand to 43 runtime tests. After formatting, two consecutive runs each reported 43 passed. An earlier run of the same test reported one failure in `raw import US1: one immutable bag preserves payload, digest, timestamps and provenance`: actual `1790633882292`, expected `1790633882293` at the `Source-Modified` versus `mtime` assertion. The next two runs passed, so this appears to be an intermittent 1 ms timestamp precision difference; I left the expectation unchanged.

The five workflow files register 56 tests in total. After T003 fixed the hash conversion, the latest Node run reported 56 tests, 31 passed and 25 failed.

## External failures and open item

`npm run test:workflow` still fails in non-owned T003 code. `scripts/clean_architecture.ts:47` throws `Cannot parse package configuration: /tmp/workflow-.../package.json` for fixtures without a root package file. The graph test also gets `FAIL` instead of `PASS` for a `#validation` package import alias; T003's current package reader handles dependencies but not `package.json#imports`. The concurrent verification test gets `ELOCKED` (`Lock file is already being held`) at a temporary repository's `.git/workflow/lock`, in the code path changed by T003's `scripts/workflow_verify.ts`. The hash conversion error at `scripts/hash.ts:6` no longer occurs after T003's fix. These files are outside T005 ownership and were not changed. The `S154` fixture sites are explicitly left/review sites, so I left them intact; T003 must preserve their behavior without changing those sites.

The latest root `npm run format:check` reports four remaining formatting errors in T004-owned files: `scripts/clean_architecture_test.ts`, `scripts/cli_contract_test.ts`, `scripts/commit_msg_test.ts`, and `scripts/docs_test.ts`. The scoped Biome check on all seven T005 tests passes; I left the T004 files unchanged.

No T005-owned unselected site needs a change. The shared worktree has edits from other workers: full `git diff --stat` showed 52 tracked files, while the scoped T005 test diff showed only the seven owned tests. The report is the only additional T005 file.

## Commands and exit codes

- `$HOME/.deno/bin/deno task workflow` before edits — exit 1; the then-current workflow command failed with `Deno.Command is not a constructor`.
- `npm run test:wiki-raw-import` after formatting — two runs, both exit 0; 43 passed each.
- `npm run test:wiki-raw-import` — one earlier exit 1; 42 passed, 1 failed on the 1 ms timestamp mismatch above.
- `npm run test:workflow` — latest exit 1; 56 total, 31 passed, 25 failed for the T003 causes above.
- `npm run test:worktree-branch` — exit 0; 3 passed.
- `npm run typecheck` — exit 0.
- `node_modules/.bin/biome format --write scripts/wiki_raw_import_test.ts` — exit 0; formatted only the owned file.
- `node_modules/.bin/biome format scripts/wiki_raw_import_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/workflow_skills_test.ts scripts/workflow_test.ts scripts/workflow_verify_test.ts scripts/worktree_branch_test.ts` — exit 0; all seven owned tests are formatted.
- `npm run format:check` — exit 1; four remaining errors are in T004 files listed above.
- `$HOME/.deno/bin/deno task workflow` before completion — exit 0; it printed the T001 workspace warning that `tools/none` was not found and skipped. The latest instructions say the main agent owns the verify replan.
- `$HOME/.deno/bin/deno task verify` — two runs, both exit 1. The first `npm run check` failed at `//#test:doctor`; the second failed at `//#format:check`, initially including the two T005 formatting diffs that were then fixed. The second log is `/home/choi-eunchang/workspaces/verbose-broccoli/develop/.git/worktrees/feature-turborepo/workflow/32237e9f-1144-4ba9-af47-acb4366d2c9b.log`. Per coordinator direction, verify was not run again after the scoped fix.
- `git diff --check -- scripts/wiki_raw_import_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/workflow_skills_test.ts scripts/workflow_test.ts scripts/workflow_verify_test.ts scripts/worktree_branch_test.ts` — exit 0.
- `rg -n 'Deno\.(test|Command|CommandOutput)\b|Deno\.execPath\(\)' scripts/wiki_raw_import_test.ts scripts/workflow_graph_test.ts scripts/workflow_plan_test.ts scripts/workflow_skills_test.ts scripts/workflow_test.ts scripts/workflow_verify_test.ts scripts/worktree_branch_test.ts` — exit 1, no matches.
- `$HOME/.deno/bin/deno fmt --check scripts/wiki_raw_import_test.ts` — exit 1; direct Deno formatting uses defaults that differ across the file, so this was not the repository formatter and no file was changed by it.

## T005b follow-up: Source-Modified precision

### Changes

- `scripts/wiki_raw_import_test.ts` — selected site `F:check:wiki_raw_import_test.ts:303-307` (`must_change`, auto, 0.96). Added the `node:fs/promises` `stat` import and compares `Source-Modified` milliseconds with `mtimeNs` truncated to milliseconds. This is the only selected site in this task; it was changed. No unselected site in this task appears to require a change.
- `specs/019-turborepo/evidence/worker-T005.md` — this addendum; no code site.

### Verification

| Command | Run | Result |
| --- | ---: | --- |
| `npm run test:wiki-raw-import` | 1 | exit 0; 43 tests, 43 passed, 0 failed |
| `npm run test:wiki-raw-import` | 2 | exit 0; 43 tests, 43 passed, 0 failed |
| `npm run test:wiki-raw-import` | 3 | exit 0; 43 tests, 43 passed, 0 failed |
| `npm run test:wiki-raw-import` | 4 | exit 0; 43 tests, 43 passed, 0 failed |
| `npm run test:wiki-raw-import` | 5 | exit 0; 43 tests, 43 passed, 0 failed |
| `npm run format:check` | 1 | exit 0 |
| `npm run workflow -- --task CHE-32-T005b --graph impact --file scripts/wiki_raw_import_test.ts` | before and after edit | exit 0 both times |
| `npm run workflow -- --task CHE-32-T005b` | final workflow | exit 0; it reports REVIEW mode and the prior verify failure in REPAIR |
| `npm run verify -- --task CHE-32-T005b` | 1 | exit 1; combined `npm run check` failed at `//#test:doctor` |
| `git diff --check -- scripts/wiki_raw_import_test.ts specs/019-turborepo/evidence/worker-T005.md` | 1 | exit 0 |

The verify log is `/home/choi-eunchang/workspaces/verbose-broccoli/develop/.git/worktrees/feature-turborepo/workflow/e1335fc5-c56f-4a7c-8192-58634a8f9343.log`. It shows `test_prepare_requests_exclude_configuration_state_and_credentials` failing in `packages/wiki-consistency/tests/test_boundary.py:8` after `qmd --index work collection add ... --name pages` returned exit 1; other tasks were interrupted during shutdown. That failure is outside this task's two-file ownership, and its cause was not established here.
