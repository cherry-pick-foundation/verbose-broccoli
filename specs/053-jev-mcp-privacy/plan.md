# Implementation Plan: Jev MCP Privacy Proxy

**Branch**: `feature/jev-mcp-privacy` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)
**Input**: Approved CHE-86 design and D1-D11; [research evidence](research.md#evidence-register).

Assumption: this record describes built HEAD 28e4ff0; D7's shared package is confirmed by the layout evidence below; Root's 2026-10-04 decisions supersede earlier D6/D9 proposals. The staged plan and committed built outcome below do not constitute final implementation acceptance. EduOK ten digits and reuse-existing-controls bounds are settled; the Ultrafast text-generation boundary remains pending in spec.md.

## Summary

Replace the owned judgment server with installed @jkudish/jev-mcp behind one FastMCP stdio proxy. Minimal middleware owns registered matching, fresh stand-ins and every-field restoration. Upstream owns protocol, schemas and OpenRouter transport. Preserve education judgments and safely migrate callers before deletion.

## Technical Context

| Item             | Planned choice / evidence                                                                                                                                                                                                                                                        |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Language/runtime | Existing Python >=3.14 and Node >=24.12 repository runtimes; upstream needs Python >=3.10 / Node >=22 (uv.lock:3; package.json:6-8; W1/W2)                                                                                                                                       |
| Dependencies     | @jkudish/jev-mcp 0.13.0 reviewed npm closure; FastMCP 4.0.10; Faker 40.40.0; existing phonenumbers 9.0.40; mcp/mcp-types 2.2.0 retained after PyModel removal; no romanizer                                                                                                               |
| Storage          | One external protected registered list; transient call maps; no relational store or per-call persistence                                                                                                                                                                         |
| Testing          | Existing pytest and Node tests; synthetic stdio/actual upstream fixture; no model/network judgment                                                                                                                                                                               |
| Platform/type    | Linux workstation, independently selected Code/Work plugins, one reusable MCP implementation package                                                                                                                                                                             |
| Bounds           | Reuse upstream schema/lib.js limits, streamed 1,000,000-byte response ceiling, deadline/retries, explicit FastMCP client timeout and SDK handling; keep list/collision/depth guards and zero per-call writes; record RSS/CPU; missing controls are handoff notes (data-model.md) |
| Scope            | New package/skills/spec in Phase A; synchronized shared integration/caller patches and deletions in Phase B                                                                                                                                                                      |
| Lock decision    | Keep mcp/mcp-types 2.2.0 after PyModel removal; repeat runtime fixtures; 2.3.0 prototype is not acceptance                                                                                                                                                                       |

## Constitution Check

Rechecked against current constitution 2.6.0 without amendments. Principle I: install dependencies through reviewed pinned closures and author runtimes. III/VI: no raw/private records in Git; search normalization is not identity; registered list stays XDG config. V: synthetic positive/negative/boundary checks inspect actual output, failure recovery and file readback. VII: reuse upstream before local glue, positive storage limits for admission, no speculative services. IX: exactly three plugins, executable reusable package under packages/<name>/src/, actual Code/Work consumers. Full verify and independent review remain pending acceptance gates, not claimed passes (.specify/memory/constitution.md:23-50,87-150,161-204).

D7 is confirmed by constitution IX:126-140 and docs/architecture.md:499-508. `packages/education-privacy-gate/src/education_privacy_gate/` contains shared implementation; `jev-mcp` is its executable. This is not a fourth plugin or a repository-wide mandatory hub. Code and Work need the same privacy-protected judgment capability. Keep one package and lifecycle; separate proxy/gate packages add no current consumer need. No constitution bump; CHE-84's amendment stays owned by CHE-84.

## Reuse before implementing

| Need                       | Existing/upstream implementation                                      | Minimum local responsibility                                                  |
| -------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| MCP server/Jev carrier     | @jkudish/jev-mcp 0.13.0, dist/index.js:9-19, provider.js:261-305      | Launch pinned child with chosen env                                           |
| Proxy/middleware/lifecycle | FastMCP 4.0.10 create_proxy, Client, StdioTransport, Middleware       | One wiring entry and tools-only policy                                        |
| People                     | Faker default-English first_name()                                    | One first name/person/call, collision checks and anchored/default restoration |
| Latin aliases              | Registered real Latin spellings and existing roster variant semantics | Same single English first name; mixed forms use anchored/default restoration  |
| Phone spans                | Existing phonenumbers 9.0.40                                          | Combine with e-mail/EduOK/resident patterns                                   |
| Registry/file safety       | Python json/os/pathlib and existing protected-file patterns           | One strict bounded reader/admission contract                                  |
| Discovery                  | scripts/plugin-clients.ts with ownership receipts                     | Equal-declaration handling and agreed equal-skill handling                    |
| Consumer judgments         | Existing upstream verify/classify/noul/find schemas                   | Repoint commands and parse actual results                                     |
| Transport retries/errors   | Upstream provider.js:94-193 and FastMCP client timeout                | Generic outward failures; no second retry engine                              |

Source evidence: W1:59-181; W2 API/romanization/phone sections; W3:24-82. Missing substantial capability is escalated with upstream options; no custom gateway or transliteration framework.

## Source layout and owned-code estimate

Measured at committed HEAD 28e4ff0 on 2026-10-05: the gate package has 820 owned production Python lines: `__init__.py` 1, `__main__.py` 272, `roster.py` 241 and `masking.py` 306. Tests/fixtures total 1,905 lines: registry 223, masking 451, proxy 598, upstream tools 476, fixture_server.py 113 and fixture-upstream.mjs 44 (`wc -l packages/education-privacy-gate/src/education_privacy_gate/*.py packages/education-privacy-gate/tests/*`). Unchanged installed upstream code is excluded. Caller/discovery glue is separate from this package count.

The initial 300-400-line estimate was an estimate, not a cap; it is superseded by these measurements. Compare the built 820 production lines and 1,905 test/fixture lines with W3's old 2,154 Python lines plus 1,054 region-data lines and 4,597 test lines. Manifests, locks and documentation are measured separately below.

W3 measured removals at HEAD 447f3f7: core Python 895, education Python 1,259, total 2,154; regions.json 1,054; tests 4,597; complete package text 7,886 plus 413,346-byte vendored ZIP. Noul port is 204 maintained lines. Other removals: docs/backfire.md 462; region script/test 103/38; code skill 257 text lines; work skill 325. W3:7-22,132-233 and backfire-files.json contain source-file counts/hashes. These are gross removal candidates; adapted matching/tests reduce net deletion. No deletion is yet authorized by a line count.

## Two phases and ownership

Phase A source is committed (3ad4ae0, 40e2645, 76fc1a8) and inspected by the coordinator. Phase B section holds were released at develop b7f3223 on 2026-10-05; integration and deletion are committed through 28e4ff0. The following staged boundaries remain ownership history, not current blockers.

Phase A: new package source/tests/manifests, two new upstream `jev` skill copies and this record only. Do not sync the root wildcard workspace or activate another server while held. The dependencies must be independently reviewed before installation/execution. New source may be tested against an isolated scratch environment, not by editing held locks.

Phase B: Root releases the named CHE-84 files after its develop merge and branch synchronization. Re-read every shared file and patch only CHE-86 judgment/provider/privacy sections. CHE-12 retains wiki-build-publish and site-specific template/example/architecture storage paragraphs. Main owns real-list population under separate authorization; effective registration/provider-path activation waits for the first official release and its fresh whole-repository review. Exact owners, holds, commands and file scopes are in [tasks.md](tasks.md).

## Phase 0 and Phase 1 outputs

Phase 0 outputs: W1-W4 evidence summarized in research.md; adoption conditions, dependency comparison and policy corrections are preserved. No repeated research or paid probe is needed to answer already-settled questions.

Phase 1 outputs: spec.md, checklist, data-model.md, four contracts, quickstart.md and this plan. tasks.md is the execution ledger. The documentation worker performs a read-only coverage/hold/link/placeholder consistency analysis; Root/develop owns quality approval and task ticks. Implementation remains unchecked.

## Risks and release gates

EduOK ten-digit detection and reuse-existing-controls bounds are settled; the Ultrafast text-generation helper remains held alongside the operational and acceptance items below in spec.md. Default-English Faker, one first name per person and mixed-form anchored/default restoration are settled; no particle matching or shortened variants. Faker only and byte-identical portable `jev` copies/resources with one deterministic local link are settled. Preserve both owners and independent disable behavior, reject divergence; shared discovery/docs integration was released for CHE-86 sections at develop b7f3223 on 2026-10-05. Wiki domain ownership and review/gate field removal are implemented in 3c5279c after the CHE-84 handoff; final acceptance remains pending. The committed [independent dependency review](security/dependency-review.md) is historical evidence; no romanizer is adopted. Acceptance implements its conditions in privacy-gate.md and T006/T007, including the actual transport-inherited six environment variables plus three Jev variables, neutral cwd, controlled stderr, disabled FastMCP side effects, tools-only blocking and every-exit map cleanup. An empty registry cannot establish a useful real privacy boundary. Missing spellings and context remain disclosure risks. Upstream sanitization and model spelling changes may prevent restoration. Finite English first-name pools can exhaust or repeat. Missing real Korean names can stand out among English fakes, an accepted trade-off; unanchored results use registered romanized spelling or Hangul fallback. FastMCP decoded-result limits do not bound raw stdio allocation. Unbounded verify/screen/classification inputs, pre-parse allocation and concurrency controls are upstream or main-owned service-scope handoff notes, not gate work; RSS/CPU are measured and recorded without gate thresholds. W2's execution-before-security sequence is not adoption approval. Python mcp/mcp-types remain 2.2.0 after jev-judge-mcp (PyModel) removal; the 2.3.0 prototype is not integration acceptance.

Credit-offers and Ultrafast browser choices now use the gated proxy (ec5f7f9, aa6c319, 9e80a5d), and deletion is committed in 28e4ff0; the text-generation helper stays held, with no ungated student-data route. Acceptance awaits chat-owner routing evidence, not a documented bypass limit. Root accepts only actual controlled caller/proxy evidence, a frozen full verification summary and other-provider review; this record does not approve its own change.

## Split review decision

Measured committed snapshot: HEAD 28e4ff0 against merge base b7f3223 with develop, before this documentation sync. `git diff --shortstat $(git merge-base HEAD develop) HEAD` reports 147 files changed, 8,255 insertions and 10,288 deletions. Excluding specs, locks and package-lock files reports 132 files changed, 6,594 insertions and 10,091 deletions:

```sh
git diff --shortstat $(git merge-base HEAD develop) HEAD -- . \
  ':(exclude)specs/**' ':(exclude)*.lock' ':(exclude)**/*.lock' \
  ':(exclude)package-lock.json' ':(exclude)**/package-lock.json'
```

`git diff --diff-filter=D --name-only $(git merge-base HEAD develop) HEAD` lists 41 deleted paths; `--numstat` counts 8,374 deleted text lines in those paths, excluding binary content. Counting each whole-file deletion as about one line gives 10,210 changed lines (8,255 additions + 1,914 deletions in surviving files + 41 deleted paths). The 1,000-line split-review threshold is reached; the numbers are measurements, not a cap.

Coordinator assessment: this is one cohesive replacement. The old route and its callers must change together, with no registered bypass between them. The only separable pieces are docs-only (this record and the operator guide) and the new unregistered package; separating them adds merge-review rounds without reducing risk. Root/develop owns the final split decision and merge review; this worker does not approve the change.
