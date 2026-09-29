# Contract: Provider Seam

## Construction

The server builds the upstream `Runtime` as

```text
Runtime(
    Settings.model_construct(),          # upstream defaults only
    provider_factory=<returns backfire's JevProvider>,
    regex_executor=<backfire's regex-library executor>,
)
```

and one `Toolset(runtime, <registry>)` per server.

## Per-call context

Before a tool runs, the server sets a context variable with the call's
absolute deadline and the session's record file. The provider reads it; a
call without it (a test that uses the `Toolset` directly) uses a deadline of
118 seconds from the start of the judgment and no record file.

## `evaluate(state, questions, model, timeout)`

1. Convert `questions` with the upstream `questions_to_wire`.
2. Await `judge(state, wire_questions, deadline=..., record_file=...)`.
   `judge()` keeps doing everything it does today: request validation and
   limits, pseudonymization and restoration, the profile and credential,
   system-one-adapter, CHE-33 retries, answer validation and the judgment
   record.
3. Return `Evaluation(answers, Usage(input, output), "compatible", model,
   None)` from its result, where `model` is the model the response
   confirmed.
4. On `JudgmentError`, raise `ProviderConfigError(text)` for
   `backend_not_configured` and `ProviderError(text)` otherwise, where
   `text` is the judgment error's text. Cancellation propagates.

The `model` argument (the upstream's configured model name) and `timeout`
are ignored: the profile names the model and the call context bounds the
time.

## Profile kinds (added 2026-09-30)

`judge()` loads the selected profile as today. For a general-model profile
(`api = "openai"`) nothing changes. For a Jev profile (`api = "jev"`):

1. The profile names `jev_provider`: `typesafe`, `openrouter`,
   `cloudflare`, `vercel` or `compatible`, plus `model`, `credential` (the
   variable name in the profile's `0600` credential file) and any address
   or account field that provider needs. Missing or unknown values are
   `backend_not_configured` naming the profile.
2. Request schema validation and pseudonymization run as for general
   profiles; the general-model size limits and answer-distribution checks
   do not.
3. The named provider's `evaluate(state, questions, model, timeout)` runs
   with the call's remaining time as `timeout`, so PyModel's retries apply.
4. Its `Evaluation` becomes the judge result (answers restored after
   pseudonymization); its `ProviderError`s become backfire's fixed error
   types; the judgment record is written as for general profiles.

The Vercel provider follows jev-agent-tools 0.1.2's driver (see
[research.md](../research.md) R11) with the address and model taken from
the profile.

## `aclose()`

Nothing to release; `judge()` opens and closes its client per judgment.
