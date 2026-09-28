# Feature Specification: Vault Page Rule Checks

**Feature Branch**: `feature/vault-rule-checks`

**Created**: 2026-09-29

**Status**: Draft

**Linear issue**: CHE-26

**Input**: Linear issue CHE-26, "Enforce the vault schema's page rules in the
offline check", and the develop session's task brief of 2026-09-29: make the
vault's offline check enforce the schema's page rules that a tool can test,
namely dates as YYYY-MM-DD and times with a time zone; every student who has
a page is in the backfire roster, read through
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml` without changing
it; no contact details or ID numbers in pages; schools written as domain
IDs; and English pages apart from names in roster spelling and short quotes
next to a translation, as far as a pattern can tell. Rules that need
judgment stay with backfire's claim check, and this specification says
which. Tests use their own fixtures and never real student data.

## Background

- The vault schema template,
  `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`, states these page
  rules since CHE-25 (feature 014) and CHE-27 (feature 015) merged: pages in
  `wiki/` are in English, student names keep the roster's spelling so that
  backfire still replaces them, a school is written as its domain ID, and a
  short direct quote may keep its original language next to an English
  translation; dates are written as YYYY-MM-DD and every time with its time
  zone; a student who has a page stays in backfire's roster even after
  leaving the student information system (EduOK); pages hold no phone
  numbers, email or postal addresses, guardian contacts or resident
  registration numbers. Today these rules are text only.
- Feature 010 (`specs/010-wiki-consistency/`) built the offline check,
  `wiki-consistency check`, in `packages/wiki-consistency`, with the region
  model of `packages/doc-regions`. It checks mechanical regions, links, page
  metadata, declared topics, cited bags and the append-only `log.md`. It
  never writes a file or uses the network, and it runs before every vault
  commit.
- Feature 011 (`specs/011-backfire-education/`) defined the roster:
  `education.toml` names a roster CSV with a `name` column and optional
  `school` and `guardians` columns. The work plugin's backfire server
  replaces the roster's student, given, guardian and school names, phone
  numbers and email addresses before a provider call. A name that is not
  written as the roster spells it is sent as it is.
- On 2026-09-29 the `work` vault keeps its student pages in `wiki/students/`,
  one page per student named after the student. The vault does not meet the
  rules yet; CHE-28 rewrites it now, and until CHE-28 commits, this
  feature's checks fail there. The `default`, `chat` and `code` vaults hold
  no pages yet.
- Other work touches nearby files: CHE-24 will add rules on grades, scores
  and evidence citations to the template; CHE-29 (Ruff) and CHE-30
  (ShellCheck) change the repository checks. Whichever feature finishes
  later merges `develop` and keeps every change.

## Clarifications

### Session 2026-09-29

These questions went to the user through the develop session.

- Q: Which pages are student pages, and which roster name belongs to each?
  → A: [pending]
- Q: What is a short quote next to a translation? → A: [pending]
- Q: Is `log.md` checked? → A: [pending]
- Q: Which time zone forms count? → A: [pending]
- Q: When must the roster be configured? → A: [pending]

## User Scenarios & Testing *(mandatory)*

The actors are the user, who owns the vaults and the roster, and a coding
agent (Claude Code or Codex) that writes pages and runs the offline check
before each vault commit.

### User Story 1 - Personal data stays out of pages (Priority: P1)

An agent writes a student page and copies a phone number, an email address,
a home address or a resident registration number from the evidence. Before
the vault is committed, the offline check fails and names the page, the line
and the kind of detail, without repeating the detail itself. An agent also
writes a page for a student whose name is not in the roster, or not in the
roster's spelling. The check fails and names the page, because backfire
would send that name to its provider unreplaced.

**Why this priority**: These rules protect students' personal data. A page
that breaks them leaks data into the vault's history and into the judgments
that backfire sends out.

**Independent Test**: In a temporary vault with synthetic pages and a
synthetic roster named by a temporary `education.toml`, write one page per
kind of detail and one student page whose name is not in the roster, run
the check, and confirm that each fails with its page and line named and no
detail repeated; then remove them and confirm that the check passes.

**Acceptance Scenarios**:

1. **Given** a page that holds a phone number, an email address, a postal
   address or a resident registration number, **When** the check runs,
   **Then** it fails, names the page, line and kind of detail, and does not
   print the detail.
2. **Given** a student page whose student is in the roster, **When** the
   check runs, **Then** the roster rule passes, whether or not the student
   is still in EduOK.
3. **Given** a student page whose student is not in the roster, **When** the
   check runs, **Then** it fails and names the page.
4. **Given** a vault whose check needs the roster and a missing, unreadable
   or malformed `education.toml` or roster file, **When** the check runs,
   **Then** it fails and names the file, and no file changes.
5. **Given** any check run, **When** it finishes, **Then** `education.toml`
   and the roster file are unchanged.

---

### User Story 2 - Pages stay in English, with roster names and school IDs (Priority: P1)

An agent writes a page from Korean evidence and leaves a Korean sentence, a
Korean school name or a romanized school name in it. The check fails and
names the page and line. Student names in the roster's Hangul spelling pass,
and so does a short Korean quote with its English translation beside it.

**Why this priority**: The pages are read by agents working in English and
judged by backfire, which only replaces names spelled as the roster spells
them.

**Independent Test**: In a temporary vault with a synthetic roster, write
pages with a Korean sentence, a Hangul school name, a romanized school name,
a roster name, and a short quote with and without a translation; confirm
that exactly the pages that break the rule fail.

**Acceptance Scenarios**:

1. **Given** a page with Hangul, Chinese or Japanese letters that are neither
   a roster name nor inside an allowed quote, **When** the check runs,
   **Then** it fails and names the page and line.
2. **Given** a page that names a student, a student's given name or a
   guardian in the roster's spelling, **When** the check runs, **Then** the
   English rule passes for those names.
3. **Given** a short quote in its original language with its English
   translation next to it, **When** the check runs, **Then** the English
   rule passes; **Given** a quote without a translation or longer than the
   limit, **Then** it fails.
4. **Given** a page that writes a school by the roster's Hangul school name
   outside an allowed quote, or by a romanized name such as "Example High
   School", **When** the check runs, **Then** it fails and says to write the
   school's domain ID.
5. **Given** a page that writes schools only as domain IDs, **When** the
   check runs, **Then** the school rule passes.

---

### User Story 3 - Dates and times have one form (Priority: P2)

An agent writes "Sept. 29, 2026", "2026.09.29" or "14:30" without a zone.
The check fails, names the page and line, and names the expected form.

**Why this priority**: One date form keeps pages comparable and sortable,
and a time without a zone is ambiguous; but a wrong form leaks nothing.

**Independent Test**: In a temporary vault, write pages with each wrong date
and time form and with the right forms; confirm that exactly the wrong ones
fail.

**Acceptance Scenarios**:

1. **Given** a date written in another form than YYYY-MM-DD, such as
   `2026.09.29`, `2026/9/29`, `09/29/2026`, `29 September 2026` or
   `Sept. 29`, **When** the check runs, **Then** it fails and names the page
   and line.
2. **Given** a YYYY-MM-DD date that does not exist, such as `2026-02-30`,
   **When** the check runs, **Then** it fails.
3. **Given** a time of day without a time zone, **When** the check runs,
   **Then** it fails; **Given** a time followed by an accepted zone, or a
   time range whose end is followed by one, **Then** it passes.
4. **Given** numbers that are not dates, such as a score `85/100`, a
   fraction `3/4`, a revision name or a source ID, **When** the check runs,
   **Then** the date rule does not fail on them.

---

### User Story 4 - The schema says what the check enforces (Priority: P3)

The schema template and the consistency skill say which page rules the
offline check enforces, which stay with judgment, and how student pages are
laid out, so an agent knows what a passing check proves.

**Why this priority**: It changes no behavior, but without it a passing
check would be read as proof of rules it cannot test.

**Independent Test**: Read the template, the skill and the repository
documents that describe the check.

**Acceptance Scenarios**:

1. **Given** the schema template, **When** an agent reads its Wiki rules,
   **Then** they describe where student pages go and name the rules the
   offline check enforces and those left to judgment.
2. **Given** the consistency skill and the repository documents that
   describe `check`, **When** an agent reads them, **Then** they list the
   new rules the same way as the template.

---

### Edge Cases

- A mechanical region, such as the `source_provenance` region that shows a
  Korean original file name and its recorded times, or the `index.md`
  catalog: not checked, because generated text is not agent-written and
  every page that the catalog lists is checked itself.
- Front matter: every field is checked like body text except `sources`,
  which holds source IDs and revision names that can look like phone or ID
  numbers.
- A roster name directly followed by Korean text, such as a particle: the
  name passes and the rest fails, since an English page has no particles.
- A Hangul school name inside an allowed quote: passes, because backfire
  replaces roster school names in quotes too.
- A date inside a URL, such as a news link: the date rule skips link
  destinations, which the page cannot change.
- A number that happens to look like a phone number, such as an 11-digit
  figure starting with 010: the check fails; the page writes the figure
  another way. False failures are preferred to leaked contacts.
- A vault without student pages and without Hangul, Chinese or Japanese
  letters, such as the `default`, `chat` and `code` vaults today: the check
  passes without reading the roster.
- The roster lists a student who has no page: passes; the rule only asks
  that students with pages be listed.
- The `work` vault before CHE-28 commits: the check fails there; this
  feature does not change any real vault.

## Requirements *(mandatory)*

### Functional Requirements

**Scope of the rule checks**

- **FR-001**: The offline check MUST apply the rule checks below to the
  agent-written text of every page in `wiki/`: everything outside
  mechanical regions and outside the front matter's `sources` field.
  [`log.md`: pending]
- **FR-002**: Each rule failure MUST fail the check and name the page, the
  line and the rule, and MUST NOT repeat the matched text, so reports passed
  on carry no personal data. Only the student-page rule names a page whose
  path holds a name.
- **FR-003**: The rule checks MUST keep feature 010's guarantees: no file
  written, no network use, no cache needed, and the same result on every
  machine for the same vault and roster.

**Personal data (User Story 1)**

- **FR-004**: The check MUST fail on phone numbers, found as the work
  plugin's backfire finds them, and on email addresses, found with
  backfire's email expression.
- **FR-005**: The check MUST fail on resident registration numbers and
  foreign registration numbers: six digits of a valid birth date, an
  optional hyphen, then a digit from 1 to 8 and six more digits.
- **FR-006**: The check MUST fail on postal addresses of the forms a pattern
  can tell: a road-name address, in Hangul or romanized, that is a name
  ending in 로, 길, `-ro`, `-daero` or `-gil` followed by a building number;
  and a lot-number address ending in 번지.
- **FR-007**: Student pages MUST be identified as [pending], and the check
  MUST fail on a student page whose student is not a `name` in the roster.
- **FR-008**: The check MUST read the roster through
  `$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml` (default
  `~/.config`) and the roster file it names, with feature 011's format
  rules, only for reading. [When: pending] A missing, unreadable or
  malformed file MUST fail the check and name that file.

**Language, names and schools (User Story 2)**

- **FR-009**: The check MUST fail on Hangul, Chinese (Han) or Japanese (kana)
  letters except where they are part of a roster student name, a given name
  that backfire derives from the roster, or a roster guardian name, matched
  exactly as backfire matches them; or part of an allowed quote.
- **FR-010**: An allowed quote MUST be [pending].
- **FR-011**: The check MUST fail on a roster `school` value that contains
  Hangul, Chinese or Japanese letters when it appears outside an allowed
  quote, and on a romanized school name, one or more capitalized words
  followed by `Elementary School`, `Middle School` or `High School`; the
  failure says to write the school's domain ID.

**Dates and times (User Story 3)**

- **FR-012**: The check MUST fail on a date written in any other form than
  YYYY-MM-DD: year, month and day separated by `.`, `/` or `-` in another
  order or without zero padding; a month name or abbreviation next to a day
  number; or a Korean date with 년, 월 or 일. It MUST also fail on a
  YYYY-MM-DD date that is not a calendar date. A month without a day, such
  as "September 2026", is not a date and passes. Link destinations are not
  checked for dates.
- **FR-013**: The check MUST fail on a time of day, written as `HH:MM` with
  optional seconds or with `AM` or `PM` (`a.m.`, `p.m.`), that is not
  followed by a time zone. A time range such as `14:00–15:30` counts as
  zoned when a zone follows its end. The accepted zones are [pending].

**Documents (User Story 4)**

- **FR-014**: The schema template MUST say how student pages are laid out
  and which page rules the offline check enforces, and MUST list the rules
  that stay with judgment, without changing the rules themselves.
- **FR-015**: The consistency skill, the example schema
  `docs/examples/wiki/AGENTS.md` and `docs/architecture.md` MUST describe the
  check the same way where they describe it.

**Fixtures and privacy**

- **FR-016**: Tests MUST use synthetic pages and a synthetic roster named by
  a temporary `education.toml`; no test may read the user's configuration,
  roster or vaults. No student name, real page or roster content may enter
  the repository, Linear or Orca messages.
- **FR-017**: This feature MUST NOT change any real vault or the user's
  roster or configuration.

### Rules left to judgment

The offline check cannot tell these from a pattern. They stay with
backfire's claim check of each unit against its cited evidence and with the
agent's own review, and a passing offline check does not prove them:

- whether text in Latin letters is English, rather than romanized Korean or
  another language, and whether a quote's translation is faithful;
- whether a student is named by a romanized, shortened or misspelled form of
  the roster name, or a person missing from the roster is named on a page
  that is not a student page;
- whether a domain ID names the right school, and school names written
  without one of the checked suffixes;
- contact details, addresses and ID numbers in forms the patterns do not
  match, such as student numbers, passport numbers, numbers split across
  lines, or a guardian's contact described in words;
- whether a date or time is correct and its zone is the right one, and
  relative dates such as "last Tuesday";
- which source wins when records disagree (EduOK for student information,
  the school's homepage for school information).

### Key Entities

- **Page rule**: One testable rule of the schema's Wiki section, with the
  failure message that names it.
- **Roster**: The operator's student list that `education.toml` names:
  student names, optional schools and guardian names. Read, never changed.
- **Student page**: A page about one student, identified as FR-007 says.
- **Allowed quote**: Original-language text that FR-010 lets stay in an
  English page.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For each rule in FR-004 to FR-013, at least one synthetic case
  fails the check with its page and line named and one close case passes,
  and each failing test was seen failing before its check was added.
- **SC-002**: No rule failure message repeats the matched text.
- **SC-003**: The offline check of a synthetic vault with 500 pages and a
  100-row roster still finishes in under 10 seconds on the development
  machine (feature 010's SC-002).
- **SC-004**: In every test, the roster, `education.toml` and the vault are
  byte-identical before and after the check.
- **SC-005**: No repository file, commit, Linear comment or Orca message
  from this feature holds a student name, a real roster row or real vault
  content.

## Assumptions

- The rules are the ones the schema template states on `develop` at
  `8f1de1e`; CHE-24's later rules on grades, scores and evidence citations
  are not part of this feature.
- The roster format is feature 011's; the check does not add columns.
- `update`, `convert`, `index` and `prepare` do not change; the rule checks
  belong to `check` only.
- Pattern checks prefer a false failure to a missed personal detail; a page
  rewrites a figure that only looks like a contact.

## Out of Scope

- Changing the `work` vault's pages; CHE-28 does that.
- New page rules, or changing the wording of existing ones.
- Sending the rules to backfire as new judgment requests.
- Checking a domain ID against the school's homepage.
