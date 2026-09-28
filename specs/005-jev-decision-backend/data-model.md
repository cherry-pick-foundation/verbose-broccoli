# Data Model: Jev-Style Decision Backend

All entities are files or messages; there is no database. Field names follow
Jev's System One wire format where one exists.

## Digests

A digest is the lowercase hex SHA-256 of the RFC 8785 canonical JSON (UTF-8) of
a value. Any independent RFC 8785 implementation reproduces it.

- **Input digest**: over `{"tool": <name>, "arguments": <arguments>}` of one
  `tools/call` request, exactly as the client sent it (missing arguments count
  as `{}`). Any changed argument, including a patch with uncommitted changes, a
  claim, evidence, test text or a policy threshold, changes it.
- **Payload digest**: over `{model, state, questions}` for one judgment:
  `state` and `questions` as the tool sent them after its own truncation, and
  `model` as the model the judge took from the selected profile, or null when
  the judgment failed before a profile was loaded.
- **Result digest**: over the `result` object of one `tools/call` response.

## Judgment request

What a ported tool hands to the in-process judge ([judgment.md](contracts/judgment.md)).

| Field | Type | Rules |
| --- | --- | --- |
| `state` | string, JSON object or array | Passed to the adapter unchanged; size is bounded by each tool. |
| `questions` | object: id → question | At least one question. Ids are the tools' own keys; some embed caller ids. |

Question types:

- **Noul**: `instructions`; optional `criteria` with `true` and `false`
  descriptions. One answer cell.
- **Choice**: `instructions`; `criteria` maps each option label to its
  description. At least 2 options. One cell per option.
- **Score**: `instructions`; `criteria` is an ordered list of at least 2 level
  descriptions, lowest first; level indices start at 0. One cell per level.

Request size limits: a Choice may have at most 250 options and a request at
most 672 cells, as gate 3 measured on 2026-09-27
([research.md](research.md#gate-3-request-limits--2026-09-27)). A request over either fails with `request_limit_exceeded` before
any provider call. The adapter rejects unknown keys and malformed questions,
also before any provider call.

## Judgment answer

One per question, returned only when every question validates.

| Type | Fields | Rules |
| --- | --- | --- |
| Noul | `type: "noul"`, `noul` | `noul` is the yes probability in [0, 1]; the no probability is 1 − `noul`; no confidence field, as in Jev's contract. |
| Choice | `type: "choice"`, `choice`, `confidence`, `probabilities` | Exactly the declared labels; each value in [0, 1]; sum within `0.01 + 1e-12` of 1; not all zero; `choice` is a label with the highest probability; `confidence` from TypeSafe's formula over the returned probabilities. |
| Score | `type: "score"`, `score`, `confidence`, `probabilities`, `legend` | Exactly the declared level indices; each value in [0, 1]; sum within `0.01 + 1e-12` of 1; not all zero; `score` is the adapter's mean of the level indices, weighted by the returned probabilities divided by their total; `confidence` from TypeSafe's formula; `legend` maps each index to its description. |

Probabilities are never rescaled. An answer that breaks a rule is a response
error, not a judgment. A placeholder, meaning a value supplied in place of
missing or unusable model output, is never returned: the adapter's first-option
fallback for an all-zero Choice and its uniform score for an all-zero Score are
rejected. A probability the model actually returned, including 0.5, is a
judgment.

## Judgment response and error response

Success: `{model, answers, usage}` where `model` is the model name in the
provider's response for this request, passed through even when it differs from
the requested one, and `usage` holds integer `input_tokens` and
`output_tokens` from the provider's `prompt_tokens` and `completion_tokens`
(for Hive, completion includes reasoning). A provider response that carries
an answer but no non-empty `model` is `model_not_confirmed`, and one that
carries an answer but no usage is `malformed_output`; a response without an
answer is `provider_error` ([judgment.md](contracts/judgment.md#errors)).

Failure: an error whose text is `<type>: <message>`, with the types of
[judgment.md](contracts/judgment.md#errors). A message is fixed per type, names
the cause and the corrective action, and never includes request content,
provider or adapter error text, or credentials.

Every judgment, successful or failed, fills its call's judgment metadata:
`attempts` (provider attempts, including the first), `latency_ms` (from the
judge's start to its end), `thinking_evidence` (true when the provider's
response showed the thinking evidence the profile names, null without a
provider response) and `reasoning_tokens` (the value at the profile's
`thinking.token_path`, or null). It holds no other field and no text.

## Tool-call record

Written by the server's MCP boundary for each `tools/call` request, before its
response reaches the client. Together with the judgment records it links to,
it is the spec's verdict record.

| Field | Content |
| --- | --- |
| `kind` | `"tool_call"` |
| `time` | UTC time the call ended |
| `session` | Random session id |
| `call` | Sequence number of the call within the session |
| `tool` | One of the eleven tool names, or `unknown` |
| `input_digest` | Input digest |
| `outcome` | `ok`, `tool_error` (`result.isError`), `protocol_error` (a JSON-RPC error, such as malformed request parameters), `cancelled` (the client cancelled it), `deadline_exceeded` (still open 118 s after its request) or `session_ended` (open when the session shut down) |
| `decisions` | The result's decision units, by position ([below](#decision-units)); null without a parsable result |
| `result_digest` | Result digest, or null |
| `model` | The `model` field of the result, or null |
| `duration_ms` | From receiving the request to sending the response or ending the call |

## Judgment record

Written by the judge for each judgment a tool requests, before its result
reaches the tool. Direct judgments by the readiness check, the gate 3 probe and
the benchmark runner write no judgment record; those callers read the returned
judgment metadata ([judgment.md](contracts/judgment.md#request)).

| Field | Content |
| --- | --- |
| `kind` | `"judgment"` |
| `time` | UTC time the response, error or abort was observed |
| `session` | Random session id |
| `judgment` | Sequence number within the session |
| `calls_in_flight` | `call` numbers of the tool calls open when the request was sent; exactly one links the judgment to its call |
| `payload_digest` | Payload digest |
| `questions` | Per question, in request order: `{type, cells}` |
| `outcome` | `ok`, the judgment's error type, or `cancelled` (the call was cancelled by the client or at its deadline) |
| `results` | Per question, in request order: Noul `{p}`, Choice `{index, confidence}` (the position of the chosen label in the declared order), Score `{score, confidence}` |
| `model` | Model name the provider reported, or null |
| `thinking_evidence` | From the judgment metadata, or null |
| `usage` | Input and output tokens from the result, and reasoning tokens from the judgment metadata |
| `attempts` | From the judgment metadata, or null |
| `latency_ms` | From the judgment metadata, or null |

Neither record holds state, instructions, criteria, answer text, question ids,
option labels or any other caller-supplied identifier.

## Decision units

The fixed-vocabulary fields of each tool's result, one unit per claim, item,
field, proposition or aspect where the tool reports several. Records and the
evaluation runner share this table. A value outside the listed vocabulary is
stored as `other`; caller-supplied fields such as ids, labels, class names,
selected candidates and text are never read.

| Tool | Unit | Fields and vocabulary |
| --- | --- | --- |
| `backfire_gate`, `backfire_review` | The result | `action`: `auto`, `review`, `escalate`; `truncated`: boolean |
| `backfire_verify` | Each claim | `verdict`: `verified`, `contradicted`, `unsupported`, `unknown`; `action`: `auto`, `review` |
| `backfire_screen` | The result | `action` (from `recommendation`): `pass`, `review`, `block`, `skip` |
| `backfire_noul` | Each proposition | `label`: `likely`, `unlikely`, `uncertain` or null; `auto`: boolean |
| `backfire_extract` | Each field | `status`: `auto`, `review`, `not_found`, `invalid_pattern`, `invalid_response` |
| `backfire_compare` | Overall, then each aspect | `relation`: `same_fact`, `contradicts`, `different_facts` or null; `decision`: `auto`, `review` |
| `backfire_classify` | Each item | `decision`: `auto`, `review` |
| `backfire_decide` | The result | `escaped`: boolean or null |
| `backfire_find` | The result | `exists_verdict`: `answered`, `partial`, `absent` or null |
| `backfire_rerank` | The result | none beyond `status` |

Every unit also keeps the result's `status` (`ok`, `invalid_response`) when the
tool reports one.

## Record files

- One file per session under `$XDG_STATE_HOME/verbose-broccoli/backfire/records/`,
  named `<UTC start>-<session id>.jsonl`, created exclusively and held under an
  exclusive lock for the session's life. The session starts a new file at
  10 MiB. The server is the only writer.
- Every append holds an exclusive lock on `records/.lock` while it adds up the
  sizes of all record files. If the new line would take the total past 50 MiB,
  it deletes the oldest files whose own lock it can take (a locked file belongs
  to a live session); if the line still does not fit, the write fails. The
  directory never holds more than 50 MiB, including after sessions close or
  die.
- A record is one line ending in a newline. Readers ignore a final line without
  one, which is what an interrupted write leaves; no session ever appends to
  another session's file.
- If the directory cannot be created, locked or written at start, the session
  fails to start with a message naming the path. If a judgment record cannot be
  written, the judge fails that judgment, and the tool reports an error and no
  verdict. If a tool-call record cannot be written, the MCP boundary answers
  the call with the fixed tool error `record_write_failed` instead of its
  result, so no unrecorded verdict reaches the client.

## Backend configuration

| Item | Value | Source |
| --- | --- | --- |
| Provider profile | The `[providers.<name>]` table that the operator's `config.toml` selects, or else the one the shipped `config.toml` selects (`hive`) ([provider-profile.md](contracts/provider-profile.md)) | Operator or shipped default; changing it is an FR-012 upgrade |
| Protocol | The adapter provider class the profile's `api` names (Hive: `openai`, Chat Completions) | Profile |
| Endpoint | The profile's `base_url` (Hive: `https://api-cdn.thehive.ai/api/v3`) | Profile |
| Model | The profile's `model` (Hive: `deepseek-ai/deepseek-v4.1-flash`) | Profile; changing it is an FR-012 upgrade |
| Request additions | The profile's `request`, including the thinking switch and the output budget (Hive: `reasoning_effort: "medium"`, `response_format: {"type": "json_object"}`, `max_tokens: 32768`) | Profile |
| Thinking evidence | The profile's `thinking` fields (Hive: `reasoning_content`, `usage.reasoning_tokens`) | Profile |
| Status meanings | The SDK's standard error classes, with the profile's `statuses` overrides (Hive: 405 is `balance_exhausted`) | SDK and profile |
| Rate limit | The profile's `rate_limit_per_second` (Hive: 5); not enforced by the judge | Profile |
| Adapter | `structured_outputs=False`, `llm_answer_mode="probabilities"`, `normalize_probabilities=False`, `n_retry_malformed_structure=0` | Constant |
| Call deadline | 118 s after a call's request arrives, the MCP boundary answers `deadline_exceeded` and cancels the call; the judge's attempts and retry waits use only the time left | Constant |
| MCP message size | At most 10 MiB; a larger message ends the session | Constant |
| Attempts | At most 4, including the first, in the judge | Constant |
| Request limits | 250 options per Choice; 672 cells per request (gate 3) | Constant |
| Credential | The profile's `credential` variable in `$XDG_CONFIG_HOME/verbose-broccoli/backfire/<profile>.env` (Hive: `HIVE_API_KEY` in `hive.env`), mode 0600, read by the judge only | Operator |

## Session

One per client MCP session, served by one server process.

| Field | Content |
| --- | --- |
| `id` | Random id used in records |
| `calls` | Open tool calls: JSON-RPC id → call number, tool, input digest, start time and deadline |

States: `starting` → `serving` → `stopping` → `stopped`.

- `starting` → `serving`: the record file is locked.
- `serving` → `stopping`: the client's input ends or a write to the client
  fails, a message exceeds 10 MiB, or the server receives SIGTERM or SIGINT.
- `stopping` → `stopped`: open calls are cancelled, which cancels their
  provider requests and kills any pattern child, and recorded as
  `session_ended`; the record file is closed.
- A killed server skips these steps; open provider connections close with it,
  a pattern child ends at its own 1,000 ms timer, and the kernel releases the
  record file's lock.

## Request lifecycle

In the judge: `received` → `validated` → `provider attempt n` →
`answer validated` → `returned`.

- Invalid request or limit: `received` → failed, before any provider call.
- Retryable failure: `provider attempt n` → `provider attempt n+1` while
  attempts remain and the wait fits the time left.
- Final provider or answer failure: → failed with its error type.
- Cancellation at any point (by the client or at the call deadline): the
  provider call and any pending retry are cancelled and nothing is returned;
  the judgment record shows `cancelled`.

## Readiness report

Defined in [readiness.md](contracts/readiness.md): requested settings,
confirmed facts, unconfirmed items with reasons, tool checks, one sample
judgment with its latency, and the tested versions of every component, runtime
and the prompt.

## Evaluation case and run

Defined in [evaluation.md](contracts/evaluation.md). A case has an id, a set, a
tool, a language, tool arguments and an expected outcome (a result or an
explicit error). A run records the set version, run index, per-case outcomes,
metrics and digest checks.

## Relationships

- A session serves many tool calls. Each call has one tool-call record and zero
  or more judgments; with the eleven 0.9.0 tools, at most one.
- Each judgment has one judgment record. `calls_in_flight` links it to its call
  when exactly one call was open.
- An evaluation run reads one versioned set and produces one result per case.
