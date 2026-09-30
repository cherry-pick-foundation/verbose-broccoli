# CHE-32 final review CR1: Node scripts, the clean-code skill and the tooling configuration

Read-only review of `git diff 8ce9b2a 9d8af61` for the non-test TypeScript in
`scripts/`, the two Git hooks, the clean-code skill, `plugins/code/package.json`
and the root tooling configuration (`package.json`, `.npmrc`, `turbo.json`,
`tsconfig.json`, `biome.json`, `.gitignore`, `orca.yaml`,
`.github/workflows/*.yml`). Lock files and `docs/reference/` were skipped.
Requirements: `specs/019-turborepo/spec.md`, `research.md`, `AGENTS.md` and the
two selected-site lists. Reviewed on 2026-09-29 with Node.js 24.19.0, npm
12.1.0 and uv 0.11.32. Scratch work ran under the session scratchpad
(`$S` below), never in the repository.

## Summary

No blockers. Six should-fix findings and five notes. The in-scope checks and
the focused test suites pass, and no in-scope file outside the lock files still
names Deno (FR-011). The check graph in `turbo.json` runs every check and all
15 test tasks that `deno task check` ran at `8ce9b2a` (FR-003).

## Findings

### F1 (should-fix): `npm run backfire:install` now removes the other workspace members

- **Evidence**: `package.json:30` still runs
  `uv sync --project packages/backfire --frozen --extra education`. With the
  root uv workspace this syncs the shared root `.venv` to backfire alone. In a
  `git archive 9d8af61` copy under `$S/copy`, after
  `uv sync --locked --all-packages --extra education --offline` (exit 0),
  `uv sync --project packages/backfire --frozen --extra education --offline --dry-run`
  printed `Would uninstall 32 packages`, including `doc-regions` and
  `wiki-consistency`. After running it for real (exit 0), the doctor's
  workspace check `uv sync --locked --check --all-packages --extra education --offline`
  exited 1. On `develop` the same command touched only
  `packages/backfire/.venv`.
- **Impact**: `docs/backfire.md:20` tells users to run it as the first build
  step. After that, `npm run check` fails at the doctor and at the
  doc-regions and wiki-consistency tests until the user reruns the full sync.
  `.github/workflows/check.yml:50` also installs only this, then runs
  `npm run check`, whose doctor now requires the whole workspace.
- **Resolution**: make `backfire:install` sync the whole workspace
  (`uv sync --locked --all-packages --extra education`, as `orca.yaml` does),
  or add `--inexact`. D6 moved to one root `.venv` but did not decide this
  command's new effect.

### F2 (should-fix): the review routing ignores the new tooling files

- **Evidence**: `scripts/workflow.ts:28-29` dropped `deno.json` and
  `deno.lock` from `reviewPaths` without adding their replacements. Testing the
  regex from both revisions with `node -e` gave: `turbo.json false`,
  `uv.lock false`, `pyproject.toml false`, `.npmrc false`,
  `plugins/code/skills/clean-code/.npmrc false`; at `8ce9b2a`,
  `deno.json true`, `deno.lock true` and `packages/backfire/uv.lock true`.
- **Impact**: `turbo.json` now decides which checks `npm run check` runs, and
  the Python lock moved from `packages/*/uv.lock` (covered by `^packages/`) to
  the root `uv.lock`. Edits to either no longer get the REVIEW route that edits
  to `deno.json` or a package lock got on `develop`.
- **Resolution**: add `turbo\.json`, `uv\.lock`, `pyproject\.toml` and
  `\.npmrc` to the file-name alternation, with a case in
  `scripts/workflow_test.ts`.

### F3 (should-fix): the IO-package rule misses packages installed in `node_modules`

- **Evidence**: `scripts/clean_architecture.ts:24-25` and `:225` match
  `forbiddenIO` against the dependency's path, and `:247` excludes
  `node_modules/`. Once npm installs a package, dependency-cruiser resolves the
  import to `node_modules/<name>/...`, which the pattern does not match. Probe
  in `$S/ca` (a `plugins/a/src/domain/io.ts` importing `hono`, a root
  `devDependencies` entry for `hono`, and `analyzeImportGraph` from this
  branch): with `node_modules/hono` present the violations were `[]`; after
  removing `node_modules` they were
  `[["plugins/a/src/domain/io.ts","hono","no-io-packages-in-inner-layers"]]`.
- **Impact**: on `develop`, Deno ran with `nodeModulesDir: "none"`, so npm
  imports stayed unresolved and the rule caught them. No IO package is
  installed and no `domain/` or `application/` file exists today, so nothing
  fails now. The rule will stay silent as soon as such a package becomes a
  dependency. The test fixture passes only because nothing is installed.
- **Resolution**: also forbid the resolved form, for example add
  `(^|/)node_modules/${ioPackages}/` to `forbiddenIO`, and add a fixture with
  an installed package.

### F4 (should-fix): the docs script's `docs` directory guard no longer fires

- **Evidence**: `scripts/docs.ts:572` keeps `if (!docs?.isDirectory)` from
  `develop`, but `info()` now returns a Node `Stats`, where `isDirectory` is a
  method and always truthy. In `$S/dr`, with `docs` as a regular file,
  `syncReferenceDocs(root, 'check')` failed later with
  `package.json: Expected a regular input file.` instead of
  `docs: Expected the repository documentation directory.`
  `rg` for Deno-style `.isDirectory`/`.isFile`/`.isSymlink` properties in the
  non-test scripts finds only this site.
- **Resolution**: call `docs?.isDirectory()`, with a test case.

### F5 (should-fix): the Node version floor is inconsistent and too low

- **Evidence**: the doctor accepts Node 22 (`scripts/doctor.ts:197-199`,
  `turbo.json:22`), and the commit-msg hook says "Node.js 22 or later"
  (`scripts/git-hooks/commit-msg:15`). The skill's own `SKILL.md:16` and
  `package.json` `engines` require 24.12.0, CI pins 24.19.0, and the scripts
  use `RegExp.escape` (`scripts/clean_architecture.ts:26`,
  `scripts/workflow_plan.ts:68`, `scripts/workflow_graph.ts:78`). On `develop`
  the doctor pinned the exact runtime (Deno 2.9.6) and checked that the
  executing runtime was the configured one; that check was dropped, not
  replaced.
- **Limit**: I could not run Node 22 here (only 24.19.0 is installed), so the
  failure mode on 22 is not measured. `node -p` on 24.19.0 shows V8 13.6 with
  `RegExp.escape` present.
- **Resolution**: set one floor (at least the skill's 24.12.0, or pin 24.19.0
  as Deno was pinned) in the doctor, its description and the hook message, or
  record a decision that keeps 22.

### F6 (should-fix): the same `execFile` wrapper is written six times

- **Evidence**: near-identical promise wrappers that map `execFile` to a
  `{success, code, stdout, stderr}` result are in
  `scripts/constitution_version.ts:31`, `scripts/doctor.ts:80`,
  `scripts/docs.ts:176`, `scripts/workflow_git.ts:17`,
  `scripts/workflow_skills.ts:65` and `scripts/workflow_verify.ts:154`. The
  `proper-lockfile` type is also hand-declared twice through `createRequire`
  (`scripts/docs.ts:30`, `scripts/workflow_verify.ts:11`).
- **Impact**: AGENTS.md "Reuse Before Implementing" asks for the least local
  code. D1 (rewrite `Deno.Command` to `node:child_process`) did not call for
  six copies.
- **Resolution**: keep one small shared helper module (or use
  `util.promisify(execFile)` with a catch that reads
  `error.code`, `stdout` and `stderr`), and import `proper-lockfile` with
  `@types/proper-lockfile` instead of the local declarations.

### N1 (note): the repository checks the clean-code skill against the root lock, not the shipped one

- **Evidence**: `orca.yaml` and `check.yml` run `npm ci` only at the root, and
  the skill directory has no `node_modules`
  (`ls plugins/code/skills/clean-code/node_modules`: no such file). So
  `npm run clean-code`, `test:clean-code` and
  `scripts/workflow_skills.ts:67` resolve the skill's imports from the root
  `node_modules`. Comparing the two locks with `node -e`: 100 entries equal,
  5 differ (for example `picomatch` 4.0.7 in the skill lock, 4.0.5 in the
  root), 3 only in the skill lock. On `develop`, the tasks and
  `workflow_skills.ts` ran the skill with its own `deno.json` and
  `deno.lock --frozen`. Only `audit.yml` now installs the skill's lock.
- **Resolution**: install the skill's lock in `orca.yaml` and CI
  (`npm ci --prefix plugins/code/skills/clean-code`) so the checks run what
  users install, or record that the root lock stands in for it.

### N2 (note): legacy evidence records are skipped without validation

- **Evidence**: `scripts/workflow_verify.ts:71-80` drops every record whose
  `context` lacks `node_version` before `validate()`. That keeps old Deno
  records from breaking `npm run verify`, but it also hides a malformed or
  truncated new record that `develop` would have rejected. No test covers it
  (`rg deno_version scripts/*_test.ts` finds nothing). These lines are outside
  the listed sites for this file (X012 line 60, X125 lines 27 and 188).
- **Resolution**: skip only records that carry `deno_version`, and add a test.

### N3 (note): the file locks now give up after ten minutes

- **Evidence**: `scripts/workflow_verify.ts:218` and `scripts/docs.ts:581`
  retry 600 times at 1 s. `develop`'s `FsFile.lock()` waited without a limit.
  A second `npm run verify` waiting behind a slow check now fails with
  `ELOCKED` after ten minutes. D12 chose the package but not this limit.
- **Resolution**: record the limit in D12, or retry without one.

### N4 (note): the Python test commands are defined twice, and their setup hints are gone

- **Evidence**: `package.json:33,34,40,41` and `turbo.json:48-126` define the
  same pytest commands; the turbo graph uses only the `turbo.json` copies, and
  CI uses `npm run test:backfire-slow`. The `develop` tasks first checked for
  the environment and printed the repair command (`Missing Backfire pytest
  environment. Run deno task backfire:install.`); the new ones do not.
- **Resolution**: point one copy at the other, or drop the unused scripts;
  the doctor's message (`scripts/doctor.ts` `checkUvWorkspace`) can serve as
  the repair hint.

### N5 (note): smaller behaviour changes without a decision

- `scripts/doctor.ts:286` now reports every entry in `package-lock.json`
  (all transitive packages, keyed by `node_modules/...` path) instead of the
  direct dependencies, and no longer throws on a missing locked dependency.
- `scripts/clean_architecture.ts` `readPackageConfig` turns plain-version
  `dependencies` into `npm:name@version` aliases and bare `imports` targets
  into `npm:` targets. D18 says the check reads the same three fields; these
  two branches go beyond it and have no test case (the tests use only `npm:`
  specifiers).
- New files outside the site lists (`.npmrc`, `plugins/code/package.json`,
  the skill's `package.json` and `.npmrc`) are each backed by a decision (the
  npm 12 finding, D18, D16).

## Checked and found consistent

- `turbo.json` `verbose-broccoli-python#check` depends on the 11 checks and
  the test task depends on all 15 tests of `develop`'s `deno.json`; every task
  has `cache: false` (FR-003, FR-008).
- The skill's `glob` rewrite keeps `develop`'s behaviour: in `$S/g`,
  `fs.promises.glob` with `withFileTypes` returned absolute `parentPath`
  values, did not descend into a symlinked directory, and reported a file
  symlink as `isFile() false`.
- `orca.yaml` syncs the whole workspace and runs `npm run doctor`; the three
  workflows install Node 24.19.0 with a checksum.

## Commands run

| Command | Exit |
| --- | --- |
| `git diff --stat 8ce9b2a 9d8af61` and per-file `git diff` | 0 |
| `node -e` glob probe in `$S/g` | 0 |
| `node run.mjs` IO-rule probe in `$S/ca` (with and without `node_modules`) | 0 (violations `[]` / 1) |
| `node run.mjs` docs-guard probe in `$S/dr` | 0 (wrong message) |
| `git archive 9d8af61` into `$S/copy`, `uv sync --locked --all-packages --extra education --offline` | 0 |
| `uv sync --project packages/backfire --frozen --extra education --offline --dry-run` (copy) | 0 (would uninstall 32) |
| `uv sync --project packages/backfire --frozen --extra education --offline` (copy) | 0 |
| `uv sync --locked --check --all-packages --extra education --offline` (copy) | 1 |
| `node -e` reviewPaths test at both revisions | 0 |
| `node -e` root and skill lock comparison | 0 |
| `npm run typecheck` | 0 |
| `npm run format:check` | 0 |
| `npm run lint` | 0 |
| `npm run plugins:validate` | 0 |
| `npm run clean-architecture` | 0 |
| `npm run clean-code` | 0 |
| `npm run docs:check` | 0 |
| `npm run test:clean-architecture` (4 pass) | 0 |
| `npm run test:clean-code` (35 pass) | 0 |
| `npm run test:doctor` (17 pass) | 0 |
| `npm run test:commit-msg` (5 pass) | 0 |
| `npm run test:workflow` (56 pass) | 0 |
| `npm run doctor` | 0 |
| `git grep -i deno 9d8af61` over the in-scope files | 1 (no matches) |
| `git status --short` after the runs | 0 (clean) |
