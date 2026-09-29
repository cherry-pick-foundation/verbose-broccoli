# Research: Turborepo trial

Measured on 2026-09-29 at `develop` 3627cb2 on the development machine
(Linux x86_64, Node.js 24.19.0, npm 12.1.0, uv 0.11.32, Deno 2.9.6). The
backfire judgments are in [evidence/](evidence/); each decision below names its
file. Backfire ran from `packages/backfire` (installed with `deno task
backfire:install`) through a local MCP client, because the session had no
backfire MCP tools. The judgments are advice; the measurements are the
evidence.

## Starting point

- 31 TypeScript and JavaScript files call the Deno namespace 733 times,
  including 158 `Deno.test` registrations and 47 `Deno.Command`
  constructions (`rg -o '\bDeno\.[A-Za-z]+'`).
- `deno.json` defines 36 tasks; `check` depends on 11 of them and `test` on
  14 test tasks. 23 tasks pass scoped `--allow-*` permission flags.
- Each Python package has its own `uv.lock` and `.venv`; `egg_base = ".venv"`
  keeps setuptools' metadata inside it.
- `deno task check` passed in 2 min 9.6 s wall clock (372.6 s user time),
  measured while other probes ran on the machine.
- Locally owned code: 176 files, 27,666 non-blank lines, counted with the
  script recorded in [report.md](report.md#method).

## Decisions

### D1. Deno APIs on Node.js

- **Decision**: Preload `@deno/shim-deno` 0.19.2 as `globalThis.Deno` so the
  file-system, `env`, `args`, `exit` and `errors` call sites stay unchanged.
  Rewrite only the call sites the shim cannot serve: `Deno.Command` and
  `Deno.CommandOutput` to `node:child_process`, `Deno.test` to `node:test`,
  `Deno.exitCode` to `process.exitCode`, and the `Deno.execPath()` spawns of
  Deno subcommands.
- **Backfire**: `backfire_decide` selected `shim_plus_rewrite` (0.88; local
  glue 0.08, full rewrite 0.02) ([d1](evidence/decide-d1.json)).
- **Evidence**: the shim provides every used API except `Deno.Command` and
  `Deno.exitCode`; its `Deno.test` only collects definitions. The upstream
  pull request that adds `Command` (denoland/node_shims#183) has been open
  since 2024-02-28, is marked blocked, reports exit code 0 as a failure and
  does not implement `spawn()`. With the preload, `scripts/validate_plugins.ts`
  ran unchanged on Node.js and printed the same report as on Deno.
- **Rejected**: a local `Deno.Command` and test-runner implementation adds
  locally owned code; rewriting all 733 call sites changes sites that an
  existing dependency already serves.

### D2. Running TypeScript on Node.js

- **Decision**: Node.js 24.19's default type stripping. Rewrite the two
  constructs that are not erasable (a constructor parameter property in
  `plugins/code/skills/clean-code/scripts/cli.ts` and one in
  `scripts/wiki_raw_import_test.ts`), and type-check with
  `erasableSyntaxOnly`.
- **Backfire**: `strip_only` (0.88) ([d2](evidence/decide-d2.json)).
- **Rejected**: `--experimental-transform-types` is experimental; `tsx` is a
  new dependency.

### D3. YAML formatting

- **Decision**: Prettier replaces `deno fmt --check .github/ orca.yaml`.
- **Backfire**: `prettier_yaml` (0.86) ([d3](evidence/decide-d3.json)).
- **Evidence**: Biome 2.5.14 ignores YAML files.
- **Open**: D5 keeps Deno for the shipped clean-code skill, so the evidence
  behind D3's second requirement changed; the question is with the user.

### D4. Permission flags

- **Decision**: Translate each task's Deno flags to Node's permission model
  (`--permission`, `--allow-fs-read`, `--allow-fs-write`,
  `--allow-child-process`) and list the scopes that Node cannot express
  (environment-variable names, program lists).
- **Backfire**: `node_permission` (0.85; ask the user 0.09)
  ([d4](evidence/decide-d4.json)).
- **Open**: dropping those scopes is the user's decision.

### D5. The shipped clean-code skill

- **Decision**: The skill in `plugins/code/skills/clean-code` stays on Deno;
  the repository's tasks and tests call it through `deno`.
- **Backfire**: `keep_skill_on_deno` (0.82) ([d5](evidence/decide-d5.json)).
- **Evidence**: it is a shipped plugin component whose `SKILL.md` tells
  users' agents to run it with Deno; moving it changes what they must
  install.
- **Superseded**: on 2026-09-29 the user moved the skill to Node as well,
  so that Deno is required nowhere (see D16).

### D16. The clean-code skill on Node

- **Decision**: The skill gets its own `package.json`, `package-lock.json`
  and `.npmrc` with the same pinned packages, and its few Deno calls are
  rewritten to Node built-ins, without a shim. Users run `npm ci --prefix
  <skill-root>` once, then `node <skill-root>/scripts/clean_code.ts`.
- **Backfire**: `skill_node_rewrite` (0.87) over a shim preload in the skill
  (0.05) ([d16](evidence/decide-d16.json)).
- **Evidence**: the skill's runtime scripts call the Deno namespace at five
  sites and its test file at about 25; JSR packages need the project
  `.npmrc` (`@jsr` registry, `allow-remote=root`).

### D6. Python environments

- **Decision**: Switch the three packages' build backend from setuptools to
  `uv_build` and drop `egg_base`; use one root `.venv` synced with
  `--all-packages`; readiness accepts the environment of the uv project that
  contains it, and the doctor and readiness sync checks cover the whole
  workspace.
- **Backfire**: `uv_build_root_venv` (0.80) ([d6](evidence/decide-d6.json)).
- **Evidence**: from the develop session's shared-workspace probe: with a
  root `.venv`, `egg_base = ".venv"` makes `uv sync` fail; without it,
  setuptools writes `src/*.egg-info` in built plugins; `uv_build` writes
  nothing outside `.venv` and keeps `.toml` and `.mjs` package data.
  Turborepo's inferred uv tasks run in the active or root environment.
- **Found during T002**: `uv_build` refuses to build a project whose
  `module-name` lists a module that is missing ("Expected a Python module at
  src/backfire_education/__init__.py"), which contradicts the earlier toy
  probe. The plugin build therefore writes into each copy a pyproject that
  names only the modules the copy contains (classified must-change, 0.99).
  Two more sites that T002 raised with failing output were classified
  must-change: the built-tree comparison in `test_build.py` and the
  per-member sync check in `ready.py`.

### D7. The built plugin's lock

- **Decision**: `backfire_tools/build.py` exports backfire's pinned versions
  from the root lock and runs `uv lock --offline` in the built copy with
  them as constraints, so the copy keeps its own `uv.lock` and the
  documented install and start commands.
- **Backfire**: `lock_in_copy` (0.88) ([d7](evidence/decide-d7.json)).
- **Evidence**: in a probe, the exported pins plus `uv lock --offline`
  produced the same 45 package versions as today's
  `packages/backfire/uv.lock`. A `pylock.toml` export works too, but its
  install needs `uv venv` and `uv pip sync`, which changes the documented
  commands.

### D10. The work plugin's copied Python projects

- **Decision**: The work build copies `doc-regions` and `wiki-consistency`
  as today and writes each copy's standalone `uv.lock` the way D7 does. In
  the copied `wiki-consistency/pyproject.toml` only, it replaces
  `doc-regions = { workspace = true }` with the path source `../doc-regions`.
  The install and run commands in the work plugin's `wiki-consistency`
  skill stay the same.
- **Backfire**: `per_project_locks` (0.86) over a plugin-root workspace
  (0.04) ([d10](evidence/decide-d10.json)).
- **Evidence**: inside a uv workspace, uv refuses a path source to a member
  ("Workspace members must be declared as workspace sources"), and outside
  one, `workspace = true` has nothing to refer to.

### D8. Turborepo caching

- **Decision**: Tasks that read files outside their package or run external
  programs have `cache: false`; caching stays on only where Turborepo's
  default inputs are complete.
- **Backfire**: `cache_off_outside` (0.50) over `declare_inputs` (0.30),
  confidence 0.40 ([d8](evidence/decide-d8.json)). The low confidence is
  reported as an open question; this choice is the one that cannot reuse a
  stale result.

### D9. Entry points

- **Decision**: Root `package.json` scripts: `workflow` runs
  `scripts/workflow.ts` on Node.js, `verify` runs it with `--verify`, and
  `check` runs `turbo run check`. The hooks call these scripts. The wording
  for `AGENTS.md` and the constitution goes to the user.
- **Backfire**: `npm_scripts` (0.70, confidence 0.64)
  ([d9](evidence/decide-d9.json)).

### D11. Shim gaps behind unchanged call sites

- **Decision**: The preload assigns a plain mutable copy of the shim to
  `globalThis.Deno` and forwards `Deno.exitCode` to `process.exitCode`, so
  the unchanged `Deno.exitCode` assignment in the clean-code skill's
  `cli.ts` and the `stub(Deno, ...)` calls in `scripts/docs_test.ts` work on
  Node.
- **Backfire**: `preload_glue` (0.90) over rewriting the sites (0.07)
  ([d11](evidence/decide-d11.json)).
- **Evidence**: measured after the first classification batches: the shim
  has no `exitCode`, so an assignment left the exit status at 0, and its
  namespace properties are non-configurable getters, which stubs cannot
  replace. T001's type check found the first gap.

### D12. File locks

- **Decision**: `proper-lockfile` 4.1.2 replaces the two exclusive file
  locks (`scripts/workflow_verify.ts` and `scripts/docs.ts`).
- **Backfire**: `proper_lockfile` (0.85) over reporting the gap (0.10) and a
  local exclusive-create lock file (0.02) ([d12](evidence/decide-d12.json)).
- **Evidence**: the shim's `FsFile` has no `lock` or `unlock`, and Node.js
  24.19 has no file-lock API. The package was last published in 2022-06; the
  report lists that as a maintenance risk.

### Scope change of 2026-09-29

The user made the trial the real change: Deno goes completely, including
the `@deno/shim-deno` preload (D1 and D11 are superseded), after merging
`develop` 8ce9b2a. The merge brought Ruff (CHE-29), the vault rule checks
(CHE-26) and a new dependency of `wiki-consistency` on `backfire[education]`.
Measured on Node 24.19 without the shim: `@std/fs` fails with "Deno is not
defined", while `@std/path`, `@std/assert`, `@std/testing/mock` and
`@cliffy/command` work. The selection was redone on the merged tree
(classification batch 20 onward).

### D17. The constitution amendment's type

- **Decision**: `feat(constitution)`, version 2.1.0 to 2.2.0 (commit
  `b1f8fff`): the workflow and verification gates name the npm commands,
  principle IX's examples no longer name Deno, and Governance records the
  decision. The user confirmed on 2026-09-29 that it is not breaking and
  that principle IX's "Do not require one repository-wide runtime, server or
  composition entry point" stays unchanged.
- **Backfire**: `feat_minor` (0.65) over `docs_patch` (0.25) and
  `breaking_major` (0.05), confidence 0.58 ([d17](evidence/decide-d17.json)).

### D18. Where the import-boundary check reads plugin exports

- **Decision**: `scripts/clean_architecture.ts` reads `plugins/**/package.json`
  and `packages/**/package.json` (outside `node_modules`) where it read
  `deno.json`, with the same fields (`name`, `imports`, `exports`). A new
  `plugins/code/package.json` declares the code plugin's one public export,
  `./cli`, which the deleted `plugins/code/deno.json` declared; it has no
  `type` field, so the plugin's hook scripts keep their module type.
- **Why**: without a config, the check gives `plugins/code` an empty public
  API, and the five root scripts that import the clean-code CLI break the
  policy graph. `package.json` defines the same three fields, so the rule
  logic stays as it is.
- **Backfire**: `package_json_same_fields` (0.85) over nested exports
  counting toward the plugin (0.10), a custom root field (0.025) and dropping
  the empty public API (0.01) ([d18](evidence/decide-d18.json)).

## Other findings

- npm 12 refuses packages whose tarballs are on another host by default
  (`allow-remote=none`); JSR's npm registry serves tarballs from
  `npm.jsr.io`. A project `.npmrc` with `allow-remote=root` installs the JSR
  aliases declared in the root `package.json` and their JSR dependencies.
- One root `uv.lock` with the constraints `starlette<=0.52.1`,
  `openai<=3.19.2`, `pyjwt<=2.15.0`, `sse-starlette<=3.4.11` and
  `magika<=0.6.3` resolves exactly the package versions of today's three
  locks (79 packages). An exact `magika==0.6.3` pin fails, because today's
  lock keeps `magika` 0.6.2 for Windows.
- Turborepo 2.11.5 appends an "agent guidance" block to the root
  `AGENTS.md` when it detects an AI agent, and re-adds it on later runs. The
  trial must not change `AGENTS.md`, so the coordinator set
  `"agentGuidance": false` in `turbo.json` and restored the file.
- Turborepo needs multi-package mode for root tasks (`//#name`), and a root
  `package.json` without a non-empty `workspaces` field puts it in
  single-package mode. `"workspaces": ["packages/*"]` makes the npm project
  in `packages/wiki-consistency` collide with the uv member of the same name,
  so the trial uses a glob that matches nothing (`tools/none`; D13,
  [d13](evidence/decide-d13.json), 0.91). A root `[project]` table with the
  same name as `[tool.turbo]` collides too, so the root uv workspace is
  virtual.
- Node's permission model reaches child Node processes through
  `NODE_OPTIONS`, and each child that has `--allow-child-process` prints a
  `SecurityWarning` to stderr, which broke the CLI contract's empty-stderr
  checks; a `--disable-warning` flag does not reach the children. An
  `.npmrc` `node-options` line fixed that but broke a doctor test, because
  npm then replaced the inherited `NODE_OPTIONS`. The trial instead starts
  `test:cli-contract` and `test:docs` with
  `NODE_OPTIONS=--disable-warning=SecurityWarning`. The same test showed that
  permission flags from a parent's `NODE_OPTIONS` and a child's own flags
  add up: a script run from a permissive test process gets the parent's
  wider grants, so a script's narrow scopes hold only when it runs first.
- `deno test` type-checks each test file and its imports before running
  it; `node --test` only strips types. With Deno gone, the `typecheck` task's
  five entry points left every test file, and anything only a test imports
  (such as the clean-code checker), unchecked. The type check now lists the
  test files too, with `skipLibCheck`, because Deno checks only local
  modules by default. The first run found a Deno-only glob option and two
  `assertRejects` calls whose predicate `@std/assert` ignores, so any
  rejection passed.
- Node's `fs.symlink` "requires full fs.read and fs.write permissions", so
  `test:git-flow` runs with unscoped reads and writes; Deno allowed writes to
  `/tmp` only. Node's test runner also could not find the test file under
  the narrower read scopes. Node checks resolved paths, so a scope on a
  symlinked `node_modules` does not cover its target.
- Turborepo runs a uv member's task in the member's directory, so the member
  test commands start with `uv --directory ../..` to keep the repository
  root as the working directory the old tasks had.
- Node 24.19 lacks `Uint8Array.prototype.toHex` and `Uint8Array.fromHex`
  (D14, Buffer instead; [d14](evidence/decide-d14.json)), and
  `@std/testing/snapshot` cannot load its `.snap` file on Node (D15, node:test
  snapshots; [d15](evidence/decide-d15.json)). Neither is a `Deno.*` call, so
  the exact and semantic searches did not find them; the test runs did.
- `@std/testing/snapshot` reads the Deno test context's `origin` and `name`;
  `node:test` in Node.js 24.19 has `TestContext.name` and
  `TestContext.filePath`.
- Turborepo 2.11.5's Python support runs its inferred tasks as `uv run
  --active --frozen --package <name> ...`, with a shell-less `command` array
  for custom tasks under `experimentalTaskCommand`
  (`node_modules/turbo/docs/guides/tools/python.mdx`).
