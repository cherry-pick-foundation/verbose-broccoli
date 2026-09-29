# Report: Turborepo, Node.js and a uv workspace (CHE-32)

**Branch**: `feature/turborepo`, with `develop` merged up to `f444287`.
**Date**: 2026-09-29. **Status**: ready to finish into `develop` after the
last reviews. The work began as a trial; on 2026-09-29 the user made it the
real change (see [spec.md](spec.md)).

## Result

Deno is gone from the repository. The TypeScript scripts, tests, hooks and
the shipped clean-code skill run on Node.js; Turborepo 2.11.5 runs the
checks; `backfire`, `doc-regions` and `wiki-consistency` form one uv
workspace with one root `uv.lock`. `npm run check` runs `turbo run check`
and passed all 27 Turborepo tasks. `npm run verify` finished `VERIFIED` on
the merged tree with the `deno` executable removed from `PATH`
([evidence/logs/verify-final.json](evidence/logs/verify-final.json)).
Check time is about the same as `develop`'s; CPU time is about 13 % higher.

## What users of the clean-code skill must install

- Node.js 24.12.0 or later: the scripts use TypeScript type stripping
  (stable in 24.12.0), `import.meta.main` (24.2.0) and `fs.glob` (24.0.0).
  The skill's `package.json` states the same floor in `engines`.
- Its npm packages, once, from the target workspace root:
  `npm ci --prefix <skill-root> --prefer-offline --ignore-scripts --no-audit --no-fund`.
  The skill's `.npmrc` takes the JSR packages from `npm.jsr.io`
  (`allow-remote=root` is needed by npm 12). This was tested with npm 12.1.0
  only.
- Then `node <skill-root>/scripts/clean_code.ts --scope` before a review, and
  the same command without `--scope` after changes (`SKILL.md`).

## What changed

- 86 files changed against `develop` `f444287` outside `specs/`: 11,646
  lines added and 7,384 removed. Without lock files, the generated
  `docs/reference/` and the CLI snapshot: 74 files, 3,358 added and 2,037
  removed (`git diff --no-renames --numstat f444287 HEAD`; the per-file
  list is [evidence/logs/numstat-f444287.txt](evidence/logs/numstat-f444287.txt)).
- New: the root `package.json`, `package-lock.json`, `.npmrc`, `turbo.json`,
  `tsconfig.json`, `pyproject.toml` and `.python-version`; the skill's
  `package.json`, `package-lock.json` and `.npmrc`; `plugins/code/package.json`
  (D18); and `scripts/cli_contract_test.ts.snapshot`.
- Removed: `deno.json`, `deno.lock`, `plugins/code/deno.json`, the skill's
  `deno.json` and `deno.lock`, the three per-package `uv.lock` files (now one
  root `uv.lock`) and the Deno snapshot file. The trial's `@deno/shim-deno`
  preload was added and removed again.
- Changed: every script, test and hook that called Deno, `orca.yaml`, the
  three GitHub workflows, `biome.json`, `.gitignore`, the three packages'
  `pyproject.toml`, `ready.py`, `build.py` and their tests, the prose in
  `AGENTS.md`, the constitution, `README.md` and the guides.
- Locally owned code and tooling configuration (non-blank lines, method
  below): 39,854 lines in 181 files on `develop`, 41,130 in 184 files on the
  branch (+1,276). New configuration is 334 lines (`turbo.json` 182, root
  `package.json` 82, `tsconfig.json` 35, the skill's `package.json` 17, root
  `pyproject.toml` 12, `plugins/code/package.json` 6), and 144 lines of Deno
  configuration went. The largest growth is in `docs_test.ts` (+143),
  `doctor_test.ts` (+139), `build.py` (+102), `doctor.ts` (+92) and
  `test_build.py` (+91).

## What backfire selected and what it left alone

- **Trial** (base `3627cb2`): 378 candidate rows in 18 classification
  batches; 205 selected, 173 left alone
  ([evidence/selected-sites.md](evidence/selected-sites.md)).
- **Full removal** (after the `develop` merge, batches 20 to 23): 193 rows;
  184 selected by backfire (`must_change` or `delete`, `auto`), 5 selected
  by the user's rule of no Deno anywhere after staying `review`, and 4 left
  ([evidence/selected-sites-full-removal.md](evidence/selected-sites-full-removal.md)).
  The two `AGENTS.md` rows (`manual_review`) became the governance step the
  user approved; two test fixture rows stay as they are (below). Batch 23
  added one README command that the searches had skipped (X169).
- **Final review findings** (batch 24): 26 findings; 12 fixed, 3 sent to a
  decision (D19 to D21) and 11 not changed in code, one of them an open
  question; batch 25 then classified the last round's five code
  findings (two fixed, three left)
  ([evidence/review-findings.md](evidence/review-findings.md)).
- Wrong or weak judgments seen: in the trial, backfire marked three hex
  sites `can_stay` at 0.93 although the method does not exist on Node. Its
  patch reviews escalated most patches with low confidence on test
  coverage; the coordinator checked those points by hand
  ([evidence/review-T010.json](evidence/review-T010.json) records one such
  check).

## Design decisions (backfire_decide)

Twenty-one decisions, recorded in [research.md](research.md) and
`evidence/decide-d*.json`; none escaped to the user. The trial's D1 to D15
are listed there. The real change added: the clean-code skill on Node with
its own npm files (D16, superseding D5); the constitution change as a minor
version, which the user confirmed (D17); the import-boundary check reading
`package.json` (D18, 0.85); a doctor floor of Node.js 24.12 (D19, 0.80); only
the needed root uv constraints (D20, 0.70); and the root lock standing in for
the skill's lock in the repository's own checks (D21, 0.68).

## Check results

| Check | `develop` (`deno task check`) | Branch (`npm run check`) |
| --- | --- | --- |
| Whole check | passed | passed: 27 of 27 Turborepo tasks |
| doctor, format, lint, shell lint, type check, plugin validation, clean-code, clean-architecture, docs, doc-regions | passed | passed |
| TypeScript suites | passed | 229 tests passed |
| backfire (not slow) | passed | 1,364 passed, 3 deselected |
| doc-regions with `scripts/doc_sources_test.py` | passed | 106 passed |
| wiki-consistency | passed | 291 passed |

The TypeScript suites on the branch are clean-architecture 5, clean-code
35, CLI contract 16, commit-msg 6, docs 16, doctor 20, git-flow 21, plugin
skills 3, Ruff 1, wiki-raw-import 44, workflow 58 and worktree-branch 4. The
final review found each converted suite with the same test registrations as
on `develop`; the review fixes then added cases. doc-regions has one test
fewer, because the fixes removed a branch that served only `deno task`.
The type check now also covers every test file, which `deno test` used to
check and `node --test` does not. The slow backfire tests (3) and
`test_load`, `test_ready` and `test_entry` (16) passed on the new Python
versions.

Locked Python versions: the root lock has the same 74 third-party packages
as `develop`'s three locks. Four are the newer versions `develop` had in one of
them (openai 3.20.0, starlette 1.7.0, pyjwt 2.15.1, sse-starlette 3.5.0).
`typesafe-sdk` stays 0.7.1, because backfire's version test fails at 0.7.2
(the FR-013 exception in [spec.md](spec.md)).

## Check time

| Run (same machine, idle) | Wall clock | User CPU |
| --- | --- | --- |
| `develop` `f444287`, `deno task check`, run 1 | 2:19.25 | 394.6 s |
| `develop` `f444287`, `deno task check`, run 2 | 2:16.91 | 376.1 s |
| Branch, `npm run check`, run 1 | 2:19.68 | 436.4 s |
| Branch, `npm run check`, run 2 | 2:22.35 | 434.6 s |

The branch is about 3 s (2 %) slower in wall-clock time and uses about 13 %
more CPU time ([evidence/logs/](evidence/logs/)). The trial was 18 % faster
than its base, before Ruff, the test-file type check and the review fixes
were added. No task is cached (D8).

## Reviews

- Fresh Codex reviews of the coordinator's own work: R1 of its trial edits
  and R2 of its conflict resolution in the first `develop` merge. The second
  merge (`f444287`) had no conflicts.
- `backfire_review` of every patch. The coordinator read every diff and sent
  follow-up tasks to three workers for problems it found, among them two
  assertions that checked nothing and a dropped test of the doctor's
  permission denials.
- Final reviews of `9d8af61`: three fresh Claude Code reviewers for the
  Codex-written code (CR1 to CR3, Opus 5.5 at high effort) and one fresh
  Codex reviewer for the coordinator's changes (R3). They found no blocker,
  15 should-fix findings and 18 notes. The fixes went in `b795b61`, among
  them `backfire:install` removing the other packages from the shared
  `.venv`, a guard that never fired, review routing that missed the new
  tooling files, and a build test that compared a lock with itself.
- A last round on the fixes and the second merge: a fresh Claude Code
  reviewer (CR4) for the fix commit and a fresh Codex reviewer (R4) for the
  coordinator's report and records. CR4 found that the fix for installed IO
  packages never fired, because the import graph skipped `node_modules`;
  backfire batch 25 selected it and one stale doc line, and `5405399` fixed
  both. R4's findings were in this report (per-file counts, the overlaps
  section) and the task ledger, and are resolved here.

## Permissions lost compared with Deno

The user accepted Node's weaker permission model (D4). What is lost:

- **Environment variables**: Node has no scope for them, so Deno's
  `--allow-env=<names>` lists are gone.
- **Programs**: `--allow-child-process` lets a script start any program,
  where Deno allowed only the named ones (`--allow-run=git,uv`).
- **Network**: Node 24.19 has no network permission, so help collection in
  `scripts/docs.ts` and the tests can reach the network; `develop` checked
  that it could not.
- **Scoped writes**: `fs.symlink` needs unscoped reads and writes, so
  `test:git-flow` and `test:clean-code` write anywhere where Deno allowed
  `/tmp` only.
- **Children**: permission flags reach child Node processes through
  `NODE_OPTIONS`, and grants add up, so a narrow scope holds only for the
  first process. The workflow script and several test children run without
  the permission model.
- **The skill**: Deno granted read and environment access only; the
  repository's `clean-code` script grants all reads, and the users' command
  runs without the permission model.

## What still names Deno

Nothing requires or invokes Deno (FR-011). The word remains in dated
history in `specs/` and the constitution, in two test fixture strings
(`Deno.FileInfo` source text in `scripts/workflow_graph_test.ts` and a
`.deno/cache` path in `scripts/workflow_plan_test.ts`, rows X032 and X146),
and in the code and test that skip Deno-era workflow evidence records
(`scripts/workflow_verify.ts`, `scripts/workflow_verify_test.ts`).

## Open risks and leftovers

- **A flaky test**: backfire's bounded-work test for `backfire_extract`
  failed once in the full checks run since the shim was removed, and passed
  on the rerun and in three runs alone. Under full parallel load its 10 MB regex scan can pass its
  deadline, and the tool then reports no judgment.
- **Not run**: the GitHub workflows were changed but cannot run locally.
- **Experimental and unusual pieces**: Turborepo's Python support and its
  task `command` arrays are experimental; the npm `workspaces` glob matches
  nothing on purpose (D13); `agentGuidance` must stay false, or Turborepo
  writes into `AGENTS.md`.
- **Dependencies**: `proper-lockfile` was last published in 2022, and its
  locks give up after ten minutes where Deno's waited without a limit (D12).
  The repository checks the skill with the root lock, which differs from
  the skill's own lock in five transitive versions (D21).
- **Behavior**: `npm run doctor` and other scripts that may start programs
  print Node's `SecurityWarning` on stderr; built plugin copies fail
  `uv lock --check` because their lock records constraints their
  `pyproject.toml` no longer lists (installs use `--frozen` and work).
- **Review findings left as they are** (classified `can_stay`): six copies
  of an `execFile` wrapper and a repeated test helper; the Python test
  commands defined in both `package.json` and `turbo.json`; a path heuristic
  in `ready.py`; a test name that still says help cannot use the network;
  a doctor test name that says doc-regions; the copied-skill test's
  `--prefer-offline`; and Biome no longer denying the `Deno` global in
  domain code (removed by the user's rule).
- **Open question**: `docs/architecture.md` says only the skill has its own
  npm manifest, but `plugins/code/package.json` (D18) is a second one; backfire
  marked it `must_change` with a `review` decision (0.75), so it stays for
  the user to decide.
- **After the finish**: the `develop` worktree needs the new setup (root
  `npm ci`, the uv workspace sync and the tools), which `orca.yaml` runs.

## Overlaps with other features

Three features reached `develop` while this one was open; the two merges
brought them in.

- **CHE-29, Python lint with Ruff** (`develop` `8ce9b2a`): `ruff.toml`,
  `tools/ruff`, Ruff steps in the Deno `lint` and `format` tasks, a
  `test:ruff` suite (`scripts/ruff_test.ts`) and a Ruff environment check in
  the doctor. This feature moved the Ruff steps and `test:ruff` into npm
  scripts and the Turborepo graph, converted `scripts/ruff_test.ts` to
  `node:test`, kept the doctor's Ruff check, and fixed the seven Ruff
  findings in code this feature had added.
- **CHE-26, vault rule checks** (`develop` `07ebf47`): new rules and tests in
  `wiki-consistency`, a dependency of `wiki-consistency` on
  `backfire[education]`, and new install steps in the work plugin's
  `wiki-consistency` skill. In the uv workspace that dependency is a
  workspace source, so the plugin build now rewrites both it and
  `doc-regions` in the copied project (D10), and the root lock takes the
  newer versions `wiki-consistency`'s lock had (FR-013).
- **CHE-35, vault link targets** (`develop` `f444287`): `wiki-consistency`
  code, tests and prose only. It merged without conflicts and needed no
  change here.

## Governance

The user approved the wording on 2026-09-29, and it is applied: `AGENTS.md`
names `npm run workflow` and `npm run verify` and no longer says "Deno
workspace" (`d5eb6be`); the constitution goes from 2.1.0 to 2.2.0 as a minor
change, which the user confirmed is not breaking (`b1f8fff`, D17). Principle
IX's "Do not require one repository-wide runtime, server or composition
entry point" stays unchanged.

## Verification of this report

`backfire_verify` checked 14 of this report's claims against the logs and
command output, and verified all 14
([evidence/verify-report-final.json](evidence/verify-report-final.json)).
`backfire_gate` verified eight completion claims (seven `auto`; the claim
that nothing outside the records names Deno at 0.78, `review`). Its patch
review escalated (safe to apply 0.14, with low confidence), because it saw
only the tooling and removal part of the diff
([evidence/gate-final.json](evidence/gate-final.json)); the rest had its
own patch reviews and the final reviews. A second round checked the nine
claims added or changed after the last reviews
([evidence/verify-report-final-2.json](evidence/verify-report-final-2.json)):
eight verified at once; the CHE-26 claim was contradicted on thin evidence
and verified when the full diffs were supplied.

## Method

Locally owned code was counted as the non-blank lines of tracked `.ts`,
`.mjs`, `.js`, `.py`, `.sh`, `.json`, `.toml` and YAML files and the hook
scripts, without `specs/`, `.specify/`, `licenses/`, `docs/`, fixtures,
snapshots, `scripts/vendor/`, the upstream ponytail hooks and their test,
lock files, `UPSTREAM` files, `.codex/`, `.claude/`, the Quarto skill,
`tools/spec-kit/` and JSON schemas. Times come from `/usr/bin/time -v` with
the base in a temporary detached worktree at `f444287`, removed afterwards.
Backfire ran from `packages/backfire` through a local MCP (Model Context
Protocol) client script on `deepseek-ai/deepseek-v4.1-flash`; provider errors
were retried. Codex workers on `gpt-6-luna` at `max` implemented every task
through Orca; their specs and reports are in
[evidence/method/specs/](evidence/method/specs/) and `evidence/worker-*.md`.
