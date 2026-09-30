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
  line (`qmd collection`, `qmd update`, `qmd embed`) and one stdio MCP
  session per search call, whose `query` tool runs typed `lex` and `vec`
  searches with reranking off and whose `status` tool gives the document
  counts and embedding readiness. `search.mjs`, which imports qmd's
  internal `dist/store.js`, goes. The review's controls apply: no
  `qmd vsearch`, query expansion or `qmd pull` (they fetch generation and
  reranking models), `QMD_FORCE_CPU=1`, umask 077 and a 0700 cache folder,
  and download tokens removed from qmd's environment.
- **Rationale**: One MCP session keeps a call's queries in one process, as
  `search.mjs` did; one process per keyword query made 200 queries take
  24 s instead of 0.5 s.
- **Dropped**: the stale-index message that lists added, changed, deleted
  and empty files (search runs `qmd update` first), the exact vector chunk
  cap (document counts stand in), checks for query shapes the callers
  cannot produce, and the removal of unexpected collections and collection
  update hooks; scores are qmd's, rounded to two decimals.

## R1. Environment check

- **Decision**: mise 2026.9.16 (the machine's APT package, now 2026.9.17)
  pins uv 0.11.32, lychee 0.24.2, Vale 3.23.0 and git-flow-next 2.1.0 in the
  root `mise.toml`, with `mise.lock` holding each download's URL, checksum
  and provenance; `npm run doctor` runs `mise doctor project`, whose
  `[doctor.checks]` replace `scripts/doctor.ts`. Node.js stays on the user's
  mise Node 24 (with `package.json` `engines`), Quarto and CodexBar stay
  separately installed with a version check each.
- **Machine changes** (the user approved each one): mise's global settings
  `paranoid`, `locked_verify_provenance`, `use_versions_host_track = false`,
  `node.gpg_verify` and `github.gh_cli_tokens = false` (backup
  `~/.config/mise/config.toml.bak-che44-20260930T001148Z`); the four tools
  installed with `mise install --locked` (the mise copies of uv, lychee and
  git-flow are byte-identical to the earlier ones in `~/.local/bin`); and the
  `MISE_*`, `RUSTUP_HOME` and `CARGO_HOME` exports in `~/.bash_profile` and
  `~/.bashrc` (backups `*.bak-che44-20260930T021734Z` and
  `*.bak-che44-20260930T023850Z`), which paranoid mode needed so tests with a
  temporary `HOME` neither fail on untrusted configuration nor download a
  1.5 GB Rust toolchain.
- **Security**: R1 (2026.9.16) and R6 (the 2026.9.17 delta) reports in
  [security/](security/): no high findings; four medium findings stand and
  were accepted with the controls.

## R5. Constitution version

- **Decision**: commitizen 4.19.0 writes the version line (`npm run
  constitution:bump -- PATCH|MINOR|MAJOR`, `.cz.toml`, hooks empty, files
  only); the rule stays in the constitution and reviewers check it. It
  bumped this feature's amendment from 2.3.0 to 2.3.1 after the merge of
  `develop`.

## R6. Wiki page rules

- **Decision**: Vale 3.23.0 rules in `packages/wiki-consistency/vale/` with
  a Python step for the roster rules (214 own-code lines in `rules.py`, about
  90 of them for the roster, which the user approved at about 60). Vale's
  raw-scope rules ignore `BlockIgnores`, so the Python step also drops
  findings inside Cog regions and the front matter.

## R8. Raw import record

- **Decision**: keep bagit's `make_bag` and its source record; remove the
  one-run lock, the stale-staging cleanup and the second hash of the
  original after copying.

## R9. Workflow, verify and import checks

- **Decision**: the user chose to replace verify's own run record (option
  B of [phase3-design.md](phase3-design.md)). `npm run verify` runs `turbo run
  check --summarize` and passes on its exit status and the same run's
  summary; dependency-cruiser's command and `.dependency-cruiser.json` replace
  `scripts/clean_architecture.ts` and answer the graph queries; import-linter
  2.15 checks the Python packages. The own-code limit check (CHE-42) goes, as
  the user decided on 2026-09-30.

## Results

Own-code lines are scc 4.1.0 Code lines of programming-language files,
tests excluded, for the replaced files at `3bd2e7f` (the first `develop`
merged into this branch) and at the branch tip. For the whole tree, the
branch's merge base with `develop` (`b9a0293`) counts 14,486 lines and the
tip 11,962: **net -2,524**.

| Swap | Tool, pin, license | Review | Removed | Own code | Dropped behaviours |
| --- | --- | --- | --- | --- | --- |
| Plugin manifests | check-jsonschema 0.38.2 (PyPI, `tools/check-jsonschema`), Apache-2.0 | R4: 0 high, 1 medium | `scripts/validate_plugins.ts` | 80 → 0 (-80) | Symlinked-manifest refusal, custom roots, JSON summary |
| Reference docs | cogapp 3.6.0 (already pinned), MIT | R4: 0 high, 1 medium | `scripts/docs.ts`, `docs_test.ts`, `docs:*` tasks | 683 → 147 (-536) | Two-step publication and recovery folder, lock, symlink and stray-file refusal, terminal-control and local-path guards, permission-bounded help run, "Input owners" line |
| Wiki search | qmd 2.8.3 CLI and MCP (already pinned), MIT | R3: 0 high, 5 medium | `search.mjs` | 516 → 257 (-259) | Stale-index file list, exact vector chunk cap, checks for impossible query shapes, removal of unexpected collections and update hooks |
| Import check, workflow and verify | dependency-cruiser 18.2.0 (MIT), import-linter 2.15 (BSD-2-Clause, with grimp 3.17), Turborepo 2.11.5 (MIT) | R5: 0 high, 5 medium; R2: 0 high, 3 medium | `scripts/clean_architecture.ts`, `workflow-evidence.schema.json`, verify's evidence record | 1,937 → 1,451 (-486) | Rules built from every package.json's exports and aliases, the architecture JSON report, verify's task/base/plan binding, snapshots, log hash, interrupted-run detection, failure streak, REVIEW threshold and lock, graph labels and test-file hints |
| Own-code limit | none (removed by the user's decision) | none | `scripts/own_code.ts`, its test, `tools/scc`, `linguist-languages` | 127 → 0 (-127) | The 300-line limit and its approval line |
| Environment check | mise 2026.9.16/17 (APT), MIT | R1, R6: 0 high, 4 medium | `scripts/doctor.ts`, its test | 426 → 0 (-426) | JSON report and `--report`, `--quarto`, executable-path checks, lock hash |
| Constitution version | commitizen 4.19.0 (PyPI, `tools/commitizen`), MIT | R4: 0 high, 1 medium | `scripts/constitution_version.ts`, the finish hook's version loop | 188 → 7 (-181); finish hook 65 → 58 (-7) | Automatic refusal in the commit-message and finish hooks, `--amend` detection |
| Git hooks | lefthook 2.1.15 (npm), MIT | R2: 0 high, 1 medium | `scripts/git-hooks/commit-msg`, `core.hooksPath` | 13 → 0 (-13) | The old hook's Node.js diagnostic |
| Wiki page rules | Vale 3.23.0 (mise), MIT | R3: 0 high, 3 medium | pattern code in `rules.py` | 604 → 214 (-390) | Date validity, registration birth-date check, backfire's phone and email detection, exact quote and time-range logic, front matter title and summary checks |
| Raw import | bagit 1.9.0 (already pinned), CC0 1.0 | R5: 0 high, 2 medium | lock, staging cleanup, copy re-check | 336 → 323 (-13) | The three removed behaviours |

The user accepted every dropped behaviour and the medium findings with the
controls on 2026-09-30.
