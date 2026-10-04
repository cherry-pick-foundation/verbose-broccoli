# Research: Jev MCP Privacy Proxy

Assumption: use the published pinned package rather than current upstream main. This summarizes research captured on 2026-10-04. Adoption, runtime acceptance and independent review remain pending. Root's 2026-10-04 decisions supersede D6's selection/GPL exclusion and D9's Ultrafast limit; neither is acceptance authority. See [pending independent dependency review](security/dependency-review.md); this record does not depend on its unfinished content.

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

The read-only W1 verdict is **adopt with conditions**. High integration risks are upstream skill frontmatter registering an unpinned bypass and unmasked request text/metadata. Medium risks include inherited provider/endpoint overrides, unvalidated usage, key restoration, ID/regex schema changes, uneven stdio bounds and paid retries. Force the chosen route and endpoint; limit child environment; restore all fields; bound requests; keep default retry behavior explicit. `dist/provider.js:168-193` retries selected HTTP statuses, at most three default attempts; ambiguous network failures are not retried (W1:167-181).

The selected OpenRouter path is `https://openrouter.ai/api/alpha/decisions` (`dist/provider.js:261-305`). Upstream already owns transport, status mapping, retries, deadline and streamed 1,000,000-byte provider-response ceiling. Do not duplicate them. No education gate, registry, call map, closure pinning policy or guarantee of exact restoration exists upstream. The package has 12 tools, no outputSchema, resources or prompts; normal results are JSON in one text block (W1:101-153).

## FastMCP fit and security limits

D5 selects [FastMCP 4.0.10](https://pypi.org/pypi/fastmcp/4.0.10/json), Apache-2.0, Python >=3.10, release commit `34597af15256dad0935809fb4b7959bd4eaf3e59`. It depends on `fastmcp-slim[client,server]==4.0.10`. The prototype's Linux/Python 3.14 closure had 68 distributions before Faker and romanizer research additions (W2 opening paragraphs; fastmcp-closure.txt).

Use `from fastmcp.server import create_proxy`, a disconnected `Client(StdioTransport(...), timeout=...)`, and `Middleware.on_call_tool`. `FastMCP.as_proxy` is absent in 4.0.10. Source: pinned `server/server.py:2511-2587`, `client/transports/stdio.py:25-69,130-153`, `server/middleware/middleware.py:97-116,237-242`, `tools/base.py:98-160`. [Proxy docs](https://gofastmcp.com/servers/providers/proxy), [middleware docs](https://gofastmcp.com/servers/middleware), version 4.0.10.

The synthetic prototype rewrote arguments/keys and restored text/structured/meta results. It exercised errors, unknown tools, timeout, child exit, six concurrent calls and direct resources/prompts. A constrained output schema rejected a restored long original; the selected Jev package has no outputSchema. These tests do not prove live Jev integration. A plain Client avoids ProxyClient automatic relays; list hiding alone does not block known resource/prompt calls. Explicit D3 blocking and metadata/error handling are necessary (W2; pinned proxy.py:173-212,479-655,724-818,1528-1779).

W2 installed/imported dependencies before the coordinator's security sequencing instruction was read. This is a sequencing deviation, not retrospective approval. Its later static artifact/OSV scan is bounded research, not pre-execution or independent acceptance. All 77 research distribution versions had no OSV match at query time and no .pth hook in inspected artifacts. Compiled wheels were not fully audited and selected wheel hashes can differ from installed binaries. FastMCP Python snapshots matched the release commit. Before adoption, obtain an independent read-only review of the actual selected closure, including native artifacts. Do not treat old advisory ranges ending before 4.0.10 as proof of safety (W2 and report-addendum.md).

Selected public Python artifact hashes from W2 artifact-review-evidence.json (not a forensic claim about installed binary wheels):

| Distribution        | Reviewed artifact                      | SHA-256                                                            |
| ------------------- | -------------------------------------- | ------------------------------------------------------------------ |
| fastmcp 4.0.10      | `fastmcp-4.0.10-py3-none-any.whl`      | `1f8462e3d97394a637e1b0f1eaea0002da661c8d98000ad43f0aa3fa1ff523e8` |
| fastmcp-slim 4.0.10 | `fastmcp_slim-4.0.10-py3-none-any.whl` | `c2abd40302b8f06b0291413cf537d57bc0f171b5fd98af5cfef3b2b6b506122f` |
| faker 40.40.0       | `faker-40.40.0-py3-none-any.whl`       | `cd45ebdd1363f92a45740ac49945e49fa18f7e10771884a83c796a235550d7b7` |
| namefyi 0.1.3       | `namefyi-0.1.3-py3-none-any.whl`       | `a5ef20c18938f806bcbe921faaf47641bb3e781d1c23f00149e318f85f673e36` |

## Faker, romanization and phone parsing

D5 chooses [Faker 40.40.0](https://pypi.org/pypi/Faker/40.40.0/json), MIT. Instantiate ko_KR per call and call `seed_instance(None)` to isolate its Random; draw `last_name()` and `first_name()` separately. Its inspected pool has 44 surnames and 121 given names: 5,324 combinations before filtering. Given endings split 46 vowel, five rieul and 70 other consonant endings. `(ord(last)-0xAC00)%28` distinguishes zero/vowel, eight/rieul and other/consonant. This preserves common particle fit without an extra dependency. Finite draws can repeat; no unlinkability guarantee follows (W2 faker-evidence.json; Faker generator.py:27-30,60-81).

The [official Revised Romanization rules](https://www.korean.go.kr/front_eng/roman/roman_01.do), sections 2 and 3(1), 3(4), 3(7), distinguish personal-name syllable behavior and preferred surnames. W2 compared 40 synthetic given names, 13 surnames and 21 diagnostic words; scores ignore case/hyphens only.

| Candidate        | Version/license                       | Given / surname / general | Decision                                                                   |
| ---------------- | ------------------------------------- | ------------------------- | -------------------------------------------------------------------------- |
| korean-romanizer | 0.28.0, GPL-3.0-or-later              | 40/40, 13/13, 7/21        | Candidate, pending decision; GPL obligations need actual adoption review   |
| hangul-romanize  | 0.1.0, two-clause BSD text            | 31/40, 11/13, 1/21        | Misses name sample                                                         |
| Python kroman    | 1.1, MIT declared; no shipped license | 33/40, 11/13, 1/21        | Old spelling behavior and provenance gap                                   |
| Python koroman   | 1.0.16, MIT wheel                     | 36/40, 13/13, 19/21       | General assimilation breaks personal-name exception; HEAD license conflict |
| namefyi          | 0.1.3, MIT                            | 40/40, 13/13, 3/21        | Candidate, pending decision; basic transliteration only, not complete RR   |
| npm kroman       | 1.0.1, MIT declared                   | 33/40, 11/13, 1/21        | Same misses; no Python benefit                                             |
| npm koroman      | 1.0.16, MIT declared                  | 36/40, 13/13, 19/21       | Same personal-name misses; no Python benefit                               |

Candidate, pending decision: [namefyi 0.1.3](https://pypi.org/project/namefyi/0.1.3/), repository snapshot `de7ec2f886897ffe5ff3f5f8c026f94c2dabf756`, no base dependencies. Its engine.py:11-16 explicitly describes basic decomposition. It is not complete Revised Romanization or an authoritative identity matcher. Known real Latin spellings win. Root has not approved it; main is asking whether limited alias derivation meets the user's requirement. Do not exclude GPL by assumption. W2's snapshot reports namefyi release 2026-03-30 and repository push 2026-07-19 at the revision above; no base dependencies. [korean-romanizer 0.28.0](https://pypi.org/project/korean-romanizer/0.28.0/) was released 2025-08-28, with repository push 2026-07-24 at `19ab68f1eacad90ba8c8394b9c673d4b9b894e5e`: the limited name sample fits, general rules remain incomplete, and GPL-3.0-or-later obligations need an adoption decision. [koroman 1.0.16](https://pypi.org/project/koroman/1.0.16/) was released/pushed 2026-05-28 at `e529729b923f8a9d9acc62b2c9c0887b00e9bd88`: strongest general sample, but assimilation violates personal-name behavior; its published wheel has a clean MIT license while HEAD contains license conflict markers. These are research snapshots, not current maintenance or license acceptance. Independent security/license review remains required before any adoption.

Without an adopted library, use only explicitly registered real romanized spellings and forms derivable from the registry's name parts, including known order/separator/case variants. Do not author transliteration. If a library is adopted, its reviewed generated forms supplement authoritative explicit spellings, with same-part stand-ins and exact reversibility; no complete preferred-spelling coverage is promised. The choice remains PENDING, not a no-library default. W2:33-49, package-survey.json, repository-survey.json, artifact-inspections/ and romanization-extended-evidence.json retain the comparison and exact diagnostic evidence.

[tossi 0.3.1](https://pypi.org/project/tossi/0.3.1/), BSD-3-Clause, adds bidict/six for a capability covered by Hangul arithmetic here; reject it for this narrow need. Reuse [phonenumbers 9.0.40](https://pypi.org/project/phonenumbers/9.0.40/) (Apache-2.0), already in `uv.lock:1231-1236`; use PhoneNumberMatcher(text, 'KR') and spans as current pseudonymize.py:667-698 does. It does not cover every digit string.

## Python MCP lock question

Current `uv.lock:991-1020` pins Python mcp/mcp-types 2.2.0; W2 resolved/tested 2.3.0. npm's independently resolved SDK versions are a different closure. Recommend resolving the actual synchronized uv workspace after CHE-84 handoff, retaining 2.2.0 only if FastMCP requirements allow it and the protocol fixtures pass. Otherwise review/pin 2.3.0 and rerun all Python consumer checks. No held lock was changed or compatibility assumed.

## Rejected alternatives and missing capabilities

Two registered judgment servers or direct upstream registration leave a bypass. A local HTTP/OpenRouter implementation duplicates reviewed upstream transport. Persistent pseudonyms contradict fresh maps. Organization/region/date/address/cohort detectors and blanket Hangul refusal contradict the approved narrowed boundary. Local transliteration duplicates incomplete upstream algorithms. Whole-frame transport rewriting adds custom transport outside scope (Design; D1-D6).

Upstream does not provide registration admission, teacher/guardian ownership facts, an authoritative EduOK format, complete Latin aliases, guaranteed restoration after changed spelling, richer Wiki page-ID validation or privacy coverage of chat's direct browser/text route. Resolve genuine missing inputs or hand off the component; do not grow a framework. W3:28-72 supplies exact caller evidence; [migration.md](contracts/migration.md) preserves it.
