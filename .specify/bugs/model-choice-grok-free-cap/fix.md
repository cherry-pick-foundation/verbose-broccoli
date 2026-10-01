# Bug Fix: Model choice offers Grok after its free usage cap is hit

- **Slug**: model-choice-grok-free-cap
- **Fixed**: 2026-10-01
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The skill's reference no longer says Grok draws on a weekly credit pool. It
states the per-model 24-hour cap, says CodexBar and Orca do not show it, and
gives a `grep | jq` line that prints the latest `free-usage-exhausted` entry's
time, model and `actual/limit`, with the rule that Grok is unavailable for
that model until about 24 hours later. It also records the check of the other
free agents.

## Changes

| File | Change | Notes |
| ---- | ------ | ----- |
| `plugins/code/skills/model-choice/references/model-choice.md` | documentation | Grok bullet corrected; new "Grok's free cap" section; one paragraph on other agents. The file is the local reference, not a copy of upstream's `SKILL.md`, and `upstream.json` lists no change to it. |

## Tests Added or Updated

None: documentation only. The command was run against the real log.
