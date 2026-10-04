---
description: "Tasks for persistent text and Quarto Wiki migration"
---

# Tasks: Persistent Text and Quarto Wiki

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contract](contracts/text-citations.md).

**Authority**: CHE-84, F1; parent `task_7f4be5b7264e` /
`ctx_7b0ae78bdbe8`, develop Run `run_9cb76d19f9da`, child
`run_aa1d2173d50c`. The feature orchestrator owns planning/integration;
scoped workers implement. Develop owns final ticks and finish.

**State**: Authoritative planning/choice/start receipts:
`~/.local/state/verbose-broccoli/workspaces/feature-wiki-quarto-text/CHE-84/ctx_7b0ae78bdbe8/`.
Each worker uses its own current Dispatch directory under the same CHE-84 root;
completed receipts and paid/conversion results are immutable. Scratch is not
resume state. Tests use synthetic data and batch CPU limits from AGENTS.md.

## Phase 1: Setup and independent research

- [ ] T001 Settle current-source caller map and aggregate vault inventory in
  `research.md`; finalize `spec.md`, `plan.md`, contract and this ledger after
  consistency analysis. Planning completes no implementation task.
  - 2026-10-04: Draft records written; initial child Run bound and independent
    read-only wave launched. Caller trace `ctx_9832c2de7df4` is Codex
    gpt-6.1-sol/high (.77/.71), checkpoint 45 min (.45/.33); preservation
    inventory `ctx_17cfaf8b5c36` is gpt-6.1-sol/medium (.80/.77), checkpoint
    30 min (.85/.83). Repository trace and inventory settled and released with all four vault
    and raw/cache/Git preservation comparisons passing. Current count is 176; all
    109 checker values remain `none`; four side files are verification-needed.
    Code's 11 staged edits remain held pending main's selected review; no writes.
  - Initial feature choice was gpt-6.1-sol/high (.36/.29); checkpoint 60 min
    (.79/.74), from develop's retained `wiki-quarto/run_9cb76d19f9da/initial-20261004T020754Z`.
    These estimates are not stopping or usage caps. Native requested/effective
    model/effort match; session is `d57b719d-0fc4-42de-919d-36b525932a38`.
- [ ] T002 Amend `.specify/memory/constitution.md` principle VI with approved
  raw/text/wiki/site/schema roles and current language/storage history; include
  `pyproject.toml`'s matching Commitizen version field and use
  Commitizen once with `--files-only --increment MINOR` in one `feat` amending
  commit. Coordinate base schema/contract through develop before F2 writes.
  - 2026-10-04: Scoped amendment worker `task_b9a684c14a66` /
    `ctx_57f79d743fa2` launched natively at gpt-6.1-sol/medium, Jev .38/.25;
    30-minute checkpoint .78/.74. Only constitution and Commitizen version field
    were writable; one bump from 2.6.0 to 2.7.0 and the focused test passed.
    The worker settled and was released; no second bump is permitted. The single
    amendment commit is `3a7bb54`; final acceptance remains pending.

## Phase 2: US3 - Quarto discovery and metadata foundation

Goal: every maintained page and caller reads `.qmd`, inherited metadata retains
meaningful page overrides, Cog and append-only log work offline. Independent
checks are synthetic discovery/link/catalog/default/override/log-rename cases.

- [ ] T003 [US3] Add regression cases in `packages/wiki-consistency/tests/`
  for `.qmd` ordinary/special discovery, nested metadata and explicit overrides,
  local links/fragments, Cog catalog and old committed log-prefix rename.
- [ ] T004 [US3] Adapt `instance.py`, `lint.py`, `rules.py`, `sources.py` under
  `packages/wiki-consistency/src/wiki_consistency/` with one shared metadata
  reader, native library reuse and no per-page `quarto inspect`; keep raw and
  existing page/privacy rules outside text/site. Update affected synthetic tests.
  - 2026-10-04: Foundation `task_0b79f0c3c6fc` / `ctx_be847b88577b`, Codex
    sol/high (.88/.86; 60-minute estimate .76/.71), settled and released: 217
    scoped Wiki tests, 124 doc-regions tests and import/lint checks passed. All
    13 hashes match the verified snapshot after restart. Main approved named
    metadata inputs in `msg_d65e95808fbb`; request integration remains pending.
- [ ] T005 [US3] Update `plugins/work/skills/wiki-raw-import/scripts/raw_import.py`
  initialization and `scripts/wiki-raw-import-test.ts` for the new special-page
  names and text role; preserve create-only raw/init behavior.
  - 2026-10-04: `task_f09b62aa0f43` / `ctx_8c89ed65a329`, sol/medium
    (.43/.32; 30-minute estimate .68/.62), settled and released. Eight focused
    regressions failed before the fix and passed after; all 45 owned integration
    tests passed, with actual qmd/text and legacy collision preservation checks.
- [ ] T006 [US3] Adapt `plugins/work/skills/grammatical-competence/scripts/grammatical_competence.py`
  and its tests for `.qmd` inventory/profile/reference/mapping reads and writes,
  inherited defaults and retained text references; do not rerun paid proposals.
  - 2026-10-04: Grammar `task_d21d62b4472f` / `ctx_1d0252610e86`,
    sol/medium (.83/.79; 30-minute estimate .92/.91), settled and released.
    All 18 synthetic tests passed, eight regressions failed on old consumer;
    source +103/-21 and tests +242/-19. Legacy line/provenance reconciliation
    remains operational, with no paid rerun or private data action.
- [ ] T007 [US3] Update affected current skill procedures, schema template
  `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  `docs/examples/wiki/AGENTS.md` and `docs/architecture.md`. Trace retained
  lexical-semantics references without rebuilding an absent held capability.

## Phase 3: US1 - Persistent original-language extraction

Goal: full text is retained per exact raw revision with honest provenance.
Independent checks are conversion/reuse/readback/conflict/unknown-status cases.

- [ ] T008 [US1] Extend `packages/wiki-consistency/tests/test_evidence.py` with
  retained text, exact hash/revision, unknown legacy provenance, correction
  retention, conflict/interruption and unchanged-raw tests.
- [ ] T009 [US1] Adapt `packages/wiki-consistency/src/wiki_consistency/evidence.py`
  and CLI wiring in `__main__.py` to reuse current converter paths, publish one
  full `text/<source-id>/<revision>.qmd` and read existing text without reruns;
  expose unreadable/partial/provenance failures. New live batch is held.

## Phase 4: US2 - Exact citation evidence

Goal: each cited sentence receives only its referenced span. Independent checks
exclude uncited sentinels and reject missing/duplicate/range/provenance errors.

  - 2026-10-04: Retained text `task_e2c00ae6beb2` / `ctx_55ff8f1ffdc5`,
    sol/high (.87/.85; 60-minute estimate .64/.56), owns only evidence.py and
    its two tests. Prior 55-test result is retained; the later byte-bound review
    receipt refinement finished with all 63 scoped tests and official CSL shape
    validation passing; the worker settled and was released. No real conversion.
- [ ] T010 [US2] Add synthetic citation/locator/bibliography cases in
  `packages/wiki-consistency/tests/test_prepare.py` and related focused tests,
  including per-sentence inputs, bag-derived keys/revisions, page/section/range
  boundaries, missing text/hash/locator, request limits and no source fallback.
  - 2026-10-04: Native Pandoc handles canonical keys/locators but cannot prove
    segment sentence completeness. Upstream security/fit review
    `task_250b2189bda5` / `ctx_d6ac0a8b4a8f`, sol/high (.60/.51; 30-minute
    estimate .85/.83), evaluates pySBD/syntok before adoption. Mixed or ambiguous
    prose must remain unresolved; a dependency changes the original estimate.
  - 2026-10-04: Read-only review settled/released; conditional pySBD 0.3.4
    adoption approved by develop `msg_97f674fbf11f`, with exact coverage and
    unresolved ambiguity requirements. Request integration `task_f0263a0bcf5f` /
    `ctx_9bfed00b20dc`, sol/high (.81/.78; 60-minute estimate .54/.46), owns
    only its source/tests/package pin and uv.lock. Native sourcepos gap permits
    restricted exact alignment, never a general parser or unchecked shape.
- [ ] T011 [US2] Adapt `packages/wiki-consistency/src/wiki_consistency/requests.py`
  using reused parsing plus narrow exact-locator glue; preserve overview,
  cross-page search and log exclusions while rejecting unresolved evidence.
- [ ] T012 [US2] Implement run-local BagIt-derived citation data in the existing
  source/evidence package with synthetic tests; retain no bibliography in Git
  and generate it every consuming run. Publish the concrete interface in
  `contracts/text-citations.md` through develop for F2 renderer integration.
- [ ] T013 [US2] Adapt `packages/wiki-consistency/src/wiki_consistency/search.py`
  and `tests/test_search.py` collection masks/root/counts for `.qmd` and retained
  text; inspect the real pinned qmd output. Avoid broadening cited evidence.

## Phase 5: US4 - Schema and F2 contract

Goal: layers and language roles agree. Independent checks inspect schema and
synthetic role separation; publishing remains F2/main-owned.

- [ ] T014 [US4] Align base schema/example and current records with original
  text, English Wiki topics and Korean site tags, no `ko/`, local Git and
  cache-only citation data. Send settled contract through develop; coordinate
  shared checker/schema writes before F2 implementation.
  - 2026-10-04: Schema/procedures `task_d7aefd07d593` / `ctx_83b1cb10a88c`,
    sol/medium (.80/.76; 30-minute estimate .90/.88), settled and released:
    eight documents +323/-110, document checks/resource test/13 init cases
    passed. Source/operational/final acceptance remains separate.

## Phase 6: Existing-vault migration

Goal: every current page migrates with exact preservation evidence. This phase
needs repository narrow checks and develop's confirmed vault writer window.

- [ ] T015 [US3] Capture fresh aggregate counts and private before-state receipts
  for all four vaults: exact HEAD/index/dirty changes, raw bytes/modes, bodies,
  metadata, committed log and side-file provenance. Check against first inventory.
  Owner: own-account scoped worker; next action: develop confirms writer window; code additionally needs main's
  selected review to settle its 11 staged edits first.
  - Current owner/next action: Feature coordinator; next: seal all-four preservation and repaired-source read-only acceptance.
  - 2026-10-04: Read-only concrete preview `task_aadaf3ea6040` /
    `ctx_a9e61da859c2`, sol/high (.78/.74; 60-minute estimate .56/.48),
    reuses completed inventory and adds needed private action/page-shape
    evidence. No write window or actual migration is authorized by that preview.
- [ ] T016 [US3] Migrate all existing `wiki/**/*.md` including index/overview/log
  to `.qmd`, correct necessary references, consolidate only equivalent defaults
  in `_metadata.yml`, preserve unchecked status, every body and foreign edits.
  - Current owner/next action: Feature coordinator; next: seal all-four preservation and repaired-source read-only acceptance.
- [ ] T017 [US1] Move the four existing `wiki/references/*.markdown` conversions
  into `text/` with body/provenance preservation and honest unknown fields;
  reuse existing conversions only. No new conversion batch.
  - Current owner/next action: Feature coordinator; next: retain four-text preservation receipts in final handoff.
- [ ] T018 [US3] Read back every migrated page/text, catalog, metadata and log;
  prove raw and foreign index preservation, scope only authorized own commits
  and retain before/after receipts. Report unresolved semantic evidence separately.
  - Current owner/next action: Feature coordinator; next: collect code commit/readback and run repaired-source read-only acceptance.
- [ ] T019 [US1] Convert and review newly selected raw revisions only after main
  notifies develop of completed selection/admission. **Held**: main owns the
  checkpoint `~/.local/state/verbose-broccoli/workspaces/main/wiki-raw-selection/`;
  next action is selection notification. Student-bearing conversion is undecided;
  neither page migration nor side-file reuse grants this batch.

## Phase 7: Acceptance and develop integration

- [ ] T020 Integrate scoped worker output, run narrow tests and full synthetic
  acceptance from `quickstart.md`; retain real readback/no-network/catalog/log
  evidence and exact command/results, resolve actionable findings through workers.
  - Current owner/next action: Feature coordinator; next: integrate repaired-source verification and renew independent review.
- [ ] T021 Measure own implementation and total diff against develop; review a
  split if the existing 1,000-line trigger is reached. Commit current records,
  clean only receipt-owned setup config before own commits, and prepare/audit
  current document judgments under workflow with retained results.
  - Current owner/next action: Feature coordinator; next: rebind scoped document evidence after repairs and refresh exact size.
  - 2026-10-04: Split assessed in plan.md: settled production +890/-251 and
    tests +1315/-209; the separable two-file doc-regions adapter is 220 changed
    lines with retained 124-test evidence and a private patch/hash receipt.
    Recommended separate prerequisite commit within approved F1; a new feature
    requires develop assignment. Frozen size/final review remain pending.
- [ ] T022 Merge current develop into this feature without guessed conflict
  resolution, freeze commit/tree and obtain develop's serialized full verify
  grant; retain start/exit and same Turbo summary and inspect actual outputs.
  - Current owner/next action: Feature coordinator/develop; next: freeze repaired synchronized source and obtain a fresh full-verify grant.
- [ ] T023 Obtain fresh final review from another provider on the frozen scope
  and requirements only; resolve findings, rerun affected checks and renew review
  on material change. Never final-approve the implementing provider's change.
  - Current owner/next action: Feature coordinator; next: choose a fresh other-provider reviewer for repaired scope and requirements.
- [ ] T024 Request integration through develop with reviewed commit/tree, exact
  verify/migration evidence, measured size and unticked held tasks. Develop owns
  review state, final ledger ticks and finish; mark worktree completed after finish.
  - Current owner/next action: Feature coordinator/develop; next: submit reviewed commit/tree and exact acceptance, keeping operational holds explicit.

## Dependencies and parallel examples

T001 settles exact scopes; T002 is a separate approved amendment and may run
beside unrelated code. Only real file/contract dependencies gate work. T003/T004 are
the metadata foundation; T005/T006 can run independently in disjoint files after
the contract settles. T008/T009 and T010/T011/T012/T013 have real evidence-reader
interfaces, so bind them before dispatch rather than assume shared-file safety.
T007/T014 share schema/docs and have one worker. Migration T015-T018 follows
narrow synthetic acceptance and confirmed writer ownership. T019 stays held and
cannot be marked complete for implementing its capability. T020-T024 require
all active child Dispatches settled and actual acceptance evidence.

First independent wave: read-only repository caller map and own-account vault
preservation inventory run concurrently. Implementation waves use temporary
exact-file plans outside Git and fresh task IDs with fixed base; graph/diff
reasons are resolved before write dispatch. No parallel shared-file writers.

2026-10-04 record correction: develop message `msg_cf92168e44ac` reserves
`specs/050-wiki-quarto-text/` for F1 and 051 for F2; 049 belongs to held
agent-parity. Only new feature records/context pointers moved; earlier receipts
remain immutable, and no model/proposal call or worker restart was repeated.

2026-10-04 recovery: runtime `f66a04d3-3aa4-4d6a-82a5-d0b4c7be2dac` retains
the original parent Task/Dispatch and child Run. Released scopes were not
repeated; active text and security review owners continue. Disposable /tmp plans
were reconstructed only from persistent receipts; required progress was retained.

2026-10-04 freeze preparation: final request owner reported a stable API and
retained 143-test/locked-environment exit-0 evidence; all 11 scoped hashes match
current source. Final CLI docs `task_f3c152d186b7` / `ctx_334d6c40721c` settled
and released (+89/-20; scoped document/whitespace checks). Full verify and
independent review remain pending; no passing whole-feature claim is made.

Concrete preview `ctx_a9e61da859c2` settled/released: 176 pages, four sidefiles,
113 JSONL files and 4,671 unchanged full-file mapping spans are proposed. No
inline canonical citations exist; current exact-sentence evidence is unresolved,
and every prior checker/status is preserved. Work/chat/default needs a granted
45-60 minute writer window; code needs a separate 15-30 minute window after
main resolves its 11 staged overlaps. This was the preview-time condition;
the later grants and current owners are recorded below.

Develop `msg_a5a4181734d8` assigned the two-file adapter prerequisite commit
within F1, not another feature. Constitution remains its separate feat/MINOR
commit at 2.7.0 with no repeat bump. In-flight net production measured 971 lines
including 274 citation-adapter lines; frozen totals will replace the estimate.
Client cleanup used the supported ownership route; project config now equals
HEAD and the global Codex config hash is unchanged.

2026-10-04 full verification attempt 01: granted frozen 5f4869b4 source ran once
and failed exit 1, Turbo 3KDZIMg2DsVOtYE7KskWzZSWXKl (4 successful, 1 failed,
39 attempted), with no source drift. The new dependency's examples package
shadowed the local browser-agent namespace. Develop granted one marker file in
msg_c52777d98dcc; native luna/medium (.86/.82; five-minute estimate .81/.76)
ctx_4a7af59816b1 settled/released, four regressions and all 51 package tests
passed. Actual turn_context tuple was independently matched by develop in
msg_428202cad151. Isolated Clean Code passed 35; no unrelated repair was made.

Document judgments remain unticked: original 24-claim request and smaller
four-claim recovery both failed with max_tokens_exceeded and identical 164,763
evidence characters. Both attempts and original full diff/358 unit IDs remain
immutable. Read-only scoping ctx_2629b44b1608, sol/high (.48/.37; 45-minute
estimate .36/.24), prepares exact relevant evidence and sizes before another
paid submission; no cap, truncation or new framework. Audit has 21 constitution
placement warnings, retained without moving approved rules or a repeat bump.


2026-10-04 readiness: full attempt 02 passed exit 0 in 313.66 seconds on frozen
source `bf359c98bb738777a8715bdd28bc805250537b7856de019a2bcaab2df290e364`,
with no source drift. Same Turbo run `3KDf2R6Q8hgw42qpD9mWAJg4FlT` reports
47 successful/47 attempted/0 failed/0 cached; workflow is VERIFIED. Outputs
include 424 Wiki, 129 doc-regions, 51 browser and 18 grammar tests passing.
Exact start, log, exit, same-run summary and frozen manifest are retained in
planning state `full-verify-attempt-02/` and `frozen-source-attempt-02.json`.
This grants readiness for existing-vault migration, not final integration.
Develop currently owns the machine-wide slot for another feature; F1 needs
another grant for its combined final snapshot. Adapter `8877ca3`, constitution
`3a7bb54` and metadata foundation `5ca2892` are scoped local feature commits.

2026-10-04 authorized writer window: main `msg_123b2e76cc5c` through develop
`msg_ce6e4b9df6ba` grants only work/chat/default writes 07:01-08:01 UTC,
with a hard end and no inferred extension. T015-T018 native own-account worker
`task_02ce62b380bc` / `ctx_93552312dec8` runs gpt-6.1-sol/xhigh (Jev .58/.48,
15-minute checkpoint .73/.67). Actual local turn_context independently confirms
that tuple/cwd, beyond startup metadata. Fresh full raw/cache/Git/body baselines
precede the exact reviewed final proposals; preservation/readback and only own
local commits follow. Authoritative private attempt receipts are in that Dispatch
state directory; no code-vault write, new conversion or original-review claim.
Code's staged cleanup separately has review/local-commit authority in develop
`msg_4df9836030b8`; historical implementer evidence is requested before choosing
a fresh different-provider reviewer. Its qmd migration still needs a separate
exclusive window after the three-vault window ends.

2026-10-04 document evidence scoping settled/released: `ctx_2629b44b1608`
preserves all 358 original units, IDs, text, order and flags plus both refusals and
full original diffs. Its 13,236 artifact assertions pass; these are not semantic
verdicts. Final `plan-attempt-05` has 215 entries, covering 47 scoped candidate,
193 partial and 118 unscoped units. Largest indivisible serialized argument is
246,579 characters/bytes, above both refused argument sizes. All submissions
remain held; no paid retry or framework was added. Owner: develop/coordinator;
next action: inspect exact per-unit selections and settle unresolved support and
compound-request handling before any paid submission. Current record edits are
REVIEW under workflow; Markdown code graph is unsupported, so scoped document
and diff checks apply. Final task ticks remain develop-owned.


2026-10-04 scoped source commits after diff/hash review: retained text
`196aebc` (T008/T009/T012), raw/grammar consumers `f486a45` (T005/T006),
exact requests/search `9e644bb` (T010/T011/T013), namespace repair `6fc65f6`
(T020), current roles/procedures `383b960` (T007/T014). Normal hooks passed;
all scoped source/test/dependency/doc bytes match the passing full snapshot.
This source-commit checkpoint preceded develop's later secrets-refresh
integration; the synchronized revision is recorded below.

Document scope is now explicitly approved in develop `msg_7210360cb8e2`, main
`msg_6f82e84fd076`: use exact old/new hunks and affected contracts, retaining all
358 objects and four classifications plus explicit unjudged dispositions; never
infer unchanged from `added=false`. Fresh read-only worker `task_8d25d1a44c8f` /
`ctx_ba6062874f70`, sol/xhigh (.48/.39; 30-minute checkpoint .34/.21), prepares
that delta and measured arguments without paid submissions. Earlier refused and
expanded plans remain immutable; no body cap, truncation or framework is added.

Historical author evidence in develop answer `msg_c8ec2cc34323`, main
`msg_6628e7ab8e71`, identifies Codex as the staged code-vault writer. Its exact
patch equals the retained historical patch; fresh stage/work/index baseline is
`code-cleanup-baseline-attempt-01/` in planning state. Fresh non-Codex read-only
reviewer `task_cf1b828ce9c9` / `ctx_e9760ec8a685` runs native Claude
`claude-sonnet-5-5`/high (.41/.30; 30-minute checkpoint .60/.52), receiving only
scope and requirements. Actual assistant model is independently matched; effort
requested/effective high is separate evidence. No cleanup commit or code-qmd
writer window is inferred. Final repository review choice is Sonnet/high
(.35/.22; 60-minute checkpoint .71/.66), pending frozen source dispatch.

Three-vault migration now has exact140-page/four-text readback and full
raw/cache/grammar/code-index preservation. Actual raw771/771 and grammar109
profiles/four mappings pass, as do chat/default lint. Work retains six proven
pre-existing lint failures and115 pre-existing orphans, reproduced from before
bytes with zero new findings. The Vale cwd route uses existing repository mise
exec and3.23.0 without source/settings changes. Concrete one-append logs and
exact reviewed patches are retained; local vault commits await develop's explicit
disposition. Work lint and sentence-semantic acceptance remain unticked, not
reported as passing. Required next action and owner stay visible after migration.


2026-10-04 completed three-vault milestone: `ctx_93552312dec8` settled/released
with local work `abd651f`, chat `b18efc6`, default `4b8f935`; exact commit/tree
and sealed receipts are in its `report.md` and `local-commits.json`. All140 pages,
four text bodies,109 effective profiles,113 JSONL/41,628 rows and4,671 spans
preserve their agreed bytes/status. Full raw/cache/grammar/code-tree/index
preservation passes. One approved append preserves each full log prefix. Main
`msg_702ece67919e` approved keeping six pre-existing work failures and115 orphan
notices; explicit extension `msg_e2be545956fc` ended08:31UTC. No writes crossed
the original cutoff while approval/extension were pending. No push/new conversion.

- [ ] T025 Resolve the six pre-existing work lint failures and115 orphan notices
  only in a separately authorized maintenance scope. Owner: develop/main;
  next action: decide the old date/link/source maintenance scope. Current F1
  preserves bodies and records exact pre-migration reproduction; it does not
  authorize repairs or claim clean work lint, semantic or original review.

Code cleanup independently approved by native Sonnet/high `ctx_e9760ec8a685`:
actual assistant model/effort/perTurnEffort all matched. Local cleanup commit
`d54279e`, tree `2d3b527`, contains only the exact11 staged paths, with all38
working files unchanged; raw39/39 and fixed-base Markdown check pass. Historical
26-unverifiable log count matches its original33-unit receipt; current25 is a
later snapshot, so no log rewrite or paid rerun occurred. Authority and exact
review/patch/hash receipts are `code-cleanup-local-commit.json` in planning state.

Main `msg_8e6757ef6887`, develop `msg_7a1680ffcff7`, grants code-only migration
08:34-09:04UTC. Fresh native `task_8a71652e23a7` / `ctx_51191dc34d50` is
sol/medium (.81/.77; five-minute checkpoint .70/.65). It uses independently
identified frozen648 tooling/templates (898 regular files, archived hash and
module-origin proof), fresh code39-raw/cache/Git baselines and exact36 proposals;
public source repair code is not read mid-edit. Current-source read-only checks
follow after repairs settle. No code-qmd commit is yet claimed by this record.

Develop447f3f70 synchronized cleanly as `648f87f`, tree `105f33c`; same F1
implementation bytes remain, incoming secrets-refresh bytes are retained.
Fresh source reviewer `task_55d21f8871e0` / `ctx_17b1e7517e30`, actual Sonnet/high
(.35/.22;60-minute checkpoint .71/.66), settled/released with REQUEST CHANGES:
four mandatory source/spec-fit findings, seven advisory lows. Focused tests pass;
review is not approval. Its complete report and combined-snapshot applicability
are retained. Unstarted full attempt03 grant was superseded; no full run launched.

Source remediation `task_651da6dfa79e` / `ctx_0f9e169f96b0`, actual sol/high
(.51/.41;60-minute checkpoint .59/.50), owns the17-file exact scope at base648.
It resolves unused whole-vault bibliography work, executable-cell/shortcode and
legacy.md checks, and restores the existing pdftotext-raw behavior through retained
text. Prior specs028/044 measurements are reused; only a meaningful synthetic
column-order regression is needed. Small source-boundary/import/temp-ignore
corrections are included. No raw/private/paid operation or substantial fallback.

Advisory dispositions: no new per-citation cache, convert-receipt redesign or
shared link-copy optimization is added in this scope; correctness and explicit
conversion/locator failures stay intact. Revisit performance with the authorized
selected-source pilot before introducing more machinery. Standalone installed
schemas/skills retain essential invariant descriptions; no new documentation
framework or pointer feature. Contract keyword-only signature is corrected here.
Existing real-vault temporary-file ignore policy is a future conversion prerequisite,
not permission to write outside the completed migration windows.

Changed-contract evidence `ctx_ba6062874f70` settled/released: original358
objects/flags/order,409 exact spans and full evidence retained;22,331 artifact
assertions pass. Final delta-attempt07 has47 held arguments (31 source behavior,
15 policy agreement, original four-item classification), covering46 spans in21
units,14 added=false. Maximum107,265 default-serializer characters/bytes;
provider acceptance remains unknown. All363 unproposed spans have explicit
unjudged dispositions. Source repairs require exact changed-support rebinding
before any submission; no old successful result is repeated or evidence truncated.
Future container/terminology/pointer changes are separately scheduled after F1;
current paths, schema and historical receipts stay unchanged.


2026-10-04 all existing pages migrated: code `ctx_51191dc34d50` settled with
local `a6b4506`, tree `5b8c47b`, at08:59:32UTC before09:04 hard end. All36
pages/one schema/one catalog/33 effective maps and one whole-prefix log append
read back exactly;39 raw revisions/195 payload-tag files and865 conversion-cache
files preserve bytes/modes/stat fields. Code Git is clean and pinned offline check
has zero problems/orphans/stale. Combined corpus is now176 qmd pages and four
retained text files; no source/private content, new conversion or semantic review
was fabricated. Authoritative `ctx_51191dc34d50/report.md`, local-commit and sealed
receipts retain the exact operation; repaired-source read-only acceptance remains.

Mandatory source corrections settled/released and entered `05464bc` after own
scoped diff/hash review, normal hooks and task trailers. All17 hashes match the
worker's verified snapshot. Meaningful old-source regressions fail and450 Wiki,
18 grammar and45 raw-import tests pass, plus lint/import/document checks.
Source +158/-62 net96, tests +280/-2, docs +39/-4. New PDF extraction reuses the
already adopted pdftotext-raw path/version and preserves synthetic stream order;
no large/private batch or new converter dependency. Untouched records/template
paths remain as currently approved; future container/pointer changes are separate.
The renewed review choice is fresh Sonnet/high (.68/.62;45-minute checkpoint
.45/.34); actual new session proof and disposition are still required before
final combined verification/integration. No final self-approval is given.
