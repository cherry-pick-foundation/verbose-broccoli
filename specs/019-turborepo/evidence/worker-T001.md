# CHE-32 T001 worker report

Assumption: the selected-site ledger is authoritative. I left every review or
leave site unchanged. The coordinator authorized the `Deno.exitCode` bridge in
the new preload, `proper-lockfile` 4.1.2 for T003's lock calls, and the npm Zod
build at 4.6.2 after the JSR source failed the requested type check.

## Changes and selected sites

| File | Selected site coverage |
| --- | --- |
| `package.json` | New root scripts replace all 42 selected `deno.json#task:*` sites; dependencies replace `deno.json#imports` and the YAML formatter from `deno.json#fmt`. The `packages/*` npm workspace glob lets Turbo run in multi-package mode alongside the uv workspace. |
| `package-lock.json` | New lock for the npm dependencies; replaces selected whole-file site `W:deno.lock`. |
| `.npmrc` | New JSR registry and remote-host setting for the aliases replacing `deno.json#imports`. |
| `turbo.json` | Root tasks for the selected `check` and `test` dependencies, Python member test commands, and the selected descriptions on `doctor` and `doc-regions:*`. The uv workspace package owns the two aggregate tasks so its npm wrappers do not recurse. |
| `tsconfig.json` | New TypeScript check configuration for selected `deno.json#task:typecheck`; includes the five prior entry files and the preload's declarations. |
| `scripts/deno_shim.ts` | New D1 preload. It makes a mutable shim copy, forwards `exitCode` to Node, and provides the `Deno.DirEntry` and `Deno.FileInfo` namespace types used by imports. `commitlint` also loads it because its `.mjs` config reads `Deno.env`. |
| `deno.json` | Removed selected `deno.json#exclude`, `#fmt`, `#imports`, `#nodeModulesDir`, `#workspace`, and all 42 `#task:*` sites. Kept review site `deno.json#compilerOptions` unchanged. |
| `deno.lock` | Deleted selected whole-file site `W:deno.lock`. |
| `.gitignore` | Deleted selected `S135` line 4 only. |
| `plugins/code/skills/clean-code/scripts/cli.ts` | Changed selected `R:plugins/code/skills/clean-code/scripts/cli.ts:6`; left `S097` unchanged. |
| `specs/019-turborepo/evidence/worker-T001.md` | New required worker report. |

The 42 task site names moved to `package.json` are: `backfire:build`,
`backfire:eval`, `backfire:install`, `backfire:ready`, `check`,
`clean-architecture`, `clean-code`, `clean-code:scope`, `commitlint`,
`doc-regions:audit`, `doc-regions:check`, `doc-regions:prepare`,
`doc-regions:update`, `docs:check`, `docs:generate`, `doctor`, `format`,
`format:check`, `lint`, `lint:fix`, `lint:shell`, `plugins:validate`, `test`,
`test:backfire`, `test:backfire-slow`, `test:clean-architecture`,
`test:clean-code`, `test:cli-contract`, `test:commit-msg`, `test:doc-regions`,
`test:docs`, `test:doctor`, `test:git-flow`, `test:plugin-skills`,
`test:wiki-consistency`, `test:wiki-raw-import`, `test:workflow`,
`test:worktree-branch`, `typecheck`, `verify`, `wiki-consistency:install`, and
`workflow`.

The retained `deno.json#compilerOptions` still supplies `@types/node` to manual
Deno checks, so a `deno.json` with only `compilerOptions` still affects Deno
type checking. Root tasks, imports, formatting, workspace, node_modules behavior,
and exclusions no longer come from it.

All selected sites were changed or deleted. I left review site
`deno.json#compilerOptions` and leave site `S097` at `cli.ts:44` byte-for-byte
unchanged. I found no unselected site that T001 must change. The remaining
typecheck errors identify T003-owned `Deno.Command` and `FsFile.lock/unlock`
calls; `clean-architecture` also reports two Node resolver failures described
below, outside T001 ownership.

## Node permission limits

Every repository TypeScript script or test launched by Node loads the preload.
The commands retain Node's `--permission` model and map Deno filesystem and
child-process scopes where present. Node has no environment-variable or
system-information permission scopes and cannot limit child processes to a
program allow-list. Where Deno allowed all programs, this adds no narrower
restriction than Deno had.

| Task | Deno scope Node cannot express |
| --- | --- |
| `doctor` | Program allow-list: Deno, Quarto, uv, git-flow, git, lychee, node, and npm. |
| `test:plugin-skills` | Program allow-list: node. Deno's environment grant is unscoped; Node cannot restrict environment names. |
| `test:doctor` | Deno environment and program grants are unscoped; Node cannot restrict environment names or child programs. |
| `test:git-flow` | Named environment grant `HOME,DENO_DIR` and program allow-list `git`. |
| `test:worktree-branch` | Program allow-list `git,sh`. |
| `commitlint` | Program allow-list `git` and `--allow-sys`. Deno's environment grant is unscoped. |
| `test:commit-msg` | Deno environment and program grants are unscoped; Node cannot restrict environment names or child programs. |
| `workflow`, `verify`, `test:cli-contract`, `test:workflow` | `--allow-sys`; environment and program grants are unscoped. |
| `lint`, `lint:fix`, `format`, `format:check` | Deno environment and program grants are unscoped; Node cannot restrict environment names or child programs. |
| `plugins:validate` | None beyond the filesystem path; Deno grants read access only to `plugins`. |
| `clean-architecture` | `--allow-sys`. Deno's environment grant is unscoped. |
| `test:clean-architecture` | `--allow-sys`; environment and program grants are unscoped. |
| `docs:generate`, `docs:check` | `--allow-sys`, program allow-list `deno` and `$HOME/.deno/bin/deno`; Deno's environment grant is unscoped. |
| `test:docs` | `--allow-sys`; environment and program grants are unscoped. |
| `test:wiki-raw-import` | Deno environment and program grants are unscoped; Node cannot restrict environment names or child programs. |

`clean-code`, `clean-code:scope`, and `test:clean-code` remain Deno tasks as
selected by D5. Tasks that run uv directly had no Deno permission flags.
`turbo.json` passes through `HOME`, `PATH`, `XDG_*`, `UV_*`,
`PYTHONDONTWRITEBYTECODE`, `DENO_DIR`, `TMPDIR`, `CI`, and the three variables
reported by Biome: `CONSTITUTION_VERSION_COMMIT`,
`CONSTITUTION_VERSION_AMEND`, and `VERBOSE_BROCCOLI_CONFIG`.

## Verification

Commands run and results:

| Command | Exit | Result |
| --- | ---: | --- |
| `$HOME/.deno/bin/deno task workflow` before edits | 0 | Printed the initial workflow instructions. |
| `npm install` | 0 | Generated the final lock after the workspace glob and coordinator-authorized dependency updates. |
| `npm ci` | 0 | Installed from the final lock. |
| `npm ls` | 0 | No dependency problems; all direct versions are pinned. |
| Script-name comparison against `git show HEAD:deno.json` | 0 | 42 prior tasks, 42 npm scripts, no missing or extra names. |
| `node --import ./scripts/deno_shim.ts scripts/validate_plugins.ts` | 0 | All three plugins PASS; direct Node invocation emits `MODULE_TYPELESS_PACKAGE_JSON` because the package has no `type` field. |
| `npm run typecheck` | 2 | T003-owned `Deno.Command` errors in `scripts/constitution_version.ts`, `scripts/docs.ts`, `scripts/workflow_git.ts`, `scripts/workflow_skills.ts`, `scripts/workflow_verify.ts`, plus `FsFile.lock/unlock` errors in `scripts/docs.ts` and `scripts/workflow_verify.ts`. |
| `npm run lint` | 0 | Clean; Node prints its `SecurityWarning` for `--allow-child-process`. |
| `npm run format:check` | 0 | Biome and Prettier checks pass. |
| `npm run lint:shell` | 0 | Clean. |
| `npm run plugins:validate` | 0 | All three plugins PASS without the direct-command module-type warning. |
| `npm run clean-architecture` | 1 | Dependency-cruiser cannot resolve `conventional-changelog-conventionalcommits` from `scripts/commitlint.config.mjs` and `@eemeli/yaml` from `scripts/docs_test.ts`; both files are outside T001 ownership. |
| `npm run commitlint -- --edit /tmp/t001-commit-message` | 1 | The `.mjs` config receives the Deno shim, then its local rule reaches T003-owned `constitution_version.ts` and fails because `Deno.Command` is not implemented yet. |
| `npm run clean-code` | 0 | Deno command ran; report says `NOT_APPLICABLE` with zero selected and 32 excluded candidates. |
| `npm run test:clean-code` | 0 | 35 passed, 0 failed. |
| `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --import ./scripts/deno_shim.ts -e 'Deno.exitCode = 7'; result=$?; test "$result" -eq 7` | 0 | The shim setter returns the exit code through `process.exitCode`. |
| `npm run workflow -- --task T001` | 1 | Fails on T003-owned runtime call `Deno.Command is not a constructor`. |
| `$HOME/.deno/bin/deno task workflow` after edits | 1 | Resolves the npm wrapper and fails on the same T003-owned `Deno.Command` call. |
| `$HOME/.deno/bin/deno task verify` | 1 | Runs the workflow with `--verify` and fails on the same T003-owned `Deno.Command` call before verification can finish. |
| `uv workspace list` | 0 | Found backfire, doc-regions, wiki-consistency, and the root workspace. |
| `npx turbo run check --dry=json` (worktree) | 1 | T002's root `pyproject.toml` still declares `verbose-broccoli-python` in both `[project]` and `[tool.turbo]`; Turbo reports a package-name collision. |
| `npx turbo run test --dry=json` (worktree) | 1 | Same root workspace collision. |
| `npx --no-install turbo ls --output=json > turbo-ls.raw` (temporary copy) | 0 | With only `[project]` removed from the temporary root manifest, Turbo discovers the three Python members and synthetic root package. |
| `npx --no-install turbo run check --dry=json > check.raw` (temporary copy) | 0 | Dry graph contains the ten root check leaves, the check/test aggregates, and fourteen test leaves listed below. |
| `npx --no-install turbo run test --dry=json > test.raw` (temporary copy) | 0 | Dry graph contains the test aggregate and fourteen test leaves listed below. |

The dry-run checks used `/tmp/t001-turbo.WA34gD` because T002's root manifest
still has the package-name collision. In that copy, I removed only `[project]`
from the root `pyproject.toml`, matching the coordinator's requested virtual
uv workspace; no worktree file was changed for this validation. The synthetic
Python workspace package provides the two `true` aggregates, while its inferred
checker is overridden so it adds no check command. The task lists were:

```text
check (26 tasks)
//#clean-architecture
//#clean-code
//#doc-regions:check
//#docs:check
//#doctor
//#format:check
//#lint
//#lint:shell
//#plugins:validate
//#test:clean-architecture
//#test:clean-code
//#test:cli-contract
//#test:commit-msg
//#test:docs
//#test:doctor
//#test:git-flow
//#test:plugin-skills
//#test:wiki-raw-import
//#test:workflow
//#test:worktree-branch
//#typecheck
backfire#test
doc-regions#test
verbose-broccoli-python#check
verbose-broccoli-python#test
wiki-consistency#test

test (15 tasks: aggregate plus 14 test leaves)
//#test:clean-architecture
//#test:clean-code
//#test:cli-contract
//#test:commit-msg
//#test:docs
//#test:doctor
//#test:git-flow
//#test:plugin-skills
//#test:wiki-raw-import
//#test:workflow
//#test:worktree-branch
backfire#test
doc-regions#test
verbose-broccoli-python#test
wiki-consistency#test
```

The Python workspace package's `check` and `test` commands are `true` task
aggregates; the check aggregate prevents Turbo's inferred workspace checker
from adding checks, and its test aggregate fans out to the 14 requested test
tasks. At the time of this T001 check, T002's root manifest still had the
workspace-name collision; T001b verified the graphs in the shared worktree
after T002b removed the `[project]` table.

`git diff --stat` shows 21 tracked files because T002 and the coordinator
changed files concurrently outside T001 ownership. The scoped tracked diff
contains only four T001 files; Git does not include the seven new, untracked
T001 files in `git diff --stat`. I did not stage or edit concurrent files.

## T001b follow-up: uv-only Turbo members

Assumption: apply the `glob_without_members` recommendation in
`evidence/decide-d13.json`. The root npm workspace glob is now `tools/none`,
which matches no npm package. Turbo remains in multi-package mode for `//#`
tasks, while its packages come from the uv workspace. This keeps
`packages/wiki-consistency/package.json` out of root npm installs and preserves
its separate `npm ci --prefix packages/wiki-consistency` project. The package
manifest remains unchanged because selected-sites marks
`W:packages/wiki-consistency/package.json` as `leave` / `can_stay` (review,
0.60).

### Changed files

| File | Site coverage |
| --- | --- |
| `package.json` | Root manifest created for T001; preserves its selected task/dependency replacements and applies D13's `glob_without_members` choice. The follow-up glob has no selected-sites ID because it is a D13 decision for this new manifest. |
| `package-lock.json` | Selected replacement for `W:deno.lock`; regenerated without an npm workspace link to `packages/wiki-consistency`. |
| `specs/019-turborepo/evidence/worker-T001.md` | Required T001b report addendum. |

No T001b-selected site was left unchanged. I found no unselected site that
needs to change; the unchanged npm manifest is a protected review site.

### T001b verification

The root Python manifest now has no `[project]` table, so these checks ran
against the shared worktree after T002b's virtual-workspace change.

| Command | Exit | Result |
| --- | ---: | --- |
| `deno task workflow` before the T001b edit | 1 | Existing workflow wrapper reached T003-owned code and failed with `Deno.Command is not a constructor`. |
| `npm install` | 0 | Regenerated the root lock; npm removed the 148 packages previously included through the wildcard workspace. |
| `npm ci` | 0 | Installed from the regenerated root lock. |
| `npm ls` | 0 | Root dependency tree has no problems. |
| `npm ci --prefix packages/wiki-consistency --ignore-scripts --no-audit --no-fund` | 0 | The independent wiki npm project still installs. |
| `if rg -n 'packages/wiki-consistency|node_modules/wiki-consistency' package-lock.json; then exit 1; else echo 'No wiki-consistency npm workspace entry'; fi` | 0 | No wiki npm workspace entry in the root lock. |
| `node_modules/.bin/turbo ls` | 0 | Lists `backfire`, `doc-regions`, `verbose-broccoli-python`, and `wiki-consistency`. |
| `node_modules/.bin/turbo run check --dry=json > /tmp/t001b-check.json` | 0 | Lists the intended 26 tasks below. |
| `node_modules/.bin/turbo run test --dry=json > /tmp/t001b-test.json` | 0 | Lists the test aggregate and 14 test tasks below. |
| `node -e 'for (const f of ["/tmp/t001b-check.json", "/tmp/t001b-test.json"]) { const j=JSON.parse(require("node:fs").readFileSync(f,"utf8")); console.log(`${f}: ${j.tasks.length} tasks`); for (const t of j.tasks) console.log(t.taskId ?? t.task); }'` | 0 | Parsed and printed both dry-run task lists. |

```text
check (26 tasks)
//#clean-architecture
//#clean-code
//#doc-regions:check
//#docs:check
//#doctor
//#format:check
//#lint
//#lint:shell
//#plugins:validate
//#test:clean-architecture
//#test:clean-code
//#test:cli-contract
//#test:commit-msg
//#test:docs
//#test:doctor
//#test:git-flow
//#test:plugin-skills
//#test:wiki-raw-import
//#test:workflow
//#test:worktree-branch
//#typecheck
backfire#test
doc-regions#test
verbose-broccoli-python#check
verbose-broccoli-python#test
wiki-consistency#test

test (15 tasks: aggregate plus 14 test tasks)
//#test:clean-architecture
//#test:clean-code
//#test:cli-contract
//#test:commit-msg
//#test:docs
//#test:doctor
//#test:git-flow
//#test:plugin-skills
//#test:wiki-raw-import
//#test:workflow
//#test:worktree-branch
backfire#test
doc-regions#test
verbose-broccoli-python#test
wiki-consistency#test
```

`deno task workflow` after the glob change exited 1 with the same T003-owned
`Deno.Command is not a constructor` error; Deno also reported that
`tools/none` does not exist and skipped that workspace entry. `deno task verify`
exited 1 on the same error before the verification workflow could finish. Both
are recorded here because the repository's AGENTS.md requires these workflow
checks; neither changes the T001b acceptance results above.

The first attempt to parse both dry-run files ran concurrently with the test
dry run and exited 1 because `/tmp/t001b-test.json` was still empty. After both
dry runs completed, the same `node -e` parser command exited 0 and printed the
26 and 15 task lists shown above.
