# Quickstart: validating the feature

Run from the repository root after Orca's setup script (or `uv sync --locked
--all-packages --extra education`).

## Offline checks (no paid calls)

```sh
npm run test:jev-ultrafast     # upstream tests plus provider and Orca-mode stubs
npm run test:credit-offers     # search, block, filter, judgment and notification stubs
npm run check                  # everything, including lint and documents
```

Expected: all pass; no test opens a network connection.

## Recompute the schedule interval

```sh
awk -F'\t' '$6=="qualifies"{print $1}' specs/021-chat-jev-ultrafast/offer-history.tsv \
  | python3 -c 'import sys,datetime as d;t=[d.datetime.fromisoformat(l.strip().replace("Z","+00:00")) for l in sys.stdin];print(len(t),round((t[-1]-t[0]).total_seconds()/3600/(len(t)-1),3))'
```

Expected: `145 6.349`.

## Orca browser mode without model calls

With Orca running, from this worktree:

```sh
uv run --frozen --offline --no-sync --package jev-ultrafast \
  python packages/jev-ultrafast/scripts/check_guards.py
```

Expected: upstream's guard checks pass in a tab this command opens in the
current worktree, and `orca tab list --worktree current --json` shows no tab
left afterwards.

## Live search without a key

```sh
install -m 600 /dev/null ~/.config/verbose-broccoli/chat/jev.env   # only if missing
JEV_PROVIDER=vercel uv run --frozen --offline --no-sync \
  --env-file ~/.config/verbose-broccoli/chat/jev.env \
  --package credit-offers credit-offers --end <a past block boundary>
```

Expected: a block with no new offer exits 1 with `jev_calls=0`; a block with
candidates exits 3 naming `AI_GATEWAY_API_KEY`, and prints no key.

## Test notification

Send one notification through the search's own notification function with a
sample offer marked as a test; expected: one GNOME notification appears.

## With a key (later)

After the user adds `AI_GATEWAY_API_KEY` to the credential file, run the
search with `--end` on a block that contains a known qualifying offer (for
example the block holding `openrouter-space-bunny-alpha-free` in
[offer-history.tsv](offer-history.tsv)) and `--notify`. Expected: exit 0, one
notification, `jev_calls=1`.
