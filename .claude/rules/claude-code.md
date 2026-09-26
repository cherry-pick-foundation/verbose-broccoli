# Claude Code in this repository

These rules add to the root `AGENTS.md` for Claude Code only.

- Claude Code coordinates here: it owns Spec Kit documents, planning,
  integration, and repository prose, and it dispatches implementation to Codex
  workers.
- Review Codex-implemented changes yourself. When you implement a change
  yourself, a Codex worker reviews it.
- Keep this repository free of `CLAUDE.md`, `.claude/CLAUDE.md`, and
  `CLAUDE.local.md`. Any of them stops Claude Code from reading `AGENTS.md`
  files. Put Claude-only rules in `.claude/rules/` instead.
