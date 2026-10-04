# Backfire operator guide

Backfire runs PyModel's [jev-judge-mcp](https://github.com/PyModel/jev-judge-mcp)
0.6.0 Model Context Protocol (MCP) server with verbose-broccoli's own model
providers. jev-judge-mcp is a Python implementation of jkudish's jev-mcp,
installed from PyPI as a pinned dependency; backfire adds only the glue in
`packages/backfire/src/backfire/`. The server reports itself as `jev-mcp`
and offers PyModel's tools (`jev_verify`, `jev_screen`, `jev_find`,
`jev_classify`, `jev_decide`, `jev_rerank`, `jev_compare`, `jev_extract`,
`jev_review`, `jev_gate` and `jev_score`) plus `jev_noul`, jev-mcp 0.9.0's
Noul tool. Each client session starts its own server process. It needs
Python 3.14.4 and uv 0.11.32 or later.

The code plugin uses it for development work. The work plugin uses it for
education work: before a judgment leaves for the provider, it replaces
student, guardian and school names, numbers, regions and other identifiers
with English stand-ins ([Work plugin](#work-plugin)). The chat plugin's
credit-offer search calls backfire's provider order as a library, without the
server (`packages/credit-offers`). Everything sent to a provider is English:
both modes refuse a request that holds Hangul
([Refusals](#refusals)).

## Run it

Backfire runs straight from the repository and is never installed. Prepare
the environment once from the repository root:

```sh
npm run backfire:install
```

The code plugin declares `backfire-code`; the work plugin declares
`backfire-education`. Their canonical `mcp.json` declarations start the
repository's package, with the work plugin adding `--education`:

```sh
uv --directory "${PLUGIN_ROOT}/../../packages/backfire" run --frozen --offline --no-sync backfire serve-mcp
uv --directory "${PLUGIN_ROOT}/../../packages/backfire" run --frozen --offline --no-sync backfire serve-mcp --education
```

Serving uses the prepared environment and does not sync packages.
`npm run plugins:prepare` refreshes live checkout skill links and project
MCP configuration for Codex and Claude Code. Optional copied client packages
use `npm run plugins:distribute` separately; they still need their source
checkout and its installed dependencies. Use a permanent checkout such as
`develop` for those packages.
See [Sharing and distribution](architecture.md#sharing-and-distribution)
for local discovery and copied client loading commands.
The live Codex route adds a generated block to tracked `.codex/config.toml`.
Before a normal git-flow finish, both develop and feature worktrees must be
clean: run `npm run plugins:clean-codex` separately in each to remove only its
exact receipt-owned block, preserving other edits. After integration, prepare
the final develop checkout again and load a fresh client session before checking MCP metadata readiness. The
[receipt and finish procedure](architecture.md#live-checkout-discovery) gives
the ownership checks; skill discovery alone does not establish MCP readiness.

## Select a provider

Both plugins and the credit-offer search read one shipped configuration,
`packages/backfire/src/backfire/config.toml`. It lists provider profiles in
an `order`, `openrouter` then `hive`, and backfire uses the first profile in
it that is not known to be out of credit
([Credit and switching](#credit-and-switching)). The work
plugin differs only in pseudonymization and the response cache
([Work plugin](#work-plugin)).

The `openrouter` profile sends judgments to TypeSafe's Jev model through
PyModel's OpenRouter provider. The `hive` profile sends them to the
OpenAI-compatible API at Hive and the `deepseek-ai/deepseek-v4.1-flash`
model through system-one-adapter, with JSON-object output, up to 32,768
completion tokens and medium reasoning effort. Answers therefore differ by
profile; each result's `provider` field names the profile that answered.
The optional operator file is
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml` (`~/.config` when
`XDG_CONFIG_HOME` is unset); both plugins read it. Its `order = [...]`
replaces the shipped order for both plugins, and a `[providers.<name>]`
table adds a profile or replaces the shipped one of that name. The order is
read at the server's first judgment; restart the client session after
changing it.

A profile is one of two kinds:

| Field | Meaning |
| --- | --- |
| `api` | `openai` for a general model through system-one-adapter, as `hive` is; `jev` for a Jev provider |
| `jev_provider` | For `jev`: `typesafe`, `openrouter`, `cloudflare` or `compatible` |
| `base_url` | The endpoint; required for `openai` and `compatible`, optional for `typesafe` |
| `model` | The model; required for `openai` |
| `account_id` | For `cloudflare`: the Cloudflare account |
| `request` | For `openai`: extra request fields sent with every request |
| `credential` | The variable that holds the key in the key file |
| `credential_file` | Optional path of the key file; the default is `<profile>.env` beside the operator file |
| `retry` | Optional table of PyModel retry policy fields for this profile's provider |
| `codexbar` | Optional CodexBar provider ID; backfire reads the provider's credit through it before using the profile |
| `insufficient_balance` | Optional HTTP statuses that mean the provider's balance is used up; the default is `[402]`, and the `hive` profile sets `[405]`, the status Hive documents for an exhausted balance |

A Jev profile uses PyModel's own provider of that name. PyModel's own
provider environment variables, such as `JEV_PROVIDER` or
`TYPESAFE_API_KEY`, do not choose backfire's provider.

## Credit and switching

Before backfire first uses a profile that names a `codexbar` provider, it
runs the command-line tool of [CodexBar](https://github.com/steipete/CodexBar)
(MIT, used unchanged): `codexbar usage --provider <id> --format json`, for
that one provider. The call's environment holds only `PATH`, `HOME` and the
profile's key in the variable named by `credential`, so no other key or
setting reaches CodexBar, and backfire uses no CodexBar configuration file.
Backfire skips the profile when CodexBar reports a balance of zero or less
or a limit at 100% used, and logs the skip; it never logs CodexBar's output,
which can name the account. The shipped `openrouter` profile names a CodexBar
provider; CodexBar reads no balance for Hive. If `codexbar` is not on the
server's `PATH`, fails, or takes longer than 30 seconds, backfire uses the
profile and logs that its credit is unknown. Credit is read once per profile
in a server session: before the profile's first judgment, which may follow a
switch.

When the provider in use answers an HTTP status in its profile's
`insufficient_balance`, backfire sends the same judgment to the next usable
profile in the order and keeps that profile for the rest of the session. The
log records each switch. Other errors never switch, and backfire returns to
the top of the order only when the client session restarts. In the work
plugin every profile receives only text with its identifiers replaced; the
user accepted on 2026-09-30 that it may reach OpenRouter and TypeSafe.

`serve-mcp --profile <name>` keeps only that profile of the order, so a
session meant for one provider fails with `no_credit` instead of switching;
an unknown name is `backend_not_configured`. The code plugin's model choice
starts backfire with `--profile openrouter`, so its judgments stay on Jev.

## Set the credential

The key file has one `<variable>=<key>` line, must be a regular file owned
by the operator with mode `0600`, and is read when backfire first uses its
profile. Provider keys live in one shared folder,
`$XDG_CONFIG_HOME/verbose-broccoli/providers/` (by default
`~/.config/verbose-broccoli/providers/`, mode `0700`), with one file per
provider that every plugin uses. The shipped `openrouter` profile reads
`OPENROUTER_API_KEY` from `providers/openrouter.env`, and the shipped `hive`
profile reads `HIVE_API_KEY` from `providers/hive.env`. They name the files
relative to the operator file's folder (`../providers/<provider>.env`), so
the path follows `XDG_CONFIG_HOME`. An operator profile without
`credential_file` still reads `<profile>.env` beside the operator file. Keep
keys out of `config.toml`, plugin files and client environment entries.

### Refresh the key files from Bitwarden Secrets Manager

`npm run secrets:refresh` refreshes key files from several Bitwarden Secrets
Manager sources ([spec](../specs/052-secrets-refresh-sources/spec.md)). It reuses
`bws`, pinned by mise and reviewed in
[`security/bws-2.1.0.md`](../specs/041-provider-secrets/security/bws-2.1.0.md).
The operator file remains `<config>/verbose-broccoli/secrets.json`, where
`<config>` is absolute `XDG_CONFIG_HOME`, otherwise `~/.config`:

```json
{
  "sources": {
    "org-a": {"token_file": "<path-to-token-a>", "project": "<org-a-project-id>"}
  },
  "files": {
    "hive.env": {"source": "org-a", "variables": {"HIVE_API_KEY": "HIVE_API_KEY"}}
  }
}
```

Each source names an absolute token-file path and a project, plus an optional
HTTPS `server` (default `https://vault.bitwarden.com`). All token files must be
regular files you own, mode `0600`, without symlink components, and hold one
non-empty `BWS_ACCESS_TOKEN=` line. Every token is checked before any bws call;
every configured source is then listed once. The child receives only `PATH`,
`HOME`, its token and an explicit `BWS_SERVER_URL`, with umask `077`. Tokens
never enter arguments; child stderr and exception details are suppressed.

A plain target name resolves to `providers/`. Variable targets also allow
only `~/.omp/agent/.env`, `<config>/ocis-mcp/client.env` and
`<config>/ocis-mcp/cloudflare-client.env`, written as absolute JSON keys.
Mappings can alias one secret into several variables or files. Refresh changes
mapped assignments in place and preserves every unmapped byte, including
comments and identifiers; missing variables append in configured order.
Duplicate mapped assignments refuse the run. The optional `content` target is
only `<config>/gws/client_secret.json`, whose non-empty secret is written
exactly, including line breaks. Token/operator aliases, symlinks, unsafe
parents and other paths refuse.

All requested values and targets are validated before writing; all private
temporary files are prepared before renaming. Written files are mode `0600`,
owned by you. Configuration, token, fetch or validation failures leave target
bytes and modes unchanged. There is no multi-file rollback after renames begin.
Success prints target names/paths and counts only; failure prints a generic
message. Backfire's readers are unchanged and read the new key when first
using a profile. Do not run `bws secret list` or `bws secret get` in a terminal:
they print values. The old single-project configuration is unsupported; see
[the placeholder quickstart](../specs/052-secrets-refresh-sources/quickstart.md)
and [operator contract](../specs/052-secrets-refresh-sources/contracts/operator-config.md).

## Work plugin

`serve-mcp --education` uses the shared order and replaces identifiers in
every judgment once, whichever profile answers: the tool's
input, the question keys, and every text in the questions (wording, choice
labels and their descriptions, Noul criteria and rubric levels). It also
turns off PyModel's optional response cache (`JEV_MCP_CACHE`), so real names
are never written to disk. The operator's configuration cannot turn either
off.

### Before sending real student records

Turn off model training in the Claude and ChatGPT account settings. Backfire's
pseudonymization covers only what backfire sends to its provider; the agents
themselves read student records when asked.

### Roster

Save the student list as a UTF-8 CSV file anywhere on this machine, for example
the list exported from EduOK. It needs a header row with a `name` column. These
columns are optional:

| Column | Holds |
| --- | --- |
| `school` | The school's name, or its domain ID such as `byeolbit-h` |
| `guardians` | Guardian names, separated by `;` |
| `id` | The student's EduOK student number |
| `romanized` | The romanized name, written together with the surname first: customary surname spelling and Revised Romanization of the given name, such as `Kim Gildong` |

Other columns, such as a grade, are ignored. Then name the file, with an absolute path, in
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml`:

```toml
roster = "/absolute/path/to/roster.csv"
```

Backfire reads the roster at every judgment and keeps no copy; edits apply to
the next judgment.

### What is replaced

Stand-ins are English, so a provider never receives Hangul.

| Found in the text | Stand-in |
| --- | --- |
| A roster student's Korean name, also with particles (`가라온은`) | `Student 03` |
| That student's EduOK number from `id`, as a whole number, also when it is a JSON number or key (`7700101`, `7700101.0`) | the same `Student 03` |
| That student's romanized name in any case, with or without hyphens or spaces (any number, non-breaking ones included) inside the given name, surname first or last (`Kim Gildong`, `KIM GIL-DONG`, `gildong kim`) | the same `Student 03` |
| That student's given name alone, Korean (`라온이가`) or romanized (`Gildong`), derived from the full name | the same `Student 03` |
| A given name several roster students share | its own `Student NN` |
| A roster guardian name | `Guardian 01` |
| A roster school, and any lowercase token that ends in `-h`, `-m` or `-e`, such as `byeolbit-h` | `School 02` |
| A phone number, such as `010-1234-5678` or `+82 10-1234-5678` | `Phone 01` |
| An email address | `Email 01` |
| A province, city, county or district name, current or abolished, in Korean (`평택시`) or romanized (`Jongno-gu`, `Pyeongtaek`, `North Chungcheong`, `Chungbuk`), with a unit word after it such as `City` or `Province` | `Region 01` |
| A school year: `Grade 10`, `Grade: 10`, `Grade: 11th`, `Grades 10 and 11`, `Grades ten and eleven`, `Grade 10/11`, `Years 10 and 11`, `Grade ten`, `10th grade`, `tenth grade` (up to `twelfth`), `Year 11`, `year eleven` (spelled from `one` to `twelve`), `first-year high school student`, `fourth-year elementary school student` (first to sixth year), `high school sophomore`, `고1`, `중2`, `초6`, `1학년`, `예비 고1`; one stand-in per grade, with no coarse band | `Cohort 01` |
| After `born`, `birthday`, `birth date`, `birth year`, `date of birth`, `DOB`, `생년월일`, `생일` or `출생`: the rest of its clause, up to a sentence end, a semicolon, a line break or a table cell end (`|`), when it holds a digit, a month name (lowercase too, except `may`), a year in words or a Roman numeral year (`MMXIII`, `mmxiii`), so a birth date in any form is hidden: `born on June 17, [ 2012 ]`, `DOB: 17.VI.2012`, `born in nineteen ninety-eight`. Other text in that clause is hidden with it: `born on June 17, 2012, and 90 points` sends no score. Also forms such as `2009년생` | `Birth date 01` |
| The rest of a line or table cell after `address` or `주소`, and a run of romanized address parts, such as `Bijeon-ro 12`, `Ha-neul-ro 487`, `Solbit-ro 12-gil 487`, `Jungang-daero 45beon-gil 7`, `Seo-dong 123-4`, `101-dong 1203-ho` or `Jongno 1-ga`, with the building, lot or unit numbers (`487 Solbit-ro`, `Solbit-ro, 487`, `101-1203`, `Apt #1203`, `building 101, unit 1203`, `(Apt 2317)`, `apt. no. 2317`, `103/2317`, `Unit 27B`), postal codes and region names before or after it; the whole run becomes one stand-in | `Address 01` |

Between a keyword and its value there may be spaces, punctuation (`:`, `=`,
`-`, `—`, `->`, quotation marks) and Markdown or table markup (`|`, `**`, `_`,
`~~`, backticks), in any order: `| DOB | 2011-04-23 |`, `**Grade:** 10` and
``Address: `487 Imaginary Street` `` are replaced. A birth clause may also
start on the next line after `born on` or a colon. When matching, dash-like and
zero-width characters count as hyphens, so `Na‑bit` (U+2011) matches `Na-bit`.

A column header can say the same for the cells below it: in a Markdown table
(the header row above its delimiter row) or a CSV or tab-separated block (its
first line), a header that names a school year, birth date, address or student
number makes each cell below it a stand-in of that kind, row by row until a
row without the separator; a quoted CSV cell keeps its commas and line breaks,
and an escaped pipe (`\|`) stays inside its Markdown cell; the header cells
that name columns are left as they are, while any other text in a header row
is scanned like the rest; in a school-year column only cells that read as a
school year, so `| Grade |` over `| 11 |` becomes a `Cohort` while `B+`
stays.

A field name can say what its value is. Everything inside a named field
becomes a stand-in: a string or a number, each item of a list, and each key and
value of an object inside it, at any depth:

- `DOB`, `date of birth`, `birth date`, `birthday`, `born`, `생년월일`, `생일` or
  `출생`: a birth date, whatever the value says;
- `address`, `home address` or `주소`: an address, whatever the value says;
- `grade`, `grade level`, `school year`, `year` or `학년`: a school year, when
  the value or key is a number from 1 to 12, an ordinal (`10th`, `tenth`), a
  number word (`ten`) or one of the school-year forms above; a field named
  inside it, such as `DOB`, keeps its own meaning.

Names match in any case, with a space, underscore or hyphen between words or
camel case (`dateOfBirth`), and may start with `student`, `child`, `pupil`,
`guardian`, `parent`, `home`, `current`, `mailing` or `street`. Other values of
a `year` or `grade` field, such as `2026` or `85`, and academic years (`학년도`)
stay; a `grade` of `5` is replaced even when it means a score. A key that is not
a string, such as the number `7700101` in a Python dictionary, is read as its
text.

A given name is the roster name without its surname: the first syllable, or
the first two when the name has at least four syllables and starts with 남궁,
황보, 제갈, 선우, 서문, 독고 or 사공. Given names are derived only from
all-Hangul names of at least three syllables, and only when they have at least
two syllables; the romanized given name is the `romanized` value without its
surname, and it is used only when the Korean name yields a given name. Scores,
lesson dates, observations and other learning content are sent as is, and so
are academic years such as `2026학년도` and `the 2026 school year`.

Region names come from the Ministry of the Interior and Safety's legal-district
code list, which is vendored unmodified in
`packages/backfire/vendor/legal-district-codes/` with a record of its source
and hashes. `npm run backfire:regions` turns it into
`packages/backfire/src/backfire_education/regions.json`, with romanized forms
from es-hangul 2.4.0, and `npm run verify` checks that the two match. es-hangul
adds a compound-word ㄴ to names such as `안양` (`Annyang`), so the list holds
the spelling without it (`Anyang`) too.

### Refusals

After the replacement, backfire scans the request again with every detector,
numbers and field names included and ignoring the stand-ins it inserted. If
anything is found, it sends nothing and fails with `identifier_remaining`.
A score or a lesson date after the end of a birth clause, as in
`born on June 17, 2012; 85/100` or `born on June 17, 2012. 85 points`, is sent.

The same error refuses a birth-date, address or student-number field whose
value was not replaced. Such a field is a key named for a birth date or an
address as above, or `student number`, `student ID`, `StudentNo`,
`EduOK number` or `학번`; or, in text, `DOB`, `date of birth`, `birth date`,
`birthday`, `address` (not `email address`), `생년월일`, `생일`, `주소` or a
student-number name followed by a colon, pipe or equals sign. The value in
text runs to the end of its line, table cell or sentence, or to a comma or
semicolon; in a Markdown table, a name in the header row applies to the cells
below it. A field passes when its value is empty, or holds a stand-in and no
digit. So `DOB: around Easter`, `Student ID: 7799999` for a number that the
roster lacks, and an `Address` column of English street names are refused,
while ordinary prose such as `the address of the lesson` or
`born in a small town` is not.
Student numbers themselves are replaced only when the roster lists them.

Both modes, with or without `--education`, then refuse a request that still
contains Hangul, composed or decomposed, in the tool input, the question keys or
any question text. It fails with `hangul_remaining` before any provider call.
In education mode this catches a name that the roster does not list. Translate
Korean material into English with Claude or ChatGPT before any backfire call.

Neither error, and no log, holds a matched value or any request text. Nor does
a provider failure in the work plugin: it is cut to the profile and the HTTP
status, such as `backfire profile 400`, or `backfire profile request failed`
when there is no status, because a provider's answer can quote the request. The
code plugin keeps PyModel's error text.

### Limits

Pattern detection cannot prove that a request is free of identifiers. The work
plugin does not detect:

- names, schools or guardians that the roster does not list and that are written
  in Latin letters, nicknames, and Latin spellings of a roster name that the
  `romanized` column does not give (a missing name in Hangul is refused, not
  sent);
- one-syllable given names, given names of roster names that are not all Hangul
  or shorter than three syllables, and a surname alone;
- school names in other forms, such as `별빛고` or `Byeolbit High School`, for a
  roster school `가상별빛고`;
- region spellings other than the generated ones, and romanizations that differ
  from the official one, such as `묵호` (es-hangul writes `Muko`, the official
  spelling is `Mukho`; es-hangul drops the `h` after `ㄱ`, `ㄷ` and `ㅂ`);
- addresses without an `address` keyword or field name or romanized address
  parts, such as a street name in English, romanized parts without their
  hyphen (`Solbitro`), building names in English words (`Solbit Apartment`),
  and a unit written letter first after an address (`Unit B27`);
- a keyword after its value (`2011-04-23 (DOB)`), and HTML markup between a
  keyword and its value;
- a difference between roster students who share a full name: they share one
  stand-in, and their EduOK numbers and romanized names map to it too.
- the part of a birth date after a clause end, as in `born on June 17; 2012`,
  `born on June 17 | 2012` or a year on the next line: a birth clause ends
  there.

They reach the provider as written; add roster names to the roster or leave the
text out of tool inputs. A student removed from the roster is no longer detected.
Ordinary words that equal a roster value, a region name or a given name are
replaced too, and so are school-year and address forms in other senses, such as
`year one of the project` or `the address of the lesson`, which can cost some
judgment quality. A birth clause with any number is hidden too, as in
`the idea was born in 3 lessons`.

### Mapping table

Pseudonyms stay the same across calls, sessions and restarts because of the
mapping table `$XDG_DATA_HOME/verbose-broccoli/backfire/pseudonyms.json`
(`~/.local/share` when `XDG_DATA_HOME` is unset). It holds a random key, a
counter per stand-in kind and keyed digests of the replaced values, never the
names or contact details themselves. It has mode `0600`, a lock file beside
it, and a 1 MiB limit. Deleting it restarts the numbering: calls stay
correct, but new stand-ins no longer match earlier ones. A table written
before the stand-ins were English holds the Korean prefixes (`학생03`); backfire
reads them as `Student 03` with the same numbers and stores the English form the
next time it saves.

A work plugin judgment fails before anything is sent when `education.toml`,
the roster or the mapping table cannot be used (`backend_not_configured` with
the path), or when two keys or labels of one request would become the same
after replacement (`pseudonym_conflict`).

## Requests and data

For each judgment, a PyModel tool turns its input into `state` and
`questions`, and the profile in use sends them: for a general-model
profile, system-one-adapter builds the model request; for a Jev profile,
the provider sends them to the Jev endpoint. The request includes the
question text and any supplied claims, evidence, patches, test output,
source excerpts or other text used by that tool, and the key goes in the
HTTP `Authorization` header. Never send secrets or credentials. Never send
private personal records such as student data to the code plugin, which
replaces nothing and refuses Hangul; use the work plugin for them, in English.

PyModel retries a failed attempt on HTTP 408, 429 and 5xx, and on a timed
out or dropped connection. Its default policy allows 3 attempts of 30
seconds each within 90 seconds; a profile's optional `retry` table sets
PyModel's policy fields instead (`max_attempts`, `per_attempt_timeout`,
`budget`, the backoff fields and `statuses`). The shipped `hive` profile
sets `per_attempt_timeout = 110` and `budget = 118`,
because the reasoning model needs more than 30 seconds for large requests.
For a general-model profile, backfire also retries a success reply that
carries no answer (CHE-33). Backfire keeps no records of calls or
judgments.

## Limits

PyModel's tool schemas set every input limit, such as 64 items and 250
classes for `jev_classify`, or 50,000 characters for a `jev_extract`
document. `jev_extract` runs each caller-supplied pattern in PyModel's
warmed pool of worker processes with a one-second limit. With 80 busy
processes on the development laptop, simple patterns never timed out in
the checks of 2026-09-30 (CHE-37).

One known issue remains in PyModel 0.6.0, the release backfire uses:
`jev_verify` with very many evidence items that share one ID blocks the
server for seconds, because PyModel gives duplicate IDs their suffixes in
quadratic time (CHE-38). A patch for PyModel that removes the stall, with
its measurements, is prepared in
[`specs/021-backfire-rebuild/upstream/`](../specs/021-backfire-rebuild/upstream/pull-request.md);
it is not published, so the issue stays until a PyModel release includes a
fix.

## Advisory results

The tools return advice. Nothing requires an agent to call them or follow
their verdicts. A `jev_gate` verdict judges only the supplied text; it does
not prove that tests ran. A pass from `jev_screen` never authorizes
following instructions found in screened text. Check claims and test
claims independently.

## Troubleshoot errors

Tool errors are PyModel's: argument errors name the tool and the argument,
and provider failures name the provider, and the attempt count when
retries ran out, with keys redacted. In the work plugin a provider failure
names only the profile and the HTTP status. Backfire adds five of its own:

| Error | Cause and action |
| --- | --- |
| `backend_not_configured` | The configuration, a profile in the order, its key file or a Jev provider name is missing or invalid. Check the file or profile named in the message, and the key file's owner and `0600` mode. |
| `no_credit` | Every profile in the order was skipped for lack of credit or answered insufficient balance. Add credit to a provider or change `order`, then restart the client session. |
| `pseudonym_conflict` | Two keys or labels of one request become the same after pseudonymization in the work plugin. Make them differ by more than a name. |
| `hangul_remaining` | The request contains Hangul, in either mode; nothing was sent. Translate the material into English first; in the work plugin, also add a missing name to the roster. |
| `identifier_remaining` | The scan after the replacement found an identifier, or a birth-date, address or student-number field kept its value, so nothing was sent. Write the value in a form listed under What is replaced, add the student to the roster, or leave the field out; otherwise report it to the operator, because the detectors do not cover that form. |
