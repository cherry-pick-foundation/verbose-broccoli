# Decision: Backfire for the chat plugin

- **Slug**: backfire-chat
- **Decided**: 2026-09-28
- **Verdict**: kill
- **Artifacts reviewed**: intake.md | research.md | problem.md

## Scorecard

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Problem validity | adequate | The user wants backfire in the chat app they use, but only ChatGPT on the web is in scope. |
| Evidence strength | strong | OpenAI's pages were quoted as read on 2026-09-28, and the account was checked directly. |
| Value vs. inaction | weak | No route works on this account, and inaction breaks nothing. |
| Feasibility / appetite | weak | Every route from ChatGPT on the web to a custom MCP server needs developer mode, which this account lacks; no concept was shaped. |
| Strategic fit | adequate | A chat build would need a constitution IX amendment; the user's earlier Claude Desktop choice included one ([intake.md](intake.md#origin--context)). |
| Risk posture | adequate | The risks are known: developer mode's elevated risk, a key-spending public endpoint (rejected), and data passing through OpenAI's tunnel service. None was tested. |

## Verdict & Rationale

Kill. ChatGPT on the web connects to a custom MCP server only through a
developer-mode app, whether the server is public or behind Secure MCP Tunnel.
This account shows no Developer mode switch on 2026-09-28
([research.md](research.md#users--demand)). The clients that can start
backfire locally are ones the user does not work in. On 2026-09-28 the user
decided to close CHE-10 without a build and to end it as Done. No code, plugin
manifest or constitution text changes.

## Dropped Paths

| Path | Why dropped |
|------|-------------|
| Claude Desktop, registered by command or as a `.mcpb` extension | The user does not use it. It runs only on macOS and Windows, and backfire's `fcntl` import rules out Windows. |
| ChatGPT desktop app, local chats | It works on Plus and Pro, but only in local chats; the user works on the web. |
| ChatGPT on the web through Secure MCP Tunnel | It needs a developer-mode app, which this account cannot create. |
| ChatGPT on the web through a public HTTPS forwarding service | It needs a developer-mode app too, plus a streamable HTTP transport and authentication so no stranger can spend the provider key. |
| claude.ai on the web | Out of scope; the user placed it in a later issue. Not assessed. |

## Reopen Triggers

Reopen CHE-10, or open a new issue, when one of these holds:

1. **Developer mode appears** under ChatGPT **Settings > Security and login**
   for the user's account, after a plan change or OpenAI's rollout. Then first
   recheck the open points in [research.md](research.md#gaps--open-questions):
   whether the account can list a tunnel, and what a tunnel costs. If both
   allow it, shape the chat build: a `chat` row in the build table with its
   own `chat` profile, the `backfire` declaration in `plugins/chat/mcp.json`, a
   constitution IX amendment, and operator steps for Secure MCP Tunnel. Also
   check whether the account allows only read/fetch tools; if so, backfire's
   eleven tools would need `readOnlyHint`, a recorded upstream deviation.
2. **The user starts working in a client that runs local stdio servers**: the
   ChatGPT desktop app's local chats, or Claude Desktop on macOS.
3. **claude.ai on the web comes into scope.** It has not been assessed.
