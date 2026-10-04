# Quickstart: Controlled Synthetic Integration

Assumption: commands describe built HEAD 28e4ff0; final acceptance remains pending. The synthetic package suite was not executed by this documentation worker. No real list, provider file, source document or account is read. Use synthetic fixtures only; no paid model call.

## Install and run the current synthetic suite

The package is integrated into the uv workspace and locks (750af5b); obsolete dependencies are removed (28e4ff0). The root `.python-version` supplies the gate's Python 3.14.4 pin; the gate has no duplicate package pin. `mcp` and `mcp-types` remain 2.2.0; no romanizer dependency or hook is installed. Existing unrelated package/tool pins are unchanged.

The following commands exist in root `package.json`. Installation prepares the reviewed npm closure; it does not make a provider call:

```sh
npm run education-privacy-gate:install
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 \
  npm run test:education-privacy-gate
```

Fixture initialization selects synthetic config/data roots and a temporary mode-0600 registered-list.json in a mode-0700 directory. Test code supplies fixture transport explicitly; production has no environment bypass to disable the gate. No real list or protected provider reader executes in this harness.

For an authorized direct client call, use the FastMCP example in [the operator guide](../../docs/jev-mcp.md#run-and-call-it). It launches only:

```sh
uv --directory packages/education-privacy-gate run --frozen --offline --no-sync jev-mcp
```

Run a saved client script with `uv run --frozen --offline --no-sync --package education-privacy-gate python <script>`. Unlike the tests, that client example spends provider credit and needs authorized local setup; it is not part of this worker's checks. Native Node is resolved with `mise which node` from `/`, or PATH when mise is absent. Callers explicitly pass only an absolute `XDG_CONFIG_HOME`; SDK baseline environment is added separately. Never read, print or pass the protected provider file.

## Actual protocol and output assertions

`tests/fixture_server.py` is a local FastMCP fixture that records received synthetic fields and returns text JSON, plain errors, nested structured content and metadata. `tests/fixture-upstream.mjs` intercepts fetch inside the pinned upstream Node process; any non-fixture network attempt fails. `test_upstream_tools.py` connects to the actual gated proxy and the installed unmodified upstream entry, reads all 12 schemas and calls each with a valid fixture. Supply only synthetic credential-format inputs in the isolated child environment; no protected provider reader executes in this harness.

Assertions must inspect the captured requests and client-visible outputs, not only process exits. Require no registered synthetic name/school/contact/number original upstream; restoration of every unchanged echo, including JSON keys and unvalidated usage strings, with exact originals where uniquely anchored and registered romanized/Hangul fallback otherwise; numeric/enum equality except ten-digit JSON integers, which become EduOK label strings and restore as decimal text; typed numeric fields reject under unchanged upstream schemas; class/grade preservation; ONE default-English Faker first name per person shared by every registered Hangul/Latin full/given/order/separator/case form, with no shortened/per-form fakes or particle rule; exact original restoration where echoed fields/identifiers uniquely anchor each spelling and otherwise registered romanized spelling or Hangul fallback; mixed forms accepted and both anchored/default restoration tested; no cross-restoration in concurrent calls; generic unsafe-slug/application-metadata/extra-surface refusals with zero forwarding; accepted integer progress counters are dropped, string counters reject, and backend SDK metadata contains no caller content; supported upstream isError results restore and retain their status; transport/protocol exceptions, unsupported content and gate failures return only `Privacy gate rejected the call.`; service recovery after timeout/child death/refusal. Compare the tool list against the pinned upstream capture. Inspect captured child/proxy stderr for payload absence. Verify locked npm public entry only, fixed OpenRouter/typesafe/jev-1.13 route/model, neutral cwd, no endpoint/proxy/Node option inheritance, disabled FastMCP update check/banner/env-file/telemetry, no caller JSON Schema passed to the SDK, and call-local maps cleared on every exit. Inspect the REAL child environment: HOME, LOGNAME, PATH, SHELL, TERM, USER from the MCP transport plus the three Jev variables; never claim a three-variable total bound (security review Q1; privacy-gate.md acceptance conditions).

Ordinary-text collision checking rejects a candidate occurring in original text/keys; registered spellings and other stand-ins keep both substring directions. Force a Faker first name already present in original text, a registered-spelling collision, different-person same-call overlap, shared given names and finite exhaustion (256 draws/identity, 128 identities). Different people never share a stand-in; same-person mixed forms do. Document the accepted risk that a missing real Korean name can stand out among English fakes. Inspect fresh draws for isolation while permitting random repeats across calls. Exercise ten-digit phone versus EduOK, isolated ten-digit and s-<ten digits> IDs, nine/eleven-digit runs, ten digits embedded in longer runs and untouched grades/classes. PhoneNumberMatcher runs first and accepted spans stay Phone NN; other isolated ten-digit strings use EduOK NN. Resident numbers remain 13 digits with an optional separator after digit six.

Reuse actual upstream schema/lib.js limits (Noul: 64 propositions of 2,000 characters), streamed 1,000,000-byte response ceiling, JEV_MCP_REQUEST_TIMEOUT_MS default 60,000 ms, JEV_MCP_MAX_ATTEMPTS default 3 clamped 1-6, explicitly configured FastMCP client timeout and SDK handling. Observe files, list storage boundaries (1 MiB, 4,096 spellings, 256 characters each), collision exhaustion and the recursion-safety depth guard with generic errors. Failed list updates preserve old bytes. Record peak process-tree RSS and CPU for a large synthetic call, including restored output and cancellation; memory/CPU are measured, not gate-enforced, and recording has no resource pass/fail threshold. Missing verify claims/evidence, screen text/purpose and classification-context input ceilings, pre-parse frame/allocation ceilings and concurrency caps are handoff notes: ask upstream for supported controls or main for an operating-system resource scope at service level. FastMCP decoded-result limits do not bound pre-parse allocation. Build no body/provider budgets or scheduler. The controls and named checks are in [data-model.md](data-model.md#positive-bounds). A fixture cannot prove provider retention, legal compliance or arbitrary model spelling restoration.

## Phase B integration and acceptance

CHE-84 released CHE-86 judgment/provider/privacy sections at develop b7f3223 on 2026-10-05. The integrated locked check underlying the npm test command is:

```sh
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7   env PYTHONDONTWRITEBYTECODE=1 uv run --frozen --offline --no-sync   --package education-privacy-gate pytest -p no:cacheprovider   packages/education-privacy-gate/tests
```

Then run exact consumer fixtures, plugin preparation/distribution tests and workflow with the coordinator's exact-file plan. Native Code-only, Work-only, combined and one-plugin-disabled client sessions, with byte-identical portable jev copies/resources, one deterministic local link, both receipt ownership sources preserved and divergence rejected, must show one gated judgment route and actual upstream tool metadata. Main effective registration/provider-path changes wait for the first official release and its fresh whole-repository review; main owns separately authorized real admission. Repository acceptance stays separate from external activation; local discovery tests do not establish that those external steps happened.

Save immutable aggregate PASS/FAIL, tool counts, resource peaks and exit results under the current dispatch's state attempt. Never persist mappings or real payloads; synthetic captures may be retained as fixture evidence. The coordinator grants one full verify at a time on frozen source after `pgrep -af "turbo run"` is clear. Require the same run's Turbo summary, independent other-provider review and split decision before finish. No full verification is run by this documentation worker (AGENTS.md:94-121; Design).
