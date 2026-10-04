# Feature Specification: Jev MCP Privacy Proxy

**Feature Branch**: `feature/jev-mcp-privacy`
**Created**: 2026-10-04
**Status**: Design draft; implementation and acceptance are pending.
Linear: CHE-86

Assumption: the approved design and D1-D11 apply except where the decisions recorded from Root below supersede them. Romanization and Ultrafast scope remain pending user decisions, not defaults. Proposed bounds and admission details below are defaults for review, not measured acceptance. Historical records stay unchanged. Source labels resolve in [research.md](research.md#evidence-register).

## User Scenarios & Testing

### User Story 1 - Judge education text through one gate (Priority: P1)

An authorized education agent submits observations, evidence and scores through the single registered `jev-mcp` server. Registered people and schools receive fresh stand-ins. The answer restores the caller's wording.

**Why this priority**: Existing semantic education judgments must remain usable within their privacy boundary (design brief; D1-D5).
**Independent Test**: A synthetic stdio upstream records all received fields and echoes them into nested results. Compare the captured request and returned result, including errors and concurrent calls.

**Acceptance Scenarios**:

1. **Given** registered synthetic person aliases and school variants, **When** any supported tool is called, **Then** upstream receives stand-ins and every returned text field restores exact matched originals.
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
- **FR-004**: Match registered full, given, romanized and school forms with deliberate boundaries and overlap precedence. Preserve ambiguous given-name handling and explicit real Latin spellings. Romanization-library adoption is pending. Without adoption, match explicitly registered real romanized spellings and forms derivable from registered name parts only; with adoption, reviewed generated aliases supplement them without claiming completeness (Root 2026-10-04 supersedes D6; W3:60-66).
- **FR-005**: Draw fresh per-call Faker ko_KR surname/given pairs and consistent alias parts, fit three Korean final-consonant classes where possible, and use call-local `School NN` labels. No stable mapping or seed in production (D5; W2 Faker findings).
- **FR-006**: Reject/redraw collisions with all registered spellings, original request text and same-call stand-ins; enforce bounded exhaustion. Keep pairs only in call memory and release them on success, error and cancellation (design brief).
- **FR-007**: Mask recognized phone spans with phonenumbers, e-mail, agreed EduOK patterns and resident-number patterns. Keep type labels; leave grades/classes and learning values unchanged. Do not restore obsolete broad detectors (design brief; W3:66-70).
- **FR-008**: Swap every unconstrained argument string and JSON key, including IDs, paths and regex literals. Schema `pattern` fields MUST stay unchanged or reject on registered/pattern identifiers; never silently exempt unsafe values (D4).
- **FR-009**: Restore every result string and key, including outer text JSON, nested JSON-encoded strings, plain error text, nested usage, structured content and allowed metadata. Preserve numbers, enums and error status. Reject ambiguous reverse maps; exact restoration covers unchanged stand-ins, not arbitrary model transformations (D2; W1:133-153).
- **FR-010**: Expose tools only. Hide and block direct resources/templates/prompts; disable sampling/elicitation/roots relays and unsupported continuations; reject application request metadata and suppress untrusted logs/progress (D3; W2 proxy findings).
- **FR-011**: Reject unsafe registry, malformed/unsupported input, size/depth limits, mapping conflicts, backend failure and unsafe results without raw exceptions or sensitive diagnostics. Use explicit timeout and mandatory-provider failure strategy; preserve service after bad input (D3; constitution V).
- **FR-012**: Enforce positive request/result/list/time/work bounds and demonstrate bounded memory/CPU plus zero per-call file writes with synthetic tests. No persistent pair store, cache, lock, budget ledger or key/salt (design brief; constitution VII).
- **FR-013**: Repoint session selection, grammatical competence, Wiki checks and prepared-request contracts before deleting dependencies. Preserve richer Wiki domain-roster checks separately; the gate list MUST NOT acquire student facts to satisfy them (W3:28-40).
- **FR-014**: Keep upstream `jev_noul`; remove local Noul only after compatibility checks. Remove `jev_score` promises without a replacement after confirming no production caller (W3:48; upstream-comparison.json), and adopt `jev_audit` as shipped. Drop Python-only `tests_format`, `tests_sha256`, `tests_weight` and typed error-code envelope assumptions at callers; local evidence hashes and receipts remain authoritative (Root 2026-10-04; D8; W1:183-203).
- **FR-015**: Refresh consumer skills under upstream name `jev`; remove direct upstream server frontmatter. Coordinate `typesafe-ai` naming and project instructions with their owners; leave historical records unchanged (design brief; W1:155-165).
- **FR-016**: Record exact credit-offers and jev-ultrafast handoffs. Credit-offers dependency repoint blocks Backfire deletion. Ultrafast direct HTTP does not satisfy the always-on gate; browser-choice and text-helper scope remain PENDING while main asks the user. Implementation stays chat-owned and requires the resulting scope handoff; do not accept the bypass as a documented limit (Root 2026-10-04 supersedes D9).
- **FR-017**: Resolve identical complete effective launch configurations once and reject conflicts before writes, with the smallest existing-discovery change and no second running server. Retain both plugin owners for cleanup and plugin-independent loading. Main effective registration/provider-path activation waits for the first official release (D11; W3:24-27).
- **FR-018**: Respect CHE-84 holds, section ownership, synthetic-only evidence, immutable completed results, workflow checks, Root-granted serialized full verification and other-provider final review. Record a split decision at 1,000 lines; develop owns final ticks (design brief; AGENTS.md:94-141).

### Key Entities

Registered list: source-backed real spellings grouped by person or school. Call map: exact matched substrings and generated aliases, scoped to one call. Tool contract: upstream input schema and observed text-result paths, versioned by the package. See [data model](data-model.md) and [tool contract](contracts/upstream-tools.md).

## Success Criteria

- **SC-001**: Actual synthetic upstream captures contain zero registered spellings or covered identifier-pattern originals across all 12 tools; echoed output restores each supported text field and key exactly.
- **SC-002**: Full/given/Latin aliases share one generated person per call; collisions redraw or reject within the bound; concurrent calls cannot cross-restore. Fresh draws are observable without claiming uniqueness across calls.
- **SC-003**: Known extra surfaces, metadata, constrained unsafe IDs, unsafe registries and failures produce generic errors with zero upstream forwarding where preflight fails; later valid calls succeed.
- **SC-004**: Boundary fixtures demonstrate every [data-model limit](data-model.md#positive-bounds), zero per-call writes and grade/class preservation. Captured peak resource use meets stated expectations or acceptance stops for review.
- **SC-005**: Code-only, Work-only, combined and one-plugin-disabled discovery yields one gated judgment route with correct cleanup ownership; actual caller fixtures parse upstream results; no live Backfire dependency remains before deletion.
- **SC-006**: Narrow checks, frozen-source full `npm run verify` with its same-run summary, a fresh other-provider review and split review precede integration. No planning document counts as runtime or legal acceptance.

## Edge Cases

Missing, empty, malformed, oversized or foreign-owned registry; symlink components; duplicate JSON keys; duplicate aliases with different owners; shared given names; compound surnames; composed/decomposed Korean; case and separator variants; overlapping school/person/pattern spans; literal candidate already in a request; collisions after key replacement; short finite Faker ending pools; upstream ID sanitization; changed regex semantics; numeric identifiers; invalid pattern; result expansion over the limit; JSON-in-text versus plain error; unvalidated usage values; unknown tools; cancellation, timeout, startup failure and child death; requests after a refused call.

## Assumptions and residual risk

Only authorized own-account Claude Code/Codex workers may read actual private sources, with training disabled. This feature's development tests use synthetic data only (plugins/work/AGENTS.md:22-26; design brief). Main populates the real list in a separate authorized admission window. The wrapper never scans a private source tree itself.

Unknown names and school spellings pass unchanged. Preferred romanizations, nicknames, unrecognized phone-like strings and bare IDs outside the agreed patterns can pass. Faker's finite pools and `School NN` labels can repeat across calls. Context, grade/class combinations and unchanged observations can identify people. Fresh maps remove stable person mappings but do not prove unlinkability or complete concealment. A model that changes a stand-in's spelling may prevent restoration. The gate does not establish legal compliance (W2; W4:39-53).

Main holds released states only. Feature source finishes into develop; no develop fast-forward or ad hoc merge into main is authorized. Main effective registration and provider-path updates wait for the first official release, whose timing belongs to the user, with a fresh whole-repository review. Repository implementation acceptance is separate from external client activation; no global rewrite or preserved user-data removal follows. Ultrafast browser-choice/text-helper scope is pending; its current direct route cannot count as satisfying the gate.

## Non-goals

No organization detector, pseudonym table, extra private persistence, local models, custom Jev/OpenRouter transport, provider framework, global configuration repair or private-data deletion. No credit-offers rewrite by this feature; Ultrafast scope awaits the user decision and chat-owner handoff, rather than an accepted direct-route exemption. No new Wiki writes, conversion batch, publication, release or push. No second CHE-84 constitution amendment or CHE-12 site changes. No replacement `jev_score` (design brief; D8-D9).

## Decisions recorded from Root (2026-10-04)

Identical Code/Work declarations are accepted only when their complete resolved launch configurations agree; one effective server retains both cleanup owners. Conflicting definitions still reject. Keep the change within existing discovery.

Wiki domain checks remain separate from the minimal private name list. The work consumer owner retains source-backed checks and obtains CHE-84 agreement before deleting old imports (former question 3). Review/gate callers drop `tests_format`, `tests_sha256`, `tests_weight` and the typed error-code envelope; local evidence hashes and receipts remain authoritative (former question 5).

Reviewed upstream schemas stay unchanged. Unsafe constrained fields reject before forwarding. Restore nested JSON strings/keys, plain errors and supported result metadata; hide and block resources/templates/prompts by list and direct call. Strip or reject unsupported relay metadata; callbacks and continuations stay disabled. Strip the upstream skill's direct unpinned server block, retain name `jev`, and remove Score promises after the production-caller check (W3:48).

The root `.python-version` becomes the source for the three old package-pin readers when Backfire is deleted, preserving the reviewed runtime. CHE-86 keeps one function returning the registry config directory. A separate future VERBOSE_BROCCOLI_HOME feature owns shared per-language path resolution; no old Backfire path migration or duplicate helper belongs here. Main activation waits for the first official release and its fresh whole-repository review.

## Open questions for Root

1. Which EduOK digit lengths and unlabelled/numeric representations are authoritative? Recommend confirming the format from an authorized source owner before detector acceptance; use labelled/page-slug synthetic shapes as provisional cases, never claim bare-number coverage.
2. Do the proposed bounds and two-active-call limit fit present education requests? Recommend the defaults in data-model.md, measured before rollout; exceedance fails closed and triggers review.
3. How should equal `jev` skills from two plugins appear in local discovery? Recommend byte-identical portable copies and one deterministic local link, with rejection on content differences. Server deduplication alone does not solve this separate existing conflict (scripts/plugin-clients.ts:189-214).
4. PENDING: does limited name-alias derivation meet the user's romanization decision, and which candidate, if any, may be adopted? Main is asking the user. Recommend deciding from the actual namefyi/korean-romanizer/koroman fit and license evidence in research.md, then the independent dependency review; do not assume GPL is excluded or namefyi approved. Until resolved, make no library selection or completeness claim.
5. PENDING: what browser-choice and text-helper scope must Ultrafast send through the privacy gate? Main is asking the user. Recommend the same gated boundary for browser-choice judgments and an explicit decision for text generation before routing work is accepted; keep implementation with the chat owner and do not treat direct HTTP as a compliant exemption.

## Cited sources

The August 2024 Ministry of Education/PIPC guideline is motivation and risk context. Printed p. 62 shows a conditional example keeping grade; printed pp. 113-114 give reference risk rankings and alternatives. Combinations require a comprehensive risk review. Resident-number use is prohibited in that example table, not authorized by masking. Verified PDF page indexes are 64, 115 and 116 (W4:11-45).

[PIPC August 2024 listing](https://pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS217&mCode=D010030000&nttId=10425), [verified PDF](https://www.sen.go.kr/component/file/ND_fileDownload.do?q_fileSn=2145906&q_fileId=55793d35-539a-4cf4-8620-79cdad5180c9). SHA-256: `4ad65a1ceab572d1e5d5eb0f4040ebd985aac0196e67bcfc28b8816432c56fa2` (W4 source-evidence.json).

Carrell et al., JAMIA 2013;20(2):342-348, [doi:10.1136/amiajnl-2012-001034](https://doi.org/10.1136/amiajnl-2012-001034), [full paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3638183/). This small English clinical pilot motivates realistic replacements only. It did not test Korean education, Faker, provider attacks or per-call unlinkability. Its extrapolated effectiveness is not this feature's result (W4:47-53).
