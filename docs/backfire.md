# Backfire operator guide

Backfire is the code plugin's local Model Context Protocol (MCP) server. Each
client session starts its own server process. The server uses Python 3.14.4 and
uv 0.11.32 or later; Deno and Node are not needed at runtime.

## Build and install

From the repository root, prepare the build environment and create a complete
code plugin in a new directory outside the repository's `plugins/` and
`packages/` trees:

```sh
deno task backfire:install
deno task backfire:build -- /path/to/backfire-plugin
```

The output path must not already exist. Install the copied server's locked
runtime dependencies and its own Python environment:

```sh
cd /path/outside/repository/backfire-plugin/backfire
uv sync --frozen --no-dev
```

The code plugin declares the `backfire` stdio server in `plugins/code/mcp.json`.
After the copy is installed, the client starts it with:

```sh
uv --directory "${PLUGIN_ROOT}/backfire" run --frozen --offline --no-sync backfire serve-mcp
```

Serving uses the installed environment and does not sync packages or access
the network to install them.

## Select a provider

The shipped profile file is `backfire/src/backfire/config.toml` in a built
plugin. It selects `hive`, the only shipped profile. The optional operator
file is `$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml`; when
`XDG_CONFIG_HOME` is unset, that path starts at `~/.config`.

The operator file uses `provider = "<name>"` to select a profile. A
`[providers.<name>]` table adds a profile or replaces the shipped table with
that name as a whole. Without this file, the shipped selection applies. The
shipped Hive profile uses the OpenAI-compatible API at Hive and the
`deepseek-ai/deepseek-v4.1-flash` model. `api = "openai"` is the supported
adapter type; Anthropic is reserved and fails as unsupported.

## Set the credential

Put the selected profile's credential variable in
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/<profile>.env`. For Hive, the file
is `hive.env` and contains `HIVE_API_KEY=<your key>`. The file must be owned by
the operator, non-empty, and have mode `0600` exactly. Keep the key out of
`config.toml`, plugin files, and client environment entries. The judge reads
the file for each judgment; it does not put the credential in the prompt,
logs, records, reports, or errors.

## Check readiness

After installation, check a built copy with:

```sh
uv --directory /path/to/backfire-plugin/backfire run --frozen --offline --no-sync backfire ready
```

For the repository package, use `deno task backfire:ready`. Readiness checks
the selected profile, credential, installed package, record directory and
server tool path. It makes one direct Noul judgment, then calls
`backfire_noul` and `backfire_extract` through MCP. These are real provider
requests and can incur charges; the check needs network access and provider
credit. It exits zero only when its requested facts and tool checks pass.

## Requests, data, and records

For each judgment, a tool turns its input into `state` and `questions`. The
pinned System One adapter builds the provider request for the selected model.
The request includes the question text and any supplied claims, evidence,
patches, test output, source excerpts, or other text used by that tool. Hive's
profile also requests JSON-object output, up to 32,768 completion tokens, and
medium reasoning effort. The provider receives the selected credential in the
HTTP `Authorization` header. Do not send secrets, credentials, or private
personal records such as student data.

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
| `provider_error` | The provider returned another failure status. Check provider status and the selected profile. |
| `truncated_output` | Output did not complete or reached the profile's `max_tokens`. Reduce the request or review the profile's output limit. |
| `malformed_output` | The response lacks required data or has invalid answers. Check the profile and model compatibility. |
| `refused` | The provider refused the judgment. Review the request against the provider's usage rules. |
| `invalid_distribution` | Choice or Score probabilities are all zero or do not sum to one within `0.01`. Check the model's probability-output support. |
| `thinking_not_confirmed` | The profile requests thinking, but the response lacks its configured evidence. Check the request setting and evidence paths. |
| `model_not_confirmed` | The response did not name the answering model. Check that the provider returns a model name. |
