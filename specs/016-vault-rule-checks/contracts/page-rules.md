# Page Rules Contract

`wiki-consistency check` applies these rules after its existing checks. Each
failure is one problem in the existing form, printed as
`<page>:<line>: page rule <name>: <instruction>`, at most one per rule and
line, and never with the matched text.

## Checked text

For every Markdown page under `wiki/` [`log.md`: pending], the page text
with these parts replaced by empty lines:

- each well-formed mechanical region, from its start marker to its end
  marker, as `doc_regions.regions.scan` finds them;
- the lines of the front matter's `sources` field.

Everything else, other front matter fields included, is checked text.
"Same line" below means the same line of the page.

## Roster

- Read with `backfire_education.roster.load_roster()`: the file
  `$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml` (default
  `~/.config/...`) and the roster CSV it names, read only.
- [When it is read: pending.] If reading fails, the check reports one
  problem on document `wiki` line 1, `page rule roster: cannot read the
  roster: <detail>`, where `<detail>` is the `JudgmentError`'s detail (a path
  or variable name), and skips the rules that need the roster.
- Name spans are the spans of kind `student` or `given` (student names and
  given names) and `guardian`; school spans are those of kind `school`.
  Spans come from backfire's span finder (research R4), which matches roster
  values as plain substrings, longest first, and merges overlaps.

## Rules

| Name | Fails on | Instruction |
| --- | --- | --- |
| `phone` | a span of kind `phone` | pages hold no phone numbers |
| `email` | a span of kind `email` | pages hold no email addresses |
| `id-number` | a registration number (below) | pages hold no resident or foreign registration numbers |
| `address` | a postal address (below) | pages hold no postal addresses |
| `student-roster` | a student page whose student is not a roster `name` | add the student to the backfire roster or fix the page name |
| `english` | a CJK letter outside name spans and allowed quotes | write pages in English |
| `school` | a school span holding a CJK letter outside allowed quotes, or a romanized school name | write the school as its domain ID |
| `date` | a date form other than YYYY-MM-DD, or a YYYY-MM-DD date that is not a calendar date | write dates as YYYY-MM-DD |
| `time` | a time of day without a time zone | write the time with its time zone |

`phone`, `email`, `id-number` and `address` apply everywhere in the checked
text, allowed quotes included.

### Registration number

Six digits `YYMMDD`, an optional `-`, a digit `G` from 1 to 8 and six more
digits, with no digit directly before or after. It counts only when
`YYMMDD` is a calendar date in the century `G` gives: 1, 2, 5 or 6 for the
1900s; 3, 4, 7 or 8 for the 2000s.

### Postal address

- A Hangul road-name address: one or more Hangul syllables ending in 로, 길
  or 대로, optional spaces, then a building number `N` or `N-N`.
- A romanized road-name address: a capitalized word, optionally joined with
  more words by hyphens, ending in `-ro`, `-daero` or `-gil`, with a building
  number `N` or `N-N` directly before it (optionally followed by a comma) or
  after it.
- A lot-number address: `N` or `N-N`, optional spaces, then 번지.

### Student page

[pending]

### CJK letter

A character for which `str.isalpha()` is true and whose `unicodedata.name`
starts with `HANGUL`, `CJK UNIFIED IDEOGRAPH`, `CJK COMPATIBILITY IDEOGRAPH`,
`HIRAGANA`, `KATAKANA`, `HALFWIDTH HANGUL` or `HALFWIDTH KATAKANA`.

### Allowed quote

[pending]

### Romanized school name

One or more words that start with a capital letter, each followed by
spaces, then `Elementary School`, `Middle School` or `High School`, matched
case-sensitively. `high school year 2` and `Middle School` alone do not
match.

### Date forms

Dates are not checked inside link destinations (`[text](destination)`),
autolinks (`<...>`) or bare URLs (`http://` or `https://` up to the next
space). Elsewhere, each of these fails:

| Form | Examples |
| --- | --- |
| Four-digit year first, separated by `.` or `/` | `2026.09.29`, `2026/9/29` |
| Four-digit year first, separated by `-`, month or day not two digits | `2026-9-29` |
| Day and month first, then a four-digit year, one separator of `.`, `/` or `-` used twice | `29.09.2026`, `09/29/2026` |
| Day and month first, then a two-digit year, separated by `/` | `9/29/26` |
| A month name or abbreviation (capitalized, with or without a period) next to a day number, in either order, with or without `st`, `nd`, `rd`, `th` or `of` | `Sept. 29`, `September 29, 2026`, `29th of September` |
| A Korean date: digits with 년 then 월, or 월 then 일 | `2026년 9월 29일`, `9월 29일` |

`YYYY-MM-DD` with two-digit month and day passes when
`datetime.date.fromisoformat` accepts it and fails otherwise. A number
directly before or after a form (for example a longer digit run) prevents
the match. `85/100`, `3/4`, `September 2026`, a revision name such as
`20260928T010203000000Z`, and a UUID do not fail.

### Time forms

A time is `H:MM` or `HH:MM` with hour 0 to 23 and minute 0 to 59, optional
`:SS`, optionally followed by `AM`, `PM`, `a.m.` or `p.m.`; or an hour 1 to
12 followed by one of those four. A digit or `:` directly before or after
prevents the match; a `T` before it (as in `2026-09-29T14:30`) does not.

A time passes when an accepted zone follows it: directly (for `Z` and
numeric offsets) or after spaces. A range, two times joined by `-`, `–`,
`—` or `to` with optional spaces, passes when a zone follows its second
time. Accepted zones: [pending].
