# Feature Specification: Jev-Style Decision Backend for the Code Plugin

**Feature Branch**: `feature/005-backfire-mcp`

**Created**: 2026-09-26

**Status**: Draft. Planned on 2026-09-26, revised the same day and on
2026-09-27; not yet implemented.

**Input**: On 2026-09-26 the user decided to adopt a Jev-style decision backend
for verbose-broccoli-code. Agents get typed judgments (a yes probability for
Noul questions; a probability for every option and a confidence value for
Choice and Score questions, plus the selected option for Choice and a
probability-weighted score for Score) through the tools of the
upstream MIT package `@jkudish/jev-mcp`, without a TypeSafe account. DeepSeek V4.1 Flash with thinking
mode on Hive's OpenAI-compatible API answers every judgment, driven by
TypeSafe's MIT `system-one-adapter` behind a local endpoint that speaks Jev's
System One contract. The user rejected the faster token-probability mode and
subscription (OAuth) routes, and removed the programming-language and runtime
restriction (constitution 0.16.0). Scope is the code plugin; the work and chat
plugins are out of scope. API keys stay outside the repository.

## Clarifications

### Session 2026-09-26

- Q: When should the feature count one of the eleven judgment tools as
  supported? → A: Only when its normal, boundary and failure cases pass through
  the real tool path in both Codex CLI and Claude Code, on the runtime the tools
  run on (first the upstream package's Node 22 or later; Deno 2.9.6 since the
  plan revision below; Python 3.14.4 since 2026-09-27); for `backfire_extract` the cases
  include Korean text returned exactly as written, no candidates, an invalid
  pattern and a pattern timeout; the feature is not done while any tool has a
  known failure.
- Q: Besides overall accuracy, what pass/fail bar should prove the tools don't
  wrongly auto-approve work? → A: A fixed safety set (failed tests, unsupported
  completion claims, truncated evidence, answers the user later corrected,
  observations about a different student, summaries with content not in the
  source) gets zero automatic approvals; on a general set, at least 97% of
  automatic decisions are correct, at least 70% of cases are decided
  automatically, and every tool and each of English and Korean is at least 90%
  correct; the 111 benchmark decisions stay a regression check while final
  acceptance uses a held-out set written before implementation and not used
  during development; dataset versions and the calibration formula are fixed,
  each evaluation runs three times, every run must pass, and failed responses
  count as wrong.
- Q: When the model's probabilities don't add up to 1, what should the backend
  do with them? → A: Never rescale; probabilities that sum to one within 0.01
  pass unchanged, and anything else (a larger deviation, a missing option, a
  value outside zero to one, or a placeholder such as 0.5) is a response error,
  not a judgment; confidence comes only from the returned probabilities through
  TypeSafe's published formula; matching Jev's format does not mean matching
  Jev's trained calibration.
- Q: What should the spec promise the gate does, and what should it say the
  gate does not do? → A: The tools are advisory: nothing makes agents call them
  or follow their verdicts, and the gate judges only supplied text and never
  proves that tests ran; each verdict is recorded with a digest of exactly the
  input it judged, including uncommitted changes, so it cannot carry over to
  changed code, requirements or evidence; recording real test runs and
  enforcement are a follow-up feature.
- Q: Should the spec adopt the review's remaining recommendations on output
  limits, failures and retries, sessions, readiness and versions, data, and
  speed, as written? → A: Yes, all six: never drop candidates, questions or
  answer fields to fit output limits, and never split one choice into smaller
  choices without its own quality check; retry only network errors and rate
  limits, in one layer, at most four attempts in total including the first,
  within a 120-second limit covering waiting, retries and split requests, while
  credential, balance and unsupported-setting errors fail at once and valid
  low-confidence or negative verdicts are never re-asked; concurrent sessions
  do not conflict, crashes leave nothing running, and cancellation reaches
  queued, retrying and in-flight requests; readiness separates requested from
  confirmed facts and records tested versions; only needed content is sent, no
  keys or personal identifiers stay in records or logs, raw-request saving is
  opt-in with a retention period, and a screening pass never authorizes
  following instructions; response times are tracked goals, not pass/fail
  conditions.
- Q (during planning): `backfire_find`, `backfire_rerank` and `backfire_decide` never mark a
  result as final without review; what should the automatic-decision rate in
  SC-010 divide by? → A: Only the cases of tools that can mark a result
  automatic; the 70% target stays.
- Q (during plan revision): Should the backend move to npm packages running in
  Deno? → A: No. TypeSafe's official Python `system-one-adapter` stays behind
  the local System One endpoint. The only npm port, by another author, has a
  GitHub dependency that Deno refuses to install, and a backend of our own would
  reimplement the adapter.
- Q (during plan revision): How does the code plugin provide the tools, given
  that `@jkudish/jev-mcp` is nine days old, released 0.8.0 and 0.9.0 about 26
  hours apart, and its `jev_extract` fails under Deno? → A: With its own MCP
  server on the official TypeScript MCP SDK, running on Deno 2.9.6 with npm
  dependencies declared in its Deno configuration. The server copies jev-mcp
  0.9.0's tool definitions and decision logic (`src/index.ts` and `src/lib.ts`
  at revision `a1fcc1e47fc696614f081e23a66ff48a890f22fd`, MIT) with minimal
  recorded changes: the regex worker loads its module with `require` so it runs
  under Deno, and the entry point uses the plugin's own session handling. A
  small transport to the local endpoint replaces the provider layer
  (`src/provider.ts` and `@jkudish/jev-agent-tools`), and `@typesafe-ai/sdk`
  still supplies the question builders. Arguments and results stay those of
  jev-mcp 0.9.0 (names: next clarification), and the npm package is not a
  runtime dependency. (Superseded on 2026-09-27: backfire is one Python
  package; see Session 2026-09-27.)
- Q (during plan revision): What should the MCP server and its tools be called?
  → A: The server is `backfire`, and the eleven tools use the `backfire_`
  prefix with the upstream suffixes (formerly `jev_gate` and so on). The
  plugin's folder, command, configuration and record paths, tasks and skill use
  the same name.

### Session 2026-09-27

- Q: The model's judgment quality was already measured on JevBench and
  backfire sends the same requests to the same model; does acceptance still
  need the benchmark, safety, held-out and 60-item classification runs? → A:
  No. Acceptance checks function only: readiness, each tool once through the
  live provider, the server loading and answering in Codex CLI and Claude
  Code, and the offline tests. SC-001, SC-002, SC-004, SC-009 and SC-010 are
  dropped, SC-003 and SC-007 are narrowed, and the evaluation runner, metrics
  and evaluation sets are not built.
- Q: Where does the backfire code live, given constitution IX's
  `packages/<name>/src/` rule for MCP servers? → A: All backfire code,
  including its acceptance tooling, moves to `packages/backfire/`, with the
  evaluation fixtures staying under `scripts/backfire/fixtures/`. The
  repository keeps no `plugins/code/backfire/`; a build step copies the
  component into the code plugin for distribution.
- Q: Should Hive be built into the backend? → A: No. Provider-specific settings
  live in provider profiles, and the backend's code names no provider. The Hive
  profile with DeepSeek V4.1 Flash ships with the feature and stays the
  selected backend; another OpenAI-compatible provider needs only a new
  profile.
- Q: How are provider profiles organized? → A: One `config.toml` holding a
  `[providers.<name>]` table per provider (first one TOML file per provider,
  replaced the same day), each with only that provider's own
  characteristics. The operator's own `config.toml` selects a provider and
  may add or replace provider tables. Protocol compatibility
  stays with the reused adapter and SDK and is not duplicated: a profile's
  `api` key names the adapter provider class (`openai` now; `anthropic`
  reserved and not supported yet), and standard status meanings come from
  the SDK, so a profile lists only the statuses whose meaning differs.
- Q: Should backfire keep two runtimes, a TypeScript copy of the tools plus a
  Python endpoint for the adapter? → A: No. backfire is one Python package:
  the MCP server on the official Python SDK, the eleven tools ported from
  `jev-mcp` 0.9.0, and judgments made in the same process by
  `system-one-adapter`. TypeSafe publishes the adapter only in Python, so
  the tools are ported rather than the adapter rewritten.
- Q: Which pattern language should the ported `backfire_extract` accept?
  → A: Python's `re`; its argument description says so, and patterns whose
  meaning differs from JavaScript are documented, not emulated.
- Q: Which reasoning setting should the shipped Hive profile request? → A:
  `reasoning_effort = "medium"` instead of the thinking switch
  `chat_template_kwargs: {"thinking": true}`. In repeated strict-mode runs of
  the JevBench public hard tier it gave the fewest wrong answers, still
  carried thinking evidence, and kept every call within the endpoint's 80 s
  budget (research.md, "Judgment quality probes").
- Q: Should a judgment be asked twice and count only when both answers
  agree, the one measure that stopped confident wrong answers in those runs?
  → A: Not in this feature. FR-007 (a valid verdict is never requested again)
  and FR-013 (upstream decision logic unchanged) stand; agreement voting is a
  follow-up feature, and the agent-facing documentation states the weakness.

## User Scenarios & Testing _(mandatory)_

All stories share one backend. User Story 1 establishes it; User Stories 2 and
3 are independently testable once it exists.

### User Story 1 - Gate a completion claim with a typed judgment (Priority: P1)

As the operator, I want an agent that finishes a code change to call the
`backfire_gate` tool (upstream `jev_gate`), one representative of the upstream
tools, which
scores a patch against the request and checks
completion claims against supplied evidence, so that unsupported "done" claims
and risky patches are flagged with probabilities and the tool's action (`auto`,
`review` or `escalate`) before I read the change. This feature adds no tool or
workflow of its own; the gate's questions and actions are the upstream tool's.
The gate is advisory: nothing makes an agent call it or follow its verdict, and
it judges only the text it receives, so it never proves that tests ran.

**Why this priority**: Cheap, structured first-pass checks before human or
reviewer-agent review are the reason to adopt the backend. This story exercises
the whole path from client to answer and delivers value on its own.

**Independent Test**: In Codex CLI and in Claude Code, each with only the code
plugin installed, call `backfire_gate` on a synthetic incomplete rename with one
supported and one contradicted claim. The action is `review` or `escalate`,
the claims' top verdicts are verified and contradicted, and the result names
the answering model.

**Acceptance Scenarios**:

1. **Given** the code plugin is installed and the operator's credential is
   configured, **When** an agent calls `backfire_gate` with a patch, test output and
   completion claims, **Then** it receives a probability distribution for each
   review rubric and each claim verdict, the tool's action and the answering
   model's identity.
2. **Given** a claim that the supplied evidence contradicts, **When** the agent
   calls `backfire_gate`, **Then** that claim's top verdict is contradicted and the
   action is `review` or `escalate`, not `auto`.
3. **Given** a typical single-question judgment, **When** it runs, **Then** its
   response time is recorded against the tracked goals in SC-002.
4. **Given** a fresh client session in which the operator started nothing else,
   **When** an agent calls a judgment tool, **Then** the backend starts with the
   session and answers, and it stops when the session ends.
5. **Given** a recorded gate verdict, **When** the code, the request or the
   evidence changes and the agent calls the gate again, **Then** the new verdict
   is recorded with a different input digest, and the earlier verdict's digest
   no longer matches the current input.

---

### User Story 2 - Use every judgment tool on real content (Priority: P2)

As the operator, I want agents to classify items, rank or find candidates,
screen external text for injected instructions, compare passages, judge
propositions, verify claims, pick extracted field values and decide between
bounded options, in English and Korean, with the same typed answers.

**Why this priority**: These tools cover routine structured decisions such as
triage, search and safety screening that otherwise consume model context. They
reuse the backend from User Story 1.

**Independent Test**: In both clients, run a versioned known-answer set of
synthetic cases, fixed before measurement with one expected result per case,
that gives every upstream tool normal, boundary and failure cases through the
real tool path, including a Korean classification, a 30-candidate search, a
prompt-injection sample and the field-extraction cases in scenario 6. Every
case returns its expected result.

**Acceptance Scenarios**:

1. **Given** 30 or more candidates, **When** an agent ranks them for a query,
   **Then** the relevant candidate ranks first and every candidate receives a
   probability.
2. **Given** Korean messages and a class catalog, **When** an agent classifies
   them, **Then** each message receives the expected class with a probability
   distribution.
3. **Given** text that contains instructions aimed at an AI agent, **When** an
   agent screens it, **Then** the result recommends blocking or review, and
   harmless text passes.
4. **Given** a document and candidate values matched by a pattern, **When** an
   agent extracts a field, **Then** the intended value is chosen.
5. **Given** a request at an upstream tool's maximum size (for example 64 items
   or propositions in one call), **When** an agent sends it, **Then** it
   completes within the tool's deadline or fails explicitly, never partially.
6. **Given** `backfire_extract` with Korean source text, with no matching
   candidates, with an invalid pattern, or with a pattern that exceeds its time
   limit, **When** an agent calls it, **Then** it returns the Korean value
   exactly as written, reports that nothing was found, rejects the pattern, or
   stops the pattern with an explicit timeout, respectively.

---

### User Story 3 - Fail closed and stay observable (Priority: P3)

As the operator, I want judgment failures to be explicit and diagnosable, so
that an unavailable, misconfigured, rate-limited, slow or misbehaving backend
never produces a fabricated judgment, and I can confirm readiness with one
check.

**Why this priority**: A wrong judgment presented as valid is worse than none.
The backend depends on an external paid service with rate limits and variable
response times.

**Independent Test**: Inject a missing credential, an insufficient-balance
response, an unreachable service, rate limiting, truncated, malformed, refused
and all-zero output, a response slower than the limit, a cancelled call and a
crashed agent session. Every affected call fails with an explicit reason and no
answer, other sessions keep working, nothing is left running, and the readiness
check reports either success or the specific failure.

**Acceptance Scenarios**:

1. **Given** no credential is configured, **When** a tool is called, **Then** it
   fails with a message that names the missing configuration, and no request
   content is logged.
2. **Given** the service returns network errors or rate limits, **When** a tool
   is called, **Then** the backend makes at most four attempts in total,
   including the first, and answers or fails explicitly within the 120-second
   limit; **given** a credential, insufficient-balance or unsupported-setting
   error instead, **Then** the call fails at once without repeating the
   request.
3. **Given** model output that is truncated, malformed, refused, missing an
   option, zero for every option or has probabilities that do not sum to one
   within 0.01, **When** the backend receives it, **Then** the call fails and
   no default option is chosen.
4. **Given** a working configuration with only the operator's Hive credential
   and no TypeSafe credential, **When** the operator runs the readiness check,
   **Then** it reports the requested provider (Hive), model (DeepSeek V4.1
   Flash) and thinking mode (on) separately from what the provider's response
   confirms, lists each unconfirmed item with its reason, shows which tool
   checks passed, and gives one sample judgment and its response time.
5. **Given** the selected model, provider route or thinking mode is
   unavailable, **When** a tool is called, **Then** the call fails and does not
   switch to another model, route or mode.
6. **Given** agents in two Orca tabs are using the tools, **When** one tab
   closes or its agent crashes, **Then** the other tab keeps working and no
   process or request from the closed session remains.
7. **Given** a tool call in progress, **When** the agent cancels it, **Then**
   the backend stops that call's queued, retrying and in-flight requests and
   discards any answer that arrives afterwards; charges already incurred at
   the provider are not guaranteed to be cancelled.
8. **Given** a valid verdict with low confidence, a negative outcome or too
   little evidence, **When** the backend receives it, **Then** it returns that
   verdict as final and does not ask again for a different one.

---

### Edge Cases

- A long thinking phase exhausts the output budget, or the service cuts output
  at a default limit while reporting a normal finish: the call fails instead of
  parsing partial text.
- A Choice question with up to 250 options, or up to 250 questions in one
  request, both within the upstream tools' limits: the backend answers
  completely or fails with an explicit limit error.
- A state at an upstream tool's input cap (for example a 50,000-character
  patch): the backend answers within the deadline or fails explicitly.
- Probabilities that sum to one within 0.01 pass unchanged; a larger
  deviation, an all-zero distribution, a missing label or a placeholder value
  fails as a response error.
- State text that tries to instruct the model is treated as data and does not
  redirect the judgment.
- Several sessions and split requests share one provider account limit (for
  Hive, five requests per second by default, per its documentation): rate
  limits are handled by the single retry layer, and answers never mix between
  requests.
- A request is too large for the output limit: independent questions may be
  split across requests as long as each answer keeps its question, but
  candidates, questions and required answer fields are never dropped, and one
  Choice is never split into smaller choices without its own quality check.
- Screened text passes screening yet still contains instructions: the pass does
  not authorize following them, and the gate's separation of input fields is an
  instruction to the model, not enforced isolation.
- The service changes the model behind a name: results keep reporting the
  identifier the service returned, and the configured identifier is pinned.
- The network drops during a request: the call fails explicitly.
- A tool gets valid answers from the backend but fails in its own runtime, as
  upstream `jev_extract` did under Deno: the tool is unsupported until its real-path
  cases pass.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The code plugin MUST make the eleven tools of `@jkudish/jev-mcp`
  0.9.0 available to agents in Codex CLI and Claude Code, with the code plugin
  installed alone and without a TypeSafe account: `backfire_gate`, `backfire_review`,
  `backfire_verify`, `backfire_noul`, `backfire_classify`, `backfire_find`, `backfire_rerank`,
  `backfire_compare`, `backfire_screen`, `backfire_extract` and `backfire_decide`, with that
  release's arguments and results under the `backfire_` names (release 0.9.0
  uses the `jev_` prefix), except that `backfire_extract`'s patterns are
  Python regular expressions. The plugin serves them from its own MCP server,
  a Python package, with that release's tool definitions and decision logic
  ported from the revision recorded in the Clarifications; the port differs
  from the release only at the points recorded in the plan's research
  ("Python package"), and the npm package is not a runtime dependency.
  Adopting a later upstream revision is an explicit upgrade under FR-012. A tool
  counts as supported only when its normal, boundary and failure cases pass
  through the real tool path in both clients on that runtime. The feature is not
  complete while any tool has a known failure.
- **FR-002**: Every judgment MUST come from the user-selected backend: DeepSeek
  V4.1 Flash with thinking mode through Hive, configured as the selected
  provider profile (FR-019). The feature MUST NOT switch silently to another
  model, provider, thinking-disabled or token-probability mode, or
  subscription sign-in route.
- **FR-003**: The backend MUST accept the Jev System One request contract (a
  state and named Noul, Choice and Score questions with their criteria) and
  return answers in the same contract: a yes probability for each Noul
  question, with the no probability being one minus it and, as in Jev's
  contract, no separate confidence value; for each Choice question, the selected option, a probability for
  every declared option summing to one and a confidence value; for each Score
  question, a probability for every declared level summing to one, the
  probability-weighted score over the level indices and a confidence value;
  and input and output token counts. The upstream tools MUST accept these
  answers without modification.
- **FR-004**: Each result MUST identify the model that produced it.
- **FR-005**: Requests within the upstream tools' documented limits MUST be
  answered completely or fail explicitly; a partial answer set MUST NOT be
  returned.
- **FR-006**: When no valid answer can be produced, including a missing or
  invalid credential, an unreachable service, exhausted retries, a timeout, a
  refusal, truncated or malformed output, a missing label, an all-zero
  distribution or probabilities that do not sum to one within 0.01, the call
  MUST fail with an explicit reason and MUST NOT return a default or
  fabricated answer.
- **FR-007**: Every tool call MUST answer or fail within 120 seconds, a limit
  that covers waiting, retries and split requests. Only network errors and rate
  limits MAY be retried, in exactly one layer, with at most four attempts in
  total including the first. Credential errors, insufficient balance and
  unsupported settings MUST fail at once, classified by the selected
  provider's documented responses as its profile records them (for Hive, 405
  for insufficient balance) rather than by generic status codes. A valid
  verdict with low confidence, a negative outcome or too
  little evidence is final and MUST NOT be requested again.
- **FR-008**: The backend MUST NOT rescale probabilities. Probabilities that
  sum to one within 0.01 pass unchanged; a larger deviation, a missing option
  or level, a value outside zero to one, or a placeholder value is a response
  error, not a judgment. A placeholder is a value supplied in place of missing
  or unusable model output, such as a default option chosen for an all-zero
  distribution; a probability the model actually returned, including 0.5, is a
  judgment. Confidence values MUST be computed from the returned
  probabilities by TypeSafe's published formula and MUST NOT be filled in any
  other way.
- **FR-009**: Credentials MUST stay outside the repository and the plugin
  package, supplied by the operator per machine. Only the content a judgment
  needs MUST be sent to the service. Committed files, verdict records, logs,
  error messages the backend produces and reports MUST NOT contain
  credentials, authentication headers, personal identifiers or request
  content; results that the tools return to the calling agent, as the upstream
  release defines them, may repeat that agent's own input. This feature keeps no raw-request
  archive. A later archive for debugging MUST be off by default, MUST NOT hold
  credentials or authentication headers, and MUST delete each saved request
  after seven days.
- **FR-010**: The backend MUST start when a client's tool session needs it and
  stop with that session; the operator MUST NOT have to start or keep a
  separate service running. Several sessions, including several Orca tabs,
  MUST work at once without conflict, and closing one MUST leave the others
  working. When an agent exits abnormally, no child process or pending request
  MUST remain. Cancelling a tool call MUST stop that call's queued, retrying and
  in-flight requests and discard answers that arrive afterwards.
- **FR-011**: The operator MUST be able to run one documented readiness check,
  a command or a tool call, that performs one real judgment and reports
  separately the requested provider, model and thinking mode; what the
  provider's response confirms; each item it could not confirm, with the
  reason; and which
  tool checks passed, with the answer and its response time. Thinking mode
  counts as confirmed only when the response carries evidence of it.
- **FR-012**: Every external component (the upstream revision the tools are
  copied from, the libraries and SDKs, the adapter library, the model identifier
  and the service endpoint) MUST be pinned to an exact version or identifier; an upgrade is an explicit change followed by re-verification. The
  tested versions of every component, runtime and prompt MUST be recorded, and
  the compatibility checks MUST pass again after any update.
- **FR-013**: The feature MUST keep the upstream tools' question design and
  decision logic, ported with only the recorded differences and checked
  against results captured from the upstream release, and MUST reuse the
  upstream adapter's answer conversion without reimplementing it. Other locally
  owned code is limited to integration glue; service-specific settings are
  provider profiles (FR-019).
- **FR-014**: The code plugin's documentation MUST state which content the tools
  send to the external service, and no instruction may direct agents to send
  credentials or private personal records to the tools.
- **FR-015**: The work and chat plugins MUST NOT gain these tools or depend on
  the backend.
- **FR-016**: The backend MUST record each verdict locally with a digest of
  exactly the input it judged, including patches with uncommitted changes, the
  claims, the evidence and the test text; the record MUST NOT contain the input
  itself. A changed input MUST produce a different digest.
- **FR-017**: The code plugin's documentation MUST state that the tools are
  advisory, that nothing makes agents call them or follow their verdicts, that
  a gate verdict judges only the supplied text and does not prove that tests
  ran, and that a screening pass never authorizes following instructions found
  in the screened text.
- **FR-018**: To fit an output limit, the backend MUST NOT drop candidates,
  questions or required answer fields. Independent questions MAY be split
  across requests only if each answer keeps its question; a single Choice MUST
  NOT be replaced by several smaller choices unless that method passes its own
  quality checks.
- **FR-019**: Every provider-specific setting MUST come from a provider
  profile: the protocol client to use, the service endpoint, the model
  identifier, the credential's name, the request fields it needs beyond the
  standard protocol (including the thinking switch and the output budget),
  the response fields that show thinking ran, the status codes whose meaning
  differs from the standard one, and its documented rate limit. Protocol
  handling that the reused adapter and SDK provide MUST NOT be restated in
  profiles. The backend's code MUST NOT name a provider. Supporting another
  provider whose API the adapter supports MUST need only a new profile and its
  selection, not a code change, as long as its departures from the standard
  protocol are ones a profile states. The Hive profile ships with the feature and is selected
  when the operator selects no other profile.

### Key Entities _(include if feature involves data)_

- **Judgment request**: a state (text or structured data) and named questions,
  each Noul, Choice or Score, with instructions and criteria or options.
- **Judgment answer**: per question, a yes probability (Noul), or a
  distribution over options or levels with a confidence value, plus the
  selected option (Choice) or the probability-weighted score (Score).
- **Tool result**: the upstream tool's combination of answers into verdicts,
  scores and an action (automatic, review or escalate), with token usage and
  the answering model.
- **Provider profile**: one provider's service endpoint, model identifier,
  credential name, request options, thinking evidence and status meanings
  (FR-019).
- **Backend configuration**: the selected provider profile, a reference to the
  operator's credential outside the repository, and the retry and deadline
  limits.
- **Readiness report**: the requested provider, model and thinking mode; what
  the provider's response confirmed; unconfirmed items with reasons; the tool checks
  that passed; and one sample answer with its response time.
- **Verdict record**: a local entry per tool call with the calling tool, the
  digest of the input the agent submitted, the result's fixed-vocabulary
  decisions, the answering model and the time, without the input's content or
  any identifier the caller supplied.
- **Raw-request archive**: a debugging store of request content that this
  feature does not provide; FR-009 constrains any later one.
- **Automatic decision**: a tool result that the upstream tool marks as final
  without review, such as the action `auto` or a screening result of `pass` or
  `block`. An **automatic approval** is an automatic decision that accepts a
  patch, claim or piece of content.
- **Evaluation sets**: versioned synthetic sets fixed before measurement: the
  benchmark regression set (JevBench's 111 public hard decisions), the safety
  set of cases that must never be approved automatically, and the held-out
  general set written before implementation and not used during development.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: As a regression check on JevBench's frozen public hard tier (111
  decisions, unchanged since JevBench v1.2), the backend answers at least 105
  correctly, with no invalid answer and an expected calibration error of at
  most 0.08, computed over ten equal-width bins of the chosen option's
  probability. The check runs three times, every run must pass, and a failed
  response counts as wrong. (Dropped on 2026-09-27 by the user's decision: acceptance checks function only; see Clarifications.)
- **SC-002**: Tracked goal, not a pass/fail condition: over those 111
  single-question judgments, measured from the operator's machine, the median
  response time is at most 5 seconds and 95% finish within 20 seconds. (Dropped on 2026-09-27 by the user's decision: acceptance checks function only; see Clarifications.)
- **SC-003**: With a code plugin built and installed outside the repository,
  the readiness check passes, each of the eleven tools returns the expected
  result for its normal known-answer case through the live provider, and in
  each of Codex CLI and Claude Code the staged `backfire` server loads and
  answers a tool call. Every answer the judge accepts satisfies the FR-003
  contract, which the judge checks before any tool receives it: all declared
  labels present, probabilities between zero and one summing to one within
  0.01, a yes probability for each Noul answer, the selected option and
  confidence for each Choice answer, and the score and confidence for each
  Score answer. (Narrowed on 2026-09-27 from the full known-answer set in both
  clients by the user's decision; see Clarifications.)
- **SC-004**: A 60-question classification request completes correctly within
  the 120-second limit; completing within 60 seconds is a tracked goal, not a
  pass/fail condition. (Dropped on 2026-09-27 by the user's decision: acceptance checks function only; see Clarifications.)
- **SC-005**: Under each injected fault from User Story 3, 100% of calls fail
  with an explicit reason and none returns a judgment.
- **SC-006**: A scan of the repository and the plugin package finds no
  credential, and the acceptance-run logs contain no credential or request
  content. (The separate scan task was dropped on 2026-09-27 by the user's
  decision; the offline tests keep credentials and request content out of
  records, logs and errors.)
- **SC-007**: On a machine where the selected provider's API key and the
  required runtimes are already installed, the operator can enable the feature
  and pass the readiness check by following the documented steps. (The
  10-minute timing was dropped on 2026-09-27 by the user's decision.)
- **SC-008**: At acceptance, every external component is identified by an
  exact version or identifier, and only the code plugin exposes the judgment
  tools.
- **SC-009**: On the safety set (failed tests, unsupported completion claims,
  truncated evidence, answers the user later corrected, observations about a
  different student, summaries with content not in the source), zero cases are
  approved automatically, in each of three runs. (Dropped on 2026-09-27 by the user's decision: acceptance checks function only; see Clarifications.)
- **SC-010**: On the held-out general set, in each of three runs, at least 97%
  of automatic decisions are correct, at least 70% of the cases for tools that
  can mark a result automatic are decided automatically, and every tool and
  each of English and Korean is at least 90% correct; a failed response counts
  as wrong. (Dropped on 2026-09-27 by the user's decision: acceptance checks function only; see Clarifications.) The sealed held-out set stays unused.
- **SC-011**: For every tool call in the acceptance runs, including split
  requests, the verdict record's digest matches the digest of the submitted
  input, and changing any one field of that input produces a different digest.
- **SC-012**: The code plugin's documentation contains every statement that
  FR-014 and FR-017 require, and none of its instructions directs agents to
  send credentials or private personal records to the tools.

## Assumptions

- The operator already holds a Hive API key, and usage cost is not an
  acceptance criterion (user decision, 2026-09-26).
- Several seconds per judgment is acceptable: the user chose thinking mode over
  the faster token-probability mode, whose probabilities were overconfident in
  the same measurement.
- Tool inputs are code, patches, test output and documentation. Private
  personal records such as student data stay out; the work plugin, which owns
  them, is out of scope.
- Agents decide when to call the tools, and nothing enforces their verdicts.
  Enforcement, for example making verification-before-completion require the
  gate, and recording real test runs (commands, exit codes, log identifiers,
  and partial, full, not-run or cancelled states) are a follow-up feature.
- Wrong verdicts can be confident. In the 2026-09-27 probes most wrong answers
  carried a top probability of at least 0.9, so the upstream thresholds mark
  them automatic; judging a response that contains a small arithmetic error
  and multi-step lookups among distractors failed most often. Agreement
  voting across repeated or different-model judgments is a follow-up
  feature.
- The clients are Codex CLI and Claude Code opened in Orca (constitution IX).
  Installing into live client configurations requires the user's separate
  go-ahead.
- Constitution 0.18.0 permits any programming language and runtime. The
  constitution's statement that no new service is implied is respected: the
  user selected this backend explicitly, and it runs only with the tool
  session.
- The user accepted the numeric thresholds in this spec during the 2026-09-26
  clarification session. The seven-day retention in FR-009 is a proposed
  default for a later raw-request archive.
- The success thresholds rest on a 2026-09-26 measurement of the selected
  setup in a throwaway harness outside version control: 111/111 on the same
  benchmark tier with calibration error 0.042, a median of 3.4 seconds and a
  95th percentile of 14.8 seconds per single-question judgment, and a
  60-question request answered in 16.6 seconds. Final acceptance re-measures
  the integrated feature. Planning records the dependency limits that the
  harness found. The 128-token output cutoff seen on Hive is an observation
  from that test, not a documented service limit, until planning confirms its
  cause from the request values, API path, streaming mode and finish reason.
- Acceptance uses synthetic content only, including the external text and
  prompt-injection samples.
- The backend reproduces Jev's answer format, not Jev's trained calibration.
  How well its probabilities match reality was measured on the selected model
  by the 2026-09-26 harness and the 2026-09-27 JevBench probes (research.md);
  since 2026-09-27 the feature does not measure it again, by the user's
  decision.
