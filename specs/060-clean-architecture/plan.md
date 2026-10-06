# Implementation Plan: Clean Architecture Tool Collection

**Branch**: `feature/clean-architecture` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/060-clean-architecture/spec.md`

## Summary

Retire the three Agent Plugins roots and deliver the same capabilities as a
collection of tools: Agent Skills folders under `skills/<area>/<name>/`,
command-line tools, and the two MCP servers the user already registers once
per agent (U-2026-10-06a, U-2026-10-06g, U-2026-10-06h). Move each
capability's code into one component package whose rings point inward
(domain, application, adapters and entry points, one bootstrap module), with
the dependency rules checked by the import-linter and dependency-cruiser
versions the repository already pins (U-2026-10-06c, R-CA-01, R-CA-04,
R-ARCH-04). Work proceeds in small reviewed slices: the rules first, with a
breaking constitution amendment the user approves; then delivery without
plugins; then the checks; then one component at a time. Code that open
branches, replacement trials or the privacy-gate bug hold stays put until its
hold is released (U-2026-10-06f).

## Technical Context

**Language/Version**: TypeScript on Node.js 24.12 or later (npm workspaces);
Python 3.12 or later in one uv workspace (`packages/*`). Turborepo 2.11.5 runs
the checks, with `experimentalPythonWorkspaces` (R-REPO-05).

**Primary Dependencies**: existing only, except `skills-ref` 0.1.1 (the Agent
Skills reference validator, R-UP-01), which replaces `check-jsonschema` after
its security review. Kept: dependency-cruiser 18.2.0, import-linter 2.15, gts,
Ruff, `platformdirs` 4.12.3 (already locked), FastMCP and the MCP SDK in the
privacy gate. Pydantic AI is not added (U-2026-10-06j, FR-024).

**Storage**: files only. Settings, state and cache in the XDG folders under
`verbose-broccoli/` ([settings contract](contracts/settings.md)); no database
change.

**Testing**: Node's test runner for TypeScript, pytest for Python, each
package's tests under its own `tests/`. Behavior tests move with unchanged
assertions (FR-013, R-GG-13); each dependency rule gets a fixture that must
fail (SC-004).

**Target Platform**: the user's Linux laptop; Claude Code and Codex in this
repository's worktrees (spec Assumptions).

**Project Type**: monorepo of agent tools: skills, command-line tools and MCP
servers.

**Performance Goals**: none beyond today's; `npm run verify` must not become
slower than its current run by more than the added checks.

**Constraints**: no paid model call inside verification (FR-023); no
installer in the repository (FR-003); no change to user-scope agent settings
without the user's approval (spec Assumptions); held code does not move
(FR-016); every pick of worker model through Jev (FR-022).

**Scale/Scope**: baseline 11,351 source and 21,030 test lines of locally owned
code (measured 2026-10-06, see [Locally owned code](#locally-owned-code)); 48
skill folders in three plugin roots (47 names: `jev` is copied in two); 5
Python packages; the `workflow` command's 1,471 lines in `scripts/workflow*.ts`
outside its tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Today | After this plan |
| --- | --- | --- |
| IX "Three Plugin Packages": exactly three Agent Plugins roots with plugin IDs | **Conflicts** with U-2026-10-06a | Rewritten by slice S1 as "Component Packages and Tool Delivery" ([text](#rule-changes-for-the-users-approval)); breaking, needs the user's approval (Governance) |
| VI wiki folders "for the plugins of those names" | Wording conflict | S1 says "for the skill areas of those names"; storage unchanged |
| VII reference tables for "plugin, server and command facts" | Wording conflict | S1 says "skill, server and command facts"; the plugin reference table is removed in S2a |
| Root `AGENTS.md` "Judge plugin packaging against … Agent Plugins" and plugin rule pointers | Conflicts | S1 replaces the packaging rule; S2b changes the pointers when the files move ([text](#rule-changes-for-the-users-approval)) |
| I Proven dependencies, pinned | Pass | `skills-ref` pinned in a `tools/` uv project after review |
| II, III, IV, V | Pass | Moves keep behavior; acceptance uses synthetic fixtures (V) |
| VI Wiki storage | Pass | No wiki data moves; `infra/` and wiki data are out of scope |
| VII Minimum implementation, reuse order | Pass | Net about −2,300 owned lines; no new framework; ports only where needed (FR-008) |
| Development workflow, git flow, review | Pass | One finish per slice from `develop`, other-provider review per slice |

Gate result: the plan may proceed to tasks. Slice S1 must land, with the
user's approval of its text, before any slice that depends on the new rules
(S2a onward).

## Decisions

Each decision cites a research row or a dated user decision.

1. **Skills at `skills/<area>/<name>/`** with areas `code`, `work` and `chat`;
   each area keeps its rules in `skills/<area>/AGENTS.md`; agents find skills
   through the committed `.agents/skills/<name>` links, and Claude Code
   through the existing `.claude/skills -> ../.agents/skills` link
   (U-2026-10-06h, R-UP-02, R-REPO-12). A skill's pointer to its area rules
   becomes `../AGENTS.md`. See the [delivery contract](contracts/delivery.md).
2. **No installer and no plugin packaging.** Delete the manifests, the schema
   check, the generator and its tests, the distribution route and the plugin
   reference table; the two MCP servers stay registered once per agent in the
   user's settings (U-2026-10-06g, R-REPO-13). Before the delivery slice
   merges, each prepared worktree runs the generator's existing cleanup
   (`npm run plugins:clean-codex`) and deletes its ignored `.mcp.json`; the
   develop orchestrator coordinates the other worktrees (FR-005).
3. **Skill validation by the upstream validator.** `skills-ref validate`
   (R-UP-01) checks every `SKILL.md`, after its read-only security review
   (FR-018); a test of about 60 lines checks only what it cannot: each link
   in `.agents/skills` resolves to exactly one skill folder and no name
   repeats (FR-002). This replaces the 2,017-line plugin discovery test.
4. **Component package rings.** Inside `packages/<name>/src/<import_name>/`
   (Python) or `packages/<name>/src/` (TypeScript): `domain/`,
   `application/`, `adapters/`, `entrypoints/` and one `bootstrap` module.
   Domain has no input or output; application holds use cases and the ports
   they own; adapters implement ports; entry points (command line, MCP
   server) parse input, call `bootstrap` and print. `bootstrap` is the only
   module that reads settings; Cosmic Python offers this as an option, and
   this repository makes it a rule so the checkers can hold it (R-CA-04,
   R-CP-17, R-CP-19; R-CA-01; R-ARCH-04). Ports sit in `application/`, not
   beside their adapters as in Cosmic Python, so the rings stay checkable
   (R-ARCH-04, R-CP-07). Rings without code are not created (FR-006,
   R-ARCH-05; [data model](data-model.md)).
5. **Ports only where needed.** A port exists only where a use case must reach
   outside its package while it runs; data that can be gathered first is
   passed in as plain values; an application service gets no interface of its
   own (FR-008, R-ARCH-03 "the exception not the rule", R-ARCH-04,
   R-ARCH-02). Cosmic Python itself says a simple create-read-update-delete
   wrapper needs no domain model or repository (R-CP-05, R-CP-10), and
   Bogard warns against uniform layers everywhere (R-ARCH-05).
6. **Tests per package.** `tests/unit/` for domain and use cases with fakes at
   paid or slow seams, `tests/integration/` for adapters against real local
   resources, `tests/e2e/` for entry points as child processes; a fake stands
   in only for the package's own port and shares one test with its real
   adapter (R-CA-04 "Tests", R-GG-12, R-GG-14, R-ARCH-03, R-CP-06, R-CP-09,
   R-EX-12). Tests build the package through `bootstrap` with fakes passed in
   (R-CP-17, R-EX-11). Moves keep assertions unchanged; splitting a test file
   by scope is allowed only when no assertion changes, and Cosmic Python's
   advice to delete covered domain tests is not followed during a move
   (FR-013, R-CP-08).
7. **Dependency rules in the existing checkers.** Rules D1 to D6 of the
   [dependency rules](contracts/dependency-rules.md) extend
   `.config/dependency-cruiser.json` and the root `pyproject.toml`
   import-linter contracts, each with a breaking fixture (FR-007, SC-004,
   R-CA-03, R-EX-11). Python input-and-output and private-module rules use
   import-linter's `protected` allow-lists, because its block-lists accept
   only top-level packages (R-ARCH-08, R-ARCH-11). The rule names follow the
   new ring names; old names that no code uses are dropped. None of the
   twelve example projects forbids input or output libraries in domain code,
   so D2 and D3 go further than all of them (R-EX-01 to R-EX-12).
8. **Settings through XDG.** Python composition roots use `platformdirs`;
   TypeScript ones use the three-step rule inline until a second consumer
   exists ([settings contract](contracts/settings.md); R-OS-01, R-OS-03,
   FR-009, FR-010).
9. **Portable skills keep their code.** A skill meant to run when copied
   elsewhere, today only `clean-code` (its copied-skill test in
   `docs/architecture.md` "CLI contract"), keeps its code in its own
   `scripts/` folder, because `skills` installs copy only the skill folder
   (R-UP-01, R-UP-02). That folder is its component package; it joins the npm
   workspace so `workflow` imports its CLI serializer by package name (D6).
10. **Ponytail stays one unchanged upstream bundle** in `tools/ponytail/`
    (constitution IX: `tools/` holds development programs). Its hooks read
    `../skills/ponytail/SKILL.md`, so its four skills stay inside the bundle,
    found through `.agents/skills` links like every other skill, and
    `.agents/ponytail` is retargeted so `.codex/hooks.json` and its trust
    hashes stay unchanged (U-2026-10-04a; root `AGENTS.md` reuse order: an
    unchanged upstream copy before a patch). This is the one exception to
    Decision 1; see [Open points](#open-points).
11. **Judgments through two gated servers** (held, H1): the current gated
    `jev-mcp` and a second gated server answered by GLM 5.3 Flash on Hive;
    code defaults to Jev and switches by a setting; GLM's timeout is a setting
    of at least 300 seconds ([judgment contract](contracts/judgment.md);
    U-2026-10-06i, R-CA-06, FR-019 to FR-022).
12. **Patterns not adopted.** No message bus, unit of work, aggregates,
    domain events, command and query split, dependency-injection container or
    shared kernel package: Cosmic Python names their costs and says small
    projects can skip them, and the examples that use them add a second
    framework without a second consumer (R-CP-09, R-CP-10, R-CP-12, R-CP-14,
    R-CP-16, R-EX-01, R-EX-06, R-EX-12; FR-008).
13. **Move order inside a component slice.** Copy the code into the rings,
    clean it, switch callers and tests to the new entry, then delete the old
    files, with the behavior tests unchanged throughout (R-CP-18, R-GG-01,
    FR-013).
14. **Thin MCP entry points.** A tool function closes over a use case built by
    `bootstrap`, returns a transport model defined in `entrypoints/`, and
    reports refusals as tool execution errors; tests call the server object
    in memory with FastMCP's client (R-FMCP-02, R-FMCP-07, R-FMCP-08,
    R-ARCH-14). No example project builds an MCP server or agent tool this
    way; none was found (research "Example projects").
15. **Repository automation stays in `scripts/`.** Hook scripts whose paths
    are trusted by hash (`coordinator-context.ts`), configuration tests and
    shell helpers are repository automation (constitution IX) and do not
    become component packages; moving a hook would need the user to trust it
    again.

## Project Structure

### Documentation (this feature)

```text
specs/060-clean-architecture/
├── plan.md              # This file
├── research.md          # Reference rows and dated user decisions
├── data-model.md        # The repository's structural entities
├── quickstart.md        # Validation scenarios
├── contracts/
│   ├── delivery.md          # How skills and MCP servers reach agents
│   ├── dependency-rules.md  # Rules D1–D6 and their checks
│   ├── judgment.md          # Judgment port, two servers, settings
│   └── settings.md          # XDG settings read by a composition root
└── tasks.md             # Phase 2 output ($speckit-tasks)
```

### Source Code (repository root)

Target after the unheld slices; held paths stay where they are until
released ([Holds](#holds)).

```text
skills/
├── code/
│   ├── AGENTS.md                  # from plugins/code/AGENTS.md
│   ├── clean-code/                # portable skill with its own package.json and scripts/
│   ├── git-commit/  jev/  model-choice/  verification-before-completion/
│   └── speckit-*/                 # 20 Spec Kit skills
└── chat/
    ├── AGENTS.md                  # from plugins/chat/AGENTS.md
    ├── credit-offers/
    └── web-agent/
plugins/work/                      # held (H2): skills, AGENTS.md, package.json for the reference connector
tools/ponytail/                    # upstream bundle: hooks/, tests/, skills/ponytail{,-audit,-debt,-review}/
packages/
├── credit-offers/src/credit_offers/{domain,application,adapters,entrypoints}/ + bootstrap.py
├── doc-regions/src/doc_regions/{domain,application,adapters,entrypoints}/ + bootstrap.py
├── workflow/                      # from scripts/workflow*.ts: src/{domain,application,adapters,entrypoints}/, bootstrap.ts
├── education-privacy-gate/        # held (H1)
├── jev-ultrafast/                 # held (H3)
└── wiki-consistency/              # held (H2)
scripts/                           # repository automation and its checks
.agents/skills/<name> -> ../../skills/<area>/<name>   (or ../../tools/ponytail/skills/<name>, or held plugins/work)
.claude/skills -> ../.agents/skills
```

**Structure Decision**: component packages under `packages/`, skills under
`skills/<area>/`, development bundles under `tools/`, repository automation
under `scripts/` (Decisions 1, 4, 9, 10, 15).

## Component mapping

| Today | Target | Slice | Hold |
| --- | --- | --- | --- |
| `plugins/code/skills/*` (29 skills) | `skills/code/<name>/`; Ponytail's four to `tools/ponytail/skills/` | S2b | none |
| `plugins/code/hooks`, `plugins/code/tests` | `tools/ponytail/hooks`, `tools/ponytail/tests` | S2b | none |
| `plugins/code/{plugin.json,mcp.json,package.json}` | deleted | S2a | none |
| `plugins/chat/skills/*`, `plugins/chat/AGENTS.md` | `skills/chat/` | S2b | none |
| `plugins/chat/plugin.json`, `plugins/work/{plugin.json,mcp.json}` | deleted | S2a | excepted from H2 (see Holds) |
| `plugins/work/skills/jev` (byte-identical copy) | deleted; `skills/code/jev` is the one copy | S2b | excepted from H2 (see Holds) |
| `scripts/plugin-clients.ts`, `plugin-skills-test.ts`, `plugins-validate-test.ts`, `scripts/vendor/agent-plugins/`, `tools/check-jsonschema/`, `docs/reference/plugins.md`, `doc_sources.plugin_table` | deleted | S2a | none |
| `plugins/work/{package.json,package-lock.json}` (the pinned reference-library connector that `scripts/reference-library-test.ts` checks) | decided when H2 is released; the user-scope registration runs a separate install in `~/.local/share/mcp-servers/zotero/1.0.1/` (checked 2026-10-06), so a move does not break it | later | H2 |
| `packages/credit-offers` (one module) | rings + `bootstrap.py` | S4 | none |
| `packages/doc-regions` | rings; published modules kept stable for `wiki-consistency` | S5 | none |
| `scripts/workflow*.ts`, `scripts/hash.ts` | `packages/workflow/` | S6 | none |
| `plugins/work/**`, `packages/wiki-consistency` | `skills/work/`, rings | later | H2 |
| `packages/jev-ultrafast` | rings or replaced by Jev Browser | later | H3 |
| `packages/education-privacy-gate`, second judgment server | rings, GLM server | later | H1 |
| `scripts/secrets-refresh.ts` | replaced by chezmoi or kept | later | H4 |

## Holds

| ID | Paths | Reason | Released by | Reported by |
| --- | --- | --- | --- | --- |
| H1 | `packages/education-privacy-gate`, the GLM judgment server | The gate's Claude Code metadata bug; `system-one-adapter` needs its read-only security review (U-2026-10-06d) | the fix merged into `develop` and a passed security review | develop orchestrator |
| H2 | `plugins/work/**`, `packages/wiki-consistency` | Open branches `document-pdf-fidelity`, `exam-calendar`, `korean-web-wiki`, `lexical-semantics` change them (checked 2026-10-06 with `git diff` against each merge base); the session-scan trial covers `session_select.py` | all four merged into `develop`, and the user's verdict on the session-scan trial | develop orchestrator; the user for the trial |
| H2 exception | `plugins/work/plugin.json`, `plugins/work/mcp.json`, `plugins/work/skills/jev`, the plugin wording of `plugins/work/AGENTS.md` | Not held: no open branch changes them (checked 2026-10-06 with `git diff` against each merge base); the check is repeated when S2a and S2b start | not applicable | not applicable |
| H3 | `packages/jev-ultrafast` | `lexical-semantics` changes it; the Jev Browser trial may replace it | the merge and the user's trial verdict | develop orchestrator; the user |
| H4 | `scripts/secrets-refresh.ts` | The chezmoi trial may replace it | the user's trial verdict | the user |

Shared files the open branches also change (`docs/architecture.md`,
`turbo.json`, `package.json`, `docs/reference/commands.md`, `uv.lock`,
`.agents/skills`) are not held: this branch merges `develop` after each of
those merges and resolves conflicts by hand (spec Edge Cases).

## Slices

Each slice is one reviewed change finished into `develop` on its own
(FR-014). Implementers and reviewers are chosen per task with Jev through the
model-choice skill, with the user's free-quota priority of 2026-10-06 as
evidence; Cursor and Copilot are offered only on their Auto setting. On
2026-10-06 Antigravity's quota (until about 15:45 KST on 8 October) and
Cursor's free plan (until 16 October) refused all work, so the reading ran on
Claude Code. Each pick is recorded under its task in `tasks.md`. The reviewer
is never the implementer's provider.

| Slice | Scope | Size estimate (owned lines) | Candidate implementer |
| --- | --- | --- | --- |
| S1 Rules | Planning records; constitution 3.0.0; root `AGENTS.md` opening and packaging rule; the opening of `docs/architecture.md` | documents only | this orchestrator (constitution work stays on Claude or Codex) |
| S2a Packaging removed | Clean each prepared checkout's generated configuration first; delete manifests, generator, its tests, the schema check and the plugin reference; adopt `skills-ref` with its review; the skills link test; keep the reference-library guard test without `mcp.json`; update tasks, mise setup and doctor, Cog regions and docs. Skills stay in place. | about −2,600 | chosen with Jev at dispatch |
| S2b Skills moved | Move code and chat skills and Ponytail; area `AGENTS.md` files; retarget links; delete the duplicate `jev`; update paths in configuration, tests and documents | about −50 (moves count as renames) | chosen with Jev at dispatch |
| S2c Spec Kit 1.1.0 | Upgrade Spec Kit from 1.0.1 project files and the 1.0.12 command line to 1.1.0 with its own commands; move the area-rules pointer into a preset with prepend overrides if Spec Kit supports it; security review of the upstream change (U-2026-10-06l) | measured then; small | chosen with Jev at dispatch |
| S3 Checks | Rules D1–D6 in both checkers with breaking fixtures and a test that each fails; fixtures also settle whether `acyclic_siblings` sees cycles between root packages and how by-name workspace imports resolve | about +180 | chosen with Jev at dispatch |
| S4 credit-offers | Rings and bootstrap; settings through `platformdirs`; tests split by scope with unchanged assertions | about +40 | chosen with Jev at dispatch |
| S5 doc-regions | Rings and bootstrap; published modules unchanged | about +30 | chosen with Jev at dispatch |
| S6 workflow | `packages/workflow` from `scripts/workflow*.ts`; imports the clean-code CLI serializer by package name | about +60 | chosen with Jev at dispatch |
| H1–H4 | After each release, one slice per hold, planned then | measured then | chosen then |

S2c follows S2b because the user asked for the Spec Kit update right after
the skill move (U-2026-10-06l); it writes through the new links, which the
skills link test checks. S2 is split because one change of both deletions
and moves would pass 1,000
changed lines and mix two kinds of change (R-GG-01; root `AGENTS.md` split
review). S3 lands before S4–S6 so every move is checked. S2's checks
are the quickstart's first two scenarios; a fresh Claude Code and Codex
session before S2a and after S2b records the skill and server lists
(SC-001).

### Slice mechanics

All slices use this branch. Each slice ends with a content-free review-record
commit and a `git flow feature finish` from the `develop` worktree; the
committed `.gitflow` sets `keep = true` under `feature.finish`, so the branch
survives each finish. No code goes past a slice's review record until
`develop` has finished it; the next slice then starts by merging `develop`
back. If the develop coordinator is down, the next slice continues in a child
worktree of this one, branched from the last review record, and merges
`develop` back once it has finished the waiting slice; nothing is rebased
(U-2026-10-06f; constitution "Development Workflow").

## Locally owned code

Measured with the session's `code-size/measure.py` (non-blank lines; upstream
copies, specs, documents and `.specify` excluded): 11,351 source and 21,030
test lines on 2026-10-06. Estimate for the unheld slices: about −2,650 lines
from S2a and S2b (the generator 589, its tests 2,062, the plugin table and
task entries), about +310 for S3–S6, so about −2,300 net. The held slices are
estimated when their holds are released. Each slice reports its measured
change (FR-017); a line count does not stop work.

## Rule changes for the user's approval

S1 carries these changes. The constitution change is breaking (principle IX
is replaced), so its version becomes 3.0.0 and it needs the user's approval
before S1 merges (Governance; FR-015).

### Constitution principle IX (replaces "Three Plugin Packages")

> ### IX. Component Packages and Tool Delivery
>
> Capabilities reach agents as Agent Skills, command-line tools, and MCP
> servers where a tool needs a running process, a login or a filter in front
> of it. Agent Plugins packages and client-specific plugin formats are not
> used, and the repository contains no installer. Each skill exists once, at
> `skills/<area>/<name>/`, in the areas `code`, `work` and `chat`; each area
> keeps its rules in its own `AGENTS.md`; agents find skills through the
> committed `.agents/skills` links. MCP servers are registered once per agent
> in the user's own settings. An upstream bundle whose code finds its skills
> by relative path keeps its upstream layout under `tools/`.
>
> Each capability with code lives in one component package,
> `packages/<name>/`, with its own manifest and its source under `src/`; do
> not retain empty placeholders.
> Inside it, dependencies point inward: a domain without input or output, an
> application layer with use cases and the ports they need, adapters, and one
> composition root that reads settings. Add a port only where a use case must
> reach outside its package while it runs. Repository verification enforces
> these rules. A skill that must work when copied elsewhere keeps its code in
> its own `scripts/` folder. A package joins a toolchain workspace only when
> it has executable code for that toolchain. A shared package requires a
> second real consumer; no common framework is created in advance.
>
> Use `tools/` for development/release programs, `scripts/` for repository
> automation and its checks, including workspace integration and contract
> checks, `docs/` for explanations and their assets and examples, `specs/`
> for feature work, and `infra/` for environment/deployment files. Examples
> require actual content. Preserve repository verification results under
> `artifacts/`. Content drafts and user deliverables stay outside the
> repository; deliverables go in the user's documents folder. A directory
> rename does not authorize deleting its contents.
>
> The chat area's skills are `web-agent` and `credit-offers`, which run in
> local Codex CLI or Claude Code sessions; its persistent state is the `chat`
> wiki (principle VI). All areas run in Codex CLI and Claude Code, and no
> capability depends on the desktop hub that launches them. Do not require
> one repository-wide runtime, server or composition entry point. Business
> capabilities belong to the work area. Package versions may move together;
> there is no per-module release framework.

### Constitution wording changes

- VI: "`default` for knowledge that belongs to no single plugin, and `chat`,
  `code` and `work` for the plugins of those names" becomes "`default` for
  knowledge that belongs to no single skill area, and `chat`, `code` and
  `work` for the skill areas of those names".
- VII: "Repository reference tables for selected plugin, server and command
  facts" becomes "Repository reference tables for selected skill, server and
  command facts".
- Governance: "Product, plugin, document, and constitution versions remain
  independent" becomes "Product, package, document, and constitution versions
  remain independent", and a dated paragraph is added: "On 2026-10-06 the
  user retired the Agent Plugins packaging, because Claude Code does not load
  Agent Plugins, and chose a collection of tools that agents use: skills in
  the `code`, `work` and `chat` areas, command-line tools and MCP servers,
  with each capability's code in one component package whose dependencies
  point inward (feature 060). Principle IX was replaced; principles VI and
  VII name skill areas and skills instead of plugins." Earlier dated
  paragraphs keep their wording as history.

### Root `AGENTS.md`

- Opening: "A personal workspace of three agent plugins for education and
  knowledge work." becomes "A personal workspace of agent tools for
  education and knowledge work: skills, command-line tools and MCP servers in
  three areas, `code`, `work` and `chat`."
- "Before working on a plugin, read its rules … [code](plugins/code/AGENTS.md),
  [work](plugins/work/AGENTS.md), or [chat](plugins/chat/AGENTS.md)." becomes,
  in S2b when the files move, "Before working in a skill area, or using its
  skills from another directory, read its rules: [code](skills/code/AGENTS.md),
  [work](plugins/work/AGENTS.md) or [chat](skills/chat/AGENTS.md)." The work
  link changes when H2 is released.
- "Judge plugin packaging against the vendor-neutral Agent Plugins
  specification and example first. Add client-specific distribution packaging
  only when the user requests it. Client-specific popularity is not evidence
  of fit." becomes "Deliver capabilities as Agent Skills, command-line tools
  and MCP servers (constitution IX). Do not add plugin packaging or an
  installer; document `skills` and `add-mcp` for installing elsewhere."
- "Lessons that hold across features belong in this file or in
  `plugins/<name>/AGENTS.md`." becomes "… or in `skills/<area>/AGENTS.md`."
  (S2b).
- "the code plugin's `model-choice` skill", "the code plugin's jev-mcp
  judgments" and "The code plugin's `code` wiki" become "the code area's …"
  (S2b).

### `.claude/rules/claude-code.md`

"Read the owning plugin's `../../AGENTS.md` from that canonical base" becomes
"Read the owning area's `../AGENTS.md` from that canonical base" (S2b, when
the skills move).

## Open points

- Decision 10 (Ponytail under `tools/`) departs from the user's
  `skills/<area>/<name>/` answer for four upstream skills; the alternative is
  a one-line patch to Ponytail's instruction loader so its skills can move to
  `skills/code/`. The plan recommends the unchanged upstream layout and asks
  the user through the coordinator with the rule text.
- Decision 9 keeps `clean-code`'s code inside its skill; the alternative, a
  `packages/clean-code` with the skill calling it, would stop the copied skill
  from working elsewhere.

## Complexity Tracking

No constitution violation remains after S1. The plan adds no new framework,
no shared package and no configuration matrix.
