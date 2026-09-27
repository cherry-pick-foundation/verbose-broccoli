<!--
Sync Impact Report
- Version: 0.20.0 -> 0.21.0 (draft minor amendment of a workflow rule;
  Governance sets draft minor increments for rule changes before 1.0).
- Input: the user's 2026-09-27 decision to automate finishing features into
  `develop` with git-flow-next, keeping its source unchanged and adapting it
  only with its settings and a minimal local hook.
- Modified principles: none.
- Modified sections: Development Workflow and Quality Gates, "Branch with git
  flow": a feature is finished with `git flow feature finish` in the `develop`
  worktree, whose pre-finish hook requires `develop` to be an ancestor of the
  feature and the feature to pass `deno task verify`. Releases and hotfixes keep
  the staged `--no-commit` procedure. Governance records the decision.
- Added sections: none. Removed sections: none.
- Follow-up (outside this document): done in the same change. `.gitflow`, the
  hook in `scripts/git-flow-hooks/`, its tests, the doctor check, Orca's setup
  script and `docs/architecture.md`. Templates need no change.
- Deferred placeholders: none.
-->

# verbose-broccoli Constitution

This project owns its three-plugin implementation, constitution and task ledger.

## Core Principles

### I. Proven Dependencies and Storage

Project code MAY use any programming language and runtime. Native tools and
package build requirements MUST be disclosed and proved in the selected
environment before adoption. Pin and validate dependency resolution and actual
entry points, including child processes. Quarto remains a separately installed
document converter. Durable relational storage MUST use PGlite.

### II. Deliver Working Capabilities and Preserve Data

Each specified capability MUST work using the selected dependencies. Prefer
upstream protocol, validation, serialization and algorithm behavior over local
compatibility code. Error wording, equivalent JSON number spellings and
generated formatting are not acceptance criteria unless a specification makes
them so. Verify documented inputs, useful results, invalid-input handling and
recovery with independent functional tests. Document/version IDs, source
records, provenance, retry safety and access restrictions remain protected.
Actual supported clients must work with the delivered interface. Planned-only
capabilities MUST remain explicit backlog, never counted as implemented.

### III. Preserve Sources and Data Ownership

Original evidence, maintained knowledge, stable IDs and provenance MUST survive
changes under principle VI. Search normalization MUST NOT become an identity
key. Existing EduOK and academy operations retain authority over operational
records; their storage is outside the Wiki knowledge classification. The project
MUST NOT create a second student register, infer relationships, publish
restricted data, or turn review status into factual accuracy.

### IV. Capabilities From Current Needs

Specify, implement and accept each capability in this repository from the
user's current needs. Earlier projects, their code, tests, captures, ledgers
and data are not requirement, evidence, implementation or migration sources,
and target code MUST NOT depend on them. Importing existing user data is a
separately specified capability with its own ownership, verification and
recovery checks before any affected write. Unknown ownership stops the affected
step.

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

This classification applies only to Wiki content processing. Real learner
events, approval/authorization records, operational configuration, audit and
deduplication state retain their own owners and recovery requirements; they are
not disposable because a program wrote them.

For the user-selected Wiki layout, each instance under the application's data
root MUST contain three distinct layers:

1. **Raw** is immutable original evidence under `raw/`, organized as `web/`,
   `files/`, `notes/`, and `assets/`. LLM maintenance MUST NOT edit or delete
   admitted raw bytes. Changed evidence creates a new source revision while
   earlier revisions remain resolvable and recoverable. Conversation records and
   exported chats are not Raw evidence; they stay outside the Wiki instance in
   the user's workspace.
2. **Wiki** is durable maintained Markdown knowledge under `wiki/`. The LLM
   maintains pages, cross-references, `index.md`, `overview.md`, and the
   append-only `log.md` under the selected operation's scope. Source summaries
   belong in `sources/`; entities, concepts, comparisons, and synthesis retain
   their own directories. Adopted knowledge MUST NOT be classified as disposable
   because it was LLM-authored. Git owns its history, and knowledge bodies or
   judgments MUST NOT acquire a parallel database or document authority.
3. **Schema** is the instance's `AGENTS.md`, above `raw/` and `wiki/`. It defines
   page conventions and ingest/query/lint workflows. It has its own versioned
   history and MUST NOT be confused with the repository's development AGENTS.md
   or a duplicate runtime-settings file.

Use the `verbose-broccoli` namespace under XDG configuration, data, state,
and cache roots. The defaults are `~/.config/`, `~/.local/share/`,
`~/.local/state/`, and `~/.cache/` respectively. Configuration owns `config.toml`
and profile files; durable data owns `registry.json` and `wikis/default/` plus
other selected Wikis. Restart/recovery state belongs in state storage. Only
rebuildable indexes, embeddings, chunks, parsed data, temporary downloads and
temporary work belong in cache. Cache cleanup MUST preserve raw evidence,
adopted Wiki knowledge, instructions, configuration, registry and operational
state. Direct Wiki index navigation and page reading MUST work without cache.

Raw sources and private user data MUST NOT enter the product source repository.
Raw sources MUST NOT enter the Wiki's versioned knowledge tree. Do not add parallel per-page revision
registries or a permanent generated-output archive. A disposable build manifest
may detect stale caches but MUST NOT become a new authority. Source identity,
retention and recovery require evidence; directory names alone do not prove them.

### VII. One Decision Owner and Minimum Implementation

Each fact or decision field MUST have one authoritative owner and edit location.
Eligibility, selected scope, same-rule revision and evidence quality are
distinct questions, not one global priority list. A newer observation cannot
override a different owner's decision. Conflicts stop the affected decision.

Repository reference tables for selected plugin, server and command facts MUST
derive from their existing manifests, configuration and command definitions.
Do not add a parallel metadata authority. Generated reference files MUST have
deterministic output and a non-mutating drift check in repository verification.
Authored introductions and design decisions retain their own edit scope; a
reference refresh MUST NOT rewrite them. Document agreement proves agreement
with declared inputs, not runtime availability or operational acceptance.
These committed repository reference files are outside principle VI's Wiki
content classification.

Retries MUST preserve the requested purpose, mode, count, scope and success
conditions. Report incomplete work honestly; do not substitute another task and
call it success. Keep format-specific extraction inside its adapter boundary and
use one downstream result contract. A normal local Wiki build is one operator
invocation; add a separate handoff only for an actual authority or deployment
boundary.

Create derived outputs only for selected consumers. Every persistent generated
writer MUST have a positive storage budget and explicit success, failure and
interruption cleanup before accumulation begins. Temporary cleanup MUST NOT wait
for whole-system recovery approval. Detailed lifecycle rules have one owner in
the Wiki contract.

Follow the user's root AGENTS.md reuse order strictly for every existing custom
implementation as well as new work, including unmerged branches and every
language. Existing code is not grandfathered. Verify existing or upstream
implementations before writing adapters; locally owned code is limited to
necessary integration and domain-specific glue. If substantial new
implementation would be required, stop that capability and report the gap and
upstream options. Do not add speculative services, compatibility copies or
configuration matrices.

### VIII. Rule Validity Before Technical Exceptions

Rules MUST apply within their declared conditions. Put known environment and
external-contract conditions in the rule itself; do not narrow its scope after
failure to avoid compliance or silently drop a required capability. A rule may
define zero or one technical exception with exactly one predetermined fallback.
No definition means no exception. This amendment creates no new operative
exception and does not weaken AGENTS.md's prohibition on substantial custom
implementation.

An exception claim MUST be examined by a separate refutation-only agent,
independent of the proposed implementation. Its sole question is whether the
rule's stated premise fails under the selected current conditions, using three
axes: temporal validity; technical preconditions (environment/external
contract); or logical/technical feasibility under unchanged mandatory
constraints. Age, a newer release, missing research, an unrun test or failure to
find a dependency is not proof of impossibility. Use reproducible evidence at
exact versions/inputs, an authoritative contract, or an explicit contradiction
between mandatory constraints. Preserve uncertainty when no proof is available.

The refutation MUST state: rule R and its revision; declared premise P; evidence
X; the concrete failure Y from applying R; and the already defined exception E
with its single fallback. Bind the reviewer's agent/task identity and actual
review-result reference to the proposal/author; verify that the reviewer did not
author or implement the proposal. A self-labeled independent review is
insufficient. The reviewer may report no established refutation. It MUST NOT
propose a better method, invent E, mutate canonical inputs or exercise the
fallback. The primary agent verifies the evidence, pre-existing definition and
action scope before applying E; the reviewer's conclusion itself grants no
authority. Use existing review/task evidence, not a new registry, runtime rule
engine or agent service.

Performance, convenience, preference, popularity, novelty, code quantity,
maintenance preference, another agent's suggestion and speculative future need
MUST NOT justify an exception. They may inform compliant implementation choices
or a separately approved rule amendment. A technical exception MUST preserve
other mandatory invariants and the requested goal/success criteria. Apply only
the named fallback; if it fails, stop the affected work without a fallback chain
or successful-result substitution.

Absent a reviewer, adequate proof, a pre-existing exception or sufficient action
authority, stop the affected operation and report what is missing. Evidence
expires when the bound rule, inputs, environment or contract changes. Existing
same-scope authorization persists; a proved, already authorized fallback does
not need repeated permission. A rule judged undesirable requires explicit user
amendment, not exception activation. Normal declared modes, failures and
recovery paths are not new exceptions merely because they branch.

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
documents folder. Existing source and
operational data roots retain their separate owners; selected Wiki storage follows
principle VI. A directory rename does not authorize deleting its contents.
Each plugin is its own Agent Plugins 1.0 package root and independently
selectable. Skills and MCP components are added only for selected capabilities.
A package joins a toolchain workspace, such as Deno's, only when it has
executable code for that toolchain.
The chat package has no skills yet and no Deno/MCP declarations, scripts or
persistent state. It runs only in the ChatGPT project with project-only memory
and the Claude chat project; skill use does not imply a work-package transition.
Code and Work run in Codex CLI and
Claude Code, and no plugin depends on the desktop hub that launches them. Distribution
and actual invocation require their own client acceptance. Always-on communication
instructions remain client-native. Conversational assistance may accompany a
technical or business task without taking over that domain's decision/data owner.
Do not require one repository-wide runtime, server or composition entry point.
Shared workspace configuration does not establish standalone package acceptance.

Business capabilities belong to the work package. Keep one decision
owner and public boundary per business module, with direct calls inside its
runtime and explicit storage ownership. Those boundaries do not impose business
layers or database dependencies on the code or chat packages. A shared package
requires an actual consumer need; no common framework is created in advance.
Plugin versions may move together; there is no new per-module release framework.

The current project `verbose-broccoli` is the development and acceptance owner.

## Product and Data Boundaries

- Scope covers the capabilities specified in this repository and the
  three-plugin workspace. It does not implicitly implement planned-only portals,
  identity issuers or infrastructure backlogs.
- Retain Codex, VSCodium, Quarto, Zotero, CopyQ, and Flameshot as the existing
  working set. No new service, scheduler, queue, vector store, or cloud
  collection is implied.
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
- Follow the existing `deno task workflow` execution instructions and effective
  client capacity. This project imposes no separate agent headcount or default
  sequential-only restriction. Parallel workers use the workflow's disjoint
  writable scopes; main owns shared files and integration.
- Use upstream [git-commit](https://github.com/github/awesome-copilot/blob/main/skills/git-commit/SKILL.md)
  for explicitly requested local Conventional Commits. Group changes by logical
  purpose and use a feature branch when isolation is needed. Related task IDs
  MAY share a branch or commit; each ID MUST retain one repository owner and
  separate verified acceptance evidence. Include a `Spec-Kit-Task: Txxx`
  trailer for each covered implementation ID. Preserve unrelated work and
  foreign index entries.
- Branch with git flow. `main` holds released states and `develop` integrates
  work; `feature/<name>` and `release/<version>` branches start from `develop`,
  and `hotfix/<version>` branches from `main`. Finish each with a
  no-fast-forward merge (`git merge --no-ff`) and Git's default merge message,
  which keeps the branch's commits together: a feature into `develop`; a
  release or hotfix into `main`, tagged `v<version>` there, then into
  `develop`. The merge commit's parents MUST be exactly the target, then the
  source. Finish a feature with git-flow-next, `git flow feature finish
  <name>`, run in the `develop` worktree: the committed `.gitflow` settings and
  the `scripts/git-flow-hooks/pre-flow-feature-finish` hook refuse the finish
  unless `develop` is an ancestor of the feature and the feature passes
  `deno task verify`, so the merge commit's tree is the verified feature tree.
  Finish a release or hotfix by hand: first recheck that the target and the
  source still point at their verified commits, then stage the merge with
  `git merge --no-ff --no-commit`. A staged tree that differs from the source's
  verified tree, as when a release returns to a `develop` that has moved, MUST
  be verified before the commit.
  Preserve source branch/commit evidence; no branch cleanup is implied.
  Fast-forward and squash merges are not alternate defaults. Base drift,
  conflicts or a failed check stop integration: abort any uncommitted merge,
  and do not reset, rebase or silently select another strategy.
- Never bypass hooks, auto-resolve integration conflicts, or merge over an
  unexpected base. An unborn repository may establish `main` with its first
  non-empty task commit as a reported BOOTSTRAP exception and then create
  `develop` from it; do not manufacture a merge parent with an empty commit.
- Push, release, deployment, account changes, external messages, and host
  effects outside selected current-project integration retain separate authority. Local
  acceptance never implies them.

## Governance

Record user-directed principle changes with their reason and impact. Increment
draft minor versions for principle changes and patch versions for wording
corrections. Compliance review follows the root AGENTS.md workflow,
verification and review requirements. Product, plugin, document, and constitution versions remain
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
its own settings and one local pre-finish hook, with its source unchanged. The
user's exact AGENTS.md is maintained as supplied, not regenerated by setup
tasks.

**Version**: 0.21.0 | **Ratified**: 2026-09-12 | **Last Amended**: 2026-09-27
