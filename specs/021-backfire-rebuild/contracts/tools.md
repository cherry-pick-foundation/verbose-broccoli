# Contract: Backfire's Tools

## Server identity

- `initialize` reports `serverInfo.name` = `backfire` and the `backfire`
  package version.
- The server is started with `backfire serve-mcp` over stdio; the plugins'
  `mcp.json` entries do not change.

## Tool list

`tools/list` returns exactly these tools, in this order:

| # | Name | Source |
| --- | --- | --- |
| 1 | `backfire_verify` | upstream `jev_verify` |
| 2 | `backfire_screen` | upstream `jev_screen` |
| 3 | `backfire_find` | upstream `jev_find` |
| 4 | `backfire_classify` | upstream `jev_classify` |
| 5 | `backfire_decide` | upstream `jev_decide` |
| 6 | `backfire_rerank` | upstream `jev_rerank` |
| 7 | `backfire_compare` | upstream `jev_compare` |
| 8 | `backfire_extract` | upstream `jev_extract` |
| 9 | `backfire_review` | upstream `jev_review` |
| 10 | `backfire_gate` | upstream `jev_gate` |
| 11 | `backfire_score` | upstream `jev_score` |
| 12 | `backfire_noul` | backfire (jev-mcp 0.9.0's Noul tool) |

For tools 1–11, each definition equals the upstream definition at
`fd6829c` except:

- `name`: `jev_` becomes `backfire_`;
- `description`: each whole-word upstream tool name `jev_<tool>` becomes
  `backfire_<tool>`; other text, including "Jev", is unchanged.

## Calls

For tools 1–11, argument handling, questions, decision logic, success
payloads, `isError` payloads and handler errors equal the upstream's, with
one mapping: a payload's top-level `tool` value `jev_<tool>` becomes
`backfire_<tool>`. Argument errors name the `backfire_` tool because the
parsers are compiled from the renamed definitions. Recorded upstream patches
(linear IDs, `regex` matching, off-loop work) do not change any payload for
inputs the upstream handles within its limits, except that some patterns
jev-mcp stops finish under `regex` (spec, Clarifications).

`backfire_noul` keeps its current definition (title, description, input
schema, `execution.taskSupport: forbidden`), its questions, its decision
logic and its result fields (`tool`, `model`, `provider`, `status`,
`results[{id, proposition, probability, label, auto}]`, `invalid` when
present, `thresholds.auto_accept`, `usage`). Its arguments are parsed and
its errors are reported by the same upstream framework as the other tools.

Success payloads carry `provider: "compatible"` when a judgment was asked
and `provider: "none"` when none was (upstream `frame`).

## Errors outside the tools

- A judgment failure's text is backfire's fixed `<type>: <message>` (for
  example `provider_unavailable: ...`), returned as the upstream returns any
  provider error.
- The boundary's `deadline_exceeded` and `record_write_failed` results and
  the 10 MiB session end are unchanged.
