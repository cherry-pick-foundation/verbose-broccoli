# Research: Upstream Tools in Place of Own Tooling Code

Own-code lines below are scc 4.1.0 "Code" counts of the files on `develop`
at `0bc0c63`, the counter and method CHE-42 chose (research R1 of
`specs/022-own-code-limit/`). Tests are not counted.

## R0. Security review and licenses

- **Decision**: Before a tool is added, a read-only reviewer on Codex's
  security model (Daybreak Blue, `gpt-daybreak-blue-latest`, max effort)
  reviews the tagged source of the exact version to be pinned, in a scratch
  clone outside the repository: install and post-install scripts, downloads
  and their verification, network calls and telemetry, reachable code
  execution and shell-outs, file writes outside the working folder,
  credential handling, published advisories and release signing. A tool is
  added only if no high-severity finding stands; high and medium findings go
  to the user through the develop session. Five reviewers split the eleven
  tools so each scope fits about a third of a context window.
- **Licenses**, confirmed from each repository on 2026-09-30:

  | Tool | Version | License (repository file) |
  | --- | --- | --- |
  | mise | 2026.9.16 | MIT |
  | check-jsonschema | 0.38.2 | Apache-2.0 (`LICENSE`; GitHub's summary shows none) |
  | commitizen | 4.19.0 | MIT |
  | cogapp | 3.6.0 | MIT |
  | lefthook | 2.1.15 | MIT |
  | Vale | 3.23.0 | MIT |
  | qmd (`@tobilu/qmd`) | 2.8.3 | MIT |
  | bagit-python | 1.9.0 | CC0 1.0 (README "License" section and the `License :: Public Domain` classifier; the repository has no license file) |
  | import-linter | 2.15 | BSD-2-Clause (with grimp 3.17, BSD-2-Clause) |
  | dependency-cruiser | 18.2.0 | MIT |
  | Turborepo | 2.11.5 | MIT |

- **Rationale**: The develop session relayed the user's security gate on
  2026-09-30. The versions are the ones the repository pins already (cogapp,
  qmd, bagit, dependency-cruiser, Turborepo), the installed mise, and the
  latest release of each new tool.

## R2. Plugin manifest check

- **Decision**: check-jsonschema 0.38.2 from PyPI, run offline as
  `check-jsonschema --schemafile <vendored schema> <manifests>` once for
  `plugin.json` and once for the `mcp.json` files, replacing
  `scripts/validate_plugins.ts` (80 lines).
- **Rationale**: It is maintained and validates 2020-12 schemas with local
  `#/$defs` references. The vendored Agent Plugins schemas under
  `scripts/vendor/agent-plugins/` stay unchanged.
- **Alternatives considered**: `ajv-cli` 5.0.0 would reuse Ajv, which is
  installed, but its last release is from 2021 and it is a separate package;
  Ajv itself has no command line, so using it needs the script this swap
  removes.

## R3. Reference documents

- **Decision**: `docs/reference/commands.md` and `docs/reference/plugins.md`
  become documents with cog regions, listed as targets in
  `scripts/doc_regions.toml`, so `npm run doc-regions:check` finds drift and
  `npm run doc-regions:update` refreshes them. The regions call new
  generator functions in `scripts/doc_sources.py`: the root task table from
  `package.json` and `turbo.json`, the help text of the repository's own
  commands, and the plugin table from the manifests. `scripts/docs.ts` (666
  lines) and its test go.
- **Rationale**: cogapp is already the repository's region generator
  (feature 008), and doc-regions already runs it in check and update mode.
- **Dropped**: the two-step publication with its recovery folder, the lock,
  the refusal of symlinks and stray files in `docs/reference/`, the check for
  terminal control characters and machine-local paths, and the "Input
  owners" line.

## R4. Git hooks

- **Decision**: lefthook 2.1.15 from npm, with `lefthook.yml` declaring the
  `commit-msg` hook that runs commitlint. `lefthook install` writes Git's
  hooks; `lefthook check-install` is one of the environment checks.
- **Shared wiring**: lefthook installs into Git's common hooks folder and
  refuses to install while `core.hooksPath` is set, so the switch from
  `core.hooksPath = scripts/git-hooks` affects every worktree of the
  repository at once. It is done once, after the finish, from the `develop`
  worktree, with the user's approval. Until an in-flight branch merges
  `develop`, its commits find no `lefthook.yml` and skip the hook.

## R7. Wiki search

- **Decision**: `search.py` keeps the functions the request builders call
  (`index`, `search`, `semantic_ready` and `_collection_chunk_count`), because
  CHE-39 changes `requests.py`, and implements them with qmd's own command
  line (`qmd collection`, `qmd update`, `qmd embed`, `qmd status`, and
  `qmd search`/`qmd vsearch --format json`, whose results carry `file`,
  `line` and `score`) or with its stdio MCP server. `search.mjs`, which
  imports qmd's internal `dist/store.js`, goes.
- **Dropped**: the stale-index message that lists added, changed, deleted
  and empty files; qmd's JSON rounds scores to two decimals.

## Pending decisions

R1 (environment check and mise installs), R5 (constitution version), R6
(Vale and the roster) and R8 (raw import record) wait for the user's answers
to the questions asked on 2026-09-30.
