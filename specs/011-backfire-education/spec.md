# Feature Specification: Backfire for Education Work

**Feature Branch**: `feature/backfire-education`

**Created**: 2026-09-28

**Status**: Draft

**Linear issue**: CHE-9

**Input**: The Linear issue CHE-9, "Backfire for education work: per-plugin
assembly and pseudonymization", written from the user's decisions of
2026-09-27, and the user's answers of 2026-09-28:

1. Make backfire, the judgment server of feature 005, usable by the work plugin
   for education work such as a student's learning status and progress.
2. One package builds a backfire server for each plugin from modules. The code
   plugin keeps the shared judgment core and a development provider profile.
   The work plugin adds a pseudonymization module and an education provider
   profile. Code is split into modules only where the plugins differ.
3. At backfire's exit to the provider, names, schools, contact details and
   guardian names are replaced with stable pseudonyms such as `학생03`, taken
   from a mapping table kept only on this machine, and restored in responses.
   Names are found by exact match against the student roster; contact details
   are found by format rules. Learning content such as scores and observations
   is sent as is. The same name must get the same pseudonym every time, so a
   replacement that encrypts with a random value per call is not acceptable.
4. Feature 005's FR-015 (the work and chat plugins must not gain or depend on
   backfire) and its assumption that student data stays out are lifted.
5. Judgment quality is measured on education tasks, because feature 005's
   acceptance sets cover code work only.
6. The education profile uses the same provider and model as the development
   profile: DeepSeek V4.1 Flash on Hive (user's answer, 2026-09-28).
7. The roster is an existing export that backfire reads in place. For now, its
   data is EduOK's list of all enrolled students of the academy, read on
   2026-09-28: each student's name, school and grade. It lists no guardian
   names or contact details (user's answers, 2026-09-28).

Out of scope: the chat plugin's variant (CHE-10), the wording of constitution
principle III (CHE-11), and feature 005 itself. Before real student records are
sent, the user turns off training in the Claude and ChatGPT account settings.

## Clarifications

### Session 2026-09-28

- Q: Teachers often write a student by given name alone, such as `라온이` for
  `가라온`, which a full-name exact match misses. Should backfire also replace
  given names alone? → A: Yes. Backfire derives each student's given name from
  the roster's full name and replaces it as well; ordinary words that equal a
  given name are replaced too.
- Q: How should judgment quality on education tasks be measured? → A: Run each
  case of a synthetic education set both with its synthetic names as written
  and pseudonymized, three times, and record accuracy per tool and per arm.
  The result is evidence of whether pseudonyms hurt judgments, not a pass/fail
  gate.

## User Scenarios & Testing _(mandatory)_

The actors are the operator (the user, a teacher who owns the student data and
this machine) and the coding agents (Codex CLI and Claude Code) that run the
work or code plugin and call backfire's tools.

### User Story 1 - Judge student records without revealing who they are about (Priority: P1)

As the operator, I want an agent in the work plugin to call backfire's tools on
a student's records, such as classifying an observation's learning status or
checking a progress claim against lesson notes. The provider should receive
pseudonyms instead of students', guardians' and schools' names and contact
details, and the agent should get its answer in terms of the real names. Then
backfire helps with my main education tasks without the provider learning who
the records are about.

**Why this priority**: Checking learning status and following progress are
main uses of backfire. Without this story, backfire cannot be used on student
records.

**Independent Test**: Build the work plugin alone, run its backfire server
against a scripted provider that records every request, and call a tool with
a synthetic record that names a roster student with Korean particles, a
school, a phone number and an email address. The recorded request holds only
pseudonyms for those, the learning content is unchanged, and the tool's
result names the real student.

**Acceptance Scenarios**:

1. **Given** a roster that lists a student and a school, **When** an agent
   calls a tool with text that names them, including forms with particles such
   as `가라온은` and the given name alone as in `라온이가`, **Then** the
   provider's request holds the student's and the school's pseudonyms, never
   the names.
2. **Given** text with a phone number or an email address, **When** an agent
   calls a tool, **Then** the provider's request holds a pseudonym in place of
   each, whether or not the roster lists them.
3. **Given** the same student named in two calls, in two sessions, or before
   and after a restart, **When** each call reaches the provider, **Then** the
   student has the same pseudonym every time, and two different roster
   entries never share one.
4. **Given** an option or candidate label that names a student, **When** the
   provider answers with the pseudonymized label, **Then** the tool receives
   the label exactly as the agent supplied it, and the result the agent gets
   contains no pseudonym.
5. **Given** a record with scores, dates and observations, **When** it is sent,
   **Then** the only change between the agent's input and the provider's
   request is the replaced names, schools and contact details.
6. **Given** the roster is missing, unreadable or malformed, or the mapping
   table cannot be read or written, **When** an agent calls a tool in the work
   plugin, **Then** the call fails with a reason that names the problem, and
   the provider receives nothing.

---

### User Story 2 - Build a backfire server per plugin (Priority: P2)

As the operator, I want each plugin that uses backfire to get its own build of
it from the one package, with only the parts that plugin needs. The code
plugin keeps working exactly as before, and the work plugin gets backfire
without depending on the code plugin.

**Why this priority**: User Story 1 needs a work build. Keeping the code build
unchanged protects the development use that feature 005 delivered.

**Independent Test**: Build the code plugin and the work plugin into separate
directories outside the repository. The code build passes feature 005's
offline tests and contains no pseudonymization or education profile. The work
build, installed alone, lists the eleven tools and answers through its
pseudonymization. Changing the provider that one plugin selects does not
change the other's.

**Acceptance Scenarios**:

1. **Given** the build is asked for the code plugin, **When** it runs, **Then**
   the output is a code plugin whose backfire behaves as feature 005 specifies,
   with the development profile selected and no pseudonymization.
2. **Given** the build is asked for the work plugin, **When** it runs, **Then**
   the output is a work plugin that declares the backfire server and contains
   the shared core, the pseudonymization module and the education profile.
3. **Given** only the work plugin is installed, **When** a client starts it,
   **Then** backfire starts and answers without any file from the code plugin.
4. **Given** the operator selects another provider for one plugin, **When** the
   other plugin's backfire runs, **Then** it still uses its own selection.
5. **Given** a plugin name the build does not know, or chat, which is out of
   scope, **When** the build is asked for it, **Then** it fails and writes
   nothing.

---

### User Story 3 - Know how well judgments work on education tasks (Priority: P3)

As the operator, I want a measurement of backfire's judgment quality on
education tasks, so I know how far to trust its answers about students before
I rely on them.

**Why this priority**: Feature 005 measured quality on code work only.
Education tasks, and the pseudonyms themselves, may change how well the model
judges.

**Independent Test**: Run the education measurement set through the work build
against the live provider, three times in each of two arms: with the cases'
synthetic names as written, and pseudonymized. Record accuracy per tool and per
arm.

**Acceptance Scenarios**:

1. **Given** the synthetic education set, **When** the measurement runs,
   **Then** every case gets a recorded outcome (correct, wrong or failed) per
   tool and per arm, and a failed response counts as wrong.
2. **Given** both arms have run three times, **When** the results are recorded
   in this feature's research record, **Then** they show accuracy per tool for
   each arm and the cases whose outcome differs between the arms. No accuracy
   level is a pass/fail condition.

---

### Edge Cases

- A roster name is part of a longer roster entry, such as a school name inside
  a longer school name: the longest match is replaced, and a text position is
  never replaced twice.
- A student is written by given name alone, such as `라온이` for `가라온`: the
  given name, derived from the roster's full name, is replaced with the same
  pseudonym as the full name.
- Two roster students share a given name: the given name alone gets its own
  pseudonym, different from both students', so the name is hidden without
  guessing which student it means.
- A roster name or given name also occurs as an ordinary word, such as `하늘`
  in `하늘색`: it is still replaced. A wrong replacement costs some judgment
  quality, while a missed one reveals a name.
- Two different labels, question keys or keys of one object become the same
  text after replacement: the call fails explicitly instead of merging them.
- The agent's input already contains text in the form of a pseudonym, such as
  `학생10명`: it is sent as is. Restoration maps each replaced label back to
  the agent's own text, so it never turns the agent's text into a name.
- A student is added to the roster: the student gets a new pseudonym, and every
  existing pseudonym stays the same.
- A student leaves the roster: the pseudonym stays assigned and is never given
  to anyone else, but the name is no longer detected. The documentation says
  so.
- A name, school or guardian not in the roster, or a contact detail in a format
  no rule covers: it is sent as is. The documentation says which identifiers
  are detected and which are not.
- The mapping table is deleted: new pseudonyms are assigned from then on.
  Calls stay correct, but pseudonyms no longer match those of earlier calls.
- Several sessions assign pseudonyms at the same time: no two entries get the
  same pseudonym, and no assignment is lost.
- Both plugins are installed in one client: each has its own `backfire`
  server with the same tool names. Agents must use the work plugin's server
  for student records; the code plugin's documentation keeps telling them not
  to send such records to its server.
- The code build receives student data by mistake: it sends it as feature 005
  does. Only the work build pseudonymizes, and the code plugin's documentation
  keeps telling agents not to send private personal records.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: One backfire package MUST build a backfire server for the code
  plugin and one for the work plugin, each containing only the modules that
  plugin needs. The shared judgment core MUST exist once in the package;
  modules MUST be split out only where the plugins differ.
- **FR-002**: The code build MUST keep feature 005's behavior, tools and tests
  unchanged, with the development profile selected and no pseudonymization.
- **FR-003**: The work plugin MUST declare the backfire server and offer the
  same eleven tools as the code plugin, with their names, arguments and
  results. It MUST work when installed alone, without the code plugin.
- **FR-004**: Each plugin's backfire MUST use its own provider profile: the
  development profile for code and the education profile for work. The shipped
  education profile MUST use DeepSeek V4.1 Flash on Hive with the same request
  settings as the development profile. The operator MUST be able to change one
  plugin's profile without changing the other's.
- **FR-005**: In the work build, every request MUST pass through
  pseudonymization before it leaves for the provider. The provider MUST NOT
  receive a roster-listed student name, guardian name or school, or a phone
  number or email address, in any part of the request.
- **FR-006**: Student names, students' given names, guardian names and schools
  MUST be detected by exact match against the roster, including when Korean
  particles or other text follow them directly. Each student's given name MUST
  be derived from the full name in the roster. Phone numbers and email
  addresses MUST be detected by format rules, whether or not the roster lists
  them.
- **FR-007**: Each detected value MUST be replaced by a pseudonym that shows
  its kind, such as `학생03` for a student, and that is the same in every call,
  session and restart. A student's given name MUST get the same pseudonym as
  the full name, unless two roster students share it; then it gets its own.
  Two different identifiers MUST NOT share a pseudonym, and a pseudonym MUST
  NOT be reused after its identifier leaves the roster.
- **FR-008**: The mapping between values and pseudonyms MUST be kept only on
  this machine, readable and writable only by the operator, outside the
  repository and the plugin packages. It MUST NOT appear in records, logs,
  errors, reports or committed files. Concurrent sessions MUST NOT lose or
  duplicate assignments.
- **FR-009**: Before the tool receives the provider's answers, every question
  key, option label and level description in them MUST be restored to exactly
  the text the agent supplied. The result the agent receives MUST contain no
  pseudonym that the agent did not write itself.
- **FR-010**: Learning content MUST be sent as is: apart from the replaced
  values, the provider's request MUST be the one the work build would send
  without pseudonymization.
- **FR-011**: The work build MUST fail a call closed, with an explicit reason
  and no provider request, when the roster is missing, unreadable or
  malformed; when the mapping table cannot be read or updated; or when two
  question keys, option labels or keys of one object would become the same.
- **FR-012**: The roster MUST be read in place from a file the operator names,
  and backfire MUST keep no copy of it. It MUST accept, per student, the
  student's name and school, and MAY list guardian names. A change to the
  roster MUST take effect at the next call.
- **FR-013**: Backfire's local records MUST stay content-free as feature 005
  requires: digests of the agent's own input, with no names, pseudonyms or
  mapping entries.
- **FR-014**: The work plugin's documentation for operators and agents MUST
  state what the work build sends to the provider, which identifiers it
  replaces and which it cannot detect, where the mapping table lives, and that
  the user turns off training in the Claude and ChatGPT account settings
  before sending real student records. It MUST also carry feature 005's
  statements that the tools are advisory.
- **FR-015**: This feature MUST supersede feature 005's FR-015 and its
  assumption that student data stays out, and 005's records MUST say so where
  those statements appear. The operator guide's rule against sending private
  personal records MUST be narrowed to the code build, and the code plugin's
  documentation MUST keep telling agents not to send them to the code build.
- **FR-016**: Judgment quality on education tasks MUST be measured with a
  synthetic education set through the work build and the live provider, in
  the two arms User Story 3 describes, and the results MUST be recorded in
  this feature's research record. Billed runs need the user's go-ahead.
- **FR-017**: Acceptance MUST use synthetic records only. Real student records
  MUST NOT enter the repository, fixtures, reports or Linear.

### Key Entities _(include if feature involves data)_

- **Roster**: the operator's list of students, read in place from a file the
  operator names. Per student: name, school, and optionally guardian names.
  The EduOK student list of 2026-09-28 provides name, school and grade.
- **Identifier**: a value to hide from the provider: a student's full or given
  name, a guardian name or a school from the roster, or a phone number or
  email address found by a format rule.
- **Pseudonym**: a stable stand-in for one identifier that shows its kind, such
  as `학생03`, `보호자01` or `학교02`.
- **Mapping table**: the local, operator-only table from identifiers to
  pseudonyms. It only grows: entries are added, never changed or reused.
- **Plugin build**: the output of the build for one plugin: that plugin's
  files, the shared judgment core, and the modules and profile that plugin
  needs.
- **Provider profile**: as in feature 005; the development profile for code
  and the education profile for work.
- **Education measurement set**: versioned synthetic education cases, such as
  observations to classify, progress claims to verify against lesson notes,
  and answers to compare, each with one expected result, fixed before
  measurement.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On a synthetic set that names every roster student (by full and
  by given name), guardian and school at least once, with and without
  particles, plus phone numbers and email addresses, 0 identifiers reach the
  scripted provider, and 100% of results returned to the agent contain the
  original names and no pseudonym.
- **SC-002**: Across two sessions and a restart, each identifier in that set
  gets the same pseudonym every time, and no two identifiers share one.
- **SC-003**: For every call in that set, the provider's request equals the
  request without pseudonymization, except at the replaced identifiers.
- **SC-004**: Under each failure in FR-011, 100% of calls fail with an explicit
  reason, and the scripted provider receives no request.
- **SC-005**: The code build passes all of feature 005's offline tests and
  contains no pseudonymization module or education profile. The only changed
  tests are the build tests, for the new plugin argument; the provider-name
  guard, for the second shipped profile; the failure table, for
  `pseudonym_conflict`; and the readiness tests, for the work build's install
  command.
- **SC-006**: A work build installed alone lists the eleven tools and answers
  one tool call through the live provider, in both Codex CLI and Claude Code,
  registered for that run only without changing saved client settings.
- **SC-007**: The education measurement runs three times in each arm, and its
  accuracy per tool and per arm, with the cases whose outcome differs between
  the arms, is recorded as User Story 3 describes.
- **SC-008**: The work plugin's documentation contains every statement FR-014
  requires, and a scan of the repository finds no real student name or
  contact detail.

## Assumptions

- The roster for now is the EduOK student list of 2026-09-28, kept by the
  operator in a file on this machine. It has no guardian names or contact
  details. Until the operator adds guardian names to the roster, guardian
  names are not detected; phone numbers and email addresses are still caught
  by the format rules.
- Teacher names, grades, dates, scores and observations are not identifiers
  under this feature and are sent as is.
- The mapping table holds keyed digests of identifiers and their pseudonyms,
  not student records. The roster stays owned by EduOK and its export.
  Constitution 1.0.0 (2026-09-28) removed principle III's sentences on a
  second student register and relationship inference, which CHE-11 was to
  clarify.
- The education profile shares the development profile's provider, model and
  credential; only its selection is separate. Usage cost is not an acceptance
  criterion.
- Installing either plugin into saved client configuration needs the user's
  separate approval. Acceptance registers the built plugin per run, as
  feature 005 did.
- The agents themselves (Codex CLI and Claude Code) read real student records
  when the user asks by name; pseudonymization covers only what backfire sends
  to its provider.
- The measurement uses synthetic Korean education records written for it, not
  real ones.
