# Packaged Ponytail skills

- Source: https://github.com/DietrichGebert/ponytail
- Version: v4.9.0
- Commit: `0a4dd63ad4541f4f655c4108a295916f3c1d8fda`
- Imported: `skills/ponytail{,-audit,-debt,-gain,-help,-review}/SKILL.md`.
- License: MIT; upstream LICENSE is retained in each skill folder.
- Removed 2026-09-25: `ponytail-help` (a reference card that repeated this
  record and the `ponytail` skill) and `ponytail-gain` (a display of upstream
  benchmark figures). The four retained skills add only the plugin-rule pointer.
- Upstream's six JavaScript hook modules and `tests/hooks.test.js` are retained
  under `tools/ponytail/hooks` and `tools/ponytail/tests`. The instruction
  loader resolves the rules pointer to the bundle's `AGENTS.md` by absolute
  path before injecting the skill text; the other modules and upstream tests
  remain byte-for-byte unchanged. `tools/ponytail/AGENTS.md` is the only added
  file: it points to the code area rules.
  The hook license is retained at `tools/ponytail/hooks/LICENSE`. The original
  instruction loader reads `../skills/ponytail/SKILL.md` inside the same bundle.
- `.agents/ponytail` links to `../tools/ponytail`, preserving existing hook
  command definitions and their trust hashes after the source move.
- `.codex/hooks.json` preserves existing hooks and adds SessionStart,
  SubagentStart and UserPromptSubmit from upstream's `claude-codex-hooks.json`.
  Commands resolve the Git root and set `PLUGIN_DATA` to the absolute Git-local
  `ponytail` directory. The Linux VM uses the installed Node runtime; the
  upstream Windows launch override is not registered in this Linux profile.
- Global configuration is not changed by installation. The six skills use
  their standalone names, such as `ponytail-review`; the existing workflow's
  `ponytail:ponytail-review` refers to this same review skill.
