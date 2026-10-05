---
name: credit-offers
description: Check the freetokens tracker for new API credit offers that cost nothing and state no time limit or end date, and show a desktop notification when one appears. Use for the scheduled Orca automation or to check a past 6-hour block by hand; not for claiming offers or for offers the tracker does not list.
---

Read [the chat plugin rules](../../AGENTS.md) before using this skill.

# Credit Offers

The `credit-offers` command in `packages/credit-offers/` looks at the latest
full 6-hour block of the day (00-06, 06-12, 12-18 or 18-24 in the laptop's
time zone). It finds the offers that entered the freetokens tracker's
published list (<https://github.com/luongnv89/freetokens>) during that block,
drops those that are no longer active or that have an end date, and asks Jev,
in one call, whether each remaining offer costs nothing to claim and states
no time limit or end date. The call is one `jev_classify` request, one item
per offer, with the classes `qualifies` and `excluded`, sent through the
repository's gated `jev-mcp` proxy. It saves nothing; the tracker's own
history tells it what is new. Why it runs every 6 hours, and the data behind
that, are in `specs/021-chat-jev-ultrafast/research.md` (R9).

## Run

From the repository root. The command starts the gated `jev-mcp` proxy
(`packages/education-privacy-gate/`) itself, with `uv`, and talks to it as an
MCP client. The proxy loads its own OpenRouter key from the shared provider
folder, so the command passes no provider key and no other environment. Only
the optional GitHub token file is passed to the command. Install the proxy's
npm closure once with `mise run setup`:

```sh
providers="${XDG_CONFIG_HOME:-$HOME/.config}/verbose-broccoli/providers"
uv run --frozen --offline --no-sync --env-file "$providers/github.env" \
  --package credit-offers credit-offers --notify
```

`github.env` may be empty. When it holds `GITHUB_TOKEN`, the search sends
that token on its GitHub API requests, which raises GitHub's limit from 60
to 5,000 requests an hour.

- `--notify` sends one desktop notification (`notify-send`) naming each
  strong offer's title, provider, amount and link. Without it, the command
  only prints.
- `--end <ISO time>` checks the block that ends then, for example
  `--end 2026-09-27T12:00:00+09:00`; the time must be a block boundary.
- `--hours <n>` changes the block length; `n` must divide 24.

The command prints one line per judged offer and `jev_calls=<n>`: 0 when the
block has no new candidate, otherwise 1. One call judges at most 64 offers; a
block with more new candidates ends with status 3.

## Exit status

| Status | Meaning |
| --- | --- |
| 0 | At least one strong offer (notified with `--notify`) |
| 1 | No strong offer |
| 2 | Invalid arguments |
| 3 | The tracker, GitHub, the gate, the provider or the notification failed; the message names it and never shows a key |

An Orca automation precheck treats anything but 0 as "skip this run", and
Orca has no failed state for a precheck: it records the run as skipped with
"Precheck exited with code N" and keeps the command's output in the run's
details. The approved automation starts no agent, so its precheck maps the
normal outcomes, 0 (notified) and 1 (nothing strong), to 1 and passes every
other status through:

```sh
<the command above>; s=$?; [ "$s" -le 1 ] && exit 1; exit "$s"
```

In Orca's run list, code 1 is a normal run and any other code, such as 3,
is an error to look at.

## Limits

- A block the laptop slept through is not checked later.
- An offer's first appearance in the tracker can be later than the
  provider's own launch.
- Without a token, GitHub allows 60 API requests an hour per network
  address, shared by every tool on the laptop; a run uses two, and a run
  that finds the limit used up ends with status 3, so its block is not
  checked.
- The judgment goes through the gated proxy only, on OpenRouter. If the proxy
  cannot start, has no key or credit, does not answer within 90 seconds, or
  refuses the call (it says only "Privacy gate rejected the call."), a block
  with candidates ends with status 3. The command never falls back to another
  route or provider.
- Which provider the scheduled automation uses stays the user's decision.
