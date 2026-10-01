---
name: concept-profile
description: Build or update a concept catalog, sentence profile, or reference mapping in a Wiki vault from admitted raw sources. Use when every sentence of a material must be linked to catalog concepts, checked, and recorded for later lookup.
---

# Concept Profile

Read the [procedure and record layouts](references/procedure.md) before a run.
From this skill folder, run the script in the Wiki consistency environment:

```sh
uv run --project ../../../../packages/wiki-consistency --frozen --offline --no-sync python scripts/concept_profile.py --run <name> <command>
```
