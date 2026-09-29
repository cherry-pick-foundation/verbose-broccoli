# Feature Specification: TypeScript Lint and Format with gts

**Feature Branch**: `feature/gts`

**Created**: 2026-09-29

**Status**: Draft

**Linear issue**: CHE-36

**Input**: Linear issue CHE-36, "Lint and format TypeScript with gts instead
of Biome", and the develop session's task brief of 2026-09-29. The user
decided on 2026-09-29 that the repository lints and formats its TypeScript
with [gts](https://github.com/google/gts) (Google TypeScript Style), which
applies Google's TypeScript style through ESLint and Prettier, in place of
Biome. gts is pinned like the other tools and runs in `npm run check` and
`npm run verify`; the one-time reformat is its own commit, separate from
hand fixes; Biome stays only where gts does not reach, or goes where
Prettier already covers that; vendored upstream code keeps its upstream
form. gts's own configuration is preferred over local rules.

## Clarifications

### Session 2026-09-29

- Q: gts's `@typescript-eslint/no-floating-promises` rule flags every
  top-level `test(...)` call of Node's built-in test runner (174 calls in
  16 files), whose promises the runner already handles. Allow them in that
  rule's configuration, or mark each call by hand? → A: Pending; the
  question went to the user through the develop session.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The checks enforce gts style (Priority: P1)

An agent changes TypeScript or JavaScript in the repository and runs the
repository checks before it finishes. The checks fail when the change breaks
a gts lint rule or gts's Prettier format, and they pass on the current code.

**Why this priority**: It is the user's decision and the purpose of the
feature.

**Independent Test**: Run `npm run check` on the feature branch; it passes.
Then check a synthetic TypeScript file with a floating promise or a
formatting deviation; the gts step fails and names the rule and the file.

**Acceptance Scenarios**:

1. **Given** the feature branch, **When** `npm run verify` runs, **Then**
   the gts step runs over every repository-owned TypeScript and JavaScript
   file and reports nothing.
2. **Given** repository-owned code with a floating promise, double quotes
   where gts wants single quotes, or other code that gts's Prettier settings
   would change, **When** the checks run, **Then** they fail and name the
   rule and the file.
3. **Given** a file that follows gts's rules and format, **When** the checks
   run, **Then** they pass.
4. **Given** a file in vendored upstream code, **When** the checks run,
   **Then** gts does not check it.

---

### User Story 2 - One formatter family for code and data files (Priority: P2)

A reader finds one set of formatting settings: gts's Prettier settings
format TypeScript and JavaScript through gts, and the same settings format
the JSON and YAML files that Biome and Prettier formatted before. No Biome
configuration or dependency remains.

**Why this priority**: The issue asks to drop Biome where Prettier covers
its work, so the repository keeps fewer tools.

**Independent Test**: Search the repository for Biome; only historical
records remain. Change the format of a tracked JSON file; the format check
fails.

**Acceptance Scenarios**:

1. **Given** the feature branch, **When** a reader looks for the formatter
   settings, **Then** the root Prettier configuration spreads gts's
   `.prettierrc.json` and adds nothing.
2. **Given** a JSON or YAML file that the checks format, **When** its
   format deviates from gts's Prettier settings, **Then** the format check
   fails.

### Edge Cases

- A new TypeScript or JavaScript file outside the excluded paths is checked
  without further setup; `.mjs` and `.cjs` files are checked as well as
  `.ts` and `.js`.
- Files in ignored folders, such as `node_modules/` and `.venv/`, are not
  checked, even though ESLint does not read `.gitignore`.
- Markdown stays out of the formatters, as it was with Biome.
- The existing ban on runtime and I/O globals in `domain/` folders keeps
  working after Biome is removed.
- Features finished into `develop` while this one is open may add
  TypeScript; the final merge of `develop` brings that code under the check,
  and its findings are fixed before the finish.
- The checks run offline from the locked install and write no files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: gts MUST be pinned to one exact version in the root
  `package.json` and `package-lock.json`, like the repository's other npm
  tools.
- **FR-002**: The lint and format configuration MUST be gts's own: the
  `eslint.config.js` and `.prettierrc.js` that `gts init` writes, plus an
  `eslint.ignores.js` that lists the excluded paths. A local rule is added
  only to keep an existing repository rule (FR-007) or where a
  clarification decides it, and each carries a one-line reason.
- **FR-003**: `npm run check`, and so `npm run verify`, MUST run gts's
  check over every repository-owned TypeScript and JavaScript file and
  Prettier's check, with gts's settings, over the JSON and YAML files that
  the checks formatted before; each MUST fail on any finding, write no
  files and need no network. The writing forms (`npm run lint:fix` and
  `npm run format`) MUST use the same tools.
- **FR-004**: Biome MUST be removed: its dependency, its configuration and
  every command and current document that names it. Historical records
  keep their text.
- **FR-005**: Vendored upstream code MUST be excluded by path and keep its
  upstream form. Today that is `scripts/vendor/`, `.specify/`,
  `plugins/code/hooks/`, `plugins/code/tests/hooks.test.js` and
  `plugins/work/skills/quarto-authoring/`. The other paths Biome excluded
  stay excluded, and Markdown stays out of the formatters.
- **FR-006**: The one mechanical reformat of existing files MUST be its own
  commit, holding only the formatters' output with the final configuration
  and no hand edits. Every remaining finding MUST be fixed by hand in later
  commits without changing behavior; the existing test suites MUST still
  pass.
- **FR-007**: The ban on runtime and I/O globals in `plugins/**/domain/**`
  and `packages/**/domain/**` that `biome.json` holds today MUST keep the
  same globals and messages, expressed with ESLint's own
  `no-restricted-globals` rule.
- **FR-008**: Acceptance MUST show positive, negative and boundary cases for
  the configuration with synthetic input: a floating promise, a formatting
  deviation, a compliant file, a vendored path, a `domain/` file that uses
  a banned global, and a JSON formatting deviation. The repository's test
  task MUST run it.
- **FR-009**: The documents that list the repository's tools and checks MUST
  name gts and its pinned version and stop naming Biome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `npm run verify` passes on the merged result of this feature
  and the final `develop`, with the gts step among the checks it ran.
- **SC-002**: The acceptance cases of FR-008 fail when the configuration is
  broken, for example when an exclusion covers all files, and pass on the
  committed configuration.
- **SC-003**: The test suites pass with the same test counts as before the
  change, apart from the new FR-008 test.
- **SC-004**: Running the formatters on the parent of the reformat commit
  reproduces that commit exactly.

## Assumptions

- "Pinned like the other tools" means an exact version in the root
  `package.json` and `package-lock.json`, as Biome, Prettier and Turborepo
  are pinned today.
- gts runs the `eslint` found on the `PATH`; in npm scripts that is the
  root's pinned ESLint. [research.md](research.md) records why that is
  acceptable.
- gts's `tsconfig-google.json` is not adopted: the issue covers lint and
  format, not type-check settings.
- The constitution and `AGENTS.md` do not change.
