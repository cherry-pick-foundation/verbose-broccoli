# CHE-32 final review CR4: the review-fix commit and the second develop merge

Reviewer: Claude Code (Opus 5.5), read-only. Branch `feature/turborepo` at
`34cd6df`. Scope: commit `b795b61` against the fix briefs F1, F2 and F3
(`evidence/method/specs/`), their shared rules in `common3.md`, decisions D19
and D20 in `research.md`; and merge commit `b96f154` (`develop` `f444287` into
`ec786ed`).

Result: one blocker, one should-fix and four notes. The merge keeps both
sides' changes. All suites and checks named in the three briefs pass.

## Findings

### B1 (blocker): the installed-IO-package rule (V03) never fires

`scripts/clean_architecture.ts:26` adds `resolvedIOImport` and line 104 adds
it to the `no-io-packages-in-inner-layers` rule. But `analyzeImportGraph`
passes `exclude: '(^|/)node_modules/|^scripts/vendor/|\\.md$'`
(`scripts/clean_architecture.ts:248`). dependency-cruiser drops every module
matching `exclude`, including the edge to it, so an import that resolves to
`node_modules/<io-package>/...` never reaches the rule. The gap V03 reported
is still open.

Evidence: a scratch fixture with `@electric-sql/pglite` installed under
`node_modules` and `plugins/a/src/domain/installed.ts` re-exporting it
(the same fixture the new test uses), run through `analyzeImportGraph`
and through `cruise` with `importRules(root)`:

```text
analyzeImportGraph violations: []
installed.ts dependencies: []
cruise, exclude as committed:              []
cruise, node_modules removed from exclude: [["plugins/a/src/domain/installed.ts","node_modules/@electric-sql/pglite/index.js","no-io-packages-in-inner-layers"]]
```

The test does not catch this. `scripts/clean_architecture_test.ts:124-134`
only checks that the rule's regex matches the string
`node_modules/@electric-sql/pglite/index.js`, and the expected-violation list
at lines 135-153 does not include `plugins/a/src/domain/installed.ts`.
`evidence/worker-F2.md` ("The first graph-based V03 fixture also did not
produce a dependency edge because the analyzer excludes `node_modules`; I
changed the case to test the generated path matcher") shows the worker saw
the missing edge and changed the test instead of asking, which `common3.md`
requires when a fix needs a change at another line.

Suggested resolution (verified in a scratch run, not applied): drop
`(^|/)node_modules/` from `exclude` and add it to `doNotFollow` instead, for
example `path: '^(?!(?:plugins|packages|scripts|tests)/)|(^|/)node_modules/'`
(and the same alternative in the `entryPaths` branch). With that change the
fixture reports the violation above, and the real repository still has 0
violations (80 modules cruised instead of 63; the extra ones are
`node_modules` leaves that are not followed). Simply removing `node_modules`
from `exclude` without the `doNotFollow` change is wrong: it crawls
`packages/wiki-consistency/node_modules` (3103 modules, many `no-cycles`
violations). Then add `['plugins/a/src/domain/installed.ts',
'no-io-packages-in-inner-layers']` to the expected-violation list, so the
test fails without the fix.

### S1 (should-fix): `docs/architecture.md` still says the doctor checks Node 22

`docs/architecture.md:253`: "`npm run doctor` checks them and Node 22."
Decision D19 raised the doctor's floor to Node.js 24.12.0
(`scripts/doctor.ts:207-208`, `turbo.json:22`,
`scripts/git-hooks/commit-msg:15`), so this sentence is now false. The
F1 brief listed only the doctor, `turbo.json` and the hook, so the stale line
is a gap in the brief rather than a worker error.

Suggested resolution: change it to "Node.js 24.12.0 or later".

### N1 (note): the built-lock comparison (V09) is a subset check

`packages/backfire/tests/test_build.py:103-116` asserts that every
`(name, version)` pair of each built `uv.lock` appears in the root
`uv.lock`. A pin written to a version absent from the root lock fails, which
meets the brief's goal. It still passes when a built lock drops packages, or
keeps only one of a package's several root versions: the root lock has two
`magika` entries (`0.6.2`, `0.6.3`, from
`python3 -c` over `uv.lock`). The self-comparisons at lines 139-141 and 178
remain, but they now only cover byte layout.

Suggested resolution: none needed for the brief. If stricter coverage is
wanted, compare versions grouped by package name for the names each built
lock contains.

### N2 (note): the Turborepo probe duplicates `probeVersion`

`scripts/doctor.ts:312-329` (`probeTurboVersion`) repeats the command call,
size limit and decode of `probeVersion` (`scripts/doctor.ts:112-134`), adding
only the `run npm ci` repair text and a caller-supplied expected version.
Also, if `turbo` ever stops being a direct root dependency,
`lock.dependencies.turbo` (`scripts/doctor.ts:374`) is `undefined` and the
error reads "turbo must report version undefined".

Suggested resolution: optional. Reuse `probeVersion` with an expected
version parameter, or keep as is.

### N3 (note): two new tests add little

- `scripts/doctor_test.ts:133-136` runs a full `runDoctor()` only to assert
  `report.turbo.version === '2.11.5'`, which the existing outside-checkout
  test also asserts (`scripts/doctor_test.ts:238`).
- `scripts/cli_contract_test.ts:103-111` asserts the literal
  `backfire:install` string in `package.json`, which restates the
  configuration rather than testing behavior.

Suggested resolution: optional; drop the first, keep or drop the second.

### N4 (note, no action): the commit hook also sets `NODE_OPTIONS`

`scripts/git-hooks/commit-msg:19` exports
`--disable-warning=SecurityWarning` for `npm`, beyond the brief's
`package.json` change. `evidence/worker-F1.md` records the coordinator's
approval: the line matters when a permissioned Node process (such as the
commit test) runs the hook. From a plain shell the `package.json` change alone
is enough: the new `commitlint` script printed no warning, and the old one
printed "SecurityWarning: The flag --allow-child-process must be used with
extreme caution".

## Other checks with no finding

- V01: `uv sync --locked --check --all-packages --extra education --offline`
  exits 0 ("Would make no changes").
- V05/D19: `scripts/doctor.ts:205-208` rejects majors below 24 and 24.x below
  12; tests cover `v24.11.1`, `v22.20.0` and `v24.12.0`.
- V24: `lockedDependencies` (`scripts/doctor.ts:290-302`) reports the root
  package's direct dependencies by name with their locked versions and throws
  `Missing locked dependency: <name>`.
- V26: `node_modules/.bin/turbo --version` prints only `2.11.5` with an empty
  stderr, even from a fresh `HOME` and XDG directories, so a first-run notice
  cannot break the probe.
- V02, V04, V14 and every V13 helper listed in F1 and F2 are fixed as briefed;
  `grep` finds no remaining unguarded `status ?? 1` or `code ?? 1` helper.
- V10: no documented command passes the extra `--` to `doc-regions prepare`
  (`docs/architecture.md:578`, `scripts/workflow.ts:49` use npm's single
  separator).
- V11 and V15/D20: the three comments are gone; the root `uv.lock` keeps the
  same 78 package versions before (`b795b61~1`) and after (`34cd6df`); only
  the four constraint lines changed; `uv lock --check --offline` exits 0.
- Every file in `b795b61` is in one of the three briefs' ownership lists.
  `docs/reference/commands.md` changed only by regeneration (table padding and
  the new doctor description).
- Merge `b96f154`: `git merge-tree --write-tree ec786ed f444287`, run with a
  scratch object directory, gives tree `4a2f0c7838a6`, identical to
  `b96f154^{tree}`. The merge is exactly Git's automatic result: nothing from
  either side was dropped or added. The develop side (wiki-consistency link
  target rules, its tests, the skill, asset and architecture text, spec 017,
  and the `vault-link-targets` bug records) is present. Its only Deno
  mentions are historical run records in `.specify/bugs/vault-link-targets/`,
  which describe runs made on `develop` with Deno; `test:wiki-consistency`
  passes on the merged tree.

## Commands run

Scratch files lived in the session scratchpad; nothing in the repository was
written, and `git status --short` was empty before and after.

| Command | Exit |
| --- | --- |
| `git show b795b61` (stat, source files, tests, docs) | 0 |
| `node io_probe.ts` (fixture through `analyzeImportGraph`) | 0, no violations |
| `node io_probe2.ts` (fixture, `cruise` with and without the `node_modules` exclude, then with it in `doNotFollow`) | 0 |
| `node io_probe3.ts` (repository, same variants) | 0 |
| `npm run test:doctor` | 0 (20 passed) |
| `npm run test:commit-msg` | 0 (6 passed) |
| `npm run test:cli-contract` | 0 (16 passed) |
| `npm run test:git-flow` | 0 (21 passed) |
| `npm run test:worktree-branch` | 0 (4 passed) |
| `npm run test:workflow` | 0 (58 passed) |
| `npm run test:clean-architecture` | 0 (5 passed) |
| `npm run test:docs` | 0 (16 passed) |
| `npm run test:wiki-raw-import` | 0 (44 passed) |
| `npm run clean-architecture` | 0 (63 cruised, 0 violations) |
| `npm run docs:check` | 0 |
| `npm run typecheck` | 0 |
| `npm run doctor` | 0 |
| `npm run test:backfire` | 0 (1364 passed, 3 deselected) |
| `npm run test:doc-regions` | 0 (106 passed) |
| `npm run test:wiki-consistency` | 0 (291 passed) |
| `npm run lint:shell` | 0 |
| `uv lock --check --offline` | 0 |
| `uv sync --locked --check --all-packages --extra education --offline` | 0 |
| `env -i … HOME=<scratch> node_modules/.bin/turbo --version` | 0 (`2.11.5`, empty stderr) |
| `npm run -s commitlint -- --edit <scratch msg>` without `NODE_OPTIONS` | 0, no warning |
| old `commitlint` command line, same message | 0, prints `SecurityWarning` |
| `git merge-tree --write-tree ec786ed f444287` (scratch object directory) | 0, tree `4a2f0c7838a6` |
| `git rev-parse 'b96f154^{tree}'` | 0, tree `4a2f0c7838a6` |
| `git diff --stat ec786ed b96f154`, `git diff f444287 b96f154 --stat -- <develop files>` | 0 |
