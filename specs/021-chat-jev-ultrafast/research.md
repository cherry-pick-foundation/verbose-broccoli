# Research: Jev Ultrafast web agent and API credit offer search

All facts below were checked on 2026-09-30 in this worktree's session. Commands
and file references are given so a reader at HEAD can repeat them.

## R1. Adopting Jev Ultrafast

**Decision**: Copy Jev Ultrafast at revision
`1231850a0bf1a0c0341fe408ef1668dbbfdfac46` into `packages/jev-ultrafast/`
(its `jev_ultrafast/` package under `src/`, `LICENSE`, `tests/test_agent.py`,
`examples/run.py`, `examples/flights.py`, which `test_agent.py` imports, and
`scripts/check_guards.py`), patch it in place, and record
the revision, each copied file's original SHA-256 and every difference in
`packages/jev-ultrafast/UPSTREAM.md`.

**Rationale**: The project is not published on PyPI
(`https://pypi.org/pypi/jev-ultrafast/json` returns 404), and uv can install a
Git revision but cannot patch it, so a patched copy is the smallest way to
depend on it. The package is small (850 lines across its six modules and
`snapshot.js`), MIT licensed, and its runtime dependencies are two published
packages: `browser-harness==0.1.13` (MIT, from PyPI) and `httpx[http2]`.
Upstream's `docs/` media, recording and rendering scripts and `uv.lock`
are left out; the root uv lock pins the dependencies.

**Alternatives considered**: A Git dependency with a run-time monkeypatch of
`post_json` (rejected: `choose()` reads `os.environ["TYPESAFE_API_KEY"]` before
the call, so a Vercel-only setup would fail, and a monkeypatch hides the
difference from upstream); rewriting the agent (rejected by "Reuse Before
Implementing").

## R2. Provider selection and the Vercel request format

**Decision**: Patch `jev_ultrafast/model.py` so `choose()` sends its request
through one new function that reads `jev_ultrafast/providers.toml`, selects the
provider named by the `JEV_PROVIDER` environment variable (default `typesafe`,
which keeps upstream behavior), reads the key from the provider's credential
variable, and speaks one of two protocols:

- `systemone`: upstream's request unchanged, to
  `https://api.typesafe.ai/v1/systemone`, with `TYPESAFE_API_KEY` and
  upstream's `TYPESAFE_MODEL` default `jev-latest`.
- `evaluation-model`: Vercel AI Gateway's endpoint
  `https://ai-gateway.vercel.sh/v4/ai/evaluation-model`, key
  `AI_GATEWAY_API_KEY`, model `typesafe-ai/jev`, headers
  `ai-gateway-protocol-version: 0.0.1`, `ai-gateway-auth-method: api-key`,
  `ai-evaluation-model-specification-version: 4` and `ai-model-id: <model>`.
  The body is `{state, questions}` without `model`. A `choice` answer is
  returned as `{type, choice, probabilities, confidence}`, with `confidence` taken from
  `providerMetadata.typesafe.confidence[<question id>]` (null when absent), and
  `usage.inputTokens`/`outputTokens` become `input_tokens`/`output_tokens`.

Addresses, headers, model names and credential variable names live only in
`providers.toml`.

**Rationale**: jev-mcp 0.9.0 (tag `v0.9.0`, commit
`a1fcc1e47fc696614f081e23a66ff48a890f22fd`) delegates its TypeSafe and Vercel
branches to `@jkudish/jev-agent-tools` (`src/provider.ts` lines 247-291 at that
tag); its `package-lock.json` locks version 0.1.2 (integrity
`sha512-Y0nPq58J2yjEZI0yaW3KXSIwsEeDa0dLwGt5thtwGRwMGE+RM2Yoc4KC+AEep83Ms11N4VdFZBpBAaJ3giQXmg==`).
That package's `dist/transports/vercel.js` defines the endpoint, headers, body
and answer adaptation above. It also maps `noul` questions to `boolean`,
which is left out because Jev Ultrafast and the offer search ask only
`choice` questions. Its `dist/transports/typesafe.js` matches upstream Jev Ultrafast's TypeSafe call.
Upstream `validate_choice()` requires a finite confidence, so a Vercel answer
without one fails closed ("no action executed"); a live check with a key will
show whether Vercel returns it.

**Alternatives considered**: Selecting the provider in a separate wrapper
package (rejected: the call and its URL sit inside `choose()`); porting
jev-agent-tools' whole provider registry with OpenRouter and Cloudflare
(rejected: the user named two providers).

## R3. Orca's built-in browser

**Decision**: Patch `jev_ultrafast/browser.py` so that, unless
`JEV_BROWSER=chrome`, `Browser` opens its own tab with `orca tab create --url
about:blank --worktree current --json`, reads that tab's address with `orca
exec --command "get cdp-url" --page <id> --json`, points browser-harness at it
through `BU_CDP_WS`, starts browser-harness's default daemon in a private
runtime folder, attaches to the one page the address lists, and on `close()`
closes the tab with `orca tab close --page <id>` and stops the daemon.
Scrolling and screenshots stay as upstream (user decision, 2026-09-30).

**Evidence** (own blank tabs in this worktree only, all closed afterwards):

| Call or step | Result |
| --- | --- |
| `Target.getTargets` on a tab's address | Lists only that tab, as `orca-proxy-target` |
| `Target.attachToTarget`, `Target.getTargetInfo` | Work; session `orca-proxy-session` (a second attach gets `-2`) |
| `Page.enable`, `DOM.enable`, `Runtime.enable`, `Network.enable` | Work |
| `Emulation.setDeviceMetricsOverride`, `Emulation.setFocusEmulationEnabled` | Work |
| `Page.navigate` | Works |
| `Runtime.evaluate`, with and without `awaitPromise` | Works |
| `Input.dispatchMouseEvent` press and release | Works |
| `Input.dispatchKeyEvent` with `commands: ["selectAll"]`, then `Input.insertText` | Work; the field's text was replaced by `Zürich` |
| `Target.createTarget` | `{"code": -32000, "message": "Not supported"}` |
| `Input.dispatchMouseEvent` `mouseWheel`, `Page.captureScreenshot` | Worked on one tab; on a tab not drawn on screen the wheel event got no reply in 5 s and the screenshot failed after 9 s with "Screenshot timed out — the browser page did not draw a frame." |
| browser-harness 0.1.13 `ensure_daemon()` with `BU_CDP_WS` set, default name, private `BH_RUNTIME_DIR`/`BH_TMP_DIR` | Started in 0.2 s and attached to the tab |
| `orca tab close --page <id>` | Closes that tab (`{"closed": true}`), although `--help` lists only `--index` |

Each tab has its own address (`ws://127.0.0.1:39505/` and
`ws://127.0.0.1:46481/` for two tabs in this session), and addresses change
when Orca restarts, so the patch reads it for every tab. A daemon named with
`BU_NAME` would call `Target.createTarget` at start-up (`daemon.py`
`attach_first_page`), which Orca refuses, so the default name in a private
folder is used; the folder must be short, because a long path failed with
"AF_UNIX path too long". browser-harness sends telemetry only from its own
command-line entry (`run.py`), not from the helpers Jev Ultrafast imports.

**Alternatives considered**: Driving Orca's browser through `orca exec`
commands instead of CDP (rejected: it would replace upstream's browser layer);
a named daemon per run (refused by Orca, above).

## R4. Plain fetch or browser for the search

**Decision**: Plain HTTP; no browser.

**Rationale**: The freetokens tracker publishes every offer as structured
data. `https://raw.githubusercontent.com/luongnv89/freetokens/main/index.json`
returned HTTP 200, `text/plain`, 128,279 bytes, with fields `slug`, `title`,
`provider`, `category`, `amount`, `expiry_date` (null for ongoing offers),
`source_url`, `status` and others. GitHub's REST API answered
`/repos/luongnv89/freetokens/commits?path=offers&since=…` without a login
(HTTP 200, `x-ratelimit-limit: 60` per hour). Nothing needs JavaScript,
sign-in or page interaction, so a browser would only add Chrome or Orca,
paid Jev calls per page and failure points.

## R5. Finding offers that appeared during a period, without saving state

**Decision**: A run looks at the latest full 6-hour block in the laptop's
time zone (00-06, 06-12, 12-18, 18-24). It asks GitHub for the last commit
that changed `index.json` before the block's start and before its end
(`commits?path=index.json&until=<time>&per_page=1`), fetches `index.json` at
both commits from `raw.githubusercontent.com`, and treats slugs present at the
end but not at the start as new. When both commits are the same, the run ends
without further requests. The tracker's history is the memory, so nothing is
saved locally.

**Rationale**: `index.json` changed in 111 commits between 2026-08-21 and
2026-09-29 and is the tracker's published list; 32 of 239 offers entered it
minutes to 12 hours after their YAML file, so the index, not the file, defines
when an offer appears for this search. Two API calls and two raw fetches per
run stay far below the unauthenticated limit.

**Limit**: runs missed while the laptop sleeps are not caught up; an offer
that entered and left the index inside one block is not seen.

## R6. The strong-offer judgment

**Decision**: Offers that are not `active` or have an `expiry_date` are
dropped without a model call. The rest go into one Jev request with one
`choice` question per offer, keyed by slug, with two criteria: `qualifies`
("Claiming it costs nothing, and it states no time limit, trial period,
expiry or end date") and `excluded` ("Claiming it needs a payment, deposit,
top-up or paid plan, or it states a time limit, trial period, expiry or end
date"). The offer's title, provider, category, amount and source link are the
state. An offer is strong when upstream `validate_choice()` accepts the answer
and the choice is `qualifies`.

**Rationale**: 56 of the 214 past offers without an `expiry_date` still state
a time limit in their text ("1-week free trial", "valid 90 days", "for 12
months", "limited time"), and a few state a cost ("after one-time $5
activation"), so the end-date field alone is not enough, and a fixed word list
misreads phrases such as "credits never expire" or "resets every 5 hours and 7
days".

## R7. Notification

**Decision**: `notify-send` (`/usr/bin/notify-send` on this GNOME laptop), one
notification per run listing each strong offer's title, provider, amount and
source link.

## R8. Automation shape

**Decision**: One Orca automation, `0 */6 * * *` in `Asia/Seoul` (the laptop's
time zone per `timedatectl`), run in the `develop` worktree
(`--workspace`, so no worktree is created per run), with the search as its
precheck. Orca runs a precheck only for scheduled runs and dispatches the
agent only when the precheck exits 0 (Orca 1.4.216 `out/main/index.js`,
function handling `skipped_precheck`); prechecks time out after at most 600 s
and keep up to 4,000 characters of output
(`out/shared/automation-precheck.js`). The precheck therefore runs the search
with notification, so a strong offer is reported without a second Jev call.
On 2026-09-30 the user approved the automation and chose that no agent
session starts at all: the precheck command ends with `; exit 1`, so Orca
records every run as skipped and keeps the search's output in the run's
details. The user also had the empty `0600` credential file created, and
will add the Vercel key to it.

## R9. The schedule interval

**Data**: [offer-history.tsv](offer-history.tsv), one row per offer that ever
entered the tracker's `index.json` (239 offers), from the tracker's public Git
history (<https://github.com/luongnv89/freetokens>, MIT; clone at commit
`643054b`, 2026-09-29; `index.json` last changed in commit `5a11993`,
2026-09-29T09:44:07Z). Columns: first time in `index.json` (UTC, the commit
time), that commit, slug, category, `expiry_date` when first seen, the
decision, when the offer left the index or was marked expired, and the amount
text.

**Definition of a strong offer** (user, 2026-09-30, replacing "high
multiplier"): claiming it costs nothing — free credits or free usage — and it
states no time limit or end date. An offer is excluded when its
`expiry_date` is set (25 offers), when its text states a time limit, trial
period, expiry, a period of validity or "limited time", or a preview or
experimental phase it lasts for (56), or when claiming needs a payment or a
paid plan (2). A card requirement without a charge, eligibility conditions
(students, startups) and recurring allowances ("per month", "resets daily")
are not time limits or costs. For the history the coordinating agent applied
this definition by reading each offer's text; the running search asks Jev.

**Calculation**: The tracker's first day, 2026-08-21, is its initial import of
11 existing offers, not a record of their appearance, so those rows are
marked "not counted". The 145 qualifying offers first appeared between
2026-08-22T07:30:21Z and 2026-09-29T09:44:07Z, 914.229 hours apart. The average
interval between consecutive appearances is 914.229 / (145 − 1) =
**6.349 hours** (6 hours 21 minutes). The schedule rounds this to **6 hours**,
the nearest whole number of hours and one that divides a day, so each run
covers one block of the day.

**Durations**: 19 qualifying offers left the index or were marked expired;
their listing lasted a median of 92.1 hours. The other 126 were still listed
at the data's end, with a median age of 362 hours. One offer,
`railway-free-vm`, was listed for less than the interval (0.5 hours; the
curator removed it). So qualifying offers do not typically last shorter than
the interval, and a 6-hour schedule misses no offer through its length alone.

**Caveat**: An offer's first appearance in the tracker is not the provider's
launch date; many tracker additions are older free tiers the curator added
later. The search reads the same tracker, so this is the rate at which it
will see new qualifying offers.

## R10. Cost of Jev calls and Vercel's free tier

Each run with new candidates makes one Jev call; a run without makes none.
At 4 runs a day that is at most 124 calls in a 31-day month. Vercel lists
Jev at $0.042 per million input tokens, served by `typesafe-ai` and
`digitalocean` (<https://vercel.com/ai-gateway/models/jev>, read
2026-09-30); the tracker recorded OpenRouter's price as "$0.042/M input
tokens and $0.00/M output tokens". At a few thousand input tokens per call,
a month of runs costs well under one cent.

**Finding (2026-09-30)**: Jev is not available on Vercel AI Gateway's free
tier, so the monthly free credit cannot pay for it. With the user's key,
three requests to the evaluation-model endpoint were refused before any
provider was tried (`providerAttemptCount: 0`), so nothing was charged:

| Time (UTC) | Status | Vercel's message |
| --- | --- | --- |
| about 19:46 | 403 | not captured (upstream's error hides the body) |
| about 19:48 | 429 | "No access to this model at this time." (`rate_limit_exceeded`) |
| 19:57:07 | 403 | "Free tier users do not have access to this model. Upgrade to paid credits … for unrestricted access." (`no_providers_available`) |

Vercel's pricing page (<https://vercel.com/docs/ai-gateway/pricing>, last
updated 2026-09-08) says: "The free tier includes a subset of models, not
the full catalog." and "Once you purchase credits, your account transitions
to the paid tier and the monthly free credit no longer applies." The Vercel
promotion that made Jev free ended on 2026-09-25 (the tracker's
`offers/vercel-ai-gateway-jev-free.yaml`). A Vercel Community report of
2026-09-29 describes the same 429 message for `typesafe-ai/jev` even after
buying credits
(<https://community.vercel.com/t/ai-gateway-typesafe-ai-jev-returns-free-tier-429-despite-paid-credits/49935>).
The user decides how Jev calls are paid for; the request format itself is
covered by the stub tests, and the live check waits for a provider that
accepts the calls.
