# Implementation Plan: Jev MCP Privacy Proxy

**Branch**: `feature/jev-mcp-privacy` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)
**Input**: Approved CHE-86 design and D1-D11; [research evidence](research.md#evidence-register).

Assumption: D7's shared package is confirmed by the layout evidence below; Root's 2026-10-04 decisions supersede earlier D6/D9 proposals. The plans below are not dependency adoption or implementation acceptance. Bounds and unresolved admission decisions remain explicit in spec.md.

## Summary

Replace the owned judgment server with installed @jkudish/jev-mcp behind one FastMCP stdio proxy. Minimal middleware owns registered matching, fresh stand-ins and every-field restoration. Upstream owns protocol, schemas and OpenRouter transport. Preserve education judgments and safely migrate callers before deletion.

## Technical Context

| Item             | Planned choice / evidence                                                                                                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Language/runtime | Existing Python >=3.14 and Node >=24.12 repository runtimes; upstream needs Python >=3.10 / Node >=22 (uv.lock:3; package.json:6-8; W1/W2)                         |
| Dependencies     | @jkudish/jev-mcp 0.13.0 reviewed npm closure; FastMCP 4.0.10; Faker 40.40.0; existing phonenumbers 9.0.40; mcp/mcp-types 2.2.0 while PyModel remains; no romanizer |
| Storage          | One external protected registered list; transient call maps; no relational store or per-call persistence                                                           |
| Testing          | Existing pytest and Node tests; synthetic stdio/actual upstream fixture; no model/network judgment                                                                 |
| Platform/type    | Linux workstation, independently selected Code/Work plugins, one reusable MCP implementation package                                                               |
| Bounds           | 256 KiB request, 2 MiB result, 1 MiB/4,096-spelling list, 60 seconds, two calls; measured RSS/CPU expectations in data-model.md                                    |
| Scope            | New package/skills/spec in Phase A; synchronized shared integration/caller patches and deletions in Phase B                                                        |
| Lock decision    | Keep mcp/mcp-types 2.2.0 while PyModel remains; repeat runtime fixtures; 2.3.0 prototype is not acceptance                                                         |

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

The initial user-visible estimate was roughly 300-400 wrapper/gate lines replacing about 2,150 Python lines plus region data (Design). W2 estimates 220-385 production lines based on a 66-line prototype, excluding tests. This per-file plan targets about 300-400 production lines; security bounds may increase it. Estimates are not caps and do not count unchanged installed upstream code.

| File                                                                   | Estimated owned production lines |
| ---------------------------------------------------------------------- | -------------------------------: |
| packages/education-privacy-gate/src/education_privacy_gate/**init**.py |                              1-5 |
| packages/education-privacy-gate/src/education_privacy_gate/**main**.py |                            65-90 |
| packages/education-privacy-gate/src/education_privacy_gate/roster.py   |                            55-75 |
| packages/education-privacy-gate/src/education_privacy_gate/masking.py  |                          160-230 |
| Total                                                                  |                          281-400 |

Package pyproject.toml, package.json/package-lock.json, the root runtime-version reference (no package .python-version) and README.md hold executable/pin/operator metadata. Tests are four focused Python files plus fixture_server.py and fixture-upstream.mjs; estimate 250-450 test/fixture lines for the full required boundary matrix, not the research prototype's limited 80-140. Prefer parameterized schema coverage over copying upstream tests. No locally owned upstream server copy or generic abstraction. A retained work-domain roster adapter may preserve up to the existing 99 source lines outside this gate estimate; caller/config glue is measured separately after handoff.

W3 measured removals at HEAD 447f3f7: core Python 895, education Python 1,259, total 2,154; regions.json 1,054; tests 4,597; complete package text 7,886 plus 413,346-byte vendored ZIP. Noul port is 204 maintained lines. Other removals: docs/backfire.md 462; region script/test 103/38; code skill 257 text lines; work skill 325. W3:7-22,132-233 and backfire-files.json contain source-file counts/hashes. These are gross removal candidates; adapted matching/tests reduce net deletion. No deletion is yet authorized by a line count.

## Two phases and ownership

Phase A: new package source/tests/manifests, two new upstream `jev` skill copies and this record only. Do not sync the root wildcard workspace or activate another server while held. The dependencies must be independently reviewed before installation/execution. New source may be tested against an isolated scratch environment, not by editing held locks.

Phase B: Root releases the named CHE-84 files after its develop merge and branch synchronization. Re-read every shared file and patch only CHE-86 judgment/provider/privacy sections. CHE-12 retains wiki-build-publish and site-specific template/example/architecture storage paragraphs. Main owns real-list population under separate authorization; effective registration/provider-path activation waits for the first official release and its fresh whole-repository review. Exact owners, holds, commands and file scopes are in [tasks.md](tasks.md).

## Phase 0 and Phase 1 outputs

Phase 0 outputs: W1-W4 evidence summarized in research.md; adoption conditions, dependency comparison and policy corrections are preserved. No repeated research or paid probe is needed to answer already-settled questions.

Phase 1 outputs: spec.md, checklist, data-model.md, four contracts, quickstart.md and this plan. tasks.md is the execution ledger. The documentation worker performs a read-only coverage/hold/link/placeholder consistency analysis; Root/develop owns quality approval and task ticks. Implementation remains unchecked.

## Risks and release gates

EduOK format/numeric handling and proposed bounds are the two open decisions in spec.md. Default-English Faker, one first name per person and mixed-form anchored/default restoration are settled; no particle matching or shortened variants. Faker only and byte-identical portable `jev` copies/resources with one deterministic local link are settled. Preserve both owners and independent disable behavior, reject divergence, and keep shared discovery/docs integration held until CHE-84 handoff. Wiki domain ownership and review/gate field removal are settled; CHE-84 agreement and caller checks still gate implementation. The committed [independent dependency review](security/dependency-review.md) is historical evidence; no romanizer is adopted. Acceptance implements its conditions in privacy-gate.md and T006/T007, including the actual transport-inherited six environment variables plus three Jev variables, neutral cwd, controlled stderr, disabled FastMCP side effects, tools-only blocking and every-exit map cleanup. An empty registry cannot establish a useful real privacy boundary. Missing spellings and context remain disclosure risks. Upstream sanitization and model spelling changes may prevent restoration. Finite English first-name pools can exhaust or repeat. Missing real Korean names can stand out among English fakes, an accepted trade-off; unanchored results use registered romanized spelling or Hangul fallback. FastMCP decoded-result limits do not bound raw stdio allocation; resource expectations must be measured. W2's execution-before-security sequence is not adoption approval. Keep Python mcp/mcp-types 2.2.0 while jev-judge-mcp (PyModel) remains; the 2.3.0 prototype is not integration acceptance.

Credit-offers imports Backfire/PyModel directly; deletion waits for a separate chat-owner repoint. Jev Ultrafast direct HTTP cannot satisfy the always-on gate. Browser-choice judgments must use this gate in a later chat-owner task; the text-generation helper stays held, with no ungated student-data route. Acceptance awaits chat-owner routing evidence, not a documented bypass limit. Root accepts only actual controlled caller/proxy evidence, a frozen full verification summary and other-provider review; this record does not approve its own change.

## Split review decision

Proposed cohesive integration: keep one proxy/gate feature, but execute new files and held integration as separate waves. Exact upstream replacement, masking and caller migration must land together to avoid a registered bypass or broken dependency. Do not split out a general gateway or optional defensive tool. Before develop merge review, measure actual diff against the merge base and count whole-file deletion as about one line for the 1,000-line rule. If threshold is reached, Root reviews whether the documentation/new-package checkpoint can be separated safely; no automated cap or approval by this worker (AGENTS.md:118-121).
