# CR3 review: the uv workspace and the Python packages

Reviewer: Claude Code (Opus 5.5), read-only, 2026-09-29. Scope:
`git diff 8ce9b2a 9d8af61` for the root `pyproject.toml`, `.python-version`
and `uv.lock`; the three members' `pyproject.toml`; `ready.py`, `build.py`,
doc-regions' `__main__.py` and `regions.py`; their changed tests; and the
Python members' tasks in `turbo.json`. One finding (F1) is in `package.json`,
outside the listed files; it was found while checking the repair command
that `ready.py` prints.

## Summary

FR-005, FR-006 and FR-013 hold. The root lock has the same 74 packages as the
union of `develop`'s three locks, with the newer version wherever they
differed and `typesafe-sdk` 0.7.1 as the recorded exception. Both built
plugins install offline, write nothing outside `.venv`, and pass the
installation part of readiness. All three test suites pass. The findings are
one documented command that now breaks the shared environment, one weakened
test, stale or false comments, and a few simplifications.

## Findings

### F1 (should-fix): `npm run backfire:install` uninstalls the other members from the shared `.venv`

- Evidence: `package.json:30` is still
  `uv sync --project packages/backfire --frozen --extra education`. In the
  workspace this syncs only backfire into the root `.venv`, exactly:
  `uv sync --project packages/backfire --frozen --offline --extra education --dry-run`
  (exit 0) prints "Would uninstall 32 packages", including `cogapp`,
  `bagit`, `pyyaml` and `wiki-consistency`. On `develop` the same command
  wrote only `packages/backfire/.venv`.
- Effect: `docs/backfire.md:20` tells users to run it first. Afterwards
  `test:doc-regions`, `test:wiki-consistency`, `doc-regions:check`, the
  doctor (`scripts/doctor.ts:168`) and readiness in the repository
  (`ready.py` checks `--all-packages`) fail until
  `npm run wiki-consistency:install` is run. D6 decides one root `.venv`
  synced with `--all-packages`; this site was selected
  (`selected-sites.md:51`) but only its runner changed.
- Resolution: make `backfire:install` run
  `uv sync --locked --all-packages --extra education`, the same command as
  the doctor's and readiness' repair text.

### F2 (should-fix): the build test no longer checks the built lock's content

- Evidence: `packages/backfire/tests/test_build.py:122-125` and `:163` take
  the expected `uv.lock` bytes from the built output itself, and `:143`
  skips its mode check. On `develop` the copied lock was compared byte for
  byte with the source lock. No other test reads a built lock
  (`grep -rn 'uv\.lock\|lock_copy\|uv export' packages/*/tests` finds only
  `test_build.py`).
- Effect: if `lock_copy` (`build.py:34-92`) dropped or mis-wrote the pins,
  `uv lock --offline` would resolve whatever the cache holds and the test
  would still pass. D7's promise (same versions as the root lock) is
  untested. The versions are right today: comparing the built locks with
  `develop` shows only the FR-013 upgrades for backfire and the
  `typesafe-sdk` 0.7.1 exception for wiki-consistency.
- Resolution: in the test, compare each built lock's `name`/`version` pairs
  with the root lock's (or with `uv export --package <p> --frozen` output),
  instead of with the built file itself.

### F3 (should-fix): doc-regions' separator comment is false under npm; the workaround is dead

- Evidence: `packages/doc-regions/src/doc_regions/__main__.py:25` says
  "npm run forwards a second separator after the positional config path."
  npm drops the first `--`: with a script
  `python3 -c "import sys;print(sys.argv[1:])" prepare cfg.toml`,
  `npm run -s p -- --base develop` printed
  `['prepare', 'cfg.toml', '--base', 'develop']` (exit 0). A `--` arrives
  only if the user types `-- --`. The documented call
  (`docs/architecture.md:577`, `scripts/workflow_test.ts:460`) is
  `npm run doc-regions:prepare -- --base develop ...`, so lines 26-27 never
  run. The test that covers them is still named
  `test_cli_accepts_deno_task_separator`
  (`packages/doc-regions/tests/test_requests.py:372`).
- Resolution: either fix the comment to say the branch tolerates a typed
  extra `--`, or remove lines 25-27 with that test, since the Deno behavior
  they served is gone (FR-011).

### F4 (should-fix): comments about install metadata now describe removed settings

- Evidence: `packages/backfire/pyproject.toml:29`,
  `packages/doc-regions/pyproject.toml:23` and
  `packages/wiki-consistency/pyproject.toml:30` still say "Keep install
  metadata inside .venv", which described `egg_base = ".venv"`. They now sit
  above `[tool.uv.build-backend]`, which selects modules and does not place
  metadata (D6: `uv_build` writes nothing outside `.venv` by itself).
- Resolution: delete the three comments, or reword them to say which
  modules the table selects.

### F5 (note): `ready.py` rebuilds uv's workspace discovery from the path

- Evidence: `_project_root` (`ready.py:186-193`) treats `_ROOT` as a member
  when its parent is named `packages` and the grandparent has a
  `pyproject.toml`. uv already answers this: `uv workspace dir --project
  packages/backfire --offline` printed the repository root (exit 0), and in
  a built copy it printed the copy (exit 0). `--all-packages` also works
  outside a workspace: `uv sync --check --frozen --offline --all-packages
  --no-dev` in the built code copy printed "Would make no changes" (exit 0),
  so the `workspace` switch at `ready.py:157` is not needed for the sync
  check.
- Effect: small; the heuristic misfires only if a plugin is built into a
  directory named `packages` whose parent has a `pyproject.toml`. The
  message at `ready.py:115`, "this component's .venv", is inaccurate in the
  workspace, where it is the repository's `.venv`.
- Resolution: optional. Pass `--all-packages` always, and take the
  environment root from `uv workspace dir` if the extra subprocess call is
  acceptable.

### F6 (note): built copies' `uv.lock` does not match their `pyproject.toml`

- Evidence: `lock_copy` writes the exported pins into the copy's
  `pyproject.toml`, runs `uv lock --offline`, then restores the file
  (`build.py:66-92`). The lock's `[manifest] constraints` therefore lists
  pins the restored file lacks, and `uv lock --check --offline` fails with
  "The lockfile at `uv.lock` needs to be updated" (exit 1) in all four built
  projects. The documented install and start commands use `--frozen`
  (`plugins/work/skills/wiki-consistency/SKILL.md:27-35`, the built
  `mcp.json`), so they work: `uv sync --frozen --no-dev --offline` exited 0
  in each copy.
- Resolution: optional. Keep the written constraints in the copy (drop the
  restore and its `try`/`finally`), so the lock and the file agree and the
  code is shorter. Not tested here.

### F7 (note): research D10 names one replaced source; the code replaces two

- Evidence: `specs/019-turborepo/research.md:136-138` says only
  `doc-regions = { workspace = true }` is replaced in the copied
  wiki-consistency `pyproject.toml`; `build.py:240-255` replaces both
  `doc-regions` and `backfire`, which is needed because
  `packages/wiki-consistency/pyproject.toml:27` makes backfire a workspace
  source too. The result matches `develop`'s path sources.
- Resolution: update D10's wording.

### F8 (note): root constraints beyond the recorded exception carry no reason

- Evidence: root `pyproject.toml:2-10` pins `starlette`, `openai`, `pyjwt`
  and `sse-starlette` with `==` and caps `magika<=0.6.3`. FR-013 needs only
  the `typesafe-sdk` constraint at the root (member constraints are
  ignored); the other versions are already held by `uv.lock`, since
  `uv lock` keeps locked versions unless asked to upgrade. As written they
  also make a later `uv lock --upgrade` silently keep these five packages.
- Resolution: add a one-line comment pointing to FR-013 for each group, or
  keep only `typesafe-sdk==0.7.1`.

### F9 (note): member test commands are defined twice and lost their setup hint

- Evidence: `turbo.json:48-126` repeats the `uv run ... pytest` commands
  from `package.json:33-41`. `develop`'s `test:backfire`,
  `test:doc-regions` and `test:wiki-consistency` first checked for the
  environment and printed which install command to run
  (`git show 8ce9b2a:deno.json`, lines 33, 52, 53); neither copy does now,
  so a missing environment fails with uv's own error. The doctor still names
  the repair (`scripts/doctor.ts:168`).
- Resolution: optional. Let one definition call the other (for example the
  npm scripts run `turbo run test --filter=<member>`).

## Confirmed without findings

- FR-005: one root workspace (`pyproject.toml:12-13`), one committed lock
  (`uv lock --check --offline`, exit 0, "Resolved 78 packages"), the member
  locks are deleted, and the root has a Turborepo name
  (`pyproject.toml:15-16`).
- FR-013: the root lock has 74 packages, the same set as `develop`'s three
  locks; the only version differences are openai 3.20.0, pyjwt 2.15.1,
  sse-starlette 3.5.0, starlette 1.7.0 (the newer ones) and typesafe-sdk
  0.7.1 (the recorded exception). `magika` keeps `develop`'s 0.6.2/0.6.3
  split.
- FR-006: both plugins build; each copied project installs offline with
  `--frozen --no-dev`, adds no file outside `.venv`, and
  `_installation_problem` returns `None` in both backfire copies and in the
  repository. The `uv_build` modules match the copied sources
  (`["backfire"]` for code, `["backfire", "backfire_education"]` for work).
- The `deno task` to `npm run` text changes in `regions.py`,
  `test_regions.py`, `test_load.py`, `test_education_e2e.py` and
  `build.py:280` are one-for-one.
- The work-plugin test gained an `npm ci` and an import check that the copy
  loads its own backfire (`test_build.py:295-337`); `--offline` moved to
  `UV_OFFLINE=1` without loss.

## Commands run

| Command | Exit |
| --- | --- |
| `npm run test:doc-regions` (107 passed) | 0 |
| `npm run test:wiki-consistency` (263 passed) | 0 |
| `npm run test:backfire` (1364 passed, 3 deselected) | 0 |
| `npm run backfire:build -- code <scratch>/b/code` | 0 |
| `npm run backfire:build -- work <scratch>/b/work` | 0 |
| `uv sync --frozen --no-dev --offline [--extra education]` in each of the 4 built projects | 0 |
| `uv lock --check --offline` in each of the 4 built projects | 1 |
| `uv lock --check --offline` at the repository root | 0 |
| `_installation_problem(_versions())` in both built backfire copies and the repository | 0 (returns `None`) |
| `uv sync --project packages/backfire --frozen --offline --extra education --dry-run` | 0 (would uninstall 32) |
| `uv sync --check --frozen --offline --all-packages --no-dev` in the built code copy | 0 |
| `uv sync --project packages/backfire --check --frozen --offline --all-packages --extra education` | 0 |
| `uv workspace dir --project packages/backfire --offline`; `uv workspace dir --offline` in the code copy | 0; 0 |
| `npm run -s p -- --base develop` and `npm run -s p -- -- --base develop` in a scratch package | 0; 0 |
| Lock comparison script (`tomllib`) over the root lock, `develop`'s three locks and the 4 built locks | 0 |
| `git status --porcelain` before and after the runs (empty) | 0 |
