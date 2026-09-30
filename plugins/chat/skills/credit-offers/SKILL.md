---
name: credit-offers
description: Check the freetokens tracker for new API credit offers that cost nothing and state no time limit or end date, and show a desktop notification when one appears. Use for the scheduled Orca automation or to check a past 6-hour block by hand; not for claiming offers or for offers the tracker does not list.
---

# Credit Offers

The `credit-offers` command in `packages/credit-offers/` looks at the latest
full 6-hour block of the day (00-06, 06-12, 12-18 or 18-24 in the laptop's
time zone). It finds the offers that entered the freetokens tracker's
published list (<https://github.com/luongnv89/freetokens>) during that block,
drops those that are no longer active or that have an end date, and asks Jev,
in one call, whether each remaining offer costs nothing to claim and states
no time limit or end date. It saves nothing; the tracker's own history tells
it what is new. Why it runs every 6 hours, and the data behind that, are in
`specs/021-chat-jev-ultrafast/research.md` (R9).

## Run

From the repository root. The key file is the provider's file in the shared
provider folder that the `web-agent` skill describes; it must exist, even
while empty. For Cloudflare Workers AI:

```sh
JEV_PROVIDER=cloudflare uv run --frozen --offline --no-sync \
  --env-file ~/.config/verbose-broccoli/providers/cloudflare.env \
  --package credit-offers credit-offers --notify
```

For Vercel AI Gateway, use `JEV_PROVIDER=vercel` and `providers/vercel.env`.

- `--notify` sends one desktop notification (`notify-send`) naming each
  strong offer's title, provider, amount and link. Without it, the command
  only prints.
- `--end <ISO time>` checks the block that ends then, for example
  `--end 2026-09-27T12:00:00+09:00`; the time must be a block boundary.
- `--hours <n>` changes the block length; `n` must divide 24.

The command prints one line per judged offer and `jev_calls=<n>`: 0 when the
block has no new candidate, otherwise 1.

## Exit status

| Status | Meaning |
| --- | --- |
| 0 | At least one strong offer (notified with `--notify`) |
| 1 | No strong offer |
| 2 | Invalid arguments |
| 3 | The tracker, GitHub, the provider or the notification failed; the message names it and never shows a key |

An Orca automation precheck treats anything but 0 as "skip this run". The
approved automation appends `; exit 1` to the command, so Orca never starts
an agent and records every run as skipped, with the command's output in the
run's details.

## Limits

- A block the laptop slept through is not checked later.
- An offer's first appearance in the tracker can be later than the
  provider's own launch.
- GitHub allows 60 unauthenticated API requests an hour per address; a run
  uses two.
- Without a key for a provider that accepts Jev calls, a block with
  candidates ends with status 3. Vercel AI Gateway's free tier refuses Jev,
  so Vercel needs paid credit.
