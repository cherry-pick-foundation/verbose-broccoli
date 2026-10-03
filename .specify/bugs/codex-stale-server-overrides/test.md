# Bug Verification: Codex cannot start in the repository after two user servers were removed

- **Slug**: codex-stale-server-overrides
- **Tested**: 2026-10-04
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: pass

## Summary

Codex starts in the fixed checkout, and the new test fails without the fix.

## Checks Performed

| Check | Command / Action | Result | Notes |
| ----- | ---------------- | ------ | ----- |
| Codex start | `codex mcp list` in the fix worktree (Codex CLI 0.160.0) | pass | Lists the servers; before the fix it failed with `invalid transport in mcp_servers.llm-wiki`. |
| New test without the fix | `node --test --test-name-pattern='declare a transport' scripts/plugin-skills-test.ts` | fail, as expected | `mcp_servers.llm-wiki: no transport` |
| New test with the fix | Same command | pass | |
| Repository check | `npm run verify` | pass | VERIFIED; 47 of 47 tasks successful. |
| Complexity review | `ponytail-review`'s `SKILL.md`, applied by reading it; the skill was not in Claude Code's catalogue | pass | Nothing to cut. |
