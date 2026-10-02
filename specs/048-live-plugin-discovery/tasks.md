# Tasks: Live Plugin Discovery

**Issue**: CHE-82 | **Branch**: `feature/live-plugin-discovery`
**Inputs**: [spec.md](spec.md), [plan.md](plan.md)

Planning is recorded and completes no implementation task. All ticks belong
to develop after integration. The feature coordinator records worker outcomes
and remaining work under the tasks, without ticking them.

- [ ] T001 [P] [US1,US2,US3] Extend `scripts/plugin-clients.ts` and necessary
  project setup/configuration for live discovery and existing local MCP servers,
  with focused regression checks in `scripts/plugin-skills-test.ts`.
  Worker selection: Jev `typesafe/jev-1.13` on OpenRouter chose Codex
  `gpt-6.1-sol` high, probability 0.55, confidence 0.49, 1,200-second budget;
  difficulty difficult (estimate). Native observed launch: Task `task_5db7c0d50cca`, Dispatch
  `ctx_4297b1adf9e8`, handle `structworker_31ebc410-14a3-4505-bc83-ea743e41ad80`;
  requested/effective model and effort match.
  2026-10-02: generator, setup and focused regressions delivered; five plugin
  tests, typecheck, scoped lint, formatting and schema/preparation checks passed.
  Generated tracked Codex block was removed after metadata probes; MCP requires
  preparation again. Worker settled successfully and was released.
  2026-10-02 pause: implementation is staged and its worker released; resume
  integrated validation, with Codex MCP requiring preparation after cleanup.
- [ ] T002 [P] [US1] Rename canonical Backfire skill directories/frontmatter to
  `plugins/code/skills/backfire-code` and
  `plugins/work/skills/backfire-education`; update active plugin references and
  `licenses/third-party-notices.md`, preserving bodies and privacy boundaries.
  Worker: Codex `gpt-6.1-sol` medium, Jev OpenRouter `typesafe/jev-1.13`
  probability 0.55, confidence 0.49, estimated difficulty medium, 1,200-second
  budget; native observed Task `task_21aecc92a419`, Dispatch `ctx_ca1a1eb0a7bf`,
  handle `structworker_c859c968-aa0f-4c12-a9e6-6914d9f5457e`.
  2026-10-02: renamed skills and assigned active references; both metadata
  validations passed, 18 relative links resolved and shared reference/license
  bytes match. Worker settled successfully and was released; integrated
  verification and native acceptance remain pending.
  2026-10-02 pause: renamed sources and reference checks are staged; resume
  integrated verification and independent review, keeping the task unticked.
- [ ] T003 [P] [US3] Update `README.md`, `docs/architecture.md` and existing
  generated references for local setup, reload behavior and separate copied
  distribution, with supported-platform limits and no publication automation.
  Worker: Codex `gpt-6.1-sol` medium, Jev OpenRouter `typesafe/jev-1.13`
  probability 0.71, confidence 0.67, estimated difficulty medium, 1,200-second
  budget; native observed Task `task_cec8f006efda`, Dispatch `ctx_fb52995d15dd`,
  handle `structworker_8d60d9e9-b89f-4d56-a801-83751f841c16`.
  2026-10-02: docs and generated command reference delivered; workflow and
  document-region checks passed. Seventeen Jev calls returned sixteen retained
  results; flagged units have source-based dispositions, and audit warnings
  remain report-only. Worker settled successfully and was released.
  2026-10-02 pause: docs, source dispositions and judgment artifacts are kept
  under `.local/che-82`; resume integrated verification and review.
- [ ] T004 [US1,US2,US3] Independently inspect fresh native Codex/Claude skill
  discovery, canonical paths/source visibility and metadata-only MCP discovery;
  record evidence and limitations in an ignored `.local/` report.
  Worker: Codex `gpt-6.1-sol` high, Jev OpenRouter `typesafe/jev-1.13`
  probability 0.38, confidence 0.31, estimated difficulty difficult, 1,200-second
  budget; native observed Task `task_6ac40a76fd4b`, Dispatch `ctx_1c47cd19adc2`,
  handle `structworker_ada85e9a-faa9-422a-8791-18067ede89e8`. No private data calls.
  2026-10-02: isolated native MCP metadata and source edit readback passed;
  normal Codex and Claude invocations report both canonical skill sources with
  existing copies enabled and no tool executions. Full native input is not
  exported; final evidence and limits are in the ignored acceptance report.
  2026-10-02 pause: native invocation evidence is preserved in the acceptance
  artifacts; stop further turns and review its final report after reboot.
  2026-10-02 resume: both clients' eight saved native reads still match current
  canonical files byte-for-byte; retained acceptance is reused without fresh
  subscription turns. The positively stopped predecessor was released.
- [ ] T005 [US1,US2,US3] Integrate workers, run focused checks, document-region
  judgments and the serialized same-run full `npm run verify`; inspect final diff
  and commit with the covered task trailers.
  Coordinator owns the single integration/commit writer and verify scheduling.
  Batch worker: Codex `gpt-6-luna` high, Jev OpenRouter `typesafe/jev-1.13`
  probability 0.57, confidence 0.51, estimated difficulty easy, 1,200-second
  budget; native observed Task `task_9dad8c53514d`, Dispatch `ctx_7b34d89c6931`,
  handle `structworker_e700888a-b407-4560-9fe8-f4c735e63a55`. Matching requested
  and effective launch is recorded; it waits for the frozen snapshot.
  2026-10-02 pause: full verify never started and its reserved slot is released;
  resume with a fresh frozen snapshot and grant, then review and commit.
  2026-10-02 resume: existing Task `task_9dad8c53514d` is retried as Dispatch
  `ctx_e5dd36eaf54f`, native requested/effective Codex `gpt-6-luna` high.
  It waits for a new frozen-snapshot instruction and fresh develop slot grant;
  authoritative logs and report use task state `che-82/verification/`.
  Before freeze, real-checkout preparation passed both schema validations,
  imported legacy ownership byte-for-byte into the hashed operation state,
  and generated all three server modes with denials preserved. Its absolute
  Codex delta was retained in task state and removed exactly back to HEAD;
  clean source requires preparation again before Codex MCP use.
- [ ] T006 [US1,US2,US3] Obtain fresh cross-provider final review, resolve findings,
  record its exact reviewed commit and request develop's integration slot.
  Develop owns merge, final ledger ticks and Linear completion.
  Retained related loader review choice: Jev OpenRouter `typesafe/jev-1.13`
  selected Claude Code Sonnet high, 600 seconds (probability 0.71, confidence
  0.63), full native ID `claude-sonnet-5-5`. This review shares the existing
  generator/packaging/mode boundaries; current account usage and actual
  assistant model metadata must be rechecked before accepting it.
  2026-10-02: staged size reached the split-review threshold; the integration
  plan records why names, local discovery and setup remain one feature.
  2026-10-02 pause: independent final review, commit and integration have not
  run; retain this feature and request fresh review/integration after verification.
  2026-10-02 resume: review Task `task_f36c40f42a91` is prepared for a fresh
  Claude Code Sonnet high reviewer after the verified feature commit, reusing
  the applicable retained Jev selection. Current Claude session/weekly usage
  is 4%/62%; exact assistant model and reviewed source must still be verified.
  Review includes the immutable main-owned shared storage-policy packet.

- [ ] T007 [US1,US2,US3] Apply the approved storage amendment to discovery
  ownership receipts and reproducible distribution, with durability, XDG,
  isolation and legacy-import regressions; refresh the affected operator docs.
  2026-10-02 resume: authoritative artifacts and ownership plan are under
  `~/.local/state/verbose-broccoli/workspaces/feature-live-plugin-discovery/che-82/`;
  `retained-before-storage/` preserves 894 files with SHA-256 readback.
  Source continuation: Task `task_c77216657f2e`, Dispatch `ctx_36c10d4ab587`,
  native handle `structworker_929edb97-23e3-4227-af7d-17c783c91cdc`; requested
  and effective Codex `gpt-6.1-sol` high match. Reuses T001's retained Jev
  decision for the same generator, ownership/conflict and packaging boundaries.
  Docs continuation: Task `task_6bb3491c2359`, Dispatch `ctx_d35288ae05b9`,
  native handle `structworker_7bd68f34-9763-4b59-a6be-dc382621a60f`; requested
  and effective Codex `gpt-6.1-sol` medium match. Reuses T003's retained Jev
  decision for the same operator document boundaries. Live catalog supports
  both efforts; current Codex weekly use is 90%, resetting 2026-10-03T17:28:48Z.
  No quota guard or reset credit is used. Existing setup, implementations,
  native subscription probes and retained paid judgments are not repeated.
  First storage source/doc continuations succeeded and were released. Source
  amendment measured +64/-15 implementation lines; seven tests, typecheck,
  lint and policy passed, and the pre-amendment generator failed five checks.
  Docs judged only five changed units in three Jev calls; the advisory gate
  escalation was dispositioned against source/diff/check evidence as delivery,
  with independent final approval still pending.
  Develop added stable producer names and same-basename path isolation.
  Follow-up source Task `task_8e6f082d7fc2`, Dispatch `ctx_f3a5bbca14f7`, is
  native Codex `gpt-6.1-sol` high with matching requested/effective launch.
  Follow-up docs Task `task_d82109a879e9`, Dispatch `ctx_a56a8a984bf8`, is
  native Codex `gpt-6.1-sol` medium with matching requested/effective launch.
  Durable reports remain in task state; these follow-ups must complete before
  the canonical snapshot freezes for full verification and final review.
  Both identity follow-ups delivered checked source/docs. Final storage
  amendment: +66/-15 implementation lines; eight focused tests passed, with
  the same-basename regression failing against the incoming generator.
  Six bounded Jev calls cover the two documentation continuations; unchanged
  judgments are reused by text hash. Advisory gates remain evidence rather
  than final approval. Full verification and cross-provider review are next.

- [ ] T008 [US1,US2,US3] Resolve the first independent review's actionable
  portability, committed-discovery, interrupted-generation and denial-check
  findings; correct affected operator documentation, then verify and review again.
  Initial implementation `e35248f9e819b497bc6019763227d7a9cb8306ee` has verified
  tree `7e2f10b4c918193423c243b9c8d601746cd2f522`; full run
  `3K8GWaOX8zZMsnRwqqFFI0ckaOx` passed 47/47 tasks, zero failures and cache hits.
  Review was bound to that commit and main's immutable policy packet by native
  Claude Code Sonnet high; actual assistant metadata confirms
  `claude-sonnet-5-5`. Its empty-tip finding was resolved by binding; two Medium
  and four Low items remain actionable. The reviewer and verifier are released.
  Exact ownership now includes `.config/lefthook.yml`,
  `scripts/commit-msg-test.ts` and `docs/backfire.md`; reuse the existing hook
  and Node filesystem support. Estimate 25–60 added implementation lines plus
  focused regressions. No source change is accepted as finally reviewed until
  renewed affected checks, a new full-run slot and fresh cross-provider review.
  Source Task `task_43e5dd167b4b`, Dispatch `ctx_36fb05984222`, is native
  Codex `gpt-6.1-sol` high; docs Task `task_b3c196ecc3b4`, Dispatch
  `ctx_d44dd0f97a36`, is native Codex `gpt-6.1-sol` medium. Requested/effective
  launch matches the retained applicable generator/docs Jev decisions.
  Authoritative evidence uses task state `che-82/review-fixes/{source,docs}/`.
  Both fix workers delivered and were released. Source +53/-9 implementation
  lines includes the existing hook; 11 plugin tests and the commit-hook suite
  passed, with eight interruption/readback cases and failing incoming regressions.
  Docs changed five units in three retained Jev calls; source dispositions
  resolve consequential uncertainty without final approval. Freeze the combined
  snapshot, run a fresh serialized full verification and obtain a fresh review.
