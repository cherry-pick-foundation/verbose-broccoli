# Implementation Plan: Free-Quota Agents in Model Choice

**Branch**: `feature/model-choice-free-agents` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Add Antigravity, Grok and Cursor to the code plugin's `model-choice`
reference as candidates, with their live catalogs, usage reads and launch
paths. Make the task's difficulty and every candidate's remaining usage part
of the evidence, and pin the judgment to backfire's Jev profile with
CHE-69's `serve-mcp --profile` option. Let the three agents give develop
merge reviews. No new code: the change is documents, two printed sentences
and their test, and one cherry-picked backfire commit.

## Reuse

| Need | Existing tool | Own code |
| --- | --- | --- |
| List each agent's models | `agy models`, `grok models` and `~/.grok/models_cache.json`, `cursor-agent models` | none |
| Read Grok's and Cursor's usage | Orca 1.4.218 `orca account list --json` (`rateLimits.grok.weekly`, `rateLimits.cursor.monthly`) | none |
| Read the other providers' usage | CodexBar, as the reference already does | none |
| Report a task's difficulty | `npm run workflow` (policy `coding-difficulty/1`) | none |
| Pin judgments to Jev | backfire `serve-mcp --profile`, cherry-picked unchanged from CHE-69 (93c5f5d) | none |
| Start workers | Orca `worker-start --agent antigravity|cursor --model`; the terminal path for Grok, whose model Orca cannot pass | none |
| Constitution version | commitizen through `npm run constitution:bump` | none |

## Technical Context

- Orca 1.4.218 starts antigravity, cursor and grok natively. `worker-start
  --model` accepts Antigravity and Cursor models; for Grok it fails with
  `invalid_argument` ("does not support launch-time model selection"), so a
  Grok worker with a chosen effort starts through an Orca terminal running
  `grok -m <model> --reasoning-effort <effort> --permission-mode
  bypassPermissions` (the auto-approve flag Orca itself uses for Grok).
- `orca account list --json` carries account identity (`usageMetadata`,
  account lists); the evidence keeps only the rate windows.
- Antigravity's usage shows in Orca only through a Gemini CLI sign-in, which
  is not installed, and `agy` has no usage command, so it stays unknown.
- Backfire's shipped order is `openrouter` (Jev), then `hive` (DeepSeek).
  `serve-mcp --profile openrouter` keeps only the first, so an empty balance
  fails instead of switching.

## Constitution Check

- Reuse order: existing tools only; the backfire change is an upstream
  commit from a sibling feature, used unchanged.
- Development Workflow: the develop merge sentence names three more
  providers; a `feat` commit raises the constitution from 2.5.0 to 2.6.0.
- Student data: only Claude Code and Codex read it (`AGENTS.md`, "Review").

## Project Structure

```text
AGENTS.md                                         review rule
.specify/memory/constitution.md, .cz.toml          develop merge sentence, 2.6.0
scripts/workflow.ts, scripts/workflow-test.ts      printed review and difficulty sentences
docs/architecture.md                               develop merge review paragraph
plugins/code/skills/model-choice/SKILL.md          description
plugins/code/skills/model-choice/references/model-choice.md
packages/backfire/                                 cherry-picked --profile option
specs/037-model-choice-free-agents/                these records
~/.claude/rules/worker-dispatch.md                 launch notes (outside the repository)
```

## Workers

Main implements the documents. Each test worker's and reviewer's agent, model
and effort come from the `model-choice` skill with Jev-only judgments;
`tasks.md` names them under their tasks.
