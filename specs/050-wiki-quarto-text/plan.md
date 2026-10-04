# Implementation Plan: Persistent Text and Quarto Wiki

**Branch**: `feature/wiki-quarto-text` | **Date**: 2026-10-04 |
**Spec**: [spec.md](spec.md)

## Summary

Adapt existing Wiki readers, converters, request preparation and skill writers.
Retain original-language extraction in `text/`, maintain English `.qmd` knowledge
in `wiki/`, and resolve sentence citations to exact retained spans. Keep Cog and
BagIt as their current authorities. F2 consumes the contract for Korean delivery.

The independent baseline caller map and preservation inventory are settled.
Implementation uses disjoint exact-file scopes and their public reader contracts.
No new real conversion batch or publication is part of the current work.

## Technical Context

**Language/Version**: Current repository Python 3.14 through its uv workspace;
Node/TypeScript for existing integration checks. Read current toolchain pins.
**Primary Dependencies**: Existing PyYAML, markdown-it-py, Cog, BagIt, MarkItDown,
python-hwpx, doc-regions, Vale, lychee and `@tobilu/qmd`. Native bundled Pandoc
parses citations. Sentence segmentation is an identified missing capability:
independent source/fit review selected conditional pySBD 0.3.4, with no runtime
package dependencies; develop approved its scoped adoption. Native source-position
limits require restricted exact alignment and explicit unresolved shapes; no
custom natural-language parser fallback or unconditional completeness claim.
**Storage**: Raw outside Git; `text/`, `wiki/` and schema in vault-local Git with
no remote. Rebuildable bibliography/search in XDG cache. Attempt evidence and
resume state in XDG state, not scratch. Site language/storage base only in F1.
**Testing**: Existing pytest and repository Node checks, extended with synthetic
fixtures; before/after private migration receipts contain local manifests only.
**Target Platform**: Current Linux machine and existing four vaults.
**Project Type**: Work-plugin reusable CLI package and skill/schema integration.
**Performance Goals**: Metadata merges in-process, no `quarto inspect` per page;
exact evidence spans avoid full-document judgment payloads. Reuse earlier
measurements; do not add a redundant paid benchmark.
**Constraints**: No raw writes, foreign staged commits, private repository data,
new paid proposer/conversion run, publication, push or external account change.
**Scale/Scope**: Historical 176 pages and 109 repeated profiles require current
aggregate verification; four retained reference extractions. Initial estimate:
400-700 locally owned implementation lines, plus 350-600 test changes and
records. This estimate is not a cap; the trace worker will refine it.

## Constitution Check

| Principle/rule | Before design | After design |
| --- | --- | --- |
| I / VII reuse | Existing libraries and converters; no speculative new service | Same; missing substantial capability is a blocker with upstream options |
| II / V observable acceptance | Synthetic cases plus actual migration readback | Required frozen snapshot, actual outputs, negative/boundary evidence |
| III / IV ownership | Authorized existing data migration only; raw unchanged | Writer window through develop; scoped own-account workers |
| VI roles | Current Markdown/cache-only statements conflict with approved design | Approved T002 amendment applied once at 2.7.0; its feat commit is 3a7bb54 |
| IX packaging | Existing work package and three plugins | No new plugin or service |
| Governance | User approved feat/MINOR amendment | One Commitizen bump in its one amending commit |
| Review / integration | Implementer cannot final-approve | Fresh other-provider review; develop owns finish and final ticks |

The user-approved principle VI amendment is applied, with one Commitizen MINOR
bump; it is recorded separately from code dependencies and entered feat commit `3a7bb54`. It did not gate unrelated code work. Historical specs remain unchanged
and are superseded by spec 050.

## Project Structure

Feature records are `spec.md`, `plan.md`, `tasks.md`, `research.md`,
`data-model.md`, `contracts/text-citations.md`, `quickstart.md` and the spec
quality checklist in this directory. Do not create a separate development Wiki.

Runtime changes stay in `packages/wiki-consistency/src/wiki_consistency/` and
its tests; profile/reference consumers remain under the grammatical-competence
skill. Raw-import initialization, schema/template, current example/architecture
and affected skill references receive only changes required by this contract.
Absent held-feature implementations are reported, never restored from branches.

## Phases and ownership

1. Orchestrator: current-source research, specification, necessary clarification,
   plan, tasks and consistency analysis. Bind child Run; share contract through
   develop. No implementation task is completed by planning.
2. Scoped worker: explicit constitution/base schema amendment and one MINOR
   bump; its scoped work may run beside unrelated code. Graph/diff/caller evidence
   and real shared-file/contract dependencies govern implementation ordering.
3. Workers: `.qmd` discovery/metadata/special pages and consumer migration;
   persistent text/provenance/locator/bibliography; exact-span requests and
   indexing integration. Use disjoint writable scopes supported by fresh workflow
   graph evidence. A shared function has one owner and all callers are traced.
4. Orchestrator: integrate worker output and route fixes; run narrow checks.
   Synthetic acceptance comes before real writes. Worker receipts keep paid and
   conversion results immutable; every retry uses its Dispatch directory.
5. Own-account migration workers, after develop's writer window: capture a fresh
   before-state, preserve bodies/status/log and foreign index, rename every page,
   relocate four reference side files, consolidate repeated scalar defaults,
   read back every result and check raw and Git preservation. Scope commits so
   no foreign staged edit is included. No new conversion batch.
6. Frozen feature: coordinate full verify slot with develop, check no other Turbo
   run, inspect output and the same run summary. Measure size and review a split
   at the existing 1,000-line trigger. Merge current develop with no automatic
   conflict resolution, verify combined snapshot, obtain fresh independent review,
   and request develop integration with reviewed commit/tree and exact evidence.

All batch tests use `systemd-run --user --scope -q -p CPUWeight=20 nice -n 10
 taskset -c 4-7`. Full verification is machine-wide serialized and needs a grant
naming frozen source and immutable attempt paths. Source drift renews acceptance.

## Coordination and records

Parent authority remains `task_7f4be5b7264e` / `ctx_7b0ae78bdbe8`, supervised by
Run `run_9cb76d19f9da`. Child Run is `run_aa1d2173d50c`. Native launch requested
and effective: Codex `gpt-6.1-sol`, effort `high`, structured session
`d57b719d-0fc4-42de-919d-36b525932a38`. Planning state is
`~/.local/state/verbose-broccoli/workspaces/feature-wiki-quarto-text/CHE-84/ctx_7b0ae78bdbe8/`.
The initial Jev 60-minute checkpoint is an estimate, not a stopping/usage cap.

F1 owns checker/base schema and sends its settled contract through develop.
F2 initially owns only records/dependency review. Main owns raw selection and
publication/privacy choices; develop relays them and coordinates shared writes.
No direct main or Linear messages. The startup-generated client config stays
until cleanup through the supported receipt-owned route before commits.

## Held work and limitations

A missing extraction or locator is reported; format migration alone does not
make judgments checked. New raw conversion waits for main's selection/admission
notification through develop. Student-bearing conversion, site readers and
publication selection remain undecided. The task ledger names each owner and
next action; held tasks stay unticked. Catalog navigation and direct reading do
not depend on these held choices.

## Recovery and current verified scopes

Orca restarted before 03:52 UTC on 2026-10-04. The same parent authority and
child Run remain live; completed calls, tests and workers were not repeated.
Foundation source hashes match all 13 files in its retained snapshot. Its scoped
217 Wiki and 124 doc-regions tests passed; raw initialization passed 45 tests.
Retained-reader receipt refinement passed 63 tests; grammar passed 18, and
schema/procedure checks passed. Request integration and concrete migration
preview settled with their scoped receipts. Full verification attempt 02 passed
47/47 on its frozen source, as recorded in tasks.md. Existing work/chat/default
migration is active within the explicit writer window; code migration, document
judgments, final independent review and develop integration remain pending.

## Split assessment before develop review

Assumption: retain the approved F1 feature boundary and use separate logical
commits unless develop assigns a separate prerequisite feature. The settled
production scopes total +890/-251 (net 639); settled tests total +1315/-209
(net 1106), excluding ongoing requests, docs, records and actual vault content.
The existing 1,000-line trigger is met; it is not a cap or a success criterion.

The independently useful shared adapter boundary is exactly
`packages/doc-regions/src/doc_regions/regions.py` (+88/-21) and
`packages/doc-regions/tests/test_regions.py` (+111/-0), 220 changed lines.
It adds optional byte-exact views to the existing checker, without importing
F1 modules or changing default Markdown callers. Its retained 124-test suite
passed. A patch/hash receipt is `split-adapter-candidate.*` in planning state.

Recommendation: isolate those two files in the first prerequisite commit, then
metadata, retained text, existing consumers, request integration and role/docs
commits. The remaining F1 data-format transition stays together because readers,
writers, schema and actual preservation acceptance share the same contract;
merging half that transition would leave incompatible live consumers. A separate
adapter feature is technically possible but needs develop's feature/record
ownership assignment, not an automatic branch from line count. This assessment
will be refreshed with frozen total size before final review and does not approve
the implementation or merge.

Current production estimate including request/search/CLI is 950-1100 net lines
(last in-flight measurement 971, including a 274-line citation adapter). Frozen
source and test/docs totals will be reported separately. Develop approved the
adapter-first prerequisite commit within F1 in msg_a5a4181734d8; no separate
feature is assigned. Grants are recorded in tasks.md; no later grant or extension is inferred.


At the first committed-source freeze, exact F1 measurement against its approved
merge base is implementation +1574/-609 (net965), tests +2308/-1635 (net673),
current documents +455/-153, and configuration/lock +19/-1. Records are separate
and still advance with operational evidence. An initial measurement compared
an advancing develop tip and is retained as superseded evidence; the fixed-base
measurement replaces it. The existing split decision remains adapter-first
within F1; no line cap or additional feature is introduced. Current develop has
advanced with unrelated secrets-refresh work; synchronization and combined
frozen verification/review are still required before integration.
