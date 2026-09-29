# Provider Profile Contract

A provider profile holds only what is specific to one provider (FR-019).
Protocol handling stays with the reused libraries and is not restated here:
the System One adapter's provider class for the profile's `api` builds each
request and reads each response, including its finish-reason check, and the
TypeSafe SDK maps standard HTTP statuses to its error classes, which the
single retry policy uses. The package's code names no provider, and a
provider whose departures from the standard behavior a profile can state
needs only a new profile and its selection, not a code change. Every profile
lives in a `config.toml` as one `[providers.<name>]` table; there is no file
per provider.

## Location and selection

- Shipped configuration: `packages/backfire/src/backfire/config.toml`,
  copied into a built code plugin with the package. It holds
  `provider = "hive"`, the user-selected backend of FR-002, and one
  `[providers.<name>]` table per shipped provider. The code reads the default
  selection only from this file.
- Operator configuration: `$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml`,
  optional, with the same shape. Its `provider`, when present, replaces the
  shipped selection, and each of its `[providers.<name>]` tables adds a provider
  or replaces the shipped table of that name as a whole; tables are never merged
  key by key. Without the file, the shipped configuration applies unchanged.
- Either file with invalid TOML, a top-level key other than `provider` and
  `providers`, or a selection that names no configured provider fails each
  judgment with `backend_not_configured`, whose message names the path.
- Credential: `$XDG_CONFIG_HOME/verbose-broccoli/backfire/<name>.env`, holding
  `<credential>=<key>` for the selected table's `credential` name, under the
  rules of [configuration.md](configuration.md). Keys never go into
  `config.toml`.

## Format

```toml
provider = "hive"

[providers.hive]
api = "openai"
base_url = "https://api-cdn.thehive.ai/api/v3"
model = "deepseek-ai/deepseek-v4.1-flash"
credential = "HIVE_API_KEY"
rate_limit_per_second = 5

# Added to every request, beyond what the adapter sends. Hive cuts output at
# 128 tokens without max_tokens and still reports finish_reason "stop".
# Medium reasoning effort measured best on 2026-09-27 (research.md).
request = { max_tokens = 32768, response_format = { type = "json_object" }, reasoning_effort = "medium" }

# Where Hive shows that thinking ran.
thinking = { requested = "on", content_path = "reasoning_content", token_path = "reasoning_tokens" }

# Only statuses whose meaning at Hive differs from the standard one.
statuses = { 405 = "balance_exhausted" }
```

A path is a dot-separated list of object keys, such as
`completion_tokens_details.reasoning_tokens`; a missing key means the value is
absent. An absent optional value is an omitted key, since TOML has no null.

| Key | Rules |
| --- | --- |
| `<name>` | The table key: lowercase letters, digits and `-`. It names the credential file. |
| `api` | The adapter provider class that handles the protocol. `openai` selects `AsyncOpenAIProvider`, which uses Chat Completions for hosts other than `api.openai.com`. `anthropic` is reserved for `AsyncAnthropicProvider` and fails each judgment with `backend_not_configured` and a message that it is not supported yet. |
| `base_url` | The API root passed to the provider class. |
| `model` | The exact model identifier sent with every request and pinned under FR-012. |
| `credential` | The variable name that holds the key in `<name>.env`. |
| `rate_limit_per_second` | Optional. The request rate per account that the provider documents. The judge does not throttle to it; the single retry layer handles rate-limit answers. The gate 2 probe sends a burst above it, and when it is absent skips the burst and reports it as not applicable, with that reason. |
| `request` | Optional. Fields added to every request beyond those the adapter sends; it MUST NOT set `model`, `messages`, `stream` or `n`. When it sets `max_tokens`, completion tokens that reach that value give `truncated_output`, for providers that report a normal finish when they cut output. |
| `thinking.requested` | `on` or `off`, as readiness reports it. A profile that requests `off` is an explicit choice, never a fallback for a profile that requests `on` (FR-002). |
| `thinking.content_path` | Optional. A path in the response message whose non-empty string shows that thinking ran. |
| `thinking.token_path` | Optional. A path in the response's `usage` whose positive integer shows that thinking ran. When `requested` is `on`, at least one of the two paths is set, and a response that shows neither fails with `thinking_not_confirmed`. When `requested` is `off`, neither is set and no thinking evidence is checked. |
| `statuses` | Optional. Maps an HTTP error status (400 to 599) whose meaning at this provider differs from the standard one to `credential_rejected`, `balance_exhausted`, `request_rejected` or `rate_limited`. Every other status keeps the meaning of the SDK's error class: 400 is `request_rejected`, 401 is `credential_rejected`, 429 is `rate_limited`, and any other status is `provider_error` ([judgment.md](judgment.md#errors)). Of these types, `rate_limited` is retried, and so is `provider_error` for a 5xx status; mapping a 5xx status to another type stops its retries ([judgment.md](judgment.md#retries-and-time)). |

A selected table with a missing or unknown key, or a key that breaks these
rules, fails each judgment with `backend_not_configured`, naming the table and
the file it came from.

Known limit: a provider that answers one status for two causes cannot be told
apart by status alone. OpenAI's own API, for example, answers 429 both for
"Rate limit reached" and for "Credit balance exhausted". Supporting such a
provider needs a small code change when one is selected
([research.md](../research.md#provider-profiles--2026-09-27)).

## Shipped profile

`hive` is the only shipped profile, and the shipped `provider` selects it. Hive
documents only an OpenAI-compatible Chat Completions API. Its values come from
[research.md](../research.md#hive-request-behavior--2026-09-26): the 128-token
cutoff without `max_tokens` while the finish reason still reads `stop`, the
rejected strict JSON schema, the medium reasoning effort and its thinking
evidence ("Judgment quality probes" in research.md), 405 for an
exhausted balance while 400, 401 and 429 keep their standard meanings, and the
documented default of 5 requests per second.

## Adding a profile

A new profile, a new `[providers.<name>]` table in either `config.toml`,
records the evidence for its values in `research.md`, like the
Hive section, and passes the probe of gate 2, readiness and the acceptance sets
before it is selected; changing the selected profile, endpoint or model is an
FR-012 upgrade.

## Test-only override

`BACKFIRE_TEST_PROVIDER_BASE_URL` replaces the selected profile's `base_url`,
so tests can point provider calls at a scripted provider. Readiness reports it
whenever it is set.
