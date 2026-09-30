# Review CR2: the TypeScript test suites

Scope: `git diff 8ce9b2a 9d8af61` for every `scripts/*_test.ts`,
`scripts/cli_contract_test.ts.snapshot`, the deleted
`scripts/__snapshots__/cli_contract_test.ts.snap`, and
`plugins/code/skills/clean-code/scripts/clean_code_test.ts`. Each converted
test was compared with its version on `develop` (8ce9b2a). Reviewer: Claude
Code (Opus 5.5), read-only; this file is the only one written.

## Summary

All 16 test files keep the same number of test registrations as on
`develop`, all 12 suites pass, and the type check and Biome lint pass. Most
conversions are faithful: `Deno.test` became `node:test`, `Deno.Command`
became `spawnSync`/`spawn` with the parent environment merged in (as Deno
did by default), and the snapshot moved to Node's adjacent `.snapshot` file
with the same text except the removed `--deno` option. Four checks are
weaker than on `develop` without a requirement or decision that covers the
loss; they are listed first.

## Findings

### F1 (should-fix): changes to the new task-graph files no longer force review mode

- Evidence: `scripts/workflow.ts:29` dropped `deno\.jsonc?|deno\.lock` from
  the review-signal pattern but added none of the files that replace
  `deno.json` as the task graph and lock (`turbo.json`, root
  `pyproject.toml`, `uv.lock`). The test list in
  `scripts/workflow_test.ts:81-85` now names `package.json` twice (lines 83
  and 85) where `develop` listed `deno.jsonc`, `deno.lock` and
  `package.json` (`git show 8ce9b2a:scripts/workflow_test.ts`, lines
  71-74).
- Command: `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON
  --input-type=module -e "import {selectWorkMode} from
  './scripts/workflow.ts'; ..."` printed `turbo.json DIRECT`,
  `uv.lock DIRECT`, `pyproject.toml DIRECT`, `package.json REVIEW` (exit 0).
- Effect: on `develop` an edit to the task graph (`deno.json`) selected
  REVIEW; on the branch an edit to `turbo.json` or `uv.lock` selects DIRECT.
- Resolution: add `turbo\.json`, `pyproject\.toml` and `uv\.lock` to the
  pattern, and replace the duplicate `package.json` in the test with those
  files.

### F2 (should-fix): the commit-msg tests replace the script the hook runs

- Evidence: `scripts/commit_msg_test.ts:192-196` rewrites the fixture's
  `scripts.commitlint` to
  `NODE_OPTIONS='--disable-warning=MODULE_TYPELESS_PACKAGE_JSON' commitlint
  ...`. The real script in `package.json` is
  `NODE_OPTIONS='--disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission
  --allow-fs-read=* --allow-child-process' commitlint ...`, and
  `scripts/git-hooks/commit-msg:19` runs it through `npm run commitlint`. On
  `develop` the fixture copied `deno.json` unchanged, so the hook tests ran
  the real `commitlint` task.
- Reproduction (scratch fixture outside the repository, with the real
  `package.json`, hook and `node_modules` link): `git commit -m "docs:
  update a"` exited 0 and `git commit -m "Update files"` exited 1 with the
  commitlint errors, so the real script works; but every commit printed
  `SecurityWarning: The flag --allow-child-process must be used with extreme
  caution` to the terminal.
- Effect: the permission flags of the real script are untested, and the
  warning users see on each commit is hidden from the tests.
- Resolution: run the real script in the fixture. If the warning is
  unwanted, add `--disable-warning=SecurityWarning` to that script's
  `NODE_OPTIONS` (the warning comes from the commitlint process itself, which
  reads `NODE_OPTIONS`).

### F3 (should-fix): the doctor no longer pins the runtime version the tools need

- Evidence: `develop` asserted the exact runtime version
  (`git show 8ce9b2a:scripts/doctor_test.ts`, line 111:
  `assertEquals(report.deno.version, '2.9.6')`, and line 251 for a wrong
  version). The branch asserts only `report.node.version >= 22`
  (`scripts/doctor_test.ts:133`) and `runtime.version === process.version`
  (`scripts/doctor_test.ts:115`), which holds for any Node.js that runs the
  test. `scripts/doctor.ts:199` and `scripts/git-hooks/commit-msg:15` accept
  Node.js 22 or later.
- The tools need more than Node.js 22: `RegExp.escape`, used at
  `scripts/clean_architecture.ts:26`, `scripts/workflow_graph.ts:78` and
  `scripts/workflow_plan.ts:68`, arrived in Node.js 24. The workflows pin
  24.19.0 (`.github/workflows/docs-check.yml:24`,
  `.github/workflows/audit.yml:26`), and the root `package.json` has no
  `engines` field. So the doctor reports PASS on a Node.js 22 install where
  the checks crash.
- Resolution: have the doctor require the version the repository is tested
  with (24.19.0, or at least 24), and assert that version in the test, as
  `develop` did for Deno.

### F4 (should-fix): "help cannot use network" is no longer enforced or tested

- Evidence: the `develop` test queried the `net` permission
  (`git show 8ce9b2a:scripts/docs_test.ts`, line 264). The branch test
  checks only `fs.write`, `child` and one read path, but its name still
  says "cannot write, spawn, use network"
  (`scripts/docs_test.ts:350`). `node --help | grep allow-` on Node.js
  24.19.0 lists no network flag, so help commands started by
  `scripts/docs.ts` can reach the network. The report's Permissions item
  (`specs/019-turborepo/report.md:175-180`) lists the lost environment and
  program scopes but not the lost network restriction.
- Resolution: rename the test to what it checks, and add the lost network
  restriction to the report's Permissions item so the user can decide on
  it.

### F5 (note): Biome no longer denies `Deno` in domain code

- Evidence: `biome.json` lost `"Deno"` from `deniedGlobals` (was line 51 on
  `develop`; `Bun` remains at `biome.json:49`). The deletion was selected by
  the user rule (`X140` in
  `specs/019-turborepo/evidence/selected-sites-full-removal.md:43`), and the
  domain test now uses only `process` variants
  (`scripts/clean_architecture_test.ts:163-170`), where `develop` checked four
  `Deno` forms (`git show 8ce9b2a:scripts/clean_architecture_test.ts`,
  lines 139-152).
- Effect: domain code can call `Deno.*` again without a lint error. Denying
  a global does not require or invoke Deno, so FR-011 does not need this
  deletion.
- Resolution: ask the user whether to keep `Deno` in `deniedGlobals`, as
  `Bun` is kept; if yes, restore one `Deno` case in the test.

### F6 (note): FR-007 names Turborepo, but the doctor has no Turborepo check

- Evidence: `grep -n -i turbo scripts/doctor.ts` finds nothing (exit 1).
  Turborepo is covered only as one package of the root npm lock check
  (`report.rootNpm`, `scripts/doctor_test.ts:155-159`). No test covers a
  missing or wrong `turbo` binary.
- Resolution: either record that the root npm lock check is the Turborepo
  check, or add a `turbo --version` probe with its repair command.

### F7 (note): the copied clean-code skill test is less strict than on `develop`

- Evidence: `scripts/cli_contract_test.ts:210-233` copies the whole skill
  directory, installs with `npm ci --prefer-offline` (network allowed), and
  runs the checker without the permission model. `develop` copied only the
  four runtime files, ran with `--cached-only`, and granted only
  `--allow-read --allow-env` (`git show 8ce9b2a:scripts/cli_contract_test.ts`,
  lines 205-225). The new form matches D16 and
  `plugins/code/skills/clean-code/SKILL.md:36-37`.
- Resolution: optional; use `--offline` in the test to keep it network-free,
  and add `--permission --allow-fs-read=*` to the run to keep the proof that
  the checker needs no write or process access.

### F8 (note): narrower child permissions were dropped in several tests

- Evidence: the constitution Git-error probe
  (`scripts/commit_msg_test.ts:126-140`; `develop` used
  `--allow-read --allow-env=PATH --allow-run=git`), the verification fixture
  check (`scripts/workflow_verify_test.ts`, the `check` script; `develop`
  used `deno run --allow-read --allow-write`), and the workflow CLI runs
  (`scripts/workflow_skills_test.ts:272-283`,
  `scripts/workflow_graph_test.ts:76-95`; `develop` used
  `--allow-run=git,<deno>`) now run with no permission model or with
  `--allow-child-process`. D4 leaves dropping these scopes to the user, and
  the report lists it.
- Resolution: none needed beyond the user's D4 decision.

### F9 (note): a killed or timed-out child counts as exit code 1

- Evidence: every command helper maps a missing status to 1
  (`scripts/cli_contract_test.ts:36`, `scripts/doctor_test.ts:38`,
  `scripts/docs_test.ts:70`, `scripts/wiki_raw_import_test.ts:58`, and five
  more). `scripts/wiki_raw_import_test.ts:148` kills a child after 30
  seconds, which then resolves with code 1; `develop` used
  `AbortSignal.timeout(30_000)`, which made `output()` reject. Checks such as
  `code !== 0` (`scripts/wiki_raw_import_test.ts:978`, `:1150`) would pass
  for a hung child.
- Resolution: fail the helper when `signal` is set, instead of mapping it to
  1.

### F10 (note): local code where the runtime or a shared helper would do

- Evidence: six test files define the same 15-line `commandOutput` wrapper
  that rebuilds Deno's `CommandOutput` shape (`scripts/cli_contract_test.ts:23`,
  `scripts/clean_architecture_test.ts:11`, `scripts/commit_msg_test.ts:32`,
  `scripts/docs_test.ts:59`, `scripts/doctor_test.ts:27`,
  `scripts/git_flow_test.ts:40`). `scripts/docs_test.ts:77` adds
  `stubBuiltin` with hand-written `restore()` calls in `try`/`finally`, where
  `node:test`'s `t.mock.method` records calls and restores at the end of the
  test by itself (`syncBuiltinESMExports()` is still needed).
- Resolution: optional; use `t.mock.method` in `docs_test.ts`, and either
  read `spawnSync` results directly or move the wrapper to one shared test
  helper.

### F11 (note): smaller coverage and naming changes

- `scripts/doctor_test.ts:108`: the `develop` test ran the doctor through
  the root task (`deno task doctor`); the new one runs `scripts/doctor.ts`
  directly. `npm run doctor` is exercised only with `--help`
  (`scripts/cli_contract_test.ts:133`).
- `scripts/doctor_test.ts:401`: the test is still named "doc-regions
  environment" but now checks the root uv workspace (`--all-packages`).
- `scripts/cli_contract_test.ts:112` copies the real root `package.json`
  into the fixture, where `develop` wrote `{}`. Only
  `scripts/clean_architecture.ts:64` reads it, and the fixture has no
  imports, so `{}` should be enough (not run).
- `scripts/clean_architecture_test.ts:144-162`: the `scopes` test was
  replaced by a test of the existing "Public exports must stay inside" check;
  this follows the removal of the `deno.json`-only `scopes`/`importMap` guard
  and D18. No action needed.

## Commands run

| Command | Exit |
| --- | --- |
| `git diff --stat 8ce9b2a 9d8af61 -- <scope>` | 0 |
| `git diff 8ce9b2a 9d8af61 -- <each test file>` | 0 |
| Per-file count of test registrations and assertions on both commits (`git show ... \| grep -c`) | 0 |
| `npm run test:plugin-skills` | 0 |
| `npm run test:doctor` | 0 |
| `npm run test:ruff` | 0 |
| `npm run test:git-flow` | 0 |
| `npm run test:worktree-branch` | 0 |
| `npm run test:commit-msg` | 0 |
| `npm run test:cli-contract` | 0 |
| `npm run test:workflow` (five workflow test files) | 0 |
| `npm run test:clean-code` | 0 |
| `npm run test:clean-architecture` | 0 |
| `npm run test:docs` | 0 |
| `npm run test:wiki-raw-import` | 0 |
| `npm run typecheck` | 0 |
| `./node_modules/.bin/biome lint scripts/*_test.ts plugins/code/skills/clean-code/scripts/clean_code_test.ts` | 0 |
| `selectWorkMode` probe for `turbo.json`, `uv.lock`, `pyproject.toml`, `package.json`, `deno.json` (F1) | 0 |
| Commit-hook reproduction in a scratch fixture: valid message / invalid message (F2) | 0 / 1 |
| `node --help \| grep allow-` on v24.19.0 (F4) | 0 |
| `grep -n -i turbo scripts/doctor.ts` (F6) | 1 |
| `git status --porcelain` after all runs (empty) | 0 |
