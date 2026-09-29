# CHE-32 task F1 worker report

Assumption: the acceptance list in the task brief is the completion target; `npm run verify` remains excluded as directed.

## Files changed

| File | Rows |
| --- | --- |
| `package.json` | V01, V07 |
| `turbo.json` | V05 |
| `scripts/doctor.ts` | V05, V24, V26 |
| `scripts/doctor_test.ts` | V05, V24, V26, V13 |
| `scripts/git-hooks/commit-msg` | V05, V07 |
| `scripts/commit_msg_test.ts` | V05, V07, V13 |
| `scripts/cli_contract_test.ts` | V01, V13 |
| `scripts/git_flow_test.ts` | V13 |
| `scripts/worktree_branch_test.ts` | V13 |
| `docs/reference/commands.md` | V05 |
| `specs/019-turborepo/evidence/worker-F1.md` | V01, V05, V24, V26, V07, V13 |

`package.json` now syncs every Python workspace package during `backfire:install`; `orca.yaml` already runs that same `uv sync` command. The doctor requires Node.js 24.12.0, reports root direct npm dependencies by locked version, and checks the root Turbo executable against the lock. The hook and `commitlint` script suppress `SecurityWarning`; signal-terminated test children now throw instead of becoming exit code 1. I regenerated the command reference. The doctor help text did not change, so the CLI snapshot stayed untouched.

The `commitlint` script option alone could not silence the warning from `npm`: Node propagated `--permission --allow-child-process` to children through `NODE_OPTIONS`, and npm starts before it runs the package script. With the hook setting the warning option for npm, removing the package-script option still made the commit test fail, so both settings remain. The coordinator approved changing the hook's npm invocation for this reason.

## Red checks observed before fixes

- V01: the install-script contract test failed with the old `uv sync --project packages/backfire --frozen --extra education` command instead of the all-packages command.
- V05 Node floor: the doctor test failed because fake Node v24.11.1 was accepted. V05 hook message: the commit test expected the 24.12.0 message but received the old Node 22 message.
- V24: the doctor test showed every `node_modules/...` lock entry where it expected only the root package's direct `dependencies` and `devDependencies`.
- V26: the root Turbo check failed because `report.turbo` was undefined before the probe was added.
- V07: the real commit fixture printed `SecurityWarning`. After adding the hook-level setting, temporarily removing the package-script setting made the same test fail again, showing that the commitlint child also needs the option.
- V13: each of the five new signal checks failed before its guard. The four synchronous helpers reported “Expected function to throw”; the worktree helper reported “Expected function to reject.”

## Commands and exit codes

Red checks before the corresponding fixes:

```text
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --test --test-name-pattern='backfire install|CLI test commands reject' scripts/cli_contract_test.ts — 1
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --test --test-name-pattern='installed identities|Node must' scripts/doctor_test.ts — 1
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --test --test-name-pattern='installed root Turborepo' scripts/doctor_test.ts — 1
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --test --test-name-pattern='commit-msg test commands reject|real commits' scripts/commit_msg_test.ts — 1
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --test --test-name-pattern='git-flow test commands reject' scripts/git_flow_test.ts — 1
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=/tmp --allow-child-process --test --test-name-pattern='test runner rejects' scripts/worktree_branch_test.ts — 1
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --test --test-name-pattern='real commits' scripts/commit_msg_test.ts — 1 (with the old hook message; the assertion showed Node 22 instead of Node 24.12.0)
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --test --test-name-pattern='real commits' scripts/commit_msg_test.ts — 1 (with the package-script warning option temporarily removed; commit output contained SecurityWarning)
```

Final verification:

```text
npm run workflow — 0 (before edits)
npm run workflow -- --task CHE-32-F1 --base 9d8af61 --graph impact --file scripts/doctor.ts — 0 (before and after edits)
npm run backfire:install — 0
uv sync --locked --check --all-packages --extra education --offline — 0
npm run docs:generate — 0
node_modules/.bin/biome format --write scripts/cli_contract_test.ts scripts/doctor.ts — 0
node_modules/.bin/biome check package.json turbo.json scripts/doctor.ts scripts/doctor_test.ts scripts/git-hooks/commit-msg scripts/commit_msg_test.ts scripts/cli_contract_test.ts scripts/git_flow_test.ts scripts/worktree_branch_test.ts — 0
npm run test:doctor — 0 (20 passed)
npm run test:commit-msg — 0 (6 passed)
npm run test:cli-contract — 0 (16 passed)
npm run test:git-flow — 0 (21 passed)
npm run test:worktree-branch — 0 (4 passed)
npm run doctor — 0
npm run docs:check — 0
npm run typecheck — 0
git diff --check -- package.json turbo.json scripts/doctor.ts scripts/doctor_test.ts scripts/git-hooks/commit-msg scripts/commit_msg_test.ts scripts/cli_contract_test.ts scripts/git_flow_test.ts scripts/worktree_branch_test.ts docs/reference/commands.md — 0
```

`npm run verify` was not run, as the task explicitly prohibits it. Read-only Ponytail complexity review: Lean already. Ship.
