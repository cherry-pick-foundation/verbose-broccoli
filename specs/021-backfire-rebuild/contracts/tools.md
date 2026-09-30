# Contract: Backfire's Server and Tools

## Server identity

- The server is PyModel's `JevMCPServer` from `jev-judge-mcp` 0.6.0. It
  reports PyModel's name (`jev-mcp`) and version, PyModel's instructions,
  and PyModel's packaged skill resources.
- Clients start it with `backfire serve-mcp` (code plugin) or
  `backfire serve-mcp --education` (work plugin), run from
  `packages/backfire`; the plugins list it under the key `backfire`.

## Tool list

`tools/list` returns PyModel's eleven tools in PyModel's order, unchanged,
then `jev_noul`:

`jev_verify`, `jev_screen`, `jev_find`, `jev_classify`, `jev_decide`,
`jev_rerank`, `jev_compare`, `jev_extract`, `jev_review`, `jev_gate`,
`jev_score`, `jev_noul`.

## Calls

- The eleven PyModel tools behave as PyModel 0.6.0's, because their code,
  argument handling and regex worker pool are PyModel's; backfire changes
  only which provider answers.
- `jev_noul` keeps jev-mcp 0.9.0's Noul definition (title, description,
  input schema without the `exclusiveMinimum` keyword, `execution`),
  questions, labels, invalid-answer handling and budget error; `auto_accept`
  must exceed 0.5, enforced by a PyModel `Refinement`. Its result is framed
  by PyModel's `frame`.
- Results report `provider` as the selected provider's name (PyModel's for
  Jev providers; `compatible` for the Hive profile, as backfire reports
  today) and `model` as the answering model.
