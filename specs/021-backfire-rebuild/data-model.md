# Data Model: Backfire Rebuilt From jev-judge-mcp

No stored data changes. Backfire's records, profiles, credentials and
education mapping table keep their formats. The entities below are the
structures the rebuild adds or changes.

## Vendored file

One file under `packages/backfire/src/jev_judge_mcp/` or
`packages/backfire/tests/upstream/`.

| Field | Meaning |
| --- | --- |
| path | Path relative to the upstream repository root at `fd6829c` (for example `src/jev_judge_mcp/ids.py`, `tests/unit/test_ids.py`) |
| upstream SHA-256 | Hash of the file at the upstream revision |
| status | `unchanged` (bytes equal the upstream), `changed` (listed changes), or `added` (no upstream file) |
| changes | For `changed` and `added`: each change with its reason and the requirement it serves |

Rule: a vendored file whose bytes differ from its upstream hash MUST have
status `changed` with at least one change; an `unchanged` file MUST match
its hash. The hash test enforces both.

## Upstream record

`packages/backfire/src/jev_judge_mcp/UPSTREAM.md`: the upstream repository,
release, commit, license, the table of vendored files, the files deliberately
not taken, and the list of changes (see `contracts/upstream-record.md`). It
replaces `packages/backfire/src/backfire/UPSTREAM.md`.

## Tool registry

The ordered tuple that the server passes to the upstream `Toolset`:

1. The eleven upstream tools in the upstream's order (`verify`, `screen`,
   `find`, `classify`, `decide`, `rerank`, `compare`, `extract`, `review`,
   `gate`, `score`), each a renamed copy of the upstream `JevTool`.
2. `backfire_noul`, a `JevTool` defined in backfire.

Invariant: listed names equal dispatched names (one registry, as in the
upstream).

## Call context

Set by the server for each tool call before the tool runs, read by the
provider seam.

| Field | Meaning |
| --- | --- |
| deadline | Absolute event-loop time by which the call must end (the boundary's 118-second deadline) |
| record file | The session's `RecordFile`, or none when the server runs without records (tests) |

Lifetime: one tool call; tasks the call starts inherit it.

## Judgment result to evaluation

| `judge()` result field | Upstream `Evaluation` field |
| --- | --- |
| `answers` (JSON dumps of system-one-adapter answers) | `answers` |
| `usage.input_tokens`, `usage.output_tokens` | `usage` |
| `model` (the model the response confirmed) | `model` |
| none | `provider` = `compatible` |
| none | `request_id` = none |

## Tool-call record decisions

`backfire/decisions.py` keeps its fixed vocabulary per tool and reads the
rebuilt tools' result fields; `backfire_score` gains an entry. Record kinds
(`tool_call`, `judgment`), fields and storage rules are unchanged.
