<!--
Sync Impact Report
- Version: 2.7.2 -> 3.0.0 (user-approved breaking amendment, 2026-10-06).
- Input: feature 060 (`specs/060-clean-architecture/`): the user's
  2026-10-06 decisions to retire the Agent Plugins packaging and to build the
  capabilities as a collection of tools in component packages whose
  dependencies point inward.
- Modified principles: IX. Three Plugin Packages -> IX. Component Packages
  and Tool Delivery; VI and VII name skill areas and skills instead of
  plugins.
- Modified sections: Governance (version independence wording and the dated
  decision).
- Added sections: none. Removed sections: none.
- Follow-up (outside this document): feature 060 removes the plugin
  packaging and moves the skills into skill areas in later slices; root
  AGENTS.md pointers change when the skills move.
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

For the user-selected Wiki layout, each Wiki instance MUST
define five distinct roles:

1. **Raw** is immutable, create-only BagIt original evidence under `raw/`,
   outside Git, organized as `web/`, `files/`, `notes/`, and `assets/`. LLM
   maintenance MUST NOT edit or delete admitted raw bytes. Changed evidence
   creates a new source revision while earlier revisions remain resolvable and
   recoverable. Conversation records and
   exported chats are not Raw evidence; they stay outside the wiki in the
   user's workspace. Two exceptions apply: exported conversations are Raw
   evidence in the `chat` and `work` wikis, and exported Claude Code and
   Codex sessions are Raw evidence in any wiki they belong to.
2. **Text** under `text/` retains one full original-language `.qmd` extraction
   per converted raw revision in wiki-local Git with no remote. Each extraction
   MUST record its source ID, revision, SHA-256, converter and version, and
   whether it was checked against the original. Review it once against the
   original; corrections are recorded in Git without changing raw evidence.
3. **Wiki** is the single maintained English `.qmd` knowledge layer under
   `wiki/`, with topics. The LLM maintains pages, cross-references,
   `overview.qmd`, and the append-only `log.qmd`; `index.qmd` is regenerated
   from page metadata. Source summaries belong in `sources/`; entities,
   concepts, comparisons, and synthesis retain their own directories. Adopted
   knowledge MUST NOT be classified as disposable because it was LLM-authored.
   Wiki-local Git with no remote owns its history.
4. **Site** under `site/` is Korean delivery derived from chosen English Wiki
   versions, with tags. F2/CHE-12 owns translation freshness and publishing.
   There is no `ko/` tree.
5. **Schema** is the instance's `AGENTS.md`, above the content layers. It defines
   these roles, page conventions and ingest/query/lint workflows. It has its own
   wiki-local Git history with no remote and MUST NOT be confused with the
   repository's development AGENTS.md or a duplicate runtime-settings file.

Use the `verbose-broccoli` namespace under XDG configuration, data, state,
and cache roots. The defaults are `~/.config/`, `~/.local/share/`,
`~/.local/state/`, and `~/.cache/` respectively. Configuration owns `config.toml`
and profile files; durable data owns `registry.json` and `llm-wiki/`, which holds
one folder per wiki: `default` for knowledge that belongs to no single skill
area, and `chat`, `code` and `work` for the skill areas of those names.
Restart/recovery state belongs in state storage. Only
rebuildable indexes, embeddings, chunks, parsed data, citation bibliographies,
temporary downloads and temporary work belong in cache. Bags are the only source
registry. Every run MUST generate its citation bibliography from bags into
rebuildable cache, never persist it as durable data or in Git. Cache cleanup MUST
preserve raw evidence, retained text, adopted Wiki knowledge, instructions,
configuration, registry and operational state. Direct Wiki index/catalog
navigation and page reading MUST work without cache.

Raw sources and private user data MUST NOT enter the product source repository.
Raw originals MUST NOT enter the Wiki's versioned knowledge tree; retained
`text/` extractions follow the Text role above. Do not add parallel per-page
revision registries or a permanent generated-output archive.

### VII. One Decision Owner and Minimum Implementation

Repository reference tables for selected skill, server and command facts MUST
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

### IX. Component Packages and Tool Delivery

Capabilities reach agents as Agent Skills, command-line tools, and MCP
servers where a tool needs a running process, a login or a filter in front
of it. Agent Plugins packages and client-specific plugin formats are not
used, and the repository contains no installer. Each skill exists once, at
`skills/<area>/<name>/`, in the areas `code`, `work` and `chat`; each area
keeps its rules in its own `AGENTS.md`; agents find skills through the
committed `.agents/skills` links. MCP servers are registered once per agent
in the user's own settings. An upstream bundle whose code finds its skills
by relative path keeps its upstream layout under `tools/`.

Each capability with code lives in one component package,
`packages/<name>/`, with its own manifest and its source under `src/`; do
not retain empty placeholders. Inside it, dependencies point inward: a
domain without input or output, an application layer with use cases and the
ports they need, adapters, and one composition root that reads settings. Add
a port only where a use case must reach outside its package while it runs.
Repository verification enforces these rules. A skill that must work when
copied elsewhere keeps its code in its own `scripts/` folder. A package joins
a toolchain workspace only when it has executable code for that toolchain. A
shared package requires a second real consumer; no common framework is
created in advance.

Use `tools/` for development/release programs, `scripts/` for repository
automation and its checks, including workspace integration and contract
checks, `docs/` for explanations and their assets and examples, `specs/` for
feature work, and `infra/` for environment/deployment files. Examples require
actual content. Preserve repository verification results under `artifacts/`.
Content drafts and user deliverables stay outside the repository;
deliverables go in the user's documents folder. A directory rename does not
authorize deleting its contents.

The chat area's skills are `web-agent` and `credit-offers`, which run in
local Codex CLI or Claude Code sessions; its persistent state is the `chat`
wiki (principle VI). All areas run in Codex CLI and Claude Code, and no
capability depends on the desktop hub that launches them. Do not require one
repository-wide runtime, server or composition entry point. Business
capabilities belong to the work area. Package versions may move together;
there is no per-module release framework.

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
  source. Before a feature is finished, a fresh reviewer from a provider
  other than the implementer's (Claude Code, Codex, Copilot, Antigravity,
  Grok or Cursor), given only the scope and requirements,
  reviews it, favoring speed; after its findings are resolved, a content-free
  review-record commit on the feature tip names the reviewer in a
  `Reviewed-by` trailer and the reviewed commit, its parent, in a
  `Reviewed-commit` trailer. Finish a feature with git-flow-next, `git flow
  feature finish <name>`, run in the `develop` worktree: the committed
  `.gitflow` settings and the `scripts/git-flow-hooks/pre-flow-feature-finish`
  hook refuse the finish unless `develop` is an ancestor of the feature, the
  feature tip is such a review record, and the feature passes `npm run
  verify`, so the merge commit's tree is the reviewed
  and verified feature tree. Finish a release or hotfix by hand: first have a fresh reviewer
  from a provider other than the implementer's, given only the scope and
  requirements, review the source
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
do not change this document. The author writes the new version with
commitizen (`npm run constitution:bump -- PATCH`, `MINOR` or `MAJOR`), and
reviewers check that it matches the commit type. Compliance review follows the
root AGENTS.md workflow, verification and review requirements. Product, package,
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
workspace (CHE-32). On 2026-09-30 the user gave the chat package a Jev
Ultrafast web agent and a scheduled search for free API credit offers
(CHE-41), so principle IX names its two skills. Also on 2026-09-30 the user
replaced the repository's own tooling code with upstream tools used
unchanged (CHE-44): commitizen writes this document's version, and the
commit-message and feature finish hooks no longer refuse a version that does
not match the commit type. Also on 2026-09-30 the user
allowed exported Claude Code and Codex sessions as Raw evidence in any vault
they belong to (CHE-47), so that local coding-agent sessions selected with
backfire can back pages in the `code` and `default` vaults as well as in
`chat` and `work`. Also on 2026-09-30 the user added GitHub Copilot as a
reviewer and a model-choice option (CHE-60), so the final review comes from
a provider other than the implementer's: Claude Code, Codex or Copilot. On
2026-10-01 the user added Antigravity, Grok and Cursor as model-choice
options that may give the develop merge review (CHE-70); release and hotfix
reviews keep Claude Code, Codex or Copilot. The user's exact AGENTS.md is
maintained as supplied, not regenerated by setup tasks. On 2026-10-04 the user
approved the CHE-84 principle VI `feat`/MINOR amendment: raw remains immutable,
create-only BagIt originals outside Git; retained original-language `text/` and
single maintained English `wiki/` use `.qmd` and vault-local Git with no remote;
Korean `site/` derives from chosen English versions, with F2/CHE-12 owning
freshness and publishing and no `ko/` tree. The schema owns all five roles;
bags remain the only source registry and every run generates its citation
bibliography into rebuildable cache. This decision preserves the existing
conversation/session exceptions and cache-independent reading guarantees.

On 2026-10-04 the user renamed the current Wiki container to `llm-wiki`
and each instance to a wiki, to avoid implying an Obsidian dependency.
CHE-90 changes repository paths and current wording only; data and history
remain preserved, and removing the temporary link stays a separate action.

On 2026-10-06 the user retired the Agent Plugins packaging, because Claude
Code does not load Agent Plugins, and chose a collection of tools that agents
use: skills in the `code`, `work` and `chat` areas, command-line tools and
MCP servers, with each capability's code in one component package whose
dependencies point inward (feature 060). Principle IX was replaced;
principles VI and VII name skill areas and skills instead of plugins.

**Version**: 3.0.0 | **Ratified**: 2026-09-12 | **Last Amended**: 2026-10-06
