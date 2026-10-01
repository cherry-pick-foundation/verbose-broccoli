# Research: CPU Load Relief

Facts were read from Turborepo 2.11.5 in this repository
(`node_modules/@turbo/linux-64/bin/turbo`), its `--dry=json` plans and
`-vv` logs, and the task commands and tests at `develop` 1eef330.

## D1. What Turborepo hashes by default

- A root task (`//#name`) hashes every file of the root package. The root
  package holds the whole repository: the dry plan at 1eef330 listed 813
  input files for `//#lint`, equal to `git ls-files | wc -l`. An untracked,
  unignored file is hashed too (a probe file raised the count to 814); an
  ignored file is not, unless a task or `globalDependencies` names it, which
  Turborepo then hashes (probes in `.local/` and `node_modules/`).
- A uv workspace package's task hashes its own files, the root Python
  configuration (`../../pyproject.toml`, `../../.python-version`,
  `../../ruff.toml` and the other names Turborepo's Python support adds) and
  every workspace package it depends on: `credit-offers#test` lists 37 files
  under `packages/backfire/`, and `wiki-consistency#test` 54 under
  `packages/backfire/` and `packages/doc-regions/`. Its
  `hashOfExternalDependencies` covers its part of `uv.lock`.
- Turborepo hashes no folder, so an empty folder is invisible to it.
- Turborepo caches only successful tasks. The run summary counts replayed
  tasks in `execution.cached` and executed ones in `execution.success` (a
  warm run: 30 cached and 8 successful of 38 attempted, `failed` 0);
  `npm run verify` still reads `execution.failed` and `execution.exitCode`
  from the same run's summary (`scripts/workflow-verify.ts`).
- With caching on, Turborepo writes each task's log next to its package:
  `.turbo/turbo-<task>-root-<hash>.log` at the root and
  `packages/<name>/.turbo/turbo-test.log` for package tasks.
- In a linked worktree with no `cacheDir` set, Turborepo uses the main
  worktree's cache: `-vv` logs "Using shared worktree cache at:
  …/develop/.turbo/cache".

## D2. Repository files

- **Decision**: Keep the root tasks' default inputs (the whole repository,
  tracked and untracked). For package tasks, keep the defaults and declare
  the files outside the package that a task reads: `doc-regions#test` runs
  `scripts/doc_sources_test.py`, which imports `scripts/doc_sources.py`.
- **Why**: The whole repository over-approximates every root task, so a
  missed reader is impossible; narrower inputs would need a proof per task
  for a saving only across worktrees with different code. Turborepo's Python
  support already adds imported workspace packages, so declaring them again
  would add nothing.
- **Ignored files that a check walks**: ESLint (`//#lint`), clean-code and
  dependency-cruiser (`//#clean-architecture`) find their files by walking
  folders, not through Git, so they also read JavaScript and TypeScript
  files that Git ignores, for example under `.local/`, `generated/` or a
  `coverage/` folder. Each declares those files as inputs (`**/*.{js,…}`
  or the folders it walks), with `node_modules` left to D4. The third
  develop merge review found this class through a related gap (D4).
- **Checked**: the Python tests read outside their package only through
  `scripts/doc_sources*.py` (doc-regions) and the root `pyproject.toml`
  (wiki-consistency's import-boundary test, a default input). Other cached
  checks list their files through Git (`format:check`, `lint:shell`), name
  them (`typecheck`, `plugins:validate`), respect `.gitignore` (ruff) or
  work in temporary fixtures (the tests).

## D3. Programs outside the repository

- **Decision**: `scripts/toolchain.sh` prints one SHA-256 over the versions
  of `node`, `npm`, `uv`, `python3`, `git`, `git flow` and `vale`, the
  resolved interpreters of `uv python find 3.14`, `.venv` and the three tool
  environments the cached tasks use, the system and global Git
  configuration (with includes), and the contents of the installed npm trees
  (D4). The `turborepo` npm script passes it to Turborepo as
  `VERBOSE_BROCCOLI_TOOLCHAIN`, which `globalEnv` hashes for every task.
- **Why**: These programs live outside the repository, so no file input can
  name them. They are what the cached tasks run: Node and npm for every npm
  script, uv and the interpreters for the Python tasks and tools, `python3`
  for the raw-import test's fixtures, Git and git-flow-next for the Git and
  workflow tests, Vale for wiki-consistency. Several are not pinned by any
  repository file (`uv` resolves to `~/.local/bin/uv`, `git flow` to
  `~/.local/bin/git-flow`, the tool environments to a floating
  `cpython-3.14` link). Some Python tests run Git without isolating its
  configuration, so the configuration outside the repository is hashed too.
- **Only standard output is hashed**: a test run under Node's permission
  flags made `npm --version` print a warning with its process ID, which
  changed the hash on every run.
- **Hashed environment variables**: `UV_*`, `MISE_*`, `CI` and
  `VERBOSE_BROCCOLI_CONFIG` move from `globalPassThroughEnv` to `globalEnv`,
  because they can change how uv, mise or a tool behaves; their values are
  the same in every worktree here. `HOME`, `PATH`, `XDG_*`, `TMPDIR`,
  `RUSTUP_HOME`, `CARGO_HOME` and `PYTHONDONTWRITEBYTECODE` stay
  pass-through: `PATH` differs per worktree (npm adds the worktree's
  `node_modules/.bin`) and the programs it finds are in the fingerprint; the
  others place files or caches, and the per-user configuration they locate
  is either Git's, which is hashed, or isolated by the tests.
- **Turborepo's own pass-through list**: even in strict mode, Turborepo
  2.11.5 passes a built-in list of variables to every task without hashing
  them (read from the binary's strings). Of those that can be set on this
  machine and can change a result, `NODE_OPTIONS`, `COREPACK_*`,
  `LD_PRELOAD`, `LD_LIBRARY_PATH`, `TZ` and `SHELL` are added to
  `globalEnv`; the fourth develop merge review found `NODE_OPTIONS`. The
  rest stay unhashed: `PWD` is the task's own folder and differs per
  worktree; `XDG_DATA_*` and `XDG_RUNTIME_DIR` are covered by `XDG_*` above;
  `XAUTHORITY`, `DBUS_SESSION_BUS_ADDRESS` and `COLORTERM` locate the
  desktop session or colour output, which no check uses; `TURBO_*` are
  Turborepo's own settings; the rest name Windows, macOS, Nix, Vercel,
  JetBrains, Docker, pnpm or Electron settings that do not apply here.
- **Cost**: about 0.1 s per Turborepo run.
- **Limit**: only the `turborepo` npm script computes the fingerprint. Every
  repository entry point (`npm run check`, `npm run test`, `npm run verify`
  and the hooks that call them) goes through it; a `turbo` run started
  directly gets an empty value and so shares no hash with those runs.

## D4. Generated and installed files

- **Decision**: Hash the installed files themselves, all ignored by Git, and
  list every entry of each environment with its type, permissions and link
  target, so that a re-pointed launcher link such as
  `node_modules/.bin/tsc` or a changed permission also changes the hash.
  `globalDependencies` names every file under `lib/` of `.venv` and of the
  tool environments the cached tasks use (`tools/ruff`, `tools/shellcheck`,
  `tools/check-jsonschema`). `scripts/toolchain.sh` hashes every file of
  `node_modules` and `packages/wiki-consistency/node_modules`, because
  Turborepo's globs skip `node_modules` (a `node_modules/**` glob hashed none
  of its 18,530 files). It also hashes the uv files that embed the
  worktree's path or name, which Turborepo would see as different in every
  worktree: each environment's `bin/` (entry-point scripts and native
  programs such as `ruff`, `shellcheck` and `magika`), its `.pth` files,
  `direct_url.json` and `pyvenv.cfg`. It reads them with the worktree's path
  replaced by `.`, an entry point's interpreter line reduced to `python`
  (uv writes `python` or `python3`, both links to the interpreter that D3
  resolves) and `pyvenv.cfg`'s `prompt` line removed.
- **Why**: Tasks run from these environments, not from the lock files (`uv
  run --frozen --offline --no-sync`), so any change inside them, including a
  hand edit to a package file or to the `pytest` launcher, must change the
  hash. The develop merge reviews found three gaps in turn: the first
  version hashed only npm's hidden lockfiles and each distribution's
  `METADATA`, the second left out the `bin/` scripts and `.pth` files, and
  the third hashed regular files only, not links.
- **Boundary**: what the repository installs from its own locks is hashed
  by content; programs installed outside it (Node.js, npm, uv and the
  interpreters it manages, Git, git-flow-next, Vale) are declared by version
  and resolved path (D3), as the user's decision allows ("external programs
  or versions").
- **Left out, and why**: every `RECORD` (install metadata listing hashes of
  the `bin/` scripts, read only by uninstallers) and uv's `uv_cache.json`
  (timestamps for its own freshness check, not read by `uv run --no-sync`);
  the shell activation scripts (`activate*`, `deactivate*`), which hold the
  worktree's name and which no task runs; and bytecode caches, which Python
  checks against their sources. `tools/commitizen` and `tools/spec-kit`
  serve no cached task.
- **Checked**: every one of the 10,632 environment files that Turborepo
  hashes is byte-identical to `develop`'s copy, and the fingerprint is the
  same in both worktrees. The other two worktrees' fingerprints differ, as
  their environments do. Hashing adds about 0.5 s of CPU to Turborepo's run
  and 0.8 s to the fingerprint.
- **Other generated files**: tracked generated files (for example
  `packages/backfire/src/backfire_education/regions.json`) are repository
  files. `__pycache__` folders are ignored and Python checks them against
  their sources; the Python tasks run with `PYTHONDONTWRITEBYTECODE=1`.

## D5. Tasks that stay uncached

| Task | Reason |
| --- | --- |
| `//#doctor` | It checks the installed tools and environments against their pins; it must run every time. |
| `//#lint:names` | ls-lint checks folder names, and Turborepo does not hash empty folders. |
| `//#test:lint-names` | It finds ls-lint with `mise which`; mise's version and global configuration are not hashed. |
| `//#test:mise-doctor` | It runs `mise doctor`; mise's version and global configuration are not hashed. |
| `//#test:constitution-bump` | It runs `mise exec`; mise's version and global configuration are not hashed. |
| `//#test:plugin-skills` | It checks that `.agents/skills` and `.claude/skills` are absent, and Turborepo does not hash folders, so an empty one would go unseen. |
| `verbose-broccoli-python#check`, `#test` and the packages' `#check` | They run `true` to group other tasks; caching saves nothing. |

These six took about 16 s together in `develop`'s last full run. The tasks
outside `npm run verify` (`doc-regions:update`, `prepare`, `audit`) keep
`cache: false`; they write files or call a model.

## D6. Cached tasks and what they run

Every cached task also hashes D3's fingerprint and variables and D4's
records. Root tasks hash the whole repository (D2).

| Task | Programs it runs | Outside reads |
| --- | --- | --- |
| `//#format:check` | Prettier (root npm tree), ruff (`tools/ruff`), `git ls-files` | none |
| `//#lint` | gts and ESLint (root npm tree), ruff | ignored JavaScript and TypeScript files (declared, D2) |
| `//#lint:shell` | `git ls-files`, shellcheck (`tools/shellcheck`) | none |
| `//#typecheck` | tsc | none |
| `//#plugins:validate`, `//#test:plugins-validate` | check-jsonschema (`tools/check-jsonschema`), npm | none |
| `//#clean-code`, `//#test:clean-code` | Node | ignored TypeScript files under `plugins/`, `packages/`, `scripts/` (declared, D2) |
| `//#clean-architecture`, `//#test:clean-architecture` | dependency-cruiser | ignored JavaScript and TypeScript files under `packages/`, `plugins/`, `scripts/` (declared, D2) |
| `//#python:imports` | import-linter (`.venv`) | none |
| `//#doc-regions:check` | doc-regions (`.venv`), Node for command help | none |
| `//#backfire:regions:check`, `//#test:backfire-regions` | Node | none |
| `//#test:ruff`, `//#test:gts` | ruff; gts and Prettier | none |
| `//#test:git-flow`, `//#test:worktree-branch`, `//#test:commit-msg` | Git, git-flow-next, commitlint | Git configuration isolated by each test |
| `//#test:workflow` | Git, dependency-cruiser | fixture repositories; some run Git with the outside configuration, which D3 hashes |
| `//#test:cli-contract` | Node, npm (`npm ci --prefer-offline` from the clean-code skill's lock) | npm's cache, integrity-checked against the lock |
| `//#test:session-select`, `//#test:grammatical-competence` | pytest (`.venv`) | temporary homes |
| `//#test:wiki-raw-import` | uv (`--locked --offline --script` from `raw_import.py.lock`), `python3`, Git | uv's cache, hash-checked against the lock; temporary home |
| `//#test:turbo-cache` | npm, Turborepo, Git | a temporary copy of the repository |
| `backfire#test`, `jev-ultrafast#test`, `credit-offers#test` | pytest (`.venv`), uv | none; temporary configuration folders |
| `doc-regions#test` | pytest, Git | `scripts/doc_sources.py`, `scripts/doc_sources_test.py` (declared) |
| `wiki-consistency#test` | pytest, Git, Vale, qmd (its npm tree) | root `pyproject.toml` (default input) |

Tests that compare dates inject the clock (`credit_offers._block(now=…)`,
`session_select.render(now=…)`).

## D7. Cache location and trust

- **Decision**: Use Turborepo's default, shared worktree cache
  (`develop/.turbo/cache`), and ignore `.turbo/` at any depth instead of
  `/.turbo/runs/`. Remote caching stays off (the `turborepo` script already
  unsets the remote-cache credentials and isolates Turborepo's config
  folders).
- **Why**: Several worktrees verify nearly the same packages; sharing lets
  one worktree replay another's unchanged package tests. Without the ignore
  rule, cache files would show as untracked in `develop`, and task logs would
  become inputs of every root task. The first measurement ignored only the
  root `.turbo/`: the package logs from one run changed every root hash, so
  the next run replayed nothing, and `npm run workflow` failed with "Code
  snapshot changed while processing the workflow".
- **Development runs**: until this feature merges, `develop` does not
  ignore `.turbo/cache/`, so runs in this worktree set `TURBO_CACHE_DIR` to
  the worktree's own `.turbo/cache`. The finish hook's verify writes to the
  shared folder moments before the merge brings the ignore rule.
- **Trust**: the local cache is not signed. Any process of the user can
  write to it, as it can to any worktree; a shared cache adds no writer that
  could not already change the code being verified.

## D8. Tests

`scripts/turbo-cache-test.ts` copies the working tree's tracked and
untracked files into a temporary Git repository, adds stand-ins for the
installed records, and compares `--dry=json` hashes through the real
`npm run turborepo` script before and after a change:

- a file outside a package (`scripts/doc_sources.py`) changes
  `doc-regions#test` and `//#lint`, not `backfire#test`;
- a workspace dependency's source changes its dependents' hashes, not
  unrelated packages';
- a new untracked file changes the root tasks;
- an ignored TypeScript file under `.local/` or a `coverage/` folder changes
  the checks that walk there, not `//#typecheck`;
- Turborepo's own task logs, at the root or in a package's `.turbo/`, change
  no hash;
- an edit to a package file in either npm tree, in `.venv` or in a tool
  environment, to a `.pth` file, to an entry-point script or to a tool's
  native program, a re-pointed launcher link and a changed permission each
  change every cached task;
- a different `git --version`, a different global Git configuration, a set
  `NODE_OPTIONS` and a set `UV_PYTHON` each change every cached task.

Hashes stand in for reruns because Turborepo looks results up by hash. Each
test fails when its declaration is removed (T004), and the log test fails
with the old `/.turbo/` rule. The tests take about 11 s of CPU per uncached
run.

## D9. Measurements

`npm run verify` on this worktree, one verify at a time on the machine, each
in `systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7`
(the four efficiency cores), timed with `/usr/bin/time`; CPU is user plus
system time of the whole process tree. Before: 1eef330's configuration and
files with this feature's Markdown records added. After: 1dfd2fb, with
`TURBO_CACHE_DIR` set to the worktree's own `.turbo/cache` (D7), emptied
before the cold run.

| Run | Wall | CPU | Replayed tasks | Result |
| --- | ---: | ---: | ---: | --- |
| Before, a full run | 230.6 s | 541.5 s | 0 of 37 | VERIFIED |
| Before, a repeat on the unchanged tree | 228.7 s | 545.1 s | 0 of 37 | VERIFIED |
| After, cold cache | 270.8 s | 583.7 s | 0 of 38 | VERIFIED |
| After, a repeat on the unchanged tree (warm) | 5.2 s | 10.0 s | 30 of 38 | VERIFIED |
| After a commit that changed only Markdown records (at 4da153c) | 49.6 s | 186.4 s | 5 of 38 | VERIFIED |

- A repeat verify on an unchanged tree now uses about 2% of the CPU time it
  used before (10.0 s against 545.1 s). Its 8 executed tasks are D5's six
  and the two grouping tasks.
- A cold run costs more CPU than before: 583.7 s here, against 545.1 s.
  The new tests take about 11 s, and the fingerprint and environment hashing
  about 1.3 s per Turborepo run. Cold runs at earlier commits of this feature
  measured 643.3 s (65d0ac9), 557.5 s (75c60d1) and 568.1 s (d7387f7); the
  spread was not analyzed.
- After an edit to files that only root tasks read, the five Python package
  tests replay and the root tasks rerun: in the last row, about a third of
  the CPU of a full run. Other worktrees replay the package tests whose
  packages they have not changed.

One base repeat failed in `doc-regions#test`, unrelated to caching: the
test's tree check counted a Git index refresh as a change (Linear CHE-75);
the next run passed.
