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
  (the default, as upstream), `vercel` (Vercel AI Gateway), `cloudflare`
  (Cloudflare Workers AI) or `openrouter` (OpenRouter's decisions API).
- **Browser**: by default the agent opens its own tab in Orca's built-in
  browser, in the current worktree, and closes it at the end.
  `JEV_BROWSER=chrome` uses upstream's Chrome connection instead.

## Credentials

Keys live in the shared provider folder
`$XDG_CONFIG_HOME/verbose-broccoli/providers/` (by default
`~/.config/verbose-broccoli/providers/`), one file per provider, which every
plugin uses. The folder is readable by
the user alone (mode `0700`) and each file has mode `0600`. Create a
provider's file once, empty, then add its key lines. The second command
does nothing when the file exists, so it never empties a file that already
holds a key:

```sh
providers="${XDG_CONFIG_HOME:-$HOME/.config}/verbose-broccoli/providers"
install -d -m 700 "$providers"
[ -e "$providers/openrouter.env" ] ||
  install -m 600 /dev/null "$providers/openrouter.env"
```

| File in `providers/` | Lines | Provider |
| --- | --- | --- |
| `cloudflare.env` | `CLOUDFLARE_API_TOKEN=<token>`, `CLOUDFLARE_ACCOUNT_ID=<id>` | `JEV_PROVIDER=cloudflare`; a token with the Workers AI permission for that account; Jev needs a paid Workers AI balance |
| `vercel.env` | `AI_GATEWAY_API_KEY=<key>` | `JEV_PROVIDER=vercel`; Jev needs paid AI Gateway credit, since the free tier refuses it |
| `openrouter.env` | `OPENROUTER_API_KEY=<key>` | `JEV_PROVIDER=openrouter` |
| `typesafe.env` | `TYPESAFE_API_KEY=<key>` | `JEV_PROVIDER=typesafe` |
| `github.env` | `GITHUB_TOKEN=<token>` | The `credit-offers` search's GitHub API requests; a token with no extra permissions is enough |

Steps that type text also need upstream's OpenAI-compatible text helper:
`TEXT_MODEL_API_KEY`, and optionally `TEXT_MODEL_BASE_URL`, `TEXT_MODEL` and
`TEXT_MODEL_REASONING`, in the file of the provider that serves that model.
Pass one `--env-file` per file a run needs; uv reads them all.

Never print a key file, paste a key into a prompt, or commit it.

## Run

From the repository root, with Orca running:

```sh
JEV_PROVIDER=openrouter uv run --frozen --offline --no-sync \
  --env-file "${XDG_CONFIG_HOME:-$HOME/.config}/verbose-broccoli/providers/openrouter.env" \
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
