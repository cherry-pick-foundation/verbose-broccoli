# Implementation Plan: Copilot as a Reviewer and a Model-Choice Option

**Branch**: `feature/copilot-option` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

## Summary

Check CodexBar 0.69.0's Copilot provider read-only, then let the code
plugin's `model-choice` reference read Copilot's allowance with it and offer
Copilot models as candidates. Name Copilot among the providers that may give
the final review, in AGENTS.md, the constitution, the text `npm run workflow`
prints and `docs/architecture.md`. Test one Copilot worker through Orca's
terminal path and send the develop session the launch steps. No new code:
the change is documents, one printed sentence and its test.

## Reuse

| Need | Existing tool | Own code |
| --- | --- | --- |
| Read Copilot's allowance | CodexBar 0.69.0 `usage --provider copilot`, already installed for the other providers | none |
| List Copilot's models | Copilot CLI 1.0.88 `copilot help config` | none |
| Start a Copilot worker | Orca's terminal path (`terminal create`, `terminal wait`, `worker-start --terminal`) | none |
| Choose the reviewer and the test worker's model | the `model-choice` skill with backfire's `jev_decide` | none |
| Constitution version | commitizen through `npm run constitution:bump` | none |

## Technical Context

- CodexBar's Copilot provider reads a GitHub token and calls GitHub's Copilot
  usage endpoint; the security check decides whether and how it may run.
- The Copilot CLI draws on the Copilot Free plan's monthly allowance, which
  resets on the first of the month (next on 2026-10-01).
- Orca 1.4.217 recognizes the Copilot CLI but its model catalog does not
  cover it, so `worker-start --agent` cannot pass a Copilot model.

## Constitution Check

- Reuse order: only existing tools; no local implementation.
- Development Workflow: the develop merge review comes from a provider other
  than the implementer's; this feature amends that sentence to name Copilot,
  with a minor version bump in a `feat` commit.
- Evidence: every security finding carries file:line evidence.

## Project Structure

```text
AGENTS.md                                         review rule
.specify/memory/constitution.md, .cz.toml          review sentences, 2.5.0
scripts/workflow.ts, scripts/workflow_test.ts      printed review sentence
docs/architecture.md                               review sentence
plugins/code/skills/model-choice/SKILL.md          description
plugins/code/skills/model-choice/references/model-choice.md
specs/031-copilot-option/                          these records
```

## Workers

Each worker's agent, model and effort come from the `model-choice` skill;
`tasks.md` names them under their tasks.
