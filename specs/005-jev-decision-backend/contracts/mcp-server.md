# Code Plugin MCP Server Contract

## Declaration

`plugins/code/mcp.json` declares one stdio server:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "backfire": {
      "type": "stdio",
      "command": "sh",
      "args": ["${PLUGIN_ROOT}/backfire/src/bin/backfire", "serve-mcp"]
    }
  }
}
```

The entry carries no `env` values: Agent Plugins treats them as public package
data, and the credential is read from the operator's configuration instead
([configuration.md](configuration.md)). The work and chat plugins declare
nothing new. The repository's `plugins/code` holds this declaration but not the
component; the entry exists in a code plugin built as described in
[Distribution build](#distribution-build).

## Distribution build

`deno task backfire:build -- <output>` runs `packages/backfire/src/build.ts`,
which writes a complete code plugin to `<output>`:

- It refuses an existing `<output>` and any `<output>` inside `plugins/` or
  `packages/`.
- It writes into a new sibling directory, `<output>.partial-<random>`, and
  renames that directory to `<output>` only after every file is written.
- It copies `plugins/code/` unchanged to the partial directory, including that
  package's own files such as its tests.
- It copies these files of `packages/backfire/` to `backfire/` in the partial
  directory, keeping their relative paths: `deno.json`, `deno.lock`,
  `pyproject.toml`, `.python-version`, `uv.lock`, `src/bin/`,
  `src/upstream/`, `src/server/` except `*_test.ts` files and
  `src/server/testing/`, and `src/backfire_backend/` except `__pycache__/`.
- It copies file contents and never writes a link.
- Its storage budget is 16 MiB for the whole output, checked before each file
  is written; a copy that would pass it fails the build.
- On any failure, and on SIGINT or SIGTERM, it removes its own partial
  directory and exits non-zero; it never removes anything else. After success
  only `<output>` remains, and the caller owns it.

So Backfire's tests, test doubles, acceptance tooling, build and pytest suites
stay out of `<output>/backfire/`, while the rest of `<output>` equals
`plugins/code/`. The same relative layout lets `src/bin/backfire` run from
`packages/backfire/` during development and from `<output>/backfire/` in a
built plugin.

## Entry commands

`<plugin root>/backfire/src/bin/backfire <command>`, where `<plugin root>` is a
built or installed code plugin; in the repository the same commands run as
`packages/backfire/src/bin/backfire <command>`:

| Command | Effect |
| --- | --- |
| `serve-mcp` | Runs one session: the server on the caller's stdio, with its endpoint child |
| `install` | `uv sync --frozen` into this copy's own environment, using the interpreter pinned in the component's `.python-version`, and `deno install --frozen` of the component's lockfile into Deno's module cache; the only step that downloads |
| `ready` | Prints the readiness report ([readiness.md](readiness.md)) |

Each component copy has its own Python environment,
`$XDG_CACHE_HOME/verbose-broccoli/backfire/venv/<copy id>/`, where `<copy id>`
is the first 16 hexadecimal digits of the SHA-256 of the component root's
resolved absolute path. `install` sets uv's project environment to that path,
so the environment's editable `backfire_backend` points at this copy's
`src/backfire_backend/`, and installing or removing another copy never changes
it. Each environment records its component root in a `component-root` file, and
`install` first removes every environment under `venv/` whose recorded root no
longer exists, so environments never outlive their copies for long. Deno's
module cache holds only immutable, version-pinned npm packages and stays
shared.

`serve-mcp` and `ready` never download or sync packages: the server runs with
`--frozen --cached-only`, and the endpoint runs from this copy's environment.
If the environment or the cached modules are missing, they exit non-zero with a
message that names `<plugin root>/backfire/src/bin/backfire install`. The
repository's `deno task backfire:install` only calls
`packages/backfire/src/bin/backfire install`.

## Runtime requirements

- `deno` 2.9.6 at `~/.deno/bin/deno` or on `PATH`. `serve-mcp` checks the
  version before starting and exits with an explicit message when it differs.
- `uv` at `~/.local/bin/uv` or on `PATH`, and the Python interpreter pinned in
  `packages/backfire/.python-version`.

Agent Plugins 1.0 lets a client start the server with a reduced environment,
so the entry depends on no inherited variable. It sets `PATH` to
`/usr/local/bin:/usr/bin:/bin` when it is unset, takes `HOME` from the account
database when it is unset, applies the XDG defaults of
[configuration.md](configuration.md), finds `deno` and `uv` in the places
above, and passes the resolved values to the server and the endpoint.

## Server composition

Paths are relative to the component root, `packages/backfire/` or
`<plugin root>/backfire/`.

- `src/upstream/` holds `jev-mcp`'s source at revision
  `a1fcc1e47fc696614f081e23a66ff48a890f22fd` (release 0.9.0, MIT) with its
  `package.json` and `LICENSE`. `src/upstream/upstream.json` records the
  source, the revision, each copied file's original SHA-256 and the diff of the
  seven recorded changes
  ([research.md](../research.md#tool-source-jev-mcp-090-copied--2026-09-26)).
  No other change is allowed; the repository's formatter and linter skip the
  directory.
- `src/server/` holds the locally owned server code: the entry with its MCP
  boundary, the endpoint child, records, decision units and readiness.
- The server's dependencies come only from the component's `deno.json` and
  `deno.lock` ([research.md](../research.md#server-runtime-and-dependencies--2026-09-26)).

## Session lifecycle

1. The server creates and locks its record file and applies the record budget.
2. It starts the endpoint: this copy's environment's Python runs
   `backfire_backend serve` with its standard input a pipe from the server and an
   environment of `PATH`, `HOME`, the XDG variables, `BACKFIRE_ENDPOINT_TOKEN`
   (a random session token) and, only when the server's own environment sets
   it, the test-only `BACKFIRE_TEST_PROVIDER_BASE_URL`
   ([provider-profile.md](provider-profile.md#test-only-override)). The endpoint binds a free `127.0.0.1` port,
   prints `{"port": <n>, "model": <model or null>}` on its standard output,
   and exits when its standard input ends. The provider credential never passes through the server.
3. It sets the transport's environment in its own process:
   - `JEV_PROVIDER=compatible`
   - `JEV_API_BASE_URL=http://127.0.0.1:<port>/v1/systemone`
   - `JEV_API_KEY=<session token>`
   - `JEV_MCP_MODEL=<model>`, the selected profile's model as the endpoint
     reports it with its port; unset when the endpoint reports none, in which
     case every judgment fails with `backend_not_configured`
   - `JEV_MCP_REQUEST_TIMEOUT_MS=82000`
   - `JEV_MCP_MAX_ATTEMPTS=1`

   Then it imports the copied tools and connects their server to the MCP
   SDK's stdio transport through the [MCP boundary](#mcp-boundary). Its own
   log goes to stderr and holds status codes, digests and timings only.
4. Shutdown starts when the client's input ends, a write to the client fails,
   the endpoint exits, a message exceeds 10 MiB, or the server receives
   SIGTERM or SIGINT. The server cancels its open calls, which aborts their
   endpoint requests, records them as `session_ended`, closes the endpoint's
   standard input, sends SIGTERM after 2 s and SIGKILL after 2 s more if the
   endpoint is still running, and exits.
5. Each client session runs its own server, endpoint, port, token and record
   file. Sessions share only the record directory, whose cleanup skips locked
   files, so closing one session leaves the others running.

## MCP boundary

- Messages are newline-delimited JSON-RPC, as MCP stdio specifies. The boundary
  sits between the SDK's stdio transport and the copied server, sees each
  message already parsed, and passes it on unchanged and in order, with the
  exceptions below. A message over 10 MiB closes the SDK's transport and ends
  the session.
- A client request with `method: "tools/call"` opens a call: its JSON-RPC id, a
  call number, the tool name (one of the eleven or `unknown`), the input digest,
  the start time and a deadline 118 s later.
- The server's response with the same id closes the call: the boundary writes
  the tool-call record ([data-model.md](../data-model.md#tool-call-record)),
  then sends the response. `result.isError` gives `tool_error`; a JSON-RPC
  `error`, including the SDK's argument validation, gives `protocol_error`;
  decisions come from `result.content[0].text` parsed as JSON.
- A client `notifications/cancelled` for an open call records it as
  `cancelled` and closes it for good: a response that still arrives for it is
  dropped, so no answer reaches the client after its cancellation.
- At a call's deadline the boundary delivers a cancellation for that call to
  the server, which aborts the tool's signal and its endpoint request, records
  the call as `deadline_exceeded`, closes it and answers the client with a tool
  result whose `isError` is true and whose text is the fixed
  `deadline_exceeded` message. The session keeps serving.
- If a tool-call record cannot be written, the boundary answers that call with
  the fixed tool error `record_write_failed` instead of its result.
- At shutdown, open calls are recorded as `session_ended`.

## Deadline

A tool call answers or fails within 120 s, in two layers:

- The endpoint answers within 80 s and the transport gives up at 82 s, so a
  call whose work before the judgment call is bounded fails with a specific
  error. The slowest such work is `backfire_extract` with 31 timed-out patterns and
  one matching one, about 31 s, which ends by about 113 s.
- The boundary's 118 s deadline catches everything else and answers
  `deadline_exceeded`. Its timer runs on the server's only thread, so no tool
  may block that thread for long; recorded change 4 removes the one known
  quadratic case, and a feasibility gate measures every tool's longest
  event-loop stall at the 10 MiB message limit.

The records' `duration_ms` lets acceptance check the bound for every call.

## Tool surface

The eleven tools of `jev-mcp` 0.9.0, renamed from `jev_` to `backfire_`
(recorded change 7), with that release's descriptions, input schemas and
results: `backfire_gate`, `backfire_review`, `backfire_verify`, `backfire_noul`,
`backfire_classify`, `backfire_find`, `backfire_rerank`, `backfire_compare`, `backfire_screen`,
`backfire_extract` and `backfire_decide`. The offline fidelity suite compares the tool
list and the results for the known-answer arguments with fixtures captured
from `jev-mcp` 0.9.0 on Node, after mapping `jev_` to `backfire_` and `jev-mcp`
to `backfire`. Adopting a later upstream revision is an explicit
change that recaptures the fixtures, reapplies the recorded changes, and
repeats the known-answer set in both clients (FR-012).

## Client registration for acceptance

Acceptance stages the code plugin alone by building it into a temporary
directory ([Distribution build](#distribution-build)), runs each client from a
working directory outside the repository, and registers only the staged
package's declared `backfire` server, with `${PLUGIN_ROOT}` replaced by the
staged path. The client writes its events as JSON Lines and keeps no session.
No saved client configuration changes.

- Claude Code (2.1.283):
  `claude -p --output-format stream-json --verbose --no-session-persistence --strict-mcp-config --mcp-config <file>`,
  where `<file>` holds the staged declaration.
- Codex CLI (0.157.0):
  `codex exec --json --ephemeral --skip-git-repo-check --ignore-user-config -c 'mcp_servers.backfire.command="sh"' -c 'mcp_servers.backfire.args=["<staged>/backfire/src/bin/backfire","serve-mcp"]'`;
  `--ignore-user-config` keeps other registered servers out while
  authentication still comes from `CODEX_HOME`, and `--skip-git-repo-check`
  allows a working directory outside Git.

Either registration may add an `env` entry that points `XDG_STATE_HOME` at the
run's own record directory. Installing the package through each client's plugin
mechanism, with skill discovery, belongs to a separate client-installation
feature, which installs a built code plugin; FR-001 and SC-008 close only after it passes for the code package with
`backfire` and the known-answer set passes through the installed package in
both clients. Installing into saved client configuration needs the user's
separate approval.
