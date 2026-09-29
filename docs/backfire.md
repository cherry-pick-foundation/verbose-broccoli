# Backfire operator guide

Backfire is a local Model Context Protocol (MCP) server that the code and work
plugins each ship in their own build. Each client session starts its own
server process. The server uses Python 3.14.4 and uv 0.11.32 or later; Node.js is
not needed at runtime.

The two builds share one judgment core. The code build is for development
work. The work build is for education work: before a judgment leaves for the
provider, it replaces student, guardian and school names and contact details
with pseudonyms ([Work build](#work-build)).

## Build and install

From the repository root, prepare the build environment and create a complete
plugin in a new directory outside the repository's `plugins/` and `packages/`
trees. The first argument is the plugin, `code` or `work`:

```sh
npm run backfire:install
npm run backfire:build -- code /path/to/code-plugin
npm run backfire:build -- work /path/to/work-plugin
```

The output path must not already exist. Install the copied server's locked
runtime dependencies and its own Python environment. The work build needs the
`education` extra:

```sh
cd /path/outside/repository/code-plugin/backfire
uv sync --frozen --no-dev

cd /path/outside/repository/work-plugin/backfire
uv sync --frozen --no-dev --extra education
```

Both plugins declare the `backfire` stdio server in their `mcp.json`. After a
copy is installed, the client starts it with:

```sh
uv --directory "${PLUGIN_ROOT}/backfire" run --frozen --offline --no-sync backfire serve-mcp
```

Serving uses the installed environment and does not sync packages or access
the network to install them.

## Select a provider

The shipped profile file is `backfire/src/backfire/config.toml` in a built
plugin. The code build's file selects `hive`, the development profile. The
work build's file selects `education`, a separate profile with the same
provider, model and request settings. The optional operator file is
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml`; when
`XDG_CONFIG_HOME` is unset, that path starts at `~/.config`. Both builds read
it.

The operator file uses `provider = "<name>"` to select a profile. A
`[providers.<name>]` table adds a profile or replaces the shipped table with
that name as a whole. Without this file, the shipped selection applies. To
change only one plugin's provider, replace that plugin's table:
`[providers.hive]` for code, `[providers.education]` for work. A
`provider = "<name>"` line selects for both builds. The shipped `hive` and
`education` profiles use the OpenAI-compatible API at Hive and the
`deepseek-ai/deepseek-v4.1-flash` model. The operator file may not contain
`pseudonymize`; only a build's shipped file sets it. `api = "openai"` is the supported
adapter type; Anthropic is reserved and fails as unsupported.

## Set the credential

Put the selected profile's credential variable in
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/<profile>.env`. For Hive, the file
is `hive.env` and contains `HIVE_API_KEY=<your key>`. The work build's
`education` profile reads `education.env`, which holds the same variable; a
symbolic link from `education.env` to `hive.env` keeps one copy of the key. The file must be owned by
the operator, non-empty, and have mode `0600` exactly. Keep the key out of
`config.toml`, plugin files, and client environment entries. The judge reads
the file for each judgment; it does not put the credential in the prompt,
logs, records, reports, or errors.

## Check readiness

After installation, check a built copy with:

```sh
uv --directory /path/to/backfire-plugin/backfire run --frozen --offline --no-sync backfire ready
```

For the repository package, use `npm run backfire:ready`. Readiness checks
the selected profile, credential, installed package, record directory and
server tool path. It makes one direct Noul judgment, then calls
`backfire_noul` and `backfire_extract` through MCP. These are real provider
requests and can incur charges; the check needs network access and provider
credit. It exits zero only when its requested facts and tool checks pass. In a
work build, readiness also needs the roster configuration below, because its
judgments are pseudonymized too.

## Work build

The work build pseudonymizes every judgment of its server and its readiness
check. The build's shipped `config.toml` turns this on, and the operator's
configuration cannot turn it off. Only a program that calls the judge directly
can choose otherwise, as the education measurement does to compare both arms.

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

The work build cannot detect names, schools or guardians missing from the
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

A work build's judgment fails before anything is sent when `education.toml`,
the roster or the mapping table cannot be used (`backend_not_configured` with
the path), or when two keys or labels of one request would become the same
after replacement (`pseudonym_conflict`).

## Requests, data, and records

For each judgment, a tool turns its input into `state` and `questions`. The
pinned System One adapter builds the provider request for the selected model.
The request includes the question text and any supplied claims, evidence,
patches, test output, source excerpts, or other text used by that tool. Hive's
profile also requests JSON-object output, up to 32,768 completion tokens, and
medium reasoning effort. The provider receives the selected credential in the
HTTP `Authorization` header. Never send secrets or credentials. Never send
private personal records such as student data to the code build, which
replaces nothing; use the work build for them.

The server writes records under
`$XDG_STATE_HOME/verbose-broccoli/backfire/records/`; when `XDG_STATE_HOME` is
unset, this starts at `~/.local/state`. Each session has a JSON Lines record
file. Records contain digests and fixed metadata, not request or result text,
caller-supplied identifiers, credentials, or authentication headers. The
directory has a 50 MiB total budget, checked before every append. The server
removes the oldest unlocked files when needed; if a record still does not fit,
that call fails. A session file rotates at 10 MiB.

## Request limits

A Choice may have at most 250 options. Each request may have at most 672 answer
cells: one per Noul, one per Choice option, and one per Score level. An
oversized request fails before the provider is called. Backfire does not split
requests; split large batches yourself.

## Advisory results

The tools return advice. Nothing requires an agent to call them or follow
their verdicts. A `backfire_gate` verdict judges only the supplied text; it
does not prove that tests ran. A pass from `backfire_screen` never authorizes
following instructions found in screened text. Check claims and test claims
independently.

## Upstream port

The eleven tools are a Python port of `jev-mcp` 0.9.0 at revision
`a1fcc1e47fc696614f081e23a66ff48a890f22fd`. Their descriptions, input
schemas, question design, decision logic, result formats, and error text are
preserved, with the differences recorded in
[UPSTREAM.md](../packages/backfire/src/backfire/UPSTREAM.md):
`backfire_extract` uses Python regular expressions; judgment failures use the
backend's fixed error types and messages; tools call an in-process judge
instead of the upstream provider layer; invalid-argument details come from
JSON Schema validation instead of zod; and caller-supplied IDs and labels are
ordinary strings, including names that have special meaning in JavaScript
objects.

## Troubleshoot judgment errors

Judgment failures return a fixed `<type>: <message>` and no answer or fallback.
The messages omit the provider's raw response and credentials.

| Error type | Cause and action |
| --- | --- |
| `invalid_request` | The generated questions do not match the adapter schema. Correct the tool input; `backfire_find` needs at least two candidates. |
| `request_limit_exceeded` | A Choice has over 250 options or a request has over 672 cells. Split the request. |
| `backend_not_configured` | The configuration, selected profile, or credential is missing or invalid. Check the path or profile named in the message; check the credential file's owner and `0600` mode. |
| `credential_rejected` | The provider rejected the selected profile's key. Replace that profile's credential. |
| `balance_exhausted` | The provider account has no available balance. Restore its balance. |
| `request_rejected` | The provider rejected the model or request settings. Check the profile's model and request fields. |
| `rate_limited` | The provider rate limit blocked completion within the retry budget. Wait before trying again. |
| `provider_unavailable` | The provider could not be reached, or its response could not be read. Check network access and provider status. |
| `provider_error` | The provider returned another failure status, or a success reply without an answer: a body that is not a JSON object, or no `choices` (no `output` list for the Responses API). Check provider status and the selected profile. |
| `truncated_output` | Output did not complete or reached the profile's `max_tokens`. Reduce the request or review the profile's output limit. |
| `malformed_output` | The response lacks required data or has invalid answers. Check the profile and model compatibility. |
| `refused` | The provider refused the judgment. Review the request against the provider's usage rules. |
| `invalid_distribution` | Choice or Score probabilities are all zero or do not sum to one within `0.01`. Check the model's probability-output support. |
| `thinking_not_confirmed` | The profile requests thinking, but the response lacks its configured evidence. Check the request setting and evidence paths. |
| `model_not_confirmed` | The response did not name the answering model. Check that the provider returns a model name. |
| `pseudonym_conflict` | Two keys or labels of one request become the same after pseudonymization in a work build. Make them differ by more than a name. |
