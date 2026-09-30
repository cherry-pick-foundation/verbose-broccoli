# Pilot Report: Concept Profiles of Teaching Materials

**Date**: 2026-09-30 | **Linear issue**: CHE-57 | **Tasks**: T005 to T010

This report gives counts only. The catalog's text, the materials' sentences
and the answer key stay in the work vault and the run folders
(`~/.local/state/verbose-broccoli/concept-profile/`), never here.

## What ran

| Step | Volume | Exam paper |
| --- | --- | --- |
| Material | Common English 2, NE Neungyule (Oh Seon-young), 2022 curriculum, 5 main-text files | 2026-09 Grade 10 English academic assessment (Incheon), question paper PDF |
| Sentences | 250 | 281 |
| Proposer | Claude Code, Fable 5.1, xhigh | same |
| Proposals | 7,352 (29 per sentence) | 6,247 (22 per sentence) |
| Proposer time | about 22 minutes | about 24 minutes |
| Proposer tokens | 127,000 output; 275,000 cache writes; 2.25 million cache reads | 159,000 output; 305,000 cache writes; 4.61 million cache reads |
| Checker | backfire `jev_verify`, education mode, OpenRouter `typesafe/jev-1.13`, one call per sentence | same |
| Check calls | 250 | 276 (5 sentences had no proposal) |
| Check tokens | 4.04 million | 3.52 million |
| Check time | 173 seconds | 158 seconds |

The probes and the first check run moved the OpenRouter key's spend from
$0.04 to $0.32, so about $0.28, or about $0.035 per million tokens. The
second run used the same number of tokens, so about $0.25 more; its exact
share cannot be separated, because other features use the same key. Both
checks ran twice: before and after develop's CHE-61 privacy rules. The
numbers below use the second run. No request was refused.

## Outcomes at the default threshold (0.8)

| | Volume | Exam paper |
| --- | --- | --- |
| Kept | 1,542 (21%) | 1,284 (21%) |
| Dropped | 1 | 0 |
| Unclear | 5,809 (79%) | 4,963 (79%) |
| Invalid results | 3 | 1 |

Backfire called most proposals "verified", with confidence mostly between
0.5 and 0.8, and almost never "contradicted" or "unsupported". Sending the
10,772 unclear items to the user is not workable. Between the two runs,
93 to 94% of outcomes agreed, and confidence moved by a median of 0.04 (0.1
at the 90th percentile), so verdicts near a threshold can change between
runs.

## The answer key

The user asked for a hand-check of 15 sentences (8 from the volume across
its five lessons, 7 from the exam across 7 questions) with 339 proposed
concepts. The develop session (Claude Code, Opus 5.5) filled in the sheet:
287 concepts ticked, 52 unticked, and 22 keys added on the Missing lines of
9 sentences. It read the full passages from the run folders, the catalog's
own examples and range columns from the raw spreadsheet, and for 4 disputed
points the Grammar in Use and CGEL sections that backfire's `jev_rerank`
picked from their unit and section titles. The user reviewed the flagged
points and accepted the sheet. **The accuracy below therefore measures
agreement with a Claude-made answer key that the user accepted, not with an
independent human key.**

Rules the key applied:

1. Range tiers: only the tier that matches the level of the actual word,
   following the tier examples.
2. Named items follow the catalog statements (for example, which article a
   concept names).
3. Joined verbs that share a subject count under both the coordination and
   the verb concept, following the catalog's examples.
4. Form concepts inside a fixed idiom count; a time-clause concept that the
   idiom only looks like does not.

## Accuracy on the 15 sentences

309 concepts are true: 287 of the proposed and 22 that the proposer missed.

| Measure | All | Volume | Exam paper |
| --- | --- | --- | --- |
| Proposer precision | 0.85 (287/339) | 0.76 (156/204) | 0.97 (131/135) |
| Proposer recall | 0.93 | 0.91 | 0.95 |

What a keep rule "verified with confidence of at least t" gives, against all
true concepts:

| t | Kept | Precision | Recall | True concepts left out |
| --- | --- | --- | --- | --- |
| 0.5 | 241 | 0.95 | 0.74 | 57 |
| 0.6 | 201 | 0.96 | 0.62 | 95 |
| 0.7 | 141 | 0.99 | 0.45 | 147 |
| 0.8 (default) | 86 | 0.99 | 0.28 | 202 |

The first run gave the same picture: at 0.5, precision 0.95 and recall 0.69;
at 0.8, precision 0.98 and recall 0.18. At 0.5 the check removed 41 of the
52 false proposals, and 57 true ones with them. Without any check, the
proposer alone has precision 0.85 and recall 0.93.

## Range tiers

The catalog has 231 concepts with a lexical-range tier (1 to 3), in 128
families of the same category, subcategory and guideword; 75 families have
two or more tiers (178 concepts).

| | Volume | Exam paper |
| --- | --- | --- |
| Proposals in tiered concepts | 3,474 of 7,352 (47%) | 2,146 of 6,247 (34%) |
| Sentence-and-family pairs with 2 or more tiers proposed | 1,157 of 1,659 (70%) | 218 of 1,655 (13%) |
| Pairs where the check kept 2 or more tiers, at 0.8 | 8 | 1 |
| Pairs where the check kept 2 or more tiers, at 0.5 | 249 | 74 |

The count is per sentence and family, not per word: proposals name no
words, so two words in one sentence can each show a different tier, and the
key itself kept two tiers for one word once. On the hand-check, tiered
proposals were right 72% of the time (113 of 156) and the others 95% (174 of
183); 43 of the 52 false proposals were tiered. The volume's proposer
tagged every tier from the word's level upward, the exam's picked one tier
by how common the word is, and the key tags only the word's own tier.

Per-sentence CEFR matching is workable for the structures that have no
tiers: 95% of those proposals were right. The tiers are where it breaks
down. They judge a word's level, not a structure, and neither the proposer
nor the check handles them consistently.

## Options for the catalog

- **Keep the English Grammar Profile and collapse the tiers**: treat each
  tier family as one concept for profiling, and derive a word's level from
  a vocabulary list if it is needed. This needs a family column in the
  catalog record, a proposer rule, and a rerun of the pilot.
- **Keep it and fix the tier rule**: tell the proposer to tag only the
  word's own tier (the key's rule 1) and rerun. The key suggests this
  removes most false proposals, but the check still cannot tell tiers apart.
- **Switch to Grammar in Use units as the catalog**, with CGEL for disputes
  and levels through a unit-to-profile mapping. This needs:
  1. a unit list of the three books from their text files in
     `wiki/references/` (unit number, title and book), as a catalog record
     whose data the script can read; today it reads only spreadsheets;
  2. the unit-to-profile mappings of the mapping record, to give units
     levels;
  3. new proposals for both materials and a new hand-check;
  4. keeping Hangul out of backfire: 7 lines of the Advanced Grammar in Use
     text contain it.

## What the method needs whichever way

- A keep rule chosen with the user. The default 0.8 keeps only a quarter of
  the true concepts; 0.5 keeps three quarters at 95% precision. `check`
  would take `--auto-accept`, or `record` would sort the stored confidences
  again without new calls.
- No review queue for the user at this scale. Unclear items stay listed as
  unclear in the record, as the design allows.
- Proposers given the same written tier rule, since the two proposers
  handled tiers differently.
