# CHE-32 T003: Node scripts, hooks, setup, and CI

Assumption: `selected-sites.md` is authoritative. I preserved concurrent work and changed only T003-owned sites, plus the coordinator-approved `package.json` permission scopes and `scripts/hash.ts` D14 site.

## Changes

| File | Selected sites covered |
| --- | --- |
| `scripts/constitution_version.ts` | S030 |
| `scripts/workflow_git.ts` | S039 |
| `scripts/workflow_skills.ts` | S036, S057 |
| `scripts/workflow_verify.ts` | S024:171-177, S024:238, S029, S051, S118 |
| `scripts/docs.ts` | F:ts_deno:scripts/docs.ts:1-14, S021:520-524, S048, S058, S124, S148, R:scripts/docs.ts:439#measured, R:scripts/docs.ts:458#measured, R:scripts/docs.ts:597#measured |
| `scripts/doctor.ts` | S044, S059, S095:121, S095:245, S095:295, S126, S149, S182, S192, S200 |
| `scripts/workflow.ts` | S127 |
| `scripts/workflow_graph.ts` | S125 |
| `scripts/clean_architecture.ts` | S155 |
| `scripts/workflow-evidence.schema.json` | S117 |
| `scripts/git-hooks/commit-msg` | R:scripts/git-hooks/commit-msg |
| `scripts/git-flow-hooks/pre-flow-feature-finish` | S128 |
| `orca.yaml` | S138, S193, S201 |
| `.github/workflows/audit.yml` | S131 |
| `.github/workflows/check.yml` | S134 |
| `.github/workflows/docs-check.yml` | S133 |
| `docs/reference/commands.md` | S140, S151; regenerated |
| `docs/reference/plugins.md` | S141; regenerated |
| `scripts/hash.ts` | R:scripts/hash.ts:6, coordinator-approved D14 |
| `package.json` | Coordinator-approved permission-scope changes only; T001 owns the rest of this file |
| `specs/019-turborepo/evidence/worker-T003.md` | This report |

The selected child-process sites now use `node:child_process`. Repository TypeScript children use Node and the preload; clean-code help and scope checks still use standalone Deno. Doctor checks Node 22+, npm and the root `package-lock.json`/`node_modules`, one locked all-package uv workspace sync, the two retained tool environments, and standalone Deno 2.9.6. Docs now use root npm scripts and Turbo task descriptions, and print `npm run` invocations. Setup and CI install Node 24.19.0 with its pinned checksum and run npm commands. The hooks call npm commitlint and verify.

Both selected file locks use `proper-lockfile` 4.1.2. The docs generator locks `docs` using the in-directory `docs/.lock` sidecar; the verification writer locks its existing `.git/workflow/lock` target while appending evidence. Both release in normal and error paths. `proper-lockfile` updates locks every five seconds and treats a lock older than its default ten-second stale interval as stale; after a process crash, a later acquisition can remove the stale sidecar. No lock artifact remained after generation.

## Preserved sites and open questions

No selected site was intentionally left unchanged. The selected clean-code subprocess sites were changed to use a standalone Deno path because that shipped skill still requires Deno (D5). Leave rows remain unchanged, including `workflow_skills.ts` S121 and the clean-code Deno installs in `check.yml` S152 and `docs-check.yml` S153. The audit workflow also retains the clean-code Deno audit. Unselected Deno filesystem, environment, arguments, error, and `import.meta.main` sites remain unchanged. No unselected site was found that must change. The remaining `deno task clean-code:scope` repair text is in leave sites; that Deno command remains available.

The docs commands have narrow read scopes for the resolved Deno executable and `$HOME/.deno/bin/deno`, so Node can launch clean-code help. The doctor command adds a dynamic read scope for the Node installation root because Node passes its permission model to child Node processes such as npm; Deno's `--allow-run` did not do this. Doctor passed with this scope, and no additional read scopes were needed for uv, Git, git-flow, Quarto, lychee, or Deno.

## Verification

Commands run and results:

| Command | Result |
| --- | --- |
| `npm ci` | Exit 0; 277 packages added, 0 vulnerabilities. |
| `npm run docs:generate` | Exit 0; PASS for both reference files. |
| `npm run docs:check` | Exit 0; PASS for both reference files. |
| `npm run doctor` | Exit 0; Node 24.19.0, Deno 2.9.6, npm locks, uv workspace, and retained tools all PASS. |
| `npm run plugins:validate` | Exit 0; code, work, and chat PASS. |
| `npm run clean-architecture` | Exit 0; 64 files scanned, 0 violations. |
| `npm run typecheck` | Exit 0. |
| `npm run lint` | Exit 0; 60 files checked. |
| `npm run lint:shell` | Exit 0. |
| `npm run format:check` | Exit 1; formatter reported four test files outside T003 ownership: `scripts/clean_architecture_test.ts`, `scripts/cli_contract_test.ts`, `scripts/commit_msg_test.ts`, and `scripts/docs_test.ts`. Their diffs are listed in the command output; these T004/T005-owned files were not edited. |
| `npm run workflow` | Exit 0; printed the workflow report using Node. It reports REVIEW for the shared 72-file worktree. |
| `$HOME/.deno/bin/deno task workflow` | Exit 0 after migration; reports the same REVIEW state and prints a non-fatal `tools/none` workspace-member warning. |
| Direct commit-hook probe with temporary messages | Outer probe exit 0; `bad commit message` was rejected with hook exit 1, and `feat: validate commit hook` passed with hook exit 0. |
| `git diff --check` | Exit 0. |
| `npm run verify` | Exit 1 with `CHECK_FAILED`; it ran and recorded `npm run check` in workflow evidence. The latest evidence record was inspected and names `npm run check`. |
| `$HOME/.deno/bin/deno task verify` | Exit 1 with the same `CHECK_FAILED`. |
| `npm run check` | Latest run exit 1. Turbo reports `test:git-flow: Could not find 'scripts/git_flow_test.ts'`, four formatter errors in the T004/T005 test files listed above, and `wiki-consistency:test: ERROR: file or directory not found: packages/wiki-consistency/tests`. Earlier runs also failed on `packages/backfire/tests` (exit 4) and `packages/doc-regions/tests`; pytest collected 0 items for the missing directories. |

The Python test-directory failure belongs to T002, and the formatter/test-file failures belong to T004/T005; the task directs T003 to report them without editing those files. An earlier verification run also reported the missing `packages/wiki-consistency/tests` directory, another T002-owned Python check.

Transient failures resolved during this task: the first doctor run said `. node_modules is missing or out of sync with package-lock.json; run npm ci`; after `npm ci`, the child npm process still hit `ERR_ACCESS_DENIED` on the mise Node path until the coordinator-approved Node installation scope was added. The first typecheck rejected the dependency type for `lockfilePath`; the local type was updated to match `proper-lockfile`. Initial docs generation lacked the correct lock/read scope; moving its lock sidecar under `docs` removed the extra root lock scope. Final doctor, docs, and typecheck runs pass as listed above.

`git diff --stat` currently shows changes from multiple workers in the shared worktree (54 tracked paths, including T001/T002/T004/T005 work, plus their untracked files). It therefore cannot show only T003 files without hiding concurrent changes. T003's changed paths are the rows above; `AGENTS.md` and `turbo.json` were not changed.

## T003b addendum

Assumption: a missing root `package.json` in a temporary workflow repository means there are no root aliases. An existing but unreadable or malformed package file still fails through TypeScript's configuration reader.

### Changes

- `scripts/clean_architecture.ts` — selected `S155`: the package reader now returns no aliases when the root package file is absent, keeps parse/read errors, and reads package `imports` alongside dependencies. Bare package targets become npm aliases; local and explicit protocol targets keep their meaning.
- `scripts/workflow_verify.ts` — selected `S024:171-177` and `S024:238`: acquisition retries every second for up to ten minutes, while proper-lockfile's default stale detection and the existing `.git/workflow/lock` protection and `finally` release remain.
- `scripts/docs.ts` — selected `S021:520-524`: the docs publication lock uses the same retry policy; `await using` still releases it on success or error.

No selected site was intentionally left unchanged. The leave/review `F:ts_deno:scripts/clean_architecture.ts:28-39` stayed unchanged. No unselected site needs to change for this fix.

### Verification

| Command | Result |
| --- | --- |
| `npm run test:workflow` | Exit 0; 56 passed, 0 failed. This passed twice during the follow-up. |
| `npm run clean-architecture` | Exit 0; 64 files scanned, 0 violations. |
| `npm run typecheck` | Exit 0. |
| `npm run lint` | Exit 0; 60 files checked. |
| `npm run docs:check` | Exit 0; both reference files PASS. |
| `node_modules/.bin/biome format scripts/clean_architecture.ts scripts/workflow_verify.ts scripts/docs.ts` | Exit 0; all three owned TypeScript files are formatted. |
| `npm run workflow -- --task task_af2b8f43b205 --graph impact --file scripts/clean_architecture.ts` | Exit 0 after the change; policy PASS. |
| `npm run workflow -- --task task_af2b8f43b205 --graph impact --file scripts/workflow_verify.ts` | Exit 0 after the change; policy PASS. |
| `npm run workflow -- --task task_af2b8f43b205` | Exit 0 before and after the changes. |
| `$HOME/.deno/bin/deno task workflow` | Exit 0 before and after the changes. |
| `npm run check` | Exit 1 at `//#format:check`: `Found 4 errors` in T004-owned `scripts/clean_architecture_test.ts`, `scripts/cli_contract_test.ts`, `scripts/commit_msg_test.ts` and `scripts/docs_test.ts`. Turbo then interrupted other running checks; the `doc-regions:test` log ends in `KeyboardInterrupt`, so that is cancellation fallout, not a separate diagnosed failure. |
| `$HOME/.deno/bin/deno task verify` | The Deno task exited 0, but its nested workflow returned `CHECK_FAILED` and recorded `exit_code: 1` for `npm run check`, with the same T004 formatting errors. The recorded log is `/home/choi-eunchang/workspaces/verbose-broccoli/develop/.git/worktrees/feature-turborepo/workflow/43f401ba-d24f-4590-a18c-aacacb111cb2.log`. |

The repository-wide failure is outside T003b ownership. The required T003b acceptance commands all pass.

## T003c addendum

Assumption: each existing lexical read scope should retain its current grant, with its resolved path added so Node can follow fixture symlinks without granting access beyond the same targets.

### Changes

- `scripts/docs.ts` — selected `S048` and `S058`: the help spawn now passes each existing read scope both lexically and through `Deno.realPath`, including the resolved `node_modules` target. It also suppresses `SecurityWarning` for direct Node children, which do not inherit npm's `node-options`.

No selected site was left unchanged. `scripts/docs_test.ts` remains unchanged: its `S007` filesystem/permission site is classified leave/can_stay and the task forbids test edits. No unselected site in `scripts/docs.ts` needs to change for the symlink fix.

### Verification

| Command | Result |
| --- | --- |
| `npm run test:docs` | Exit 1; 4 passed, 10 failed. The resolved-scope change fixes the real help collection and deterministic source-facts tests. |
| `npm run docs:check` | Exit 0; both reference files PASS. |
| `npm run typecheck` | Exit 0. |
| `npm run lint` | Exit 0; 60 files checked. |
| `node_modules/.bin/biome format scripts/docs.ts` | Exit 0. |
| `npm run workflow -- --task task_cb896589639c` | Exit 0; workflow printed REVIEW instructions for the shared worktree. |
| `$HOME/.deno/bin/deno task workflow` | Exit 0; same REVIEW state, with the existing `tools/none` warning. |
| `npm run workflow -- --task task_cb896589639c --graph impact --file scripts/docs.ts` | Exit 0; direct consumer `scripts/docs_test.ts` found and import policy PASS. |

The ten remaining `test:docs` failures are all in T004-owned `scripts/docs_test.ts`. Nine cases fail in its shared `tree()` helper at line 119 because Node's `Deno.readFile()` result does not provide `.toHex()`: `invalid manifests, tasks and duplicate identities retain the previous pair`; `every failed help form preserves output and check never repairs it`; `passing and drifting checks preserve working files and the Git index`; `tracked, untracked, ignored, directory and symlink extras are never read or removed`; `failed rollback retains recovery and the next generation restores it`; `first-publication failure retains the complete stage for explicit recovery`; `another writer appearing between renames is preserved with the recovery pair`; `actual SIGKILL between directory renames is detected and recoverable`; and `local and PR check entrypoints agree without Node actions`. The remaining `help cannot write, spawn, use network or read live Wiki configuration` test fails because its guard sees `permission widened`; `@deno/shim-deno`'s `Permissions.querySync` returns `granted` for every request (`node_modules/@deno/shim-deno/dist/index.mjs:426-439`). Both causes are in `S007` leave/can_stay test behavior; no test or shim files were changed.

Scoped ponytail review found no unnecessary code to remove; net: 0 lines possible.
