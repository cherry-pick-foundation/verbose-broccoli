# CHE-32 T004 worker report

## Result

Migrated the selected registrations and subprocess sites in the seven owned test files to `node:test` and `node:child_process`. Test order is preserved; the CLI snapshot stays unchanged through a Node-compatible `{name, origin}` context, and the coordinator-approved doctor Python test rename reflects its new root-workspace behavior. Four npm suites pass, while three do not meet the requested npm-script acceptance; details follow.

## Files and selected sites

| File | Selected sites handled |
| --- | --- |
| `scripts/clean_architecture_test.ts` | `S042`, `S055`, `S065`, `S105`, `S147` |
| `scripts/cli_contract_test.ts` | `S031`, `S050`, `S068`, `S161` |
| `scripts/commit_msg_test.ts` | `F:T004:commit_msg_test.ts:539-552`, `S035`, `S054`, `S067`, `S162` |
| `scripts/docs_test.ts` | `F:T004:docs_test.ts:686-689`, `R:scripts/docs_test.ts:87`, `S034`, `S053`, `S062`, `S120`, `S145` |
| `scripts/doctor_test.ts` | `F:T004:doctor_test.ts:100-110`, `:182-195`, `:385-397`, `:398-410`, `:474-476`, `:477-491`, `S045`, `S049`, `S069`, `S106`, `S115`, `S160`, `S181`, `S191` |
| `scripts/git_flow_test.ts` | `S040`, `S066`, `S092`, `S158` |
| `scripts/plugin_skills_test.ts` | `S047`, `S070` |

`S049` in `doctor_test.ts` intentionally retains `Deno.execPath()` because it supplies the actual Deno executable for Deno runtime and identity fixtures. The CLI's shipped clean-code route also stays on Deno as directed. Deno filesystem, environment, and error APIs remain on the preload shim. The `cli_contract_test.ts` snapshot was not changed; `scripts/wiki_raw_import_test.ts` and its D2 row are outside this task's ownership.

The coordinator-approved Biome formatting pass touched two `leave` sites only as formatter reflows: `S002` at the `Deno.copyFile` fixture copy in `commit_msg_test.ts`, and `S007` at the `Deno.readTextFile` task-config assertion in `docs_test.ts`. A TypeScript syntax-token comparison against pre-format copies found no changes except trailing comma additions/removals and no other token mismatches. The coordinator accepted those formatter-only comma changes. No selected site was otherwise omitted.

## Test counts and blockers

Base source registration counts were read from `git show HEAD:<file>` with `rg -c 'Deno\.test\('`. Node's runtime test count matches for each suite except that the CLI file has six source registration sites and expands its loop to 14 runtime cases.

| Suite | Base Deno registrations | Node runtime result |
| --- | ---: | ---: |
| clean architecture | 4 | 4 passed |
| CLI contract | 6 | 14 total; 2 passed, 12 failed |
| commit message | 5 | 5 passed |
| docs | 14 | 14 total; 0 passed, 14 failed |
| doctor | 16 | 16 passed |
| git flow | 20 | npm entry point stopped before tests; direct Node invocation passed 20 |
| plugin skills | 3 | 3 passed |

`npm run test:cli-contract` fails because invoked CLI routes write Node's `SecurityWarning` to stderr, violating the existing empty-stderr checks and prefixing JSON expected by error assertions. The warning says: `SecurityWarning: The flag --allow-child-process must be used with extreme caution. It could invalidate the permission model.` For example, `npm run --silent doctor -- --help` exits 0 but emits that warning on stderr. `package.json` is outside this worker's ownership.

`npm run test:docs` fails all 14 cases at the shared help-collection step with: `scripts/doctor.ts: Help collection failed (exit 1, stderr 991 bytes). Run npm run docs:generate.` The failing implementation is in T003-owned `scripts/docs.ts`, which this worker could not change.

`npm run test:git-flow` exits before running tests with `Could not find 'scripts/git_flow_test.ts'`. In `package.json`, replace this script command:

```text
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=node_modules --allow-fs-read=scripts --allow-fs-read=plugins --allow-fs-read=.gitflow --allow-fs-read=package.json --allow-fs-read=package-lock.json --allow-fs-read=turbo.json --allow-fs-read=tsconfig.json --allow-fs-write=/tmp --allow-child-process --import ./scripts/deno_shim.ts --test scripts/git_flow_test.ts
```

with the validated direct command:

```text
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --import ./scripts/deno_shim.ts --test scripts/git_flow_test.ts
```

The equivalent direct Node command passed all 20 tests; the package script belongs to T001. No unselected code site in the owned files is known to require a behavior change.

## Commands and results

- `npm run workflow -- --task T004 --graph impact --file scripts/doctor_test.ts` — exit 0.
- `npm run workflow -- --task T004 --graph impact --file scripts/docs_test.ts` — exit 0.
- `$HOME/.deno/bin/deno task workflow` — exit 0; printed the repository's `REVIEW` guidance for the combined worktree.
- `npm run test:clean-architecture` — exit 0, 4/4 passed.
- `npm run test:cli-contract` — exit 1, 2/14 passed; stderr/JSON failures described above.
- `npm run test:commit-msg` — exit 0, 5/5 passed.
- `npm run test:docs` — exit 1, 0/14 passed; all stop at the 991-byte doctor help-collection error above.
- `npm run test:doctor` — exit 0, 16/16 passed.
- `npm run test:git-flow` — exit 1 before test discovery; `Could not find 'scripts/git_flow_test.ts'`.
- `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --import ./scripts/deno_shim.ts --test scripts/git_flow_test.ts` — exit 0, 20/20 passed.
- `npm run test:plugin-skills` — exit 0, 3/3 passed.
- `./node_modules/.bin/biome format --write scripts/clean_architecture_test.ts scripts/cli_contract_test.ts scripts/commit_msg_test.ts scripts/docs_test.ts` — exit 0; coordinator-approved formatting only.
- `npm run format:check` — exit 0; Biome checked 60 files and Prettier passed.
- `rg -n 'Deno\.(test|Command|CommandOutput)\b' scripts/clean_architecture_test.ts scripts/cli_contract_test.ts scripts/commit_msg_test.ts scripts/docs_test.ts scripts/doctor_test.ts scripts/git_flow_test.ts scripts/plugin_skills_test.ts` — exit 1, no matches.
- `git diff --check -- scripts/clean_architecture_test.ts scripts/cli_contract_test.ts scripts/commit_msg_test.ts scripts/docs_test.ts scripts/doctor_test.ts scripts/git_flow_test.ts scripts/plugin_skills_test.ts` — exit 0.
- `git diff --stat -- scripts/clean_architecture_test.ts scripts/cli_contract_test.ts scripts/commit_msg_test.ts scripts/docs_test.ts scripts/doctor_test.ts scripts/git_flow_test.ts scripts/plugin_skills_test.ts` — exit 0; only the seven owned test files appear in the tracked diff. `git status --short` for the owned paths also shows the new report and no snapshot change.
- `git diff --quiet HEAD -- scripts/__snapshots__/cli_contract_test.ts.snap` — exit 0, snapshot unchanged.
- `$HOME/.deno/bin/deno task verify` — exit 1 before the formatting pass; it reported `CHECK_FAILED`, with `//#format:check` failing on the four owned files now fixed above. The coordinator owns the verification loop and directed this worker not to rerun it. The recorded log is `/home/choi-eunchang/workspaces/verbose-broccoli/develop/.git/worktrees/feature-turborepo/workflow/ae536a9d-99e7-4416-b36a-3a58dc617c87.log`.

The remaining acceptance work is in T001's npm script configuration and T003's docs help route, plus the CLI stderr handling. No files outside this task's ownership were edited by this worker.

## T004b addendum

Assumption: `node:test` writes string snapshots in a different on-disk encoding from Deno, so I compared the decoded help strings. The coordinator approved keeping Node's workflow-help output as generated, without normalizing the test input or editing `scripts/workflow.ts`.

### Files and selected sites

| File | Selected sites handled |
| --- | --- |
| `scripts/cli_contract_test.ts` | `R:scripts/cli_contract_test.ts:2`, `R:scripts/cli_contract_test.ts:132` — use `t.assert.snapshot(text)` and remove the old snapshot imports/context adapter. |
| `scripts/__snapshots__/cli_contract_test.ts.snap` | `W:scripts/__snapshots__/cli_contract_test.ts.snap` — deleted after comparison. |
| `scripts/cli_contract_test.ts.snapshot` | Node's adjacent default snapshot file, generated by `node:test`. |
| `scripts/docs_test.ts` | `R:scripts/docs_test.ts:87` — use `Buffer.from(bytes).toString('hex')`; `F:T003c:docs_test.ts:258-270` — check `process.permission.has` for write, child process, and the protected read path. |
| `specs/019-turborepo/evidence/worker-T004.md` | This addendum. |

No selected site from this follow-up was left unchanged. Node 24.19 has no network permission check, so the permission fixture no longer tests network access; its existing test title remains unchanged. `scripts/workflow.ts:405` is unselected and unchanged. Node renders its `workspace` and `HEAD` defaults with single quotes, and the coordinator approved that one runtime-specific snapshot difference.

Ponytail review of these follow-up edits: Lean already; net: 0 lines possible.

### Snapshot comparison

I evaluated the original Deno snapshot map from `git show HEAD:scripts/__snapshots__/cli_contract_test.ts.snap` and the generated Node map in a local Node VM. I decoded Deno's multiline quoted string representation and Node's JSON-escaped string representation, then compared the underlying UTF-8 help texts byte for byte. Four of five texts were identical; the workflow text was 949 bytes in both files and differed only in the quote delimiters around the two defaults, with all remaining bytes equal.

| Original Deno help line | Generated Node help line |
| --- | --- |
| `--task      <id>      - Task identity for the evidence loop.       (Default: "workspace")` | `--task      <id>      - Task identity for the evidence loop.       (Default: 'workspace')` |
| `--base      <ref>     - Baseline Git commit or reference.          (Default: "HEAD")` | `--base      <ref>     - Baseline Git commit or reference.          (Default: 'HEAD')` |

The other four snapshot values (`doctor`, `clean-architecture`, `plugins:validate`, and `clean-code`) were byte-identical. The generated file has five entries.

### Counts and remaining docs failures

| Suite | Base `Deno.test(` registrations | Node result |
| --- | ---: | ---: |
| CLI contract | 6 (the loop expands to 14 cases) | 14/14 passed twice without updating snapshots |
| Docs | 14 | 12/14 passed |

The two remaining docs failures were outside the two newly selected test sites. `references: invalid manifests, tasks and duplicate identities retain the previous pair` failed at `scripts/docs_test.ts:258` with `Expected function to reject` on the first accepted invalid task fixture, `turbo.json` containing `{"tasks":{"invalid":{}}}`. The unowned `scripts/docs.ts:310-318` schema accepts that object because `description` is optional and unknown properties pass through; it was not changed. `references: local and PR check entrypoints agree without Node actions` failed at `scripts/docs_test.ts:700`: the fixture's `npm run docs:check` child could not read the real symlink target `node_modules/@deno/shim-deno/dist/index.mjs` and returned `ERR_ACCESS_DENIED`. The copied package script grants the lexical `node_modules` path, but Node resolves the symlink to the worktree's real path; `package.json` is T001-owned, so it was not changed.

### Commands and results

| Command | Result |
| --- | --- |
| `$HOME/.deno/bin/deno task workflow` | Exit 0 before and after the edits; shared worktree reports REVIEW. |
| `npm run workflow -- --task T004b --graph impact --file scripts/cli_contract_test.ts` | Exit 0 before and after the edits; import policy PASS. |
| `npm run workflow -- --task T004b --graph impact --file scripts/docs_test.ts` | Exit 0 before and after the edits; import policy PASS. |
| `npm run workflow -- --task T004b --graph policy` | Exit 0; policy PASS. |
| `npm run workflow -- --task T004b` | Exit 0; shared worktree reports REVIEW. |
| `npm run test:cli-contract -- --test-update-snapshots` | Exit 1; npm appends the flag after the test path, so Node did not enter update mode. |
| `env NODE_OPTIONS=--disable-warning=SecurityWarning node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --import ./scripts/deno_shim.ts --test --test-update-snapshots scripts/cli_contract_test.ts` | Exit 0; generated the adjacent Node snapshot, 14/14 passed. |
| `node` VM/JSON comparison of the original snapshot from `git show HEAD:...` and `scripts/cli_contract_test.ts.snapshot` | Exit 0; four texts byte-identical, workflow text differs only as described above. |
| `rm scripts/__snapshots__/cli_contract_test.ts.snap` | Exit 0. |
| `./node_modules/.bin/biome format --write scripts/cli_contract_test.ts scripts/docs_test.ts` | Exit 0; no fixes applied. |
| `npm run test:docs` | Exit 1; 12/14 passed, with the two failures described above. |
| `npm run test:cli-contract` | Exit 0 twice consecutively without update mode; 14/14 each run. |
| `npm run format:check` | Exit 0; Biome checked 60 files and Prettier passed. |
| `git diff --check -- scripts/cli_contract_test.ts scripts/docs_test.ts scripts/__snapshots__/cli_contract_test.ts.snap scripts/cli_contract_test.ts.snapshot specs/019-turborepo/evidence/worker-T004.md` | Exit 0. |
| `git diff --stat -- scripts/cli_contract_test.ts scripts/docs_test.ts scripts/__snapshots__/cli_contract_test.ts.snap scripts/cli_contract_test.ts.snapshot specs/019-turborepo/evidence/worker-T004.md` | Exit 0; tracked diff contains only owned test files; the new Node snapshot and report are untracked until the coordinator stages them. |

The base count check was `git show HEAD:scripts/cli_contract_test.ts | rg -c 'Deno\.test\(' && git show HEAD:scripts/docs_test.ts | rg -c 'Deno\.test\('` — exit 0, output `6` and `14`. The selected-call-site scan was `rg -n 'Deno\.(test|Command|CommandOutput)\b' scripts/cli_contract_test.ts scripts/docs_test.ts` — exit 1 with no matches. The one-off `node` VM/JSON snapshot comparison exited 0.

## T004c addendum

Assumption: `scripts/docs_test.ts`'s direct invalid-argument Node invocation is part of the already selected child-process migration site; it also needs the resolved `node_modules` read scope because the fixture symlinks that directory to the repository.

### Files and selected sites

| File | Selected sites handled |
| --- | --- |
| `scripts/docs_test.ts` | `S145` — replace the two Deno task fixtures with invalid Turbo task definitions (`description: 1` and a non-object task). `S034`/`S053` — add the repository's resolved `node_modules` path to the direct Node child used for the invalid-argument check; after the npm `docs:check` child passed with its new scope, this direct child exposed the same `ERR_ACCESS_DENIED` while loading the shim through the fixture symlink. |
| `package.json` | The translations of `deno.json#task:docs:generate` and `deno.json#task:docs:check` — add `--allow-fs-read="$(realpath node_modules)"` beside the lexical scope in each script. No other package entries changed. |
| `specs/019-turborepo/evidence/worker-T004.md` | This addendum. |

No selected site requested by T004c was left unchanged. No unselected site appears to require a change.

### Counts and commands

The base docs suite has 14 `Deno.test(` registrations; `npm run test:docs` passed 14/14 after the changes.

| Command | Result |
| --- | --- |
| `$HOME/.deno/bin/deno task workflow` | Exit 0; the combined worktree reports REVIEW. |
| `npm run workflow -- --task T004c --graph impact --file scripts/docs_test.ts` | Exit 0; import policy PASS after the edit. |
| `npm run workflow -- --task T004c` | Exit 0; the combined worktree reports REVIEW. |
| `npm run workflow -- --task T004c --graph impact --file package.json` | Exit 1; workflow does not support JSON files as graph inputs (`File is not a supported code file: package.json`). |
| `git show HEAD:scripts/docs_test.ts \| rg -c 'Deno\.test\('` | Exit 0; output `14`. |
| `npm run test:docs` | First exit 1, 13/14; after adding the resolved path to the direct Node child, exit 0, 14/14. |
| `npm run docs:check` | Exit 0; status `PASS`. |
| `npm run format:check` | Exit 0; Biome and Prettier passed. |
| `git diff --check -- scripts/docs_test.ts` | Exit 0. |
