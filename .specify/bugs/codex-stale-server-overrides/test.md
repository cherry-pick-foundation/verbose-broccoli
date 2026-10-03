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
| Document judgments | `npm run doc-regions:prepare -- --base develop --max-evidence-chars 20000` at cec8e55; a scratch client sent its 11 `jev_verify` requests to `backfire serve-mcp --profile openrouter` | pass | `typesafe/jev-1.13` on OpenRouter, 12 calls (one result was lost to a client-script error and its request resent). 352 units: 8 verified, 342 unsupported, 1 contradicted, 1 without an answer (`invalid_response`), 58 flagged for review. The contradicted unit, `AGENTS.md:3-8` (report-only), stands: `.codex/config.toml` still holds the Codex `developer_instructions`. The unanswered unit, `docs/architecture.md:335-341`, describes the work plugin's backfire and is unrelated. No flagged unit concerns this change, and no document names the removed servers. |
