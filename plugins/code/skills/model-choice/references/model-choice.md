# Model choice in Verbose Broccoli

Every worker, reviewer and orchestrator started through Orca gets its agent
(Codex, Claude Code, Copilot, OMP, Antigravity, Grok or Cursor), model and
reasoning effort from a backfire judgment made for that task on a Jev model.
There is no default model and no table from task difficulty or risk to a
model, agent or effort; backfire weighs the facts each time, including the
task's difficulty and every candidate's remaining usage. One rule stays
fixed: a change's final review comes from a provider other than the
implementer's (`AGENTS.md`, "Review").

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
- Copilot: the `/model` picker in a Copilot session lists the models the
  plan allows. `copilot help config` lists every model the CLI knows, and
  `--model` with one the plan lacks falls back to Auto with only a warning.
  The Free plan allows only `auto`, which picks the model for each task;
  `--auto-tier` sets its routing profile (`efficiency`, `balance`,
  `intelligence` or `fast`). The Free plan's allowance is small (200 AI
  credits a month, about 50 requests), so Copilot suits small tasks and
  reviews; give backfire that fact.
- Antigravity: `agy models` lists the models; each id carries a thinking
  level, for example `gemini-3.8-flash-low`. `agy --effort` takes `low`,
  `medium`, `high` or `max`. The account uses Google's free tier, whose
  quota refreshes weekly (Gemini 3.1 Pro and 3.8 Flash); give backfire that
  fact.
- Grok: `grok models` lists the models, and `~/.grok/models_cache.json`
  lists each model's efforts. The free tier also caps each model at
  1,000,000 tokens over a rolling 24-hour window, which no tracker shows;
  read it from Grok's own log (see "Grok's free cap" under Usage limits).
- Cursor: `cursor-agent models` lists the models; a named model carries its
  effort in its id. On the free plan the only candidate is `auto`, which
  picks the model for each request; leave out the named models, which fail
  at the first prompt. Its monthly quota has two buckets, "Cursor Models"
  and "Other Models".

Orca's `worker-start` accepts only the efforts in its own model catalog and
fails with `invalid_argument` otherwise. The user's current list of those gaps
and the terminal-path steps are in `~/.claude/rules/worker-dispatch.md`. An
effort outside Orca's catalog is still a candidate; it launches through the
terminal path. Orca's catalog does not cover Copilot, so Copilot always
launches through the terminal path. `worker-start --model` takes Antigravity
and Cursor models but not Grok's, so Grok launches through the terminal path
too.

MiniMax Code (`mcode`) is not a candidate for workers, reviewers or
orchestrators, because Orca does not supervise it. Use it only in scripted
runs (`mcode exec`).

A task that reads student data (the work vault's student pages, backfire's
roster or raw student sources) takes only Claude Code and Codex candidates,
which run on the user's own Claude and ChatGPT accounts; never another
agent.

## Evidence

Give backfire facts:

- The task spec: scope, files, kind of work, and whether it is read-only.
- The task's difficulty on the user's five-level scale: very easy, easy,
  medium, difficult or very difficult. `npm run workflow` reports a level for
  observed changes (`difficulty[].level`, policy `coding-difficulty/1`; per
  task with `--plan`). When no change exists yet or the level is null, give
  your own estimate and say that it is one.
- Track records in this repository: the `Reviewed-by` trailers of the develop
  merge review records
  (`git log --grep='record develop merge review' --format='%h %(trailers:key=Reviewed-by,valueonly)'`)
  and the workers named in each feature's `tasks.md`.
- The user's standing priorities, taken from the user's instructions and
  `AGENTS.md`, for example review speed before `develop`, accuracy before
  `main`, and using the free quotas of the locally installed agents where a
  task allows. Never invent a priority.
- The other-provider rule for final reviews: name the implementer's provider
  and state the rule in `priorities`.

Never put credentials into the evidence. Never send student data or other
personal records through this plugin's backfire, and write the evidence in
English: backfire refuses any request that contains Hangul. Keep the evidence
minimal.

### Usage limits

Read the remaining limits and credit with CodexBar's `usage` command, one
call per provider, from a directory outside any repository. OpenRouter,
Vercel and Copilot each get only their own key file, through uv's
`--env-file`:

```sh
clean=(env -u OPENROUTER_API_URL -u OPENROUTER_MANAGEMENT_API_KEY
  -u CODEXBAR_CONFIG -u CLAUDE_CLI_PATH -u CODEX_CLI_PATH -u ANTHROPIC_ADMIN_KEY
  -u ANTHROPIC_ADMIN_API_KEY -u CODEXBAR_CLAUDE_OAUTH_TOKEN
  -u OPENROUTER_API_KEY -u AI_GATEWAY_API_KEY -u COPILOT_API_TOKEN)
keys="${XDG_CONFIG_HOME:-$HOME/.config}/verbose-broccoli/providers"
"${clean[@]}" CI=1 codexbar usage --provider codex --source oauth --format json
"${clean[@]}" CI=1 codexbar usage --provider claude --source oauth --format json
"${clean[@]}" uv run --no-project --env-file "$keys/openrouter.env" -- \
  codexbar usage --provider openrouter --format json
"${clean[@]}" uv run --no-project --env-file "$keys/vercel.env" -- \
  codexbar usage --provider vercel --format json
"${clean[@]}" uv run --no-project --env-file "$keys/copilot.env" -- \
  codexbar usage --provider copilot --format json
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
- Copilot's `COPILOT_API_TOKEN` comes from GitHub's device login for the
  OAuth app and `read:user` scope that CodexBar's own Copilot login uses.
  CodexBar sends any token it gets, so never give it a personal access token
  or the GitHub CLI's login.
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
only" in `usage.extraRateWindows`, and Copilot a monthly `Chat` window.
Balances are `usage.details` rows: OpenRouter's "Credits" → "Remaining" and
Vercel's "Team credits" → "Available balance".

Codex also reports its usage-limit reset credits in `usage.codexResetCredits`:
`availableCount` and `credits[]`, each with `title`, `reset_type`, `status`,
`granted_at` and `expires_at`. Claude and the other providers report none; say
"none reported" for them, and for Codex when the field is missing. Reset
credits are evidence, not a rule. Give backfire
the `availableCount` and the `expires_at` of each `available` credit, so that a
provider with unused resets that expire is not steered away from early. Leave
out the credits' descriptions and any credit IDs, for example with:

```sh
"${clean[@]}" CI=1 codexbar usage --provider codex --source oauth --format json |
  jq '.[0].usage.codexResetCredits
    | if . then {availableCount,
        credits: [.credits[] | select(.status == "available")
          | {title, reset_type, status, granted_at, expires_at}]}
      else "none reported" end'
```

Only the user spends reset credits. An agent uses a limit fully, then stops
and reports to the develop session; it never spends a credit.

Read Grok's and Cursor's limits from Orca, which uses each CLI's own
sign-in. Its output carries account identity, so keep only the rate windows:

```sh
orca account list --json | jq '.result.rateLimits
  | {grok: (.grok | {weekly, status, error}),
     cursor: (.cursor | {monthly, buckets, planType, status, error})}'
```

Grok reports a `weekly` window and Cursor a `monthly` window, with one window
per bucket in `buckets` (`usedPercent`, `resetsAt` in milliseconds). Orca
shows Antigravity's usage only through a Gemini CLI sign-in, which is not
installed, and `agy` reports none.

#### Grok's free cap

Grok's free tier caps each model at 1,000,000 tokens over a rolling 24-hour
window. Neither CodexBar (source `grok-web`) nor Orca (source `oauth`) reads
it: both show only the weekly window, which stayed at 0% used on 2026-10-01
while Grok refused every request. The cap appears only in the API's 429
error, which Grok logs. Read the latest such entry and nothing else from
`~/.grok`; `auth.json` there holds credentials.

```sh
grep -h 'subscription:free-usage-exhausted' ~/.grok/logs/unified.jsonl | tail -1 |
  jq -r '(.ctx.message // .ctx.reason) as $m | "\(.ts) \($m | capture("model (?<m>[^ ]+) for now").m) \($m | capture("actual/limit\\): (?<n>[0-9]+/[0-9]+)").n)"'
```

It prints the entry's time, model and `actual/limit`. On 2026-10-01
the last entry read `2026-10-01T13:11:58.698Z grok-4.7 1012248/1000000`.
Give that line to backfire as evidence. Grok counts as unavailable for that
model until about 24 hours after the heavy use that hit the cap, so about
24 hours after the entry's time at the earliest. No entry, or one older than
24 hours, shows no known cap, not that Grok is free of one: the log may be
missing or rotated, so say so in the evidence. Other models have their own
cap.

Copilot's and Cursor's trackers show the same kind of window their plans
cap (monthly), and no refusal that the tracker missed has been seen for
them. Antigravity's weekly quota is unread (see above), so its candidates
keep an unknown limit. When any agent refuses with a limit message, give
that refusal and its time to backfire and leave the agent out until its
window clears.

Dropping candidates is a fact check, not a threshold table. Drop the
candidates that draw on a window at 100% used, until its `resetsAt`, or on a
prepaid balance of zero. Codex's extra-usage credit (`credits.remaining`) at
zero does not drop Codex while its windows have room. A reset credit drops
nothing and keeps nothing: a full window still drops its candidate until its
`resetsAt`, because only the user spends a credit. Nothing reads the limits
of Hive, Tetrate, Cloudflare or Antigravity, so candidates there keep an
unknown limit; say so in the evidence. When a call fails, give the failure as
evidence and do not guess. Give the remaining limits and their reset times to
`jev_decide` as evidence, with Codex's reset-credit count and expiry dates.

## The call

`jev_decide` takes 2 to 6 candidates. With more, narrow them first, for
example with `jev_rerank` over the catalog entries with the task as the query,
or decide in steps: agent, then model, then effort. When `jev_rerank` scores
every candidate the same, it cannot narrow; decide in steps. Read the
[`jev_decide`](../../backfire/reference/tools.md#jev_decide) and
[`jev_rerank`](../../backfire/reference/tools.md#jev_rerank) blocks before the
first call.

The judgment runs on a Jev model only, never on a general model such as
DeepSeek. Backfire's shipped order tries the `openrouter` profile (Jev), then
`hive` (DeepSeek), and the plugin's backfire MCP tools follow that order. So
call backfire with the snippet below, which starts `serve-mcp --profile
openrouter`: an empty OpenRouter balance then fails instead of switching.
Check that each answer names `provider` `openrouter` and a Jev `model`, for
example `typesafe/jev-1.13`. When the Jev profile cannot answer, ask the user;
do not fall back.

## Acting on the answer

- Pass the chosen agent, model and effort explicitly, never a default:
  `orca orchestration worker-start --agent <agent> --model <model> --effort <effort>`.
  Use the terminal path when the effort is outside Orca's catalog,
  `omp --model <provider>/<model-id>` for OMP, `copilot --model auto
  --auto-tier <tier>` for Copilot (`--reasoning-effort <effort>` with a
  named model), and `grok -m <model> --reasoning-effort <effort>` for Grok.
  Cursor takes `--model` only, since its model id carries the effort.
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

## Calling backfire

Call backfire from the repository package, never through a marketplace or
client installation. Save this snippet in your session scratch space, not in
the repository. It starts `backfire serve-mcp` over stdio with the command in
the code plugin's `mcp.json` plus `--profile openrouter`, through the locked
`mcp` client library:

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
    "--no-sync", "backfire", "serve-mcp", "--profile", "openrouter"])


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
