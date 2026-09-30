# Three-plugin workspace

The [plugin reference](reference/plugins.md) lists the three portable packages,
their locations, identities and declared capabilities. Each capability is
specified anew from current needs as a feature under `specs/`; earlier projects
are not requirement, evidence or implementation sources.

## Current skeleton

Each package has a `plugin.json`; the code and work packages also have
`skills/`. The `code` package has a small `package.json` that only declares
its exports for the import-boundary check, and its clean-code skill has its
own npm package manifest with the skill's dependencies. Current versions and
MCP declarations come from
the [plugin reference](reference/plugins.md).
The `code` package contains the adapted Wondel Clean Code skill
and `clean_code.ts`, the Spec Kit, Ponytail, commit and verification skills, and
an MCP declaration for the `backfire` server.
The `work` package contains the `quarto-authoring`, `session-migrate`,
`wiki-raw-import`, `wiki-consistency` and `backfire` skills and an MCP declaration for its own
`backfire` server, which
pseudonymizes student identifiers; its other business capabilities have no
implementation until new features specify them.
The `chat` package contains only its manifest and license; it
has no skills, package manifest, MCP declaration or scripts, and its
persistent state is the `chat` vault (see [Wiki storage](#wiki-storage)).
No release has occurred, and actual client installation
remains open.

Root tasks reuse Node.js and Ajv with the unmodified official Agent Plugins
schemas. `npm run check` (`turbo run check`) runs the runtime doctor, formatting, lint, the
shell check, type checks, plugin schema validation, Clean Code, architecture checks, the test
suites, the reference drift check, the own-code limit (see
[Own-code limit](#own-code-limit--2026-09-30)) and the document region check (see
[Document consistency](#document-consistency--2026-09-28)). gts 7.0.0 lints
JavaScript and TypeScript with Google's TypeScript rules and Prettier
formatting; its configuration bans runtime and I/O globals in `domain/`
folders. Prettier uses gts's settings for JSON and YAML. gts, ESLint 10.10.0
and Prettier 3.9.9 are pinned npm dependencies in `package.json`, with their
dependency tree pinned in `package-lock.json`.
Ruff 0.16.9 lints and formats Python; `tools/ruff/uv.lock` pins its environment.
The Clean Code skill keeps its own ESLint-based checker. ShellCheck 0.11.0,
which the Google shell style guide recommends, checks the repository's own
shell scripts: `npm run lint:shell` runs it on every `*.sh` file and on the
hooks in `scripts/git-hooks/` and `scripts/git-flow-hooks/`, but not on Spec
Kit's vendored scripts under `.specify/`. The root `.shellcheckrc` turns on
four optional checks for guide rules: `${var}` braces, quoted variables,
explicit `-z` or `-n` tests, and `[[ … ]]` in Bash or Ksh scripts. The scripts stay
POSIX `sh`, so the guide's Bash-only rule is not applied; neither are its
formatting rules, which ShellCheck does not check. `tools/shellcheck/` is a uv
project whose `uv.lock` pins `shellcheck-py` 0.11.0.1, the PyPI wheels of the
official binary; Orca's setup script syncs it. `doctor` checks the
selected standalone Quarto executable, uv, git-flow and lychee from
`PATH`, the Spec Kit, ShellCheck, Ruff, scc, doc-regions and
wiki-consistency environments, the git-flow configuration
and locked dependencies without writing by default. `workflow` supplies execution mode, graph queries,
verification evidence and three additive skill triggers; `verify` uses that same
loop. In REVIEW mode it asks the implementer or the orchestrator to review the
diff before each commit and leaves the independent review to the merge into `develop` or
`main` (see [Git flow](#git-flow--2026-09-27)). Reuse those commands for later
feature work.

The [command reference](reference/commands.md) lists every root task and the five
selected help entrypoints. `npm run docs:generate` refreshes exactly the two
files in `docs/reference/`; `npm run docs:check` rejects stale, missing or
unexpected output without changing files or the Git index. Authored guidance and
live Wiki data are outside both commands' scope.

Generation stages a complete pair and retains the prior pair through readback.
An interrupted publication leaves `docs/.reference-publication/` for the next
explicit generation to recover; unknown entries or conflicting changes stop
recovery and name that path. `check`, the existing `verify` loop and the PR
documentation job run the same drift check. The job definition alone does not
establish a successful hosted run or required branch protection.

Workflow difficulty is independent of execution mode, verification and model
selection. The same Git collector supplies workspace routing and each declared
plan task's literal file scope. Without a plan, difficulty describes the whole
workspace, including unrelated changes. It measures observed staged, unstaged
and untracked changes against the selected base, not future work. Reversals
between index and worktree are counted separately. Public-entry detection is a
file-path signal, not proof of a changed API signature.

Policy `coding-difficulty/1` evaluates the following conditions in order:

| Level | Mechanical condition | CLI guidance |
| --- | --- | --- |
| Unassessed (`null`) | Invalid plan/scope, no changed files, or unknown text line count | Gather observable changes before assessing |
| `very_difficult` | More than 20 files or 2,000 changed lines | Split and review the large scope |
| `difficult` | Public entry, deletion/rename/type/conflict, more than 5 files or 500 lines | Review the entry, structure or large change |
| `medium` | More than 2 files or 100 lines | Check related changes together |
| `easy` | More than 1 file or 20 lines | Implement and check the bounded change |
| `very_easy` | Remaining observed changes | Check the small single-file change |

The five labels reuse LOM vocabulary only. These initial project thresholds are
not a standardized or calibrated measure of coding difficulty. They infer no
runtime complexity, graph independence or model capability. The JSON result
includes the policy version, scope, level, Korean description and measured facts.
A required REVIEW can coexist with `very_easy`; difficulty never relaxes gates
or selects a model. Agents, models and efforts are chosen with the code
plugin's `model-choice` skill.

### Own-code limit — 2026-09-30

A feature branch may add at most 300 net lines of the repository's own code
against its merge base with `develop`, unless the user approves more
([feature 022](../specs/022-own-code-limit/spec.md), CHE-42). `npm run
own-code` (`scripts/own_code.ts`), part of `npm run check`, measures the
worktree and the merge base, prints both sizes and the net change, and fails
over the limit. The feature finish hook runs `npm run verify`, so the limit
also guards the merge into `develop`; `develop` itself measures net 0.

- scc 4.1.0 counts code lines, neither blank nor comment. `tools/scc/` is a uv
  project whose `uv.lock` pins `scc-bin` 4.1.0, the PyPI wheels of scc's
  release binaries; Orca's setup script syncs it.
- Code is a file whose scc language GitHub Linguist's data
  (`linguist-languages` 9.5.0) classes as programming, so Markdown, JSON,
  YAML and TOML do not count.
- Tests do not count: paths under a `tests/` folder or named `*_test.*` or
  `*.test.*`.
- Upstream copies do not count: files whose SHA-256 appears in an
  `UPSTREAM.md`, an `upstream.json` or a Spec Kit install manifest
  (`.specify/integrations/*.manifest.json`) of the same tree. A patched copy
  no longer matches, so it counts in full. Copies without recorded hashes,
  such as Ponytail's hook modules and Spec Kit's extension scripts, count as
  own code.
- The user's approval of a larger limit is a line
  `**Own-code limit**: <number>, approved by the user on <date>` that the
  branch adds to its records under `specs/`, `.specify/bugs/` or
  `.specify/assessments/`. A line already on `develop` does not count.

## CLI contract

The repository-owned entrypoints `doctor`, `workflow` (and its `verify` alias),
`clean-architecture`, `plugins:validate` and `clean-code` (including `--scope`)
use pinned Cliffy for help and parsing. A small shared serializer owns JSON
output, error serialization and exit classification; it is exported only as
the `code` package's `./cli` entry and bundled in the portable clean-code
skill.

| Outcome | Exit | stdout | stderr |
| --- | --- | --- | --- |
| `--help` / `-h` | 0 | Plain-text Cliffy help | Empty |
| Completed successfully | 0 | One command-specific JSON object | Empty |
| Invalid options, arguments or input-plan schema | 2 | Empty | Error JSON |
| Execution failure | 1 | Empty | Error JSON |
| Checks found violations | 1 | Empty | Error JSON with the full report in `details` |

Errors use `{ "error": { "code": "INVALID_ARGUMENT", "message": "..." } }`.
Codes are `INVALID_ARGUMENT`, `EXECUTION_FAILED` and `CHECK_FAILED`. The
`details` field sits beside `error` and keeps the checker or workflow report,
including loop evidence, graph diagnostics and skill guidance when a workflow
gate fails. A selected REVIEW mode is not a failed check and still exits 0.
Use `npm run --silent <command>` for machine consumption; npm's own banners
and launch failures are outside this contract, and gts, Prettier and Node
test output keep their native form.

`npm run test:cli-contract` checks these rules with real child processes, and
help snapshots freeze the presentation. A copied-skill test checks that
clean-code runs outside the repository. Update the snapshots only after review
with `npm run test:cli-contract -- --update`, then rerun without updating.
The Clean Code skill and checker share mechanically selected files; see
the `code` package's [Clean Code skill](../plugins/code/skills/clean-code/SKILL.md). Adding a
workspace member does not make it an independently published JSR package.

The root README is a short project summary; use specs and docs for detailed
documentation. The dependency pins remain in `package.json` and `package-lock.json`, and
the Ajv subpath mapping uses the same approved package version.

## Package and runtime ownership

Each plugin is independently selectable and must eventually pass installation
and capability checks without either of the other two plugin packages present. A
plugin can contain skills, MCP entries, or both. Final checks cover Codex CLI and
Claude Code: actual selected components, MCP processes, required hooks and
permission/data paths; a manifest check or empty component list is insufficient.
Three plugins do not require three servers, databases, or continuously running
processes.

The `code` package reuses selected upstream skills and tools.
The `chat` package targets the ChatGPT and Claude chat projects and has no
skills yet; actual distribution and invocation remain separate from local
validation. Business capabilities belong to the `work` package once
features specify them. Create TypeScript entry points, source directories and
internal layers only when a specified capability has an actual consumer. Selected
Wiki storage follows constitution principle VI; restructuring code does not move
live data or other external operational or source roots.

### Wiki storage

The Wiki instances, called vaults, live in
`$XDG_DATA_HOME/verbose-broccoli/vaults/` (by default under
`~/.local/share`), outside the repository, one folder per vault:

| Vault | Holds |
| --- | --- |
| `default` | Knowledge that belongs to no single plugin |
| `chat` | Exported conversations as raw evidence and the pages written from them; the chat package's persistent state |
| `code` | Coding knowledge for work in any project: libraries, patterns, decisions. It is not this repository's development memory, which stays in the Spec Kit records, code and Git |
| `work` | Education work: the raw imports, including exported conversations, and the per-student pages |

Each vault holds the schema `AGENTS.md`, `raw/{web,files,notes,assets}/` and
`wiki/`, and its own Git repository versions the schema and `wiki/` but
ignores `raw/`. A plugin's Wiki skills use the vault named after the plugin
unless the user selects another; `default` is always selected by name. Vaults
are the user's shared Wiki storage, not a plugin's private store, so any
plugin's Wiki tool may write a vault the user selects.

The work plugin's `wiki-raw-import` skill creates a vault and copies documents
the user confirms into its `raw/`, in `work` unless another vault is named.
Only the `chat` and `work` vaults admit exported conversations; the skill
admits each ChatGPT export into both. Each copy is one
read-only BagIt bag whose `bag-info.txt` records the source ID, the original
path and modification time, and the admission time, and whose manifest holds
the SHA-256 digest. The bags
are the only record of sources and revisions. The user's exclusions live in
`$XDG_CONFIG_HOME/verbose-broccoli/config.toml`; import staging and the
one-run lock live under the cache and state roots.

### Wiki consistency

Wiki pages follow the region model of repository documents (below): each part
is a mechanical region that a generator rebuilds from named instance files, or
agent-written text that backfire judges. The engine is the uv project
`packages/wiki-consistency/`, which calls `packages/doc-regions/` as a library
with the instance as its root; the work plugin's build ships both projects,
and the plugin's `wiki-consistency` skill runs the commands. The instance's
`AGENTS.md`, from the `wiki-raw-import` skill's template, states the rules.

- Pages are written in English, whatever the language of the raw evidence,
  which stays unchanged; student names keep the roster's spelling so backfire
  still replaces them, a school is written as its domain ID, and a short
  direct quote may stay next to its translation.
- Pages carry YAML front matter with a title, a one-line summary, the
  source revisions they cite and one or more topics. A vault groups its
  pages by topic instead of splitting into more vaults; the front matter of
  its `AGENTS.md` declares the topics its pages may list, and the layer
  folders stay as they are. `index.md` is one mechanical region,
  `page_catalog`, built from that metadata, which lists the pages under a
  heading per topic; a source page may hold a `source_provenance` region
  built from its bags. `overview.md` is written by the agent, and `log.md`
  is append-only and never judged.
- `check` runs before every commit of the instance. It fails on a stale or
  malformed region, a broken link (lychee, offline), missing or unresolvable
  page metadata, a missing or malformed topic list in `AGENTS.md`, a page
  topic that list does not declare, a cited bag that fails BagIt's fast
  validation, or a changed earlier `log.md` entry, and it lists orphan pages
  and citations of non-latest revisions. It also tests the page rules that a
  pattern can tell, outside mechanical regions, the front matter's `sources`
  field and `log.md`: phone numbers, email and postal addresses and
  registration numbers; a student page (`wiki/students/<name>.md`) whose
  name is not in backfire's roster; Hangul, Chinese or Japanese text other
  than roster names and one quote of at most 100 characters in quotation
  marks with its English translation in parentheses beside it; roster
  school names in Hangul outside such a quote, instead of domain IDs; and
  dates not written as YYYY-MM-DD or times without a zone. The language,
  school and date rules skip link targets outside code, which a page
  cannot change without breaking the link.
  Roster names, phone numbers and email addresses are found with the work
  build's own `backfire_education` code, so the check sees them as backfire
  replaces them; it reads the roster only when a page needs it. A failure
  never repeats the matched text. It writes nothing, uses no network and
  needs no cache. `update` regenerates stale regions.
- The judgment step runs at the end of an operation that changed pages, and
  over the whole Wiki in a lint. `convert` turns cited revisions into
  Markdown under `$XDG_CACHE_HOME/verbose-broccoli/wiki-evidence/` (by default
  `~/.cache`) (1 GiB budget): markitdown 0.1.8 reads XLSX and other supported
  formats, and python-hwpx 6.6.0 reads HWP and HWPX. An HWP file that
  python-hwpx converts only in part keeps its text and is listed under
  `partial`, with a `<revision>.partial.json` mark beside the text. Scanned
  PDFs remain unreadable, so claims resting only on them are unverifiable.
  `index` builds qmd 2.8.3
  collections of the pages and the converted evidence under
  `$XDG_CACHE_HOME/verbose-broccoli/qmd/` (3 GiB budget), with the multilingual
  Qwen3 embedding model, a 610 MB download on first use. Without the model,
  keyword search alone finds no other page for a whole paragraph, so
  `prepare` then checks units only against their evidence and says that it
  searched no other pages. `prepare` prints
  `jev_verify` requests (units against their cited evidence, and against
  candidate units of other pages), `jev_find` cross-reference requests
  in a lint, and `jev_classify` requests for new units. qmd only finds
  candidates; backfire judges.
- The agent sends the requests to the work plugin's backfire server, which
  replaces the roster's student, guardian and school names, phone numbers
  and email addresses before the provider call and sends all other text as
  it is, and confirms a contradiction between two pages with `jev_compare`.
- `npm run wiki-consistency:install` installs both environments, after
  backfire's with its `education` extra, which `wiki-consistency` uses as a
  library; Orca's setup script runs the same installs, and `npm run
  doctor` checks them and Node.js 24.12.0 or later. `npm run test:wiki-consistency` runs
  the package's tests.
- Not automated: sending the requests and acting on the results, accepting
  suggestions, updating stale citations, writing `log.md` entries, applying a
  new schema template to an existing instance, and converting scanned PDFs.

### Backfire server

`plugins/code/mcp.json` and `plugins/work/mcp.json` both declare the `backfire`
stdio server and start it from the repository with `uv --directory
${PLUGIN_ROOT}/../../packages/backfire run --frozen --offline --no-sync
backfire serve-mcp`, the work plugin adding `--education`; backfire is used
from the repository and never installed. The server is PyModel's
jev-judge-mcp 0.6.0, a pinned PyPI dependency: backfire's entry point builds
PyModel's server from PyModel's tools plus `jev_noul` and passes PyModel's
runtime a provider factory. The factory reads backfire's profiles from
`packages/backfire/src/backfire/config.toml` (code),
`packages/backfire/src/backfire_education/config.toml` (work) and the
optional `$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml`, and
builds either a general-model provider through system-one-adapter (Hive by
default) or a Jev provider: PyModel's own, or the Vercel AI Gateway
provider ported from jev-agent-tools. With `--education` it wraps that
provider with the pseudonymization module in
`packages/backfire/src/backfire_education/`. What backfire needs from
PyModel's own code (CHE-38) is prepared as a patch for PyModel in
`specs/021-backfire-rebuild/upstream/`. See the
[Backfire operator guide](backfire.md) for setup, profiles and
troubleshooting.

## Sharing and distribution

Reuse existing dependencies directly first. Constitution IX puts reusable
implementation packages, including libraries and MCP servers, under
`packages/<name>/src/`; add one only for a concrete shared need. A package joins
a toolchain workspace only when it has executable code for that toolchain, so
the Python package `packages/backfire/` joins the root uv workspace and no npm
workspace.
Shared packages are implementation dependencies, not a fourth plugin. Plugins do not deep-import
another plugin's private files or open another plugin's private operational
store; Wiki vaults are not such a store (see [Wiki storage](#wiki-storage)).

The code and work plugins are used from the repository checkout and never
installed: their `backfire` server runs from `packages/backfire` through a
repository path in `mcp.json` (the user's decision of 2026-09-30), so a copy
of a plugin outside the repository cannot start it. Do not distribute
`skills/` or package components as symlinks into neighboring workspace
directories. Development workspace resolution is not proof that an isolated
installation works. Reuse upstream packaging tools if an installable plugin
becomes necessary.

Use root `plugin.json`, `skills/`, and `mcp.json` according to
[Agent Plugins 1.0](https://agent-plugins.org/specification). Client-specific
adapters remain separate future work. Clients load the packaged skills from the
plugin folders: Claude Code directly, for example with `--plugin-dir` or
`CLAUDE_CODE_PLUGIN_DIRS`, and Codex and OMP through a local marketplace install,
which copies each plugin, so edited plugins must be reinstalled there. The
project keeps no `.agents/skills` or `.claude/skills` links, which would list
every packaged skill twice. OMP does not offer a plugin skill that declares
`argument-hint`, so OMP needs `ponytail` in its user skills folder,
`~/.omp/agent/skills`. Marketplace registration, host config changes, and
global skill migration remain separate.

### Skill source ownership — 2026-09-14

Maintain each skill only in its owning package, without discovery links or
duplicate source trees elsewhere in the repository. The one exception is the
`backfire` skill: the code and work plugins each carry a vendored copy of the
same upstream skill, because a plugin may not link to another plugin's files,
and `scripts/plugin_skills_test.ts` keeps the copies' shared files identical.

<!-- [[[cog import doc_sources; cog.out(doc_sources.skill_table("plugins/*/skills/*/SKILL.md")) ]]] -->
| Package | Owned skills |
| --- | --- |
| `plugins/code/skills` | `backfire`, `clean-code`, `git-commit`, `model-choice`, `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-review`, `speckit-agent-context-update`, `speckit-analyze`, `speckit-assess-decide`, `speckit-assess-define`, `speckit-assess-intake`, `speckit-assess-research`, `speckit-assess-shape`, `speckit-bug-assess`, `speckit-bug-fix`, `speckit-bug-test`, `speckit-checklist`, `speckit-clarify`, `speckit-constitution`, `speckit-converge`, `speckit-git-validate`, `speckit-implement`, `speckit-plan`, `speckit-specify`, `speckit-tasks`, `speckit-taskstoissues`, `verification-before-completion` |
| `plugins/work/skills` | `backfire`, `quarto-authoring`, `session-migrate`, `wiki-consistency`, `wiki-raw-import` |
<!-- [[[end]]] -->

`session-migrate` owns task handoff and resumption, including checks of current
sources.

Ponytail's unchanged upstream modules and tests live in `plugins/code/hooks`
and `plugins/code/tests`. `.agents/ponytail` is a compatibility link to that
package, so the commands in `.codex/hooks.json` and their trust hashes stay
unchanged. The instruction loader finds the packaged skill without a link out
of the package. Runtime state remains in the Git-local `ponytail` directory.
Client hook registration remains project configuration, not a new portable
hook manifest. The existing project policy hook is separate from this migration.

Skill licenses, provenance, templates, references and invocation metadata move
with their sources. Spec Kit continues to operate on the target project's
initialized `.specify` scripts, templates and constitution; those project assets
are not moved into the plugin. Quarto retains its existing host runtime
requirement.

`npm run test:plugin-skills` checks that the project keeps no skill discovery
links and that `.agents/ponytail` resolves to the `code` package, copies skill
resources into temporary packages without workspace links, then runs the
upstream Ponytail checks. This checks resource packaging; client installation
and native invocation still need their own acceptance.

### Spec Kit extensions — 2026-09-27

The project uses Spec Kit's bundled `agent-context`, `assess`, `bug` and `git`
extensions, installed under `.specify/extensions/`. `specify extension add`
writes their skills to `.agents/skills`; following the table above, the ten in
use live in `plugins/code/skills` instead.

- `assess` and `bug` run only when invoked. They keep their records in
  `.specify/assessments/<slug>/` and `.specify/bugs/<slug>/`.
- One local preset, `linear-issue` in `.specify/presets/`, adds an `append`
  layer to the spec template for the feature's Linear issue line (see
  [Linear](#linear--2026-09-27)). Spec Kit's `specify preset add --dev`
  installed it and wrote `.specify/presets/.registry`; `specify preset resolve
  spec-template` shows the layers.
- Every `git` hook is disabled in `.specify/extensions.yml`. Each worktree is
  created on its own feature branch, and the `before_specify` hook would create
  and switch to another branch inside it; the auto-commit hooks would bypass
  the constitution's commit rules. Only `speckit-git-validate` is packaged; it
  checks numeric or timestamp-prefixed branches against matching spec directory
  prefixes, so it does not validate unnumbered `feature/<name>` branches.
- `agent-context` writes its current-plan pointer to the gitignored
  `.claude/rules/current-plan.md`, which Claude Code loads and Codex does not.
  The pointer differs per worktree, and the root `AGENTS.md` is maintained as
  the user supplied it. Both after hooks are enabled and non-optional. They run
  Python with PyYAML from `SPECKIT_PYTHON`, which `.claude/settings.json` and
  `.codex/config.toml` set to `tools/spec-kit/.venv/bin/python`.
- `tools/spec-kit/` is a uv project whose `uv.lock` pins the Spec Kit CLI
  1.0.12 (commit `e77daa9`), PyYAML and Python 3.14; `pyproject.toml` requires
  uv 0.11.32. Orca's setup script runs `uv sync --locked --project
  tools/spec-kit` in each worktree to create the gitignored `.venv`, and
  `npm run doctor` fails when that environment is missing or differs from the
  lock. Run Spec Kit from the repository root as
  `uv run --project tools/spec-kit specify …`.

### Git flow — 2026-09-27

Features are finished into `develop` with git-flow-next 2.1.0
(<https://github.com/gittower/git-flow-next>, BSD-2-Clause). Its source is
unchanged; only its settings and one hook adapt it to the constitution's git
flow rule.

- git-flow-next is a host tool at `~/.local/bin/git-flow`, installed from the
  release's linux-amd64 archive after checking it against the release's
  checksum file. Orca's setup script requires it, trusts the committed hook
  path and runs `git flow config sync`. `npm run doctor` checks its version
  and that the local Git config matches `.gitflow`.
- `.gitflow` configures only `main`, `develop` and `feature/`. Features merge
  with `--no-ff`, keep their branch, never fetch or push, and are updated from
  `develop` by merge, not rebase. Release and hotfix types are left out, so
  `git flow release` and `git flow hotfix` refuse to run; the constitution has
  releases and hotfixes finished by hand.
- Before the finish, a fresh reviewer from the other provider (Claude Code or
  Codex), given only the scope and requirements, reviews the feature tip,
  favoring speed. After its findings are resolved, a content-free commit
  records the review:

  ```sh
  git commit --allow-empty -m 'chore(review): record develop merge review' \
    -m "Reviewed-by: <reviewer, for example provider and model>
  Reviewed-commit: $(git rev-parse HEAD)"
  ```

  Any later commit on the feature, including a merge of `develop`, needs a new
  review and a new record.
- Run `git flow feature finish <name>` in the `develop` worktree. The hook
  `scripts/git-flow-hooks/pre-flow-feature-finish` refuses the finish unless
  that worktree is on `develop` with no uncommitted changes, `develop` is an
  ancestor of the feature, the feature is checked out in a clean worktree, its
  tip is a review record, every non-merge feature commit that changes the
  constitution passes the version rule against its parent, and `npm run
  verify` passes there. A review record has one parent and the same tree as
  that parent, exactly one non-empty `Reviewed-by` trailer, and exactly one
  `Reviewed-commit` trailer that resolves to the parent. The merge then has
  Git's default message, its parents are `develop` and then the review record,
  and its tree is the reviewed and verified feature tree. `npm run
  test:git-flow` checks these cases with the real binary.
- Orca's setup script gives a new worktree's branch its git flow name, because
  `orca worktree create` has no branch option and turns a `/` in `--name` into
  `-`. `scripts/worktree-branch.sh` maps the worktree's folder name:
  `release-<rest>` becomes `release/<rest>`, `hotfix-<rest>` becomes
  `hotfix/<rest>`, and any other name becomes `feature/<name>` without a
  leading `feature-`. It renames only a branch that has no upstream and no
  commits of its own, never `develop` or `main`, and changes nothing on a
  second run; folder names stay flat. Remove the script and its setup line
  once `orca worktree create` offers a branch option. `npm run
  test:worktree-branch` checks it.
- Not automated: deciding that a feature is ready, running the merge review,
  updating a feature after `develop` moves (merge `develop` into it, verify,
  review, then finish again), resolving conflicts, releases, hotfixes, the
  review before a release or hotfix merges into `main`, and pushing.

### Commit messages — 2026-09-27

Every commit in a set-up worktree passes the `commit-msg` hook
`scripts/git-hooks/commit-msg`. It runs commitlint 21.2.3
(<https://github.com/conventional-changelog/commitlint>, MIT) with
`@commitlint/config-conventional` and the Conventional Commits parser preset
from `conventional-changelog-conventionalcommits` 10.4.0, pinned in `package.json`
and `package-lock.json` and run by `npm run commitlint`.

- Headers must follow Conventional Commits 1.0.0 as `config-conventional`
  defines it. Any trailer is accepted, including `Spec-Kit-Task`,
  `Reviewed-by`, `Reviewed-commit` and `Co-Authored-By`. commitlint's default
  ignores skip Git's default merge messages, so git-flow finishes and
  hand-finished merges pass. At commit time, commitlint's default ignores also
  skip other messages, such as those starting with `fixup!`, `squash!`,
  `amend!`, `Revert ` or `Reapply `.
- One local rule, in `scripts/constitution_version.ts`, compares
  `.specify/memory/constitution.md` in `HEAD` with the index being committed.
  A commit that changes the file must raise its version exactly one step: a
  breaking commit (`!` or a `BREAKING CHANGE` footer) the first digit, `feat`
  the middle digit, `docs` or `fix` the last digit. Other types and an
  unchanged version are refused. A breaking change also needs the user's
  approval before it is committed, which the hook cannot check.
- An amend is compared with `HEAD^`, the parent of the commit it replaces, so
  it keeps the version that commit set. Git does not tell a `commit-msg` hook
  about `--amend`, so the hook reads the arguments of the `git` process that
  runs it from `/proc/$PPID/cmdline`. When one is `--amend` or an abbreviation
  git accepts (`--am`, `--ame`, `--amen`) and no later `--no-amend` form
  cancels it, the hook sets `CONSTITUTION_VERSION_AMEND` for the rule;
  otherwise it clears any inherited value. Where those arguments cannot be
  read, an amend is compared with the commit it replaces, as before this rule
  handled amends, so it can be refused or accepted wrongly. The hook does not
  know which options take a value, so a value such as the message in
  `-m --amend` counts as the flag: a new commit is then compared with `HEAD^`,
  and a value `--no-amend` hides a real amend.
- `git rebase -i` does not run `commit-msg` for `fixup` or `squash`. Before a
  feature finish, the hook checks each non-merge feature commit that changes
  the constitution against its parent and its own tree. This check disables
  commitlint's default ignores and applies only the version rule, so combined
  commits and `fixup!` messages are checked. A refusal names the commit and
  branch; rewrite it, then review and record again.
- The configuration is `scripts/commitlint.config.mjs`. commitlint loads a
  TypeScript configuration through jiti, which cannot resolve `npm:`
  specifiers, and resolves the preset's package name with `require.resolve`,
  which needs `node_modules`; so the configuration is plain JavaScript and
  passes the preset's parser options directly.
- Git finds the hook through the repository setting `core.hooksPath =
  scripts/git-hooks`. The path is relative, so each worktree runs its own
  checkout's hook, and a worktree whose checkout has no `scripts/git-hooks/`
  runs none. Orca's setup script sets it, and `npm run doctor` fails when it
  differs. The hook finds Node.js on `PATH` and refuses
  the commit when it is missing.
- `npm run test:commit-msg` checks the rule and real commits in temporary
  repositories.

### Linear — 2026-09-27

The project tracks its work in Linear's free plan, in the workspace
`verbose-broccoli` with one team, `cherry-pick-foundation` (key `CHE`), and
reaches it only through Orca: the `orca linear` commands and Orca's
`orca-linear` skill. No Claude Code or Codex Linear plugin and no Spec Kit
Linear extension is used. The design and its reasons are in
[specs/007-linear-usage/](../specs/007-linear-usage/).

- An issue is a to-do entry for one feature or bug; `tasks.md` stays the
  detailed task record. There are no sub-issues. Each issue has one type label
  (Feature, Bug or Improvement) and a plugin label (`code`, `work`, `chat`) for
  each plugin the work concerns; repository-wide tooling has none.
- Only the main agent writes to Linear, after searching for similar issues,
  including archived ones (`orca linear list-issues --team CHE --query <words>
  --include-archived`). Workers report out-of-scope bugs to it through Orca
  messages. Linear is an external service, so issues and comments never hold
  operational data or secret values. Both rules are in the root `AGENTS.md`.
- A feature's worktree is linked to its issue when it is created (`orca
  worktree create … --linear-issue CHE-<n>`, or `orca worktree set` later),
  and its spec names the ID in one header line, `**Linear issue**: CHE-<n>`.
  The Spec Kit preset `linear-issue` in `.specify/presets/` appends that line,
  with instructions, to the spec template. Commits and branch names carry no
  issue ID; a bug's `assessment.md` keeps the issue URL.
- Merging into `develop` completes the issue. The main agent commits the
  record on the feature branch, moves the issue to In Review, runs the merge
  review and finish described under [Git flow](#git-flow--2026-09-27), then
  moves the issue to Done with one completion comment giving the merge commit
  and the record location instead of a PR link. `npm run workflow` prints
  this order in every mode. The commands are in
  [the life-cycle contract](../specs/007-linear-usage/contracts/linear-lifecycle.md).
- Issues are archived, never deleted. The free plan counts only non-archived
  issues toward its limit of 250, and Linear archives closed issues one month
  after they close (Team Settings > Issue statuses & automations); archived
  issues stay readable with `--include-archived`. Nothing monitors the count:
  a failed creation at the limit is the signal, and the main agent reports it
  to the user.
- Orca cannot archive or delete issues or create labels, projects, documents,
  cycles or milestones. Label, project and team-setting changes happen in
  Linear's UI, and no other Linear integration is added; the same `npm run
  workflow` instruction says so.

### Document consistency — 2026-09-28

`README.md`, `docs/architecture.md` and `docs/backfire.md` follow one region
model, from [feature 008](../specs/008-doc-consistency/spec.md). Every part of
these target documents is either a mechanical region, written by a generator,
or an agent region, written by agents. No part is human-written.

- A mechanical region is a Cog block (cogapp 3.6.0, MIT) in HTML comments. Its
  code is one call of a function in `scripts/doc_sources.py`, whose arguments
  name the repository files or globs it reads. The marker syntax and its rules
  are in the [regions contract](../specs/008-doc-consistency/contracts/regions.md).
  Documents link to it instead of quoting a marker, because Cog would run a
  quoted marker as a region.
- Everything else is an agent region. Backfire judges it before each `develop`
  merge review.
- `scripts/doc_regions.toml` lists the targets, and `AGENTS.md` and the
  constitution as report-only documents. `specs/`, vendored skills and the
  generated `docs/reference/` are not listed. A plugin document becomes a
  target when the project writes one.
- To add a mechanical region, add a function to `scripts/doc_sources.py` and a
  test to `scripts/doc_sources_test.py` with fixture sources, the exact output,
  and a missing source that raises. The function reads only its named sources
  and uses no network, clock or environment. Then put the markers around the
  text in a target and run `npm run doc-regions:update`.
- `npm run check`, and so `npm run verify`, runs `npm run
  doc-regions:check`. It fails when a region differs from its generator's
  output, a marker is malformed or names a missing source, or a target links
  to a missing local file or heading (lychee 0.24.2, offline). It writes
  nothing and uses no network. `npm run doc-regions:update` regenerates
  stale regions.
- Before each `develop` merge review, the main agent runs the judgment step
  that `npm run workflow` prints in REVIEW mode. `npm run
  doc-regions:prepare -- --base develop --max-evidence-chars <n>` splits the
  agent regions into units with markdown-it-py 4.2.0 (MIT). It prints
  `jev_verify` requests, with units as claims and the feature diff as
  evidence, and `jev_classify` requests for the units the feature added.
  The agent sends them through its MCP client. It corrects target units judged
  contradicted or flagged for review, or records why they stand, and decides
  which suggested candidates become mechanical regions.
- `npm run doc-regions:audit` runs MemoryLint 1.5.1's read-only audit (MIT)
  on `AGENTS.md` and the constitution. It downloads the pinned archive once
  into `~/.cache/verbose-broccoli/memorylint/1.5.1/` after a hash check.
  Findings for these two files, from the audit or from backfire, are only
  reported to the user; the tooling never changes them.
- The engine is the uv project `packages/doc-regions/`. Orca's setup script
  syncs it, and `npm run doctor` checks its environment and lychee's version.
  Feature 010 calls its modules as a library, with a Wiki instance as the root
  and its own targets, generators and evidence.
- lychee is a host tool at `~/.local/bin/lychee`, installed from the release's
  x86_64 Linux archive after checking it against the release's checksum.
- Not automated: sending the backfire requests and acting on the results,
  reporting drift in `AGENTS.md` and the constitution to the user, choosing
  which candidates become mechanical regions, and installing lychee.
