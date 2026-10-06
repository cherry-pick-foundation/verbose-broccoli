# Contract: How Skills and MCP Servers Reach Agents

Claude Code and Codex find every skill and MCP server in each worktree of
this repository with no installer inside it (FR-003, U-2026-10-06g). This
contract holds after slice S2; held work-area skills keep their current
folder until hold H2 is released ([plan](../plan.md#holds)).

## Skills

| Item | Rule | Source |
| --- | --- | --- |
| Folder | `skills/<area>/<name>/SKILL.md`, areas `code`, `work`, `chat`; `name` in the front matter equals the folder name | U-2026-10-06h, R-UP-01 |
| Validity | `skills-ref validate` passes for every skill in verification | R-UP-01 |
| Uniqueness | one folder per name in the whole repository | FR-002 |
| Area rules | `skills/<area>/AGENTS.md`; each skill's first instruction points to it as `../AGENTS.md` | R-REPO-12, `.claude/rules/claude-code.md` |
| Discovery | `.agents/skills/<name>` is a committed relative link to `../../skills/<area>/<name>`; Codex scans `.agents/skills`; Claude Code reads `.claude/skills`, a committed link to `../.agents/skills` | R-UP-02 (project paths per agent), `docs/architecture.md` "Live checkout discovery" |
| Held skills | while H2 holds, `.agents/skills/<name>` links to `../../plugins/work/skills/<name>` | plan Holds |
| Upstream bundle | Ponytail's four skills stay at `tools/ponytail/skills/<name>/`; `.agents/ponytail` links to `../tools/ponytail`, so `.codex/hooks.json` is unchanged | plan Decision 10 |
| Portable skill | a skill meant to work when copied elsewhere carries its code in its own `scripts/`; today only `clean-code` | plan Decision 9, R-UP-02 |
| Upstream names | a skill taken from upstream keeps its upstream name and provenance file | U-2026-10-04a |

A check in verification fails when a link is broken, points outside
`skills/`, `tools/ponytail/skills/` or held `plugins/work/skills/`, when two
links reach the same folder, or when a skill folder has no link.

## MCP servers

The repository adds no project MCP configuration: no root `.mcp.json` and no
generated block in `.codex/config.toml`. Each server is registered once per
agent in the user's own settings.

| Server | Claude Code | Codex | Restrictions |
| --- | --- | --- | --- |
| `jev-mcp` | `~/.claude.json` `mcpServers` | `~/.codex/config.toml` `[mcp_servers.jev-mcp]` | always the gated proxy from the permanent `develop` checkout's `packages/education-privacy-gate` (FR-004, FR-021) |
| `reference-library` | `~/.claude.json` `mcpServers` | `~/.codex/config.toml` `[mcp_servers.reference-library]` | delete and empty-trash tools blocked: Claude deny rules in `~/.claude/settings.json`, Codex `disabled_tools` (FR-004) |
| second judgment server (GLM) | added when hold H1 is released | same | gated; see the [judgment contract](judgment.md) |

Changing these registrations changes user-scope settings, which needs the
user's approval; the main session makes such changes (spec Assumptions).

## Installing elsewhere

Documented in `README.md`, never run by repository code:

- A skill into another project or agent: `npx skills add <path or repository>
  --skill <name> -a claude-code -a codex`, with `DISABLE_TELEMETRY=1` or
  `DO_NOT_TRACK=1` so the command sends no usage data (R-UP-02).
- An MCP server into another agent: `npx add-mcp "<command>" --name <name>
  -a <agent>` (R-UP-03). `add-mcp` cannot block tools, so the reference
  library's delete and empty-trash restrictions are added by hand. Its `sync`
  command renames servers and `find` contacts a registry; neither is used.
- A skill's pointer to `../AGENTS.md` leaves the skill folder, which the
  Agent Skills specification does not expect (R-UP-01); it serves this
  repository only. A copied skill keeps working without it, and the portable
  `clean-code` skill carries everything it needs inside its folder.

## Retired

Plugin manifests (`plugin.json`, `mcp.json`), the Agent Plugins schema check,
`scripts/plugin-clients.ts` and its `plugins:*` commands, copied client
packages and the plugin reference table are removed (FR-005). Their durable
receipts under `$XDG_STATE_HOME/verbose-broccoli/workspaces/*/plugin-discovery/`
stay as history; deleting them is the user's choice.
