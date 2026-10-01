# Implementation Plan: Root Configuration Boundaries

**Branch**: `feature/root-config` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Give each concern one owner: the mise file for the environment (versions,
`setup`, doctor), tool configs for code rules, `package.json` for commands and
`turbo.json` for the check graph. Fold or move nine root files, remove the
copies of tool versions and setup steps, and give each Python package its own
Turborepo `test` and `check` tasks ([research.md](research.md)).

## Reuse

| Need | Existing tool | Own code |
| --- | --- | --- |
| Find `.config/mise.toml` and its lock | mise discovers `.config/mise.toml` and writes `.config/mise.lock` (D1) | none |
| One setup | mise task `setup` (`mise run`) | the task's command list, moved from `orca.yaml` and `check.yml` |
| Install only the repository's tools, not the user's global ones | `mise ls --local`, `mise install --locked` | one command substitution (D2) |
| Find lefthook, commitizen, ruff, prettier config | lefthook's `.config/lefthook.yml`, `[tool.commitizen]`, `[tool.ruff]`, the `prettier` key (D1) | none |
| ls-lint and dependency-cruiser config | their `-config` and `--config` options | the new path in two commands |
| Per-package check graph | Turborepo 2.11.5 Python workspaces | `turbo.json` tasks (D4, D5) |
| Prove it | `turbo run --dry=json`, Node's test runner, Ruff's `--show-settings` | `scripts/root-config-test.ts` (D8) |

## Constitution Check

- Reuse order: every moved config stays in its upstream tool's own format and
  location; local code is the `setup` command list and one test file.
- No compatibility copies (principle VII); no empty placeholders (IX) — the
  `tools/none` workspace entry is replaced by the real `packages/*` glob.
- Verification passes only on the exit status and the same run's summary.
- The constitution is not changed, so its version does not change.

## Project Structure

```text
.config/mise.toml, mise.lock   tool versions, setup task, doctor checks
.config/lefthook.yml           Git hooks
.config/ls-lint.yml            name rules
.config/dependency-cruiser.json  import rules
pyproject.toml                 + [tool.commitizen], [tool.ruff]
package.json                   + "prettier"; workspaces; scripts
turbo.json                     per-package test and check tasks
orca.yaml, .github/workflows/  call `mise run setup`
scripts/root-config-test.ts    layout, pins, setup and graph tests
specs/042-root-config/         these records
```

## Workers

Main (Claude Code, Sonnet at high effort, chosen with two Jev judgments:
agent `claude` 0.90 with confidence 0.89, model `claude_sonnet_high` 0.44 with
confidence 0.36; a probability is not evidence of correctness) implements the
change. The develop merge reviewer comes from a provider other than Claude
Code, chosen with the `model-choice` skill; `tasks.md` names it.
