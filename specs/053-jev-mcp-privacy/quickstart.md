# Quickstart: Controlled Synthetic Integration

Assumption: this is a planned acceptance procedure after the reviewed dependencies and tests exist. It was not executed by the documentation worker. No real list, provider file, source document or account is read. Use synthetic fixtures only; no paid model call.

## Phase A check without held workspace integration

The implementer first obtains independent security review of the selected dependency artifacts. Create a disposable isolated environment under `/tmp/che86-gate-check/`, using the reviewed lock closure: FastMCP 4.0.10, Faker 40.40.0, phonenumbers 9.0.40, and mcp/mcp-types 2.2.0 while jev-judge-mcp (PyModel) remains. No romanizer dependency or hook. The 2.3.0 prototype is not integration acceptance. Use the root .python-version; no new package pin. Do not `uv sync` the repository while CHE-84 holds pyproject.toml/uv.lock. The root wildcard would include the new package (pyproject.toml:9-10; W3:78-82).

With that environment installed, the planned narrow command is:

```sh
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7   env PYTHONDONTWRITEBYTECODE=1   PYTHONPATH=packages/education-privacy-gate/src   /tmp/che86-gate-check/bin/python -m pytest -p no:cacheprovider   packages/education-privacy-gate/tests/test_registry.py   packages/education-privacy-gate/tests/test_privacy_gate.py   packages/education-privacy-gate/tests/test_proxy.py   packages/education-privacy-gate/tests/test_upstream_tools.py
```

The disposable Python path is a required prepared test environment, not a shipped client path. Fixture initialization selects synthetic config/data roots and a temporary mode-0600 registered-list.json in a mode-0700 directory. Test code supplies fixture transport explicitly; production has no environment bypass to disable the gate. Do not point this command at a live list or credentials.

## Actual protocol and output assertions

`tests/fixture_server.py` is a local FastMCP fixture that records received synthetic fields and returns text JSON, plain errors, nested structured content and metadata. `tests/fixture-upstream.mjs` intercepts fetch inside the pinned upstream Node process; any non-fixture network attempt fails. `test_upstream_tools.py` connects to the actual gated proxy and the installed unmodified upstream entry, reads all 12 schemas and calls each with a valid fixture. Supply only synthetic credential-format inputs in the isolated child environment; no protected provider reader executes in this harness.

Assertions must inspect the captured requests and client-visible outputs, not only process exits. Require no registered synthetic name/school/contact/number original upstream; restoration of every unchanged echo, including JSON keys and unvalidated usage strings, with exact originals where uniquely anchored and registered romanized/Hangul fallback otherwise; numeric/enum equality; class/grade preservation; ONE default-English Faker first name per person shared by every registered Hangul/Latin full/given/order/separator/case form, with no shortened/per-form fakes or particle rule; exact original restoration where echoed fields/identifiers uniquely anchor each spelling and otherwise registered romanized spelling or Hangul fallback; mixed forms accepted and both anchored/default restoration tested; no cross-restoration in concurrent calls; generic unsafe-slug/metadata/extra-surface refusals with zero forwarding; service recovery after timeout/child death/refusal. Compare the tool list against the pinned upstream capture. Inspect captured child/proxy stderr for payload absence. Verify locked npm public entry only, fixed OpenRouter/typesafe/jev-1.13 route/model, neutral cwd, no endpoint/proxy/Node option inheritance, disabled FastMCP update check/banner/env-file/telemetry, no caller JSON Schema passed to the SDK, and call-local maps cleared on every exit. Inspect the REAL child environment: HOME, LOGNAME, PATH, SHELL, TERM, USER from the MCP transport plus the three Jev variables; never claim a three-variable total bound (security review Q1; privacy-gate.md acceptance conditions).

Force a Faker first name already present in original text, a registered-spelling collision, different-person same-call overlap, shared given names and finite exhaustion (256 draws/identity, 128 identities). Different people never share a stand-in; same-person mixed forms do. Document the accepted risk that a missing real Korean name can stand out among English fakes. Inspect fresh draws for isolation while permitting random repeats across calls. Observe files and process-tree RSS/CPU under the maximum fixtures, including restoration expansion, list/depth/node boundaries and cancellation. The limits and named checks are in [data-model.md](data-model.md#positive-bounds). A fixture cannot prove provider retention, legal compliance or arbitrary model spelling restoration.

## Phase B integration and acceptance

After Root grants the handoff, planned locked checks use:

```sh
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7   env PYTHONDONTWRITEBYTECODE=1 uv run --frozen --offline --no-sync   --package education-privacy-gate pytest -p no:cacheprovider   packages/education-privacy-gate/tests
```

Then run exact consumer fixtures, plugin preparation/distribution tests and workflow with the coordinator's exact-file plan. Native Code-only, Work-only, combined and one-plugin-disabled client sessions, with byte-identical portable jev copies/resources, one deterministic local link, both receipt ownership sources preserved and divergence rejected, must show one gated judgment route and actual upstream tool metadata. Main effective registration/provider-path changes wait for the first official release and its fresh whole-repository review; main owns separately authorized real admission. Repository acceptance stays separate from external activation; local discovery tests do not establish that those external steps happened.

Save immutable aggregate PASS/FAIL, tool counts, resource peaks and exit results under the current dispatch's state attempt. Never persist mappings or real payloads; synthetic captures may be retained as fixture evidence. The coordinator grants one full verify at a time on frozen source after `pgrep -af "turbo run"` is clear. Require the same run's Turbo summary, independent other-provider review and split decision before finish. No full verification is run by this documentation worker (AGENTS.md:94-121; Design).
