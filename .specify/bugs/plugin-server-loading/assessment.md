# Bug Assessment: Plugin servers do not load with their intended modes

- **Slug**: plugin-server-loading (provided by the dispatch)
- **Created**: 2026-10-02
- **Source**: [CHE-78](https://linear.app/verbose-broccoli/issue/CHE-78), including its current comment; `linear.app`, allowlisted, read through Orca.
- **Verdict**: valid
- **Severity**: high

## Assumption and symptom

Backfire and the reference connector remain checkout dependencies. Preparing a
local client distribution does not authorize changing saved client settings or
publishing a package. Code and Work must have distinct Backfire server names;
Work must always start its education mode.

Claude Code 2.1.286 ignores the portable root MCP declaration without a native
manifest pointing to it. Codex 0.159.2 reads the portable declaration but keeps
Code's `backfire` when Work declares the same name. A copied plugin's current
`${PLUGIN_ROOT}/../../packages/backfire` also no longer points to this checkout.

## Reproduction and current evidence

Synthetic local plugins were installed using `codex plugin marketplace add`
and `codex plugin add` with an isolated `CODEX_HOME`. `codex mcp list --json`
returned only Code's server. With an isolated `CLAUDE_CONFIG_DIR`, Claude's
`mcp list` returned no servers until each native manifest declared
`mcpServers: "./mcp.json"`; it then attempted both namespaced servers.
Claude left `${PLUGIN_ROOT}` literal while expanding `${CLAUDE_PLUGIN_ROOT}`.
Only the server-name keys in the saved Code and Work cache declarations were
read: both lists remain empty. No private configuration or credentials were read.

## Cause and remediation

The client loaders differ, plugin server names collide, and Codex installs a
copy. Keep `plugins/*/plugin.json` and `plugins/*/mcp.json` canonical. Prepare
one ignored, bounded local distribution with checkout paths resolved and a
Claude manifest pointing to its same portable `mcp.json`. Use the clients'
supported local plugin and marketplace loading paths. Give the modes distinct
names, reject duplicate names before publishing generated output, and leave
the Backfire server unchanged.

The relevant consumers are `scripts/plugin-skills-test.ts`, the manifest checks
in `package.json`, `scripts/doc_sources.py::plugin_table`, and each client's
loader. The connector command in Work's declaration also needs its dependency
path resolved, without connecting to real reference-library data during tests.

## Upstream fit and acceptance

[Codex's official packaging guide](https://developers.openai.com/plugins/build/plugins)
supports portable declarations and local marketplace installs. [Claude's
manifest reference](https://code.claude.com/docs/en/plugins-reference#mcpservers)
supports an MCP file path. Their native loading features handle discovery.
[AgentPlugins](https://github.com/sigilco/agentplugins) is a separate manifest
compiler and installation framework, outside the requested layout.
[agent-plugins](https://peter-gy.github.io/agent-plugins/reference/mcp-json)
resolves validated subprocess declarations but does not distribute checkout
dependencies to these clients. Native filesystem and JSON operations suffice
for the remaining preparation glue.

Acceptance requires a failing-before-fix regression, isolated client lists and
startup behavior, Work's education refusal and continued service after bad
input, source readback, and full repository verification. Saved-client cache
refresh remains an approval boundary after the patch and preview are ready.
