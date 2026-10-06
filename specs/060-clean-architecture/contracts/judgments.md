# Judgment Backend Contract

## Route and Policy

One provider-neutral judgment port uses the existing gated jev-mcp client.
Do not duplicate the upstream tool schemas, protocols, retries, HTTP status
mapping or finish-reason checks. Shared client extraction requires two concrete
consumers; until then the capability owns its own small port/adapter.

| Profile | Upstream settings owned by composition | Required behavior |
| --- | --- | --- |
| Jev | `JEV_PROVIDER=openrouter`; `JEV_MCP_MODEL=typesafe/jev-1.13`; approved OpenRouter credential file | General judgments and all model-choice judgments; returned route checked. |
| GLM | `JEV_PROVIDER=compatible`; `JEV_MCP_MODEL=zai-org/glm-5.3-flash`; `JEV_API_BASE_URL` to reviewed system-one-adapter's System One endpoint; adapter reads the approved Hive credential | General judgments only; Hive is not treated as a Jev provider. |

The upstream server stays hidden behind FastMCP education privacy middleware.
The adapter endpoint is loopback-only, protected according to the reviewed
upstream route. Only the gated proxy is exposed to clients; launching another
configured gated instance for a Jev-only purpose is not direct upstream access.
Neither profile silently substitutes for a failed one.

S5 adds `--profile jev|glm` to the existing gate's `jev-mcp` entry. With no flag,
it reads the configured general profile, defaulting to Jev when unset. The
model-choice reference's supported plain-client transport passes `--profile jev`
explicitly and checks `provider=openrouter` and `model=typesafe/jev-1.13` in the
answer. That client instance is ephemeral, always gated and never registered as
a direct upstream server. A wrong/missing route fails the selection.

Credit offers retains Jev for its existing no-flag invocation, including the
approved scheduled job. Its S5 manual `--profile glm` option chooses the private
GLM profile explicitly; choosing another scheduled provider remains a separate
user decision. These flags are planned behavior to implement/test in S5, not
commands claimed available in the planning slice.

Configuration is read from the approved XDG configuration root, with existing
absolute-variable/default handling and protected provider files. Only the fields
upstream lacks need local settings; reuse its environment knobs. Document a
candidate configuration without writing live settings or reading key values.
The baseline registration is retained until separately authorized activation.

## Timeouts and Failures

Set `JEV_MCP_REQUEST_TIMEOUT_MS=300000` for GLM and keep Jev's 60000 ms request
default. Initial client deadlines are 330 seconds for GLM and 90 seconds for Jev,
including a 30-second transport margin. During S5 verify upstream's whole-tool
and retry time bound; extend the client if its documented total can exceed those
initial deadlines. Do not implement another retry policy. The model-choice helper's former 60-second client
and credit-offers' 90-second client must not cut off a valid GLM call earlier.

Settings acceptance covers absent, empty, relative and absolute XDG variables
with an isolated synthetic HOME. Defaults must not read the real registered
list or credentials. Invalid profile/timeout input fails explicitly; supported
custom settings preserve existing protected-file and storage behavior.

Test a synthetic response after 60 seconds but within the GLM deadline, and
an out-of-deadline response that reports explicit failure. A controllable clock
or reduced-scale equivalent exercises routine boundary cases; one real slow
synthetic end-to-end case proves the actual timeout stack when accepting the
backend slice. Record exactly which was run.

Unknown configuration, invalid arguments, upstream MCP errors, malformed
answers, timeout and cancellation remain failures through the consumer's
existing error contract. Continued valid service after a bad request is
required. Return route evidence only when actually present.

## Privacy and Acceptance

The gate replaces registered synthetic person/school forms and identifier
patterns before either backend and restores supported output text afterward.
The existing per-call in-memory mapping and residual-risk semantics remain.
No direct student-data path or persisted mapping is added. Tests use temporary
synthetic lists; workers do not read the private registered list or real raw data.

Before system-one-adapter adoption, review an immutable exact upstream revision,
its dependency closure, network/authentication/logging/process boundaries and
recoverability. Obtain evidence for every security finding and resolve actionable
ones before installation. Runtime and server stay upstream-authored.

Both backends are implemented and exercised in the first backend slice using
representative non-personal classify/verify/decide calls. This representative
set is an acceptance scenario, not a permanent billed-call cap. Record actual
provider/model, outcome, duration and call count without secrets.
Model-choice acceptance uses Jev even when the general configured profile is
GLM; if no Jev route is usable, selection stops and asks the coordinator.
