# Research: TypeScript Lint and Format with gts

All findings come from a trial on 2026-09-29: a copy of `develop` at
`7e18ad4` with `gts@7.0.0` installed, the three files that `gts init`
writes, and an `eslint.ignores.js` with Biome's exclusions. The copy lived
in a scratch directory outside the repository.

## R1. gts version and what it ships

- **Decision**: Pin `gts` 7.0.0, the latest release (2025-12-15).
- **Evidence**: `npm view gts versions` ends at 7.0.0. Its changelog moves
  the ESLint configuration to the flat format. The package's
  `build/src/index.js` is the whole rule set: `@eslint/js` recommended,
  `eslint-config-prettier`, `prettier/prettier` as an error, a few core
  rules, and for `**/*.ts` typescript-eslint's recommended set with
  `@typescript-eslint/no-floating-promises` as an error and
  `parserOptions.project: './tsconfig.json'`. `.prettierrc.json` sets
  `bracketSpacing: false`, `singleQuote: true`, `trailingComma: "all"` and
  `arrowParens: "avoid"`, which match the current `biome.json`.
- **Configuration files**: `gts init` writes `eslint.config.js` (spreads an
  optional `eslint.ignores.js`, then `require('gts')`), `eslint.ignores.js`
  and `.prettierrc.js` (`...require('gts/.prettierrc.json')`). The
  repository uses these templates as written, taken from
  `build/src/init.js`, and fills only `eslint.ignores.js`.

## R2. Which ESLint runs

- **Decision**: Let gts run the root's pinned ESLint 10.10.0.
- **Evidence**: `gts lint` calls `execa('eslint', …)`, which takes `eslint`
  from the `PATH`; npm scripts put the root `node_modules/.bin` first. The
  root already pins ESLint 10.10.0 for the Clean Code checker, so npm nests
  gts's own `eslint@^9.37.0` (9.39.5, which npm marks as no longer
  supported) under `node_modules/gts/`. The trial gave the same 200
  findings under both versions. Upstream has an open pull request to move
  gts to ESLint 10 (google/gts#959).
- **Alternatives rejected**: Putting gts's nested ESLint first on the `PATH`
  depends on npm's install layout and runs an unsupported ESLint. An npm
  `overrides` entry would patch gts's dependency for no observed gain.

## R3. Findings on the current code

The trial's `gts lint .` reported 200 errors:

| Rule | Count | Where | Handling |
| --- | --- | --- | --- |
| `@typescript-eslint/no-floating-promises` | 174 | top-level `test(...)` calls of `node:test` in 16 test files | Hand fix in its own commit: `void test(...)` (spec.md clarification) |
| `prettier/prettier` | 15 | `scripts/docs.ts`, `scripts/validate_plugins.ts`, `scripts/workflow.ts`, `scripts/workflow_skills.ts`, `scripts/workflow_verify.ts` | Reformat commit |
| `no-undef` | 9 | `process` in `packages/wiki-consistency/src/wiki_consistency/search.mjs` (8) and `scripts/commitlint.config.mjs` (1) | Hand fix: import `process` from `node:process` |
| `no-control-regex` | 1 | `scripts/docs.ts:126`, which a `biome-ignore` comment covers today | Hand fix: the same reason in an `eslint-disable-next-line` comment |
| `@typescript-eslint/no-unused-vars` | 1 | `_lock` in `scripts/docs.ts:575` | Hand fix |

A second `biome-ignore` comment, in
`plugins/code/skills/clean-code/scripts/clean_code_test.ts:65`, covers a
Biome rule that gts does not enable; it goes.

Prettier with gts's settings would also change `turbo.json`,
`scripts/workflow-evidence.schema.json`, the four workflows under
`.github/workflows/` and `orca.yaml` (`bracketSpacing: false` in YAML flow
maps). These changes belong to the reformat commit.

## R4. What gts's lint covers

- **Decision**: Run `gts lint .` and `gts fix .` rather than bare
  `gts lint`.
- **Evidence**: Without file arguments, gts passes `**/*.ts`, `**/*.js`,
  `**/*.tsx` and `**/*.jsx`, which leaves out the two `.mjs` files that
  Biome checks today. With `.`, ESLint checks every file that a
  configuration object matches: its defaults `**/*.js`, `**/*.mjs` and
  `**/*.cjs`, and gts's `**/*.ts` and `**/*.tsx`.
- **Ignores**: ESLint reads no `.gitignore`, so `eslint.ignores.js` lists
  `**/.venv/` next to Biome's exclusions. ESLint ignores `node_modules/`
  itself.
- **Type information**: gts's typed rules need every linted `.ts` file in
  the root `tsconfig.json` program. `tsc --listFilesOnly` shows that all 32
  tracked `.ts` files are in it today.

## R5. JSON and YAML

- **Decision**: Drop Biome and format JSON and YAML with Prettier and gts's
  settings, through the root `.prettierrc.js`.
- **Evidence**: Prettier is already a root dependency (3.9.9) and formats
  YAML today; gts depends on Prettier `^3.6.2`, which the root pin
  satisfies. Biome's JSON formatting differed from Prettier's in only two
  files that stay (R3). Biome's JSON lint rules, such as duplicate keys, go
  with it; Prettier still rejects JSON it cannot parse.
- **File set**: The format check covers the tracked JSON and YAML files
  outside the excluded paths; Markdown stays out. A `.prettierignore` or an
  explicit file list, whichever is smaller, keeps the excluded paths out.

## R6. The `domain/` globals ban

- **Decision**: Express it with ESLint's core `no-restricted-globals` for
  `plugins/**/domain/**` and `packages/**/domain/**`, with Biome's names and
  messages.
- **Evidence**: `biome.json` holds the ban; `docs/architecture.md` names it;
  no `domain/` folder exists today, so the ban guards future code only.
  `scripts/clean_architecture.ts` checks import direction, not globals.

## R7. gts's TypeScript settings

- **Decision**: Keep the root `tsconfig.json`; do not extend gts's
  `tsconfig-google.json`.
- **Evidence**: The issue covers lint and format. The trial's type check
  with `tsconfig-google.json` gave five errors: three because its `lib` is
  ES2023 while the scripts use `RegExp.escape`, and two from
  `noImplicitReturns`. Adopting it would mean overriding its `lib` and
  `composite` settings, since the repository runs TypeScript directly on
  Node and emits nothing.
