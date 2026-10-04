# Research: Jev MCP Privacy Proxy

Assumption: use the published pinned package rather than current upstream main. This summarizes research captured on 2026-10-04. Runtime acceptance remains pending. The independent dependency review is committed; its adoption conditions still require implementation evidence. Root's 2026-10-04 Faker-only decision supersedes D6: no romanizer is adopted. Browser-choice judgments must use the gate in a later chat-owner task; the text-generation helper stays held, with no ungated student-data route. See the historical [independent dependency review](security/dependency-review.md); its romanizer candidates do not override the current selection.

## Evidence register

`STATE` denotes the approved XDG state namespace `verbose-broccoli/workspaces/feature-jev-mcp-privacy/jev-mcp-privacy/`. Use an absolute XDG_STATE_HOME, otherwise HOME/.local/state. This is a public storage contract, not a private inventory. The authoritative immutable reports are:

| Label     | Path below STATE                                                           | Content                                                        |
| --------- | -------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Design    | `design-brief.md`                                                          | Approved single proxy, privacy scope, holds and acceptance     |
| Decisions | `decisions-wave1.md`                                                       | D1-D11; these decision IDs are cited throughout                |
| W1        | `results/w1-upstream-jev-mcp/attempt-1/report-v2.md`                       | npm closure, protocol/field tables, source and security review |
| W2        | `results/w2-fastmcp-gate-fit/attempt-1/report.md` and `report-addendum.md` | FastMCP, Faker, romanizer and phone fit; sequencing limits     |
| W3        | `results/w3-repo-inventory/attempt-1/report.md`                            | Callers, counts, hold and ownership inventory                  |
| W4        | `results/w4-source-verify/attempt-1/report.md`                             | Correct policy pages and bounded Carrell interpretation        |

Versioned consumer skill `skills/jev/SKILL.md` SHA-256: `b23f1627e33b5f82729f16362f7876c95a62f6380340dadd398238a7d9a4250a`; `skills/jev/reference/tools.md` SHA-256: `ca85854a139c8cc6b2562ffb9f075fa1ad1e10364220b2441a9641e483a061c7`. Both are npm 0.13.0 at the pinned commit (W1:155-165; provenance.json).

Public pinned URLs and essential tables below make this record usable without STATE. Source paths like `dist/server.js:95-105` refer to the inspected published tarball, not repository code. JSON evidence stays beside each report. Reports are research evidence, not acceptance certificates.

## Upstream Jev fit and closure

Decision D1 selects [@jkudish/jev-mcp 0.13.0](https://registry.npmjs.org/@jkudish%2fjev-mcp/0.13.0), commit [5e0ca5cacd1556dc0b8c227648843d3ebf5bdc93](https://github.com/jkudish/jev-mcp/tree/5e0ca5cacd1556dc0b8c227648843d3ebf5bdc93), MIT, Node >=22. Reviewed probes used Node 24.19.0. Pin the full lock with scripts disabled; the package declares caret dependency ranges (W1:21-57).

Tarball integrity: `sha512-0fFOAJwlsntMdHu4+t40H4BObOowfqVsZdMnU1tbqIHojbWotRia8quh8/SjEtwpC0CbemZF9TpBDbFNBhnRGw==`.

| npm package                  | Resolved version | License    |
| ---------------------------- | ---------------- | ---------- |
| @jkudish/jev-mcp             | 0.13.0           | MIT        |
| @jkudish/jev-agent-tools     | 0.1.4            | MIT        |
| @typesafe-ai/sdk             | 0.6.0            | MIT        |
| @modelcontextprotocol/core   | 2.3.0            | Apache-2.0 |
| @modelcontextprotocol/server | 2.3.0            | Apache-2.0 |
| @modelcontextprotocol/node   | 2.1.1            | Apache-2.0 |
| @hono/node-server            | 1.19.17          | MIT        |
| hono                         | 4.13.13          | MIT        |
| zod                          | 4.6.5            | MIT        |

W1's `dependency-closure.json` and `package-lock.json` retain every resolved URL/integrity. `npm ls --all --json` captured these nine production entries. `npm audit --json` reported zero advisory matches, not proof of security. No closure install lifecycle or native build was found; installation used `--ignore-scripts` (W1:39-57).

The read-only W1 verdict is **adopt with conditions**. High integration risks are upstream skill frontmatter registering an unpinned bypass and unmasked request text/metadata. Medium risks include inherited provider/endpoint overrides, unvalidated usage, key restoration, ID/regex schema changes, uneven stdio bounds and paid retries. Force the chosen route and endpoint; limit child environment; restore all fields; reuse existing tool/runtime/schema controls and report missing controls; keep default retry behavior explicit. `dist/provider.js:168-193` retries selected HTTP statuses, at most three default attempts; ambiguous network failures are not retried (W1:167-181).

The selected OpenRouter path is `https://openrouter.ai/api/alpha/decisions` (`dist/provider.js:261-305`). Upstream already owns transport, status mapping, retries, deadline and streamed 1,000,000-byte provider-response ceiling. Do not duplicate them. No education gate, registry, call map, closure pinning policy or guarantee of exact restoration exists upstream. The package has 12 tools, no outputSchema, resources or prompts; normal results are JSON in one text block (W1:101-153).

## FastMCP fit and security limits

D5 selects [FastMCP 4.0.10](https://pypi.org/pypi/fastmcp/4.0.10/json), Apache-2.0, Python >=3.10, release commit `34597af15256dad0935809fb4b7959bd4eaf3e59`. It depends on `fastmcp-slim[client,server]==4.0.10`. The prototype's Linux/Python 3.14 closure had 68 distributions before Faker and romanizer research additions (W2 opening paragraphs; fastmcp-closure.txt).

Use `from fastmcp.server import create_proxy`, a disconnected `Client(StdioTransport(...), timeout=...)`, and `Middleware.on_call_tool`. `FastMCP.as_proxy` is absent in 4.0.10. Source: pinned `server/server.py:2511-2587`, `client/transports/stdio.py:25-69,130-153`, `server/middleware/middleware.py:97-116,237-242`, `tools/base.py:98-160`. [Proxy docs](https://gofastmcp.com/servers/providers/proxy), [middleware docs](https://gofastmcp.com/servers/middleware), version 4.0.10.

The synthetic prototype rewrote arguments/keys and restored text/structured/meta results. It exercised errors, unknown tools, timeout, child exit, six concurrent calls and direct resources/prompts. A constrained output schema rejected a restored long original; the selected Jev package has no outputSchema. These tests do not prove live Jev integration. A plain Client avoids ProxyClient automatic relays; list hiding alone does not block known resource/prompt calls. Explicit D3 blocking and metadata/error handling are necessary (W2; pinned proxy.py:173-212,479-655,724-818,1528-1779).

W2 installed/imported dependencies before the coordinator's security sequencing instruction was read. This is a sequencing deviation, not retrospective approval. Its later static artifact/OSV scan is bounded research, not pre-execution or independent acceptance. All 77 research distribution versions had no OSV match at query time and no .pth hook in inspected artifacts. Compiled wheels were not fully audited and selected wheel hashes can differ from installed binaries. FastMCP Python snapshots matched the release commit. The committed independent read-only review covers the selected closure and native-artifact limits; implement its applicable conditions before acceptance. Do not treat old advisory ranges ending before 4.0.10 as proof of safety (W2 and report-addendum.md).

Selected public Python artifact hashes from W2 artifact-review-evidence.json (not a forensic claim about installed binary wheels):

| Distribution        | Reviewed artifact                      | SHA-256                                                            |
| ------------------- | -------------------------------------- | ------------------------------------------------------------------ |
| fastmcp 4.0.10      | `fastmcp-4.0.10-py3-none-any.whl`      | `1f8462e3d97394a637e1b0f1eaea0002da661c8d98000ad43f0aa3fa1ff523e8` |
| fastmcp-slim 4.0.10 | `fastmcp_slim-4.0.10-py3-none-any.whl` | `c2abd40302b8f06b0291413cf537d57bc0f171b5fd98af5cfef3b2b6b506122f` |
| faker 40.40.0       | `faker-40.40.0-py3-none-any.whl`       | `cd45ebdd1363f92a45740ac49945e49fa18f7e10771884a83c796a235550d7b7` |

## Faker, romanization and phone parsing

Root's latest amendment selects [Faker 40.40.0](https://pypi.org/pypi/Faker/40.40.0/json), MIT, with its DEFAULT ENGLISH locale and ONE `first_name()` per real person per call. Instantiate per call and use `seed_instance(None)` to isolate its Random. This supersedes W2's Korean-locale draw and particle-fit proposal; no final-consonant arithmetic or particle matching belongs in implementation/tests. All registered forms of one person use the same single first name. Redraw collisions with registered spellings, original text/keys and other same-call stand-ins, within 256 draws/identity and 128 identities; no stable seed/history. Mixed forms restore exact uniquely anchored originals, otherwise the registered romanized spelling or Hangul fallback. Test both rules. Finite draws can repeat; no unlinkability guarantee follows. A missing real Korean name can stand out among English fakes, an accepted trade-off (Root amendment 2026-10-04; W2 Faker generator.py:27-30,60-81).

The [official Revised Romanization rules](https://www.korean.go.kr/front_eng/roman/roman_01.do), sections 2 and 3(1), 3(4), 3(7), distinguish personal-name syllable behavior and preferred surnames. W2 compared 40 synthetic given names, 13 surnames and 21 diagnostic words; scores ignore case/hyphens only.

| Candidate        | Version/license                       | Given / surname / general | Decision                                                            |
| ---------------- | ------------------------------------- | ------------------------- | ------------------------------------------------------------------- |
| korean-romanizer | 0.28.0, GPL-3.0-or-later              | 40/40, 13/13, 7/21        | Not adopted: Faker-only decision; GPL review remains historical     |
| hangul-romanize  | 0.1.0, two-clause BSD text            | 31/40, 11/13, 1/21        | Not adopted: Faker only; misses name sample                         |
| Python kroman    | 1.1, MIT declared; no shipped license | 33/40, 11/13, 1/21        | Not adopted: Faker only; old spelling/provenance gap                |
| Python koroman   | 1.0.16, MIT wheel                     | 36/40, 13/13, 19/21       | Not adopted: Faker only; personal-name misses/HEAD license conflict |
| namefyi          | 0.1.3, MIT                            | 40/40, 13/13, 3/21        | Not adopted: Faker only; basic transliteration, not complete RR     |
| npm kroman       | 1.0.1, MIT declared                   | 33/40, 11/13, 1/21        | Not adopted: Faker only; same misses, no Python benefit             |
| npm koroman      | 1.0.16, MIT declared                  | 36/40, 13/13, 19/21       | Not adopted: Faker only; personal-name misses, no Python benefit    |

Not adopted comparison evidence: [namefyi 0.1.3](https://pypi.org/project/namefyi/0.1.3/), repository snapshot `de7ec2f886897ffe5ff3f5f8c026f94c2dabf756`, no base dependencies. Its engine.py:11-16 explicitly describes basic decomposition, not complete Revised Romanization or authoritative identity matching. W2's snapshot reports release 2026-03-30 and repository push 2026-07-19 at that revision; its reviewed wheel SHA-256 is `a5ef20c18938f806bcbe921faaf47641bb3e781d1c23f00149e318f85f673e36`, retained as comparison evidence only, not a dependency pin. [korean-romanizer 0.28.0](https://pypi.org/project/korean-romanizer/0.28.0/) was released 2025-08-28, with repository push 2026-07-24 at `19ab68f1eacad90ba8c8394b9c673d4b9b894e5e`: the limited name sample fits but general rules remain incomplete; GPL-3.0-or-later obligations were reviewed as facts, not adoption authorization. [koroman 1.0.16](https://pypi.org/project/koroman/1.0.16/) was released/pushed 2026-05-28 at `e529729b923f8a9d9acc62b2c9c0887b00e9bd88`: strongest general sample, but assimilation violates personal-name behavior; its published wheel has a clean MIT license while HEAD contains license conflict markers. These are research snapshots, not current maintenance or license acceptance. Root's Faker-only decision adopts none of these romanizers; the security review remains unchanged as historical evidence.

Decision recorded from Root (latest amendment 2026-10-04): FAKER ONLY. No romanizer dependency, generated Latin spellings or optional romanize hook. Persist only registered real person/school spellings; order, separator and case matching variants of a REGISTERED Latin spelling follow existing roster semantics in memory and are not new spellings. Every registered form of one real person uses the SAME single default-English Faker first name per call. Mixed forms are allowed. Where an echoed field/identifier uniquely anchors an original spelling, restore that exact original; otherwise restore the person's registered romanized spelling, or the Hangul name if no romanized spelling is registered. Preserve within-call identity and test both anchored and default restoration. Do not reject mixed forms or invent per-form fakes. W2:33-49, package-survey.json, repository-survey.json, artifact-inspections/ and romanization-extended-evidence.json retain the not-adopted comparison and exact diagnostic evidence.

[tossi 0.3.1](https://pypi.org/project/tossi/0.3.1/), BSD-3-Clause, adds bidict/six for particle matching, which is outside the latest approved first-name design; not adopted. Reuse [phonenumbers 9.0.40](https://pypi.org/project/phonenumbers/9.0.40/) (Apache-2.0), already in `uv.lock:1231-1236`; use PhoneNumberMatcher(text, 'KR') and spans as current pseudonymize.py:667-698 does. It does not cover every digit string.

## Decided EduOK and bounds

Root (2026-10-04) settled EduOK detection: isolated ten-digit numbers, including `s-<ten digits>` page IDs, use `EduOK NN`. Numeric boundaries exclude longer digit runs. phonenumbers runs first; an accepted phone span retains `Phone NN`, otherwise an isolated ten-digit number is EduOK. Resident numbers remain isolated 13-digit shapes with an optional separator after digit six. Nine/eleven-digit and embedded-ten-digit non-EduOK cases, phone overlap and grade/class preservation are required fixtures.

Root also settled reuse-existing-controls bounds. W1:71 records `JEV_MCP_REQUEST_TIMEOUT_MS` default 60,000 ms and `JEV_MCP_MAX_ATTEMPTS` default 3, clamped 1-6 (`dist/provider.js:20-29`). W1:167-181 and `dist/provider.js:31,94-136,261-305` record the streamed 1,000,000-byte response ceiling. Reuse unchanged per-tool schema/lib.js limits, including Noul's 64 propositions of 2,000 characters (W1:183-203; `dist/server.js:282-298`), explicit FastMCP client timeout and SDK message handling. Keep list storage limits, collision exhaustion, recursion safety and zero per-call writes; measure and record RSS/CPU without gate thresholds. [data-model.md](data-model.md#positive-bounds) lists the controls and named checks.

W1:174 and the independent security review identify missing stdio schema ceilings for verify claims/evidence, screen text/purpose and classification context. Pre-parse stdio allocation and concurrency controls are also not supplied by the gate. Record each as a handoff note to ask upstream for supported limits, or main for an operating-system resource scope at service level. Do not build new body/provider limits, custom framing or a scheduler. Only Ultrafast's student-data boundary for its held text-generation helper remains pending; browser-choice judgments must use the gate.

## Python MCP lock question

Decision recorded from the committed independent review F7/Q2: keep Python `mcp==2.2.0` and `mcp-types==2.2.0` while `jev-judge-mcp` 0.6.0 (PyModel) remains; it requires `mcp<2.3,>=2.2`. These pins satisfy FastMCP's declared ranges, but runtime compatibility still requires the synthetic acceptance fixtures. W2's 2.3.0 prototype is not integration acceptance. npm's SDK versions are a separate closure. Recheck the actual synchronized uv workspace after CHE-84 handoff without upgrading these Python pins while PyModel remains; no held lock was changed. Selected gate pins are FastMCP 4.0.10, Faker 40.40.0 and phonenumbers 9.0.40, with the review's applicable remaining closure and no romanizer.

## Rejected alternatives and missing capabilities

Two registered judgment servers or direct upstream registration leave a bypass. A local HTTP/OpenRouter implementation duplicates reviewed upstream transport. Persistent pseudonyms contradict fresh maps. Organization/region/date/address/cohort detectors and blanket Hangul refusal contradict the approved narrowed boundary. Local transliteration duplicates incomplete upstream algorithms. Whole-frame transport rewriting adds custom transport outside scope (Design; D1-D6).

Upstream does not provide registration admission, teacher/guardian ownership facts, complete Latin aliases, guaranteed restoration after changed spelling, richer Wiki page-ID validation or privacy coverage of chat's direct browser/text route. Resolve genuine missing inputs or hand off the component; do not grow a framework. W3:28-72 supplies exact caller evidence; [migration.md](contracts/migration.md) preserves it.
