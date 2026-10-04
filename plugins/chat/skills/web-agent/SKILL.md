---
name: web-agent
description: Reach a narrow goal on a web page with the Jev Ultrafast browser agent, in a tab of Orca's built-in browser or in Chrome. Use when a task needs clicks, typing or selections on a live page that no API or plain download can do; not for reading pages that plain HTTP can fetch.
---

Read [the chat plugin rules](../../AGENTS.md) before using this skill.

# Web Agent

Jev Ultrafast, from Browser Use, reads the page's visible controls, lets Jev
choose one operation and one element per step, and executes that choice in
the browser. This repository's copy, `packages/jev-ultrafast/`, changes three
things from upstream; its `upstream.md` lists every difference:

- **Judgments**: Jev's choices go through the repository's gated `jev-mcp`
  proxy (`packages/education-privacy-gate/`), which the agent starts with `uv`
  and calls as an MCP client (`jev_classify`). The package has no route to a
  provider of its own, and `JEV_PROVIDER` has no effect.
- **Browser**: by default the agent opens its own tab in Orca's built-in
  browser, in the current worktree, and closes it at the end.
  `JEV_BROWSER=chrome` uses upstream's Chrome connection instead.
- **Typing is held**: upstream's small text model has no gated route, so it
  is switched off. A step that must type text stops with an error before
  anything is typed.

## Credentials

The agent and its command line pass no provider key. The proxy loads
`OPENROUTER_API_KEY` itself from
`~/.config/verbose-broccoli/providers/openrouter.env`, a file readable by the
user alone (folder mode `0700`, file mode `0600`). Create it once, empty,
then add the key line. The second command does nothing when the file exists,
so it never empties a file that already holds a key:

```sh
providers="$HOME/.config/verbose-broccoli/providers"
install -d -m 700 "$providers"
[ -e "$providers/openrouter.env" ] ||
  install -m 600 /dev/null "$providers/openrouter.env"
```

| File in `providers/` | Line | Read by |
| --- | --- | --- |
| `openrouter.env` | `OPENROUTER_API_KEY=<key>` | The gated proxy, on every start |
| `github.env` | `GITHUB_TOKEN=<token>` | The `credit-offers` search's GitHub API requests; a token with no extra permissions is enough |

Never print a key file, paste a key into a prompt, or commit it. Install the
proxy's npm closure once with `mise run setup`.

## Run

From the repository root, with Orca running:

```sh
uv run --frozen --offline --no-sync \
  --package jev-ultrafast \
  python packages/jev-ultrafast/examples/run.py \
  --url 'https://en.wikipedia.org/wiki/Main_Page' \
  --goal 'Find and open the Wikipedia article about Gödel’s incompleteness theorems.'
```

Repeat `--goal` for an ordered list of goals. The command prints the elapsed
time, the number of actions and the status after each step, then the final
URL. Each step asks Jev once for the operation and, when that operation has
two or more elements to choose between, once more for the element: one or
two paid calls. Report the number of steps.

## Limits

- Run one browser job at a time. Other sessions share Orca's browser; the
  agent touches only the tab it opened.
- Screenshots and mouse-wheel scrolling need the tab to be drawn on screen.
  On a tab that is not visible they can stall until they time out, so keep
  the worktree's browser visible for goals that need scrolling.
- Each step starts the gated proxy once; the decision time shown for a step
  includes that start.
- A `DONE` step is not proof: check the outcome on the page yourself.
- Upstream does not handle shadow roots, frames, canvas, uploads, pop-up
  tabs, nested scrolling or arbitrary keyboard widgets.
- Without Orca, or when `orca` is not on `PATH`, Orca mode stops with an
  error; set `JEV_BROWSER=chrome` to use Chrome.
