# Contract: Profiles and the Provider Factory

## Construction

```text
Runtime(load_settings(),
        provider_factory=<backfire factory>,
        regex_executor=<backfire regex executor>)
```

PyModel's `Runtime` calls the factory once, at the first judgment of a
server process.

## Configuration

- Shipped configuration: `backfire/config.toml` (code plugin) or
  `backfire_education/config.toml` (work plugin, selected by
  `--education`, which also turns pseudonymization on).
- Operator configuration: `$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml`,
  which may select a profile or add and replace profiles, as today.
- Key: from a `0600` file owned by the user, `<profile>.env` in the same
  directory by default, or the path in the profile's `credential_file`;
  the line `<credential>=<key>` names the variable. The key is never logged
  or printed.

## Profile kinds

- **Hive (general model)**, `api = "openai"`: `base_url`, `model`,
  `credential`, optional `request` fields sent with every request. The
  provider asks system-one-adapter and returns PyModel's `Evaluation`
  (`provider` = `compatible`). Retries: PyModel's policy (408, 429, 5xx),
  plus a normal-looking reply without an answer (CHE-33).
- **Jev**, `api = "jev"`: `jev_provider` (`typesafe`, `openrouter`,
  `cloudflare`, `compatible` or `vercel`), `credential`, and the fields that
  provider needs (`base_url` for `compatible` and `vercel`, `account_id` for
  `cloudflare`, optional `base_url` for `typesafe`), optional `model`.
  PyModel's `resolve_provider` builds the first four from
  `Settings.model_construct(...)`; `vercel` is backfire's Vercel provider.

## Education wrapper

With education settings on, the factory returns a provider that
pseudonymizes `state` and the questions, calls the chosen provider, and
restores names in the answers, for either kind. Its errors
(`backend_not_configured`, `pseudonym_conflict`) keep backfire's
`JudgmentError` text.

## Errors

A missing or invalid profile, key file or provider name raises PyModel's
`ProviderConfigError` with `backend_not_configured: ...` naming the file or
profile, before anything is sent. Other provider failures are PyModel's
`ProviderError`s, reported by PyModel's tools as they are.
