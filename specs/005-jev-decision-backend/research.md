# Research and Decision Record: Jev-Style Decision Backend

**Observed**: 2026-09-26, Asia/Seoul, with a revision the same day. Measurements
come from a throwaway harness outside version control, from direct Hive probes,
from probes of Deno 2.9.6 and from the pinned upstream artifacts named below.
They inform the plan; they are not acceptance of this feature.

## Evidence baseline — 2026-09-26

Input: the specification and its clarification session of the same day.

The harness lives in the git-ignored `.local/jev-substitute/system-one-adapter/`.
Its settings differ from this plan in ways that matter:

| File | SHA-256 | Shows |
| --- | --- | --- |
| `results/jb_ds_on.jsonl` | `38d4610e78d51456987f84288b3bd12e7a6fd95f5ee35d33dc4ca0775e7d089b` | JevBench public hard, thinking on: 111/111, ECE 0.0418, median 3.35 s, 95th percentile 14.75 s |
| `results/jb_ds_off.jsonl` | `2e1820118a13ccd5915f785434dca9f446873e2ea63036f5cc08162e8bb7b47f` | Same set, thinking off: 81/111 |
| `results/mcp_ds_on.json` | `f61d1bcb9cd94abc65d4bc1ce71894a7738a300378ce8dee3f636b06ad60595f` | `jev-mcp` 0.8.0 under Deno: nine passing checks over eight tools; `jev_extract` failed |
| `results/mcp_extract_node.json` | `678e305696f5ef69290e98f33775fd4bc3f3471c9bf267529de10294885f1bd0` | `jev_extract` passed under Node |
| `results/stress_DeepSeek-thinking-on.log` | `a89e1aa2ca6f85b8a363f11d3a955189f33bbe0590c2ea9bf93e3485d425b874` | 60 classification questions: 60/60 in 16.6 s, 5,240 output tokens |
| `jb_run.py` | `458c249cd3426e47629500f149a67bbba4d9d512062d95a4afc7f5a222fe9eb6` | Benchmark runner |
| `hive_provider.py` | `3893662344dca9f411d09396743e731383450313625486d6b1fddb77bfa4fdad` | Hive provider subclass |

- The benchmark ran with `normalize_probabilities=True`, two corrective re-asks,
  `RetryPolicy(max_retries=4)`, `max_tokens` 16,000 and a 180 s provider
  timeout. Rows report zero retries, but raw pre-normalization probabilities
  were not kept, so the calibration figure is not evidence for this plan's
  no-rescaling rule. Final acceptance re-measures it (SC-001).
- The tool checks cover `jev_gate`, `jev_review`, `jev_verify`, `jev_noul`,
  `jev_classify`, `jev_find`, `jev_screen`, `jev_compare` and `jev_extract`;
  `jev_rerank` and `jev_decide` were never exercised. The checks are not the
  eleven-tool acceptance that FR-001 requires.
- Jev 1.13 answered 81 of 111 in JevBench's own published per-task results.

Probes during the plan revision, same day:

- `jev-mcp` 0.8.0 run by Deno 2.9.6 from npm listed all eleven tools, and its
  `jev_extract` returned `invalid_pattern` with the reason "Cannot use import
  statement outside a module" before any judgment call. The tool starts its
  regex worker with `new Worker(source, {eval: true})`, and the source opens
  with an ESM `import` of `node:worker_threads`. A probe of both forms showed
  that Deno 2.9.6 rejects the ESM form, while
  `const { parentPort, workerData } = require("node:worker_threads");` works
  under Deno 2.9.6 and Node 24.19.0.
- Deno's `links` setting can substitute a patched local copy of an npm package,
  but only with a `node_modules` directory (Deno reports "Linking npm packages
  requires using a node_modules directory"); with `nodeModulesDir: "auto"` the
  patched copy ran and `jev_extract` reached the judgment call.
- Deno 2.9.6 by default refuses npm versions younger than 24 hours: resolving
  `@jkudish/jev-mcp` 0.9.0, published 2026-09-25T23:19Z, failed until then.
- The npm package `system-one-adapter` 0.5.0 (by SynthLuvr, not TypeSafe)
  declares a GitHub dependency, and Deno refuses to install it ("Package
  specified a dependency outside of npm"). TypeSafe publishes its adapter only
  on PyPI (`typesafe-ai/system-one-adapter-python`).
- `createRequire(import.meta.url)("../package.json")`, `process.env` and an
  exclusive `Deno.FsFile.lock` all work under Deno 2.9.6.

## Hive request behavior — 2026-09-26

Decision: the shipped `hive` provider profile
([provider profiles](#provider-profiles--2026-09-27)) makes every request send
`max_tokens` 32,768, JSON-object output and a thinking request, which is
`reasoning_effort: "medium"` since 2026-09-27
([Judgment quality probes](#judgment-quality-probes--2026-09-27)); the probes
below used the earlier `chat_template_kwargs: {"thinking": true}`. The backend
treats a response as
truncated when its completion tokens reach the profile's limit, whatever the
finish reason says.

Rationale: on `POST https://api-cdn.thehive.ai/api/v3/chat/completions` with
model `deepseek-ai/deepseek-v4.1-flash`, a request without `max_tokens` stopped
at exactly 128 completion tokens in both non-streaming and streaming modes, and
both reported `finish_reason: "stop"`. With `max_tokens: 4096` the same prompt
completed at 744 tokens; with `max_tokens: 50` it stopped at 50 tokens and still
reported `"stop"`. Hive's Chat Completions documentation describes `max_tokens`
only as an "output token cap" and names no 128-token default, so the cutoff is
recorded as observed behavior of this route, not a documented limit.

A direct probe on 2026-09-26 sent `max_tokens: 32768`,
`response_format: {"type": "json_object"}` and
`chat_template_kwargs: {"thinking": true}` together: HTTP 200 in 3.5 s, the
response `model` was exactly `deepseek-ai/deepseek-v4.1-flash`, the message had
a non-empty `reasoning_content`, and `usage` carried a top-level
`reasoning_tokens` (13 of 19 completion tokens; completion tokens include
reasoning). The backend takes either signal as per-response evidence that
thinking ran.

Hive rejected the adapter's strict `json_schema` response format with HTTP 400
and accepted `{"type": "json_object"}`. Thinking was disabled only by
`reasoning_effort: "none"` or `chat_template_kwargs: {"thinking": false}`;
`thinking: {"type": "disabled"}` and `enable_thinking: false` were ignored.

Status evidence for failure classes: Hive's documentation
(`docs.thehive.ai/docs/chat-completions-openai-compatible-llms`) sets a default
limit of 5 requests per second, answers 429 when it is exceeded, and answers 405
when the organization's balance is exhausted. The 2026-09-26 probes returned
401 for an invalid key and 400 for an unknown model, each with a body of
`{status_code, message}`. No other status was observed or documented.

Alternatives considered: relying on Hive defaults (the 128-token cutoff
truncates thinking silently); strict JSON schema (rejected by Hive); streaming
(the same cutoff applies and it adds parsing without benefit).

### Gate 2 probe, settings part — 2026-09-27

T002's profile-driven probe (`packages/backfire/src/acceptance/probe_provider.ts`)
ran once with the shipped `hive` profile (reported at 16:30 KST). The settings request
(the profile's `max_tokens` 32,768, JSON-object output and the thinking switch)
returned 200 in 1.1 s, with a response `model` of exactly
`deepseek-ai/deepseek-v4.1-flash`, non-empty `reasoning_content` and 54
reasoning tokens of 60 completion tokens, finishing with `stop`. An invalid key
returned 401, an unknown model 400, and a burst of six concurrent requests,
above the profile's 5 requests per second, returned five 200s and one 429 while
other evaluation traffic shared the account. Observed: 200, 401, 400 and 429;
405 stays documented-only and is covered offline by T049. The probe printed no
key, request or response content, or provider error text.

Rerun with the medium reasoning effort, 2026-09-27: after the move to one
`config.toml` and `reasoning_effort = "medium"`, the reworked probe ran once with
the shipped configuration. The settings request returned 200 in 2.3 s with a
response `model` of exactly `deepseek-ai/deepseek-v4.1-flash`, non-empty
`reasoning_content` and 77 reasoning tokens of 83 completion tokens, finishing
with `stop`; the invalid key returned 401, the unknown model 400, and the burst
of six five 200s and one 429. The medium setting is therefore accepted and
carries the thinking evidence the profile names.

## Python package — 2026-09-27

Decision: backfire is one Python package. It supersedes the two-runtime design
of the sections below that carry a note naming this one.

- **Runtime.** The package `backfire` lives in
  `packages/backfire/src/backfire/` and runs on the pinned Python 3.14.4 in a
  uv environment made from `uv.lock`. Nothing in the package runs on Deno or
  Node; the repository's own automation stays on Deno 2.9.6 and calls uv.
- **Server.** The MCP server uses the official MCP Python SDK (`mcp` 2.2.0,
  MIT) over stdio, one process per client session. The SDK's `stdio_server`
  reads whole lines with no size limit but accepts the caller's input stream
  (`mcp/server/stdio.py` in the 2.2.0 wheel), so the server passes a bounded
  line reader that ends the session when a line passes 10 MiB; the SDK still
  parses every message.
- **Tools.** The eleven tools are a Python port of `jev-mcp` 0.9.0's
  `src/index.ts` and `src/lib.ts` at revision
  `a1fcc1e47fc696614f081e23a66ff48a890f22fd` (MIT), served as
  `backfire_<suffix>` by the server `backfire`. The port keeps that release's
  descriptions, input schemas, question design, decision logic, result formats
  and error texts, with `ensureUniqueIds` in linear time (formerly recorded
  change 4). It differs from the release only in these recorded points, which
  `src/backfire/UPSTREAM.md` lists with the source revision and the original
  files' SHA-256:
  1. `backfire_extract`'s patterns are Python `re` regular expressions, and
     its argument description says so (the user's decision of 2026-09-27).
     Patterns whose meaning differs between JavaScript and Python are
     documented, not emulated.
  2. A failed judgment surfaces as the backend's fixed error text for its
     type ([judgment.md](contracts/judgment.md)), not as upstream's
     `Jev-compatible endpoint <status>: <body>`, because no HTTP transport
     exists.
  3. The tools make judgments through the in-process judge below instead of
     upstream's provider layer; `src/provider.ts` is not ported.
- **Judgments.** The tools call `system-one-adapter` 0.2.1's asynchronous
  client in the same process, with the profile-driven provider subclass, the
  SDK's retry policy and answer validation without rescaling. The local HTTP
  endpoint, its session token, port line and `X-Judgment-Metadata` header, the
  copied transport and its judgment-record hook (formerly recorded change 6)
  are gone; a per-call context carries the provider's reported model, thinking
  evidence, usage, attempts and latency to the judgment record. The judge's
  callers are the tools, whose deadline and record file come from the MCP
  boundary, and three direct callers, the readiness check, the gate 3 probe
  and the benchmark runner, which each set a 118 s deadline per judgment and
  write no judgment record; they read the returned judgment metadata.
- **Patterns.** `backfire_extract` runs each field's pattern with Python `re`
  in a child process, one field after another, and kills the child after
  1,000 ms, as upstream bounds its regex worker; cancellation and session end
  kill it too. The child also sets a timer on itself whose default action ends
  it at the same limit, so no child outlives a killed server for long.
- **Deadline.** Each tool call runs as one task. At 118 s after its request the
  MCP boundary cancels it, which cancels the provider request and kills a
  pattern child, and answers `deadline_exceeded`; provider attempts and retry
  waits use only the time left. The endpoint's 80 s and the transport's 82 s
  layers are gone.
- **Records.** The server writes the same tool-call and judgment records
  ([data-model.md](data-model.md#record-files)); digests use `rfc8785` 0.1.4
  (RFC 8785 canonical JSON).
- **Fidelity.** Gate 5 still captures `jev-mcp` 0.9.0's tool list and results
  on Node against a scripted System One endpoint, together with every judgment
  request the tools send (`state` and `questions`, in order); the offline
  fidelity tests give the port the same scripted answers through a test-only
  judge and require the same tool list, the same judgment requests and the
  same results after mapping the names, except where a recorded difference
  applies. With scripted answers, comparing results alone would not show a
  changed instruction or question.
- **Layout and launch.** The project follows the standard Python src layout
  (the user's decision of 2026-09-27): the runtime package
  `src/backfire/` with `__main__.py` and a `backfire` console command from
  `pyproject.toml`'s `[project.scripts]`, the tools in the subpackage
  `backfire.tools`, the development and release programs (the build, the
  probes, the evaluation runner and the upstream capture) in a second package
  `src/backfire_tools/` that is not shipped, and the pytest suites in
  `tests/`. The code plugin starts the server the standard way for Python MCP
  servers, `uv --directory ${PLUGIN_ROOT}/backfire run --frozen --offline
  --no-sync backfire serve-mcp`, and installing a copy is
  `uv sync --frozen --no-dev` in its `backfire/` directory, which creates the
  copy's own `.venv` there without the test tools. `pyproject.toml` requires uv
  0.11.32 or later (`required-version = ">=0.11.32"`, relaxed from the exact
  pin the same day at the user's choice), so clients with a newer uv can start
  the server while `uv.lock` still fixes every package. This replaces the POSIX
  `sh` launcher and the per-copy environments under `~/.cache` of the
  two-runtime design.
- **Tests.** The offline tests are pytest suites run through
  `deno task test:backfire`.

Rationale: the user decided on 2026-09-27 that one Python package is cleaner.
TypeSafe publishes its adapter only in Python, so a single runtime means either
porting the tools to Python or rewriting the adapter in TypeScript; the port
keeps the adapter's prompt, parsing and confidence formula unchanged (FR-013).
Removing the second runtime removes the process boundary between the server
and the endpoint: the local HTTP contract, the child's lifecycle, the session
token, the metadata header, the layered deadlines, a second test stack, lock
and build path, and the record hook inside copied code.

Cost, accepted by the user: about 2,100 lines of upstream logic become locally
owned code; `backfire_extract` accepts Python patterns instead of JavaScript
ones; each upstream release needs a re-port instead of a re-copy; and fidelity
now rests on captured upstream results instead of a byte-for-byte copy.

Alternatives considered for the launch: keeping a small `sh` launcher with
per-copy environments in the cache, so nothing is written inside a plugin copy
(more code and not the standard Python layout; the user chose `uv run` with the
copy's own `.venv`).

Alternatives considered: the two-runtime design of 2026-09-26 (a TypeScript
copy of the tools plus a Python endpoint; the process boundary above);
TypeScript only (rewrites the adapter and TypeSafe's formula, against FR-013);
Python with a JavaScript-compatible regex engine (the user chose Python `re`);
calling upstream `jev-mcp` on Node from Python (keeps two runtimes).

## Tool source: `jev-mcp` 0.9.0, copied — 2026-09-26

Superseded on 2026-09-27 by [Python package](#python-package--2026-09-27): the
tools are ported to Python instead of copied, and the recorded changes below
are replaced by the port's recorded differences. The evidence about the
release's behavior still applies.

Decision: the code plugin does not depend on the npm package
`@jkudish/jev-mcp`. It copies the package's TypeScript source at revision
`a1fcc1e47fc696614f081e23a66ff48a890f22fd` (release 0.9.0, MIT) into
`packages/backfire/src/upstream/`, together with the package's `package.json` and
`LICENSE`, and runs it under Deno 2.9.6 in the plugin's own MCP server. The
copied files and their SHA-256 at that revision:

| File | Lines | SHA-256 |
| --- | --- | --- |
| `src/index.ts` | 1,707 | `10ae5eee5fbe0de52a4e5e8240b550585a12bab953235d511d550b3decccaac7` |
| `src/lib.ts` | 406 | `6b96ab62448b4154a7e4a25ff6ca064b43d5df3fa0e087f6b02fa25e767067d2` |
| `src/provider.ts` | 435 | `29a993ed57c6137be2d633c666cb6ce7a9f9a313712f37b70e33a1d4fb44dc0c` |
| `package.json` | 57 | `26b822f14fb0eeffada9833cfa0905d40bc364e88e7785df01f40eeec8856d01` |
| `LICENSE` | 21 | `61ada187d8ec32d7ee7a31fe6d9ec1623cf02e43b9333300fdf8b3508a383717` |

The copy changes only these recorded points; `src/upstream/upstream.json` holds the
source, revision, original hashes and the diff:

1. `src/index.ts` imports `./lib.ts` and `./provider.ts`, and `src/provider.ts`
   imports `./lib.ts`, instead of the compiled `.js` names, which Deno does
   not map. (The provider's import was found during T006 on 2026-09-27.)
2. `src/index.ts` opens its regex worker source with
   `const { parentPort, workerData } = require("node:worker_threads");`
   instead of the ESM import, which Deno 2.9.6 rejects in an `eval` worker.
3. `src/index.ts` exports its `server` and no longer connects it to stdio; the
   plugin's entry connects it ([MCP boundary](#mcp-boundary--2026-09-26)).
4. `src/lib.ts`'s `ensureUniqueIds` keeps the next suffix for each base id, so
   items that share an id take linear instead of quadratic time; the resulting
   ids and their order are unchanged.
5. `src/provider.ts` keeps only its compatible-endpoint branch (lines 331 to
   382 at the revision) and the helpers that branch calls; the TypeSafe,
   Vercel, OpenRouter and Cloudflare branches and the import of
   `@jkudish/jev-agent-tools` go.
6. That branch hands each request's payload, response and
   `X-Judgment-Metadata` header, or its abort, to the plugin's judgment recorder
   ([Records](#records--2026-09-26)).
7. `src/index.ts` names its server `backfire` instead of `jev-mcp`, and the
   eleven tools `backfire_<suffix>` instead of `jev_<suffix>` wherever a client
   sees the name: tool registrations, the results' `tool` field, descriptions
   and error messages. Comments and `src/lib.ts` keep the upstream names.

Input schemas, question design, decision logic, result formats and error
texts stay those of release 0.9.0; the server and tool names follow change 7
(the user's decision of 2026-09-26). The provider
settings stay the upstream environment variables, which the entry sets in the
server's own environment: `JEV_PROVIDER=compatible`, `JEV_API_BASE_URL`,
`JEV_API_KEY` (the session token), `JEV_MCP_MODEL`, `JEV_MCP_MAX_ATTEMPTS=1` and
`JEV_MCP_REQUEST_TIMEOUT_MS=82000`. `@typesafe-ai/sdk` 0.6.0, TypeSafe's own
JavaScript SDK, keeps supplying the question builders `choice`, `noul` and
`score`.

Rationale, following AGENTS.md's order of reuse: a dependency on the npm
package no longer fits.

- Fit: its `jev_extract` fails under Deno, the repository's runtime; its stdio
  server ignores the end of the client's input, so a pending call keeps the
  process alive; and it offers no hook for the verdict records that FR-016 and
  SC-011 require. As a black box it forced the stdio relay, the end-of-input
  handling and the session kill of the first plan.
- Maintenance: the repository was created on 2026-09-17 and has 54 commits
  since; 0.8.0 and 0.9.0 came out about 26 hours apart, and its companion
  `@jkudish/jev-agent-tools` went from 0.1.0 to 0.1.3 in two days.
- A patched npm dependency under Deno works (probe above) but is still a patch,
  needs a `node_modules` directory and waits out Deno's minimum age on every
  release. Copying the source at a pinned revision with seven recorded changes
  keeps the upstream question design and decision logic, which FR-013 requires,
  and owns only the integration points.

What 0.9.0 does, from its source, under its own tool names; the copy keeps all
of it, served as `backfire_<suffix>`, except where a recorded change says
otherwise:

- Every tool passes the MCP request's abort signal to its judgment call, so an
  MCP cancellation aborts the HTTP request to the compatible endpoint.
- The compatible transport posts `{model, state, questions}` to
  `JEV_API_BASE_URL` with `Authorization: Bearer <JEV_API_KEY>`; the body does
  not name the calling tool. A non-2xx answer becomes the tool error
  `Jev-compatible endpoint <status>: <first 200 characters of the body>`, with
  the key redacted. A body that is not a JSON object with an `answers` object,
  or whose `usage` lacks finite non-negative token counts, becomes
  `Jev-compatible endpoint returned an invalid response: <reason>`. Missing
  `usage` is read as zero; a missing `model` is read as the configured name.
- `JEV_MCP_MAX_ATTEMPTS` counts all attempts including the first (default 3,
  clamped 1 to 6); retries apply to 408, 409, 429 and 500 to 599.
  `JEV_MCP_REQUEST_TIMEOUT_MS` is one deadline over all attempts (default
  60,000) that starts only when the tool calls the transport. Response bodies
  are capped at 1,000,000 bytes.
- Each tool validates the answers it receives: exact labels, values in
  [0, 1], sums within `0.01 + 1e-12`, the chosen Choice option at the maximum,
  and a Score's `score` within `0.02 + 1e-12` of its distribution's mean.
  An invalid answer becomes `invalid_response` and never `auto`.
- Some results never reach the endpoint: `jev_extract` makes no judgment call
  when no field has regex matches, and argument or budget errors fail inside
  the tool. Tool errors thrown by the upstream code, such as
  `Duplicate item id: <id>`, repeat caller input.
- `jev_review` and `jev_gate` cut the request, diff, test and evidence texts at
  50,000 characters and claims at 2,000, report `truncated: true` and never
  return `auto` for truncated input. Policy arguments such as `auto_accept`
  change verdicts without reaching the endpoint.
- `jev_extract` runs each field's pattern in a worker with a 1,000 ms limit,
  one field after another, for up to 32 fields, before the judgment call; the
  loop does not observe the abort signal.
- `jev_verify` accepts any number of evidence items, and in 0.9.0 its
  duplicate-id handling (`ensureUniqueIds`) is quadratic and synchronous: a
  probe with 100,000 evidence items sharing one id (4.2 MB) had neither
  answered nor called the endpoint after 121 s. Recorded change 4 makes it
  linear.
- `jev_find` accepts a single candidate, but the adapter rejects any Choice
  with fewer than two options, so that call fails with `invalid_request`.
- `jev_decide` reports `recommendation.escaped` only to say whether a supplied
  candidate was chosen; it applies no threshold and marks nothing for review.
- The MCP SDK's stdio transport (1.30.1) reacts to data and errors on stdin but
  not to end of input, and closes itself when its input buffer exceeds 10 MiB,
  so no MCP message may be larger.

Per-tool maximum requests in 0.9.0:

| Tool | Largest judgment request |
| --- | --- |
| `jev_find` | One Choice over up to 250 candidates, plus one Noul |
| `jev_classify` | Up to 64 Choice questions over up to 250 classes, at most 8,000 item-class pairs |
| `jev_rerank` | Up to 250 Noul questions |
| `jev_noul` | Up to 64 Noul questions |
| `jev_extract` | Up to 32 Choice questions of up to 21 options |
| `jev_gate` | Five review questions plus up to 16 claim Choices |
| `jev_verify` | One three-option Choice per claim, plus one evidence Choice per claim when there are several evidence items; the claim count has no upstream cap |
| `jev_compare` | Up to 11 three-option Choices |
| `jev_decide` | One Choice of up to 9 options plus up to 18 three-option Choices |

Alternatives considered: the npm package on Node with a committed
`package-lock.json` (the first plan; a second JavaScript runtime and the relay
around a black box); the npm package on Deno with a patched copy through
`links` (a patch plus `node_modules`, and every release waits out the minimum
age); writing new tools on the MCP SDK (drops the validated question design,
against FR-013); porting the tools to Python beside the adapter (one process,
but a rewrite of about 2,500 lines).

## Server and tool name — 2026-09-26

Decision: the MCP server is `backfire`, and its eleven tools are
`backfire_<suffix>` (recorded change 7). The plugin's folder, command,
configuration and record paths, tasks and skill use the same name.

Rationale: TypeSafe named Jev after William Stanley Jevons: "We named Jev after
William Stanley Jevons. We expect machine intelligence to follow a similar path
to coal, after steam-engine efficiency led to an increase in demand."
([TypeSafe, "Introducing System One Models & Jev"](https://typesafe.ai/blog/introducing-system-one-models-and-jev)).
The Jevons paradox is the strongest form of the rebound effect: an efficiency
gain leads to so much extra use that total use ends above where it started,
which economists call backfire. The name keeps that lineage without TypeSafe's
product name, because this backend is not TypeSafe's model.

Alternatives considered: `jev` (TypeSafe's product name, which this backend is
not); `judgment` (the domain word the records and contracts already use);
`rebound` (the general effect, of which backfire is the Jevons case);
`decision` and `verdict` (narrower than what the tools do).

## MCP boundary — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): the boundary observes the MCP Python SDK's message streams in the same way; the rules below still apply.

Decision: the plugin's entry creates the MCP SDK's stdio transport, connects
the copied `server` through it and observes the JSON-RPC messages that pass in
both directions, already parsed. It writes one tool-call record for every
`tools/call` request, whatever ends it: the tool's result, a tool error, a
protocol error from the SDK's own argument validation, a cancellation, the
call deadline or the end of the session. It passes every message unchanged,
except that:

- at the call deadline it cancels the call inside the server and answers the
  client with a fixed tool error of its own;
- it drops a response for a call that is already closed (cancelled or past its
  deadline);
- when a tool-call record cannot be written, it answers that call with a fixed
  error instead of the unrecorded result;
- when the client's input ends or its output breaks, it shuts the session down
  ([Session lifecycle](#session-lifecycle--2026-09-26)).

Rationale: FR-016 and SC-011 bind each verdict to the input the agent submitted,
and SC-011 covers every tool call, including those the SDK rejects before a
tool runs. Observing at the transport inside the process sees exactly what the
client sent and received, with no second process, no line parsing and no
change to the tool handlers.

Alternatives considered: wrapping each tool handler (misses calls the SDK
rejects during argument validation); a separate stdio relay process (the first
plan; only needed around a black box); reading the SDK's private tool registry
(an unpinned internal).

## One retry layer and one deadline — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): the retry layer stays the SDK's policy, but the endpoint's 80 s and the transport's 82 s layers are gone; the 118 s call deadline cancels the in-process judgment directly.

Decision: the copied transport runs with `JEV_MCP_MAX_ATTEMPTS=1` and
`JEV_MCP_REQUEST_TIMEOUT_MS=82000`. The endpoint owns every retry through the
TypeSafe SDK's `RetryPolicy`, passed to the adapter, and ends each request
within 80 s of receipt.

- Retried, at most four attempts in total including the first: 429 and any
  status the selected profile maps to `rate_limited`, and connection failures
  before the request reached the provider (the policy's `http_statuses` set to
  those statuses, plus a predicate that accepts only connect-phase errors; the
  SDK's broader connection and timeout rules are off).
- `Retry-After` is honored. The policy's time budget is the endpoint's
  remaining time, so a wait that would not fit ends the request with the last
  error instead of retrying early.
- Everything else fails at once, including read errors and timeouts after the
  request was sent, and every other status (for Hive, every 5xx status). Malformed or truncated output is
  never re-asked: the adapter runs with `n_retry_malformed_structure=0`. A
  valid verdict is final.

The SDK's time budget only stops further retries; an outer timeout in the
endpoint interrupts an attempt still in flight at 80 s.

The 120 s limit of FR-007 covers the whole tool call, in two layers:

- In the normal worst case, a `backfire_extract` call with 31 timed-out patterns and
  one matching pattern spends about 31 s before the judgment call (32
  timed-out patterns took 32.0 s on the host's Node 24.19.0 on 2026-09-26),
  then at most 82 s in the transport, which the endpoint's 80 s answer always
  precedes. The call fails with a specific error by about 113 s.
- The MCP boundary gives every call a deadline of 118 s after its request
  arrived. At the deadline it cancels the call inside the server, which aborts
  the tool's signal and with it the transport's HTTP request, answers the
  client with the fixed tool error `deadline_exceeded` and records the call.
  The session keeps serving other calls.

The deadline timer runs on the server's only thread, so it fires only if no
tool blocks that thread. Upstream work before the judgment call is bounded once
recorded change 4 removes the quadratic duplicate-id loop: every other input is
capped by the tools or by the 10 MiB message limit. A feasibility gate measures
each tool's longest event-loop stall at that limit and requires it to stay
under 1 s, so an answer at the 118 s deadline still leaves the 120 s limit;
`backfire_extract`'s pattern timeouts are awaited, not blocking, and count
toward the whole-call time instead.

Rationale: FR-007 allows retries only for network errors and rate limits, in
exactly one layer. The SDK already implements attempt counting, backoff,
`Retry-After` and a time budget, and the OpenAI SDK retries are already off
inside the adapter (`max_retries=0`). Hive documents no 5xx retry semantics,
and a failure after the request was sent may already have been processed, so
no 5xx status is retried unless a profile maps it to `rate_limited`, which
the Hive profile does not.

Alternatives considered: letting the transport retry (its allowlist includes
every 5xx); retrying 502, 503 and 504 (not network errors under FR-007); ending
the whole session at the deadline (the first plan's relay; it also ended other
open calls); running every call in its own worker so that blocking work can be
terminated (kept as the fallback if the feasibility gate finds unbounded work;
it adds a worker per call and a message protocol).

## Answer validation without rescaling — 2026-09-26

Decision: the adapter runs with `normalize_probabilities=False`. Its output
schema already rejects missing or extra labels, values outside [0, 1] and
non-JSON output. The backend additionally rejects a Choice or Score
distribution whose sum differs from one by more than `0.01 + 1e-12`, and an
all-zero distribution. Every value the adapter computes stays as it is: the
Choice, the Score's `score` (the mean of the level indices weighted by the
returned probabilities divided by their sum) and the confidence values from
TypeSafe's formulas. The returned probabilities are never changed.

A placeholder under FR-008 is a value supplied in place of missing or unusable
model output. The adapter has two such fallbacks: an all-zero Choice becomes
its first option, and an all-zero Score is scored as uniform. Both are
rejected. A probability the model actually returned, including 0.5, is a
judgment and passes unchanged; FR-007 makes low-confidence verdicts final.

Rationale: FR-008 forbids rescaling the probabilities, which stay untouched.
The upstream tools use Score only in `jev_review` and `jev_gate`, always with
three levels, and they require a score in [0, 2] within `0.02 + 1e-12` of the
plain sum of index × probability, not divided by the probability total. For
three levels and a total within 0.01 of one, the adapter's score always lies in
[0, 2] and within 0.02 of that sum;
a check of 200,000 random distributions and the boundary cases on 2026-09-26
found no violation (largest gap 0.020000000000000018). Only a sum within 1e-12
of the 0.01 limit could exceed the upstream tolerance, by at most 1e-12, and
the tool then reports `invalid_response`. The plain sum itself leaves the
range: `{0: 0, 1: 0.005, 2: 1}` gives 2.005, which `backfire_review` rejects.

Alternatives considered: adapter normalization (forbidden by FR-008);
replacing the score with the plain sum (breaks `backfire_review` and `backfire_gate` at
allowed totals above one); rejecting every 0.5 (would discard genuine
uncertainty).

## Request size limits — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): the in-process judge applies the limits, and requests must finish within the time left of the 118 s call deadline instead of the endpoint's 80 s budget.

Decision: the endpoint fails a request with `request_limit_exceeded` before any
provider call when a Choice has more options than the option limit or the
request has more answer cells than the cell limit. A cell is one Noul, one
Choice option or one Score level. The option limit is 150 and the cell limit
300 until the feasibility task fixes both; 300 cells is the 60-item, five-class
classification that passed on 2026-09-26. The backend does
not split requests. At the other end, a single-candidate `backfire_find` fails with
`invalid_request` because the adapter needs at least two options; the backend
does not invent a second one. One MCP message may not exceed 10 MiB.

Rationale: in single measurements with one relevant option among unrelated
ones, 50, 100 and 150 options returned the relevant option with probability 1.0
(4.2 s, 9.3 s and 25.9 s). At 250 options the model returned exactly 1/250 for
every option, and the adapter's argmax picked the first. Several upstream
maximums (table above) exceed the measured throughput of about 315 output
tokens per second within the 80 s budget. A limit gives the explicit failure
that FR-005 allows before any cost; the upstream tools already tell agents to
split large batches. FR-018 permits but does not require splitting independent
questions.

Alternatives considered: letting the deadline catch oversized requests (slow,
billed and timing-dependent in tests); splitting independent questions inside
the backend (more glue; revisit only if agents need the upstream maximums);
splitting one Choice (FR-018 requires its own quality check); treating uniform
answers as errors (a genuinely uncertain answer can be uniform over few
options).

## Session lifecycle — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): there is no endpoint child; a session is one Python process, and shutdown cancels its calls and kills any pattern child.

Decision: the code plugin's MCP entry starts one server process per client
session, on Deno 2.9.6. The server starts the local System One endpoint as its
child: a Python process bound to `127.0.0.1` on a port it chooses and reports
on its standard output, checking a random per-session bearer token that the
server passes in the child's environment. The child's standard input is a pipe
from the server, and the child exits when that pipe reaches its end, which
happens when the server exits for any reason, including SIGKILL. When the
client's input ends or its output breaks, or the server receives SIGTERM or
SIGINT, the server cancels its open calls, which aborts their requests to the
endpoint, records them as `session_ended`, closes the child's standard input,
waits two seconds, then sends SIGTERM and, after two more seconds, SIGKILL,
and exits. The endpoint cancels a request's provider call when the server
closes the connection.

Rationale: FR-010 needs no separately managed service, independent sessions,
cleanup after crashes and cancellation that reaches the provider. End of input
is how a pipe reports a dead client, whatever killed it, and the same holds for
the child's pipe from the server. A parent-death signal would fire when the
spawning thread exits, not the process, and Deno spawns from its own threads.

Trust boundary: the token keeps other OS accounts and other sessions from using
the endpoint. Processes of the operator's own account can read the child's
environment and the key file; the operator's account is trusted.

Alternatives considered: a shared always-on service (a new service and one
failure point for all tabs); a Python launcher that starts the tools as its
child (the first plan; the MCP entry then has to relay stdio); `PR_SET_PDEATHSIG`
on the child (tied to the spawning thread).

## Server runtime and dependencies — 2026-09-26

Superseded on 2026-09-27 by [Python package](#python-package--2026-09-27): the server runs on Python 3.14.4 with its dependencies in `uv.lock`; the package has no Deno configuration or lock.

Decision: the server runs on the repository's Deno 2.9.6 with its own
configuration and lockfile in `packages/backfire/`, like the clean-code skill,
so a built code plugin installs from its own lockfile
([component location](#component-location-and-distribution-build--2026-09-27)).
It declares its npm dependencies
there, pinned exactly: `@modelcontextprotocol/sdk` 1.30.1, `zod` 4.6.5 and
`@typesafe-ai/sdk` 0.6.0, the versions `jev-mcp` 0.9.0's own lockfile resolves,
and `canonicalize` 5.0.0 for RFC 8785 digests, the version the repository
already pins. `nodeModulesDir` is `none`. Installation resolves from the
lockfile with `--frozen`; serving runs `--cached-only`, so it never downloads.
Every pinned version is older than Deno's default minimum dependency age of 24
hours, which stays on.

Rationale: constitution I requires pinned resolution and proven entry points,
and the repository's runtime contract forbids downloads at normal runtime. The
same SDK, zod and TypeSafe SDK versions as the upstream lockfile keep the
copied code's behavior. `canonicalize` implements RFC 8785, so any independent
verifier reproduces a digest.

Alternatives considered: Node 22 or later with npm (a second JavaScript
runtime for one component); floating semver ranges (unpinned resolution);
switching Deno's minimum age off (a supply-chain guard for no benefit).

## Gate 4, packaging — 2026-09-27

Superseded on 2026-09-27 by [Python package](#python-package--2026-09-27): this evidence is for the TypeScript server and is repeated for the Python package.

Evidence (T013, Deno 2.9.6 with TypeScript 6.0.3, uv 0.11.32): a plugin built
with `deno task backfire:build` into a directory outside the repository, run
with `DENO_DIR` and `XDG_CACHE_HOME` pointing at empty directories and a
separate uv Python directory, installed through its own
`backfire/src/bin/backfire install`: Deno fetched 95 npm and six JSR packages
from the built copy of `deno.lock` under its default minimum dependency age, uv
downloaded CPython 3.14.4 and `uv sync --frozen` installed the lock (26
applicable packages, with `typesafe-sdk` 0.7.1), both locks stayed
byte-identical to the source, and a later cached-only install and
`uv sync --frozen --offline --check` changed nothing. Offline,
`load_test.ts` builds two copies, installs them with `UV_OFFLINE=1`, runs
`serve-mcp` under `env -i` with the transport environment, and sees the server
`backfire` at version 0.9.0 (read through `createRequire`) with exactly the
eleven tools; each copy's environment imports `backfire_backend` from its own
copy and survives installing the source package and removing the other copy.

Decision: the copied `src/upstream/src/index.ts` stays out of type checking.
`deno check` reports 135 errors in it, all from the upstream source: 78
TS7006 and 53 TS7031 (implicit `any` parameters and bindings), and one each of
TS18046, TS2345 and TS2339 twice. With `strict` off, four remain (TS2339 three
times, TS2345 once), so no compiler setting makes it pass, and fixing them would
change the copied source beyond the recorded changes. No test imports it or
`main.ts` statically; `deno run` loads them at runtime and the load test
exercises them. The copied `lib.ts` and `provider.ts` pass strict checking.

Rationale: constitution I asks that the entry points be proven, which the
fresh-cache install and the load test do; keeping the copy unchanged matters
more than type-checking code this feature does not own (constitution VII).

Alternatives considered: relaxing the compiler options for the package (still
fails, and weakens checking of the locally owned code); editing the copied
source (an unrecorded change); `--no-check` for the tests (would hide errors in
the locally owned code).

## Local endpoint and Python environment — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): the interpreter pin and the lock stay; the endpoint becomes an in-process judge without Starlette or Uvicorn, and each copy's environment is its own `.venv` instead of one under the XDG cache.

Decision: the endpoint is a Python package managed by `uv`, with an exact
interpreter pin in `.python-version` (3.14.4, the host version) and a committed
`uv.lock`. Dependencies: `system-one-adapter[openai]` 0.2.1 (MIT, Python 3.10
or later; it declares `typesafe-sdk>=0.7.0` with no upper bound, and the lock
pins the tested 0.7.1), Starlette and Uvicorn for the endpoint, and pytest for
tests. Each component copy (the package in the repository, a built plugin, a
staged acceptance copy) has its own environment in the XDG cache, keyed by the
copy's resolved path and pruned when the copy is gone
([mcp-server.md](contracts/mcp-server.md#entry-commands)); revised on
2026-09-27, because uv installs the project editable and one shared
environment would let the last-synced copy's source serve every other copy. The
packaged install command runs `uv sync --frozen`; serving never syncs or
downloads. The host has uv 0.11.32.

Rationale: TypeSafe publishes its adapter only on PyPI, and the only npm port
cannot be installed by Deno (evidence baseline); constitution 0.18.0 permits
any language; constitution I requires pinned resolution and proven entry
points.

Alternatives considered: FastAPI (not needed over Starlette); the standard
library HTTP server (no asynchronous cancellation); an endpoint of our own in
TypeScript (reimplements the adapter, against FR-013).

## Component location and distribution build — 2026-09-27

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): the location stands; the build is a Python program in `backfire_tools` and copies only the runtime package, and the `sh` launcher and per-copy cache environments are replaced by `uv run` with the copy's own `.venv`.

Decision: all backfire code is the implementation package `packages/backfire/`,
with every source file under `src/`: the `bin/backfire` entry, the copied
upstream source, the server, the Python endpoint package `backfire_backend`,
the acceptance tooling (gate probes, evaluation runner, metrics, credential
scan and upstream capture) and the build step. The package root holds only
`deno.json`, `deno.lock`, `pyproject.toml`, `.python-version`, `uv.lock` and
the pytest suites in `tests/`. The package is not a member of the root Deno
workspace. The committed evaluation fixtures, including the held-out seal,
stay in `scripts/backfire/fixtures/`. The repository has no
`plugins/code/backfire/`: `deno task backfire:build -- <output>` writes a code
plugin to an output directory outside `plugins/` and `packages/`, copying
`plugins/code/` and, under `backfire/`, the package's configuration, locks,
`src/bin/`, `src/upstream/`, `src/server/` without tests or test doubles, and
`src/backfire_backend/`. It copies file contents, never links, with `@std/fs`.
Acceptance stages, and the client-installation feature installs, such a built
plugin.

Rationale: constitution IX (0.20.0) puts reusable implementation packages,
including MCP servers, under `packages/<name>/src/`, and on 2026-09-27 the user
directed the move, extended it to all backfire code, and chose to keep no
`plugins/code/backfire/` in the repository. A Deno workspace member shares the
root lockfile, while a built plugin must install with `--frozen` from its own
lock. The constitution permits a package outside the workspace: a package joins
a toolchain workspace only when it has executable code for it, which is a
necessary condition, not a requirement. Deno 2.9.6 ran a test under a
configuration outside the workspace's members from the repository root, with
and without `--config`, and from the package directory (checked on 2026-09-27
in a temporary workspace). The same relative layout in the package and in the
built plugin lets one entry script serve both. `docs/architecture.md` still
admits packages only for a shared need and registers them in the root
workspace; T057 aligns it with IX.

Alternatives considered: keeping the component in `plugins/code/backfire/`
(the earlier plan; against IX since 0.19.0); committing the built copy with a
drift check, like `docs/reference/` (the user chose no copy in the
repository); ignoring a built copy inside `plugins/code/` (also excluded by
that choice); a symbolic link from the plugin into the package (the
architecture forbids distributing package components as links); `deno bundle`
(rewrites the copied upstream source that the fidelity fixtures and the
recorded diff describe, and cannot carry the Python endpoint); `git archive`
(misses uncommitted work during development); joining the root Deno workspace
(the built plugin would need a generated lockfile).

## Hive provider glue — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): the provider subclass and its checks stay; the metadata reaches the judgment record through a per-call context instead of the `X-Judgment-Metadata` header.

Revised on 2026-09-27: the glue is provider-neutral and reads every
provider-specific value from the selected profile
([provider profiles](#provider-profiles--2026-09-27)); the heading keeps its
date and name for existing links.

Decision: subclass the adapter's `AsyncOpenAIProvider` to send the profile's
request options (for Hive, `max_tokens`, `response_format: {"type":
"json_object"}` and the thinking switch) and a request timeout, and to check
the response conditions: empty `choices` or content, a refusal, completion
tokens at the `max_tokens` its profile's request sets, missing usage, and missing thinking
evidence as the profile names it. The adapter client runs with `structured_outputs=False`,
`llm_answer_mode="probabilities"`, `normalize_probabilities=False`,
`n_retry_malformed_structure=0` and the retry policy above. Prompt, schema,
parsing and confidence stay in the adapter.

Per-request metadata: for each endpoint request the endpoint opens a context
variable that the provider subclass fills with the reported model, thinking evidence
and usage; concurrent requests never share it. The adapter's own
`SystemOneResponse.model` repeats the configured name and is not used. A
response without a non-empty `model` fails with `model_not_confirmed`, because
the tools would otherwise show the configured name as the answering model. A
different identifier is passed through unchanged, as the spec's edge case on
renamed models requires, and readiness marks the model unconfirmed. The
endpoint returns the metadata that the server cannot see in the response body
(attempts, latency, thinking evidence and reasoning tokens) in the
`X-Judgment-Metadata` header of every answer and error.

Nothing from the adapter's diagnostics leaves the boundary: `response.debug`,
`TypeSafeError.debug`, provider exception text and tracebacks hold rendered
messages and raw responses, so they are never logged, returned or placed in a
header. Errors are reported by fixed type and message only.

Rationale: the adapter's `OpenAIProvider` sends only model, messages and
response format, and its constructor accepts no request options. With
`structured_outputs=True` and JSON-object mode the questions would reach
neither the messages nor the API format; prompted mode puts the questions and
schema in the system message. Open adapter issues #45 (all-zero map returns
option #1), #46 (ignored refusal field), #47 (empty `choices` raises
`IndexError`) and #48 (no provider timeout option) are handled here and in
answer validation.

Alternatives considered: patching the adapter (a larger diff to maintain);
reading the model from the adapter's debug capture (holds request content);
reporting an upstream issue for request options (still worth filing, with the
user's approval, but not a dependency).

## Provider profiles — 2026-09-27

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): the shipped file is `src/backfire/config.toml`, the judge reads the selected profile in the server process, and there is no port line or transport model name.

Decision: every provider-specific value lives in a provider profile, one
`[providers.<name>]` table of the shipped `src/backfire_backend/config.toml`
([provider-profile.md](contracts/provider-profile.md)), and a profile holds
only what is specific to its provider. Its `api` key names the adapter
provider class that handles the protocol (`openai`, implemented; `anthropic`,
reserved and failing as not supported yet). The rest is the provider's own
characteristics: the API root, the model, the credential's variable name, the
request fields it needs beyond what the adapter sends (for Hive `max_tokens`,
JSON-object output and the medium reasoning effort), the paths to the response fields
that show thinking ran, the statuses whose meaning differs from the standard
one (for Hive, 405 for an exhausted balance), and the documented rate limit,
which the gate 2 probe exceeds on purpose. Standard status meanings come from
the TypeSafe SDK's error classes, the finish-reason check from the adapter, and
only `rate_limited` is retried. The endpoint's code, file names, tasks and
commands name no provider. The operator selects a profile, and may add or
replace provider tables, in `$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml`;
without that file the shipped `config.toml` selects `hive`, so the default is data
rather than code, and the Hive credential file stays `hive.env` with
`HIVE_API_KEY`. The endpoint reports the selected model on its port line, so
the server sets the transport's model name without reading a profile. A test
runs the same code with a second, test-only profile that has different request
fields, a nested reasoning-token path and a different status override, and
another fails when any file under `packages/backfire/src/` other than
`src/backfire_backend/config.toml` names Hive. Later the same day the user
replaced the file per provider with one `config.toml` that holds a table per
provider, in both the shipped and the operator location, so provider settings
live in one place.

Rationale: on 2026-09-27 the user rejected building Hive into the backend and
asked for an abstraction that allows reuse, choosing profiles over a broader
backend interface, TOML over JSON and YAML, and then only provider-specific
values over per-API sections, because protocol compatibility is already
handled elsewhere. The evidence for that: `system-one-adapter` 0.2.1 chooses
the OpenAI client itself (Responses for `api.openai.com`, Chat Completions for
other hosts), raises when the finish reason is not `stop`, and ships
`AsyncAnthropicProvider` behind its `anthropic` extra; its errors go through
the TypeSafe SDK's `api_error`, which maps 400, 401, 403, 404, 422, 429 and
5xx to error classes, and its `RetryPolicy` retries by status (wheel sources
of `system-one-adapter` 0.2.1 and `typesafe-sdk` 0.7.1, read on 2026-09-27).
A profile that restated those rules would duplicate them. Hive documents only
its OpenAI-compatible Chat Completions API. TOML needs no new dependency:
Python 3.14 reads it with the standard library's `tomllib` and Deno with
`@std/toml`, and it allows comments beside each value. FR-002 still fixes the
selected backend, so the default profile is the user's selection, and changing
the profile, endpoint or model stays an FR-012 upgrade. Keeping the credential
file name per profile leaves the operator's existing `hive.env` valid.

Known limit: a provider that answers one status for two causes cannot be
distinguished by a status override. OpenAI's own API answers 429 both for
"Rate limit reached" and for "Credit balance exhausted" and advises against
retrying the latter
([OpenAI error codes](https://developers.openai.com/api/docs/guides/error-codes)).
No selected provider does this, so support for it waits until one is selected.

Alternatives considered: Hive-specific code and names (rejected by the user);
one backend interface over all of the adapter's provider types (the user chose
profiles; it adds code for providers nobody selected); per-API sections with
full error rules, a configurable budget field and error-body matching (they
restate protocol handling that the adapter and SDK own; the user chose
provider-only values); keeping `jev-mcp`'s own provider branches instead of
recorded change 5 (they select System One services, not model providers, and
need `@jkudish/jev-agent-tools`); profile settings in environment variables of
`mcp.json` (Agent Plugins treats them as public package data, and the operator
could not change them without editing the package); operator-supplied profile
files (no second provider is needed yet; a shipped profile keeps its evidence
in this record); implementing the Anthropic-compatible API now (a second
subclass, the Anthropic SDK in the lock and a fake Messages server, with no
provider that uses it); JSON (no comments); YAML (a new parser dependency in
both runtimes, and implicit typing that reads an unquoted `on` as true).

## Records — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): the Python server writes the same records, with digests from `rfc8785`; the judgment record's metadata come from the in-process judge.

Decision: the server is the only record writer. It writes two kinds of JSON
Lines records to one file per session under
`$XDG_STATE_HOME/verbose-broccoli/backfire/records/`:

- a tool-call record per `tools/call`, from the MCP boundary, with the calling
  tool, the input digest over the submitted arguments, the outcome, the
  result's fixed-vocabulary decisions and its digest, and the duration;
- a judgment record per endpoint request, from the copied transport (recorded
  change 6), with the payload digest over the body it sent, the question types
  and sizes, per-question numbers by position, the provider's model, and the thinking
  evidence, usage, attempts and latency from the `X-Judgment-Metadata` header.

Digests are SHA-256 over RFC 8785 canonical JSON. Records hold no text from the
request or result and no caller-supplied identifier: question ids, option
labels, candidate ids and class names can all come from the caller, so options
appear only as positions. Each session holds an exclusive lock on its own file
and starts a new file at 10 MiB. Every append first takes an exclusive lock on
the directory's lock file and adds up all record files; if the new line would
pass 50 MiB, it deletes the oldest files it can lock, and if the line still
does not fit, the write fails. The directory therefore never holds more than
50 MiB, whatever sessions start, close or die. A record that cannot be written
fails its call instead of letting an unrecorded verdict through.

Rationale: FR-009, FR-016, SC-011 and constitution V and VII. One writer per
session keeps one locking implementation; the per-file lock stops cleanup from
deleting a live file; both locks are released by the kernel when a session
dies. Checking the total before each append keeps the bound after sessions
close or crash, when no later session may run cleanup. The server sees each
payload it sends, so the endpoint writes nothing.

Alternatives considered: the endpoint writing judgment records (a second writer
in a second language, and a call link it cannot see); one shared file with
rotation (needs cross-process coordination on every append); keeping labels as
"safe" metadata (callers control them).

## No raw-request archive — 2026-09-26

Decision: this feature keeps no raw-request archive. FR-009's archive clause
constrains any later one.

Rationale: nothing else in the specification needs an archive; the clarification
asked for retention only if raw requests are saved. A session-bound backend
cannot delete an entry seven days after saving it when no session runs, so a
correct archive needs a scheduler that outlives sessions. Tool-call and judgment
records cover diagnosis without content, and an agent's transcript already holds
the input.

Alternatives considered: cleanup at session start and hourly (misses the
seven-day guarantee between sessions); a systemd user `tmpfiles.d` rule with the
timer the OS already runs (the right owner if an archive is added later, but an
operator setup step outside this feature's need).

## Upstream error text returned to the agent — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): judgment failures now surface as the backend's fixed error texts; tool errors thrown by the ported tools still repeat the caller's input as release 0.9.0 does.

Decision: FR-009's ban on request content in error messages applies to what the
backend writes: endpoint error bodies, server logs, records and reports. Tool
results that the copied tools return to the calling agent over MCP, such as
`Duplicate item id: <id>` or an invalid pattern's text, repeat that agent's own
input as release 0.9.0 does, and the feature neither changes nor stores them.

Rationale: FR-013 keeps the upstream question design and results, and
rewriting them would change their contract. The clarification input asked that
keys, authentication headers and personal identifiers not remain in request
records and error logs; the records store only fixed-vocabulary fields.

Alternatives considered: rewriting tool errors at the MCP boundary (changes
upstream behavior and would need its own contract).

## Credential location — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): the file and its rules stand; the in-process judge reads it for each judgment, and nothing else in the server does.

Decision: the operator puts the selected profile's credential variable in
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/<profile>.env` (default `~/.config`)
with mode 0600; for the `hive` profile that is `HIVE_API_KEY=<key>` in
`hive.env`. The endpoint reads it; the server never does. A missing or empty
file, or one readable by group or others, fails each judgment with
`backend_not_configured`, which names the path. The only other setting is the
optional profile selection ([provider profiles](#provider-profiles--2026-09-27)).

Rationale: FR-009 keeps credentials outside the repository and the package;
Agent Plugins treats `env` values in `mcp.json` as public package data; the
constitution already sets the `verbose-broccoli` XDG namespace. Only the
process that calls the provider needs the key.

Alternatives considered: `${PLUGIN_DATA}` (not provided by every client);
reusing another tool's key file (a different owner); passing the key from the
server to the endpoint (puts it in a second process's environment).

## Agent-facing documentation — 2026-09-26

Decision: vendor the upstream skill `skills/jev` from `jev-mcp` 0.9.0 (MIT;
`SKILL.md` sha256 `53a2478ec24e2dfce94d3c427fe0b2895f553816d2918336e694658f0e725c27`,
`reference/tools.md` sha256
`1377d8cef66a70377fd36a10ea8b14086648cdff92b86e324d9cdbbb9d65a942`) into
`plugins/code/skills/backfire/` with an `upstream.json` record of these four
changes:

1. Remove the frontmatter `mcpServers` block, whose `npx -y` command would start
   an unpinned server with TypeSafe as the default provider.
2. Replace the first "Data handling and cost" bullet, which names TypeSafe as the
   provider and permits secrets, credentials or private source "unless policy
   allows it", with: inputs go to the model provider of the local backend's
   selected profile (Hive by default) through the code plugin's local backend,
   and never send secrets, credentials or private personal records such as
   student data.
3. Add a "See also" link to a local `references/verbose-broccoli.md`.
4. Rename the skill to `backfire` and every tool name in `SKILL.md` and
   `reference/tools.md` to `backfire_<suffix>`, matching the server.

The local reference states what is sent to the selected provider (the tool inputs within the
upstream size limits, and the questions), that the tools and this skill's
"gate before done" advice are advisory and nothing enforces them, that a gate
verdict judges only supplied text and does not prove that tests ran, and that a
screening pass never authorizes following instructions.

Rationale: the upstream skill already says the tools advise and the agent
enforces policy, that screened content is task data, and how to gate
completion; it describes the same tools the copied source serves. The
conditional permission in its data-handling bullet conflicts with FR-014 and
SC-012, so it is the one wording change beyond packaging.

Alternatives considered: a new local skill (duplicates upstream guidance);
leaving the upstream data-handling bullet (conditionally permits sending
credentials).

## Client acceptance — 2026-09-26

Decision: acceptance in Codex CLI and Claude Code runs the code plugin alone,
staged by building it into a temporary directory
([component location](#component-location-and-distribution-build--2026-09-27)),
from a working directory outside the repository, with no repository task. Each run registers only the staged package's declared `backfire` server for that invocation, reads tool arguments and results from the client's
event stream, and keeps no client session: Claude Code with
`-p --output-format stream-json --verbose --no-session-persistence
--strict-mcp-config --mcp-config <file>`, Codex with
`exec --json --ephemeral --skip-git-repo-check --ignore-user-config` and
`-c mcp_servers.backfire.*`. Installing the package through each client's plugin
mechanism, with skill discovery, belongs to a separate client-installation
feature; FR-001 and SC-008 stay open until it passes for the code package with
`backfire` and the known-answer set passes through the installed package in
both clients.

Rationale: FR-001 requires the code plugin installed alone. Claude Code 2.1.283
offers `--plugin-dir` for one session, but whether it reads this package layout
is that feature's question; Codex 0.157.0 installs plugins only from marketplaces, which
changes saved configuration and needs the user's approval.

Alternatives considered: registering the server from the repository checkout
(proves neither the package nor its declaration); installing into live client
configuration (needs the user's separate approval).

## Evaluation assets — 2026-09-26

Decision: the known-answer set, a one-case 60-item classification set and the
safety set are committed synthetic fixtures. The held-out general set is
written by a worker who does not implement the feature, before implementation,
stored outside the repository under `$XDG_DATA_HOME/verbose-broccoli/backfire-eval/`
and sealed by a committed hash and counts. Safety and held-out cases carry one
decision unit each, so a case's decision and approval are unambiguous.
`backfire_find`, `backfire_rerank` and `backfire_decide` mark no result as final without
review, so their cases never count as automatic, and the automatic-decision
rate divides only by the cases of the other eight tools (the user's decision of
2026-09-26, recorded in SC-010). Their cases still count toward accuracy.
The JevBench public hard tier is downloaded at evaluation time from a pinned
revision and checked against a recorded SHA-256. Every criterion runs three
times; each run must pass; failed responses count as wrong.

Runs work in a cache directory with a 256 MiB budget that is checked before
each write; a run that would pass it fails. The directory is removed when the
run ends, fails or is interrupted. Final acceptance replaces one committed
record, `artifacts/jev-decision-backend/acceptance.json`, in a single atomic
write.

Rationale: SC-001, SC-003, SC-004, SC-009 and SC-010 require fixed, versioned
sets and a held-out set that development never saw. The rate exists to catch a
backend that sends everything to review; the three tools without a review mark
cannot do that, and counting them would have capped the rate at 8/11 with equal
case counts, so 70% would have needed about 96% automatic decisions from the
other eight tools. Repository verification results live in `artifacts/`
(constitution IX), and
bounded working storage plus one replaced file give the evaluation writer a
fixed budget (constitution VII).

Alternatives considered: committing the held-out set (visible during
development); reusing the 111 benchmark items for final acceptance (the
clarification made them a regression check only); dividing by all cases, as
SC-010 first read (see the cap above); weighting the held-out mix toward the
eight tools (the result would depend on the chosen mix); treating
`escaped: false` as automatic (the tool marks nothing final; a 0.5/0.5 tie also
reports it).

## Evaluation expectations — 2026-09-27

Decision: a case's `expect.result` maps paths in the tool's result object to
one accepted value or a list of accepted values, and `expect.error` names text
that the call's error must contain ([evaluation.md](contracts/evaluation.md#case-format)).
Where a tool's primary result is an action or label and the right outcome is
automatic, the outcomes that defer the decision also count as correct: `review`
and `escalate` for `backfire_gate` and `backfire_review`, `review` for
`backfire_screen`, and `uncertain` for `backfire_noul`. Safety and held-out
cases carry `result` expectations only. The held-out seal has a fixed shape.

Rationale: the held-out set is sealed before implementation, so the runner's
implementers must be able to read every expectation from the contract alone,
and paths into the result object need no per-tool code. The user decided on
2026-09-27 that a deferring outcome counts as correct: SC-010's
automatic-decision rate measures decisiveness separately, and counting
deferrals as wrong would make the 90% accuracy bar demand near-total
decisiveness and leave the 70% bar redundant. Failure paths are covered by the
known-answer set and SC-005, so the safety and held-out sets measure judgments
only.

Alternatives considered: per-tool expectation fields named after the decision
units (per-tool code, and no place for top candidates or extracted values);
counting deferrals as wrong (the option the user rejected); failure cases in the
held-out set (they measure no judgment).

## Judgment quality probes — 2026-09-27

Question: which thinking request and how many questions per request the
selected backend should use, and where its judgments fail, measured before
implementation.

Setup: `system-one-adapter` 0.2.1 in this feature's strict mode
(`normalize_probabilities=False`, `n_retry_malformed_structure=0`, retries only
through the SDK's policy) against Hive's Chat Completions, driven by a
throwaway runner outside version control; the JevBench public hard tier at the
revision and SHA-256 of [evaluation.md](contracts/evaluation.md#sets) (111
English decisions: 67 Choice, 38 Noul, 6 Score); an off-sum or all-zero
distribution counted invalid and a failed call counted wrong; five runs per
setting, each with a different question order, one decision per request unless
stated. Other traffic shared the account during some runs, so times are
indicative.

DeepSeek V4.1 Flash, one decision per request, 555 decisions per setting:

| Thinking request | Correct per run | Wrong (confident ≥ 0.9) | Failed calls | Call time median / 95th | Output tokens per decision |
| --- | --- | --- | --- | --- | --- |
| `chat_template_kwargs: {"thinking": true}` | 109–110 | 4 (4) | 2 malformed | 4.5 s / 18.4 s | 1,206 |
| `reasoning_effort: "xhigh"` | 108–111 | 5 (3) | 0 | 5.9 s / 21.8 s | 1,484 |
| `reasoning_effort: "high"` | 108–111 | 6 (4) | 0 | 5.1 s / 16.2 s | 1,205 |
| `reasoning_effort: "medium"` | 109–111 | 3 (2) | 1 malformed | 5.2 s / 15.9 s | 1,159 |
| `reasoning_effort: "low"` | 108–111 | 6 (5) | 0 | 4.2 s / 12.9 s | 821 |
| none | 109–111 | 7 (5) | 0 | 5.4 s / 17.0 s | 1,192 |

Every setting carried non-empty `reasoning_content` and `reasoning_tokens` on
probe requests. The medium runs had an expected calibration error of 0.031 to
0.038 and no call over 33 s. With the thinking switch and eight decisions per
request, five runs gave 108 to 110 correct, 10 wrong answers and calls of 33 s
median and 60 s at most.

Findings:

- Wrong answers are mostly confident: 31 of 41 wrong DeepSeek answers had a
  top probability of at least 0.9, so the upstream tools' 0.85 thresholds would
  mark them automatic.
- The same decisions failed at every setting: approving a response that
  contains a small arithmetic error (`hard-sol-b-judge_hard-02`, wrong in 13 of
  the 30 one-per-request runs) and multi-step lookups among distractors
  (`hard-sol-a-multi_hop-09` and `-12`). Adversarial, ambiguous, probability,
  routing and trap questions were never answered wrong.
- More reasoning did not mean fewer errors: `xhigh` made more than `medium`.
- Asking again and accepting only agreement: two agreeing medium answers
  accepted no wrong answer over all 20 run pairs and left 1.4% of decisions for
  review; with the thinking switch, even three agreeing answers accepted wrong
  ones (0.36%).
- GLM 5.3 Flash on Hive, measured the same way over 37 runs, gave 102 to 111
  correct per run; its `max` effort made more errors than its default (17
  against 8 over ten runs of eight decisions per request) and three requests
  over 80 s, and one malformed answer lost all eight decisions of its request.
- The benchmark has no Korean content, so Korean behavior is unmeasured.
- Five runs per setting is a small sample; the settings differ by a few
  decisions.

Decision: the shipped `hive` table requests `reasoning_effort = "medium"`
instead of the thinking switch, with the same thinking evidence paths, and gate
2's probe reruns with it (the user's decision of 2026-09-27). Agreement voting
stays out of this feature: FR-007 forbids requesting a valid verdict again and
FR-013 keeps the upstream decision logic (the user's decision of 2026-09-27),
so it is a follow-up feature and the agent-facing reference states the weak
spots (T040). Gate 3 (T036) also measures requests of several hard questions.

Rationale: medium gave the fewest wrong answers and the fewest confident ones,
still showed thinking, and stayed far inside the 80 s endpoint budget.

Alternatives considered: keeping the thinking switch (more errors and
malformed answers, and wrong answers even under three agreeing asks); `xhigh`
or `high` (more errors, slower); `low` (cheapest, but more errors, including a
Score); GLM 5.3 Flash (less reliable; the user excluded it on 2026-09-27);
agreement voting now (a spec change that doubles provider calls).

## Testing layers — 2026-09-26

Superseded in part on 2026-09-27 by [Python package](#python-package--2026-09-27): all offline suites are pytest; the fidelity suite feeds scripted answers through a test-only judge.

Decision: offline tests run in `deno task check` without network access.
`deno test` drives the real server over MCP stdio, with the real endpoint in
front of a scripted fake OpenAI-compatible provider, and covers the MCP
boundary, records, cancellation and its race, client death, sessions, the
record budget and privacy. The deadline tests wait out the real 118 s limit, so
they run in `deno task test:backfire-slow`, which CI and the completion check
of every task run, and not in `deno task check`. A tool-fidelity suite compares the
server's tool list and its results on the known-answer arguments with
fixtures captured once from `jev-mcp` 0.9.0 on Node against the same scripted
endpoint. pytest, through `uv run --frozen`, covers the endpoint: validation,
the Score boundaries, fault classification and retries, the endpoint deadline,
token checks and the `X-Judgment-Metadata` header. Live acceptance against the selected provider runs
on demand through a separate task and covers readiness, the known-answer set in
both clients, the 60-item classification, the benchmark, the safety and
held-out sets, digests and the credential scan.

Rationale: constitution V requires positive, negative and boundary cases with
synthetic fixtures; repository checks must not depend on a paid external
service or on Node; the spec leaves live installation to the user's separate
go-ahead. Captured upstream fixtures prove that the recorded changes kept the
tools' behavior.

Alternatives considered: live calls inside `deno task check` (cost, flakiness,
credentials in CI); running `jev-mcp` on Node in every check (adds Node to CI
for a comparison that fixed fixtures already make); mocking the tools (would
not prove the real tool path that FR-001 requires).
