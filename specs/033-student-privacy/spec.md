# Feature Specification: Student Privacy Gate

**Feature Branch**: `feature/student-privacy`

**Created**: 2026-09-30

**Status**: Planned

**Linear issue**: CHE-61

**Input**: Linear issue CHE-61, "Hide all student identifiers from
non-Claude/ChatGPT models and name student pages by student number", its
comments of 2026-09-30, and the develop session's task brief of the same day.
Identifying details must never reach Jev or any other model provider except
the user's own Claude and ChatGPT accounts, which have training turned off.
Backfire's education mode (work plugin) is the single gate for every other
provider; the code plugin's backfire never receives student data.

Every example in this feature is synthetic. Specs, commits, Orca messages,
Linear and reports name students only by count or by EduOK student number.

## Clarifications

### Session 2026-09-30

Decided by the user in CHE-61 and its comments, relayed by the develop
session.

- Everything sent to or received from Jev is English, in both backfire modes.
  Stand-ins are English (`Student 03`, `Guardian 01`, `School 02`,
  `Region 01`, `Phone 01`, `Email 01`). A request that still contains Hangul
  after the swap is refused. Korean content is translated into English by
  Claude or ChatGPT before any backfire call.
- The Wiki is English only. Student names inside pages are romanized; the
  Korean spelling stays only in the roster, which gains a romanized-name
  column, and backfire hides the romanized form too.
- Student page files are `wiki/students/s-<EduOK student number>.md`. The
  number is not backfire's stand-in: EduOK numbers are hidden from Jev too,
  and the gate replaces both the number and the name with the stand-in.
- When the user names a student in Korean, agents resolve the name to the
  EduOK number through the roster or the raw EduOK capture, then open the
  page. Pages hold no Korean names.
- Q: Birth dates kept leaking in new forms after five fix rounds, and wider
  matching removed scores and lesson dates. How should the gate treat them?
  → A: after a birth keyword, hide the rest of that clause, up to a sentence
  end, semicolon, line break or table cell end, as one `Birth date`
  stand-in, accepting that other content in that clause is hidden too;
  document the trade-off, and have a fresh Codex privacy reviewer confirm it.
- Q: Which romanization do the roster and pages use? → A: customary surname
  spellings (Kim, Lee, Park, Choi) with Revised Romanization for given names,
  written together: `Kim Gildong`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nothing identifying leaves for Jev (Priority: P1)

An agent sends translated, English student material through the work
plugin's backfire. Before the request leaves, backfire replaces every
identifier it can detect with an English stand-in, scans the request again,
and refuses to send it if an identifier or any Hangul remains.

**Why this priority**: It is the user's privacy rule and the core of CHE-61.

**Independent Test**: With a synthetic roster and a fake provider, send
requests carrying each identifier kind and check what the fake provider
receives or that nothing is sent.

**Acceptance Scenarios**:

1. **Given** a synthetic roster with a Korean name, romanized name, EduOK
   number, school and domain ID, **When** a request names the student in any
   of those forms, **Then** the provider receives the same `Student NN` for
   all of them and none of the original values.
2. **Given** a request with a school year, a region, a domain ID, a birth date
   or an address, **When** it is sent, **Then** each is replaced by its
   stand-in and learning content such as scores and lesson dates is sent as
   is.
3. **Given** a request that still holds Hangul after the swap, such as a name
   missing from the roster, **When** it is sent, **Then** backfire refuses it
   with `hangul_remaining`, sends nothing, and the error holds no request
   text.
4. **Given** a detected identifier survives the swap, **When** the request is
   checked, **Then** backfire refuses it with `identifier_remaining` and
   sends nothing.

### User Story 2 - The code plugin's backfire stays English and data-free (Priority: P1)

The code plugin's backfire, including model choice, and the chat plugin's
credit-offer search refuse any request that contains Hangul. Their
instructions say they never receive student data.

**Independent Test**: Send a Hangul request through the provider without
education mode and check the refusal.

**Acceptance Scenarios**:

1. **Given** backfire without `--education`, **When** a request holds
   Hangul, **Then** it is refused with `hangul_remaining` and nothing is sent.

### User Story 3 - Agents translate first and find students by number (Priority: P2)

The work plugin's instructions tell agents to translate Korean material into
English before any backfire call, never to send student data to the code
plugin's backfire, and to resolve a Korean student name to the EduOK number
before opening a student page.

**Independent Test**: In a Claude Code session and a Codex session, ask in
Korean about a synthetic or real student; each finds the right
`s-<number>.md` page. Report the result without names.

### User Story 4 - Student pages are named by EduOK number (Priority: P2)

After CHE-59 finishes, student pages move to `wiki/students/s-<number>.md`,
their text uses the romanized name, links follow, and the vault schema and
the Wiki check enforce the new rule.

**Independent Test**: The Wiki check passes on the renamed vault, fails on a
page named otherwise or with a number missing from the roster, and no page
holds Hangul names.

### Edge Cases

- A romanized name written with a hyphen or space between given-name
  syllables, in any case, or with the surname last, is still replaced.
- A given name several students share gets its own stand-in, as today.
- Region names that equal ordinary words or given names are replaced too,
  which can cost judgment quality; the documentation lists them as a limit.
- Choice labels that become equal after the swap still fail with
  `pseudonym_conflict`.
- An existing mapping table keeps its numbering; old Korean prefixes read as
  the English ones.
- Students without an EduOK number get an assigned number only after the user
  approves it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Stand-ins MUST be English: `Student NN`, `Guardian NN`,
  `School NN`, `Region NN`, `Phone NN`, `Email NN`, and for the new kinds
  `Cohort NN` (school year), `Birth date NN` and `Address NN`. The mapping
  table MUST keep existing numbers.
- **FR-002**: The roster MUST accept optional `id` (EduOK student number) and
  `romanized` (romanized name) columns. Both MUST map to the stand-in of that
  row's student. Romanized names MUST match case-insensitively, with or
  without a hyphen or space between given-name letters, and with the surname
  first or last; the romanized given name alone MUST match under the same
  rule as Korean given names (at least two Korean syllables).
- **FR-003**: School years MUST be replaced with no coarse band: English
  forms (`Grade 10`, `10th grade`, `Year 11`, `first-year high school
  student`, `high school sophomore`) and Korean forms (`고1`, `중2`, `초6`,
  `1학년`, `예비 고1`); academic years such as `2026학년도` or `the 2026
  school year` MUST stay.
- **FR-004**: Region names MUST come from the Ministry of the Interior and
  Safety's legal-district code list, pinned, not a hand-kept list: every
  province and city/county/district name, current or abolished, in Korean and
  in its Revised Romanization forms, as plan.md defines.
- **FR-005**: School domain IDs MUST be replaced as schools: roster values and
  lowercase tokens ending in `-h`, `-m` or `-e` such as `byeolbit-h`.
- **FR-006**: EduOK student numbers from the roster's `id` column MUST be
  replaced where they stand as whole numbers.
- **FR-007**: After a birth keyword (`born`, `birthday`, `birth date`,
  `date of birth`, `DOB`, `생년월일`, `생일`, `출생`), the rest of its clause,
  up to a sentence end, a semicolon, a line break or a table cell end, MUST
  be replaced as one birth date when it holds a digit, a month name, a year in
  words or a Roman numeral year; other text in that clause is hidden with it.
  `NNNN년생` is a birth year. Text after the clause stays.
- **FR-008**: Addresses MUST be replaced: the rest of a field after an address
  keyword (`address`, `주소`) and romanized Korean address parts (`-ro`,
  `-gil`, `-daero`, `-dong`, `-eup`, `-myeon`, `-ri` names with their
  numbers, apartment units such as `101-dong 1203-ho`).
- **FR-009**: After the swap, education mode MUST scan the serialized
  outgoing state and questions again with every detector, ignoring the
  stand-ins it inserted, and refuse with `identifier_remaining` if anything
  remains.
- **FR-010**: In both modes, a request whose serialized state and questions
  contain Hangul (syllables or Jamo, composed or decomposed) MUST be refused
  with `hangul_remaining` before any provider call.
- **FR-011**: Errors and logs MUST NOT contain matched values or request
  text.
- **FR-012**: `docs/backfire.md` MUST describe the roster columns, the
  English stand-ins, every kind replaced, the refusals and an updated list of
  what is not detected.
- **FR-013**: The work plugin's instructions MUST say to translate Korean
  material into English with Claude or ChatGPT before any backfire call
  (backfire skill, Wiki check evidence step, session selection), and that the
  code plugin's backfire never receives student data; the code plugin's
  backfire skill and the model-choice skill and reference MUST say the same.
- **FR-014**: Tests MUST use a synthetic roster only and include leak tests:
  for each kind, the provider's received request holds no original value.
- **FR-015** *(Part 2)*: The roster MUST gain filled `id` and `romanized`
  columns; numbers are assigned only to students with none, after the user
  approves.
- **FR-016** *(Part 2)*: Student pages MUST be `wiki/students/s-<id>.md`
  with romanized names, links updated, no Hangul names; the vault schema's
  naming rule, the schema template and the Wiki check MUST enforce it.
- **FR-017** *(Part 2)*: The work plugin's instructions MUST tell agents to
  resolve a Korean student name (given names, particles, shared names; ask
  when ambiguous) to the EduOK number through the roster or the raw EduOK
  capture before opening the page.

### Key Entities

- **Roster row**: `name`, optional `school`, `guardians`, `grade`, `id`,
  `romanized`; read in place by backfire.
- **Region list**: generated from the official list; Korean and romanized
  forms per province and city/county/district.
- **Stand-in**: an English label and a two-digit number, stable across calls
  through the mapping table.

## Success Criteria *(mandatory)*

- **SC-001**: Every leak test passes: no synthetic identifier of any kind
  reaches the fake provider.
- **SC-002**: A privacy review by a reviewer from another provider than the
  implementer, with its own leak test, finds no identifier that reaches the
  provider undetected beyond the documented limits.
- **SC-003**: `npm run verify` reports VERIFIED on the merged result.
- **SC-004** *(Part 2)*: The Wiki check passes on the renamed vault, and the
  Claude and Codex lookup tests each open the right page.

## Assumptions

- Claude and ChatGPT may read student data; translation happens in the
  agent's own session before any backfire call.
- Pattern detection cannot prove absence: text that no detector recognizes
  and that holds no Hangul, such as a nickname in Latin letters, still
  reaches the provider. The documentation says so.
