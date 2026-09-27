# Pseudonymization Contract

This is what a work build's judge does to every judgment when its shipped
`config.toml` has `pseudonymize = true`
([configuration.md](configuration.md)). The code build never does it.

## Place in the judge

In `backfire.judge.judge`, in this order:

1. Validate the request as feature 005 does, on the agent's questions.
2. Pseudonymize: load the roster and the table and replace identifiers in the
   state and the questions (below). This runs in a worker thread, off the
   event loop, and within the call's deadline.
3. Load the profile and credential and call the adapter with the
   pseudonymized state and questions.
4. Validate the answers as feature 005 does, then restore them (below).
5. Write the judgment record with the digest of the agent's original state and
   questions, as feature 005 does.

A failure in step 2 ends the call before any provider request. Cancellation
behaves as in feature 005.

`judge` takes one new optional keyword, `pseudonymize`. The default, `None`,
follows the shipped `config.toml`, and the tools never pass it. The
measurement runner and tests pass `True` or `False` to choose explicitly.

## Roster

A UTF-8 CSV file, with or without a byte-order mark, and a header row:

| Column | Required | Meaning |
| --- | --- | --- |
| `name` | yes | The student's full name. |
| `school` | no | The student's school, as written in the source. |
| `guardians` | no | Guardian names, separated by `;`. |

Other columns are ignored. Leading and trailing spaces in cells are removed;
empty optional cells are skipped. Rows that repeat a name describe the same
identifier.

## Identifiers and their kinds

| Kind | Found by | Normalized value | Pseudonym prefix |
| --- | --- | --- | --- |
| `student` | exact match of a roster `name` | the name | `학생` |
| `student` | exact match of a given name that one student has | that student's name | `학생` (the same as the full name) |
| `given` | exact match of a given name that several students share | the given name | `학생` (its own number) |
| `guardian` | exact match of a roster guardian name | the name | `보호자` |
| `school` | exact match of a roster `school` | the school | `학교` |
| `phone` | `phonenumbers.PhoneNumberMatcher(text, "KR")`, default leniency | E.164 form | `연락처` |
| `email` | the expression below | lowercase | `이메일` |

Given names follow [research.md](../research.md#given-names): only all-Hangul
names of at least three syllables; the surname is the first syllable, or the
first two when the name has at least four syllables and starts with 남궁, 황보,
제갈, 선우, 서문, 독고 or 사공; a given name shorter than two syllables is not
used. When one text value belongs to several kinds, the first row of the table
above wins.

Email expression: `[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+`.

Exact matches are plain substring matches, so `가라온은`, `라온이가` and
`가상별중학교` are caught; a match is not required to stand alone.

## Replacement

For each string:

1. Find all roster matches with one expression of the escaped values, longest
   first, and all phone and email matches.
2. Sort the spans by start and then by length, longest first, and keep a span
   only if it does not overlap one already kept.
3. Replace each kept span with its identifier's pseudonym.

The state is replaced in every string value and every object key, at any
depth. Each question is replaced in its JSON form, including its key in the
questions mapping, its instructions, its criteria keys and texts and its level
descriptions, and is rebuilt with its own class. The adapter's own fixed text
is never touched.

If two different keys of one object, two question keys, or two option labels of
one question become the same string, the call fails with
`pseudonym_conflict` before any provider request. Otherwise text that already
looks like a pseudonym, such as `학생10명`, is sent as is.

## Pseudonyms

A pseudonym is its prefix and a number of at least two digits: `학생03`,
`학생104`. Numbers count up from 1 per prefix and are never reused.

## Mapping table

`pseudonyms.json`:

```json
{
  "version": 1,
  "key": "<64 hex characters, random, made on first use>",
  "counters": {"학생": 3, "학교": 2},
  "entries": {"<HMAC-SHA256 hex of kind + ':' + normalized value>": "학생03"}
}
```

- The digest uses the table's own key, so the file holds no names, schools or
  contact details.
- Reading and changing the table happen under an exclusive `flock` on
  `pseudonyms.lock`. A change is written to a temporary file in the same
  directory with mode `0600`, flushed, and renamed over the table; a failed or
  interrupted write leaves the previous table and removes its temporary file.
- The table is written only when a new identifier appears.
- A change that would make the file larger than 1 MiB fails the call with
  `backend_not_configured` naming the table, and the table stays as it was.

## Restoration

The judge keeps, for the one call, a map from each changed question key,
option label and level-description string back to the agent's original. After
the adapter validates the answers, each answer's question key, its `choice`,
the keys of its `probabilities` and the values of its `legend` are mapped
back. Numbers and fixed type names are untouched. The result the tool receives
therefore uses only the agent's own text.

## What never leaves the process

Names, pseudonyms, the roster path's contents, table entries and the table key
never appear in records, logs, error messages or reports. Error details are
limited to the configuration paths in [configuration.md](configuration.md).

## Error types

| Error type | Message | Cause |
| --- | --- | --- |
| `backend_not_configured` | feature 005's | A configuration, roster or table problem, or the module or `phonenumbers` missing; the detail names the path. |
| `pseudonym_conflict` | Two keys or labels become the same after pseudonymization; make them differ by more than a name. | The conflict above. |

`pseudonym_conflict` is new in `backfire/failures.py`; the operator guide's
troubleshooting table gains its row.
