# Upstream 0.9.0 capture

These are the unchanged `jev-mcp` results for every argument set in
`../known-answers-v1.jsonl`, captured from revision
`a1fcc1e47fc696614f081e23a66ff48a890f22fd` on Node. `metadata.json` records
the source hashes, Node and npm versions, commands, and input-set hash.

`tools-list.json` is the complete `tools/list` result. Each `cases.jsonl` row
contains the case `id`, upstream `tool` name, exact `arguments`, ordered
`judgments`, and either the MCP `result` or JSON-RPC `error`. Each judgment
contains the received `request` (`state` and `questions`) and the scripted
HTTP `response` (`status` and JSON `body`). Empty `judgments` means no endpoint
request occurred. Object insertion order and array order are preserved.

Answers are synthetic: first Choice with probability 1, Noul 0.875, and the
middle Score level with probability 1. They test fidelity, not semantic
accuracy against the known-answer expectations. A singleton Choice receives
HTTP 400 with `invalid_request`; its upstream error text is kept verbatim.

For T030 replay, pass each successful response body unchanged to the scripted
judge as a `{"result": body}` step. Map failed responses to the backend's
fixed error under recorded difference 2 in
`packages/backfire/src/backfire/UPSTREAM.md`.
Compare every captured request and result after the recorded name mappings
and differences; do not regenerate answers from the Python port's questions.

Regenerate from the repository root (network is needed for the pinned source
and npm packages):

```sh
PATH="$HOME/.local/share/mise/installs/node/24.19.0/bin:$PATH" \
  PYTHONDONTWRITEBYTECODE=1 \
  uv run --project packages/backfire --frozen --offline --no-sync \
  python -m backfire_tools.acceptance.capture_upstream
deno run --frozen --cached-only --no-prompt --allow-read --allow-env --allow-run \
  npm:@biomejs/biome@2.5.14 format --write \
  scripts/backfire/fixtures/upstream-0.9.0/metadata.json \
  scripts/backfire/fixtures/upstream-0.9.0/tools-list.json
```

The capture downloads a fresh source tree into a temporary directory, runs
`npm ci --ignore-scripts` and `npm run build` there, and starts
`node dist/index.js` with `JEV_PROVIDER=compatible` and
`JEV_MCP_MAX_ATTEMPTS=1`. Only the loopback scripted endpoint answers its
judgments. Source trees and child processes are cleaned up on exit; generated
fixtures are written only after the capture succeeds.
