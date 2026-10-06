# Tasks: Clean Architecture Migration

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md) and [contracts/](contracts/).
**Tests**: Required by the migration specification and repository rules.
**Assumption**: Existing behavior is the baseline; no implementation task is
complete merely because its plan is written. Develop owns final ledger ticks.

All task lines use IDs, story labels where applicable and concrete target paths.
Parallel markers allow only disjoint writes after their actual prerequisites.
Shared manifests/configuration and final integration have one coordinator owner.

## Phase 1: Setup — Whole-Move Planning (S0)

- [ ] T001 Write and validate whole-move records in specs/060-clean-architecture/spec.md, plan.md, research.md, data-model.md, contracts/ and checklists/requirements.md; include measured baseline and owned-code estimate.
  2026-10-06: Records written; read-only research by Claude Sonnet 5.5/high, chosen by Jev at probability 0.81/confidence 0.78. Evidence: feature XDG state research/ctx_bf6309123828/ and planning/ctx_3c171f99f9bf/. No source migration performed.
- [ ] T002 Generate specs/060-clean-architecture/tasks.md and run read-only Spec Kit cross-artifact analysis; retain the actual output in the planning Dispatch's XDG state and resolve actionable planning gaps through the owning specify/plan/task step.
  2026-10-06: 46 ordered tasks generated and format/path checks passed. Jev selected fresh Claude Sonnet 5.5/medium for read-only analysis (probability 0.53/confidence 0.42), with a 900-second soft budget; the medium/high alternatives were close. This is analysis, not the final merge review.
  Analysis found all 24 requirement/criterion keys covered, no critical issue and two high/five medium gaps. The owning plan/tasks steps resolved the XDG tests, explicit Jev-only launch, timeout, schedule and ordering gaps; immutable report: planning/ctx_3c171f99f9bf/analysis-report-attempt-1.md in feature XDG state.
- [ ] T003 Verify the S0 records using specs/060-clean-architecture/quickstart.md, record the measured diff/split decision, review the diff and present the planning slice to develop; do not tick code tasks.

## Phase 2: Foundational — Contracts and Ownership

These checks apply separately before each relevant slice; they do not create a
global framework or require held capabilities before S1.

- [ ] T004 Review the independently stated baseline in specs/060-clean-architecture/contracts/migration.md against current package/test entry points before differential acceptance; record owners, current develop base, immutable attempt paths and refreshed estimates there.
- [ ] T005 Extend the existing rules in .config/dependency-cruiser.json to adapters/composition and add meaningful violation cases in scripts/clean-architecture-test.ts when the first TypeScript package moves; preserve cycle/public-entry checks.
- [ ] T006 Add a layers contract per migrated Python capability to pyproject.toml and package-owned negative import tests; exercise composition/domain back-edges and concrete external I/O dependencies without writing a custom scanner.
- [ ] T007 Record the current scope release/trial evidence and per-slice coordination under this file before dispatch; preserve held paths and keep the root package.json, turbo.json, pyproject.toml and lockfile edits under one owner.

## Phase 3: User Story 1 — Isolated Capabilities (P1)

**Goal**: Existing capabilities keep their behavior through independently usable
package migrations. S1 document regions is the first useful increment.

**Independent test**: Preserved public cases before/after, pure rule tests,
real-entry cases and enforced inward dependencies for each moved component.

### S1: Document Regions

- [ ] T008 [US1] Run and retain the pre-move packages/doc-regions/tests and scripts/doc_sources_test.py baseline, then add the ten held-consumer import/behavior cases in packages/doc-regions/tests/integration/test_public_api.py and a real console-entry case in tests/e2e/test_cli.py.
- [ ] T009 [US1] Move pure marker, LF-line, unit and request-batching rules into packages/doc-regions/src/doc_regions/domain/; preserve existing semantics and test them without file/process/model access in tests/unit/.
- [ ] T010 [US1] Move document check/update/prepare/audit flows and their required ports into packages/doc-regions/src/doc_regions/application/; connect existing file/Cog/lychee/Git/MemoryLint behavior in adapters/outbound/ and the current CLI in adapters/inbound/ with composition.py.
- [ ] T011 [US1] Keep explicit existing exports in packages/doc-regions/src/doc_regions/{config,regions,requests,units}.py and __main__.py; update package-owned tests into tests/unit, tests/integration and tests/e2e without editing held wiki consumers.
- [ ] T012 [US1] Update the doc-regions contract in pyproject.toml and current references in docs/architecture.md; run test:doc-regions, unchanged test:wiki-consistency, doc-regions:check, import checks and full verify, then record S1 evidence and request its separate review/finish slot.

### S2: Credit Offers

- [ ] T013 [US1] Retain the packages/credit-offers/tests/test_credit_offers.py baseline, sort cases into tests/unit and tests/integration and add a real help/entry case in tests/e2e/test_cli.py; preserve output/error/notification expectations.
- [ ] T014 [US1] Move explicit clock/block/filter rules to packages/credit-offers/src/credit_offers/domain/ and the tracker/judgment/notification use case with only its needed ports to application/; remove import-time I/O from inner modules.
- [ ] T015 [US1] Move HTTP, gated MCP and notify-send integration to packages/credit-offers/src/credit_offers/adapters/outbound/; keep CLI/exit behavior in adapters/inbound/, private settings and tracker loading in composition.py and the existing console entry public.
- [ ] T016 [US1] Update the credit-offers layers contract in pyproject.toml and docs/architecture.md; verify test:credit-offers, help without network, empty/populated block call counts, malformed responses and notification failures, then full verify and a separate S2 review/finish.

### S3: Clean Code and Command Contract

- [ ] T017 [US1] Prove standard npm packaging of package-owned executable resources satisfies scripts/cli-contract-test.ts's independently copied skill case in scratch before deleting plugins/code/skills/clean-code/scripts/clean-code.ts; retain the proof and report any concrete unmet contract.
- [ ] T018 [US1] Move the current shared CLI helper once into packages/cli-contract/src/cli-contract/ with real Clean Code/workflow consumers and package.json exports; preserve JSON/help/error/exit behavior without a duplicate maintained serializer.
- [ ] T019 [US1] Move checker policy, checking use case, ESLint/compiler/files adapters and composition into packages/clean-code/src/clean-code/; keep plugins/code/skills/clean-code/SKILL.md and its script as portable thin delivery of generated package-owned resources.
- [ ] T020 [US1] Move Clean Code cases into packages/clean-code/tests/unit, tests/integration and tests/e2e; update root package.json workspace/dependency entries, package-lock.json, tsconfig.json and .config/dependency-cruiser.json together with the new public exports, preserving the local and copied-skill cases in scripts/cli-contract-test.ts.
- [ ] T021 [US1] Run test:clean-code, clean-code --scope, test:cli-contract, import/type checks and full verify; update docs/architecture.md and record/request S3 review and finish separately.

### S4: Workflow and Small Automation

- [ ] T022 [US1] Preserve the scripts/workflow-test.ts, workflow-plan-test.ts, workflow-verify-test.ts, workflow-graph-test.ts and workflow-skills-test.ts baseline and CLI snapshots; move the cases by role into packages/workflow/tests/.
- [ ] T023 [US1] Move mode/difficulty/plan/verification rules into packages/workflow/src/workflow/domain/ and use cases/ports into application/; move Git/files/graph/Turbo/skill effects into adapters/, pass the real project root and wire composition.ts.
- [ ] T024 [US1] Keep scripts/workflow.ts as the stable thin entry and move scripts/hash.ts with its existing consumers; remove the private plugin CLI import and its old exception only after packages/cli-contract serves both consumers.
- [ ] T025 [US1] Inspect scripts/coordinator-context.ts and scripts/coordinator-context-test.ts against the reuse order and actual consumers; retain already thin integration entries and move only substantial policy into packages/coordinator-context/src/coordinator-context/ when justified, preserving .claude/settings.json, .codex/hooks.json, .gitflow, orca.yaml and native shell/hook behavior.
- [ ] T026 [US1] Update package.json, turbo.json, tsconfig.json, .config/dependency-cruiser.json and docs/architecture.md for S4; run workflow/CLI/context/hook/import tests, workflow from supported directories and full verify, then request S4 review/finish.

## Phase 4: User Story 2 — Both Judgment Backends (P1, S5)

**Goal**: Both chosen routes work in the first backend slice, behind the existing
privacy boundary. Worker/model choice remains Jev-only.

**Independent test**: Synthetic privacy/protocol/slow-call cases and real
non-personal representative judgments on both profiles, with observed routes.

This phase waits for develop's release of the gate metadata bug. It can be
researched alongside S1 without editing held source or adopting unreviewed code.

- [ ] T027 [US2] Obtain an evidence-backed read-only security review of an immutable system-one-adapter revision and dependency closure before adoption; retain the reviewer report and accepted disposition with the S5 task evidence, and cite it in specs/060-clean-architecture/research.md.
- [ ] T028 [US2] Coordinate the reported metadata bug and current source release with develop before touching packages/education-privacy-gate/src/education_privacy_gate/; add synthetic continued-service/metadata cases in its tests/integration and tests/e2e after the fix is integrated.
- [ ] T029 [US2] Move pure masking policy to packages/education-privacy-gate/src/education_privacy_gate/domain/, protected-call flow/ports to application/, registry/upstream/MCP integration to adapters/ and private settings to composition.py while preserving all existing privacy contracts and public entry.
- [ ] T030 [US2] Add the two approved profile mappings and explicit --profile jev|glm entry at packages/education-privacy-gate/src/education_privacy_gate/composition.py and adapters/inbound/; connect reviewed unmodified system-one-adapter and update pyproject.toml/uv.lock only after accepted review, with synthetic tests/integration cases for missing, empty, relative and absolute XDG settings, invalid profiles/timeouts and isolated HOME, preserving one exposed gated route and loopback protection.
- [ ] T031 [US2] Extend the existing S2 judgment port/client at packages/credit-offers/src/credit_offers/application/ and adapters/outbound/ for explicit manual profile choice and aligned timeout; preserve Jev for the existing scheduled/no-flag invocation. Normally keep this port local; extract packages/judgments/ only if two released executable consumers actually share it, recording both paths here first.
- [ ] T032 [US2] Update plugins/code/skills/model-choice/references/model-choice.md's supported plain-client transport to invoke the gated jev-mcp --profile jev entry; add a synthetic caller test under packages/education-privacy-gate/tests/e2e/ with general profile GLM that verifies actual OpenRouter/Jev route evidence and fails without substitution on wrong, missing or unavailable Jev.
- [ ] T033 [US2] Align provider/client timeouts in the gate and credit-offers composition modules and the documented model-choice client; add synthetic within/beyond-deadline, cancellation, bad-answer and privacy-restoration tests to the owning packages' tests/integration and tests/e2e.
- [ ] T034 [US2] Exercise representative non-personal classify/verify/decide calls through both profiles, record actual routes/durations/counts, run all affected privacy/caller/import tests and full verify, update docs/jev-mcp.md and docs/architecture.md and request S5 review/finish; live configuration activation stays separate.

## Phase 5: User Story 3 — Whole-Move Completion (P2, S6–S7)

**Goal**: Finish surviving capabilities after their owners release them, without
lost behavior, evidence or portable plugin selection.

**Independent test**: Every surviving component has real boundaries/tests and
all three plugin selections still resolve their declared capabilities.

- [ ] T035 [US3] Obtain release/current-base evidence from lexical-semantics, korean-web-wiki, document-pdf-fidelity and exam-calendar before editing plugins/work/ or packages/wiki-consistency/; refresh the affected estimates and accepted baseline in specs/060-clean-architecture/plan.md and this ledger.
- [ ] T036 [US3] Reorganize packages/wiki-consistency/src/wiki_consistency/ into meaningful domain/application/adapters/composition boundaries and tests/unit, tests/integration, tests/e2e while preserving raw/text/wiki/site, metadata, evidence, citations, search, budgets and interrupted-write behavior; add its layers contract in pyproject.toml.
- [ ] T037 [US3] Move surviving executable work capabilities from plugins/work/skills/ into their concrete packages/<capability>/src/<module>/, recording each actual package/consumer in plan.md before dispatch; keep upstream-authored instruction-only skills unchanged and delivery thin.
- [ ] T038 [US3] Integrate develop's rulesync, chezmoi, session-scan and Jev Browser trial decisions before changing scripts/plugin-clients.ts, scripts/secrets-refresh.ts, plugins/work/skills/wiki-raw-import/scripts/session_select.py or packages/jev-ultrafast/; map only surviving reviewed glue in plan.md and this ledger.
- [ ] T039 [US3] Apply S1–S5 boundary/behavior/estimate discipline to each released replacement survivor package and keep plugin ownership/delivery intact; test no cross-plugin deep imports in .config/dependency-cruiser.json and the existing plugin validation/discovery tests.
- [ ] T040 [US3] Validate plugins/code/plugin.json, plugins/work/plugin.json and plugins/chat/plugin.json plus their declared skills/mcp.json delivery independently with real installed dependencies and native Linux clients; retain fresh model/tool-readiness evidence without reading student data or changing client settings.
- [ ] T041 [US3] Reconcile current docs/architecture.md, docs/jev-mcp.md, generated docs/reference/ and licenses/third-party-notices.md with the surviving packages; refresh required generators and report instruction drift without silently rewriting AGENTS.md or the constitution.
- [ ] T042 [US3] Execute specs/060-clean-architecture/quickstart.md across all surviving capabilities, record limits/unperformed cases and prove held/data roots unchanged before the final S7 review/finish request.

## Phase 6: Cross-Cutting Verification and Integration

- [ ] T043 Run workflow's required document preparation/audit/judgment steps for the current slice, preserve their outcomes with specs/060-clean-architecture/ record links and correct actionable target-document findings through their owning scope.
- [ ] T044 Record measured diff and the required split assessment per slice in specs/060-clean-architecture/plan.md or a slice record; review each diff before a Conventional Commit with every covered Spec-Kit-Task trailer.
- [ ] T045 Verify the current merged develop base, obtain the fresh other-provider review and content-free tip record, and request the serialized finish/board transition from develop; record receipts under the corresponding task in specs/060-clean-architecture/tasks.md.
- [ ] T046 Develop: after each successful finish and verified develop tree, tick only the finished slice's tasks in specs/060-clean-architecture/tasks.md and record merge/review/verify/next-work evidence; finish the feature's Linear issue when the whole move is merged.

## Dependencies and Execution Order

T001 → T002 → T003 is S0. T004/T007 apply before each dispatched code slice.
T006 is integrated with each Python move; T005 with the first TypeScript move,
so neither needs empty future package placeholders.

S1: T008 → T009 → T010 → T011 → T012.
S2: T013 → T014 → T015 → T016.
S3: T005 → T017 → T018 → T019 → T020 → T021; workspace/dependency/lock entries
are coordinated with the package moves in T018/T020, not deferred until S4.
S4: T022 → T023 → T024/T025 → T026; T024 needs T018.
S5: T027 and develop's bug release precede T028–T030; T031–T033 connect the
actual callers before T034. Both routes are acceptance gates for this slice.
S6/S7: T035 precedes T036/T037; T038 precedes T039; T040–T042 check the result.
T043–T046 apply to each coherent integration slice, not only the final one.

There are no unconditionally parallel writable task scopes in this initial
ledger: early packages share root import/manifests and the same document targets.
That is a current ownership fact, not a global sequential-only policy.
Before any parallel wave, declare exact disjoint files in a workflow plan and
let its result govern eligibility. Read-only research/security review can run
alongside scoped implementation without sharing writes; a full verify remains
machine-wide single-run.

## Parallel Examples and Implementation Strategy

For US1, an independently scoped document-rule review and a credit-offer baseline
inventory can run together; only the coordinator updates shared configuration.
For US2, upstream security review can run while S1 is built, but it cannot install
the reviewed dependency or edit the held gate. For US3, released instruction-only
inventory and native-plugin test planning may run independently; actual shared
work/wiki writers wait for owner releases and workflow-scoped disjointness.

Deliver S0 first, then S1 as the smallest working capability migration. Continue
S2–S4 in separately reviewable slices, S5 after its real gates, and held survivors
only after current source/trial decisions arrive. No later task tick or feature
completion follows from the first useful slice. Required resume/evidence lives
in feature XDG state under each task/Dispatch; .local copies are disposable.
