# Research: Backfire for Education Work

Decisions for [plan.md](plan.md), each with its rationale and the alternatives
considered. Evidence was gathered on 2026-09-28 on the operator's host (Linux
x86_64, kernel 7.0.0-34-generic, uv's managed CPython 3.14.4).

## Where pseudonymization sits

**Decision**: Inside the shared judge, between request validation and the
adapter call. `backfire.judge.judge` hands the state and questions to the
pseudonymization module, sends the pseudonymized copies through the adapter,
and gives the adapter's answers back to the module for restoration. The
judgment record keeps the digest of the agent's original state and questions.

**Rationale**: Everything the provider receives is built by
`system-one-adapter` from exactly two inputs, `state` and `questions`
(`packages/backfire/src/backfire/judge.py`, `client.system_one(state,
questions)`); the adapter adds only its own fixed prompt text. Replacing
identifiers in those two structures is therefore the last point where the
agent's data can be changed before it leaves, and the first point where the
answers come back as typed data. The answers hold no free text, only question
keys, option labels, probabilities, scores and Score legends
(`typesafe_sdk/_schemas/models.py`: `ChoiceAnswer`, `NoulAnswer`,
`ScoreAnswer`), so restoring means mapping keys, labels and legend texts back,
which a per-request map does exactly.

**Alternatives considered**:

- Replace text in the rendered provider messages inside `ProfileProvider` and
  restore the raw response text before the adapter parses it. This is the
  literal network exit, but the model's output would have to be rewritten as
  text before its JSON is checked, and malformed output could be restored
  wrongly. The judge-level point sends the same bytes with less code.
- Wrap the judge from outside, in the MCP entry point. Other in-process callers
  of the judge in a work build, such as the readiness check or a later
  package's own calls, would bypass it, and the judgment record would digest
  the pseudonymized input, in which two different inputs can collide
  (`가라온` and `라온` both become `학생03`).

## Turning it on per build

**Decision**: A top-level `pseudonymize = true` in the shipped `config.toml` of
the work build turns pseudonymization on for every judgment that build makes.
Only the shipped file may contain the key; the operator's `config.toml` is
rejected if it does. When the key is true, the judge imports
`backfire_education.pseudonymize`; if that fails, every judgment fails with
`backend_not_configured` naming the shipped file. The code build's shipped
file has no such key, so its judgments are unchanged.

**Rationale**: The property belongs to the build, not to a provider profile or
an entry point. An operator who replaces or adds a provider table, which
feature 005 allows, cannot turn pseudonymization off by accident, and every
entry point of the work build (`backfire serve-mcp`, `backfire ready`, and
in-process callers) passes through the same judge. Both builds keep the same
`backfire serve-mcp` command.

**Alternatives considered**:

- A key inside the education profile table. The operator's table replaces the
  shipped table whole (feature 005), so a replacement without the key would
  silently disable pseudonymization.
- A separate entry command for the work build (`python -m backfire_education
  serve-mcp`). It covers only the server; readiness and in-process callers
  would still reach the provider unpseudonymized.

## Per-plugin build

**Decision**: `deno task backfire:build -- <plugin> <output>` with `<plugin>`
`code` or `work`. `backfire_tools/build.py` keeps one table that names, per
plugin, the source packages under `packages/backfire/src/` to copy and the file
that becomes the build's shipped `backfire/src/backfire/config.toml`:

| Plugin | Packages copied | Shipped `config.toml` from |
| --- | --- | --- |
| `code` | `backfire` | `src/backfire/config.toml` (development profile) |
| `work` | `backfire`, `backfire_education` | `src/backfire_education/config.toml` (education profile) |

The build copies `plugins/<plugin>/` and then the listed packages, skipping
every package's own `config.toml`, and writes the selected profile file to
`backfire/src/backfire/config.toml`. Everything else about the build (partial
directory, budget, symbolic-link refusal, interruption cleanup) stays as
feature 005's
[mcp-server contract](../005-jev-decision-backend/contracts/mcp-server.md#distribution-build)
describes.

**Rationale**: The shared core exists once in the source tree, and each build
contains only what its plugin needs (FR-001): the code build has no education
package or profile, and the work build has no development profile. Putting
the selected profile at the core's fixed path lets feature 005's configuration
code, readiness check and documentation work unchanged in both builds. A
later package that the work plugin needs is one more entry in the work row.

**Alternatives considered**:

- Keep `backfire:build -- <output>` for the code plugin and add a flag for
  work. A required plugin name is explicit, and the only callers are the
  operator guide and the build tests.
- Teach the core configuration loader a per-plugin shipped file. That changes
  feature 005's configuration code for a choice the build can make by copying.

## Education profile and per-plugin selection

**Decision**: The work build ships a separate profile table,
`[providers.education]`, with the same values as the development profile's
`[providers.hive]` (DeepSeek V4.1 Flash on Hive, the same request, thinking and
status settings), and selects it with `provider = "education"`. Its credential
file is `$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.env`, holding
`HIVE_API_KEY`; a symbolic link to `hive.env` is accepted, because feature
005's credential check inspects the opened file. The operator's shared
`config.toml` changes one plugin's provider by replacing that plugin's table:
`[providers.education]` for work, `[providers.hive]` for code. A top-level
`provider = "<name>"` line in the operator file selects for both builds, and
the operator guide says so.

**Rationale**: The user chose Hive and DeepSeek V4.1 Flash for education and a
separate profile table so the two can diverge later without code changes
(2026-09-28). Profile names choose credential files in feature 005, so a
separate name also means the work build cannot call the provider until the
operator places `education.env`, an explicit opt-in to sending education data.
No core configuration code changes.

**Alternatives considered**:

- Reuse the `hive` table in the work build. Replacing it in the operator file
  would then change both plugins, which FR-004 forbids.
- Separate operator files per plugin. That changes feature 005's
  configuration paths and code for no gain over replacing one table.

The two tables are two copies of the same provider facts. Keeping them apart
is the user's decision; they are expected to diverge.

## Detection and replacement: standard library and phonenumbers, not Presidio

**Decision**: Detect roster values with one compiled regular expression of the
escaped values, longest first; detect phone numbers with `phonenumbers`
9.0.40 (`PhoneNumberMatcher(text, "KR")` at its default `VALID` leniency);
detect email addresses with one regular expression. Merge the spans, keep the
leftmost and then longest of any overlapping spans, and replace them in one
pass with Python string slicing. Presidio is not used.

**Rationale**: AGENTS.md prefers the standard library first. The probe on
2026-09-28, in a scratch environment on CPython 3.14.4:

- `presidio-anonymizer` 2.2.364 (MIT) installs in 16 MB and takes 1.3 s to
  import, pulling in `cryptography`. What it adds is span replacement, which
  is string slicing. Given two overlapping spans of different types, it
  replaced both and produced broken text (`학생03X`), so overlap resolution is
  needed before it anyway.
- `presidio-analyzer` 2.2.364 raises the environment to 302 MB with spaCy,
  thinc and numpy, for recognizers this feature does not use: names come from
  the roster by exact match, not from a language model. Its deny-list
  recognizer only matches a value between non-word characters
  (`_deny_list_to_regex` in `presidio_analyzer/pattern_recognizer.py`), which
  Korean particles defeat: in the probe it found `가라온` standing alone but
  not in `가라온은`.
- Presidio's phone recognizer wraps `phonenumbers` (Apache-2.0), the Python
  port of Google's libphonenumber, and that library alone does the work. In
  the probe it found `010-1234-5678`, `01098765432`, `031-651-1234` and
  `+82 10-2222-3333` in Korean text with particles attached, and none of
  `2026-09-28 10:30`, `20-24, 26, 29-37번` or `1234567890`. At `POSSIBLE`
  leniency it also took the date, so the default `VALID` stays.

The CHE-9 issue says Presidio "can do the replacement"; it names it as an
option, not a requirement. What the issue forbids, Presidio's `encrypt`
operator, is not used either way.

**Alternatives considered**: Presidio anonymizer with local detection (adds a
dependency for string slicing); Presidio analyzer with a custom Korean
recognizer (adds spaCy for regular expressions); a local phone-number
expression (reimplements `phonenumbers`).

## Given names

**Decision**: For each roster student whose name is all Hangul and at least
three syllables long, the given name is the name without its surname: the
first two syllables are the surname when the name has at least four syllables
and starts with one of the two-syllable surnames 남궁, 황보, 제갈, 선우, 서문,
독고 or 사공; otherwise the first syllable is. A derived given name shorter than
two syllables is not used. A given name that exactly one student has gets that
student's pseudonym; one that several students share gets its own pseudonym.

**Rationale**: The user chose to derive given names from the roster
(2026-09-28). Korean surnames are almost always one syllable; the listed
two-syllable surnames cover the common exceptions. A one-syllable given name
would match inside countless ordinary words, so it is not matched; the
operator guide says so. All ten students in the EduOK list of 2026-09-28 have
three-syllable names with one-syllable surnames.

**Alternatives considered**: A Korean name-splitting library (none is needed
for this rule, and none was found worth a dependency); given names only as the
operator lists them (rejected by the user).

## Mapping table

**Decision**: One JSON file,
`$XDG_DATA_HOME/verbose-broccoli/backfire/pseudonyms.json`, mode `0600`,
holding a random 32-byte key made on first use, one counter per pseudonym
kind, and entries from `HMAC-SHA256(key, kind + ":" + normalized value)` to
the assigned pseudonym. Updates happen under an exclusive `flock` on
`pseudonyms.lock` in the same directory, written to a temporary file there,
flushed and renamed over the table. The table may not exceed 1 MiB; a change
that would pass that fails the call.

**Rationale**:

- Stability: the same normalized value always gives the same digest, so the
  same pseudonym, across calls, sessions and restarts (FR-007). Counters only
  grow, so a pseudonym is never reused (FR-007).
- Privacy: the table holds no names, schools or contact details, only keyed
  digests and pseudonyms. It is not a second student register (constitution
  III); the roster stays with its owner and is read in place.
- Concurrency and interruption: the lock serializes sessions, and the rename
  makes each update all-or-nothing, as feature 005's record writer does with
  its own lock (`packages/backfire/src/backfire/records.py`).
- Storage budget: constitution VII needs a positive budget for every
  persistent writer. At about 100 bytes per entry, 1 MiB holds about 10,000
  identifiers; the roster is tens of students, and contact values grow only
  with those actually sent.

The table is durable data, not state or cache: deleting it loses the
stability of pseudonyms across calls, which is why it lives under the XDG data
root (constitution VI).

**Alternatives considered**: Store names in clear (a readable second register
of names); plain SHA-256 (anyone with the table could test guesses without a
key, although the key sits beside it, so the gain is only against casual
reading); a database (constitution I requires PGlite for durable relational
storage, which one small file does not need).

## Roster format

**Decision**: A UTF-8 CSV file (a byte-order mark is accepted) with a header
row. Column `name` is required; `school` and `guardians` are optional, and
`guardians` holds names separated by `;`. Other columns, such as a grade, are
ignored. The path is `roster` in
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml`, and it must be
absolute. The file is read at every call and never copied.

**Rationale**: The user chose an existing export read in place (2026-09-28).
EduOK offers no export file today; the list the user supplied was read from
EduOK's web page by another agent, so the operator saves it once as a file.
CSV is what spreadsheet and school systems export, the standard library reads
it, and ignoring extra columns lets an export with more fields be used as it
is.

**Alternatives considered**: The JSON shape of the legacy files under
`~/projects/work` (an earlier project's format, which constitution IV does not
let target code depend on); TOML written by hand (no system exports it).

## Education quality measurement

**Decision**: A synthetic Korean education set,
`scripts/backfire/fixtures/education-v1.jsonl`, in the known-answer format of
feature 005 (`id`, `tool`, `language`, `kind`, `arguments`, `expect`), with a
synthetic roster, `education-roster-v1.csv`, beside it. A runner in
`backfire_tools/acceptance/` calls the tools in process with the real judge,
three times in each of two arms: without pseudonymization, and with it,
using the synthetic roster and a temporary mapping table. It prints per case,
run and arm whether the result matched, and the per-tool accuracy of each arm;
the results go into this file. No accuracy is a pass/fail condition.

**Rationale**: The user chose to record both arms without a bar (2026-09-28).
Feature 005's known-answer format already expresses expected results as
dotted result paths. Running in process isolates the model's judgment from the
transport that the offline tests and the client check already cover.

**Alternatives considered**: Running the measurement through a built server
(adds process handling to every call without measuring anything new); a pass
bar (not chosen by the user).

## Client check

**Decision**: Register the built work plugin's server per invocation in Codex
CLI and in Claude Code, as feature 005's
[client registration](../005-jev-decision-backend/contracts/mcp-server.md)
did, with a temporary `XDG_CONFIG_HOME` holding `education.toml` (pointing at
the synthetic roster) and an `education.env` link to the operator's
`hive.env`, and a temporary `XDG_DATA_HOME`. Each client lists the eleven
tools and answers one call. No saved client setting changes.

**Rationale**: Installing into saved client configuration needs the user's
separate approval (spec Assumptions). A link keeps the key in one file and out
of the temporary directory.

## Results

### Offline suites

On 2026-09-28 at `0c1416d`, the coordinator ran quickstart steps 1 to 4 and the
checks of T022:

- `deno task backfire:install`, then `deno task test:backfire`: 1,337 passed,
  3 deselected (the slow tests). The end-to-end suite
  (`packages/backfire/tests/test_education_e2e.py`) covers step 4, SC-001 to
  SC-004, the eleven tools of FR-003 and a roster edit taking effect at the
  next call (FR-012).
- `deno task test:backfire-slow`: 3 passed.
- Steps 2 and 3 in a scratch directory outside the repository: the code build's
  `src/` holds only `backfire/` with the development profile; the work build's
  holds `backfire/` and `backfire_education/`, its only `config.toml` equals
  `backfire_education/config.toml`, and it installed offline with
  `uv sync --frozen --no-dev --extra education`. A `chat` build exited with 1
  and wrote nothing.
- `deno task check` and `deno task verify` passed.

A probe of the pseudonymizer replaced Korean mobile numbers written as
`010-1234-5678`, `01012345678`, `010 1234 5678` and `+82 10-1234-5678` with one
pseudonym and a Seoul landline with another, and left dates such as
`2026.09.28` and `20260928`, scores and ranges unchanged; `0c1416d` added these
cases to the unit tests.

### Client check

Pending the user's go-ahead (T020).

### Education measurement

Pending the user's go-ahead (T014).
