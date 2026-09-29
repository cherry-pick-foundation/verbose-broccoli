# Research: Backfire Rebuilt From jev-judge-mcp

## Inputs

The read-only evaluation of jev-judge-mcp below was made on 2026-09-29 by a
Codex worker of the develop session, before this feature started. It is
copied from the worker's scratch report, with only its heading levels
lowered, because scratch directories are cleared on restart. Its paths are relative to the scratch
clones it names; `packages/backfire/...` paths are relative to `develop` at
`ae8cadf`.

The CHE-37 findings this feature must fix are in
`.specify/bugs/extract-regex-startup-timeout/assessment.md` on branch
`feature/backfire-extract-test` (last commit `ce72dac`). The develop
session's notes on it, also copied from scratch:

> CHE-37 lessons to check on the rebuilt server (from feature/backfire-extract-test, .specify/bugs/extract-regex-startup-timeout/assessment.md):
> 1. The extract regex limit must not count process start-up or imports; realistic patterns need at most 2 ms of CPU.
> 2. Runaway-pattern tests must use a pattern that still runs away in the chosen engine (the regex library finishes (a+)+$ at once).
> 3. The bounded-work test's 1-second event-loop stall check measures real time: backfire_verify failed it 3 of 3 with 16 busy processes, backfire_extract once with 80, before any fix.

## Evaluation of jev-judge-mcp 0.6.0 (2026-09-29)

### PyModel reuse evaluation

**Verdict.** Do not use `jev-judge-mcp==0.6.0` as a drop-in Backfire dependency. PyModel freezes against Jev MCP 0.5.0, while Backfire ports 0.9.0; PyModel also has its own schema, result, error, provider, and runtime behavior. For the planned FastMCP rebuild, use compatible MIT source selectively and keep Backfire’s own port as the compatibility reference. This is source reuse with a porting pass, not a small patch or a dependency swap.

MCP means Model Context Protocol. It is the JSON-RPC protocol that exposes tools to an agent. A provider sends the tool’s questions to a model API and returns its answers.

### Scope and checks

I cloned PyModel and jkudish/jev-mcp into this scratch directory. PyModel’s v0.6.0 tag is `fd6829c3fd1c3eb244f0feb011b6ca55298459f8`; its current branch is four commits past that tag. The upstream Jev MCP v0.5.0 tag is `67dd9fa5a6e895909f1b2d80bf45534c29cff25a`; Backfire’s source revision is `a1fcc1e47fc696614f081e23a66ff48a890f22fd`. Backfire records that source and its five port differences in `packages/backfire/src/backfire/UPSTREAM.md:3-53`. In this report, `packages/backfire/...` paths are relative to the `develop` checkout; PyModel paths are relative to its scratch clone, and `src/index.ts` references are relative to the upstream clone.

I installed the PyPI 0.6.0 package in the scratch environment, then ran the checkout’s tests. The full Python 3.12 source-checkout suite reported **4,577 passed, 8 skipped, 17 deselected** in 308 seconds. A first run from the installed wheel had five failures in installer tests that require the source checkout’s `pyproject.toml`; those tests passed from the checkout. A Python 3.14.6 install smoke check used `mcp==2.2.0` and `typesafe-sdk==0.7.1`; 144 provider, retry, and schema tests passed. No paid provider calls were made. Load checks used synthetic inputs and a fake provider. I did not open the held-out file or Backfire’s saved records.

In the commands below, `$SCRATCH` is the task scratch directory. The full suite command was run from the PyModel checkout with `HOME` and all `XDG_*` paths directed into scratch:

```sh
pytest -q -p no:cacheprovider --basetemp="$SCRATCH/.pytest-tmp-source"
# 4577 passed, 8 skipped, 17 deselected in 308.06s
```

The Python 3.14 targeted command was:

```sh
pytest -q tests/unit/test_retry.py tests/unit/test_providers.py tests/unit/test_schema_compile.py
# 144 passed in 2.06s
```

### 1. Tools and behavior

PyModel’s frozen TypeScript 0.5.0 tools list has ten tools. Backfire exposes the ten corresponding 0.9.0 tools plus `backfire_noul`. PyModel instead adds `jev_score`; it has no `jev_noul`. Backfire’s published order is in `packages/backfire/src/backfire/server.py:33-68`. PyModel’s frozen names, descriptions, and schemas are in `docs/reference/ts-0.5.0-tools-list.json`; its source definitions and handlers are in `src/jev_judge_mcp/tools/`.

The table lists required inputs first. Other listed fields are optional. “Description” summarizes each published description; the exact 0.5 text is in the frozen JSON file, and Backfire says it preserves 0.9 descriptions except for the Python regex change (`UPSTREAM.md:15-18,27-40`).

| PyModel tool → Backfire tool | Inputs and described purpose | Result and decision logic |
|---|---|---|
| `jev_verify` → `backfire_verify` | Required: `claims`, `evidence`. Optional: `auto_accept`. Checks each claim against evidence. | Per-claim verdict, confidence, action, and evidence link, plus a summary. Malformed answers fail closed as invalid responses. PyModel adds response fields and uses a different error envelope. PyModel: `tools/verify.py:65-151`; Backfire: `tools/verify.py:158-226`. |
| `jev_screen` → `backfire_screen` | Required: `text`. Optional: `purpose`, `block_at`, `review_at`. Screens external text for injection, substance, and relevance. | Probabilities, thresholds, and a recommendation. A missing or malformed required answer becomes an invalid response and review. PyModel: `tools/screen.py:30-114`; Backfire: `tools/screen.py:127-166`. |
| `jev_find` → `backfire_find` | Required: `query`, `candidates`. Optional: `top_k`. Finds and ranks candidate text. | Existence judgment and ranked candidates. Missing or malformed ranking answers fail closed. PyModel: `tools/find.py:19-115`; Backfire: `tools/find.py:119-166`. |
| `jev_classify` → `backfire_classify` | Required: `items`, `classes`. Optional: `purpose`, `context`, `auto_accept`, `minimum_margin`. Assigns items to a shared class list. | Per-item class, probabilities, and auto/review decision, plus totals. Jev 0.9 requires the chosen class to be the probability argmax. PyModel rejects a generated-ID collision; the upstream behavior lets one duplicate overwrite another. PyModel: `tools/classify.py:107-184`; Backfire: `tools/classify.py:166-231`. |
| `jev_decide` → `backfire_decide` | Required: `decision`, `evidence`, `priorities`, `candidates`. Optional: `requirements`, `escape_hatches`. Chooses among bounded alternatives. | Recommendation, supporting judgment, and action. Invalid choice answers fail closed. PyModel: `tools/decide.py:120-200`; Backfire: `tools/decide.py:186-250`. |
| `jev_rerank` → `backfire_rerank` | Required: `query`, `candidates`. Optional: `top_k`. Ranks candidates by relevance. | Ordered candidates with relevance scores and a summary. PyModel: `tools/rerank.py:19-141`; Backfire: `tools/rerank.py:84-180`. |
| `jev_compare` → `backfire_compare` | Required: `passage_a`, `passage_b`. Optional: `aspects`, `purpose`, `auto_accept`, `minimum_margin`. Compares factual relation and named aspects. | Overall relation and per-aspect judgments. PyModel adds a `warnings` field when an aspect contradicts the overall relation; it does not change the overall decision. PyModel: `tools/compare.py:28-156`; Backfire: `tools/compare.py:121-155`. |
| `jev_extract` → `backfire_extract` | Required: `document`, `fields`. Optional: `purpose`, `auto_accept`, `minimum_margin`. The caller’s regex finds candidate spans; Jev picks among them. | Per-field candidates, value, status, and truncation information, plus totals. Regex engine, flags, and timeout behavior differ. PyModel: `tools/extract.py:30-259`; Backfire: `tools/extract.py:131-315`. |
| `jev_review` → `backfire_review` | Required: `request`, `diff`. Optional: `tests`, `auto_accept`, `review_at`, `composite_floor`. Scores a patch on four rubrics and estimates whether it is safe to apply. | Rubric scores, composite, `safe_to_apply`, and auto/review/escalate action. Jev 0.9 adds score distributions and reason codes. PyModel additionally accepts a file list for `diff`, plus `tests_format` and `tests_sha256`. Backfire accepts a string diff and test text. PyModel: `tools/review.py:38-107,257-327`; Backfire: `tools/review.py:33-95,263-320`. |
| `jev_gate` → `backfire_gate` | Required: `request`, `diff`, `claims`, `evidence`. Optional: `tests`, `auto_accept`, `review_at`, `composite_floor`. Combines patch review with claim verification. | Review result, per-claim results, summaries, and one overall action. PyModel adds file-list review, evidence `kind`/`role`, and test format/hash fields. PyModel also sends diff and test text as implicit evidence and adds renamed-ID fields. Backfire’s v0.9 schema keeps evidence items to `id` and `text`. PyModel: `tools/gate.py:66-153,451-518`; Backfire: `tools/gate.py:23-167,170-374`. |

There are two unmatched tools. Backfire’s `backfire_noul` is a Jev 0.9 addition for calibrated proposition probabilities. It returns per-proposition probability, likely/unlikely/uncertain label, and auto flag. PyModel does not implement it. PyModel’s `jev_score` is its own extension for grading a subject against a caller-supplied ordered rubric; Backfire’s 0.9 tool list has no equivalent. PyModel’s definition is `tools/score.py:20-70`; Jev 0.9 adds Noul at `src/index.ts:339-446`.

The common input field names mostly align, but the versions do not have identical schemas. PyModel’s frozen v0.5 review and gate accept a string `diff`, while PyModel itself extends those tools to accept a file list and adds evidence metadata and test metadata. Backfire’s v0.9 port accepts a string diff and evidence `id`/`text`. PyModel also says the item shape directly in array descriptions. These are PyModel changes listed as `file-list-and-evidence-metadata` and `argument-item-shape-descriptions` in `docs/reference/divergences.json:610-635`.

There is also an important validation mismatch. Jev 0.9 rejects unknown input keys. PyModel’s argument parser follows the v0.5 behavior and strips unknown keys even though the published schema says `additionalProperties: false` (`tools/arguments.py:3-10). Backfire validates arguments against its published JSON Schema in `packages/backfire/src/backfire/server.py:71-96`. Its error keeps the Jev prefix but uses jsonschema’s validation text rather than Zod’s text, as Backfire records in `UPSTREAM.md:46-49`.

Jev MCP 0.5.0 to 0.9.0 changed more than the Noul tool. I compared the tagged source to `a1fcc1e`. The command `git diff --stat v0.5.0 a1fcc1e -- src/index.ts src/lib.ts src/provider.ts` reports **3 files changed, 792 insertions, 285 deletions**. The commit log identifies these material changes:

- Jev 0.9 adds `jev_noul` (`56f99f5`).
- It fails closed on missing or malformed answers in verify, screen, and find (`5554ca5`, `a98a593`), and requires classify’s selected class to be the probability argmax (`42aa7ff`).
- It rejects unknown input keys (`76940d6`).
- It retains review score distributions and reason codes (`ab41e42`).
- Its provider layer adds bounded retries, deadlines, response-size limits, and cancellation (`7162ac4`), and adds a compatible provider (`11f519c`).
- It fixes multi-letter regex flags in extract (`8ff16ff`) and upgrades Zod to 4 (`78487ae`).

Those are upstream 0.5-to-0.9 changes. PyModel’s own divergences are separately recorded in `docs/reference/divergences.json`. The ones that matter most here are:

- `extract-stdlib-re-subset`, `extract-deadline-includes-queue`, and `extract-pool-saturation-reason` (`divergences.json:106-155): Python’s regex dialect is narrower; its one-second deadline includes queueing and worker startup; saturation has a separate reason.
- `classify-generated-id-collision` (`divergences.json:277-290): PyModel errors on a generated-ID collision instead of preserving the source’s overwrite quirk.
- `score-tool-extension`, `compare-aspect-contradiction-warning`, and `program-response-fields` (`divergences.json:363-435): PyModel adds a tool, warning/result fields, and changes some questions and result fields.
- `file-list-and-evidence-metadata`, `argument-item-shape-descriptions`, and `error-code-content-block` (`divergences.json:610-650): PyModel broadens review/gate inputs, expands descriptions, and returns a typed error code in an extra result block.

For success, both expose one JSON text result per call, and Backfire’s documented business payloads follow Jev 0.9 except its five listed changes (`UPSTREAM.md:15-53`). Their MCP error envelopes differ. PyModel returns two content blocks on errors: the unchanged error text and a second compact JSON code block, also mirrored in `structuredContent.code` (`tools/toolset.py:116-125`). Backfire returns one text block and `isError: true` (`server.py:94-103`). Backfire’s tool-call error text uses jsonschema details; PyModel’s custom parser uses the TypeScript-compatible argument errors. PyModel also types an upstream 401 as `auth`; Jev 0.9 did not have typed provider errors (`divergences.json:637-660`).

### 2. TypeSafe and system-one-adapter

PyModel’s TypeSafe provider cannot use Backfire’s system-one-adapter client unchanged. “Drop-in client” means a replacement that accepts the same constructor and method calls. These two classes do not.

PyModel’s `TypeSafeProvider._sdk_client()` imports and constructs `AsyncTypeSafeClient` with `api_key`, `base_url`, retry policy, and an injected HTTP client (`providers/typesafe.py:121-144`). Each call passes `timeout` and `response_model`, then reads `response.root` (`providers/typesafe.py:160-195`). The adapter takes `structured_outputs`, `llm_answer_mode`, and optional provider/model settings instead; its `system_one` does not take `timeout` or `response_model`, and returns `SystemOneResponse`, not the SDK’s `.root` wrapper.

I proved the first mismatch with a fake client. I substituted the adapter class for `typesafe_sdk.AsyncTypeSafeClient` and called PyModel’s real `TypeSafeProvider._sdk_client()`. It failed locally, before any network call:

```
TypeError: _BaseSystemOneAdapterClient.__init__() got an unexpected keyword argument 'api_key'
```

A usable bridge must replace the hard-coded construction and adapt the call and response parsing in `providers/typesafe.py`. It must also preserve PyModel’s retry owner, cancellation, error translation, and HTTP redirect checks. I estimate about 30–60 lines for that bridge, plus a small provider-resolution/configuration seam and tests. This estimate is not an implemented patch. PyModel also exposes `Runtime(provider_factory=...)` (`tools/base.py:95-106`), so an external custom `JevProvider` can wrap the adapter without changing PyModel. That would not make the stock TypeSafe provider accept it.

### 3. Backfire-only modules

| Backfire module | Where it fits |
|---|---|
| `records.py` | Keep it as a wrapper or judgment hook. It records digests and fixed projections, not raw tool inputs or output text (`records.py:155-188,190-279`). PyModel has telemetry, but not this file format. A server hook is needed for tool-call records; provider/runtime instrumentation is needed for attempts and model-use metadata. |
| `backfire_education` pseudonymization | Keep it as a provider wrapper or pre/post-judgment hook. Backfire transforms state and questions before the provider and restores answers after it (`judge.py:123-177`). It is not a PyModel feature. A custom `JevProvider` can provide this without changing PyModel’s tool code. |
| `ready.py` | Keep as a separate acceptance command. It probes configuration and makes synthetic server/tool calls (`ready.py:196-213,364-365`). It does not belong in a reusable MCP server library. |
| `config.py` and profiles | Keep profile files and credential lookup outside the tool package. Backfire supports per-profile API, URL, model, credential, thinking, request, and status settings (`config.py:34-96,141-209). A fixed environment can be mapped to PyModel’s provider settings. Per-call Backfire profile selection needs a custom provider/resolver or a PyModel patch. |
| `boundary.py` | Keep a custom server/transport wrapper. It enforces a 10 MiB line limit, 118-second call deadline, cancellation, and record writes (`boundary.py:19-65,103-175). Stock tool decorators do not supply these Backfire policies. A new FastMCP server can implement them around calls; a PyModel server integration would need a server-layer patch. |
| `backfire_tools/acceptance` | Keep these as external test/acceptance tools. They target Backfire’s provider profiles, pseudonymization, and limits. They do not belong in PyModel’s runtime dependency. |

### 4. CHE-33, CHE-37, and CHE-38

### CHE-33: retrying transient provider failures

PyModel retries HTTP 408, 429, and every 5xx status. Its default is three attempts, a 30-second per-attempt limit, and a 90-second total budget (`providers/retry.py:42-72`). A fake-provider check produced:

```
500 calls=3 error=ProviderError: TypeSafe API request failed after 3 attempts: last failure: 500: local stub
missing-object calls=1 error=ProviderError: TypeSafe API returned an invalid response: expected an answers object.
missing-key calls=1 result answers={}
```

So PyModel handles an HTTP 500 with retries. It does not retry a valid HTTP 200 body whose whole `answers` object is absent. That envelope error is non-transient in `parse_envelope` (`providers/base.py:103-129,235-249`). If `answers` exists but a tool’s answer key is missing, the provider returns once and the tool’s fail-closed logic reports invalid response.

Backfire’s CHE-33 assessment plans retries for both 5xx and answerless-success responses (`.specify/bugs/provider-error-bursts/assessment.md:120-133`). PyModel only covers the first today.

### CHE-37: regex timeouts that include process startup

Backfire starts one Python regex child per field and applies a 1,000 ms parent timeout (`UPSTREAM.md:27-40`). Process startup therefore consumes that field’s timeout.

PyModel uses a bounded, warmed process pool. Its one-second deadline still includes admission, worker startup, inter-process communication, and matching. When the queue is full, it returns `regex_pool_saturated`; a queued or replacement worker can still use up the deadline (`extract/worker.py:93-150`; `divergences.json:131-155`). The server warms workers before serving requests (`server.py:279-287`).

I ran PyModel’s own synthetic load test, up to 64 concurrent calls, with this command from the PyModel checkout:

```sh
pytest -q -s -p no:cacheprovider --basetemp="$SCRATCH/.pytest-tmp-load" tests/load/test_overhead.py::test_local_overhead_stays_within_budget_up_to_64_concurrent_calls -m load
```

It reported:

```
1 concurrent: p50 1.37 ms p95 1.99 ms max 2.78 ms
4 concurrent: p50 2.27 ms p95 3.28 ms max 5.30 ms
16 concurrent: p50 2.13 ms p95 5.35 ms max 8.22 ms
32 concurrent: p50 1.58 ms p95 4.59 ms max 13.99 ms
64 concurrent: p50 1.42 ms p95 3.97 ms max 16.46 ms
1 passed in 10.48s
```

No regex timeouts occurred in that run. It used ordinary synthetic patterns and a warmed pool. It does not rule out false timeouts from saturation or worker replacement.

### CHE-38: synchronous duplicate-ID work blocks the event loop

PyModel’s `ensure_unique_ids` restarts its suffix search at 1 for each duplicate ID (`ids.py:30-51`). That makes a list of identical IDs quadratic. `jev_verify` runs this work for all evidence before its first `await` (`tools/verify.py:65-91`). Backfire’s port instead remembers the next suffix per base ID and reports linear work (`UPSTREAM.md:19-20`).

I measured PyModel’s helper with synthetic duplicate IDs using this inline script from the PyModel checkout:

```python
from time import perf_counter
from jev_judge_mcp.ids import ensure_unique_ids
for count in (1000, 2000, 5000, 10000):
    items = [{"id": "same"} for _ in range(count)]
    start = perf_counter()
    result = ensure_unique_ids(items, "evidence")
    print(count, perf_counter() - start, len({item["id"] for item in result.items}))
```

It printed:

```
1000: 0.037s; unique=1000
2000: 0.137s; unique=2000
5000: 0.888s; unique=5000
10000: 3.610s; unique=10000
```

A separate in-memory `jev_verify` call with 100,000 identical evidence IDs had not returned after 37 seconds at full CPU. I stopped it. The source path above shows the work happens before the handler yields to the event loop. This is the same kind of stall CHE-38 guards against. The full call was synthetic and bypassed the stdio byte limit; I did not measure a complete 100,000-item response.

### 5. Maintenance, private internals, and version fit

As of 2026-09-29, the PyModel clone has tags from v0.1.0 on Sep 23 through v0.6.0 on Sep 28. That is ten releases in six days. The git author summary shows one named human contributor and the GitHub Actions bot; `pyproject.toml` names the same person as maintainer. This is active but very young maintenance. It does not establish long-term stability. The source is [PyModel/jev-judge-mcp on GitHub](https://github.com/PyModel/jev-judge-mcp), and the package is [jev-judge-mcp on PyPI](https://pypi.org/project/jev-judge-mcp/).

The declared pins fit Backfire’s current stack:

- PyModel requires Python `>=3.12`, `mcp>=2.2,<2.3`, and optional `typesafe-sdk>=0.7.1,<0.8` (`pyproject.toml:1-27).
- Backfire pins `mcp==2.2.0` and `typesafe-sdk==0.7.1` (`packages/backfire/pyproject.toml:5-27).
- I installed and imported PyModel under Python 3.14.6 with those exact versions. The targeted tests passed. I did not run the whole suite under Python 3.14.

PyModel itself calls out private internals as the reason it caps the tested MCP and SDK minor versions: `server.py` accesses `MCPServer._lowlevel_server`, and `providers/typesafe.py` overrides SDK response parsing (`pyproject.toml:12-16). This makes upgrades sensitive to internals even though the current pins match Backfire.

### 6. Adoption size and recommendation

As a runtime dependency, PyModel would not remove most of Backfire’s package-specific code. Backfire still needs Noul, provider profiles, education pseudonymization, records, its stdio boundary, readiness checks, and acceptance tools. PyModel also lacks exact 0.9 tool behavior in several places. It would need a Noul addition, strict-input behavior, v0.9 fail-closed/argmax changes, Backfire’s error/result envelope, and an adapter bridge if it uses system-one-adapter.

The useful code reuse is the shared tool question/policy and validation logic, plus regex worker and provider utilities. Reusing those from source could replace much of the ten overlapping handlers and helpers. It cannot replace the Backfire-only modules above. `jev_score` should not be exposed unless requested. The overlapping handlers also need name/result adaptation and the 0.9 fixes. There is no safe line-count percentage because the packages divide the work differently.

Of the three requested options, I recommend **keeping Backfire’s port as the runtime compatibility layer**, and selectively reusing PyModel MIT source during the FastMCP rebuild. This avoids taking a young, 0.5-based server dependency while retaining the useful Python implementation. It also preserves Backfire’s 0.9 behavior as the target. Retain the license and copyright notices for copied source.

### 7. FastMCP and source reuse

There are three names that can be confused:

- `mcp.server.fastmcp` was the official SDK’s earlier high-level server module. It is absent from the installed `mcp==2.2.0`; importing it raises `ModuleNotFoundError`. The official SDK’s server in this version is `mcp.server.mcpserver.MCPServer`. That is the version that fits Backfire’s pin.
- PrefectHQ’s separate PyPI package is named `fastmcp`. Its optional `mcp` extra accepts `mcp>=2,<3`, so it can resolve with `mcp==2.2.0` ([package metadata](https://raw.githubusercontent.com/PrefectHQ/fastmcp/main/fastmcp_slim/pyproject.toml)). I did not install or integration-test that separate package.
- PyModel does not use the earlier official `FastMCP` module. Its `JevMCPServer` subclasses `MCPServer`, overrides `list_tools` and `call_tool`, and accesses the private `_lowlevel_server` only for notification handlers and its stdio transport (`server.py:62-110`).

PyModel separates tool logic from that server class. Each file in `tools/` declares a raw `mcp.types.Tool` schema and a handler that receives parsed arguments plus a `Runtime` (`tools/base.py:178-204). `Toolset` owns the tool registry and dispatches calls (`tools/toolset.py:27-91). The domain, policy, validation, limits, and regex worker modules do not need the MCP server layer.

For a FastMCP-style rebuild, keep the manual definitions and call path. Do not rely on decorators that infer schemas from Python type hints. Construct each `Tool` with the exact name, title, description, `inputSchema`, and `execution` values. Then override tool listing and call dispatch, or use the SDK’s low-level server API. Return a `CallToolResult` directly to control exact text, content blocks, and `isError`. The official SDK documents schema generation from type hints on the decorator path and supports custom JSON Schema through its low-level server path: [tool servers](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/servers/tools.md), [low-level server](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/advanced/low-level-server.md), [migration guide](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/migration.md).

The pure `domain/`, `policy/`, `validation/`, `extract/`, and shared limits/text/ID code can carry over unchanged if the package namespace and internal interfaces stay intact. The ten tool handlers can carry over as Jev tools only if their `jev_` names and output payloads remain acceptable. To publish `backfire_` names, retain Backfire result fields, and attach record/profile hooks, add a thin server adapter or change those definitions. Replace PyModel’s `server.py` and stdio entry point. Keep or adapt `tools/base.py` and `toolset.py` for the custom raw-schema dispatcher.

I found no MCP protocol behavior that a custom server cannot reproduce. The stock type-hint decorator path alone cannot guarantee Backfire’s exact schemas, argument-error text, or error blocks. The transport’s 10 MiB line cap, 118-second deadline, cancellation, and record policy also need custom transport hooks. These are server-layer work, not reasons to rewrite the pure tool logic.

## Phase 0 decisions (2026-09-29)

The coordinator read the upstream at `fd6829c` (cloned from
<https://github.com/PyModel/jev-judge-mcp>, tag `v0.6.0`), backfire at
`ae8cadf`, and the installed `mcp` 2.2.0, and settled these points for the
plan.

### R1. Which upstream files are vendored

- **Decision**: the import closure of `jev_judge_mcp.tools` and
  `jev_judge_mcp.stdio`, computed from the upstream's `import` statements:
  `__init__`, `cache`, `errors`, `fsutil`, `ids`, `keyfile`, `limits`,
  `responses`, `serialize`, `settings`, `stdio`, `telemetry`, `text`; the
  `domain` package (`answers`, `json`, `questions`, `usage`); `extract`
  (`candidates`, `dialect`, `executor`, `worker`); `policy` (`actions`,
  `claims`, `extract`, `ranking`, `review`, `screen`, `thresholds`);
  `providers` (`base`, `cloudflare`, `compatible`, `openrouter`,
  `resolver`, `retry`, `typesafe`); `tools` (`arguments`, `base`,
  `classify`, `common`, `compare`, `decide`, `extract`, `files`, `find`,
  `gate`, `observed`, `rerank`, `review`, `score`, `screen`, `toolset`,
  `verify`); `validation` (`caps`, `choice`, `extract`, `noul`, `numbers`,
  `score`), with the six subpackage initializers: 64 modules, 8,115 lines, plus `LICENSE` and
  `THIRD_PARTY_NOTICES.md`.
- **Rationale**: it is everything the tools need, unchanged, so imports and
  upstream tests keep working. The rest of the upstream (server entry point,
  installer, CLI, HTTP transport, doctor, calibration, hooks, packaged
  skills; about 5,000 lines) serves needs that backfire's plugins, build and
  readiness check already meet.
- **Alternatives**: the whole upstream tree (adds unused installer and HTTP
  code and its dependencies); only the pure modules with rewritten tool
  handlers (a rewrite, against the reuse rule); PyPI `jev-judge-mcp` as a
  dependency (rejected by the evaluation: 0.5-based and needs patches the
  package cannot take).

### R2. Where the vendored copy lives

- **Decision**: `packages/backfire/src/jev_judge_mcp/`, a module of the
  existing `backfire` package, with the upstream `LICENSE`,
  `THIRD_PARTY_NOTICES.md` and a new `UPSTREAM.md` in that directory. The
  vendored upstream tests go under `packages/backfire/tests/upstream/`,
  keeping the upstream `tests/` layout below it so their own imports work.
- **Rationale**: `backfire_tools/build.py` copies modules of
  `packages/backfire/src` by name into each plugin build, so the vendored
  copy and its license travel with the server without a new workspace
  package. Import names stay `jev_judge_mcp`, so no vendored line changes for
  the move.
- **Alternatives**: a separate workspace package `packages/jev-judge-mcp`
  (a new package, lock and build path for one consumer); renaming the
  package to `backfire._vendor.jev_judge_mcp` (touches every import line).

### R3. `backfire_` names without patching the tools

- **Decision**: backfire builds a copy of each upstream `JevTool` with the
  name mapped, tool-name tokens in its description mapped, and a handler
  wrapper that maps the payload's top-level `tool` value. `Toolset` compiles
  its argument parsers from these copies, so argument errors name the
  `backfire_` tool.
- **Rationale**: in the upstream, tool names appear only in each
  definition, in `frame(...)` calls and in `jev_gate`'s error payload
  (`tools/*.py`), always as the payload's first `tool` key. Mapping them at
  the registry keeps the vendored tools and their tests unchanged.
- **Alternatives**: editing every `jev_` literal in the vendored tools (as
  the port did), which changes eleven files and breaks their upstream
  tests.

### R4. Provider seam and the provider name

- **Decision**: a `JevProvider` subclass whose `evaluate` calls `judge()`
  and reports `provider: "compatible"`. It overrides `evaluate` rather than
  `_send`, so the upstream retry loop (3 attempts, 30-second attempts,
  90-second budget) does not wrap backfire's own CHE-33 retries or cut
  judgments short of the 118-second call deadline. The call's deadline and
  record file reach it through a context variable that the server sets for
  each call.
- **Rationale**: `Runtime.ask` calls `provider.evaluate(state, questions,
  model, None)` (`tools/base.py`), and nothing in the tools catches provider
  errors specially (`grep "except Provider" tools/`), so any
  `ProviderError` text reaches the caller unchanged. `compatible` is the
  value backfire's results carry today (`backfire/tools/answers.py`
  `PROVIDER`), is one of the upstream's provider names, and names no vendor.
  system-one-adapter's answers, dumped to JSON, have the fields the upstream
  validators read (`choice`, `probabilities`, `confidence`, `noul`, `score`).
- **Alternatives**: the upstream `TypeSafeProvider` with an adapter bridge
  (the evaluation estimates 30–60 lines plus a resolver seam, and it would
  bypass backfire's profiles); reporting the profile name (puts operator
  configuration into every result).

### R5. Server layer

- **Decision**: an `MCPServer` subclass modelled on PyModel's
  `JevMCPServer` (`server.py:62-110` upstream): `list_tools` and
  `call_tool` go to the `Toolset`, the `arguments: null` case raises the same
  error, and the cancelled and initialized notifications get no-op handlers.
  Its low-level server runs inside backfire's `Boundary.run`, which gets the
  raw request ID from `context.request_context.request_id`.
- **Rationale**: `JevMCPServer` itself cannot be imported without
  vendoring the upstream server module, which pulls in the HTTP transport,
  bearer-token middleware, key file, packaged skills and version lookup of
  the `jev-judge-mcp` distribution. The subclass is about 40 lines and is
  credited in its module docstring.
- **Alternatives**: vendoring `server.py` and patching out its HTTP and
  skill parts (a larger patch than the copy); the SDK's low-level `Server`
  as today (the user chose `MCPServer`).

### R6. stdio

- **Decision**: use the vendored `stdio_streams()` (lone surrogates kept,
  `NaN` refused, stdin read in an abandonable thread, fd 1 pointed at stderr
  while serving), patched to read at most 10 MiB per line and to end the
  session with `message_limit_exceeded` beyond it, as backfire does today.
  Backfire's `BoundedLineReader` is removed.
- **Rationale**: reuses the upstream transport and keeps the limit that
  backfire's contract requires.

### R7. `regex` executor (CHE-37, user's answer)

- **Decision**: a `RegexExecutor` implementation in backfire, passed as
  `Runtime(regex_executor=...)`. `extract/executor.py`'s `match_all` is
  patched to take its compile step as a parameter (default `re.compile`),
  so both engines share the upstream candidate pipeline. The upstream
  dialect translation compiles with `re.ASCII | re.IGNORECASE` at most
  (`extract/dialect.py:80`) and spells out every class, so translated
  patterns mean the same in `regex`'s version-0 mode; but `regex.ASCII` is
  128 where `re.ASCII` is 256 (checked with `regex` 2026.9.29), so the
  executor maps the two flag bits by name instead of passing the integer.
  The same check confirmed the user's runaway case: `(a|aa)+$` on 60 `a`
  and a `b` raised `TimeoutError` after 1.0 s of CPU with
  `concurrent=True`, and `(a+)+$` returned at once.
- **Rationale**: the seam exists, and the pipeline (empty-match advance,
  dedupe, caps) stays one implementation.
- **Alternatives**: patching `extract/worker.py`'s process pool (the user
  chose `regex` instead); copying `match_all` into backfire (a compatibility
  copy).

### R8. Upstream settings

- **Decision**: `Settings.model_construct()` with defaults only. The
  upstream's `Settings()` reads only the environment, so a stray
  `JEV_MCP_CACHE`, `JEV_MCP_MODEL` or provider key would otherwise change
  backfire's behaviour. The no-judgment model stays the upstream default
  `jev-latest`, which backfire reports today as well.

### R9. Upstream tests

- **Decision**: vendor the upstream tests that exercise the vendored
  modules and run offline without Node.js, Docker or network, with their
  support files and fixtures, under `packages/backfire/tests/upstream/`,
  unchanged except for recorded changes. Tests of modules or behaviour
  backfire replaces (process pool, providers it never selects) may stay if
  they pass unchanged. Added test-only dependencies are pinned as dev
  dependencies. The added run time is measured and reported.

### R10. What CHE-38 must move off the event loop

- **Decision**: measure before patching. Candidates found by reading the
  code: the stdio reader parses each line (`decode_json` and pydantic
  validation of up to 10 MiB) on the event loop; `Toolset._call` runs the
  argument parser and `stringify` of the result on it; handlers build IDs
  and questions before their first `await` (`tools/verify.py:65-91`); the
  writer's `encode_frame` serializes the response on it; backfire's
  `Boundary.receive` computes the input digest on it. The quadratic
  `ensure_unique_ids` (`ids.py:30-51`) alone stalls `backfire_verify` for
  tens of seconds with 100,000 identical IDs.

### R11. Jev profiles and the Vercel provider (user's answer, 2026-09-30)

- **Decision**: backfire's profiles get a second kind, a Jev profile
  (`api = "jev"`) that names its provider (`typesafe`, `openrouter`,
  `cloudflare`, `vercel` or `compatible`) and holds the provider's address,
  model and credential variable; the key stays in the profile's `0600`
  credential file. `judge()` keeps its order for both kinds: request
  validation, pseudonymization, the provider call, restoration, and the
  judgment record. A general-model profile keeps system-one-adapter, the
  size limits measured for general models, answer-distribution checks and
  CHE-33's retries. A Jev profile calls the named provider's `evaluate` with
  the call's remaining time, so PyModel's retries (408, 429, 5xx) apply, and
  leaves answer validity to the upstream tools, as PyModel does. Provider
  failures of a Jev profile map to backfire's fixed error types (for
  example `ProviderConfigError` to `backend_not_configured`, 401 and 403 to
  `credential_rejected`, 429 to `rate_limited`, a timeout to
  `provider_unavailable`, an envelope error to `malformed_output`), so no raw
  provider text reaches results, as today.
- **Vercel provider**: jev-mcp 0.9.0 (`src/provider.ts:247-279` at
  `a1fcc1e`) takes Vercel from `@jkudish/jev-agent-tools` 0.1.2 (MIT,
  Joey Kudish; `dist/transports/vercel.js`, fetched with `npm pack`): one
  `POST` of `{state, questions}` to
  `https://ai-gateway.vercel.sh/v4/ai/evaluation-model` with a bearer key
  and the headers `ai-gateway-protocol-version: 0.0.1`,
  `ai-gateway-auth-method: api-key`,
  `ai-evaluation-model-specification-version: 4` and `ai-model-id`; Noul
  questions go out as `boolean` and come back as `noul`; per-answer
  confidence comes from `providerMetadata.typesafe.confidence`; usage comes
  from `inputTokens` and `outputTokens`; the model defaults to
  `typesafe-ai/jev` unless it starts with `typesafe-ai/`. The port is a
  subclass of PyModel's `HttpProvider`, like its `compatible` provider, so
  it reuses PyModel's transport, redirect check, redaction and retries; the
  address and model come from the profile instead of the code.
- **Rationale**: the user chose this option; it keeps one judgment path for
  pseudonymization and records and adds only the Vercel protocol as new
  code.
- **Alternatives**: only a Vercel provider next to the general-model
  profiles (option B, not chosen); PyModel's own environment-variable
  resolver (it reads `JEV_PROVIDER` and provider keys from the environment,
  bypassing backfire's profiles and credential files).
