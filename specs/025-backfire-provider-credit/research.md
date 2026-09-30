# Research: free models for the Cloudflare and Vercel profiles

All web pages were read on 2026-09-30, without a key, and no billed or
authenticated call was made. "Model list" means the public
`https://ai-gateway.vercel.sh/v1/models` (395 entries). "Vercel page data" means
the data embedded in `https://vercel.com/ai-gateway/models?freeTier=true`.
Repository references are file:line at this branch.

**Assumption used for cost**: one judgment is about 2,000 input and 1,200 output
tokens. The input size is a guess: 021's R10 says a real Jev request was not
measured (`specs/021-chat-jev-ultrafast/research.md:253`, on branch
`feature/chat-jev-ultrafast`). The output size is DeepSeek V4.1 Flash's
1,159 tokens per decision at medium effort
(`specs/005-jev-decision-backend/research.md:1304-1311`). Other models will
differ, and reasoning tokens count as output.

## How backfire calls a general model

- Profile `api = "openai"` sends `response_format = {type = "json_object"}` and
  extra fields from `request` (`packages/backfire/src/backfire/config.toml:8`).
- `structured_outputs=False` (`packages/backfire/src/backfire/providers.py:84`),
  so the adapter asks for JSON-object output, not a JSON schema. Hive rejected
  the schema form with HTTP 400 (`specs/005-jev-decision-backend/research.md:89`).
- A profile's `insufficient_balance` lists HTTP statuses only; the default is
  `[402]` (`docs/backfire.md:83`).
- The user's decision (`specs/025-backfire-provider-credit/spec.md:58-66`): the
  Cloudflare and Vercel profiles run a free model through this path; the user
  picks the models; a used-up allowance counts as insufficient balance.

## 1. Vercel AI Gateway free tier

**What the free tier is.**

- "The free tier includes a subset of models, not the full catalog." Free
  requests are rate limited per model, "with lower limits than the paid tier."
  Buying credits moves the team to the paid tier and "the monthly free credit no
  longer applies" (<https://vercel.com/docs/ai-gateway/pricing>, last updated
  2026-09-08).
- The free tier is "a monthly included credit, not an expiring trial"
  (<https://vercel.com/docs/ai-gateway/faq>, last updated 2026-09-13).
- Vercel's pages give no dollar amount. Third-party pages say $5 a month, for
  example <https://agentjournal.dev/blog/vercel-ai-gateway-free/> and
  <https://freeaiapi.org/articles/vercel-api-key-guide>; treat $5 as unconfirmed.
- The free credit starts at the first request. A team may first need a payment
  method: `403` with `customer_verification_required` means "The team must add a
  valid payment method before using free credits" (FAQ above).
- The OpenAI-compatible endpoint is `https://ai-gateway.vercel.sh/v1`; Vercel's
  own example posts to `/v1/chat/completions` with `Authorization: Bearer <key>`
  (<https://vercel.com/docs/ai-gateway/rate-limits>, last updated 2026-09-08).

**Which models the free tier may call.** Vercel says to "browse the Free Tier
models" at `https://vercel.com/ai-gateway/models?freeTier=true` (pricing page
above). Two public sources disagree, so use the second:

- The model list has no tier field. Its tag `free` marks only five zero-price
  models: `inclusionai/ling-3.0-flash-sante`, `-sante-free`, `ling-3.1-flash`,
  `-flash-free`, and `poolside/laguna-s-2.1-free`. None lists `response_format`
  in `supported_parameters`, so they cannot honor backfire's JSON-object request.
- Vercel page data has a per-model `availableToFreeTier`: 223 of 401 entries are
  `true` (chat, embedding, image and other types together). It is `true` for all
  five candidates below and `false` for `deepseek/deepseek-v4.1-flash` (the model
  Hive runs), `deepseek/deepseek-v4-flash` and `typesafe-ai/jev`.
- Limit of this evidence: the page was read without a login, and the page's own
  props carry `enableTeamAvailability: true`, so a team's own view may differ.
  Only an authenticated request or the dashboard confirms it.

**The earlier refusal** (021 R10, `specs/021-chat-jev-ultrafast/research.md:257-266`):
on 2026-09-30 the free tier refused `typesafe-ai/jev` three times, with 403 "Free
tier users do not have access to this model. Upgrade to paid credits … for
unrestricted access." (`no_providers_available`) and 429 "No access to this model
at this time." (`rate_limit_exceeded`). A Vercel Community report of 2026-09-29
shows the same 429 text
(<https://community.vercel.com/t/ai-gateway-typesafe-ai-jev-returns-free-tier-429-despite-paid-credits/49935>,
cited there). So Jev is outside the subset, which matches `availableToFreeTier =
false` above.

## 2. Cloudflare Workers AI

**Free allowance.** "10,000 Neurons per day at no charge"; limits "reset daily at
00:00 UTC"; past a limit "further operations will fail with an error"
(<https://developers.cloudflare.com/workers-ai/platform/pricing/>, last updated
2026-09-17). The allowance is per account, so any other Workers AI use shares it.
Text generation is limited to 300 requests a minute except paid-plan models
(<https://developers.cloudflare.com/workers-ai/platform/limits/>, last updated
2026-09-17).

**Excluded (paid billing needed)**, same pricing page: `@cf/moonshotai/kimi-k2.6`,
`kimi-k2.7-code`, `@cf/zai-org/glm-5.2`, `glm-5.3`, `glm-5.3-flash`,
`@cf/deepseek-ai/deepseek-v4-flash-0731` and `deepseek-v4-pro-0813`. Calling one
on the free plan answers `403`, code `5035`, "This model requires a Workers Paid
plan." (<https://developers.cloudflare.com/workers-ai/platform/errors/>, last
updated 2026-09-17).

**OpenAI-compatible endpoint.** Base URL
`https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1`, route
`/chat/completions`, header `Authorization: Bearer {api_token}`, model written as
`@cf/vendor/name`
(<https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/>).
That page does not mention `response_format`.

**JSON mode** (<https://developers.cloudflare.com/workers-ai/features/json-mode/>,
last updated 2026-09-14): `response_format` takes `json_object` or `json_schema`;
"Workers AI can't guarantee that the model responds according to the requested
JSON Schema", and a failure returns the error `JSON Mode couldn't be met`. Its
"Supported Models" list names six models, and of the candidates below only
`llama-3.3-70b-instruct-fp8-fast`. Each candidate's own model page lists a
`response_format` parameter, but no page says the OpenAI-compatible route accepts
`json_object` for it. That needs a live probe with a key, which this research may
not make.

## 3. Candidates

Reference point already measured here: DeepSeek V4.1 Flash on Hive got 108-111 of
111 English decisions right per run, with call time about 5 s median and 16 s at
the 95th percentile (`specs/005-jev-decision-backend/research.md:1304-1311`). It
also records GLM 5.3 Flash as less reliable
(`specs/005-jev-decision-backend/research.md:1334-1338`, `1356`). **None of the
candidates below has been measured in this repository**: a search of
`specs/005-*`, `specs/021-*` and `specs/025-*` found only DeepSeek and GLM.

### Cloudflare (free allowance 10,000 neurons a day)

Neuron prices are from the pricing page; context and features are from each model
page under `https://developers.cloudflare.com/workers-ai/models/<name>/`. Calls a
day = 10,000 divided by the neurons of one judgment (2,000 in, 1,200 out). No page
documents latency.

| Model | Context | Neurons per M in / out | Neurons per judgment | Judgments a day | Reasoning control | JSON |
| --- | --- | --- | --- | --- | --- | --- |
| `@cf/google/gemma-4-26b-a4b-it` | 256,000 | 9,091 / 27,273 | 51 | 196 | Reasoning "Yes"; thinking turns on with a token at the start of the system prompt (Google's card, below) | `response_format` listed |
| `@cf/openai/gpt-oss-20b` | 128,000 | 18,182 / 27,273 | 69 | 144 | `low`, `medium` (default), `high` | `response_format` listed |
| `@cf/openai/gpt-oss-120b` | 128,000 | 31,818 / 68,182 | 145 | 68 | `low`, `medium` (default), `high` | `response_format` listed |
| `@cf/qwen/qwen3-30b-a3b-fp8` | 32,768 | 4,625 / 30,475 | 46 | 218 | Reasoning "Yes" | `response_format` listed |
| `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 24,000 | 26,668 / 204,805 | 299 | 33 | none | on Cloudflare's JSON-mode list |

Fit for judgment tasks:

- **Gemma 4 26B A4B**: MMLU Pro 82.6%, GPQA Diamond 82.3%, 256K context, mixture
  of experts with 3.8B active parameters
  (<https://ai.google.dev/gemma/docs/core/model_card_4>). The model card has no
  instruction-following row.
- **gpt-oss-120b**: GPQA Diamond 80.81, MMLU-Pro 80.8
  (<https://huggingface.co/openai/gpt-oss-120b>, evaluation results section).
  OpenAI says it "matches or exceeds OpenAI o4-mini" on MMLU and HLE and supports
  Structured Outputs (<https://openai.com/index/introducing-gpt-oss/>).
- **gpt-oss-20b**: no number found; OpenAI says it "matches or exceeds OpenAI
  o3-mini" (same OpenAI page).
- **Qwen3-30B-A3B**: the Qwen blog gives no scores for it and says thinking is
  switched by `enable_thinking` or `/think` and `/no_think`
  (<https://qwenlm.github.io/blog/qwen3/>). Scores found online (IFEval 84.7,
  GPQA 70.4) belong to the later Instruct-2507 checkpoint, not to Cloudflare's
  `qwen3-30b-a3b-fp8`, so they are not used.
- **Llama 3.3 70B**: not researched further; 33 judgments a day and a 24,000
  context rule it out.
- Not researched: `@cf/nvidia/nemotron-3-120b-a12b` (45,455 / 136,364 neurons),
  `@cf/zai-org/glm-4.7-flash` (same family as the model the user excluded on
  2026-09-27), `@cf/ibm-granite/granite-4.0-h-micro`.

### Vercel (free credit only)

From the model list (context, parameters, list price) and Vercel page data
(free-tier flag, average time to first token and tokens a second, as Vercel
measured them; window not stated). Price is per million tokens, input / output.
Judgments per $5 assume the unconfirmed $5 credit. Vercel's two sources give
different prices for the `gpt-oss` models because the price varies by provider;
the higher one is used.

| Model | Free tier | Context | Price in / out | Judgments per $5 | First token, tokens/s | JSON | Reasoning control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `openai/gpt-oss-120b` | yes | 131,072 | $0.35 / $0.75 (list $0.10 / $0.50) | 3,100 (6,200) | 332 ms, 223 | `response_format`, `structured_outputs` | effort `low`/`medium`/`high` |
| `openai/gpt-oss-20b` | yes | 131,072 | $0.07 / $0.30 (list $0.03 / $0.14) | 10,000 (21,900) | 354 ms, 915 | same | same |
| `google/gemini-2.5-flash-lite` | yes | 1,048,576 | $0.10 / $0.40 | 7,350 | 241 ms, 367 | same | toggle, effort, `budget_tokens` |
| `openai/gpt-5-nano` | yes | 400,000 | $0.05 / $0.40 | 8,600 | 5,193 ms, 147 | same | effort `minimal`-`high` |
| `alibaba/qwen3.7-flash` | yes | 991,000 | $0.03 / $0.13 | 23,000 | 2,422 ms, 89 | same | toggle, effort to `max`, `budget_tokens` |

Fit for judgment tasks:

- **gpt-oss-120b, gpt-oss-20b**: same sources as under Cloudflare above.
- **Gemini 2.5 Flash-Lite**: GPQA Diamond 64.6% non-thinking and 66.7% thinking
  for the June 2025 release; 70.2% and 71.7% for the September 2025 preview;
  Humanity's Last Exam 5.1% and 6.9%
  (<https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Flash-Lite-Model-Card.pdf>,
  table on page 3). The model list does not say which release Vercel serves.
- **GPT-5 nano** and **Qwen3.7 Flash**: no official score found. Not researched
  beyond the Vercel data.
- A zero-price model (`ling-3.1-flash-free`) is out: no JSON parameter.
- `deepseek/deepseek-v4.1-flash`, the model measured here, is not on the free tier.

## 4. When the allowance or credit runs out

| | Cloudflare Workers AI | Vercel AI Gateway |
| --- | --- | --- |
| Status | `429` | `402` per docs (see below); observed refusals were `403` and `429` |
| Code and text | `3036`: "You have used up your daily free allocation of 10,000 neurons. Please upgrade to Cloudflare's Workers Paid plan if you would like to continue usage." | `402` whose `type` is not `quota_for_entity_exceeded`: "The team does not have a positive credit balance" (FAQ, cause column). No message text is published. |
| Overlaps a rate limit? | Yes. `3040` "Capacity temporarily exceeded, please try again." is also `429` | Yes. Free-tier per-model rate limit is `429` with `{"error": {"message": "Rate limit exceeded", "type": "rate_limit_exceeded"}}`; a provider's own `429` may carry its own body |
| Recovery | Resets 00:00 UTC | Monthly credit; a `402` with `quota_for_entity_exceeded` is a budget the team set, not the free credit |
| Sources | errors page (2026-09-17) and pricing page | rate-limits page (2026-09-08) and FAQ (2026-09-13) |

Gaps to close before relying on these:

- Vercel does not say what a free-tier team gets when the monthly credit is
  spent. `402` is the documented answer for "no positive credit balance", but no
  document ties it to the free credit. The refusals seen on 2026-09-30 were about
  model access, not spent credit, so they say nothing here.
- Neither provider's page shows the error body on the OpenAI-compatible route.
  Cloudflare documents `3036` for the platform; the compatible route is not shown
  to return the same body.
- backfire matches `insufficient_balance` by HTTP status only (`docs/backfire.md:83`).
  Listing `429` for Cloudflare would also treat a passing capacity error (`3040`)
  or a rate limit as spent credit and skip the profile. Matching the code `3036`
  or its message avoids this. Vercel's `402` is safe to list because Vercel uses
  `429` for rate limits, but only if a spent free credit really answers `402`.

## 5. Recommendation and open risks

**Cloudflare: `@cf/google/gemma-4-26b-a4b-it`.** It has the strongest published
scores among the cheap options (MMLU Pro 82.6%, GPQA Diamond 82.3%), a 256,000
context, and the second-lowest cost, 51 neurons per judgment, about 196 judgments
a day. Thinking can be left off to save output tokens. Runner-up:
`@cf/openai/gpt-oss-120b` for quality, at about 68 judgments a day; or
`@cf/openai/gpt-oss-20b` for volume at 144.

**Vercel: `openai/gpt-oss-120b`.** Free-tier flag true, JSON parameters listed,
context 131,072, effort control, 332 ms to first token, GPQA Diamond 80.81. At the
higher price about 3,100 judgments a month if the credit is $5. Runner-up:
`openai/gpt-oss-20b` for volume, or `google/gemini-2.5-flash-lite` for a
different model family (weaker on GPQA, 64.6% to 66.7%). Choosing Gemma on
Cloudflare and gpt-oss on Vercel keeps the two fallbacks from failing the same
way.

**Open risks.**

1. No candidate is measured on the 111-decision evaluation set
   (`specs/005-jev-decision-backend/research.md`, "Judgment quality probes"). Run
   it before the profile ships; Hive's DeepSeek got 108-111 right, and a smaller
   free model may be well below that.
2. `json_object` on Cloudflare's compatible route is undocumented for all five
   candidates (section 2). A model that ignores it will fail every judgment.
3. The Vercel free-tier flag comes from an unauthenticated page and may differ
   for the user's team; the $5 amount is third-party. A first request with the
   key settles both.
4. Cloudflare's 10,000 neurons are a daily cap for the whole account, and gpt-oss
   reasoning tokens raise the cost per judgment above the estimate.
5. Both providers may rewrite the free subset or prices without notice; the pages
   above were dated 2026-09-08 to 2026-09-17.
6. Pseudonymized student text goes to both providers with the user's approval
   (`specs/025-backfire-provider-credit/spec.md:53-56`). The Vercel model list
   marks data retention (`zdr`) and training (`no_training`) per model:
   `openai/gpt-oss-120b` and `google/gemini-2.5-flash-lite` are `some` for `zdr`
   and `all` for `no_training`. Cloudflare's data terms were not read.
