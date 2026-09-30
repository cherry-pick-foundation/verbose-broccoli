# Implementation Plan: Concept Profiles of Teaching Materials

**Branch**: `feature/grammar-profile` | **Date**: 2026-09-30 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/028-concept-profile/spec.md`

## Summary

Add the work-plugin skill `concept-profile`: a short `SKILL.md`, the
procedure and record layouts in `references/procedure.md`, and one script,
`scripts/concept_profile.py`, for the steps no existing tool covers. Extend
the vault schema template with the three record kinds. Then run the pilot on
the user's chosen volume and exam paper in the work vault and bring the
numbers to the user.

Existing tools do the rest: `wiki-raw-import` admits sources,
python-hwpx and markitdown (through `wiki_consistency.evidence`) and
pdftotext extract text, an Orca worker proposes concepts, backfire checks
them, and `wiki-consistency` keeps the vault consistent.

## Research

### R1 - What existing tools cover

| Need | Existing tool | Evidence |
| --- | --- | --- |
| Admit sources as raw | `wiki-raw-import` skill | `plugins/work/skills/wiki-raw-import/SKILL.md` |
| Find a source's latest raw revision and payload | `wiki_consistency.instance.revisions` | `packages/wiki-consistency/src/wiki_consistency/instance.py` |
| HWP, HWPX, DOCX to text | `wiki_consistency.evidence.convert` and `read` (markitdown with a python-hwpx converter; cached in `CACHE/wiki-evidence/`) | `packages/wiki-consistency/src/wiki_consistency/evidence.py` |
| PDF to text | `pdftotext` (poppler, `/usr/bin/pdftotext`) | user decision |
| Read the catalog spreadsheet | openpyxl, locked through `markitdown[xlsx]` | `uv.lock`, `packages/wiki-consistency/pyproject.toml` |
| Call backfire without its MCP tools loaded | the `mcp` stdio client pattern in `plugins/code/skills/model-choice/references/model-choice.md` | that file, "Calling backfire without its MCP tools" |
| Check claims against evidence | backfire `jev_verify`, education mode | `plugins/work/mcp.json` (`serve-mcp --education`) |
| Page rules, links, index, log | `wiki-consistency check` and `update` | `plugins/work/skills/wiki-consistency/SKILL.md` |

The script runs in `packages/wiki-consistency`'s environment
(`uv run --project ../../../../packages/wiki-consistency --frozen --offline
--no-sync python scripts/concept_profile.py`), which already has every
dependency: `wiki_consistency`, backfire and its `mcp` client, markitdown,
python-hwpx, openpyxl and PyYAML. No dependency is added.

### R2 - What the glue must do

No existing tool builds one `jev_verify` request per sentence from proposals
and catalog entries, sorts the results into outcomes, writes a review sheet
and applies it, or writes the record. These steps must be deterministic and
exact (catalog text copied verbatim, outcomes by a fixed rule), so a script
does them, not an agent.

### R3 - `jev_verify`

Input: `claims` (strings), `evidence` (a string or items), optional
`auto_accept` (default 0.8). With several evidence items, each claim asks two
questions (relation and supporting item)
(`.venv/.../jev_judge_mcp/tools/verify.py`, `handle`). Output per claim:
`verdict` (`verified`, `contradicted`, `unsupported`, or `unknown` with
`status: invalid_response`), `probabilities`, `confidence`, `action`
(`auto` or `review`) and `supporting_evidence`. Results report token usage.
The work plugin's reference notes that eight-question batches were malformed
once in three measured runs (`plugins/work/skills/backfire/references/verbose-broccoli.md`);
the pilot counts invalid responses.

### R4 - Why sentences go in data files, not pages

The vault's `check` applies the page rules to every page outside mechanical
regions and the front matter's `sources` field: no phone numbers, email or
postal addresses, no Hangul, and times only with a zone. Exam passages carry
notices with phone numbers and times such as "10:00 a.m.", so sentence text
in a page would fail `check`. Every page unit is also judged against the
page's raw sources during consistency; a profile table would double the
backfire calls and come back unsupported, since the sources say nothing
about concepts. So each profile's and mapping's rows go in a JSON Lines data
file next to its page; `check` reads only `wiki/**/*.md`
(`packages/wiki-consistency/src/wiki_consistency/instance.py`, `pages`).

### R5 - The legacy stall and how this design avoids it

The legacy textbook-to-CGEL matching (`~/data/automatic-disco/workspace/working/english/textbook-grammar/`,
read only) produced candidate links from title seeds and search, with a
human as the only verifier: its latest summary lists 1,657 unreviewed
candidates against 24 approved and 6 rejected links. This design differs:

1. No candidate state. Every proposal gets an outcome in the same run:
   backfire keeps or drops it, and only the unclear rest reaches the user.
2. A record is complete without the user: unclear proposals are listed as
   unclear, not blocking.
3. Each run reports its unclear share. If it exceeds the limit set with the
   user after the pilot, the method changes (claim wording, evidence,
   threshold, proposer) before more runs, instead of queuing reviews.
4. Mappings work per catalog concept (at most three proposed sections each),
   not per textbook topic against every reference concept.

### R6 - Pilot sources

- Volume: Common English 2, NE Neungyule (Oh Seon-young), 2022 curriculum,
  the main-text files of Lessons 1 to 4 and the Special Lesson (HWPX), copied
  from the legacy source cache into `~/Documents/20_reference/textbooks/`
  and admitted from there.
- Exam: the 2026 September Grade 10 academic assessment (Incheon), original
  question paper PDF, from the user's midterm folder.
- Catalog: the user's spreadsheet in `~/Downloads/`: one sheet, a header row
  and 1,222 rows. Its column names go only into the catalog record in the
  vault.

## Record layouts

All records live in the work vault's `wiki/`, carry the page front matter
the vault schema requires (`title`, `summary`, `topics`, `sources`), use the
declared topic `Teaching materials`, and add one block named after their
kind. Paths inside a block are relative to the page.

### Catalog record: `wiki/catalogs/<catalog>.md`

The catalog's data stays in its raw spreadsheet; the page describes it.

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

The body, written by the agent, says what the catalog is, its terms of use
and its counts. For the first catalog the block names the spreadsheet's own
headers, the levels A1 to C2, and English claim wording; these exist only in
the vault.

### Profile record: `wiki/profiles/<material>.md` and `<material>.jsonl`

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

`concepts` holds kept concepts and unclear ones the user accepted, in
catalog order; `unclear` holds those the user has not decided. Dropped and
rejected concepts are not recorded.

### Mapping record: `wiki/mappings/<catalog>--<reference>.md` and `.jsonl`

Designed now, built in a later feature.

```yaml
mapping:
  catalog: ../catalogs/<catalog>.md
  reference: <reference title>
  data: <catalog>--<reference>.jsonl
  proposer: <agent, model and effort>
  checker: <backfire provider and model>
  counts: {concepts: 0, kept: 0, dropped: 0, unclear: 0}
```

`sources` cites the catalog's spreadsheet and the reference's raw
extraction. A section is addressed by its heading path in that revision of
the extraction, for example `Unit 12 > 12A`. Data rows, one per concept, in
catalog order:

```json
{"concept": "<id>", "sections": ["<heading path>"], "unclear": ["<heading path>"]}
```

A check sends one `jev_verify` per concept: one claim per proposed section
("<reference> section <path> explains <label>: <statement>"), with the
concept's statement and examples and each section's text as evidence items.

## Run folder and working files

`STATE/concept-profile/<run>/`, where `STATE` is
`$XDG_STATE_HOME/verbose-broccoli` (default `~/.local/state/verbose-broccoli`).
Storage budget: 200 MB per run folder, checked before each write. Files are
written to a temporary name and renamed; `checks.jsonl` is appended one line
per sentence, and a torn last line is dropped on resume. After the record is
committed in the vault, the procedure deletes the run folder; after a
failure or interruption the folder stays for the rerun.

| File | Written by | Content |
| --- | --- | --- |
| `catalog.tsv` | `catalog` | One line per concept: ID, level, label, statement (no examples), for the proposer |
| `text/<source ID>.txt` | `extract` | Extracted text of one raw source |
| `proposals.jsonl` | the proposer | `{"source", "part", "text", "concepts": [ids]}` per sentence, in text order |
| `checks.jsonl` | `check` | Per sentence: its proposals, each result's verdict, action, confidence and outcome, token usage and time |
| `review.md` | `check` | Unclear proposals as `- [ ]` items grouped by sentence, each with the concept's label and statement |

## Script: `concept_profile.py`

Commands, each with `--wiki <vault>` (default `work`) and `--run <name>`:

- `catalog --catalog <page>`: write `catalog.tsv` from the raw spreadsheet as
  the catalog record describes it.
- `extract --source <id> ...`: write `text/<id>.txt` for each source's latest
  revision: PDF through `pdftotext`, other formats through
  `wiki_consistency.evidence.convert` and `read`.
- `check --catalog <page>`: validate `proposals.jsonl` (FR-006), send one
  `jev_verify` per unchecked sentence to `backfire serve-mcp --education`
  started from `packages/backfire`, append `checks.jsonl`, write `review.md`,
  and print counts, calls, tokens and time as JSON.
- `record --catalog <page> --name <material> --title <title> --summary <line> [--reviewed]`:
  write the profile page and data file into the vault. With `--reviewed`
  (the user has returned `review.md`), ticked items become concepts and
  unticked ones are dropped; without it, every unclear item stays listed as
  unclear.

Exit 0 means success; 1 means at least one sentence was refused or failed;
2 means an error stopped the command before writing.

Estimated own code: about 250 lines of Python and 200 lines of tests. With
the skill text (about 250 lines), the template section (about 40) and the
test wiring, the change stays under 1,000 lines, so no split review is
needed.

## Pilot

1. Copy the five volume files into `~/Documents/20_reference/textbooks/`;
   admit them, the exam paper and the catalog spreadsheet with
   `wiki-raw-import`.
2. Update the vault's `AGENTS.md` from the template; write the catalog record.
3. Run `catalog` and `extract` for each material (one run folder each).
4. Two proposer workers, one per material, write `proposals.jsonl`; their
   agent, model and effort come from `model-choice`.
5. Run `check`; the user decides the unclear items on `review.md`; run
   `record`; run `wiki-consistency` (`update`, `check`), log and commit.
6. Hand-check sheet: 30 sentences, 15 per material, sampled with a fixed
   seed across parts; every proposal unchecked in catalog order with its
   label and statement, no outcome shown, and a line for missing IDs. The
   sheet stays in the run folder.
7. Report on the sampled sentences: precision of kept concepts, recall of
   the record (kept and accepted against the user's marks plus added IDs),
   dropped concepts the user marked present, the unclear share, and the
   proposer's recall; for the whole pilot, backfire calls, their tokens, the
   proposer's tokens where the agent reports them, and time per step. The
   scoring runs in the run folder and is not committed.

## Technical Context

**Language/Version**: Python 3.14 in the uv workspace.
**Primary Dependencies**: wiki-consistency (workspace), backfire (workspace,
`mcp` client), openpyxl, python-hwpx, markitdown, PyYAML; poppler's
`pdftotext`.
**Storage**: the work vault (raw bags, pages, data files, Git) and the run
folder in XDG state.
**Testing**: pytest with synthetic catalogs, synthetic HWPX or text sources
and a stubbed backfire call, run by a new `test:concept-profile` task in
`npm run verify`.
**Constraints**: no catalog data, material text or student data in the
repository or messages; subject-neutral names.

## Constitution Check

- I, VII (reuse order): extraction, raw handling, consistency and judgment
  reuse existing tools; the script is glue only (R1, R2). Pass.
- V (observable acceptance): tests cover positive, negative and boundary
  cases with synthetic fixtures, interrupted runs and unchanged raw bags;
  the pilot exercises real files. Pass.
- VI (Wiki layers): sources enter raw through `wiki-raw-import`; records are
  pages plus data files in `wiki/`; working files live in state storage with
  a budget and cleanup. Raw sources and private data stay out of the
  repository. Pass.
- VII (storage budget): 200 MB per run folder, cleanup after the commit.
  Pass.
- IX (layout): a work-plugin skill with its script, since the capability is
  education work. Pass.

## Project Structure

### Documentation (this feature)

```text
specs/028-concept-profile/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
plugins/work/skills/concept-profile/
├── SKILL.md
├── references/procedure.md
└── scripts/
    ├── concept_profile.py
    └── concept_profile_test.py
plugins/work/skills/wiki-raw-import/assets/AGENTS.md   # record kinds
package.json, turbo.json                               # test:concept-profile
docs/                                                  # regenerated tables
```

## Stage 2 (a later feature)

Stage 2 needs: the user's decision on the pilot numbers (unclear-share limit,
threshold, claim wording); the list of volumes and exam papers to profile and
their originals copied out of `~/data` where needed; a proposer choice that
scales (Orca workers per material, or a direct API proposer if the pilot's
tokens and time call for it); and the four reference mappings with a
`map` step in the script.

## Complexity Tracking

No constitution violations.
