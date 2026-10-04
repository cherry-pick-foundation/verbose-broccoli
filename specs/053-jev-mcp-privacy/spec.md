# Feature Specification: Jev MCP Privacy Proxy

**Feature Branch**: `feature/jev-mcp-privacy`
**Created**: 2026-10-04
**Status**: Built through 28e4ff0; final review, frozen verification and release activation are pending.
Linear: CHE-86

Assumption: the approved design and D1-D11 apply except where the decisions recorded from Root below supersede them. Default-English Faker first-name stand-ins, mixed-form restoration, gated browser judgments and the portable skill convention are settled. EduOK ten-digit detection and reuse-existing-controls bounds are settled; the Ultrafast text-generation helper remains held alongside the operational and acceptance items below. Controls below record requirements and the built implementation, not final acceptance. Historical records stay unchanged. Source labels resolve in [research.md](research.md#evidence-register).

## User Scenarios & Testing

### User Story 1 - Judge education text through one gate (Priority: P1)

An authorized education agent submits observations, evidence and scores through the single registered `jev-mcp` server. Registered people and schools receive fresh stand-ins. The answer restores anchored original spellings or the registered Latin/Hangul fallback.

**Why this priority**: Existing semantic education judgments must remain usable within their privacy boundary (design brief; D1-D5).
**Independent Test**: A synthetic stdio upstream records all received fields and echoes them into nested results. Compare the captured request and returned result, including errors and concurrent calls.

**Acceptance Scenarios**:

1. **Given** registered synthetic person aliases and school variants, **When** any supported tool is called, **Then** upstream receives stand-ins and every returned text field restores uniquely anchored original spellings, otherwise the registered romanized spelling or Hangul fallback.
2. **Given** phone, e-mail, EduOK and resident-number patterns, **When** they occur beside grades and classes, **Then** patterns are masked while grades, classes, scores and ordinary Korean remain unchanged.
3. **Given** two simultaneous calls, **When** both complete or one fails, **Then** their maps remain separate and no pairs reach disk, logs or the other call.
4. **Given** an unregistered name or school spelling, **When** it does not match a covered pattern, **Then** it passes unchanged; the agent remains responsible for that residual disclosure risk.

### User Story 2 - Keep every supported tool within the boundary (Priority: P1)

Code and Work use the same upstream tool schemas. There is no registered bypass or opt-out switch.

**Why this priority**: Arguments, map keys and metadata can carry identifiers (W1:113-153; W2 middleware and proxy source findings).
**Independent Test**: Exercise all 12 schemas through the actual proxy, plus known resource/prompt names, malicious metadata, malformed inputs and upstream failure.

**Acceptance Scenarios**:

1. **Given** a registered spelling in a schema `pattern`-constrained slug, **When** submitted, **Then** the gate rejects before forwarding, without echoing that spelling.
2. **Given** private text in paths, regex literals or arbitrary JSON keys, **When** submitted in unconstrained strings, **Then** it is swapped and resulting schemas remain valid or the call fails closed.
3. **Given** resource, template, prompt, sampling, elicitation or roots access, **When** attempted, **Then** it is unavailable and no unmasked relay occurs.
4. **Given** timeout, child exit, mapping exhaustion, unsafe registry or restoration conflict, **When** encountered, **Then** a generic error returns and the next valid call still works.

### User Story 3 - Replace the old server without breaking callers (Priority: P2)

The maintainer installs the reviewed upstream closure, repoints callers, then removes obsolete Backfire implementation and promises.

**Why this priority**: Direct imports and launchers make deletion order observable (W3:24-58).
**Independent Test**: Run synthetic consumer fixtures and generate registrations for Code alone, Work alone, both and after disabling either plugin. Verify one judgment server and preserved unrelated configuration.

**Acceptance Scenarios**:

1. **Given** both plugins selected, **When** discovery resolves identical declarations, **Then** one `jev-mcp` registration remains after comparing complete resolved launch configurations; both plugin owners remain in cleanup receipts, and conflicting declarations are rejected before writes.
2. **Given** current Noul, classification and verification callers, **When** repointed, **Then** they parse actual upstream results and preserve source/order/resume checks.
3. **Given** credit-offers still imports Backfire, **When** deletion is proposed, **Then** deletion stays blocked until its chat owner supplies a tested repoint.
4. **Given** CHE-84's file hold, **When** Phase A runs, **Then** only new files are added; shared integration waits for handoff and synchronization.

## Requirements

### Functional Requirements

- **FR-001**: Register exactly one judgment server named `jev-mcp` for Code and Work, backed by a hidden unmodified `@jkudish/jev-mcp` 0.13.0 stdio child. Every tool call MUST pass the gate (D1, D5, D11).
- **FR-002**: Pin reviewed npm/Python closures and upstream skill provenance. Force OpenRouter and `typesafe/jev-1.13`; load its key from existing protected provider configuration with a limited child environment. No custom transport or general-model fallback (D1; W1:39-99).
- **FR-003**: Persist only a registered list of real person names and school spellings for gate matching, outside Git. Extend it on authorized admission; include supplied teacher and guardian forms without inventing source facts (design brief; W3:60-72).
- **FR-004**: Match registered full, given, Latin and school spellings with deliberate boundaries and overlap precedence. Preserve ambiguous given-name handling. Persist only registered real spellings; order, separator and case variants of a REGISTERED Latin spelling follow existing roster semantics in memory and are not new spellings. Use Faker only: no romanizer dependency, generated Latin spellings or optional romanize hook (Root 2026-10-04 supersedes D6; W3:60-66).
- **FR-005**: Draw ONE fresh per-call Faker 40.40.0 DEFAULT ENGLISH first name per real person; every registered Hangul/Latin full/given, order, separator and case form maps to that SAME first name. No shortened variants, per-form fakes, generated Latin spellings, romanizer or naming framework. Use call-local `School NN` labels. No stable mapping or seed in production (Root amendment 2026-10-04 supersedes D5-D6).
- **FR-006**: Reject/redraw collisions with all registered spellings, original request text and same-call stand-ins; enforce bounded exhaustion. Keep pairs only in call memory and release them on success, error and cancellation (design brief).
- **FR-007**: Mask recognized phone spans with phonenumbers first, then e-mail, isolated ten-digit EduOK numbers and `s-<ten digits>` page IDs, and isolated 13-digit resident numbers with an optional separator after digit six. A phone span accepted by phonenumbers stays `Phone NN`; otherwise an isolated ten-digit number is `EduOK NN`. Numeric boundaries prevent matching inside longer digit runs. Keep type labels; leave grades/classes and learning values unchanged. Do not restore obsolete broad detectors (design brief; W3:66-70).
- **FR-008**: Swap every unconstrained argument string and JSON key, including IDs, paths and regex literals. Schema `pattern` fields MUST stay unchanged or reject on registered/pattern identifiers; never silently exempt unsafe values (D4).
- **FR-009**: Restore every result string and key, including outer text JSON, nested JSON-encoded strings, plain error text, nested usage, structured content and allowed metadata. Preserve numbers, enums and error status except the ten-digit JSON integer-to-label masking described below. Mixed forms are allowed. Where an echoed field/identifier uniquely anchors an original spelling, restore that exact original; otherwise restore the person's registered romanized spelling, or the Hangul name if no romanized spelling is registered. Preserve within-call identity and test both anchored and default restoration. Do not reject mixed forms merely because their spellings share the person's first-name stand-in. Reject actual different-person reverse collisions or unsafe key collisions. Restoration covers unchanged stand-ins, not arbitrary model transformations (Root amendment 2026-10-04; D2; W1:133-153).
- **FR-010**: Expose tools only. Hide and block direct resources/templates/prompts; disable sampling/elicitation/roots relays and unsupported continuations; reject application request metadata and suppress untrusted logs/progress (D3; W2 proxy findings).
- **FR-011**: Reject unsafe registry, malformed/unsupported input, violations of reused upstream schema limits or gate-owned storage/collision/depth guards, mapping conflicts, transport/protocol exceptions and unsafe results without raw exceptions or sensitive diagnostics. Reuse upstream deadline/retry controls, explicitly set the FastMCP client timeout and mandatory-provider failure strategy; preserve service after bad input (D3; constitution V).
- **FR-012**: Reuse actual upstream per-tool schema/lib.js limits, streamed response ceiling, request deadline/retries and FastMCP/MCP SDK message handling. Keep positive registered-list storage bounds, collision-exhaustion bounds and a recursion-safety depth guard; prove zero per-call file writes. Record peak memory and CPU of a large synthetic call without gate-enforced resource thresholds. Report missing input, pre-parse allocation and concurrency controls as upstream/service-level handoff notes; do not invent body/provider limits. No persistent pair store, cache, lock, budget ledger or key/salt (design brief; constitution VII).
- **FR-013**: Repoint session selection, grammatical competence, Wiki checks and prepared-request contracts before deleting dependencies. Preserve richer Wiki domain-roster checks separately; the gate list MUST NOT acquire student facts to satisfy them (W3:28-40).
- **FR-014**: Keep upstream `jev_noul`; remove local Noul only after compatibility checks. Remove `jev_score` promises without a replacement after confirming no production caller (W3:48; upstream-comparison.json), and adopt `jev_audit` as shipped. Drop Python-only `tests_format`, `tests_sha256`, `tests_weight` and typed error-code envelope assumptions at callers; local evidence hashes and receipts remain authoritative (Root 2026-10-04; D8; W1:183-203).
- **FR-015**: Refresh consumer skills under upstream name `jev`; remove direct upstream server frontmatter. Coordinate `typesafe-ai` naming and project instructions with their owners; leave historical records unchanged (design brief; W1:155-165).
- **FR-016**: Record exact credit-offers and jev-ultrafast handoffs. Credit-offers dependency repoint blocks Backfire deletion. Browser-choice judgments MUST go through this gate; the chat-owner migration is committed in ec5f7f9, aa6c319 and 9e80a5d; the text-generation helper stays held, with no ungated student-data route. Ultrafast direct HTTP cannot satisfy the always-on gate. Implementation stays chat-owned and requires handoff and tested routing evidence (Root amendment 2026-10-04 supersedes D9).
- **FR-017**: Resolve identical complete effective launch configurations once and reject conflicts before writes, with the smallest existing-discovery change and no second running server. Retain both plugin owners for cleanup and plugin-independent loading. Byte-identical portable `jev` copies/resources in Code and Work resolve to one deterministic local link; reject divergence, preserve both ownership sources and independent selection/disable behavior. Shared discovery/docs integration was released for CHE-86 sections at develop b7f3223 on 2026-10-05; add no loading framework or direct unpinned upstream mcpServers block. Main effective registration/provider-path activation waits for the first official release (Root 2026-10-04; D11; W3:24-27).
- **FR-018**: Respect CHE-84 holds, section ownership, synthetic-only evidence, immutable completed results, workflow checks, Root-granted serialized full verification and other-provider final review. Record a split decision at 1,000 lines; develop owns final ticks (design brief; AGENTS.md:94-141).

### Key Entities

Registered list: source-backed real spellings grouped by person or school. Call map: exact matched substrings and Faker stand-ins, scoped to one call. Tool contract: upstream input schema and observed text-result paths, versioned by the package. See [data model](data-model.md) and [tool contract](contracts/upstream-tools.md).

## Success Criteria

- **SC-001**: Actual synthetic upstream captures contain zero registered spellings or covered identifier-pattern originals across all 12 tools; echoed output restores every supported text field/key using exact anchored originals or the registered romanized/Hangul fallback.
- **SC-002**: All registered forms of a person share ONE default-English Faker first name per call. Deterministically anchored fixtures restore each original spelling; unanchored fixtures use the registered romanized spelling or Hangul fallback. Mixed forms are allowed; different people never share a stand-in, collisions redraw/reject within the bound, and concurrent calls cannot cross-restore. Fresh draws are observable without claiming uniqueness across calls.
- **SC-003**: Known extra surfaces, metadata, constrained unsafe IDs, unsafe registries and failures produce generic errors with zero upstream forwarding where preflight fails; later valid calls succeed.
- **SC-004**: Boundary fixtures demonstrate the reused controls and gate-owned guards in [data-model.md](data-model.md#positive-bounds), zero per-call writes and grade/class preservation, including phone/EduOK overlap and numeric-boundary cases. Record peak resident set size (RSS) and CPU for a large synthetic call; recording is required, with no resource pass/fail threshold. Missing controls remain explicit handoff notes.
- **SC-005**: Code-only, Work-only, combined and one-plugin-disabled discovery yields one gated judgment route with correct cleanup ownership; actual caller fixtures parse upstream results; no live Backfire dependency remains before deletion.
- **SC-006**: Narrow checks, frozen-source full `npm run verify` with its same-run summary, a fresh other-provider review and split review precede integration. No planning document counts as runtime or legal acceptance.

## Edge Cases

Missing, empty, malformed, oversized or foreign-owned registry; symlink components; duplicate JSON keys; duplicate aliases with different owners; shared given names; compound surnames; composed/decomposed Korean; case and separator variants; mixed Hangul/Latin/case forms of one person sharing one first-name stand-in, with anchored exact restoration or registered romanized/Hangul fallback; different-person stand-in collisions; overlapping school/person/pattern spans; literal candidate already in a request; collisions after key replacement; finite Faker first-name pools; upstream ID sanitization; changed regex semantics; numeric identifiers; invalid pattern; large restored results and the upstream response ceiling; JSON-in-text versus plain error; unvalidated usage values; unknown tools; cancellation, timeout, startup failure and child death; requests after a refused call.

## Assumptions and residual risk

Only authorized own-account Claude Code/Codex workers may read actual private sources, with training disabled. This feature's development tests use synthetic data only (plugins/work/AGENTS.md:22-26; design brief). Main populates the real list in a separate authorized admission window. The wrapper never scans a private source tree itself.

Unknown names and school spellings pass unchanged. Preferred romanizations, nicknames, unrecognized phone-like strings and bare IDs outside the agreed patterns can pass. Faker's finite pools and `School NN` labels can repeat across calls. Context, grade/class combinations and unchanged observations can identify people. Fresh maps remove stable person mappings but do not prove unlinkability or complete concealment. A real Korean name missing from the list can stand out among English fakes; the user accepted this trade-off. Mixed-form unanchored output uses the registered romanized spelling or Hangul fallback and may differ from the input spelling. Surrounding Korean particles are not rewritten. A model that changes a stand-in's spelling may prevent restoration. The gate does not establish legal compliance (W2; W4:39-53).

Main holds released states only. Feature source finishes into develop; no develop fast-forward or ad hoc merge into main is authorized. Main effective registration and provider-path updates wait for the first official release, whose timing belongs to the user, with a fresh whole-repository review. Repository implementation acceptance is separate from external client activation; no global rewrite or preserved user-data removal follows. Ultrafast browser-choice judgments use this gate; the text-generation helper stays held with no ungated student-data route.

## Non-goals

No organization detector, pseudonym table, extra private persistence, local models, custom Jev/OpenRouter transport, provider framework, global configuration repair or private-data deletion. Credit-offers and Ultrafast browser choices were migrated by the chat owner; the text-generation helper stays held with no ungated student-data route. No new Wiki writes, conversion batch, publication, release or push. No second CHE-84 constitution amendment or CHE-12 site changes. No replacement `jev_score` (design brief; D8-D9).

## Decisions recorded from Root (2026-10-04)

Faker only (latest Root amendment): use ONE Faker 40.40.0 DEFAULT ENGLISH first name per real person per call. Every registered Hangul/Latin full/given, order, separator and case form maps to that SAME first name; no shortened variants, per-form fakes, naming framework, romanizer dependency, generated Latin spellings or optional romanize hook. Remove Korean-locale and final-consonant/particle rules. Retain the not-adopted romanizer comparison as evidence in research.md. Matching variants of a registered Latin spelling follow existing roster semantics, without adding new spellings. Redraw on collisions with registered spellings, original text/keys or other same-call stand-ins; bounded exhaustion returns fixed generic error before forwarding.

Mixed forms are allowed. Where an echoed field/identifier uniquely anchors an original spelling, restore that exact original; otherwise restore the person's registered romanized spelling, or the Hangul name if no romanized spelling is registered. Preserve within-call identity and test both anchored and default restoration. Deterministically anchored inputs/results test each original spelling alongside unanchored fallback cases. Mixed forms are not a pending question or refusal condition. A missing real Korean name can stand out among English fakes; this trade-off is accepted.

EduOK is settled: isolated ten-digit numbers and `s-<ten digits>` page IDs use `EduOK NN`; phonenumbers-accepted spans retain `Phone NN`. Nine/eleven-digit runs and ten digits embedded in longer runs are not EduOK matches. Resident numbers remain 13 digits with an optional separator after digit six. Grades/classes remain unchanged.

Bounds are settled: reuse actual tool/runtime/schema controls rather than inventing request/result/provider limits. Keep list storage, collision exhaustion, recursion safety and zero per-call writes; measure and record memory/CPU without gate thresholds. Missing schema-input, pre-parse frame/allocation and concurrency controls are handoff notes for upstream issues or a main-owned operating-system service scope, not new gate implementation. See data-model.md for the exact controls and tests.

Browser-choice judgments now go through this gate (ec5f7f9, aa6c319, 9e80a5d). The text-generation helper stays held until its student-data boundary is settled, with no ungated student-data route.

Skill convention (former question 3): byte-identical portable `jev` copies/resources in Code and Work, one deterministic local link, reject divergence, preserve both ownership sources and independent selection/disable behavior. A tracked link to another known plugin's canonical copy of the same skill is discovery-managed and may be retargeted to the selected byte-identical copy; record the old target in the pending journal. Foreign targets and links to a copy whose bytes differ still conflict; a user's own link elsewhere is never touched. No loading framework or direct unpinned upstream mcpServers block; shared discovery/docs integration was released for CHE-86 sections after the CHE-84 handoff at develop b7f3223 on 2026-10-05.

Identical Code/Work declarations are accepted only when their complete resolved launch configurations agree; one effective server retains both cleanup owners. Conflicting definitions still reject. Keep the change within existing discovery.

Wiki domain checks remain separate from the minimal private name list. The work consumer owner retains source-backed checks and obtains CHE-84 agreement before deleting old imports (former question 3). Review/gate callers drop `tests_format`, `tests_sha256`, `tests_weight` and the typed error-code envelope; local evidence hashes and receipts remain authoritative (former question 5).

Reviewed upstream schemas stay unchanged. Unsafe constrained fields reject before forwarding. Restore nested JSON strings/keys, plain errors and supported result metadata; hide and block resources/templates/prompts by list and direct call. Strip or reject unsupported relay metadata; callbacks and continuations stay disabled. Strip the upstream skill's direct unpinned server block, retain name `jev`, and remove Score promises after the production-caller check (W3:48).

The root `.python-version` is the sole pin used by the gate and the three former Backfire-pin readers, preserving 3.14.4. Other packages/tools retain their existing pins; no package pin was added to the gate. CHE-86 keeps one function returning the registry config directory. A separate future VERBOSE_BROCCOLI_HOME feature owns shared per-language path resolution; no old Backfire path migration or duplicate helper belongs here. Main activation waits for the first official release and its fresh whole-repository review.

Built details checked at 28e4ff0: a ten-digit JSON integer becomes an `EduOK NN` label string, retaining its decimal digits for text restoration. A typed numeric field then fails the unchanged upstream schema before forwarding (`masking.py:111-112`; `test_privacy_gate.py:384-413`). Other numeric learning values retain their types.

An integer `progressToken` is accepted and dropped; string tokens and every other application `_meta` key reject. SDK connection metadata and valid fixed logging levels are dropped too. The backend SDK stamps its own counter/connection metadata, containing no caller content (`__main__.py:87-117`; `test_proxy.py:435-475`). Supported upstream `isError` results are restored and preserved. Transport/protocol exceptions, unsupported content and gate failures become the fixed text `Privacy gate rejected the call.` (`__main__.py:153-166`; `test_proxy.py:479-502`).

Ordinary-text collision checking asks whether the candidate occurs in the original request text or key. Registered spellings and other stand-ins retain checks in both substring directions (`masking.py:179-201`). Native Node is resolved with `mise which node` from `/`, falling back to PATH when mise is absent (`__main__.py:194-211`). Callers explicitly pass only an absolute `XDG_CONFIG_HOME`; the MCP SDK supplies its baseline environment. Credit-offers and browser answers retain the former `validate_choice` guarantees locally (aa6c319).

Browser runs charge each operation/target gated tool-call attempt before dispatch, including failures: `MAX_STEPS * 2` gives 120 attempts, separate from the 60-action guard (9e80a5d). Under the default OpenRouter route upstream may make up to three fetch attempts per dispatched request, up to 360 explicit fetch attempts per browser run; actual processed requests and billing are unknown. `JEV_MCP_MAX_ATTEMPTS` defaults to 3 and is clamped 1-6; the proxy does not set it. The 1.7-second startup figure is mocked-run evidence only.

Deletion 28e4ff0 covers T018/T019: Backfire, jev-judge-mcp and system-one-adapter source/dependency routes are removed. The uv lock loses ten packages; `mcp` and `mcp-types` remain 2.2.0. The exact list and commit evidence are in [migration.md](contracts/migration.md#built-migration-evidence).

## Open questions for Root

1. Ultrafast text-generation helper: keep it held with no ungated student-data route until its boundary and tested routing are decided.
2. Wiki domain-roster operator location: the legacy `backfire` name is retained; main decides any rename.
3. First-release activation timing: the user decides; no external client/provider-path activation is claimed.
4. Real-list population: main owns the separate authorized admission window.
5. Final review and frozen verification gates: Root/develop owns acceptance and task ticks.

## Cited sources

The August 2024 Ministry of Education/PIPC guideline is motivation and risk context. Printed p. 62 shows a conditional example keeping grade; printed pp. 113-114 give reference risk rankings and alternatives. Combinations require a comprehensive risk review. Resident-number use is prohibited in that example table, not authorized by masking. Verified PDF page indexes are 64, 115 and 116 (W4:11-45).

[PIPC August 2024 listing](https://pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS217&mCode=D010030000&nttId=10425), [verified PDF](https://www.sen.go.kr/component/file/ND_fileDownload.do?q_fileSn=2145906&q_fileId=55793d35-539a-4cf4-8620-79cdad5180c9). SHA-256: `4ad65a1ceab572d1e5d5eb0f4040ebd985aac0196e67bcfc28b8816432c56fa2` (W4 source-evidence.json).

Carrell et al., JAMIA 2013;20(2):342-348, [doi:10.1136/amiajnl-2012-001034](https://doi.org/10.1136/amiajnl-2012-001034), [full paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3638183/). This small English clinical pilot motivates realistic replacements only. It did not test Korean education, Faker, provider attacks or per-call unlinkability. Its extrapolated effectiveness is not this feature's result (W4:47-53).
