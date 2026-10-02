# Implementation Plan: Grammatical Competence Profiles, Later Batches

**Branch**: `feature/grammatical-competence-batches` | **Date**: 2026-10-02 |
**Spec**: [spec.md](spec.md)

## Summary

Reconcile which materials still need a profile after feature 036's 63
profiles, prepare one exact file list per batch for the user, and, batch by
approved batch, copy the originals, admit them, run one proposer worker per
material and record the profiles in the work vault. The
`grammatical-competence` and `wiki-raw-import` skills stay as they are. No
repository code is planned; the repository gets these records.

## Research

### R1 - What remains (checked 2026-10-02)

A read-only comparison of every file's SHA-256 in the survey list with the
digests of the source revisions of the 63 recorded profiles gives the
counts in `tasks.md` T002. The first batch's textbook volumes are complete:
11 volumes looked `partial` only because the survey also lists HWP copies of
lessons already profiled from their HWPX files (45 files, all with a
profiled HWPX twin of the same name). Two profiles from feature 028's
pilot (one textbook volume and one office paper) carry other names than the
survey's material IDs; they match their materials by digest.

### R2 - Source checks

Every listed file was converted read-only with the skill's own converters
(`pdftotext -raw` for PDF; python-hwpx through markitdown for HWP and HWPX).
The English letters per material give the work estimate. Failures: ten
files of eight papers are old HWP files that python-hwpx cannot read (one is
named as a 1997-format file); seven of those papers have no readable file,
one has a readable second file. Scanned PDFs have no text. Photo sets have no
text. Details and counts are in `tasks.md` T003.

### R3 - Copy destinations

The first batch put 294 textbook files and 6 exam papers flat into
`~/Documents/20_reference/textbooks/` and `exams/`. Textbook file names are
unique. Among the exam files, 17 names collide (zip members such as the
national papers' even and odd types), so exam copies go into one folder per
paper below `exams/`: `exams/<group>/<paper id>/<original name>`. A member of
a zip is copied out under its own name; the zip stays where it is.

### R4 - Work size and Codex use

At the first batch's rates the remaining 418 materials hold about 95,000
sentences, about six times the first batch's 15,600. The first batch ran at
medium effort; these batches run at `xhigh`, which costs more per
sentence. One weekly Codex window cannot hold all of it, so the batches run
in stages and the first wave of a batch is small enough to measure real
use.

## Procedure per approved batch

1. Copy the approved files (never move); read each destination's SHA-256
   back and compare with the list.
2. Write the selection to `STATE/vaults/work/selections/`, run
   `raw_import.py admit` and `verify`.
3. Per material: `inventory` once per run folder, `extract`, start one
   native Orca worker (Codex `gpt-6.1-sol`, `xhigh`) with the procedure's
   proposer instructions, wait for its `proposals.jsonl`, then `record
   --unchecked`.
4. `wiki-consistency` `update` and `check`, append the log entry, commit
   the pages, data, index and log in the vault. Retain paid results, logs and
   resume evidence; remove only rebuildable scratch after required data and
   receipts persist. Preserve the six saved closeout folders unchanged.

## Constitution Check

- I, VII (reuse order): the existing skills do everything; no code is
  added. Pass.
- V (observable acceptance): copy digests, `verify`, the Wiki check and the
  counts per material. Pass.
- VI (Wiki layers): sources through `wiki-raw-import`, profiles as pages
  and data files, working files in state storage. Pass.

## Project Structure

```text
specs/044-grammatical-competence-batches/
├── spec.md
├── plan.md
└── tasks.md
```

Private, outside the repository: the survey folder's `lists-2026-10-02/`,
`precheck-2026-10-02*.tsv`, the work vault's `raw/` and `wiki/profiles/`, and
the run folders.

## Complexity Tracking

No constitution violations.
