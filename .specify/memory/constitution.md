<!--
Sync Impact Report
- Version: 2.1.0 -> 2.2.0 (`feat` commit, so a minor bump).
- Input: Linear CHE-32, feature 019 (`specs/019-turborepo/`): the user's
  2026-09-29 decision to replace Deno with Node.js and Turborepo for the
  repository's tooling and to make the three Python packages one uv
  workspace.
- Modified principles: IX (the toolchain-workspace example and the chat
  package's declarations no longer name Deno).
- Modified sections: Development Workflow and Quality Gates (the workflow and
  verification commands are `npm run workflow` and `npm run verify`);
  Governance (the decision record and the version).
- Added sections: none. Removed sections: none.
- Follow-up (outside this document): feature 019 changes `AGENTS.md`'s
  commands the same way.
- Deferred placeholders: none.
-->

# verbose-broccoli Constitution

## Core Principles

### I. Proven Dependencies and Storage

Project code MAY use any programming language and runtime. Pin dependency
resolution. Quarto remains a separately installed document converter. Durable
relational storage MUST use PGlite.

### II. Deliver Working Capabilities and Preserve Data

Error wording, equivalent JSON number spellings and generated formatting are
not acceptance criteria unless a specification makes them so. Planned-only
capabilities MUST remain explicit backlog, never counted as implemented.

### III. Preserve Sources and Data Ownership

Search normalization MUST NOT become an identity key.

### IV. Capabilities From Current Needs

Earlier projects, their code, tests, captures, ledgers and data are not
requirement, evidence, implementation or migration sources, and target code
MUST NOT depend on them. Importing existing user data is a separately specified
capability.

### V. Observable Acceptance

Acceptance MUST exercise positive, negative, and boundary behavior with
synthetic fixtures or selected copies. Required cases include continued protocol
service after bad input, path and resource isolation, duplicate/conflict
handling, interrupted writes, actual file readback, unchanged originals, and
recovery at relevant failure points. Differential checks MUST use an
independently reviewed contract. Package installation, version strings, type
checks, and test counts do not prove runtime, browser, hardware, or operational
compatibility. Record every unperformed check accurately.

### VI. Wiki Layers and Storage Ownership

For the user-selected Wiki layout, each Wiki instance, called a vault, MUST
contain three distinct layers:

1. **Raw** is immutable original evidence under `raw/`, organized as `web/`,
   `files/`, `notes/`, and `assets/`. LLM maintenance MUST NOT edit or delete
   admitted raw bytes. Changed evidence creates a new source revision while
   earlier revisions remain resolvable and recoverable. Conversation records and
   exported chats are not Raw evidence; they stay outside the vault in the
   user's workspace. The `chat` and `work` vaults are the exceptions: exported
   conversations are Raw evidence there.
2. **Wiki** is durable maintained Markdown knowledge under `wiki/`. The LLM
   maintains pages, cross-references, `overview.md`, and the append-only
   `log.md`; `index.md` is regenerated from page metadata. Source summaries
   belong in `sources/`; entities, concepts, comparisons, and synthesis retain
   their own directories. Adopted knowledge MUST NOT be classified as
   disposable because it was LLM-authored. Git owns its history.
3. **Schema** is the instance's `AGENTS.md`, above `raw/` and `wiki/`. It defines
   page conventions and ingest/query/lint workflows. It has its own versioned
   history and MUST NOT be confused with the repository's development AGENTS.md
   or a duplicate runtime-settings file.

Use the `verbose-broccoli` namespace under XDG configuration, data, state,
and cache roots. The defaults are `~/.config/`, `~/.local/share/`,
`~/.local/state/`, and `~/.cache/` respectively. Configuration owns `config.toml`
and profile files; durable data owns `registry.json` and `vaults/`, which holds
one folder per vault: `default` for knowledge that belongs to no single plugin,
and `chat`, `code` and `work` for the plugins of those names. Restart/recovery
state belongs in state storage. Only
rebuildable indexes, embeddings, chunks, parsed data, temporary downloads and
temporary work belong in cache. Cache cleanup MUST preserve raw evidence,
adopted Wiki knowledge, instructions, configuration, registry and operational
state. Direct Wiki index navigation and page reading MUST work without cache.

Raw sources and private user data MUST NOT enter the product source repository.
Raw sources MUST NOT enter the Wiki's versioned knowledge tree. Do not add parallel per-page revision
registries or a permanent generated-output archive.

### VII. One Decision Owner and Minimum Implementation

Repository reference tables for selected plugin, server and command facts MUST
derive from their existing manifests, configuration and command definitions.
Generated reference files MUST have deterministic output and a non-mutating
drift check in repository verification. Authored introductions and design
decisions retain their own edit scope; a reference refresh MUST NOT rewrite
them. Document agreement proves agreement with declared inputs, not runtime
availability or operational acceptance. These committed repository reference
files are outside principle VI's Wiki content classification.

Retries MUST preserve the requested purpose, mode, count, scope and success
conditions. Report incomplete work honestly; do not substitute another task and
call it success.

Every persistent generated writer MUST have a positive storage budget and
explicit success, failure and interruption cleanup before accumulation begins.

Follow the user's root AGENTS.md reuse order strictly for every existing custom
implementation as well as new work, including unmerged branches and every
language. Existing code is not grandfathered. Verify existing or upstream
implementations before writing adapters; locally owned code is limited to
necessary integration and domain-specific glue. Do not add speculative
services, compatibility copies or configuration matrices.

### IX. Three Plugin Packages

The repository MUST use exactly three plugin package roots:
`plugins/chat`, `plugins/code`, and `plugins/work`. Their plugin IDs are
`chat`, `code`, and `work`.
Use `packages/` for reusable implementation packages, including libraries and
MCP servers. Keep their source code under `packages/<name>/src/`; do not retain
empty placeholders.
Use `tools/` for development/release programs, `scripts/` for repository
automation and its checks, including workspace integration and contract checks,
`docs/` for explanations and their assets and examples, `specs/` for feature
work, and `infra/` for environment/deployment files. Examples require actual
content.
Preserve repository verification results under `artifacts/`. Content drafts
and user deliverables stay outside the repository; deliverables go in the user's
documents folder. A directory rename does not authorize deleting its contents.
Each plugin is its own Agent Plugins 1.0 package root and independently
selectable. Skills and MCP components are added only for selected capabilities.
A package joins a toolchain workspace, such as the uv workspace, only when it
has executable code for that toolchain.
The chat package has no skills yet and no MCP declaration or scripts;
its persistent state is the `chat` vault (principle VI).
Code and Work run in Codex CLI and
Claude Code, and no plugin depends on the desktop hub that launches them.
Do not require one repository-wide runtime, server or composition entry point.

Business capabilities belong to the work package. A shared package
requires an actual consumer need; no common framework is created in advance.
Plugin versions may move together; there is no new per-module release framework.

## Product and Data Boundaries

- Retain existing source and storage roots unless a specified capability changes
  them; a changed plan is not a reason to delete their contents.
- Private records and credentials MUST NOT enter committed fixtures, snapshots,
  or reports. Inventories may record ownership/integrity without recording
  private contents.
- Repository prose is English; required Korean outputs, exact source evidence,
  identifiers, and language test cases retain their original text.

## Development Workflow and Quality Gates

- Follow specification, necessary clarification, plan, tasks, consistency
  analysis, implementation, and acceptance. Planning completes no implementation
  task ID.
- Follow the existing `npm run workflow` execution instructions. This project
  imposes no separate agent headcount or default sequential-only restriction.
  Parallel workers use the workflow's disjoint writable scopes; main owns shared
  files and integration.
- Use upstream [git-commit](https://github.com/github/awesome-copilot/blob/main/skills/git-commit/SKILL.md)
  for explicitly requested local Conventional Commits. Related task IDs MAY
  share a branch or commit. Include a `Spec-Kit-Task: Txxx` trailer for each
  covered implementation ID. Preserve unrelated work and foreign index entries.
- Branch with git flow. `main` holds released states and `develop` integrates
  work; `feature/<name>` and `release/<version>` branches start from `develop`,
  and `hotfix/<version>` branches from `main`. Finish each with a
  no-fast-forward merge (`git merge --no-ff`) and Git's default merge message,
  which keeps the branch's commits together: a feature into `develop`; a
  release or hotfix into `main`, tagged `v<version>` there, then into
  `develop`. The merge commit's parents MUST be exactly the target, then the
  source. Before a feature is finished, a fresh reviewer from the other
  provider (Claude Code or Codex), given only the scope and requirements,
  reviews it, favoring speed; after its findings are resolved, a content-free
  review-record commit on the feature tip names the reviewer in a
  `Reviewed-by` trailer and the reviewed commit, its parent, in a
  `Reviewed-commit` trailer. Finish a feature with git-flow-next, `git flow
  feature finish <name>`, run in the `develop` worktree: the committed
  `.gitflow` settings and the `scripts/git-flow-hooks/pre-flow-feature-finish`
  hook refuse the finish unless `develop` is an ancestor of the feature, the
  feature tip is such a review record, each non-merge feature commit that
  changes this constitution passes the version rule in Governance, and the
  feature passes `npm run verify`, so the merge commit's tree is the reviewed
  and verified feature tree. Finish a release or hotfix by hand: first have a fresh reviewer
  from the other provider, given only the scope and requirements, review the source
  branch, favoring accuracy, and resolve its findings; then recheck that the
  target and the source still point at their reviewed and verified commits,
  and stage the merge with `git merge --no-ff --no-commit`. A staged tree that
  differs from the source's verified tree, as when a release returns to a
  `develop` that has moved, MUST be verified before the commit.
  Preserve source branch/commit evidence; no branch cleanup is implied.
  Fast-forward and squash merges are not alternate defaults. Base drift,
  conflicts or a failed check stop integration: abort any uncommitted merge,
  and do not reset, rebase or silently select another strategy.
- Never bypass hooks, auto-resolve integration conflicts, or merge over an
  unexpected base.
- Push, release, deployment, account changes and external messages retain
  separate authority. Local acceptance never implies them.

## Governance

Record user-directed principle changes with their reason and impact. Each
commit that changes this constitution raises its version exactly once, by that
commit's Conventional Commits type: a breaking change (`!` or a `BREAKING
CHANGE` footer) raises the first digit and needs the user's approval, `feat`
the middle digit, and `docs` or `fix` the last digit; commits of other types
do not change this document. The repository's commit-message hook enforces
this rule, and the feature finish hook checks it again for each non-merge commit
on the feature that changes this constitution. Compliance review follows the
root AGENTS.md workflow, verification and review requirements. Product, plugin,
document, and constitution versions remain
independent. The latest user direction governs conflicts. The user's 2026-09-22
plugin layout supersedes the earlier `apps/` and root `deno.jsonc` requirement,
and the user's 2026-09-22 Raw/Wiki/Schema and XDG layout governs Wiki storage.
The user's 2026-09-26 decision permits any programming language and runtime;
PGlite is the durable relational store. On 2026-09-26 the user restarted the
project from a blank slate: earlier projects stopped being sources of
requirements, evidence, code or data; Features 001, 003 and 004 were closed;
their work plugin implementation and the tools adopted from earlier projects were
removed; and each capability is specified anew from current needs. The same
day the user tidied the repository root: workspace checks live under `scripts/`,
and static assets and examples under `docs/`; the user also removed the chat
package's skills and adopted git flow, whose no-fast-forward merges replace the
earlier Squash Merge rule. On 2026-09-27 the user selected `packages/<name>/src/`
for reusable libraries and MCP servers so plugin packages can select shared
implementations without adding a fourth plugin. The same day the user renamed
the plugin IDs to `chat`, `code` and `work`, so client install IDs such as
`code@<marketplace>` do not repeat the project name. Also that day the user
adopted git-flow-next to finish features into `develop`, adapted only through
its own settings and one local pre-finish hook, with its source unchanged. Also
on 2026-09-27 the user moved the final independent review to the merge into
`develop` or `main`, recorded for `develop` by a review-record commit that the
feature finish requires and held for `main` as a step before the hand-finished
merge, and made the amending commit's type decide the constitution's version
bump. On 2026-09-28 the user removed every rule whose criteria were vague or
that made no functional sense, including principle VIII, instead of clarifying
them. Also on 2026-09-28 the user chose to regenerate each Wiki instance's
`index.md` from page metadata instead of having the LLM maintain it. The same
day the user renamed the Wiki storage folder `wikis/` to `vaults/` and kept
four vaults: the existing instance, which held education work, became `work`;
`default` holds knowledge that belongs to no single plugin; the `chat` vault
admits exported conversations as Raw evidence and is the chat package's
persistent state; and the `code` vault holds coding knowledge for work in any
project. On 2026-09-29 the user allowed exported conversations as Raw evidence
in the `work` vault as well, so that its pages about students can cite the
ChatGPT exports they come from. Also on 2026-09-29 the user replaced Deno
with Node.js and Turborepo for the repository's tooling, including the
shipped clean-code skill, and made the three Python packages one uv
workspace (CHE-32). The user's exact AGENTS.md is maintained as
supplied, not regenerated by setup tasks.

**Version**: 2.2.0 | **Ratified**: 2026-09-12 | **Last Amended**: 2026-09-29
