---
name: grammatical-competence
description: Build or update a grammatical inventory record, sentence profile, or reference mapping in a Wiki vault from admitted raw sources. Use when every sentence of a material must be linked to inventory items, checked, and recorded for later lookup.
---

Read [the work plugin rules](../../AGENTS.md) before using this skill.

# Grammatical Competence

Read the [procedure and record layouts](references/procedure.md) before a run.
Records are English `.qmd` pages with shared folder metadata; reference text
is retained in `text/<source-id>/<revision>.qmd`. Keep JSON Lines order, repeated
sentences, empty entries and explicit unchecked status. Read the current schema.
From this skill folder, run the script in the Wiki consistency environment:

```sh
uv run --project ../../../../packages/wiki-consistency --frozen --offline --no-sync python scripts/grammatical_competence.py --run <name> <command>
```
