# Data Model: Backfire Rebuilt on jev-judge-mcp

No stored data is added. Backfire's records are removed; profiles, key
files and the education mapping table keep their formats, with two
optional profile fields added.

## Profile (TOML table under `[providers.<name>]`)

| Field | Kinds | Meaning |
| --- | --- | --- |
| `api` | both | `openai` (Hive, general model) or `jev` |
| `base_url` | Hive, Jev `compatible`/`vercel` (optional for `typesafe`) | Endpoint address |
| `model` | both (optional for Jev) | Model name |
| `credential` | both | Variable name in the key file |
| `credential_file` | both, optional | Path of a `0600` key file other than `<profile>.env` |
| `request` | Hive, optional | Extra request fields sent with every request |
| `jev_provider` | Jev | `typesafe`, `openrouter`, `cloudflare`, `compatible` or `vercel` |
| `account_id` | Jev `cloudflare` | Cloudflare account |

The shipped code configuration selects the Hive profile and carries an
unselected `vercel` Jev profile whose `credential_file` is the chat
plugin's `~/.config/verbose-broccoli/chat/jev.env` with
`credential = "AI_GATEWAY_API_KEY"`.

## Provider chain for one judgment

`Runtime.ask` → [education wrapper] → Hive provider or Jev provider →
`Evaluation(answers, usage, provider, model)` → PyModel's tool validation.

## Upstream contribution

`specs/021-backfire-rebuild/upstream/pymodel.patch` (against PyModel
`v0.6.0`) and `pull-request.md` (what, why, tests, measured effect).
