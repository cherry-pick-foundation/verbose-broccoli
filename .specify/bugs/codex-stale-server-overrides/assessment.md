# Bug Assessment: Codex cannot start in the repository after two user servers were removed

- **Slug**: codex-stale-server-overrides
- **Created**: 2026-10-04
- **Source**: pasted text (found by the main Claude Code session on
  2026-10-04 while checking Codex after a checkout move; no Linear issue yet,
  because the develop orchestrator that files issues runs on Codex and could
  not start)
- **Verdict**: valid
- **Severity**: high

## Report (summarized)

Codex CLI 0.160.0 exits before it starts in every verbose-broccoli checkout,
including the develop orchestrator's:

```text
Error: failed to load bootstrap configuration

Caused by:
    invalid transport
    in `mcp_servers.llm-wiki`
```

The same command started from the home folder works.

## Symptom

Any Codex command run inside a checkout, such as `codex mcp list`, fails with
the error above. It should load the project configuration and start.

## Reproduction

1. Have no `llm-wiki` or `duckdb` server in the user configuration
   (`~/.codex/config.toml`).
2. In any checkout, run `codex mcp list`: it fails with the error above.
3. Run it from the home folder: it lists the servers.

## Suspected Code Paths

- `.codex/config.toml:22-28` — `[mcp_servers.llm-wiki]` and
  `[mcp_servers.duckdb]` hold only `enabled = false`, to keep two user-level
  servers out of this project. They have no `command` or `url`.

## Root Cause Hypothesis

Codex merges the project tables into the user's server definitions. The two
entries were added on 2026-09-27 (21d7fc4) to turn off user-level servers of
the same names. On 2026-10-03 the user removed those servers with
`codex mcp remove` when uninstalling the ChatGPT desktop app. Each project
entry is now a whole server definition with no transport, which Codex rejects
while loading. Confidence: high; with the two entries deleted,
`codex mcp list` starts in the checkout.

## Proposed Remediation

**Preferred**: delete both entries and their comment. The servers they turned
off no longer exist, so nothing else changes.

**Files likely to change**:

- `.codex/config.toml`
- `scripts/plugin-skills-test.ts`

**Tests to add or update**:

- Every `[mcp_servers.<name>]` table in the project configuration declares a
  `command` or a `url`.

## Risks & Considerations

- If the user adds a server named `llm-wiki` or `duckdb` again, it becomes
  available in this project too. The test then rejects bringing back an
  override that holds only `enabled = false`, so that choice needs a full
  server definition or another route.

## Open Questions

- None.
