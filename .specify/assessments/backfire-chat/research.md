# Idea Research: Backfire for the chat plugin

- **Slug**: backfire-chat
- **Created**: 2026-09-28
- **Evidence confidence (overall)**: high

## Users & Demand

- The user's answers of 2026-09-28, relayed by the develop session: the plan is
  ChatGPT Plus or Pro, not Business or Enterprise/Edu; the user does not use
  Claude Desktop; the chat plugin is for the web chat apps of OpenAI and
  Anthropic, and for now only ChatGPT on the web; the ChatGPT desktop app is not
  the target; claude.ai on the web comes later. — [source: user answers through
  Orca `ask`] (confidence: high)
- Look-only check on 2026-09-28 in Orca's built-in browser, with the user logged
  in to chatgpt.com: **Settings > Security and login** has no Developer mode
  switch, and **Settings > Plugins** has no developer or advanced setting.
  Nothing was clicked or changed. — [source: direct observation] (confidence:
  high)
- The Platform tunnel settings page was not checked: it needed a separate
  login, and its result could not change the outcome once developer mode was
  missing (see Market & Context). — [source: direct observation] (confidence:
  high)

## Prior Art

- Feature 011 builds backfire only for `code` and `work`; the plugin table has
  no `chat` row (`packages/backfire/src/backfire_tools/build.py:13-16`), and a
  `chat` build fails before writing anything
  (`specs/011-backfire-education/contracts/build.md:42`). — [source: repository]
- Backfire serves only stdio: "The eleven ported tools on the MCP SDK's
  low-level stdio server" (`packages/backfire/src/backfire/server.py:1`, using
  `mcp.server.stdio.stdio_server` at line 12). Its tools declare no MCP
  annotations; `rg -n "readOnlyHint|annotations" packages/backfire/src` finds
  nothing. — [source: repository]
- Constitution IX says: "The chat package has no skills yet and no Deno/MCP
  declarations or scripts" (`.specify/memory/constitution.md:140`), so any chat
  build would need an amendment. — [source: repository]

## Market & Context

- **ChatGPT on the web** connects only to remote servers. OpenAI's Help Center,
  "Developer mode and MCP apps in ChatGPT" (updated "last month" when read on
  2026-09-28): "Can I connect to a local MCP server? Not directly. ChatGPT
  connects to remote MCP servers. If your MCP server runs on a private network,
  on-premises, or on a developer machine, use Secure MCP Tunnel". — [source 1]
  (confidence: high)
- A custom MCP server reaches ChatGPT only as a developer-mode app. OpenAI's
  developer guide: "Select the plus button and create a developer-mode app for
  your remote MCP server. … The plus button will only create developer-mode apps
  after you turn on Developer mode." Supported protocols are "SSE and streaming
  HTTP". — [source 2] (confidence: high)
- OpenAI's sources disagree on which plans get developer mode. The developer
  guide says "Available to Pro, Plus, Business, Enterprise, and Education
  accounts on the web" [source 2]. The Help Center says "Full MCP is only
  available to Business and Enterprise/Edu users, currently. Pro users can
  connect MCPs with read/fetch permissions in developer mode", and does not
  mention Plus [source 1]. The testing guide says "Developer mode availability
  can depend on account and workspace policy" [source 3]. The account check
  above settles it for this account today. (confidence: high)
- **Secure MCP Tunnel** runs `tunnel-client` on the user's machine. It starts a
  stdio server itself (`--mcp-command`) and makes only outbound HTTPS to
  `api.openai.com:443`. It needs a `tunnel_id` from Platform tunnel settings, a
  runtime API key, and Tunnels Read + Manage or Use in a Platform organization;
  "For personal accounts, use the personal Platform organization that belongs to
  that account". In ChatGPT it is used only through a developer-mode app: "Go to
  ChatGPT Plugins, select the plus button to create a developer-mode app, and
  choose **Tunnel** under **Connection**." — [source 4] (confidence: high)
- **A public HTTPS endpoint** through a forwarding service is the other
  documented route ("A development tunnel or another HTTPS forwarding service
  can also provide an endpoint for local testing" [source 3]). It also needs a
  developer-mode app. It would also need a streamable HTTP transport, which
  backfire lacks, and authentication. Without that, anyone who has the URL could
  spend the user's provider key. — [source 3; transport from the repository]
  (confidence: high)
- **The ChatGPT desktop app** can run local stdio servers on Plus and Pro, but
  only in local chats on its Codex host. "The ChatGPT desktop app, Codex CLI, and
  IDE extension support MCP servers and share MCP configuration for the same
  Codex host"; "ChatGPT web doesn't read local Codex configuration files"
  [source 5]. The plan table lists "ChatGPT desktop app for local chats" as
  available for Plus and Pro [source 6]. The user works on the web. (confidence:
  high)
- **Claude Desktop** installs local MCP servers as desktop extensions (`.mcpb`)
  or by manual JSON configuration [source 7], and "is available for macOS and
  Windows" [source 8]. Backfire imports `fcntl`, which Windows Python lacks
  (`packages/backfire/src/backfire/records.py:5`,
  `packages/backfire/src/backfire_education/table.py:4`). The user does not use
  Claude Desktop. (confidence: high)
- **claude.ai on the web** was not assessed; the user placed it outside this
  issue.

## Data & Constraints

- Backfire judges education records. Its pseudonymization covers only what
  backfire sends to its provider; the chat agent itself reads the records it is
  given (`docs/backfire.md:104-108`). — [source: repository]
- OpenAI marks developer mode as elevated risk and warns of "prompt injections
  and other risks" and "malicious MCPs that attempt to steal information"
  [source 2]. Tools without `readOnlyHint` "are treated as write actions"
  [source 2]. Under the Help Center's read/fetch-only rule for Pro [source 1],
  backfire's unannotated tools may be refused. Annotating them would change the
  shared server for every build and add a recorded upstream deviation.
  (confidence: medium; not tested)

## Evidence Against the Idea

- This account has no Developer mode switch, and every documented route from
  ChatGPT on the web to a custom MCP server, whether a public URL or Secure MCP
  Tunnel, goes through a developer-mode app. — [direct observation; sources 2
  and 4]
- The two clients that can start a local stdio server (the ChatGPT desktop app
  and Claude Desktop) are not ones the user works in. — [user answers]
- Even with developer mode, Pro may allow read/fetch tools only [source 1], and
  a tunnel needs a Platform API key and a client that runs whenever the user
  chats [source 4].

## Gaps & Open Questions

- Why the Developer mode switch is missing (plan, rollout or account policy) is
  unknown; OpenAI's pages disagree [sources 1-3].
- Whether a Plus or Pro personal account can list a tunnel in ChatGPT is
  documented only for personal Platform organizations [source 4] and was not
  tested.
- No tunnel pricing is documented [source 4].

## Sources

1. <https://help.openai.com/en/articles/12584461-developer-mode-apps-and-full-mcp-connectors-in-chatgpt-beta>
   (host: help.openai.com, policy: confirmed-by-user; the user asked for
   OpenAI's current documentation)
2. <https://developers.openai.com/api/docs/guides/developer-mode> (host:
   developers.openai.com, policy: confirmed-by-user)
3. <https://developers.openai.com/plugins/deploy/connect-chatgpt> (host:
   developers.openai.com, policy: confirmed-by-user)
4. <https://developers.openai.com/api/docs/guides/secure-mcp-tunnels> (host:
   developers.openai.com, policy: confirmed-by-user)
5. <https://learn.chatgpt.com/docs/extend/mcp> (host: learn.chatgpt.com,
   policy: confirmed-by-user)
6. <https://learn.chatgpt.com/docs/pricing> (host: learn.chatgpt.com, policy:
   confirmed-by-user)
7. <https://support.claude.com/en/articles/10949351> (host: support.claude.com,
   policy: confirmed-by-user)
8. <https://modelcontextprotocol.io/docs/develop/connect-local-servers> (host:
   modelcontextprotocol.io, policy: confirmed-by-user)
