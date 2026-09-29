# Contract: Jev provider selection

Applies to `packages/jev-ultrafast/src/jev_ultrafast/model.py` and
`packages/jev-ultrafast/src/jev_ultrafast/providers.toml`. See
[research R2](../research.md#r2-provider-selection-and-the-vercel-request-format).

## Configuration

`providers.toml` holds one table per provider. It is the only place that
names a provider's address, headers, model or credential variable.

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
```

## Selection

- `JEV_PROVIDER` names a table; unset or empty means `typesafe`.
- An unknown name raises an error naming it and the known names, before any
  request.
- A missing or empty credential variable raises an error naming the
  variable, before any request. No error or log contains a key.

## Protocols

| | `systemone` | `evaluation-model` |
| --- | --- | --- |
| Request body | Upstream's `{model, state, questions}`, unchanged (model from `TYPESAFE_MODEL`, default `jev-latest`) | `{state, questions}`; each question keeps `instructions` and `criteria`, and type `noul` becomes `boolean` |
| Headers | `Authorization: Bearer <key>` | `Authorization: Bearer <key>`, the configured headers, and `ai-model-id: <model>` |
| Answer given to the caller | The response as upstream reads it | `{"answers": …, "usage": {"input_tokens", "output_tokens"}, "model": <model>}`, where a `choice` answer becomes `{type, choice, probabilities, confidence}` with confidence from `providerMetadata.typesafe.confidence[<id>]` or null, a `boolean` answer becomes `{type: "noul", noul: <probability>}`, and other answers pass through |
| Retries and errors | Upstream `post_json()`: retries 429, 503 and 529 twice, then raises without executing an action | The same function |

`choose()` calls the selected provider instead of the fixed TypeSafe address;
everything else in `choose()` and `validate_choice()` is unchanged.
