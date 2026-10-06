# Research: Clean Architecture Migration

**Date**: 2026-10-06 | **Baseline**: `d9392f14b332a484db13f2f21af68007955abe9f`

## Evidence and Prior Decisions

The user's 2026-10-06 component-package and backend choices govern. The local
repo-convention captures and Google-guide captures support package isolation,
source layout, testing through public behavior and small reviewable changes.
They do not themselves specify this project's business rules.

Read-only research evidence is retained under the feature's XDG state task
`research/ctx_bf6309123828/`. The source/test measurements, exact consumer
searches and import-linter probes are reproducible from its evidence files.
The prior structure and replacement-survey results remain evidence; no duplicate
architecture vote or replacement survey was run.

## Decisions

### Component Packages and Dependencies

**Decision**: One package per capability, internal domain/application/adapters,
and a composition module. Use Python-safe `inbound` and `outbound` names.

**Rationale**: The user rejected packages per ring. Package boundaries follow
actual consumers, while dependency direction protects rules from delivery.
Reuse the existing [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/)
and [source layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
rather than new loaders. TypeScript package entries use the existing npm
workspace and [Node exports](https://nodejs.org/api/packages.html#package-entry-points).

**Alternatives considered**: Ring-wide packages and a shared framework are rejected
by the user/constitution. Empty layer directories provide no working capability.
Nested workspace manifests conflict with the captured
[Turborepo repository guidance](https://turborepo.com/docs/crafting-your-repository/structuring-a-repository).

### Mechanical Dependency Checks

**Decision**: Add a layers contract for each migrated Python package, with
composition above adapters above application above domain. Preserve package-level
and cycle contracts. Reuse import-linter's external-package forbidden contracts
for concrete I/O dependencies in inner rules. Extend TypeScript's existing
domain/application rules to `adapters` and `composition`.

**Rationale**: Current `pyproject.toml:46-70` has only package/cycle contracts.
Current `.config/dependency-cruiser.json:11-24` omits the new layer names.
The read-only scratch probe shows the installed import-linter can reject a
domain-to-adapter import and a domain-to-pathlib/subprocess import without a
new checker. Isolated tests still matter: static import checks cannot prove
absence of all dynamic effects.

**Alternatives considered**: A custom import scanner would duplicate tools already
installed. A blanket ban on pure standard-library use would block legitimate
datetime/AST/sequence policy.

### Public Document-Region Interfaces

**Decision**: Preserve the existing `doc_regions.config`, `regions`,
`requests` and `units` public import paths using explicit re-exports from
their new owners. Do not edit held wiki consumers or copy implementation bodies.

**Rationale**: Current wiki source imports `files`; `check`, `scan`,
`shape`, `update`, `_split_lf_lines`; `MAX_CLAIM_CHARS`,
`classify_requests`, `verify_requests`; and `split`.
There are ten names across four modules. The private helper is an existing
consumer edge, not permission to remove it during this slice.
See `packages/wiki-consistency/src/wiki_consistency/evidence.py:34`,
`lint.py:12`, `requests.py:12` and `citations.py:14`.

**Alternatives considered**: Updating consumers now crosses a held ownership
boundary. Public forwarding modules preserve a real interface and contain no
compatibility implementation copy, so no speculative-copy exception is needed.

### Clean Code and Shared Command Output

**Decision**: Move checker implementation to a capability package. Prove
self-contained delivery using standard npm packaging before deleting the old
skill source. Extract the current 49-line command helper once for the two real
consumers, Clean Code and workflow.

**Rationale**: `scripts/cli-contract-test.ts:241` exercises a copied skill with
its own dependencies; `scripts/workflow.ts:1` imports the same helper that
`clean-code.ts:1` uses. The user's package decision rules out leaving maintained
business implementation in the plugin for convenience. The portable plugin can
deliver generated runtime resources while the package remains their sole source.

**Alternatives considered**: Keeping the checker in the skill contradicts the
explicit layout. Duplicating the serializer adds a second maintained owner.
A new custom bundler has no demonstrated need. If ordinary npm packaging fails
the actual copied-skill check, report that limitation before changing behavior.

### Stable Automation Entries

**Decision**: Preserve native script paths as thin integration glue. Move
substantial workflow/context policy to capability packages; move `hash.ts`
with its two existing workflow consumers. Keep repository Cog generator entries
at their declared path unless a later scoped change updates all consumers.

**Rationale**: Client hooks, Git flow, lefthook and Orca call fixed entry paths:
`.claude/settings.json:22`, `.codex/hooks.json:20`, `.gitflow:24`,
`orca.yaml:7` and `.config/lefthook.yml:11`.
Workflow also has depth-relative configuration lookups in
`scripts/workflow-depcruise.ts:9`, `workflow-files.ts:8` and
`workflow-skills.ts:57`; their adapters must receive the actual project root.

**Alternatives considered**: A package for every tiny shell/configuration file
adds manifests without isolating meaningful policy. Leaving the 599-line
workflow implementation in a thin-entry directory does not meet the requested move.

### Jev and GLM Through the Gate

**Decision**: Reuse unmodified upstream jev-mcp's selected transports. Jev uses
OpenRouter `typesafe/jev-1.13`; GLM uses Hive `zai-org/glm-5.3-flash`
through reviewed TypeSafe system-one-adapter and `JEV_PROVIDER=compatible`.
Configure existing upstream environment fields at the composition boundary.

**Rationale**: The earlier structure attempt completed equivalent calls on both
routes. Its GLM decide took 86.9 seconds and verify about 96 seconds; these are
run measurements, not a performance promise. Use a proposed 300,000 ms request
timeout for GLM and a longer caller deadline. The gate remains the only exposed
judgment-server route. No client protocol/retry/status implementation is added.

**Alternatives considered**: Hive has no Jev model in the user-selected route.
GLM cannot replace Jev for model selection. Direct upstream calls, silent
fallback and a new ungated endpoint for student data are excluded.

**Adoption gate**: Before installing system-one-adapter, select and review an
exact upstream revision and its resolved runtime dependency closure, then pin the
accepted implementation. This is implementation due diligence, not an unresolved
product choice or permission to assume a version/security result.

### Private Settings Versus Project Inputs

**Decision**: Composition reads operator settings from approved XDG configuration.
Repository-owned `scripts/doc-regions.toml` remains an explicit project input
at its existing command argument; it is not relocated into a user's settings.

**Rationale**: Preserve the document generator contract and reproducibility.
Private backend/credential/timeout and cache-root settings remain outside Git.
No external client setting or credential is rewritten during structure changes.

## Measurements and Estimate Method

Physical line counts at the baseline are in [plan.md](plan.md). They include
comments and blanks. The researcher collected 130 doc-regions and 66 credit-offers
test cases and ran current import checks; collection is not a passing test run.

Early glue estimates count actual external seams, public exports, composition,
native packaging and contract tests. The total is adjusted to move the shared
serializer rather than copying it and to follow the mandated package layout.
Held capability estimates are provisional and must be refreshed when their
owners release current source. No supporting tool or framework is priced as a
required implementation merely because it appeared in a survey.

## Research Worker and Limits

Jev selected Claude `claude-sonnet-5-5` at high effort for read-only research
(probability 0.81, confidence 0.78). Its actual assistant model was observed;
the effort evidence is the native requested/effective launch receipt.
The registered MCP selection call was refused; the supervising coordinator
authorized the skill's documented plain-client route to the same gate, which
returned OpenRouter and `typesafe/jev-1.13`. One successful selection call and
one refused registered call occurred during this planning research.

The independent read-only analysis found full requirement/task coverage and no
constitution conflict, with two high gaps and five medium planning issues.
The owning plan/tasks steps added XDG boundary tests, an explicit Jev-profile
launch, concrete initial deadlines, preserved scheduled Jev selection, conditional
small-script moves and first-TypeScript-slice workspace/import prerequisites.
The recorded 1,053-line initial size is a measurement before these notes, not a
current size claim. Required unperformed acceptance cases still prevent success.
Remaining low notes concern already stated conditional structure or later adopted
dependency evidence; no implementation is approved by the analysis.

No new dependency was adopted, no migration was built, no provider configuration
was activated and no student data was read. The metadata refusal remains a
develop-owned prerequisite for moving the privacy gate.
