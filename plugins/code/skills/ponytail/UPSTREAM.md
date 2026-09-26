# Packaged Ponytail skills

- Source: https://github.com/DietrichGebert/ponytail
- Version: v4.9.0
- Commit: `0a4dd63ad4541f4f655c4108a295916f3c1d8fda`
- Imported: `skills/ponytail{,-audit,-debt,-gain,-help,-review}/SKILL.md`.
- License: MIT; upstream LICENSE is retained in each skill folder.
- Removed 2026-09-25: `ponytail-help` (a reference card that repeated this
  record and the `ponytail` skill) and `ponytail-gain` (a display of upstream
  benchmark figures). The other four imported skills are unchanged.
- Upstream's six JavaScript hook modules and `tests/hooks.test.js` are retained
  byte-for-byte under `plugins/code/hooks` and `plugins/code/tests`.
  The hook license is retained at `plugins/code/hooks/LICENSE`. The original
  instruction loader reads `../skills/ponytail/SKILL.md` inside the same package.
- `.agents/ponytail` links to `../plugins/code`, preserving existing hook
  command definitions and their trust hashes after the source move.
- `.codex/hooks.json` preserves existing hooks and adds SessionStart,
  SubagentStart and UserPromptSubmit from upstream's `claude-codex-hooks.json`.
  Commands resolve the Git root and set `PLUGIN_DATA` to the absolute Git-local
  `ponytail` directory. The Linux VM uses the installed Node runtime; the
  upstream Windows launch override is not registered in this Linux profile.
- Global configuration is not changed by installation. The six skills use
  their standalone names, such as `ponytail-review`; the existing workflow's
  `ponytail:ponytail-review` refers to this same review skill.
