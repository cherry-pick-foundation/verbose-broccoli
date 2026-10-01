# Implementation Plan: Grammatical Competence Profiles, Stage 2

**Branch**: `feature/grammatical-competence` | **Date**: 2026-10-01 | **Spec**:
[spec.md](spec.md)

## Summary

Rename stage 1's `concept-profile` skill to `grammatical-competence`, with
the record kind catalog renamed to inventory and concept to item; count each
tier family as one item; drop the review sheet; rerun and score the pilot;
add a map step for inventory-to-reference mappings and build the four
mappings; survey the materials; and, after the user's catalog choice and
approval of the list, profile every listed material in the work vault.

Stage 1's tools stay: `wiki-raw-import`, python-hwpx, markitdown and
pdftotext, backfire's `jev_verify` in education mode, and `wiki-consistency`.
Proposers and section indexes are Orca workers whose agent, model and effort
come from the code plugin's `model-choice` skill.

## Research

### R1 - Tier families in the first grammatical inventory

The inventory's spreadsheet has a tier column whose cells are a tier number
(1 to 3) or a not-applicable mark. Grouping tiered rows by their label
columns gives 128 families with 231 rows, 75 of them with two or more tiers
(178 rows), but only after the label's inner whitespace is collapsed: without
that, the same rows form 142 families with 65 multi-tier ones. Tiers are not
always in row order (16 families). So a family is keyed by the collapsed
label, and its item takes the lowest tier's key and ID. The inventory shrinks
from 1,222 rows to 1,119 items (checked 2026-10-01 on the admitted revision).

### R2 - The answer key at family level

The kept answer key lists 15 sentences with 339 proposed and 22 added keys.
Mapping every key to its family's item gives 292 true items. The stage 1
proposals scored this way have precision 0.965 (276 of 286) and recall 0.945
(276 of 292): the volume 0.942 and 0.918, the exam 0.992 and 0.978. Stage 1
reported 0.85 and 0.93 without families. The scoring script lives in the
coordinator's scratch space; it reads the key, the proposals and the checks,
and prints counts only.

### R3 - Section addressing in the reference texts

Stage 1 planned to address a section by its heading path in the reference's
text file. The four PyMuPDF4LLM extractions do not support that: their
heading levels are inconsistent (in one Grammar in Use book, units appear as
a level-one heading on some exercise pages only, and explanation pages are a
`PDF Page` heading followed by level-six headings), and the reference grammar
has 5,206 headings, 2,547 of them at level six. Every file does mark each PDF
page with a `## PDF Page <n>` heading (305 to 1,862 per book). So a section
is addressed by a label and a line range in the text file, taken from a
section index made once per book; the line ranges stay valid because the
text file is kept byte for byte.

### R4 - Cost of the check step

Stage 1's checks cost about $0.035 per million tokens on OpenRouter (Jev) and
about 14,300 tokens per sentence. The OpenRouter key had $8.47 left on
2026-10-01, enough for about 240 million tokens, so about 17,000 sentences
at stage 1's rate. The full run's size against that budget goes to the user
with the materials list.

## Script changes: `grammatical_competence.py`

- `inventory --inventory <page>` (was `catalog --catalog`) writes
  `inventory.tsv`; with a `family` column in the inventory block, each tier
  family is one line (R1).
- `check` and `record` take `--inventory`; proposals, checks and profile rows
  use `items` and `item`; `check` writes no review sheet and `record` has no
  `--reviewed`.
- `sections --reference <page>` is not needed: the section index is a
  worker's output, `sections.tsv` in the run folder (label, first line, last
  line).
- `map --inventory <page> --reference <page>` validates `mappings.jsonl`
  (one row per item: `{"item": <key>, "sections": [<label>, ...]}`, at most
  three labels), sends one `jev_verify` per item with a claim per section and
  the item's text plus each section's lines, minus lines with Hangul, as one
  evidence text, and appends `checks.jsonl`; it resumes like `check`.
- `record --reference <page>` writes the mapping record instead of a profile
  record: `wiki/mappings/<inventory>--<reference>.md` and `.jsonl`, one row
  per item `{"item": <id>, "sections": [{"label", "lines"}], "unclear": [...]}`.

## Run folders

`$XDG_STATE_HOME/verbose-broccoli/grammatical-competence/<run>/`, one per
material or per mapping, with stage 1's budget and cleanup. The kept answer
key and the pilot's proposals stay in stage 1's folder until the rerun is
scored.

## Constitution Check

- I, VII (reuse order): no new dependency; the script stays glue (R3 keeps
  section finding out of the code). Pass.
- V (observable acceptance): synthetic tests for families, the map step and
  the record; the rerun scores real files against the key. Pass.
- VI (Wiki layers): sources through `wiki-raw-import`, records as pages and
  data files, working files in state storage. Pass.
- IX (layout): a work-plugin skill. Pass.

## Project Structure

```text
specs/036-grammatical-competence/
├── spec.md
├── plan.md
└── tasks.md
plugins/work/skills/grammatical-competence/
├── SKILL.md
├── references/procedure.md
└── scripts/
    ├── grammatical_competence.py
    └── grammatical_competence_test.py
plugins/work/skills/wiki-raw-import/assets/AGENTS.md   # Inventory records
package.json, turbo.json, docs/                        # test wiring, tables
```

## Complexity Tracking

No constitution violations.
