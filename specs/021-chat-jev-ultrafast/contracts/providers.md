# Contract: Jev provider selection

Applies to `packages/jev-ultrafast/src/jev_ultrafast/model.py` and
`packages/jev-ultrafast/src/jev_ultrafast/providers.toml`. See
[research R2](../research.md#r2-provider-selection-and-the-vercel-request-format).

## Configuration

`providers.toml` holds one table per provider. It is the only place that
names a provider's address, headers or credential variable, and the model
of every provider except TypeSafe. TypeSafe's model stays upstream's
`TYPESAFE_MODEL` environment variable (default `jev-latest`), so the TypeSafe
request is unchanged.

```toml
[typesafe]
protocol = "systemone"
url = "https://api.typesafe.ai/v1/systemone"
key_env = "TYPESAFE_API_KEY"

[vercel]
protocol = "evaluation-model"
url = "https://ai-gateway.vercel.sh/v4/ai/evaluation-model"
key_env = "AI_GATEWAY_API_KEY"
model = "typesafe-ai/jev"

[vercel.headers]
ai-gateway-protocol-version = "0.0.1"
ai-gateway-auth-method = "api-key"
ai-evaluation-model-specification-version = "4"

[openrouter]
protocol = "systemone"
url = "https://openrouter.ai/api/alpha/decisions"
key_env = "OPENROUTER_API_KEY"
model = "typesafe/jev-1.13"

[cloudflare]
protocol = "ai-run"
url = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run"
key_env = "CLOUDFLARE_API_TOKEN"
account_env = "CLOUDFLARE_ACCOUNT_ID"
model = "typesafe/jev"
```

The `cloudflare` table was added on 2026-09-30 at the user's request, after
Vercel's free tier refused Jev (research R10), and the `openrouter` table
the same day, also at the user's request, before the user picks the offer
search's provider. OpenRouter's decisions API takes TypeSafe's request and
answers in its form, so it uses the `systemone` protocol with its own
model.

## Selection

- `JEV_PROVIDER` names a table; unset or empty means `typesafe`.
- An unknown name raises an error naming it and the known names, before any
  request.
- A missing or empty credential variable, or for `ai-run` a missing account
  variable, raises an error naming the variable, before any request. No
  error or log contains a key.

## Protocols

| | `systemone` | `evaluation-model` | `ai-run` |
| --- | --- | --- | --- |
| Request body | Upstream's `{model, state, questions}`; the model is the table's `model` when it has one (OpenRouter), else upstream's `TYPESAFE_MODEL` (default `jev-latest`) | `{state, questions}`; questions are sent as they are | `{model, input: {state, questions}}` with the configured model |
| Address | `url` | `url` | `url` with `{account}` replaced by the account variable's value |
| Headers | `Authorization: Bearer <key>` | `Authorization: Bearer <key>`, the configured headers, and `ai-model-id: <model>` | `Authorization: Bearer <key>` |
| Answer given to the caller | The response as upstream reads it | `{"answers": …, "usage": {"input_tokens", "output_tokens"}, "model": <model>}`, where a `choice` answer becomes `{type, choice, probabilities, confidence}` with confidence from `providerMetadata.typesafe.confidence[<id>]` or null, and other answers pass through unchanged | The model output, taken from Cloudflare's v4 envelope (`result.result`, else `result`, else the body), already in TypeSafe's answer form |
| Retries and errors | Upstream `post_json()`: retries 429, 503 and 529 twice, then raises without executing an action | The same function | The same function |

The carrier also maps `noul` questions to `boolean` and back. Jev
Ultrafast and the offer search ask only `choice` questions, so that mapping
is left out.

`choose()` calls the selected provider instead of the fixed TypeSafe address;
everything else in `choose()` and `validate_choice()` is unchanged.
