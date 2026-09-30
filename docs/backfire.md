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
student, guardian and school names and contact details with pseudonyms
([Work plugin](#work-plugin)).

## Run it

Backfire runs straight from the repository and is never installed. Prepare
the environment once from the repository root:

```sh
npm run backfire:install
```

Both plugins declare the `backfire` stdio server in their `mcp.json` and
start it from the repository's package, the work plugin with `--education`:

```sh
uv --directory "${PLUGIN_ROOT}/../../packages/backfire" run --frozen --offline --no-sync backfire serve-mcp
uv --directory "${PLUGIN_ROOT}/../../packages/backfire" run --frozen --offline --no-sync backfire serve-mcp --education
```

Serving uses the prepared environment and does not sync packages. The path
reaches `packages/backfire` only while a client loads the plugin from the
repository checkout, as Claude Code does with `--plugin-dir`; a client that
copies the plugin elsewhere, such as a local marketplace install, cannot
start it.

## Select a provider

The shipped configuration is `packages/backfire/src/backfire/config.toml`
for the code plugin, which selects `hive`, and
`packages/backfire/src/backfire_education/config.toml` for the work plugin,
which selects `education`. Both profiles send judgments to the
OpenAI-compatible API at Hive and the `deepseek-ai/deepseek-v4.1-flash`
model through system-one-adapter, with JSON-object output, up to 32,768
completion tokens and medium reasoning effort. The optional operator file
is `$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml` (`~/.config`
when `XDG_CONFIG_HOME` is unset); both plugins read it. It uses
`provider = "<name>"` to select a profile, and a `[providers.<name>]` table
adds a profile or replaces the shipped one of that name. The selection is
read at the server's first judgment; restart the client session after
changing it.

A profile is one of two kinds:

| Field | Meaning |
| --- | --- |
| `api` | `openai` for a general model through system-one-adapter, as `hive` is; `jev` for a Jev provider |
| `jev_provider` | For `jev`: `typesafe`, `openrouter`, `cloudflare`, `compatible` or `vercel` |
| `base_url` | The endpoint; required for `openai`, `compatible` and `vercel`, optional for `typesafe` |
| `model` | The model; required for `openai` |
| `account_id` | For `cloudflare`: the Cloudflare account |
| `request` | For `openai`: extra request fields sent with every request |
| `credential` | The variable that holds the key in the key file |
| `credential_file` | Optional path of the key file; the default is `<profile>.env` beside the operator file |
| `retry` | Optional table of PyModel retry policy fields for this profile's provider |

A Jev profile uses PyModel's own provider of that name; `vercel` uses
backfire's Vercel AI Gateway provider, ported from jkudish's
jev-agent-tools 0.1.2 because PyModel does not support Vercel. The code
plugin ships unselected `vercel` and `openrouter` profiles; select one with
`provider = "vercel"` or `provider = "openrouter"` in the operator file. PyModel's own provider
environment variables, such as `JEV_PROVIDER` or `TYPESAFE_API_KEY`, do not
choose backfire's provider.

## Set the credential

The key file has one `<variable>=<key>` line, must be a regular file owned
by the operator with mode `0600`, and is read when the server's provider is
created. Provider keys live in one shared folder,
`~/.config/verbose-broccoli/providers/` (mode `0700`), with one file per
provider that every plugin uses. The shipped `hive` and `education` profiles
read `HIVE_API_KEY` from `providers/hive.env`, the shipped `vercel` profile
reads `AI_GATEWAY_API_KEY` from `providers/vercel.env`, and the shipped
`openrouter` profile reads `OPENROUTER_API_KEY` from
`providers/openrouter.env`. They name the
files relative to the operator file's folder (`../providers/<provider>.env`),
so the path follows `XDG_CONFIG_HOME`. An operator profile without
`credential_file` still reads `<profile>.env` beside the operator file. Keep keys out of `config.toml`, plugin files and client
environment entries.

## Work plugin

`serve-mcp --education` selects the education profile and pseudonymizes
every judgment, whichever profile kind the operator selects: the tool's
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
the list exported from EduOK. It needs a header row with a `name` column; the
optional `school` and `guardians` columns add schools and guardian names, with
several guardians separated by `;`. Other columns, such as a grade, are
ignored. Then name the file, with an absolute path, in
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml`:

```toml
roster = "/absolute/path/to/roster.csv"
```

Backfire reads the roster at every judgment and keeps no copy; edits apply to
the next judgment.

### What is replaced

| Found in the text | Pseudonym |
| --- | --- |
| A roster student's full name, also with particles (`가라온은`) | `학생03` |
| That student's given name alone (`라온이가`), derived from the full name | the same `학생03` |
| A given name several roster students share | its own `학생NN` |
| A roster guardian name | `보호자01` |
| A roster school | `학교02` |
| A phone number, such as `010-1234-5678` or `+82 10-1234-5678` | `연락처01` |
| An email address | `이메일01` |

A given name is the roster name without its surname: the first syllable, or
the first two when the name has at least four syllables and starts with 남궁,
황보, 제갈, 선우, 서문, 독고 or 사공. Given names are derived only from
all-Hangul names of at least three syllables, and only when they have at least
two syllables. Scores, dates,
grades, observations and other learning content are sent as is.

The work plugin cannot detect names, schools or guardians missing from the
roster, nicknames, one-syllable given names, given names of roster names that
are not all Hangul or shorter than three syllables, shortened school names such as
`별빛고` for `가상별빛고`, addresses, or Hangul written in decomposed form
(NFD), as some file names and PDF copies are. They reach the provider as
written; add them to the roster or leave them out of tool inputs. A student removed
from the roster is no longer detected. Ordinary words that equal a roster
value, such as a given name inside another word, are replaced too, which can
cost some judgment quality.

### Mapping table

Pseudonyms stay the same across calls, sessions and restarts because of the
mapping table `$XDG_DATA_HOME/verbose-broccoli/backfire/pseudonyms.json`
(`~/.local/share` when `XDG_DATA_HOME` is unset). It holds a random key, a
counter per pseudonym kind and keyed digests of the replaced values, never the
names or contact details themselves. It has mode `0600`, a lock file beside
it, and a 1 MiB limit. Deleting it restarts the numbering: calls stay
correct, but new pseudonyms no longer match earlier ones.

A work plugin judgment fails before anything is sent when `education.toml`,
the roster or the mapping table cannot be used (`backend_not_configured` with
the path), or when two keys or labels of one request would become the same
after replacement (`pseudonym_conflict`).

## Requests and data

For each judgment, a PyModel tool turns its input into `state` and
`questions`, and the selected provider sends them: for a general-model
profile, system-one-adapter builds the model request; for a Jev profile,
the provider sends them to the Jev endpoint. The request includes the
question text and any supplied claims, evidence, patches, test output,
source excerpts or other text used by that tool, and the key goes in the
HTTP `Authorization` header. Never send secrets or credentials. Never send
private personal records such as student data to the code plugin, which
replaces nothing; use the work plugin for them.

PyModel retries a failed attempt on HTTP 408, 429 and 5xx, and on a timed
out or dropped connection. Its default policy allows 3 attempts of 30
seconds each within 90 seconds; a profile's optional `retry` table sets
PyModel's policy fields instead (`max_attempts`, `per_attempt_timeout`,
`budget`, the backoff fields and `statuses`). The shipped Hive and
education profiles set `per_attempt_timeout = 110` and `budget = 118`,
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
retries ran out, with keys redacted. Backfire adds two of its own:

| Error | Cause and action |
| --- | --- |
| `backend_not_configured` | The configuration, the selected profile, its key file or a Jev provider name is missing or invalid. Check the file or profile named in the message, and the key file's owner and `0600` mode. |
| `pseudonym_conflict` | Two keys or labels of one request become the same after pseudonymization in the work plugin. Make them differ by more than a name. |
