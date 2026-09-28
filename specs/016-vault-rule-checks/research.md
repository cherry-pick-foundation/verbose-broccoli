# Research: Vault Page Rule Checks

## R1. Where the rule checks run

- **Decision**: A new module, `packages/wiki-consistency/src/wiki_consistency/rules.py`,
  with one entry function that `lint.check` calls after its existing page
  checks. It returns problems in the existing `{document, line, message}`
  form. `update`, `convert`, `index` and `prepare` do not call it.
- **Rationale**: `check` is the step that runs before every vault commit and
  is offline and read-only (feature 010, FR-009 and FR-010); the rules are
  about agent-written text, which `update` never writes. One module keeps
  the rule patterns together, apart from `lint.py`'s region, link, metadata
  and log checks.
- **Alternatives considered**: New checks inside `instance._metadata`,
  rejected because that function also serves `update` and `page_catalog`,
  which must not fail on page prose; a separate command, rejected because
  the schema asks for one check before each commit.

## R2. Which text is checked

- **Decision**: For each page, the page text with two parts blanked out
  (replaced by empty lines, so line numbers stay): every well-formed
  mechanical region, found with `doc_regions.regions.scan`, and the lines of
  the front matter's `sources` field, found from PyYAML's node positions.
  The rest of the front matter is checked like body text. `wiki/index.md`
  is one mechanical region and so has nothing left to check.
- **Rationale**: Mechanical regions are generated from raw metadata; the
  `source_provenance` region prints the original file name, which is often
  Korean, and the recorded times as the bag holds them. The page cannot
  change either. `sources` holds UUIDs and digit-heavy revision names that
  can look like phone or ID numbers. Other front matter fields, such as a
  date field an agent adds, are agent-written and should follow the rules.
  `scan` is the parser the region check already uses, so both agree on
  where regions are.
- **Alternatives considered**: Checking only `title`, `summary` and
  `topics`, which misses other front matter an agent writes; parsing
  Markdown into prose tokens, which is more code and would skip code spans
  that can still hold personal data.

## R3. Reading the roster: reuse backfire's reader

- **Decision**: `wiki-consistency` depends on the repository's backfire
  package with its `education` extra, as a path dependency
  (`backfire = { path = "../backfire", editable = true }` under
  `[tool.uv.sources]`, the way it already uses `../doc-regions`), and calls
  `backfire_education.roster.load_roster()`. A `JudgmentError` with
  `error_type == "backend_not_configured"` becomes a check problem that
  names its `detail` (the file or variable).
- **Rationale**: The root `AGENTS.md` reuse order puts existing repository
  functionality first and prefers less owned code over fewer dependencies.
  `load_roster` already reads `education.toml` and the roster CSV in place
  with feature 011's format rules, refuses non-regular files, and derives
  given names and guardian and school identifiers with the precedence that
  backfire uses when it replaces them. The rule "student names keep the
  roster's spelling, so backfire still replaces them" is best checked with
  backfire's own reader: any copy could drift from it. The work plugin's
  build already places `backfire/`, `doc-regions/` and `wiki-consistency/`
  side by side (`packages/backfire/src/backfire_tools/build.py`, `PLUGINS`),
  so `../backfire` resolves in the repository and in a built plugin.
- **Cost**: `wiki-consistency`'s environment gains backfire's dependencies
  (`jsonschema`, `mcp`, `rfc8785`, `system-one-adapter[openai]`,
  `phonenumbers`). The backfire project's `.venv` must exist before
  `wiki-consistency` is synced, as for `doc-regions` (its setuptools
  metadata lives in `.venv`); the install steps in the skill and in
  `deno task wiki-consistency:install` gain that step.
- **Alternatives considered**: A local reader of about 30 lines with its own
  copy of the given-name rule, rejected by the reuse order and because it
  could drift from backfire's matching.

## R4. Phone numbers, email addresses and name matches: one span finder

- **Decision**: Move the `spans` closure inside
  `backfire_education.pseudonymize.pseudonymize` to a public module-level
  function in the same module that takes the text, the identifier map and
  its compiled pattern, and returns the kept `(start, stop, (kind, value))`
  spans. `pseudonymize` calls it through its existing per-call cache, so
  its behavior and tests stay the same. `wiki-consistency` calls it once
  per page text with the roster's identifiers (or none, when the roster is
  not needed) and maps offsets to lines.
- **Rationale**: This finder is exactly what backfire replaces: roster
  names by kind, phone numbers through `phonenumbers.PhoneNumberMatcher(text,
  "KR")`, and email addresses with feature 011's expression, with overlaps
  merged. Using it means a page passes the name rules only when backfire
  would replace the names, and fails the contact rule for every number
  backfire would treat as a phone. The change is a narrow move of existing
  code, not a rewrite. A spot check on 2026-09-29 with the develop
  worktree's backfire environment found `010-1234-5678`, `02-123-4567`,
  `+82 10 1234 5678` and `01012345678`, and nothing in `2026-09-29`,
  `14:30`, `85/100`, `2026.09.29` or a revision name.
- **Alternatives considered**: Calling `phonenumbers` and copying the email
  expression in `wiki-consistency`, rejected as a second copy of backfire's
  detection; calling `pseudonymize` itself, rejected because it assigns and
  stores pseudonyms in the mapping table, which the read-only check must not
  write.

## R5. Detecting Hangul, Chinese and Japanese letters

- **Decision**: A character is a CJK letter when `str.isalpha()` is true
  and its `unicodedata.name` starts with `HANGUL`, `CJK UNIFIED IDEOGRAPH`,
  `CJK COMPATIBILITY IDEOGRAPH`, `HIRAGANA`, `KATAKANA`, `HALFWIDTH HANGUL`
  or `HALFWIDTH KATAKANA`.
- **Rationale**: The standard library comes first in the reuse order; the
  Unicode names cover the scripts without a hand-kept table of ranges.
  Latin letters with diacritics and Greek letters used in mathematics stay
  allowed.
- **Alternatives considered**: The `regex` package's script properties,
  a new dependency for what the standard library already answers; any
  non-Latin letter, rejected because Greek letters are normal in the
  `default` vault's mathematics pages.

## R6. Resident and foreign registration numbers

- **Decision**: A local pattern: six digits, an optional hyphen, a digit
  from 1 to 8 and six more digits, not inside a longer run of digits, where
  the first six digits are a calendar date in the century that the seventh
  digit gives (1, 2, 5, 6: 1900s; 3, 4, 7, 8: 2000s).
- **Rationale**: The check should catch a mistyped or made-up number as
  well as a valid one, since it is still personal data in form. The date
  test keeps most other 13-digit figures from failing.
- **Alternatives considered**: `python-stdnum`'s `stdnum.kr.rrn`, which
  validates a check digit and so would pass a number with a wrong last
  digit; no check digit, no date test, which fails more unrelated figures.

## R7. Dates, times and addresses

- **Decision**: Local regular expressions and `datetime.date.fromisoformat`
  from the standard library, with the exact forms in the
  [contract](contracts/page-rules.md). Dates are not checked inside link
  destinations and bare URLs.
- **Rationale**: No dependency answers "is this date written in the vault's
  form"; date finders such as `dateparser` search for any date and would
  need the same form rules on top. The forms come from the spec (FR-005,
  FR-006, FR-012, FR-013) and stay a small, tested table.
- **Alternatives considered**: `dateparser.search`, rejected as a heavy
  dependency that finds dates but not their forms, and that would flag
  numbers that are not dates.

## R8. Failure messages

- **Decision**: Each problem names the page, the line and a rule name with
  a short instruction, for example `page rule date-format: write dates as
  YYYY-MM-DD`. No message holds the matched text. The student-page rule
  names the page path, which holds the student's name, because it is the
  page to fix. One problem per rule and line.
- **Rationale**: The check's output is read by agents and may be passed on
  in reports and messages; it must not carry phone numbers or names that
  the page holds (spec FR-002).

## R9. Tests

- **Decision**: Tests in `packages/wiki-consistency/tests/test_rules.py`
  build synthetic vaults with the existing `conftest.py` helpers and a
  synthetic roster CSV named by an `education.toml` in a temporary
  `XDG_CONFIG_HOME`, set with `monkeypatch`. Synthetic names follow the
  style of backfire's fixtures (made-up Hangul names that no real student
  has been checked to have). Each rule's cases are written and seen failing
  before the rule is implemented.
- **Rationale**: Constitution V asks for positive, negative and boundary
  cases with synthetic fixtures; the brief asks for failing-then-passing
  tests per check.
