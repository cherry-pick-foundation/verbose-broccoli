# Quickstart: Validate the Jev-Style Decision Backend

Validation scenarios for the finished feature. Commands run from the
repository root unless a step says otherwise. Live scenarios make billed calls
to the selected provider; the offline suite does not. The steps use the shipped
`hive` profile, which the shipped `config.toml` selects unless the operator's
`config.toml` selects another.

## Prerequisites

- Deno 2.9.6, `uv`, and the Python version in
  `packages/backfire/.python-version`.
- An API key with a positive balance for the selected provider (Hive).
- Codex CLI and Claude Code signed in, for the client scenarios.

## 1. Build, install and configure (SC-007)

```bash
out="$(mktemp -d)/code"
deno task backfire:build -- "$out"
"$out/backfire/src/bin/backfire" install
cfg="${XDG_CONFIG_HOME:-$HOME/.config}/verbose-broccoli/backfire"
mkdir -p "$cfg"
[ -e "$cfg/hive.env" ] || (umask 077 && : > "$cfg/hive.env")
chmod 600 "$cfg/hive.env"
# add HIVE_API_KEY=<key> to that file with an editor
```

Expected: the build writes a copy of `plugins/code` with the component's
runtime files under `$out/backfire/`, and none of Backfire's tests or
acceptance files; the install step reports the
pinned server packages, adapter and interpreter versions and the copied
`jev-mcp` revision, and writes nothing inside the repository. Running the
steps again keeps an existing key. From a prepared machine, this step and step 2
take under 10 minutes.
Contracts: [configuration.md](contracts/configuration.md),
[provider-profile.md](contracts/provider-profile.md),
[mcp-server.md](contracts/mcp-server.md#distribution-build).

## 2. Readiness (FR-011)

```bash
"$out/backfire/src/bin/backfire" ready
```

Expected: exit 0; `requested` names the `hive` profile's provider, endpoint,
model and thinking mode; `confirmed` repeats the provider, model and thinking
mode from the provider's response; `unconfirmed` is empty; all tool checks
pass. With the key file removed, the check exits 1 before any network call and
names the file.
Contract: [readiness.md](contracts/readiness.md).

## 3. Offline suite (FR-003 to FR-010, FR-016, FR-018, FR-019)

Prepare once, with network access, as CI does:

```bash
deno install --config packages/backfire/deno.json --frozen --no-prompt
packages/backfire/src/bin/backfire install
(cd packages/backfire && uv sync --frozen)
deno task test:backfire
```

Expected: all tests pass without network access and without Node. The suite
drives the real server over MCP stdio, with the real endpoint in front of a
scripted provider, and covers:

- provider profiles: the same code sends a second, test-only profile's
  settings and applies its status overrides, and no file under
  `packages/backfire/src/` other than `src/backfire_backend/config.toml` names Hive;
- the build: the built plugin holds the runtime files and no test, test
  double, acceptance, build or linked file;

- the endpoint contract, validation without rescaling, placeholder rejection
  with a genuine 0.5 accepted, the request limits, a single-candidate
  `backfire_find` failing with `invalid_request`, and the adapter's Score at the
  three-level boundaries (`{0: 0, 1: 0.005, 2: 1}` and `{0: 0, 1: 0, 2: 0.99}`)
  accepted by the real `backfire_review`;
- every error type with its retry behavior, including a response without a
  model, `Retry-After` that does not fit, and wrong or foreign tokens that never
  reach the provider;
- tool fidelity: the tool list, and the results and error texts for every
  known-answer argument set, match the fixtures captured from `jev-mcp` 0.9.0
  on Node after mapping the upstream names to `backfire`, including the four `backfire_extract` cases;
- the MCP boundary: messages passed unchanged, one tool-call record per call
  including local-only `backfire_extract` results, tool errors and the SDK's
  argument errors, and a completed response held back until after its
  cancellation, then dropped;
- `backfire_verify` with 100,000 evidence items sharing one id reaches its
  judgment call within seconds;
- sessions: concurrent sessions, closing one, the client's input ending during a
  call and while idle, a killed client, a killed server leaving no endpoint, a
  client that dies during start, and a message over 10 MiB;
- records: digests, positions instead of labels, the `X-Judgment-Metadata` fields,
  the 50 MiB bound across rotation, normal close and a killed writer while two
  sessions write, an interrupted final line, and both kinds of record write
  failure;
- privacy: a planted request string, synthetic identifiers and the key value
  never appear in records, logs or endpoint errors.

The deadline tests wait out the real limits, so they run separately:

```bash
deno task test:backfire-slow
```

Expected: `backfire_extract` with 31 timed-out patterns and one matching
pattern against a stalled provider fails with the transport's error within
120 s; a call made to stall past 118 s gets `deadline_exceeded`, its provider
request is cancelled, and another call in the same session still answers;
cancelling during pattern matching makes no provider call.

## 4. Known-answer set in both clients (SC-003)

```bash
deno task backfire:eval -- known-answers --client claude
deno task backfire:eval -- known-answers --client codex
```

Expected: the runner stages the code plugin alone by building it into a
temporary directory and runs each client outside the repository; 100% of cases are correct in each client, including every
failure case failing with its expected error, and every answer meets the
FR-003 contract. Neither client's saved configuration changes.
Contract: [evaluation.md](contracts/evaluation.md).

## 5. Sixty-item classification (SC-004)

```bash
deno task backfire:eval -- classify-60 --runs 3
```

Expected: in each run all 60 items are correct and the call ends within
120 s; the time against the 60 s goal is reported.

## 6. Benchmark regression (SC-001, SC-002)

```bash
deno task backfire:eval -- benchmark --runs 3
```

Expected: in each run, at least 105 of 111 correct, no invalid answer and
ECE at most 0.08; median and 95th-percentile times are reported as tracked
goals.

## 7. Safety and held-out sets (SC-009, SC-010)

```bash
deno task backfire:eval -- safety --runs 3
deno task backfire:eval -- heldout --runs 3
```

Expected: zero automatic approvals on the safety set in every run. The held-out
run first verifies the seal, then in every run meets at least 97% accuracy of
automatic decisions, at least 70% of the decision tools' cases decided
automatically, and at least 90% accuracy per tool and per language.

## 8. Sessions in real clients (FR-010)

1. Start two client sessions (two Orca tabs) with the server registered, and
   call a tool in each at the same time. Both answer.
2. Close one tab; the other still answers, and `ps` shows no server or
   endpoint process left from the closed tab.
3. Send `kill -9` to one client process during a long call; its server and
   endpoint are gone within five seconds.
4. Cancel a long tool call in a client; its tool-call record shows `cancelled`
   and no later answer reaches the client.

## 9. Data handling and acceptance record (FR-009, SC-006, SC-011, SC-012)

- Every evaluation run above checks each tool call's record digest and the
  mutation cases, and the final scan finds no key value, planted string or
  synthetic identifier where it must not be.
- Read `plugins/code/skills/backfire/references/verbose-broccoli.md` and the vendored
  `SKILL.md`: they state what is sent to the selected provider, that the tools and the skill's
  advice are advisory, that a gate verdict does not prove that tests ran, that a
  screening pass does not authorize following instructions, and that
  credentials and private personal records are never sent.
- Final acceptance leaves one updated
  `artifacts/jev-decision-backend/acceptance.json` and no other new file.
