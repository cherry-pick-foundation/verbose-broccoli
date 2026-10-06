# Contract: Judgments Through Jev or GLM

Held until hold H1 is released: the privacy gate's Claude Code metadata bug
is fixed and `system-one-adapter` passes its read-only security review
([plan](../plan.md#holds)). This contract fixes what that slice must deliver
(FR-019 to FR-024).

## Servers

| Server | Backend | Model | Request time limit | Launch |
| --- | --- | --- | --- | --- |
| `jev-mcp` (exists) | Jev on OpenRouter | `typesafe/jev-1.13` | 60 seconds (the gate's client default today) | the gate's proxy with its OpenRouter profile (`packages/education-privacy-gate`, `build_proxy`) |
| second gated server (name chosen in the H1 slice) | GLM 5.3 Flash on Hive through `system-one-adapter` as a System One-compatible endpoint | `zai-org/glm-5.3-flash` | a setting, at least 300 seconds (FR-020) | the same gate with a second provider profile: upstream `JEV_PROVIDER=compatible`, `JEV_API_BASE_URL` at the local endpoint, `JEV_MCP_MODEL`, `JEV_MCP_REQUEST_TIMEOUT_MS` |

Both servers expose the same upstream `jev-mcp` 0.13.0 tools behind the same
privacy gate (U-2026-10-06i, R-CA-06). Tool names are unique only within one
server, so the two registrations need distinct server names; agents tell the
tools apart by those names (R-ARCH-14). Provider facts live in the provider
profile and settings, not in the tools' code (root `AGENTS.md` "Rule
placement and reusable boundaries").

## Use from code

- A component that needs a judgment owns a port named for its purpose, for
  example "judge these offers", in `application/` (R-CA-02, R-ARCH-04). Its
  adapter calls one gated server over MCP; `bootstrap` picks the server from
  settings.
- Code defaults to `jev-mcp`; the setting below switches it to the GLM
  server (U-2026-10-06i).
- No shared judgment package is created until two component packages need
  the same adapter code (FR-008).
- Pydantic AI is not used until a tool first needs to call a model directly
  (FR-024).

## Settings

In `$XDG_CONFIG_HOME/verbose-broccoli/config.toml` ([settings
contract](settings.md)):

| Key | Default | Meaning |
| --- | --- | --- |
| `[judgment] server` | `"jev-mcp"` | which gated server a component's judgment adapter calls |
| `[judgment.glm] timeout_seconds` | `300` | request limit for the GLM server; values below 300 are refused at start |

Keys stay in `providers/openrouter.env` and `providers/hive.env`; only the
launcher reads them, and no tool prints them.

## Rules

1. Every judgment that may contain student data passes the gate; if the gate
   cannot start, the request is refused, never sent ungated (FR-021).
2. Worker model-choice judgments use `jev-mcp` only (FR-022).
3. Verification uses a fake judge at the port; live calls run separately and
   report their count (FR-023, R-GG-15, R-GG-16).
4. A Hive 429 or 405, or exhausted OpenRouter credit, is reported; the tool
   does not switch provider on its own (spec Edge Cases).
5. GLM refuses answers longer than its output limit; callers keep requests
   small. On 2026-10-06 requests of about 8 to 11 claims passed and larger
   `jev_verify` requests failed ([research](../research.md#citation-check)).

## Time limits

A GLM answer can take minutes, so every layer's limit must allow at least the
GLM setting:

- the gate's client limit to the hidden upstream server, 60 seconds today
  (`build_proxy(..., timeout=60)` in `packages/education-privacy-gate`), taken
  from the provider profile instead;
- upstream `JEV_MCP_REQUEST_TIMEOUT_MS` for the model request;
- each agent's own tool-call limit, set in the user-scope registration with
  the user's approval: Codex 0.160.0 reads `tool_timeout_sec` per server, and
  Claude Code 2.1.289 reads `MCP_TOOL_TIMEOUT` (milliseconds) or a per-server
  tool-call limit. The MCP specification leaves tool-call limits to clients
  (R-ARCH-14).

## Errors

The gate's refusals, a missing credential and a provider refusal come back
as tool execution errors (`isError: true`) the model can read; malformed
requests and unknown tools stay protocol errors (R-ARCH-14).

## Decided in the H1 slice

- Whether `system-one-adapter` runs as a child of the gate or as a user
  service, after its security review. Pydantic AI lists `typesafe:`,
  `system-one:`, `zai:` and `openrouter:` providers (R-PAI-05); their pages
  were not captured, so the slice reads them first under the reuse order.
- If Pydantic AI is used: a structured `output_type` for Jev, which cannot
  return text (R-PAI-04); OpenAI client `max_retries=0` and no
  `FallbackModel`, so no call repeats or switches provider silently (R-PAI-05,
  R-PAI-06); `native=True` MCP stays off, so the provider never reaches a
  gated server itself (R-PAI-07); no extra request metadata, which the gate
  refuses (R-PAI-08); `ALLOW_MODEL_REQUESTS = False` in the adapter's tests
  (R-PAI-10).
- The second server's registration name, and its registration in both agents'
  user settings with the user's approval.
