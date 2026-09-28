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
- **Open**: scope is the user's decision.

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
- `@std/testing/snapshot` reads the Deno test context's `origin` and `name`;
  `node:test` in Node.js 24.19 has `TestContext.name` and
  `TestContext.filePath`.
- Turborepo 2.11.5's Python support runs its inferred tasks as `uv run
  --active --frozen --package <name> ...`, with a shell-less `command` array
  for custom tasks under `experimentalTaskCommand`
  (`node_modules/turbo/docs/guides/tools/python.mdx`).
