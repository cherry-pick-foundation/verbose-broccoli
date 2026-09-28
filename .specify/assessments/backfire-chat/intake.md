# Idea Intake: Backfire for the chat plugin

- **Slug**: backfire-chat
- **Created**: 2026-09-28
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-10> (Linear CHE-10,
  read with `orca linear issue CHE-10 --json`; host `linear.app`, allowlisted)
- **Type**: exploration

## Idea (as captured)

> Decide whether the chat plugin can use backfire, and assemble its variant if
> it can.
>
> Scope:
>
> - Check whether the ChatGPT and Claude chat apps that the chat plugin targets
>   can run a local MCP server, or need a remote connection.
> - If they can, assemble a chat variant from the modules built in CHE-9.
>
> Out of scope: the code and work variants.
> Depends on: CHE-9.

## Restated

Find out whether a chat client the user works in can reach backfire, the local
Model Context Protocol (MCP) server that feature 011 (CHE-9) builds for the code
and work plugins. If one can, add a chat build of it.

## Origin & Context

- **Raised by**: the user, in Linear CHE-10 (created 2026-09-27).
- **Trigger**: feature 011 made backfire buildable per plugin, with
  pseudonymization for education work, but only for `code` and `work`
  (`packages/backfire/src/backfire_tools/build.py:13-16`); a `chat` build is
  refused (`specs/011-backfire-education/contracts/build.md:42`).
- **Handover**: CHE-9's orchestrator created this worktree and handed CHE-10
  over on 2026-09-28. The handover task, sent through Orca by the develop
  session, recorded the user's choice from earlier that day: "A chat build for
  Claude Desktop: a chat row in CHE-9's per-plugin build table (backfire core
  plus pseudonymization, with its own chat profile), backfire declared in
  plugins/chat/mcp.json, and constitution IX amended; plus ChatGPT through
  OpenAI's Secure MCP Tunnel as an operator setup." The user's answers
  recorded in [research.md](research.md) replaced that choice before any
  implementation.

## First-Glance Unknowns

- Which chat clients the user actually uses, and on which plan.
- Whether those clients can start a local stdio MCP server or reach one on the
  user's machine.
- What a chat build would contain for a client that does not load Agent Plugins
  packages.
