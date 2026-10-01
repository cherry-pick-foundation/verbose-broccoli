# Research: Root Configuration Boundaries

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Measured on 2026-10-01 and 2026-10-02 in this worktree with mise 2026.9.18,
Turborepo 2.11.5, Ruff 0.16.9, Prettier 3.9.9, lefthook 2.1.15, ls-lint
2.3.1, dependency-cruiser 18.2.0 and commitizen 4.19.0.

## D1. Each moved config is found natively or by an option the tool already takes

| Config | Where | How the tool finds it | Evidence |
| --- | --- | --- | --- |
| mise | `.config/mise.toml`, `.config/mise.lock` | mise reads `.config/mise.toml` and its lock beside it; tasks and doctor checks run from the repository root | a lock entry changed to a wrong version failed `mise install --locked` in a scratch copy; `mise doctor project` and `mise run` ran from a subfolder with the root as working folder; `npm run test:mise-doctor` |
| lefthook | `.config/lefthook.yml` | lefthook's own search list includes `.config/lefthook.yml` | `npm run test:commit-msg` (a temporary repository with only `.config/lefthook.yml`) accepts a conventional commit and rejects "Update files" |
| ls-lint | `.config/ls-lint.yml` | `-config` option in `scripts/lint-names.sh` | `npm run test:lint-names`; a file named `Bad_Name.txt` made `npm run lint:names` exit 1 |
| dependency-cruiser | `.config/dependency-cruiser.json` | `--config` option in the `clean-architecture` script and in `scripts/workflow-depcruise.ts`; its `$schema` path became `../node_modules/…` | `npm run test:clean-architecture` (every rule fires on synthetic imports) and `npm run clean-architecture` (no violation) |
| commitizen | `[tool.commitizen]` in `pyproject.toml` | commitizen reads `pyproject.toml` in the working folder | `npm run test:constitution-bump` |
| Ruff | `[tool.ruff]` in `pyproject.toml` | Ruff reads `[tool.ruff]`; each package's `extend` names `../../pyproject.toml` | `npm run test:ruff`; D2 |
| Prettier | `"prettier": "gts/.prettierrc.json"` in `package.json` | Prettier reads the `prettier` key; the string names gts's shared config | `npm run test:gts`; it failed with the key set to `{}` (mutation check) |

## D2. Effective rules are unchanged

Ruff's `--show-settings` for 11 files (the scripts, each package's source, a
package test, a plugin script and a Spec Kit path) before and after the fold
differ in one place only: `linter.src` lists the same five package source
folders, in alphabetical order because `packages/*/src` is a glob. Prettier's
resolved options for 9 files (TypeScript, JSON, YAML, Markdown, a nested
package's `package.json`) are equal before and after
(`bracketSpacing: false`, `singleQuote`, `trailingComma: all`,
`arrowParens: avoid`); only the source file of the options changed.

## D3. One setup task

The three copies of setup differed:

- `orca.yaml` synced the script environment of `raw_import.py` and ran
  `npm run doctor`; the hosted check did neither.
- The hosted check ran `uv python install --no-bin` first, installed five of
  the ten tools, and synced the uv workspace twice (the second time through
  `backfire:install`); Orca did not install Python and listed all ten tools.
- `wiki-consistency:install` repeated the uv sync of `backfire:install`.

`[tasks.setup]` in `.config/mise.toml` now holds the union once.
`mise install --locked` with no tool names fails here, because the user's
global tools are not in the project lock (`pnpm@latest is not in the
lockfile`); and it would install them. The task therefore passes the project's
own names, `$(mise ls --local --no-header | awk '{print $1}')`, and each name
resolves to the version in the file. Later commands use `mise exec --`
because the tools were installed by the task's first line. Lefthook's hooks
stay a separate step: they are installed once into the shared hooks folder
(architecture note), and the hosted check does it after setup.

`uv python install --no-bin` is in the task because the sync would download
the same interpreter; `--no-bin` adds no program to the user's `PATH`.

## D4. Turborepo: what the placeholder and the umbrellas did

- `"workspaces": ["tools/none"]` puts Turborepo in multi-package mode.
  With no `workspaces` it stops with "Package tasks … are not allowed in
  single-package repositories"; with `[]` the same. Feature 019's
  `packages/*` collided with `packages/wiki-consistency/package.json`
  (the uv member has the same name). The glob
  `["packages/*", "!packages/wiki-consistency"]` works in Turborepo and npm:
  `package-lock.json` changes by those two lines and `npm ls --all` exits 0.
  It names real folders and keeps wiki-consistency's own npm tree, so the
  placeholder is gone.
- The root uv workspace is itself a Turborepo package and needs a name
  (`[tool.turbo] name`; without it Turborepo stops).
- For Python, Turborepo infers `check` only at the workspace level:
  `verbose-broccoli-python#check` would run `uv check --frozen
  --all-packages`. That is uv's type checker: it reported 169 diagnostics and
  exit 1, and it replaced the editable installs in `.venv` with copies (the
  `uv-workspace` doctor check then failed until `uv sync` was run again).
  A member's `check` runs only when something depends on it. So the task
  `verbose-broccoli-python#check` stays, now as the Python fan-out: it
  depends on each package's `check` and runs `true`. `test` and `build` are
  inferred per package, so `verbose-broccoli-python#test` is gone.
- Root tasks `//#check` and `//#test` are the entry points. They need
  `command: ["true"]`: with the root `check` and `test` scripts, which start
  Turborepo, Turborepo would otherwise run them and recurse. A `command` in
  `turbo.json` takes precedence over the script (the dry run printed
  `true`).
- Graph after the change (`turbo run check --dry=json`, 47 tasks): each
  package `<p>#check` depends on `<p>#test`; `verbose-broccoli-python#check`
  depends on the five `#check` tasks; `//#check` depends on the twelve root
  checks, `//#test` and `verbose-broccoli-python#check`; `//#test`
  depends on the 22 root tests. Before: 40 tasks and
  `verbose-broccoli-python#test` and `#check` held the lists.

## D5. Python test commands

A package's `test` runs `npm --prefix ../.. run test:<package>`, so the
`pytest` command lines exist once, in `package.json`. Turborepo no longer
sees those lines, so `../../package.json` is an input of each package test:
editing a script reruns the tests. `scripts/turbo-cache-test.ts` has a case
for it; it fails when the input is removed. Real run: the `credit-offers`,
`doc-regions` and `jev-ultrafast` checks passed through the new commands
(6 tasks, all successful).

## D6. Duplicate pins: what was removed and what stays

Removed: the ten-tool list in `orca.yaml`, the five-tool list and the Quarto
version and checksum in `check.yml`, the uv version and checksum in
`docs-check.yml` (it now installs uv from the lock through the shared
`.github/actions/prepare-mise` action, which also holds mise's own release
and checksum once), `required-version` in all eleven `pyproject.toml`
files, and the explicit versions in the session-selection reference's
install command and the architecture note's list.

Stay, with the reason:

- `uv_build>=0.11.32,<0.12` in five packages' `[build-system]`: a range for
  the build backend that follows uv's minor version, not a pin of the tool.
  A uv bump past 0.12 needs it moved; CHE-50's weekly update must handle it.
- The Node release and checksum in three workflows: Node is not pinned in
  the mise file (it comes from the user's global mise), so there is no source
  to read.
- CodexBar's version appears three times inside its own doctor check; all in
  the mise file.
- Prose that names a tool's version where it describes the tool (the
  architecture note, `docs/backfire.md`'s "uv 0.11.32 or later").

The guard that `required-version` gave (a different uv failed loudly) is now
the doctor check `uv-version`: it compares `uv --version` with the version
mise holds for uv. It fails with a fake uv first on `PATH`. (A check on the
path of uv would fail on this machine: `~/.local/bin/uv` is a standalone copy
of the same version and comes first.)

## D7. Tests

`scripts/root-config-test.ts` (`npm run test:root-config`) has six tests.
Mutation checks, each reintroducing one old arrangement, made the right test
fail: a `ruff.toml` at the root; a pin in `orca.yaml`; `npm ci` in
`orca.yaml`; `required-version` in a package; a stale `extend` path; a
`pytest` command in `turbo.json`; `tools/none` back in the workspaces.
It also found a leftover `verbose-broccoli-python#test` that the dry run of
`check` does not list.

## D8. Hosted acceptance not exercised

The GitHub workflows were not run. They validate against the vendored GitHub
workflow and action schemas (`check-jsonschema --builtin-schema
vendor.github-workflows` and `vendor.github-actions`), pass Prettier, and
their commands were run locally. A hosted run, a local composite action in
`docs-check.yml` and `mise exec` with `MISE_EXEC_AUTO_INSTALL=false` on a
runner stay open.

## D9. Commit-message rules: three rule sets

Rules:

| Rule | commitlint (config-conventional 21.2.3) | `cz check` (cz_conventional_commits) | Pull-request title pattern |
| --- | --- | --- | --- |
| Types | 11 (build chore ci docs feat fix perf refactor revert style test) | the same plus `bump` | the same 11 |
| Type case | lower | exact match, so lower | lower |
| Scope | any text | any non-space text | `[a-z0-9-]+` only |
| `!` and `BREAKING CHANGE` | yes | yes | `!` only |
| Separator | `: ` (no space is rejected) | `: ` | `: ` and a non-space next |
| Empty subject | rejected | rejected | rejected |
| Subject case | rejects sentence, start, pascal and upper case | none | none |
| Subject full stop | rejected | none | none |
| Header length | 100 | none (the `-l` option can set it) | none |
| Header whitespace | trimmed | none | leading space rejected |
| Blank line before body | warning | rejected | none |
| Body and footer line length | 100 | none | none |
| Merge, revert, fixup, squash | skipped by default ignores | skipped by default prefixes | rejected (a title) |

Measured on 30 messages: commitlint as the hook runs it
(`commitlint --config scripts/commitlint.config.mjs`), `cz check
--commit-msg-file`, and `grep -E` with the pattern of
`.github/workflows/pr-title.yml` on the header line:

| case | commitlint | cz check | PR title |
|---|---|---|---|
| plain valid | accept | accept | accept |
| scope valid | accept | accept | accept |
| scope upper/space-free | accept | accept | reject |
| scope with space | accept | reject | reject |
| breaking bang | accept | accept | accept |
| breaking footer | accept | accept | accept |
| type bump | reject | accept | reject |
| unknown type | reject | reject | reject |
| uppercase type | reject | reject | reject |
| no type | reject | reject | reject |
| empty subject | reject | reject | reject |
| subject Sentence case | reject | accept | accept |
| subject UPPER | reject | accept | accept |
| subject Start Case | reject | accept | accept |
| subject trailing period | reject | accept | accept |
| header 100 chars | accept | accept | accept |
| header 101 chars | reject | accept | accept |
| body line 100 | accept | accept | accept |
| body line 101 | reject | accept | accept |
| body no blank line | accept | reject | accept |
| footer line 101 | reject | accept | accept |
| trailers | accept | accept | accept |
| merge commit | accept | accept | reject |
| revert generated | accept | accept | reject |
| leading whitespace header | reject | accept | reject |
| two spaces after colon | accept | accept | reject |
| no space after colon | reject | reject | reject |
| CRLF body | accept | accept | accept |
| non-ascii subject | accept | accept | accept |
| fixup | accept | accept | reject |

What a replacement would do:

- `cz check` in place of commitlint would stop checking subject case,
  trailing full stop, header and body and footer length and whitespace, and
  would start rejecting a body that follows the header with no blank line and
  accepting `bump`. `-l 100` restores only the header length. It would
  remove commitlint and its two helper packages.
- Using commitlint for the pull-request title would loosen three rules of the
  pattern (uppercase or underscore in a scope, `Merge …`/`Revert …`/`fixup!`
  titles, two spaces after the colon) and tighten others (case, full stop,
  length), and the title workflow would need an npm install; today it has no
  checkout.
- Neither changes the constitution bump: commitizen stays for `cz bump`.

Recommendation: commitlint owns the commit-message rules (no other tool has
its rules); commitizen keeps only the version bump. For the title, either keep
the pattern (status quo) or run commitlint on it. No tool changes until the
user decides; the question went to the develop session.
