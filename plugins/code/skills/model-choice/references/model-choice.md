# Model choice in Verbose Broccoli

Every worker, reviewer and orchestrator started through Orca gets its agent
(Codex, Claude Code or OMP), model and reasoning effort from a backfire
judgment made for that task. There is no default model and no table from task
difficulty or risk to a model, agent or effort; backfire weighs the facts each
time. One rule stays fixed: a change's final review comes from a provider
other than the implementer's (`AGENTS.md`, "Review").

## Candidates

A candidate is one agent, model and effort, with its catalog description and
launch path. Build the candidates from the live catalogs at choice time, never
from a written model list:

- Codex: `~/.codex/models_cache.json`. Each `models[]` entry has `slug`,
  `description`, `supported_reasoning_levels[].effort` and `visibility`.
- Claude Code: `claude --help` documents `--model` (an alias such as `fable`,
  `opus` or `sonnet`, or a full model name) and `--effort`.
- OMP: `omp models` lists each provider's models; `~/.omp/agent/models.yml`
  defines the providers.

Orca's `worker-start` accepts only the efforts in its own model catalog and
fails with `invalid_argument` otherwise. The user's current list of those gaps
and the terminal-path steps are in `~/.claude/rules/worker-dispatch.md`. An
effort outside Orca's catalog is still a candidate; it launches through the
terminal path.

## Evidence

Give backfire facts:

- The task spec: scope, files, kind of work, and whether it is read-only.
- Track records in this repository: the `Reviewed-by` trailers of the develop
  merge review records
  (`git log --grep='record develop merge review' --format='%h %(trailers:key=Reviewed-by,valueonly)'`)
  and the workers named in each feature's `tasks.md`.
- The user's standing priorities, taken from the user's instructions and
  `AGENTS.md`, for example review speed before `develop` and accuracy before
  `main`. Never invent a priority.
- The other-provider rule for final reviews: name the implementer's provider
  and state the rule in `priorities`.

Never put credentials into the evidence. Send personal records only through a
provider profile the user has approved for them, and keep the evidence
minimal.

### Usage limits

Read the remaining limits and credit with CodexBar's `usage` command, one
call per provider, from a directory outside any repository. OpenRouter and
Vercel each get only their own key file, through uv's `--env-file`:

```sh
clean=(env -u OPENROUTER_API_URL -u OPENROUTER_MANAGEMENT_API_KEY
  -u CODEXBAR_CONFIG -u CLAUDE_CLI_PATH -u CODEX_CLI_PATH -u ANTHROPIC_ADMIN_KEY
  -u ANTHROPIC_ADMIN_API_KEY -u CODEXBAR_CLAUDE_OAUTH_TOKEN)
keys="${XDG_CONFIG_HOME:-$HOME/.config}/verbose-broccoli/providers"
"${clean[@]}" CI=1 codexbar usage --provider codex --source oauth --format json
"${clean[@]}" CI=1 codexbar usage --provider claude --source oauth --format json
"${clean[@]}" uv run --no-project --env-file "$keys/openrouter.env" -- \
  codexbar usage --provider openrouter --format json
"${clean[@]}" uv run --no-project --env-file "$keys/vercel.env" -- \
  codexbar usage --provider vercel --format json
```

CodexBar's security review allows it only within these limits:

- Name exactly one `--provider` per call. Never use `all`, `both` or
  `--status`; `all` reads other tools' secrets.
- Pass `--source oauth` for Codex and Claude. Claude's default source types
  `/usage` into a real interactive Claude session, which could start a billed
  turn.
- Give each call only its own key, with the variables that reroute keys or
  switch sources unset, as `clean` does. Keys stay in the env files: never
  copy them into CodexBar's config, never print them.
- Create no CodexBar config file (`~/.config/codexbar/config.json`,
  `~/.codexbar/config.json` or `$CODEXBAR_CONFIG`), and keep
  `~/.config/codexbar/providers/` empty, because CodexBar loads any plugin
  there.
- Run only `usage`, never `serve`, `hooks`, `cookie`, `plugins fetch` or
  `config set-api-key`.
- The JSON carries account identity. Strip it before the output goes into
  evidence, messages or logs, for example with
  `jq 'map(del(.account, .openaiDashboard, .usage.identity, .usage.accountEmail, .usage.accountOrganization))'`.

Each call prints a one-item array. Rate windows are `usage.primary` and
`usage.secondary` (`usedPercent`, `resetsAt`, `windowMinutes`), named in
`rateWindowLabels`: Codex reports only a `Weekly` secondary window, Claude a
`Session` and a `Weekly` window, plus model-scoped windows such as "Fable
only" in `usage.extraRateWindows`. Balances are `usage.details` rows:
OpenRouter's "Credits" → "Remaining" and Vercel's "Team credits" → "Available
balance".

Dropping candidates is a fact check, not a threshold table. Drop the
candidates that draw on a window at 100% used, until its `resetsAt`, or on a
prepaid balance of zero. Codex's extra-usage credit (`credits.remaining`) at
zero does not drop Codex while its windows have room. CodexBar does not cover
Hive, Tetrate or Cloudflare, so candidates there keep an unknown limit; say so
in the evidence. When a call fails, give the failure as evidence and do not
guess. Give the remaining limits and their reset times to `jev_decide` as
evidence.

## The call

`jev_decide` takes 2 to 6 candidates. With more, narrow them first, for
example with `jev_rerank` over the catalog entries with the task as the query,
or decide in steps: agent, then model, then effort. When `jev_rerank` scores
every candidate the same, it cannot narrow; decide in steps. Read the
[`jev_decide`](../../backfire/reference/tools.md#jev_decide) and
[`jev_rerank`](../../backfire/reference/tools.md#jev_rerank) blocks before the
first call.

## Acting on the answer

- Pass the chosen agent, model and effort explicitly, never a default:
  `orca orchestration worker-start --agent <agent> --model <model> --effort <effort>`.
  Use the terminal path when the effort is outside Orca's catalog, and
  `omp --model <provider>/<model-id>` for OMP.
- Compare `launch.requested` with `launch.effective` in the launch result, and
  check the worker's status line.
- Create extra worktrees as children of your own
  (`orca worktree create --parent-worktree path:<worktree>`). Keep each
  worktree's Orca board status in step with its Linear issue:
  `orca worktree set --worktree path:<worktree> --workspace-status in-review`
  at In Review, and `completed` right after the finish into `develop`. Check
  the flags with `--help`.
- When backfire escapes (`ask_user`, `investigate` or `none`) or fails
  (`invalid_response` or a transport error), ask the user; a worker asks
  through its `orca orchestration ask` command. Do not call again or fall back
  to a default.
- Report the pick with its probability and confidence, and name it under its
  task in the feature's `tasks.md`.

## Calling backfire without its MCP tools

When the session has no backfire MCP tools, call backfire from the repository
package, never through a marketplace or client installation. Save this
snippet in your session scratch space, not in the repository. It starts
`backfire serve-mcp` over stdio with the command in the code plugin's
`mcp.json`, through the locked `mcp` client library:

```python
"""Call one backfire tool: python backfire_call.py <tool> <args.json>."""

import json
import subprocess
import sys

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
server = StdioServerParameters(command="uv", args=[
    "--directory", f"{root}/packages/backfire", "run", "--frozen", "--offline",
    "--no-sync", "backfire", "serve-mcp"])


async def main(tool, path):
    with open(path) as file:
        arguments = json.load(file)
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments)
            for block in result.content:
                print(getattr(block, "text", block))


anyio.run(main, sys.argv[1], sys.argv[2])
```

Write the tool's arguments to a JSON file, then run the snippet from a
worktree root:

```sh
uv run --frozen --offline --no-sync --package backfire python <file> <tool> <args.json>
```
