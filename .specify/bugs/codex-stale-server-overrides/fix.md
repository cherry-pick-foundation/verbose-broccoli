# Bug Fix: Codex cannot start in the repository after two user servers were removed

- **Slug**: codex-stale-server-overrides
- **Fixed**: 2026-10-04
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The project Codex configuration no longer turns off the `llm-wiki` and
`duckdb` servers, which the user removed from the user configuration on
2026-10-03. A test now requires every server table in the project
configuration to declare a transport.

## Changes

| File | Change | Notes |
| ---- | ------ | ----- |
| `.codex/config.toml` | configuration | Deleted `[mcp_servers.llm-wiki]`, `[mcp_servers.duckdb]` and their comment. |
| `scripts/plugin-skills-test.ts` | test | New case: each `[mcp_servers.<name>]` table has a `command` or `url`. |

## Tests Added or Updated

`plugin skills: project Codex servers declare a transport` fails on the old
configuration with `mcp_servers.llm-wiki: no transport` and passes after the
deletion.
