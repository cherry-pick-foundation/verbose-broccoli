# Implementation Plan: TypeScript Lint and Format with gts

**Branch**: `feature/gts` | **Date**: 2026-09-29 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/020-gts/spec.md`

## Summary

Replace Biome with gts 7.0.0 for TypeScript and JavaScript, and with
Prettier under gts's settings for JSON and YAML:

- The root `package.json` pins `gts` and drops `@biomejs/biome`;
  `biome.json` goes.
- `eslint.config.js` and `.prettierrc.js` are the files `gts init` writes;
  `eslint.ignores.js` lists the excluded paths. The only local rule is the
  ported `domain/` globals ban (FR-007).
- `lint` runs `gts lint .` before Ruff, and `format:check` runs Prettier's
  check on JSON and YAML before Ruff; `lint:fix` and `format` run the
  writing forms. Turborepo's existing `//#lint` and `//#format:check` tasks
  keep them in `npm run check` and `npm run verify`.
- One commit holds only the formatters' output. Later commits fix the
  remaining findings by hand.
- `scripts/gts_test.ts` checks the configuration with synthetic input.

The research, including the trial's findings, is in
[research.md](research.md).

## Technical Context

**Language/Version**: TypeScript 6.0.3 on Node.js 24.12 or later.

**Primary Dependencies**: gts 7.0.0 (ESLint configuration, typescript-eslint
8.70.0 through the root pin, eslint-plugin-prettier); ESLint 10.10.0 and
Prettier 3.9.9 already pinned at the root.

**Storage**: None.

**Testing**: `npm run check` and `npm run verify`; the Node and Python
suites keep their counts; a new `node:test` file for the configuration.

**Target Platform**: The development machine (Linux) and Orca worktrees.

**Project Type**: Repository checks.

**Performance Goals**: None beyond the existing check run.

**Constraints**: Offline and read-only in the checks (no ESLint cache);
vendored upstream code excluded, not edited; Markdown not formatted.

**Scale/Scope**: 32 tracked `.ts` files, 7 `.js` and 2 `.mjs`, of which the
7 `.js` files are vendored. 200 findings in the trial (research.md R3).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Proven Dependencies**: gts is pinned to one version in
  `package-lock.json`. Pass.
- **V. Observable Acceptance**: The new test covers positive, negative and
  boundary cases, the vendored-path exclusion and the `domain/` ban with
  synthetic input; the suites keep their counts. Pass.
- **VII. Minimum Implementation and reuse order**: gts's rule set and
  Prettier settings are reused as shipped, through the files `gts init`
  writes; ESLint's core rule replaces Biome's `domain/` ban. The only local
  code is task wiring and the test. Pass.
- **IX. Layout**: Configuration at the root, the test under `scripts/`.
  Pass.
- **Development workflow**: Spec Kit records here; the develop merge review
  and `git flow feature finish` follow the constitution. Pass.

Post-design re-check: no change.

## Project Structure

### Documentation (this feature)

```text
specs/020-gts/
├── spec.md
├── plan.md
├── research.md
└── tasks.md
```

### Source Code (repository root)

```text
package.json, package-lock.json      # gts in, Biome out; lint, lint:fix,
                                     # format, format:check, docs:*, test task
turbo.json                           # //#test:gts in the test dependencies
eslint.config.js, eslint.ignores.js  # new: gts init's files, ignores filled
.prettierrc.js                       # new: gts init's file
biome.json                           # removed
scripts/gts_test.ts                  # new: configuration test
tsconfig.json                        # lists scripts/gts_test.ts
scripts/docs.ts, scripts/docs_test.ts   # read eslint.ignores.js, not biome.json
scripts/workflow_files.ts            # exclusions from eslint.ignores.js
scripts/workflow.ts, scripts/workflow_graph.ts  # drop Biome's name
scripts/clean_architecture_test.ts   # the domain/ ban test runs ESLint
docs/architecture.md, docs/reference/*  # tool list; generated tables
scripts/*.ts, scripts/*.mjs, plugins/code/skills/clean-code/scripts/*.ts,
packages/wiki-consistency/src/wiki_consistency/search.mjs  # fixes
```

## Commits

1. Tooling, configuration, test and documents (`build`).
2. `style: apply gts format` — only the formatters' output, taken with the
   final configuration, no hand edits.
3. Hand fixes, each keeping behavior and tests.
4. `void` in front of each top-level `node:test` call, in its own commit
   (spec.md clarification).

The checks pass only after the last commit; the commit hook checks messages,
not the checks, so the intermediate commits are allowed.

## Validation

1. `npm ci` from the committed lock installs gts 7.0.0; `npm ls gts`
   shows it.
2. `npm run lint` and `npm run format:check` report nothing.
3. `npm test` runs the configuration test and the suites; their counts
   match `develop`.
4. Running `npm run format` and `npm run lint:fix` on the parent of the
   reformat commit reproduces it.
5. `npm run verify` passes after the final merge of `develop`.
