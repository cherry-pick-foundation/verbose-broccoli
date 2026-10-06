# Claude Code in this repository

These rules add to the root `AGENTS.md` for Claude Code only.

- A change's final review comes from a provider other than the one that
  implemented it (`AGENTS.md`, "Review").
- Keep this repository free of `CLAUDE.md`, `.claude/CLAUDE.md`, and
  `CLAUDE.local.md`. Any of them stops Claude Code from reading `AGENTS.md`
  files. Put Claude-only rules in `.claude/rules/` instead.
- Before using a linked project skill, resolve its directory with filesystem
  `realpath`. Use that canonical directory as the base before constructing any
  relative Read or Bash path, including rules, references, helpers and assets.
  Read the owning area's `../AGENTS.md` from that canonical base before
  following the skill; do not resolve it from `.claude/skills`, `.agents/skills`
  or the session's working directory.
