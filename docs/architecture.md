# Three-plugin workspace

The [plugin reference](reference/plugins.md) lists the three portable packages,
their locations, identities and declared capabilities. Each capability is
specified anew from current needs as a feature under `specs/`; earlier projects
are not requirement, evidence or implementation sources.

## Current skeleton

Each package has a `plugin.json`; the code and work packages also have
`skills/`. Only `code` has a Deno workspace configuration. Current versions and MCP declarations come from
the [plugin reference](reference/plugins.md).
The `code` package contains the adapted Wondel Clean Code skill
and `clean_code.ts`, the Spec Kit, Ponytail, commit and verification skills, and
an MCP declaration without servers.
The `work` package contains the `quarto-authoring` and
`session-migrate` skills and an MCP declaration without servers; its business
capabilities have no implementation until new features specify them.
The `chat` package contains only its manifest and license; it
has no skills, Deno configuration, MCP declaration, scripts or persistent state.
No release has occurred, and actual client installation
remains open.

Root tasks reuse Deno and Ajv with the unmodified official Agent Plugins
schemas. `deno task check` runs the runtime doctor, formatting, lint, type
checks, plugin schema validation, Clean Code, architecture checks, the test
suites and the reference drift check. Biome formats and lints code and JSON with
one root `biome.json`, which keeps the Google TypeScript style settings, turns
on its floating-promise check, and bans runtime and I/O globals in `domain/`
folders; `deno fmt` formats YAML. Biome 2.5.14 runs through Deno's npm support,
and its package ships a platform-specific native binary that `deno.lock` pins.
The Clean Code skill keeps its own ESLint-based checker. `doctor` checks the
selected standalone Deno/Quarto executables and locked dependencies without
writing by default. `workflow` supplies execution mode, graph queries,
verification evidence and three additive skill triggers; `verify` uses that same
loop. Reuse those commands for later feature work.

The [command reference](reference/commands.md) lists every root task and the five
selected help entrypoints. `deno task docs:generate` refreshes exactly the two
files in `docs/reference/`; `deno task docs:check` rejects stale, missing or
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
or selects a model. Model selection remains a separate client decision.

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
Use `deno task --quiet <command>` for machine consumption; Deno's own banners
and launch failures are outside this contract, and Biome, `deno fmt` and Deno
test output keep their native form.

`deno task test:cli-contract` checks these rules with real child processes, and
help snapshots freeze the presentation. A copied-skill test checks that
clean-code runs outside the repository. Update the snapshots only after review
with `deno task test:cli-contract -- --update`, then rerun without updating.
The Clean Code skill and checker share mechanically selected files; see
the `code` package's [Clean Code skill](../plugins/code/skills/clean-code/SKILL.md). Adding a
workspace member does not make it an independently published JSR package.

The root README is a short project summary; use specs and docs for detailed
documentation. The dependency pins remain in `deno.json` and `deno.lock`, and
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

## Sharing and distribution

Reuse existing dependencies directly first. Add a package under `packages/` only
for a concrete shared need and register it in the root workspace. Shared
packages are implementation dependencies, not a fourth plugin. Plugins do not
deep-import another plugin's private files or open another plugin's private
operational store.

A shipped plugin must include its required package files or resolve explicitly
pinned runtime dependencies. Do not distribute `skills/` or package components
as symlinks into neighboring workspace directories. Development workspace
resolution is not proof that an isolated installation works. Reuse upstream
packaging tools if bundled shared code becomes necessary.

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
duplicate source trees elsewhere in the repository.

| Package | Owned skills |
| --- | --- |
| `plugins/code/skills` | `clean-code`, `git-commit`, `ponytail*`, `speckit-*`, `verification-before-completion` |
| `plugins/work/skills` | `quarto-authoring`, `session-migrate` |

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

`deno task test:plugin-skills` checks that the project keeps no skill discovery
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
- Every `git` hook is disabled in `.specify/extensions.yml`. Each worktree is
  created on its own feature branch, and the `before_specify` hook would create
  and switch to another branch inside it; the auto-commit hooks would bypass
  the constitution's commit rules. Only `speckit-git-validate` is packaged; it
  checks numeric or timestamp-prefixed branches against matching spec directory
  prefixes, so it does not validate unnumbered `feature/<name>` branches.
- `agent-context` writes its current-plan pointer to the gitignored
  `.claude/rules/current-plan.md`, which Claude Code loads and Codex does not.
  The pointer differs per worktree, and the root `AGENTS.md` is maintained as
  the user supplied it. Both after hooks are enabled and non-optional, and they
  require Python 3 with PyYAML. `deno task doctor` does not check this host
  dependency. Before use, run `python3 -c 'import yaml'`, or
  `"$SPECKIT_PYTHON" -c 'import yaml'` when that override is set. The bundled
  extension README has installation details.
