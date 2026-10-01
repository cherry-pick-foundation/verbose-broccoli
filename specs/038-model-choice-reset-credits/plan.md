# Implementation Plan: Reset Credits in Model Choice

**Branch**: `feature/model-choice-reset-credits` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Add Codex's usage-limit reset credits to the evidence in the code plugin's
`model-choice` reference, "Usage limits", as CHE-70 (feature 037) did for the
other usage reads. No new code: documents only.

## Reuse

| Need | Existing tool | Own code |
| --- | --- | --- |
| Read reset credits | CodexBar 0.69.0 `usage --provider codex --source oauth` (`usage.codexResetCredits`), already the reference's Codex read | none |
| Strip identity and credit IDs | `jq`, as the reference already does | none |
| Pin judgments to Jev | backfire `serve-mcp --profile openrouter` (feature 037) | none |

## Constitution Check

- Reuse order: existing tools only.
- Only the user spends reset credits (the user's decision of 2026-10-01).

## Project Structure

```text
plugins/code/skills/model-choice/references/model-choice.md   "Usage limits"
docs/architecture.md                                           CodexBar sentence
specs/038-model-choice-reset-credits/                          these records
```

## Workers

Main implements the documents. The develop merge reviewer's agent, model and
effort come from the `model-choice` skill with Jev-only judgments; `tasks.md`
names them.
