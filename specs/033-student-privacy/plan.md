# Implementation Plan: Student Privacy Gate

**Branch**: `feature/student-privacy` | **Date**: 2026-09-30 |
**Spec**: [spec.md](spec.md) | **Linear issue**: CHE-61

## Summary

Backfire's education module keeps its shape: `load_roster` reads the roster
in place, `find_spans` finds spans, `pseudonymize` swaps them through the
mapping table and restores labels. This feature adds detectors (romanized
names, EduOK numbers, school years, regions, domain IDs, birth dates,
addresses), makes stand-ins English, and adds two refusals before any
provider call: a re-scan of the swapped request (education mode) and a
Hangul check (both modes). Region names come from the Ministry of the
Interior and Safety's legal-district code list, romanized at generation time
by es-hangul; the generated list is committed with a drift check. Part 2
renames the work vault's student pages after CHE-59 and changes the Wiki
check.

## Technical Context

**Language/Version**: Python 3.14 (backfire), Node 22 with TypeScript
(generator and drift check), uv 0.11.32 or later.

**Primary Dependencies**: unchanged Python dependencies (`phonenumbers`
9.0.40 stays). New: npm devDependency `es-hangul` 2.4.0 (MIT, Toss), pinned
exactly, used only by the generator. New upstream data: the Ministry's
legal-district code list (행정표준코드관리시스템, "법정동코드 전체자료"),
downloaded on 2026-09-30 by `POST https://www.code.go.kr/etc/codeFullDown.do`
with `codeseId=00002`: a ZIP of 413,346 bytes, SHA-256
`44b96f4a86ad102057463a05aae8842f1d706d3e9e69d2dfc409023bf75ca56b`, holding
`법정동코드 전체자료.txt` (CP949, tab-separated, file date 2026-09-17,
SHA-256 `8cfd829c797270b56243a46e9f1e4e95377c2135153c36909021a35a1e32966a`).
Vendor the ZIP unmodified with a record of source, request, date and hashes.
No Python romanizer is used: `korean-romanizer` is GPL-3.0 and, like
`hangul-romanize`, writes `jongro` for 종로 (official `Jongno`); es-hangul
writes `jongno`, `gangneung`, `jeollanam`, `cheorwon`.

**Testing**: pytest in `packages/backfire/tests` (`npm run test:backfire`),
the session-selection and wiki-consistency suites, which call
`load_roster` and `compile_roster_pattern`, and a node test or check for the
generator. Synthetic roster only; no network.

## Constitution Check

- **I, pinned dependencies**: es-hangul and the data file are pinned by
  version and hash. Pass.
- **V, observable acceptance**: leak tests with a fake provider cover every
  kind, both refusals and the re-scan; a cross-provider privacy review adds
  its own leak test. Pass.
- **VII, reuse order and generated files**: the official list and es-hangul
  are reused; local code is detectors and glue. The generated region list is
  deterministic and has a non-mutating drift check in `npm run verify`. Pass.
- **Product and Data Boundaries**: no private record enters fixtures,
  specs, commits or reports. Pass.

## Design

### Stand-ins and the mapping table (`table.py`)

`PREFIXES`: `student` and `given` → `Student`, `guardian` → `Guardian`,
`school` → `School`, `phone` → `Phone`, `email` → `Email`, `region` →
`Region`, `cohort` → `Cohort`, `birth` → `Birth date`, `address` →
`Address`. A stand-in is `f"{prefix} {number:02d}"`. Reading a table whose
entries or counters use the old Korean prefixes (학생, 보호자, 학교, 연락처,
이메일) converts them to the English ones with the same numbers; the next
write stores the English form. Validation otherwise stays as strict.

### Roster (`roster.py`)

Optional columns `id` and `romanized`. Each non-empty value maps to
`("student", <name>)`, the row's student identifier, so the name, the number
and the romanized name share one stand-in. The romanized given name is the
romanized value without its first word (the surname), used only when the
Korean name yields a given name under today's rule; a romanized given name
several students share maps to `("given", <value>)`. `load_roster()` and
`compile_roster_pattern()` keep working for `session_select.py` and
`wiki_consistency.rules`; flexible romanized matching (case-insensitive,
optional hyphen or space between given-name letters, surname first or last)
may use a second pattern, and `find_spans` applies both.

### Detectors (`find_spans`)

Candidates from every detector are merged as today (earliest, then longest,
then kind priority: roster before patterns). Patterns use ASCII-letter and
digit boundaries so they never match inside a longer word or number.

- **Romanized names and EduOK numbers**: from the roster, as above; numbers
  match only as whole digit runs.
- **School year → `cohort`**: the forms FR-003 lists, one normalized value
  per grade so equal grades share a stand-in; academic years stay.
- **Region → `region`**: from the generated list below; case-insensitive,
  optionally followed by a unit word (`City`, `County`, `District`,
  `Province`, `Metropolitan City`, `Special City`, `Special Self-Governing
  City`, `Special Self-Governing Province`, `State`), which is replaced with
  it.
- **Domain ID → `school`**: roster values, and `[a-z][a-z0-9]*(?:-[a-z0-9]+)*-[hme]`
  bounded by characters other than letters, digits and hyphens.
- **Birth date → `birth`**: FR-007's keywords followed within a short gap by a
  date (`2009-03-15`, `2009.3.15`, `09.03.15`, `March 15, 2009`,
  `15 March 2009`, `2009년 3월 15일`) or a year; `NNNN년생` and `NN년생`.
- **Address → `address`**: FR-008's keyword forms up to the end of the line
  or field, and romanized address runs (`Bijeon-ro 12`, `Seo-dong 123-4`,
  `101-dong 1203-ho`, `Jungang-daero 45beon-gil 7`) with an adjacent
  five-digit postal code.
- Phone numbers and email addresses stay as today.

### Region list (generated)

A Node script (for example `scripts/backfire_regions.ts`, run by
`npm run backfire:regions`) reads the vendored ZIP, decodes CP949 with
`TextDecoder("euc-kr")`, and takes every level-1 code (`XX00000000`) and
level-2 code (`XXYYY00000`, including `3611000000`), current or abolished.
Each space-separated part after the province (`수원시`, `장안구`) and each
province name is one entry, deduplicated. For an entry, the unit is its
ending: `특별시`, `광역시`, `특별자치시`, `특별자치도`, `통합특별시`, `도`,
`시`, `군` or `구`; the stem is the rest. Romanized forms, capitalized:

- `<Stem>-<unit>` with `do`, `si`, `gun`, `gu` (`Pyeongtaek-si`,
  `Jongno-gu`), and for the long units the stem with the English unit words;
- the stem alone when the Korean stem has at least two syllables
  (`Pyeongtaek`, `Seoul`);
- for a `도` stem ending in 남 or 북: `South <rest>` or `North <rest>`
  (`North Chungcheong`) and the two-syllable short form (`Chungbuk`).

Korean forms are the full entry (`평택시`, `경기도`). The script writes
`packages/backfire/src/backfire_education/regions.json` deterministically
(sorted, one entry per line) and, with `--check`, compares without writing;
the check runs in `npm run verify` through Turborepo. es-hangul's known gap:
`ㄱ/ㄷ/ㅂ + ㅎ` in proper nouns (`묵호` → official `Mukho`, es-hangul
`muko`); document it as a limit.

### Refusals

- **Re-scan (education mode)**: after the swap, run `find_spans` over every
  string of the swapped state and questions (keys included), with this
  call's stand-ins blanked out first. Any span → `JudgmentError
  ("identifier_remaining")`.
- **Hangul (both modes)**: in `_OrderProvider.evaluate`, after the swap and
  before the first provider call, any character in U+1100-11FF,
  U+3130-318F, U+A960-A97F, U+AC00-D7AF, U+D7B0-D7FF or U+FFA0-FFDC in any
  string of state or questions → `JudgmentError("hangul_remaining")`.
- Both errors map to `pymodel.ProviderError`, name only the error type and
  message, and never the matched text. `failures.py` adds both messages.

### Documents and instructions

- `docs/backfire.md`: Roster (new columns), What is replaced (English
  stand-ins, every kind), the not-detected list (Latin-letter nicknames and
  spellings the roster does not list, region spellings other than the
  generated ones, `묵호`-type romanizations, school names in other forms,
  addresses without a keyword or romanized parts), Mapping table (prefix
  conversion), Troubleshoot errors, and the Hangul refusal in both modes;
  `docs/architecture.md` where it names pseudonyms.
- Work plugin: `skills/backfire/SKILL.md` and `references/verbose-broccoli.md`
  (translate first, what is replaced, the refusals, never the code plugin's
  backfire); `skills/wiki-consistency/SKILL.md` (translate evidence before
  the judgment step); `skills/wiki-raw-import/references/session-selection.md`
  (translate digests before classification).
- Code plugin: `skills/backfire/SKILL.md` and its reference, and
  `skills/model-choice/SKILL.md` and `references/model-choice.md`: never
  student data; requests must be English. Record the local modification in
  each `upstream.json`.

### Part 2 (after CHE-59)

Vault (its own Git repository): roster `id` and `romanized` columns filled
for every row (numbers from the raw EduOK capture's `StudentNo`; romanized
names with customary surnames and es-hangul given names, written together);
pages renamed to `wiki/students/s-<id>.md` with links fixed and romanized
names; schema naming rule changed. Repository: the Wiki check
(`packages/wiki-consistency`) requires `s-<id>` names whose number is in the
roster's `id` column and no Hangul roster names in pages; the schema
template in `plugins/work/skills/wiki-raw-import/assets/AGENTS.md` and the
work plugin's instructions for resolving Korean names follow.

## Size

About 350 lines of Python and TypeScript, 400 of tests, 150 of documents and
one generated line per region (about 600). The branch may pass 1,000 lines;
review whether to split Part 2 before the develop merge review.
