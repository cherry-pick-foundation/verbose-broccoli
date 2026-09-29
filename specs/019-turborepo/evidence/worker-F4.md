# CHE-32 F4 worker report

Assumption: the existing synthetic fixture already represented an installed package; the defect was that its resolved graph edge was excluded.

V27 changes `scripts/clean_architecture.ts` to keep `node_modules` modules as leaves using `doNotFollow`, in both default and selected-entry runs. `scripts/clean_architecture_test.ts` now requires `plugins/a/src/domain/installed.ts` to report `no-io-packages-in-inner-layers` in both graph modes. Its fixture installs `@electric-sql/pglite` under `node_modules`.

V28 changes only `docs/architecture.md` to say Node.js 24.12.0 or later.

After adding the installed-package graph violation to the expected list, I saw `npm run test:clean-architecture` fail before changing the analyzer. It exited 1 because the installed file had no `no-io-packages-in-inner-layers` violation. After moving the match to `doNotFollow`, both graph cases passed. Repository cruise count changed from 63 to 80 modules and stayed at 0 violations. V28 is documentation-only; `npm run docs:check` passed.

## Files and rows

- `scripts/clean_architecture.ts` — V27
- `scripts/clean_architecture_test.ts` — V27
- `docs/architecture.md` — V28
- `specs/019-turborepo/evidence/worker-F4.md` — V27, V28

## Commands and exit codes

- `npm run workflow` — 0.
- `npm run workflow -- --task CHE-32-F4 --graph impact --file scripts/clean_architecture.ts` — 0.
- `npm run clean-architecture` before the fix — 0; 63 modules, 0 violations.
- `npm run test:clean-architecture` before the analyzer fix — 1; expected missing installed-package violation.
- `npm run test:clean-architecture` after the fix — 0; final run had 5 passed, 0 failed.
- `npm run clean-architecture` after the fix — 0; 80 modules, 0 violations.
- `npm run workflow -- --task CHE-32-F4 --graph policy` — 0; PASS, 0 errors and 0 violations.
- `npm run test:workflow` — 0; 58 passed, 0 failed.
- `npm run typecheck` — 0.
- `npm run docs:check` — 0.
- `node_modules/.bin/biome check scripts/clean_architecture.ts scripts/clean_architecture_test.ts` — 1 initially for test indentation, then 0 after formatting.
- `node_modules/.bin/biome format --write scripts/clean_architecture_test.ts` — 0.
- `git diff --check` — 0.

`npm run verify` was not run, as the task instructions prohibit it. Ponytail review found no unnecessary code: Lean already.
