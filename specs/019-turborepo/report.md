# Trial report: Turborepo, Node.js and a uv workspace (CHE-32)

**Branch**: `feature/turborepo`, based on `develop` at `3627cb2`. **Date**:
2026-09-29. **Status**: the trial works on its branch; it is not merged, and
merging is the user's decision.

## Result

`npm run check` runs `turbo run check`, which runs the same 11 checks and 14
test suites as `deno task check` at the base commit. It passed on the branch,
in 1 min 30 s and 1 min 34 s against 1 min 52 s and 1 min 54 s for `deno task
check` at the base commit, measured on the same idle machine. The TypeScript
tooling runs on Node.js 24.19; `backfire`, `doc-regions` and
`wiki-consistency` are one uv workspace with one root `uv.lock`, and
Turborepo's experimental Python support runs their tests. `deno task
verify` and `npm run verify` finish `VERIFIED`. Deno is still needed for
the shipped clean-code skill (D5). The branch has three commits on top of
the records: `54f7937` (implementation), `231bba2` (documents) and
`f1e1ab0` (workflow permission fix).

## What changed

- 63 files changed outside `specs/019-turborepo/`: 6,712 lines added and
  4,244 removed. Without lock files and the generated `docs/reference/`,
  56 files: 1,949 added and 1,112 removed (`git diff --shortstat 3627cb2`).
- New: `package.json`, `package-lock.json`, `.npmrc`, `turbo.json`,
  `tsconfig.json`, `scripts/deno_shim.ts` (the preload), root
  `pyproject.toml`, `.python-version` and `uv.lock`, and
  `scripts/cli_contract_test.ts.snapshot`.
- Removed: `deno.lock`, the three `packages/*/uv.lock` files and
  `scripts/__snapshots__/cli_contract_test.ts.snap`. The root `deno.json`
  keeps only `compilerOptions`, whose classification was `review`.
- Changed: 10 TypeScript scripts, the evidence schema and 14 test files under
  `scripts/`, the two
  hooks, `orca.yaml`, the three GitHub workflows, the three Python packages'
  `pyproject.toml`, `ready.py`, `build.py`, `regions.py`, five backfire and doc-regions
  test files, the clean-code CLI's one non-erasable constructor, and the
  selected lines of `docs/architecture.md` and `docs/backfire.md`.
- Locally owned code and tooling configuration (non-blank lines, method
  below): 27,666 lines in 176 files before, 28,555 in 182 files after
  (+889). New configuration accounts for 313 lines (`turbo.json` 181,
  `package.json` 80, `tsconfig.json` 19, the preload 17, root `pyproject.toml`
  14, `.npmrc` 2). Most of the rest is the `node:child_process` code that
  replaced `Deno.Command`: six non-test scripts each carry their own
  promise wrapper of about 25 lines (for example
  `scripts/workflow_git.ts:9-43`), and `build.py` gained 66 lines to lock the
  built plugin copies (D7, D10).

## What backfire selected and what it left alone

- Candidates, 378 rows in 18 classification batches: 253 in the first
  (exact `rg` matches grouped by file and kind, `deno.json` split per task,
  and 8 hits of the `backfire_find` search by meaning over 592 TypeScript
  and configuration chunks); 68 in the second (hits of two searches over
  1,375 Python chunks, 14 whole-file rows for lock, version and build
  settings, two non-erasable TypeScript constructs, and the commit-msg hook,
  which `rg` missed); 21 late search hits; and 36 rows split or raised later
  by workers, test runs and the review with failing evidence ([evidence/classify.json](evidence/classify.json),
  [evidence/selected-sites.md](evidence/selected-sites.md)).
- Selected (`must_change` or `delete` with an `auto` decision): 205 rows.
  Left alone: 173 rows: 132 `can_stay`, one `manual_review` (`AGENTS.md`)
  and 40 with a `review` decision; two of those, S095 and S150, were later
  split and classified again with new evidence.
- Left unchanged although they now read wrongly (`review` rows, open
  questions): the root `deno.json` `compilerOptions`; the comments
  "Keep install metadata inside .venv" above the new `uv_build` tables in the
  three `pyproject.toml` files; the message "run deno task clean-code:scope"
  in `scripts/workflow_skills.ts` (S121); `biome.json`'s `!**/deno.lock`
  (S146); backfire's own `constraint-dependencies` line; the per-package
  `.python-version` files; and `plugins/code/deno.json`. Deno's `deno task`
  also runs `package.json` scripts, so the old commands still work.
- Not in any candidate list, found by running the checks: Node 24.19 has no
  `Uint8Array.prototype.toHex`/`fromHex` (D14), `@std/testing/snapshot`
  cannot load its `.snap` file on Node (D15), Node rounds file modification
  times to the millisecond where Deno truncated (a test failed about half
  the time), and the shim answers every `Deno.permissions.query` with
  `granted`. Each was classified with its failing evidence before any change.
- The fresh Codex review of the coordinator's own edits (R1,
  [evidence/review-R1.md](evidence/review-R1.md)) found one should-fix: four
  `docs/architecture.md` lines (row S150, `review`) still named the deleted
  `deno.lock`. Classified again with that evidence, they became must-change
  (0.93 to 0.96) and now name `package.json` and `package-lock.json`.
- Also stale but never a candidate: `README.md` and `AGENTS.md` still begin
  "A personal Deno workspace"; the searches covered code and configuration,
  not those two files' prose.
- Wrong judgments seen: backfire marked three `docs.ts` hex sites `can_stay`
  at 0.93 although the method does not exist on Node, and chose them only
  when the measured TypeErrors were added. The catalog context of the first
  batch also contained an error of mine (it said `Deno.execPath()` returns
  Node under the shim; it returns the `deno` on PATH); that error could only
  mark sites for change that did not need one.

## Design decisions (backfire_decide)

Fifteen decisions, all recorded in [research.md](research.md) and
`evidence/decide-d*.json`; none escaped to the user. Selected: the shim
preload plus targeted rewrites (D1, 0.88), Node's type stripping (D2, 0.88),
Prettier for YAML (D3, 0.86), Node's permission model (D4, 0.85), the
clean-code skill kept on Deno (D5, 0.82), `uv_build` with one root `.venv`
(D6, 0.80), a lock generated inside each built plugin copy (D7, 0.88; D10,
0.86), no caching for tasks that read outside their package (D8, 0.50 over
0.30, confidence 0.40), npm scripts as entry points (D9, 0.70), a preload
bridge for `exitCode` and stubs (D11, 0.90), `proper-lockfile` for file
locks (D12, 0.85), an npm `workspaces` glob that matches nothing (D13, 0.91),
Buffer hex conversion (D14, 0.86) and node:test snapshots (D15, 0.72).

## Check results

| Check | Base (`deno task check`) | Trial (`npm run check`) |
| --- | --- | --- |
| Whole check | passed | passed: 26 of 26 Turborepo tasks |
| doctor, format, lint, shell lint, type check, plugin validation, clean-code, clean-architecture, docs, doc-regions | passed | passed |
| TypeScript suites | 213 tests passed | 213 tests passed |
| backfire (not slow) | 1,351 passed, 3 deselected | 1,355 passed, 3 deselected |
| doc-regions with `scripts/doc_sources_test.py` | 107 passed | 107 passed |
| wiki-consistency | 169 passed | 169 passed |

`deno task verify --task che-32-trial` and `npm run verify` both finished
`VERIFIED` with exit code 0 on the committed branch; `deno task` still
works because Deno runs the root `package.json` scripts. The first verify
failed: Node adds a parent's permission grants to its children, so the
checks started by the permission-restricted workflow inherited its grants
and the tests of denied permissions failed. The workflow script now runs
without Node's permission model; its Deno task granted every scope it
listed, so no scope Deno enforced is lost (commit `f1e1ab0`).

`backfire_gate` on the final diff ([evidence/gate.json](evidence/gate.json))
verified all nine completion claims against the logs (eight `auto`; the
claim that `AGENTS.md` and the constitution are unchanged at 0.62, `review`),
and its patch review escalated (composite 0.72, safe to apply 0.22, test
coverage the weakest score). The gate saw the first 50,000 of 213,435
characters of the diff.

The TypeScript suites are clean-architecture 4, clean-code 35, CLI contract
14, commit-msg 5, docs 14, doctor 16, git-flow 20, plugin skills 3,
wiki-raw-import 43, workflow 56 and worktree-branch 3. Run separately on the
branch: `test_load.py` 1, `test_ready.py` 11, `test_entry.py` 4 and
`test_build.py` 32, 48 passed; `npm run test:doctor` 16 of 16; `npm run
doctor` reports PASS. Backfire's non-slow count grew by 4 because two
`test_ready.py` tests gained a `workspace` parameter (T002). The logs are in
[evidence/](evidence/).

## Check time

| Run | Wall clock | User CPU |
| --- | --- | --- |
| Base, first run (other work running) | 2:09.59 | 372.6 s |
| Base, idle, run 2 | 1:51.56 | 340.7 s |
| Base, idle, run 3 | 1:54.25 | 334.2 s |
| Trial, idle, run 1 | 1:29.92 | 363.9 s |
| Trial, idle, run 2 | 1:33.69 | 374.9 s |

The trial is about 20 s (18 %) faster in wall-clock time and uses about 10 %
more CPU time. No task is cached (D8), so a second run is not faster.

## What still depends on Deno

- The shipped clean-code skill: its `deno.json` and `deno.lock`, the
  `clean-code`, `clean-code:scope` and `test:clean-code` scripts, the
  copied-skill contract tests, the help collection in `scripts/docs.ts`, the
  doctor's Deno 2.9.6 check, the Deno install in `orca.yaml` and the
  workflows, and the clean-code `deno audit` step.
- The Deno API through `@deno/shim-deno` on Node: 519 `Deno.*` references in
  32 files remain, 30 of them in the skill.
- `deno.json` with only `compilerOptions` and `plugins/code/deno.json`
  (review rows).

## Open risks

- **Merge base**: `develop` has moved to `8ce9b2a` (CHE-29 Ruff and CHE-26
  vault rule checks merged). 17 files changed on both sides, including
  `deno.json`, `orca.yaml`, the three `pyproject.toml` files, `build.py` and
  its tests, and the doctor. A merge would need the selection redone on the
  new base, because both features changed sites the classification covered.
- **Permissions**: Node cannot express Deno's environment-variable and
  program allow-lists (T001's report lists them per task), `fs.symlink` needs
  unscoped read and write, child processes inherit the permission model and
  add the parent's grants to their own, and `--allow-child-process` lets a
  child run without restrictions. The narrow scopes are therefore weaker than
  Deno's, and the workflow script runs without the permission model.
- **Experimental and unusual pieces**: Turborepo's Python support and task
  `command` are experimental; the `workspaces` glob matches nothing on
  purpose; Turborepo writes an agent-guidance block into `AGENTS.md` unless
  `agentGuidance` is false.
- **Dependencies**: `@deno/shim-deno` lacks `Deno.Command`, `exitCode` and
  file locks, and its `permissions.query` always answers `granted`;
  `proper-lockfile` was last published in 2022; JSR packages come through
  npm's `allow-remote=root`.
- **Behavior differences**: `workflow --help` prints its defaults with single
  quotes ('workspace', 'HEAD'); `npm run doctor` and other scripts print
  Node's `SecurityWarning` on stderr outside the two silenced test scripts;
  the built plugin's `uv.lock` records constraints its `pyproject.toml` no
  longer lists, so `uv lock --check` fails there (installs use `--frozen`).
- **Reviews**: `backfire_review` returned `escalate` for every patch (T001
  0.70, T002 0.69, T003 0.68, T004 0.54 and 0.81, T005 0.84 and 0.73), with
  test coverage the weakest score. The coordinator read each diff; a human
  or a fresh reviewer should review before any merge. The GitHub workflows
  were changed but not run.

## Governance wording for the user

`AGENTS.md` and the constitution were not changed. If the user adopts the
trial:

- `AGENTS.md`, "Workflow and verification": replace `deno task workflow` with
  `npm run workflow` and `deno task verify` with `npm run verify`.
- `AGENTS.md`, first paragraph: "A personal Deno workspace" becomes "A
  personal workspace".
- Constitution, "Development Workflow and Quality Gates": "Follow the
  existing `npm run workflow` execution instructions" and "the feature passes
  `npm run verify`".
- Constitution IX: confirm that Turborepo as a development task runner does
  not conflict with "Do not require one repository-wide runtime, server or
  composition entry point", and that "A package joins a toolchain workspace
  ... only when it has executable code for that toolchain" allows the uv
  workspace of the three Python packages.

## Verification of this report

`backfire_verify` checked 13 of this report's claims against the logs and
command output ([evidence/verify-report.json](evidence/verify-report.json)).
Eleven were verified. Two diff sizes were contradicted, because they were
counted before the last two edits; they are corrected above, and a second
round verified one and left the other `unsupported` (0.55), because the
evidence text did not name the path exclusion.

## Method

Locally owned code was counted as the non-blank lines of tracked and new
`.ts`, `.mjs`, `.js`, `.py`, `.sh`, `.json`, `.toml` and YAML files and the
two hook scripts, excluding `specs/`, `.specify/`, `licenses/`, `docs/`,
fixtures, snapshots, `scripts/vendor/`, the upstream ponytail hooks and their
test, lock files, `UPSTREAM` files, `.codex/`, `.claude/`, the Quarto skill,
`tools/spec-kit/` and JSON schemas. Times come from `/usr/bin/time -v`; the
base runs used a temporary detached worktree at `3627cb2`, removed
afterwards. Backfire ran from `packages/backfire` through a local MCP client
(`deepseek-ai/deepseek-v4.1-flash` on Hive); provider errors were retried,
and one of 35 batches of the search for code that reads outside its package
never succeeded. Codex workers on `gpt-6-luna` at `max` implemented T001 to
T005 and their follow-ups through Orca Run `run_d06084761156`; their reports
are `evidence/worker-T00*.md`.
