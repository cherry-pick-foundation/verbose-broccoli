# Contract: `credit-offers` command

Package `packages/credit-offers/`, console script `credit-offers`. See
[research R4-R8](../research.md#r4-plain-fetch-or-browser-for-the-search).

## Invocation

```sh
JEV_PROVIDER=<provider> uv run --frozen --offline --no-sync \
  --env-file "${XDG_CONFIG_HOME:-$HOME/.config}/verbose-broccoli/providers/<provider>.env" \
  --package credit-offers credit-offers [--hours N] [--end ISO-8601] [--notify]
```

- `--hours` (default 6): block length in whole hours; must divide 24.
- `--end`: the block's end, for testing a past block; default is the latest
  block boundary at or before now, in the local time zone. It must fall on a
  boundary.
- `--notify`: send the desktop notification when strong offers are found.

## Tracker configuration

The tracker's repository, index path, API root and raw-file root are read
from `credit_offers/tracker.toml`, not written in code:

```toml
repository = "luongnv89/freetokens"
index_path = "index.json"
api_root = "https://api.github.com"
raw_root = "https://raw.githubusercontent.com"
```

## Behavior

1. Find the last commit that changed the index before the block's start and
   before its end. If they are the same, print that no offer is new and exit
   1 without further requests.
2. Fetch the index at both commits; new offers are slugs present at the end
   and absent at the start.
3. Drop offers whose `status` is not `active` or whose `expiry_date` is set.
   If none remain, exit 1 without a Jev call.
4. Send one Jev request through `jev_ultrafast.model` (the selected provider)
   with one `choice` question per remaining offer (research R6), and validate
   each answer with upstream `validate_choice()`.
5. Print one line per judged offer (slug, choice, probability) and
   `jev_calls=<n>`.
6. If at least one offer is strong: with `--notify`, send one notification
   with `notify-send`; exit 0. Otherwise exit 1.

## Exit status and output

| Status | Meaning |
| --- | --- |
| 0 | At least one strong offer (and, with `--notify`, the notification was sent) |
| 1 | No strong offer |
| 2 | Invalid arguments |
| 3 | A request, provider, validation or notification failure; stderr names it without any key |

An Orca precheck treats every status other than 0 as "skip this run".

## Side effects

None besides the notification: no files, caches or records are written.
