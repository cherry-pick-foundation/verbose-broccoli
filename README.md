# verbose-broccoli

A personal workspace of three agent plugins for education and knowledge
work: `code`, `work` and `chat`. The [plugin reference](docs/reference/plugins.md)
lists their contents, and [docs/architecture.md](docs/architecture.md) describes
the layout and repository tasks.

Development follows the [constitution](.specify/memory/constitution.md), Spec
Kit feature ledgers under `specs/` and the repository's coding guidelines. Each
capability is specified anew from current needs.

For a new checkout, trust its mise configuration and run `mise run setup`.
With dependencies installed, `npm run plugins:prepare` refreshes live local
skills and project Model Context Protocol (MCP) configuration for Codex and
Claude Code. Edit canonical skills under `plugins/*/skills/`; `.agents/skills`
indexes them through relative links, and `.claude/skills` links to that index.
`backfire-code` forbids student
data; `backfire-education` retains its education privacy gate.
See [local discovery and reload limits](docs/architecture.md#live-checkout-discovery).
Before a normal git-flow finish, clean both develop and feature worktrees by
running `npm run plugins:clean-codex` separately to remove only their
receipt-owned generated Codex blocks; prepare and reload
the final develop project configuration again after integration.
Optional copied packages use `npm run plugins:distribute` separately; local
skill edits need neither reinstall nor a version bump.
Discovery ownership stays in XDG state storage; reproducible copied packages
stay in XDG cache storage. Both use the stable `plugin-discovery` operation
namespace and a checkout path hash to isolate same-named folders. Client discovery
files keep their supported project locations; `.local/` holds disposable editor copies.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
Third-party components retain their upstream licenses; see
[licenses/third-party-notices.md](licenses/third-party-notices.md).
