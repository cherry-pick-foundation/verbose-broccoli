# CHE-32 final review CR2: the TypeScript test suites (read-only)

**Report file**: `specs/019-turborepo/evidence/review-CR2.md`.

**Scope** (`git diff 8ce9b2a 9d8af61 -- <path>`): every `scripts/*_test.ts`, `scripts/cli_contract_test.ts.snapshot` (and the deleted `scripts/__snapshots__/cli_contract_test.ts.snap`), and `plugins/code/skills/clean-code/scripts/clean_code_test.ts`. Judge each test against the version on `develop`: a converted test should check at least what it checked before, unless a selected site or a decision says otherwise. You may run the suites (`npm run test:<name>`; the scripts are in `package.json`).
