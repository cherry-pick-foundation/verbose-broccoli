# Code Plugin MCP Server Contract

The server is one Python package, `backfire`
([research.md](../research.md#python-package--2026-09-27)).

## Declaration

`plugins/code/mcp.json` declares one stdio server, started the standard way for
Python MCP servers:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "backfire": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory", "${PLUGIN_ROOT}/backfire",
        "run", "--frozen", "--offline", "--no-sync",
        "backfire", "serve-mcp"
      ]
    }
  }
}
```

The entry carries no `env` values: Agent Plugins treats them as public package
data, and the credential is read from the operator's configuration instead
([configuration.md](configuration.md)). `--no-sync` and `--offline` keep a
start from changing the environment or downloading anything. The work and chat
plugins declare nothing new. The repository's `plugins/code` holds this
declaration but not the component; the entry exists in a code plugin built as
described in [Distribution build](#distribution-build).

## Distribution build

`deno task backfire:build -- <output>` runs `python -m backfire_tools.build
<output>` in the component's environment, which writes a complete code plugin
to `<output>`:

- It refuses an existing `<output>` and any `<output>` inside `plugins/` or
  `packages/`.
- It writes into a new sibling directory, `<output>.partial-<random>`, and
  renames that directory to `<output>` only after every file is written.
- It copies `plugins/code/` unchanged to the partial directory, including that
  package's own files such as its tests.
- It copies these files of `packages/backfire/` to `backfire/` in the partial
  directory, keeping their relative paths: `pyproject.toml`,
  `.python-version`, `uv.lock` and `src/backfire/` except `__pycache__/`.
- It copies file contents and never writes a link. A symbolic link among the
  copied inputs fails the build with a message naming its path; the inputs
  hold none.
- Its storage budget is 16 MiB for the whole output, checked before each file
  is written; a copy that would pass it fails the build. The test-only
  variable `BACKFIRE_TEST_BUILD_MAX_BYTES` lowers the budget (never above
  16 MiB) so tests can exceed it with a small build.
- On any failure, and on SIGINT or SIGTERM, it removes its own partial
  directory and exits non-zero; it never removes anything else. After success
  only `<output>` remains, and the caller owns it.

So Backfire's tests and the `backfire_tools` package (the build and the
acceptance tooling) stay out of `<output>/backfire/`, while the rest of
`<output>` equals `plugins/code/`. The same relative layout lets the same
`uv` command serve `packages/backfire/` during development and
`<output>/backfire/` in a built plugin.

## Entry commands

Paths are relative to the component directory, `packages/backfire/` in the
repository or `<plugin root>/backfire/` in a built or installed code plugin.

| Command | Effect |
| --- | --- |
| install: `uv sync --frozen --no-dev` in the component directory | Makes the copy's own `.venv` there from `uv.lock` with the interpreter pinned in `.python-version`; the only step that downloads. The repository's `deno task backfire:install` runs `uv sync --frozen` for `packages/backfire/`, which also installs the test tools |
| `backfire serve-mcp` | Runs one session: the server on the caller's stdio (the declaration above) |
| `backfire ready` | Prints the readiness report ([readiness.md](readiness.md)); `deno task backfire:ready` runs it for `packages/backfire/` |

`backfire` is the console command that `pyproject.toml`'s `[project.scripts]`
installs into the copy's `.venv`; `python -m backfire` runs the same commands.
Each copy has its own `.venv`, so installing or removing another copy never
changes it. Serving and readiness never sync or download: `uv run --frozen
--offline --no-sync` uses the environment as installed. Before the install
command has run, uv creates an empty `.venv` and the start fails with
``Failed to spawn: `backfire` ``; the operator documentation names the install
command, which then fills that `.venv`.

## Runtime requirements

- `uv` 0.11.32 or later on the client's `PATH`, as `pyproject.toml`'s
  `required-version` (`>=0.11.32`) demands; uv refuses to run the project
  otherwise. `uv.lock` still fixes every package version.
- The Python interpreter pinned in `.python-version` (3.14.4), which the
  install command provides.
- No Deno or Node at runtime.

## Server composition

The component directory is a standard Python project with the src layout:

- `pyproject.toml`, `.python-version` and `uv.lock`;
- `src/backfire/`, the runtime package: `__main__.py` with the `serve-mcp` and
  `ready` commands; the MCP server on the official MCP Python SDK with the MCP
  boundary below; the subpackage `backfire.tools` with the eleven tools, ported
  from `jev-mcp` 0.9.0's `src/index.ts` and `src/lib.ts` at revision
  `a1fcc1e47fc696614f081e23a66ff48a890f22fd` (MIT); the in-process judge of
  [judgment.md](judgment.md) with the profile-driven provider subclass, answer
  validation and failure classification; the configuration, records, decision
  units and readiness code; `config.toml`, the shipped provider configuration
  ([provider-profile.md](provider-profile.md)); and `UPSTREAM.md`, which
  records the port's source, revision, the original files' SHA-256 and its
  recorded differences ([research.md](../research.md#python-package--2026-09-27));
- `src/backfire_tools/`, the development and release programs, not shipped:
  the build and the acceptance tooling;
- `tests/`, the pytest suites.

The package's dependencies come only from `pyproject.toml` and `uv.lock`.

## Session lifecycle

1. The server creates and locks its record file and applies the record budget.
2. It loads nothing from the provider yet: the configuration and the credential
   are read for each judgment ([judgment.md](judgment.md)), so a
   misconfiguration fails the judgment, not the session. The test-only
   `BACKFIRE_TEST_PROVIDER_BASE_URL`
   ([provider-profile.md](provider-profile.md#test-only-override)) applies
   when the server's own environment sets it.
3. It serves the tools over the SDK's stdio transport through the
   [MCP boundary](#mcp-boundary). Its own log goes to stderr and holds status
   codes, digests and timings only.
4. Shutdown starts when the client's input ends, a write to the client fails,
   a message exceeds 10 MiB, or the server receives SIGTERM or SIGINT. The
   server cancels its open calls, which cancels their provider requests and
   kills any pattern child of `backfire_extract`, records them as
   `session_ended`, and exits. A killed server leaves no pattern child for
   long: each child sets a timer on itself before matching whose default
   action ends the process after the 1,000 ms pattern limit, even while the
   regex engine runs.
5. Each client session runs its own server process and record file. Sessions
   share only the record directory, whose cleanup skips locked files, so
   closing one session leaves the others running.

## MCP boundary

- Messages are newline-delimited JSON-RPC, as MCP stdio specifies. The server
  gives the SDK's `stdio_server` its own input stream: a bounded line reader
  that counts each line's bytes as they arrive and ends the session when a
  line passes 10 MiB before its newline. The SDK still parses every message.
- The boundary sits between the SDK's stdio transport and the server, sees
  each message already parsed, and passes it on unchanged and in order, with
  the exceptions below.
- A client request with `method: "tools/call"` opens a call: its JSON-RPC id, a
  call number, the tool name (one of the eleven or `unknown`), the input digest,
  the start time and a deadline 118 s later.
- The server's response with the same id closes the call: the boundary writes
  the tool-call record ([data-model.md](../data-model.md#tool-call-record)),
  then sends the response. `result.isError` gives `tool_error`, including
  invalid arguments, which the server checks against the tool's published
  input schema; a JSON-RPC `error` gives `protocol_error`;
  decisions come from `result.content[0].text` parsed as JSON.
- A client `notifications/cancelled` for an open call records it as
  `cancelled` and closes it for good: a response that still arrives for it is
  dropped, so no answer reaches the client after its cancellation.
- At a call's deadline the boundary cancels the call's task, which cancels its
  provider request and kills a pattern child, records the call as
  `deadline_exceeded`, closes it and answers the client with a tool result
  whose `isError` is true and whose text is the fixed `deadline_exceeded`
  message. The session keeps serving.
- If a tool-call record cannot be written, the boundary answers that call with
  the fixed tool error `record_write_failed` instead of its result.
- At shutdown, open calls are recorded as `session_ended`.

## Deadline

A tool call answers or fails within 120 s. The boundary's 118 s deadline is the
only call-level timer: the judge's attempts and retry waits use the time left
([judgment.md](judgment.md#retries-and-time)), so a stalled provider ends in a
specific judgment error when time allows and in `deadline_exceeded`
otherwise. The slowest work before a judgment is `backfire_extract` with 31
timed-out patterns and one matching one, about 31 s of pattern children. The
deadline fires only if no tool blocks the server's event loop; a feasibility
gate measures every tool's longest event-loop stall at the 10 MiB message
limit.

The records' `duration_ms` lets acceptance check the bound for every call.

## Tool surface

The eleven tools of `jev-mcp` 0.9.0 under the `backfire_` names, with that
release's descriptions, input schemas and results except for the port's
recorded differences: `backfire_gate`, `backfire_review`, `backfire_verify`,
`backfire_noul`, `backfire_classify`, `backfire_find`, `backfire_rerank`,
`backfire_compare`, `backfire_screen`, `backfire_extract` and
`backfire_decide`. The offline fidelity suite compares the tool list and the
judgment requests (`state` and `questions`, in order) and results for the
known-answer arguments with fixtures captured from `jev-mcp` 0.9.0 on Node,
after mapping `jev_` to `backfire_` and `jev-mcp` to `backfire` and applying
the recorded differences. Adopting a later upstream revision is
an explicit change that recaptures the fixtures, re-ports the changed logic,
and repeats the known-answer set in both clients (FR-012).

## Client registration for acceptance

Acceptance stages the code plugin alone by building it into a temporary
directory ([Distribution build](#distribution-build)) and installing the staged
copy with the install command of [Entry commands](#entry-commands), runs each
client from a
working directory outside the repository, and registers only the staged
package's declared `backfire` server, with `${PLUGIN_ROOT}` replaced by the
staged path. The client writes its events as JSON Lines and keeps no session.
No saved client configuration changes.

- Claude Code (2.1.283):
  `claude -p --output-format stream-json --verbose --no-session-persistence --strict-mcp-config --mcp-config <file>`,
  where `<file>` holds the staged declaration.
- Codex CLI (0.157.1):
  `codex exec --json --ephemeral --skip-git-repo-check --ignore-user-config -c 'mcp_servers.backfire.command="uv"' -c 'mcp_servers.backfire.args=["--directory","<staged>/backfire","run","--frozen","--offline","--no-sync","backfire","serve-mcp"]'`;
  `--ignore-user-config` keeps other registered servers out while
  authentication still comes from `CODEX_HOME`, and `--skip-git-repo-check`
  allows a working directory outside Git.

Either registration may add an `env` entry that points `XDG_STATE_HOME` at the
run's own record directory. Installing the package through each client's plugin
mechanism, with skill discovery, belongs to a separate client-installation
feature, which installs a built code plugin; FR-001 and SC-008 close only after
it passes for the code package with `backfire` and the known-answer set passes
through the installed package in both clients. Installing into saved client
configuration needs the user's separate approval.
