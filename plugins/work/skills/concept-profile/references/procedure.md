# Concept Profile Procedure

## Sources and extraction

Admit the catalog spreadsheet, each material file, and each reference book
through the work plugin's `wiki-raw-import` skill. Check the raw revisions
with that skill. Read only the admitted revisions; never edit or delete
anything in `raw/`.

From this skill folder, the script runs in the Wiki consistency environment.
`--wiki <vault>` (default `work`) and `--run <name>` come before the command:

```sh
uv run --project ../../../../packages/wiki-consistency --frozen --offline --no-sync python scripts/concept_profile.py --run <name> <command>
```

Use one run folder per material: `--run <name>` is
`$XDG_STATE_HOME/verbose-broccoli/concept-profile/<name>/`, or `~/.local/state`
when `XDG_STATE_HOME` is unset. Before each write, the script refuses to pass
200 MB in the run folder. It writes a file under a temporary name and renames
it, and appends `checks.jsonl` one line per sentence. Exit code 0 means
success, 1 means a proposal was refused or a backfire result was invalid, and
2 means an error stopped the command, such as a backfire failure during
`check`.

- `catalog --catalog catalogs/<catalog>.md` writes `catalog.tsv` for the
  proposer from the catalog page's first source, the spreadsheet, at the
  revision the page cites. Each line has four tab-separated columns: the key,
  the level, the label and the statement. The key is the concept's one-based
  data-row number in the sheet. The catalog's own ID and the examples are not
  in the file. Cell values are stripped of surrounding whitespace.
- `extract --source <source-id> ...` writes `text/<source-id>.txt` from each
  source's latest revision: PDF through `pdftotext -raw`, everything else
  through `wiki_consistency.evidence.convert` and `read`. `-raw` keeps the
  content-stream order, which keeps sentences whole across the columns of a
  two-column exam paper; the default reading order split 13 sentences of the
  pilot's paper. A source with no letters in its text, such as a scanned PDF,
  stops the command; the user decides.

## Proposals

Choose the proposer with the code plugin's `model-choice` skill. Ask it to
read every extracted source in order and identify every English sentence in
passages, dialogues and full-sentence English answer choices. Skip Korean
text, headings, labels and phrase-only choices. Keep each sentence's text as
it occurs in the extraction. Make one row for every sentence, including rows
with no concepts, in text order, with repeated sentences as separate rows.

Write `proposals.jsonl` in the run folder, one JSON object per sentence:

```json
{"source": "<source ID>", "part": "<lesson or section>", "text": "<sentence>", "concepts": [1, 4]}
```

`concepts` holds keys from `catalog.tsv`, not the catalog's own IDs. Use an
empty list when the sentence shows no concept. Select every concept the
sentence shows, not only the lesson target or the exam answer.

## Check and review

`check --catalog catalogs/<catalog>.md` first tests every row: its text, after
whitespace is normalized, must occur in the extracted text of its source, and
every key must be in the catalog. If any row fails, the command names each on
stderr as `proposal <n>: <reason>`, exits 1 and sends nothing.

Then it opens one `backfire serve-mcp --education` session, started from
`packages/backfire`, and sends every unchecked sentence with concepts as one
`jev_verify` call. Each concept, once and in key order, gives one claim: the
catalog page's `catalog.claim` template filled with `{text}` (the normalized
sentence), `{label}` and `{statement}`. The evidence is the item
`{"id": "sentence", "text": "<sentence>"}`, then one item per concept with the
catalog ID as `id` and the label, statement and examples on separate lines as
`text`.

A result is kept when its verdict is `verified` with action `auto`, dropped
when it is `contradicted` or `unsupported` with action `auto`, and unclear
otherwise. A single result whose verdict is `unknown` (backfire's
`invalid_response`) is recorded as unclear and counted in `invalid`.

If a call raises, backfire returns a tool error or output that is not the
expected JSON, or the number of results differs from the number of claims, the
command writes nothing for that sentence, prints `row <n>: <reason>` on stderr
and exits 2. The sentences before it stay in `checks.jsonl`, so the same
command resumes at the failed sentence.

`checks.jsonl` gets one line per sentence: `row` (the proposal's line number),
`provider`, `model`, `usage`, `seconds`, and `results`: each backfire result
with the concept's catalog ID as `concept` and the `outcome` added. A run that stopped is
rerun with the same command: sentences already in `checks.jsonl` are not sent
again, and a torn last line is dropped first.

`review.md` is rewritten from all results after every run. It has a heading
`## <row>. <sentence>` for each sentence with unclear concepts, and one line
`- [ ] <row> <JSON string of the catalog ID> — <label>: <statement>` for each
of them. The user ticks the concepts the sentence shows. Do not rerun `check`
after the user has started on the sheet.

The command prints one JSON object over all recorded results: `sentences`,
`calls`, `invalid` (results without a verdict or with `unknown`), `tokens`
(usage `input_tokens` plus `output_tokens`), `seconds`, and the counts `kept`,
`dropped` and `unclear`. Exit code 1 means `invalid` is above zero.

## Record and finish

`record --catalog catalogs/<catalog>.md --name <material> --title <title>
--summary <line> --proposer '<agent, model and effort>' [--reviewed]` writes
`wiki/profiles/<material>.md` and `<material>.jsonl`, and replaces both when
they exist; the vault's Git keeps the earlier record. It stops with exit code
2 unless `checks.jsonl` covers every proposal.

Without `--reviewed`, every unclear concept stays in the row's `unclear` list.
With it, the ticked ones of `review.md` become concepts and the unticked ones
are dropped. The `checker` field lists the distinct provider and model pairs
in `checks.jsonl`. `sources` lists each proposal source at its latest revision,
then the catalog page's sources; `topics` come from the catalog page.

After recording, use the work plugin's `wiki-consistency` skill: run `update`
and `check`, fix failures, append the required entry to `wiki/log.md`, and
commit the page, data file, index and log in the vault. Delete the run folder
after the record commit. A failed or interrupted run keeps its folder for a
rerun.

## Record layouts

All records live in the work vault's `wiki/`, use the declared topic
`Teaching materials`, and cite their raw source revisions. Page front matter
also requires `title`, `summary`, `topics` and `sources`. Paths in a block are
relative to its page.

### Catalog: `wiki/catalogs/<catalog>.md`

The spreadsheet stays in `raw/`; the page names it as its first source and
describes the catalog. Its block records the spreadsheet's own headers and
claim wording.

```yaml
---
title: <catalog name>
summary: <one line>
topics:
  - Teaching materials
sources:
  - id: <spreadsheet source ID>
    revision: <revision>
catalog:
  sheet: <sheet name>
  columns:
    id: <header of the ID column>
    label: [<header>, ...]      # joined with " / " for display
    level: <header>
    statement: <header>
    examples: <header>          # one cell, one example per line
  levels: [<lowest>, ..., <highest>]
  claim: <template with {text}, {label} and {statement}>
---
```

The body says what the catalog is, its terms of use and its counts.

### Profile: `wiki/profiles/<material>.md` and `<material>.jsonl`

```yaml
---
title: <material title>
summary: <one line>
topics:
  - Teaching materials
sources:                        # every raw source of the material, then the catalog's
  - id: <source ID>
    revision: <revision>
profile:
  catalog: ../catalogs/<catalog>.md
  data: <material>.jsonl
  proposer: <agent, model and effort>
  checker: <backfire provider and model>
  counts: {sentences: 0, kept: 0, dropped: 0, unclear: 0}
---
```

The body is one short paragraph written by the script: the material, the
catalog link and the data link. Data rows, one per sentence, in order:

```json
{"n": 1, "source": "<source ID>", "part": "Lesson 1", "text": "<sentence>", "concepts": ["<id>"], "unclear": ["<id>"]}
```

`concepts` holds kept concepts and unclear ones the user ticked, in catalog
order. `unclear` holds those the user has not decided. Dropped and unticked
concepts are not recorded. In `counts`, `kept` counts the concepts of all rows,
`unclear` the undecided ones, and `dropped` every other proposal.

### Mapping: `wiki/mappings/<catalog>--<reference>.md` and `.jsonl`

The layout and method are designed here; a later feature builds the mappings.

```yaml
mapping:
  catalog: ../catalogs/<catalog>.md
  reference: <reference title>
  data: <catalog>--<reference>.jsonl
  proposer: <agent, model and effort>
  checker: <backfire provider and model>
  counts: {concepts: 0, kept: 0, dropped: 0, unclear: 0}
```

`sources` cites the catalog spreadsheet and the reference's raw extraction.
A section is addressed by its heading path in that revision, such as
`Unit 12 > 12A`. Data rows, one per concept, in catalog order:

```json
{"concept": "<id>", "sections": ["<heading path>"], "unclear": ["<heading path>"]}
```

The proposer may name at most three sections for each concept. A check sends
one `jev_verify` call per concept, with one claim per proposed section:
`<reference> section <path> explains <label>: <statement>`. Evidence has the
concept's statement and examples and each proposed section's text. Each run
reports its unclear share. Once the pilot sets a limit with the user, stop a
run that exceeds it and change the method before continuing; keep unresolved
items in the record instead of building a review queue.
