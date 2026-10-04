# Grammatical Competence Procedure

## Sources and extraction

Admit the inventory spreadsheet, each material file, and each reference
book's original PDF through the work plugin's `wiki-raw-import` skill. Check
the raw revisions with that skill. Read only the admitted revisions; never
edit or delete anything in `raw/`.

From this skill folder, the script runs in the Wiki consistency environment.
`--wiki <vault>` (default `work`) and `--run <name>` come before the command:

```sh
uv run --project ../../../../packages/wiki-consistency --frozen --offline --no-sync python scripts/grammatical_competence.py --run <name> <command>
```

Use one run folder per material: `--run <name>` is
`$XDG_STATE_HOME/verbose-broccoli/grammatical-competence/<name>/`, or
`~/.local/state` when `XDG_STATE_HOME` is unset. Before each write, the
script refuses to pass 200 MB in the run folder. It writes a file under a
temporary name and renames it, and appends `checks.jsonl` one line per
sentence. Exit code 0 means
success, 1 means a proposal was refused or a backfire result was invalid, and
2 means an error stopped the command, such as a backfire failure during
`check`.

- `inventory --inventory inventories/<inventory>.qmd` writes `inventory.tsv`
  for the proposer from the inventory page's first source, the spreadsheet,
  at the revision the page cites. Each line has four tab-separated columns:
  the key, the level, the label and the statement. The key is the item's
  one-based data-row number in the sheet. The inventory's own ID and the
  examples are not in the file. Cell values are stripped of surrounding
  whitespace. When the inventory block names a `family` column, rows whose
  family cell holds a tier number and whose labels match (whitespace
  collapsed) form one tier family, counted as one item everywhere: it keeps
  its lowest tier's key and inventory ID, its levels are joined with `/`, its
  statements with `; `, and its examples hold every tier's examples. Its
  other rows' keys are not in the file.
- `extract --source <source-id> ...` reuses
  `text/<source-id>/<revision>.qmd` through `wiki_consistency.evidence.read`.
  A fresh run selects the source's latest revision and calls the shared
  `evidence.convert` only when retained text is absent and conversion is
  authorized. Shared PDF conversion uses `pdftotext -raw` to preserve
  content-stream order, recording its actual version; there is no separate
  grammar-only bypass. The run's `text/<source-id>.txt`
  is a body copy; `extractions.json` pins the exact revision, raw SHA-256 and
  full `.qmd` extraction SHA-256. Resumption validates both retained and copied
  bytes, and later raw revisions cannot silently retarget the recorded profile.
  Legacy runs without provenance are refused/unresolved, never repaired by a
  paid rerun. A source with no letters, such as a scanned PDF, stops the command.
  New real conversion and student-bearing decisions stay held with main.

Retained text keeps the full returned original-language output and known
converter/raw provenance. `conversion-status: extracted` means backend output,
not completeness or original review. Report partial/unknown status and missing
markers honestly. `checked-against-original: true` requires actual caller review
bound to raw `sha256`, full-file `extraction-sha256` and nonempty `evidence`;
corrections invalidate earlier review evidence. Do not invent a receipt.

All page reads use shared `read_metadata` and `_metadata.yml` defaults. Preserve
meaningful page overrides, including `profile.checker: none`, when consolidating
defaults; inventory/reference paths remain relative to the consuming page.

## Proposals

Choose the proposer with the code plugin's `model-choice` skill. Ask it to
read every extracted source in order and identify every English sentence in
passages, dialogues and full-sentence English answer choices. Skip Korean
text, headings, labels and phrase-only choices. Keep each sentence's text as
it occurs in the extraction. Make one row for every sentence, including rows
with no items, in text order, with repeated sentences as separate rows.

Write `proposals.jsonl` in the run folder, one JSON object per sentence:

```json
{"source": "<source ID>", "part": "<lesson or section>", "text": "<sentence>", "items": [1, 4]}
```

`items` holds keys from `inventory.tsv`, not the inventory's own IDs. Use an
empty list when the sentence shows no item. Select every item the
sentence shows, not only the lesson target or the exam answer.

Tier rule, the same for every proposer: a line whose level holds `/` is a
tier family, whose tiers differ only in how wide a range of words a learner
uses. Name its key once when any word of the sentence fits the family,
whatever the word's own level; never judge which tier a word belongs to.

## Check

`check --inventory inventories/<inventory>.qmd` first tests every row: its
text must hold no Hangul, because everything sent to backfire is English;
after whitespace is normalized, it must occur in the extracted text of its
source; and every key must be in the inventory. If any row fails, the command
names each on stderr as `proposal <n>: <reason>`, exits 1 and sends nothing.

Then it opens one `backfire serve-mcp --education` session, started from
`packages/backfire`, and sends every unchecked sentence with items as one
`jev_verify` call. Each item, once and in key order, gives one claim: the
inventory page's `inventory.claim` template filled with `{text}` (the
normalized sentence), `{label}` and `{statement}`. The evidence is one text:
the line `Sentence: <sentence>`, then one block per item with its inventory
ID, label, statement and examples on separate lines. One text, not one
evidence item per inventory item, makes backfire ask one question per claim
instead of two; on the
pilot it cut a 29-claim call from about 86,000 to 16,500 tokens and let a
36-claim call pass the provider's size limit.

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
with the item's inventory ID as `item` and the `outcome` added. A run that
stopped is rerun with the same command: sentences already in `checks.jsonl`
are not sent again, and a torn last line is dropped first.

The command prints one JSON object over all recorded results: `rows`,
`calls`, `invalid` (results without a verdict or with `unknown`), `tokens`
(usage `input_tokens` plus `output_tokens`), `seconds`, and the counts `kept`,
`dropped` and `unclear`. Exit code 1 means `invalid` is above zero.

## Record and finish

`record --inventory inventories/<inventory>.qmd --name <material> --title
<title> --summary <line> --proposer '<agent, model and effort>'
[--auto-accept <t> | --unchecked]` writes `wiki/profiles/<material>.qmd` and
`<material>.jsonl`, and replaces both when they exist; the vault's Git keeps
the earlier record. It stops with exit code 2 unless `checks.jsonl` covers
every proposal, unless `--unchecked` is given.

`--auto-accept <t>` sorts the stored results again without new calls: a
result counts as confident when its confidence is at least `t`, and the
rule above then keeps, drops or leaves it unclear; the page records `t` as
`profile.auto_accept`. Without it, the outcomes stay as `check` recorded
them at backfire's default of 0.8. On the pilot, 0.8 kept only 28% of the
true items at 99% precision and 0.5 kept 74% at 95%; the user chose 0.5.

`--unchecked` records a profile without `check`: it first refuses rows as
`check` does, then keeps every proposed item, and `checker` is `none`. The
user chose it for the first full run, so no backfire credit is spent; on the
pilot rerun the proposer alone had precision 0.94 and recall 0.90, and the
items kept at 0.5 had 0.97 and 0.77.

Nobody reviews unclear items: each stays in its row's `unclear` list. The
`checker` field lists the distinct provider and model pairs in
`checks.jsonl`. `sources` lists each proposal source at its pinned extraction revision,
then the inventory page's sources; `topics` come from the inventory page.

After recording, use the work plugin's `wiki-consistency` skill: run `update`
and `check`, fix failures, append the required entry to `wiki/log.qmd`, and
commit the page, data file, index and log in the vault. Delete the run folder
after the record commit. A failed or interrupted run keeps its folder for a
rerun.

## Record layouts

All records live in the work vault's `wiki/`, use the declared topic
`Teaching materials`, and cite their raw source revisions. Page front matter
also requires `title`, `summary`, `topics` and `sources`. Paths in a block are
relative to its page.

### Inventory: `wiki/inventories/<inventory>.qmd`

The spreadsheet stays in `raw/`; the page names it as its first source and
describes the inventory. Its block records the spreadsheet's own headers and
claim wording.

```yaml
---
title: <inventory name>
summary: <one line>
topics:
  - Teaching materials
sources:
  - id: <spreadsheet source ID>
    revision: <revision>
inventory:
  sheet: <sheet name>
  columns:
    id: <header of the ID column>
    label: [<header>, ...]      # joined with " / " for display
    level: <header>
    statement: <header>
    examples: <header>          # one cell, one example per line
    family: <header>            # optional: a tier number per row (see above)
  levels: [<lowest>, ..., <highest>]
  claim: <template with {text}, {label} and {statement}>
---
```

The body says what the inventory is, its terms of use and its counts.

### Profile: `wiki/profiles/<material>.qmd` and `<material>.jsonl`

```yaml
---
title: <material title>
summary: <one line>
topics:
  - Teaching materials
sources:                        # the material's raw sources, then the inventory's
  - id: <source ID>
    revision: <revision>
profile:
  inventory: ../inventories/<inventory>.qmd
  data: <material>.jsonl
  proposer: <agent, model and effort>
  checker: <backfire provider and model>
  auto_accept: <t, when record was given one>
  counts: {sentences: 0, kept: 0, dropped: 0, unclear: 0}
---
```

The body is one short paragraph written by the script: the material, the
inventory link and the data link. Data rows, one per sentence, in order:

```json
{"n": 1, "source": "<source ID>", "part": "Lesson 1", "text": "<sentence>", "items": ["<id>"], "unclear": ["<id>"]}
```

`items` holds kept items, in inventory order, and `unclear` the unclear
ones. Dropped items are not recorded. In `counts`, `kept` counts the items of
all rows, `unclear` the unclear ones, and `dropped` every other proposal.

### Reference: `wiki/references/<reference>.qmd`

A reference book's original PDF stays in raw. Its full original-language
extraction is `text/<source-id>/<revision>.qmd`, versioned in vault-local Git
with no remote. It is not an English Wiki page; English page lint does not
apply to the source body. The approved student-data privacy boundary still applies. The reference page cites the exact PDF bag
revision, records known converter and review facts without guessing missing
legacy provenance, and links the retained extraction:

```yaml
reference:
  text: ../../text/<source-id>/<revision>.qmd
```

The reader validates the declared revision, raw hash and full extraction hash,
then pins the run in `extractions.json`. Existing legacy side-file bodies must
be preserved when moved; a header or move that shifts lines requires verified
section-index reconciliation, never guessed offsets or new paid proposals.
Name the reference page in kebab-case with the edition.

### Mapping: `wiki/mappings/<inventory>--<reference>.qmd` and `.jsonl`

A mapping links each item of an inventory to at most three sections of one
reference that explain it. Build it in its own run folder:

1. `inventory --inventory inventories/<inventory>.qmd` writes `inventory.tsv`.
2. A section index worker, chosen with `model-choice`, writes `sections.tsv`:
   one line per section of the reference's text file, with tab-separated
   columns: the label, the first line and the last line (one-based, inclusive),
   and optionally the section's title for the proposer. Sections are the book's
   own units or numbered sections, labeled in English as the book labels them,
   such as `Unit 12`, and each holds at most 20,000 characters; split a longer
   one at its subsections. Count exact full-file lines, including the retained
   `.qmd` front matter. Use only verified source boundaries; neither guessed
   offsets nor PDF formfeeds establish original page markers. Missing or
   ambiguous source maps remain unresolved.
3. A proposer, chosen the same way, writes `mappings.jsonl`: one row per
   line of `inventory.tsv`, in key order,
   `{"item": <key>, "sections": [<label>, ...]}`, with at most three labels
   and an empty list when no section explains the item.
4. `map --inventory inventories/<inventory>.qmd --reference
   references/<reference>.qmd` first refuses a file that does not list every
   inventory key exactly once, and rows whose key is not in the inventory, that
   name more than three sections, a label not in the index or with Hangul,
   lines outside the text, or a section over 20,000 characters, as `mapping
   <n>: <reason>` with exit code 1. Then it sends each row with sections as one
   `jev_verify` call: one claim per section, `<reference title>, section
   <label>, explains <item label>: <statement>`, and one evidence text with the
   item's ID, label, statement and examples, then each section's lines, leaving
   out every line with Hangul. It uses backfire without education mode, because
   a reference holds no student data; education mode refused a practice book's
   example that looked like an identifier. Results, resumption and the printed
   counts work as in `check`, with `section` in place of `item`.
5. `record` with `--reference references/<reference>.qmd`, which refuses the
   same rows as `map`, and `--name <inventory>--<reference>` writes the mapping
   record instead of a profile.

```yaml
mapping:
  inventory: ../inventories/<inventory>.qmd
  reference: ../references/<reference>.qmd
  data: <inventory>--<reference>.jsonl
  proposer: <agent, model and effort>
  checker: <backfire provider and model>
  auto_accept: <t, when record was given one>
  counts: {items: 0, kept: 0, dropped: 0, unclear: 0}
```

`sources` cites the inventory's sources, then the reference page's. Data
rows, one per item, in inventory order:

```json
{"item": "<id>", "sections": [{"label": "Unit 12", "lines": [100, 180]}], "unclear": []}
```

Each run reports its unclear share. Keep unclear sections in the record
instead of building a review queue.
