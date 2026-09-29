---
name: web-agent
description: Reach a narrow goal on a web page with the Jev Ultrafast browser agent, in a tab of Orca's built-in browser or in Chrome. Use when a task needs clicks, typing or selections on a live page that no API or plain download can do; not for reading pages that plain HTTP can fetch.
---

# Web Agent

Jev Ultrafast, from Browser Use, reads the page's visible controls, lets Jev
choose one operation and one element per step, and executes that choice in
the browser. A small text model writes a value only when the step types
text. This repository's copy, `packages/jev-ultrafast/`, adds two things to
upstream; its `UPSTREAM.md` lists every difference:

- **Provider**: Jev calls go to the provider that `JEV_PROVIDER` names in
  `packages/jev-ultrafast/src/jev_ultrafast/providers.toml`: `typesafe`
  (the default, as upstream) or `vercel` (Vercel AI Gateway).
- **Browser**: by default the agent opens its own tab in Orca's built-in
  browser, in the current worktree, and closes it at the end.
  `JEV_BROWSER=chrome` uses upstream's Chrome connection instead.

## Credentials

Keys live only in `~/.config/verbose-broccoli/chat/jev.env`, readable by the
user alone. Create the file once, empty, then add the key lines the chosen
provider needs:

```sh
install -d -m 700 ~/.config/verbose-broccoli/chat
install -m 600 /dev/null ~/.config/verbose-broccoli/chat/jev.env
```

| Line | Needed for |
| --- | --- |
| `AI_GATEWAY_API_KEY=<key>` | `JEV_PROVIDER=vercel`; Jev needs paid AI Gateway credit, since the free tier refuses it |
| `TYPESAFE_API_KEY=<key>` | `JEV_PROVIDER=typesafe` |
| `TEXT_MODEL_API_KEY=<key>`, and optionally `TEXT_MODEL_BASE_URL`, `TEXT_MODEL`, `TEXT_MODEL_REASONING` | Steps that type text (upstream's OpenAI-compatible text helper) |

Never print the file, paste a key into a prompt, or commit it.

## Run

From the repository root, with Orca running:

```sh
JEV_PROVIDER=vercel uv run --frozen --offline --no-sync \
  --env-file ~/.config/verbose-broccoli/chat/jev.env \
  --package jev-ultrafast \
  python packages/jev-ultrafast/examples/run.py \
  --url 'https://en.wikipedia.org/wiki/Main_Page' \
  --goal 'Find and open the Wikipedia article about Gödel’s incompleteness theorems.'
```

Repeat `--goal` for an ordered list of goals. The command prints the elapsed
time, the number of actions and the status after each step, then the final
URL. Each step is one paid Jev call; report the number of steps.

## Limits

- Run one browser job at a time. Other sessions share Orca's browser; the
  agent touches only the tab it opened.
- Screenshots and mouse-wheel scrolling need the tab to be drawn on screen.
  On a tab that is not visible they can stall until they time out, so keep
  the worktree's browser visible for goals that need scrolling.
- A `DONE` step is not proof: check the outcome on the page yourself.
- Upstream does not handle shadow roots, frames, canvas, uploads, pop-up
  tabs, nested scrolling or arbitrary keyboard widgets.
- Without Orca, or when `orca` is not on `PATH`, Orca mode stops with an
  error; set `JEV_BROWSER=chrome` to use Chrome.
