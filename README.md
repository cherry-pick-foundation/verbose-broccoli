# verbose-broccoli

A personal workspace of agent tools for education and knowledge work: Agent
Skills, command-line tools and Model Context Protocol (MCP) servers in three
areas, `code`, `work` and `chat`. [docs/architecture.md](docs/architecture.md)
describes the layout and repository tasks, and the
[command reference](docs/reference/commands.md) lists every root command.

Development follows the [constitution](.specify/memory/constitution.md), Spec
Kit feature ledgers under `specs/` and the repository's coding guidelines. Each
capability is specified anew from current needs.

For a new checkout, trust its mise configuration and run `mise run setup`.
Codex and Claude Code find the skills with no further step: edit canonical
skills under `skills/<area>/` (Ponytail's under `tools/ponytail/skills/`, the
work area's still under `plugins/work/skills/`); `.agents/skills` indexes them
through relative links, and `.claude/skills` links to that index. The `jev-mcp` and
`reference-library` servers are registered once per agent in the user's own
settings; the repository adds no project MCP configuration.
The upstream `jev` skill calls one registered `jev-mcp` server: a FastMCP
proxy with an always-on education privacy gate in front of unmodified
`@jkudish/jev-mcp` 0.13.0 over OpenRouter (`typesafe/jev-1.13`).
Model-choice evidence still forbids student data and other personal records.
See the [Jev MCP operator guide](docs/jev-mcp.md) for calls and privacy limits.
See [local discovery and reload limits](docs/architecture.md#live-checkout-discovery).

## Installing elsewhere

The repository ships no installer. To use a skill or server in another project
or agent, run Vercel's `skills` or Neon's `add-mcp` yourself:

```sh
DISABLE_TELEMETRY=1 npx skills add <path or repository> --skill <name> -a claude-code -a codex
npx add-mcp "<command>" --name <name> -a <agent>
```

`add-mcp` cannot block tools, so add the reference library's delete and
empty-trash restrictions by hand. Do not use its `sync` command, which renames
servers, or `find`, which contacts a registry. A skill's pointer to
`../AGENTS.md` leaves the skill folder and serves this repository only; the
portable `clean-code` skill carries everything it needs inside its folder.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
Third-party components retain their upstream licenses; see
[licenses/third-party-notices.md](licenses/third-party-notices.md).
