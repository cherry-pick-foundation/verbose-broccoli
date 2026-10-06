# Implementation Plan: Clean Architecture Migration

**Branch**: `feature/clean-architecture` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: The whole-move specification and the user's component-package decision.
**Assumption**: Preserve existing public behavior. Keep explicit package exports for
unmigrated consumers; use generated portable delivery resources where a skill
must run independently. Neither requires duplicate maintained implementations.

## Summary

Move surviving implementation into capability packages with inner rules,
application-owned ports, outer adapters and one composition module per package.
Keep the three plugins as delivery roots. Start with unowned components and
integrate each coherent slice separately. The first backend slice delivers both
Jev and GLM through the same education privacy gate; model selection stays Jev.

No ring-wide package or common application framework is needed. Existing Cog,
Markdown parsers, Git, FastMCP/MCP clients, ESLint, TypeScript, Turborepo and import
checkers perform their existing work. [research.md](research.md) records evidence,
reuse choices, concrete constraints and the code-size method.

## Technical Context

**Language/Version**: Preserve each Python package's current requirement
(doc-regions >=3.13, credit-offers >=3.12) and the locked uv workspace.
TypeScript runs through the existing Node >=24.12 entry route.

**Primary Dependencies**: Existing pinned Cog/markdown-it-py, httpx, FastMCP/MCP,
Faker, Cliffy, ESLint, TypeScript, dependency-cruiser and import-linter.
The pinned upstream jev-mcp stays unmodified. Reintroducing system-one-adapter
requires the read-only security review before adopting its reviewed revision.

**Storage**: Existing files, Git and approved XDG roots. PGlite remains the
relational-store rule; this migration creates no database for components that
currently need none. No real wiki or provider configuration is relocated.

**Testing**: Preserve pytest and Node test suites; sort existing tests by
unit/integration/e2e role and add boundary/entry cases where a real gap exists.
Synthetic identities and temporary files only; no student-data reads.

**Target Platform**: Existing Linux native command and plugin routes.
**Project Type**: Multi-language capability workspace, three Agent Plugins 1.0 roots.
**Performance Goals**: Preserve command behavior and bounded storage/call budgets.
GLM's initial request timeout is 300,000 ms, with an initial 330-second caller
deadline; Jev keeps 60,000 ms and a 90-second caller deadline. Verify those
deadlines against upstream's full operation/retry behavior and adjust the caller
upward if necessary, without duplicating upstream retries. Slow-call acceptance uses a controllable
synthetic server, not several minutes of every routine test.
**Constraints**: Inward dependencies, no speculative ports, no silent backend
fallback, no extra publication/client formats, separately reviewed slices.
**Scale/Scope**: Whole surviving repository implementation; held and replacement
paths are inventoried but cannot be edited until their owners release them.

## Constitution Check

| Gate | Design disposition |
| --- | --- |
| I: proven dependencies and PGlite | Preserve locks and reused tools; no new relational store. Review adapter adoption first. |
| II/V: working behavior and observable acceptance | Record baseline, retain cases and prove real entries; planning completes no implementation task. |
| III/VI: sources, privacy and storage | No data-root moves or student reads; synthetic privacy checks; settings stay outside Git. |
| VII: minimum implementation and one owner | Actual external seams only; public re-exports contain no copied logic; use existing packaging/import tools. |
| IX: three plugins and implementation packages | Keep code/work/chat roots and thin scripts. Capability implementations live under packages; no fourth plugin or ring-wide runtime. |
| Workflow/review | Follow workflow before edits/scope changes/completion, verify one run at a time, cross-provider merge review and current develop base. |

The design needs no constitution change. If an implementation would change a
governed rule, stop that slice and use the explicit amendment procedure;
a major amendment still needs the user.

## Project Structure

### Documentation (this feature)

```text
specs/060-clean-architecture/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/migration.md
  contracts/judgments.md
  checklists/requirements.md
  tasks.md
```

The consistency analysis is read-only; retain its output with the Dispatch's
evidence and reference it from the task ledger.

### Source Code (repository root)

```text
plugins/{code,work,chat}/
  plugin.json
  skills/
  mcp.json                         # only where declared
  thin delivery entries
packages/<capability>/
  pyproject.toml or package.json   # no nested workspace manifests
  src/<module>/
    domain/
    application/                  # use cases and required ports
    adapters/inbound/
    adapters/outbound/
    composition.py or composition.ts
  tests/unit/
  tests/integration/
  tests/e2e/
scripts/                           # stable automation entries/configuration
tools/                             # unchanged upstream development programs
```

Python import roots use snake_case; repository package names and TypeScript
paths use kebab-case. Empty rings, unused tests and blanket nested AGENTS.md
files are not scaffolding: add a directory only with useful content. A component
with only integration behavior has an adapter/composition entry and a real test,
without an invented domain entity.

| Capability | Source destination and required seams |
| --- | --- |
| document regions | Existing doc-regions package: pure marker/unit/request rules; application flows with file, generator/link, Git and audit ports; current CLI becomes inbound adapter. |
| credit offers | Existing credit-offers package: explicit time/filter rules; application uses tracker, judgment and notification ports; composition loads tracker/provider settings. |
| Clean Code | New clean-code package: selected-file/rule policy, checking use case, ESLint/compiler/files adapters and command entry. Prove independent skill delivery before removing old source. |
| command contract | New cli-contract package only when Clean Code and workflow consume it; move the existing 49-line helper rather than duplicating it. |
| workflow | New workflow package: work-mode/difficulty/plan/verification policy, use cases and Git/graph/files/Turbo/skill adapters. scripts/workflow.ts remains the stable thin entry. |
| small automation | Inspect context policy/consumers against reuse first; keep already thin native hooks/shell/configuration entries in scripts and move only substantive policy to a capability package. Move hash.ts with its actual workflow consumers. |
| privacy gate | Existing education-privacy-gate package after develop releases the metadata bug: pure masking rules, protected-call use case, upstream/registry/MCP adapters, private composition settings. |
| work and wiki capabilities | Existing wiki-consistency and surviving work implementations after their branch holds. Retain raw/text/wiki/site roles, public evidence APIs and PGlite policy. |
| replacement survivors | Incorporate reviewed trial outcomes before mapping discovery, secrets, session selection and browser glue; do not move the code that may be deleted. |

A shared judgment package is conditional on a demonstrated second executable
consumer. Credit offers can own its small judgment port/client adapter initially.
If model-choice delivery or a released browser/session consumer uses the same
client implementation, extract that implementation with both consumers in the
same slice. Do not add a shared ports framework.

S2 retains the approved Jev route for credit offers. S5 adds an explicit manual
profile selection while its unchanged scheduled invocation continues to use Jev;
the new general GLM setting cannot silently change that automation's provider.
The planned gate entry `jev-mcp --profile jev` launches a separate ephemeral
gated client instance for model-choice, independent of the general profile.
This is an added CLI capability in S5, not an already available command.

## Migration Slices and Release Gates

| Slice | Scope | Ready condition and proof |
| --- | --- | --- |
| S0 | Whole-move Spec Kit records | Analysis, measured baseline/estimate, workflow and full verify; docs-only integration can precede code. |
| S1 | doc-regions and its import contract | Preserve current import names, generator/CLI behavior and unchanged wiki consumers; narrow tests then full verify. |
| S2 | credit-offers and its import contract | Preserve six-hour behavior, one classify call per populated block, exit/notification/privacy boundaries; no new scheduled provider setting. |
| S3 | Clean Code and shared command contract | Standard npm packaging proves copied-skill execution; existing CLI help/error snapshots remain valid; no copied maintained serializer. |
| S4 | workflow and small automation | Preserve all external entry paths; root-aware adapters replace module-depth guesses; CLI/graph/hook tests pass. |
| S5 | gate and two judgment backends | Metadata bug coordinated, security review accepted, both routes work, Jev-only selection and slow/failed-call cases pass. |
| S6 | work/wiki implementation | All four listed feature owners release affected paths; reread merged sources, refresh estimates, preserve evidence and storage contracts. |
| S7 | reviewed replacement glue and whole-workspace acceptance | Trial decisions integrated; each surviving capability has boundaries/tests, all plugins selectable, final current-base verification/review. |

S1 and S2 may be researched independently; shared root configuration edits have
one coordinator owner. Build and merge coherent slices, rather than accumulating
the whole migration on one unreviewed tip. Request each finish slot from develop.
If a slice reaches 1,000 changed lines, assess splitting by actual capability and
risk; line count alone is not a stop or an invented cap.

S0 split assessment, 2026-10-06: the initial records contain 1,053 lines before
analysis notes. Keep the specification, plan, contracts and task sequence in one
coherent documentation slice: separating them would leave either review missing
its requirements or implementation ordering. No runtime source is changed in S0.
Later code slices remain separate, with their own measured split assessment.

Before every finish, integrate current develop without auto-resolving conflicts,
verify the resulting feature tree, renew independent review and record it at the
tip. Recheck develop immediately before finishing. Develop owns Linear, its
final task ticks and the finish; board state is in-review for review and
completed only after the finish. Never push under this feature authorization.

## Locally Owned Code Estimate

The first code slices currently contain **3,124 source lines** in doc-regions,
credit-offers, Clean Code and workflow, plus 172 generator lines, 11 hash lines
and 161 coordinator-context lines. Their tests contain **4,068 lines**, plus
166 generator and 346 context-hook test lines. These are measured physical
lines, including comments/blank lines, not projected additions or test passes.

| Work | New or materially rewritten integration/rule-boundary source and config | Added acceptance/boundary test lines |
| --- | --- | --- |
| First safe code slices | 250–450 | 100–200 |
| Both backend routes and timeout/gate integration | 80–180 | 100–220 |
| Held surviving capabilities, provisional until owners release them | 250–500 | 200–400 |
| Whole move, provisional total | **580–1,130** | **400–820** |

Most existing source/tests move and are adjusted, not replaced by new local
implementations. The measured early source/test counts are independent of these
estimates. Estimates include required ports, composition, public exports, native
packaging glue and import contracts; they exclude upstream unmodified copies and
Spec Kit prose. Recalculate per slice before dispatch and report measured change
afterward. The shared 49-line serializer is moved once. No line budget or approval
gate is derived from this estimate.

Reuse existing standard npm packaging for portable runtime delivery. Do not
introduce a custom bundler or another maintained implementation to satisfy the
copied-skill contract. A scratch packaging proof precedes deletion of the old
checker. If standard packaging cannot preserve the actual contract with minimal
glue, report the concrete limitation before changing that scope.

## Verification Strategy

Use [quickstart.md](quickstart.md) and the two contracts. Record pre-move cases,
run the narrowest affected tests, then import checks, real commands and full
verification. Python uses one import-linter layers contract per migrated package;
TypeScript extends existing rules to adapters/composition. Negative fixtures
must prove those named rules reject real forbidden imports, including composition
back-edges and I/O imports in pure rules. Static imports do not prove absence of
all dynamic I/O; isolated rule tests and real-entry cases supply that evidence.

No recorded collection count proves a passing test. No handshake proves judgment
quality, copied-skill execution or privacy. Record every unperformed check and
all live judgment call counts. Evidence is immutable per attempt in XDG state,
with repository verification receipts preserved under artifacts as required.
