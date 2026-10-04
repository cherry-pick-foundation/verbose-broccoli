# Jev Ultrafast upstream record

Source: <https://github.com/browser-use/jev-ultrafast>

Revision: `1231850a0bf1a0c0341fe408ef1668dbbfdfac46`

SHA-256 values below are for each file at that upstream revision. Package
paths show where the files were copied here.

| Upstream file | Package file | Original SHA-256 |
| --- | --- | --- |
| `LICENSE` | `LICENSE` | `5afa3d97bf1e6f998d587fa101e3fe0d0c416840b7fe77bcd6ae97690a334631` |
| `pyproject.toml` | `pyproject.toml` | `3afd9e12c2c1c1efb32231669cd2d415b16c098cc057e91fc05844f4ab6c19e2` |
| `tests/test_agent.py` | `tests/test_agent.py` | `3f1e4e45077e8d2a8933f21e5c3fc7eeb3382125157d39a2a794faf3a6108ad5` |
| `examples/run.py` | `examples/run.py` | `3710883749a19c820626eb29d86b4686417a6741ba2e6292bb772851f96bc98c` |
| `examples/flights.py` | `examples/flights.py` | `a58322ac24c99985af6eec76deb4bbb6a84c9c6571aded327bc02ba7463a661c` |
| `scripts/check_guards.py` | `scripts/check_guards.py` | `adbc0c76cfaa30d89d0e9117c6246f22b0bbc090a5c96514e8c62d4a02d1ed1c` |
| `jev_ultrafast/__init__.py` | `src/jev_ultrafast/__init__.py` | `60f025b8d24465e2c0f7a3547d43b8020fd8843de7b6cb3f892ef63f5548cf63` |
| `jev_ultrafast/agent.py` | `src/jev_ultrafast/agent.py` | `aaf8b271cb0ee6643fe7beb525328ab80de8568c7ac044d02b9c6721161e7c8b` |
| `jev_ultrafast/browser.py` | `src/jev_ultrafast/browser.py` | `ee08dafa93d731bd292aa0263a578a29c8001cf22eef3c59fe44a159649155ee` |
| `jev_ultrafast/demo.py` | `src/jev_ultrafast/demo.py` | `a0cfb10909b370efb284cbbe16bdb4b7e7e06ba6385827404169027645a1d8a4` |
| `jev_ultrafast/model.py` | `src/jev_ultrafast/model.py` | `a85ada8458d23642c5c8a4095acf0565e6268f81dcda26f6308942b653e9c9f3` |
| `jev_ultrafast/questions.py` | `src/jev_ultrafast/questions.py` | `66a7054b85040b949e1757311257ea0c5a843c635f9a40c99f6d15ad660fb422` |
| `jev_ultrafast/snapshot.js` | `src/jev_ultrafast/snapshot.js` | `e50473501c8fb8e70f3b21866d987393e3f2315c639d638bd477d170e81ed78d` |
| `jev_ultrafast/static/app.js` | `src/jev_ultrafast/static/app.js` | `711e1cb2df44fff17e79bc9344d3e2aab1111107c6d169ec06b6a0d416fac9fb` |
| `jev_ultrafast/static/fixture.html` | `src/jev_ultrafast/static/fixture.html` | `e48e7d7b6225b215060692e0a28c3d0b59e465e4b94c1bc510d5f37ff0b8bfbe` |
| `jev_ultrafast/static/index.html` | `src/jev_ultrafast/static/index.html` | `a03afe6f51df1c844225f976488dd4b5ae6c9985d1f4f8aa26392013cb3b6cf6` |
| `jev_ultrafast/static/style.css` | `src/jev_ultrafast/static/style.css` | `cde13f05006719cf01d881a54ccedd6c25326122badaee0c68f78656a36f9e8d` |

## Differences from upstream

- `pyproject.toml`: use `uv_build` with `src` as the module root; use the
  workspace's `pytest==9.1.1` dev dependency; omit the upstream README path
  because that file is not copied. Keep upstream runtime dependencies and the
  `jev` script.
- `src/jev_ultrafast/model.py`: remove the direct provider route
  (`request_jev`, `post_json`, provider selection and its `providers.toml`).
  Send each Choice head as a `jev_classify` call to the repository's gated
  `jev-mcp` proxy over MCP, in one session per decision: the operation first,
  then only the chosen operation's targets. A target head with one option is
  chosen without a call, because `jev_classify` needs two. `validate_choice`,
  `action_space`, `field_context` and the decision dictionary keep their
  shape. The text helper is held: `field_text` raises before any model or
  network use. Each step sends one or two gated calls. The per-step proxy
  startup was measured at about 1.7 seconds under a mock only, not live.
  Upstream's internal retries mean gated-call attempts are not provider HTTP
  attempts or billing counts; a timeout leaves the provider outcome unknown.
- `src/jev_ultrafast/agent.py`: charge each gated request attempt immediately
  before dispatch, including failures, refusals, timeouts and cancellations;
  never refund. Retain the 120-attempt allowance (`MAX_STEPS * 2`) and the
  separate 60-action guard. Exhaustion before a target request leaves no
  decision to execute. Record `model_calls` separately from `decisions`,
  numeric usage (when supplied) and elapsed time.
- `src/jev_ultrafast/browser.py`: use Orca's private runtime folder and an
  owned Orca tab by default; read that tab's CDP address, attach to its page,
  and close the tab and daemon. `JEV_BROWSER=chrome` retains upstream target
  creation and close behavior.
- `tests/test_agent.py`: replace the tests of the direct HTTP post and the
  text helper with tests of the gated route (one request per used head, a lone
  option, refusal, malformed results, held text), plus attempted-call budget
  boundaries and callback ordering; retain the existing execution guards.

## Call units

A browser run allows at most 120 gated tool-call attempts (`MAX_STEPS * 2`):
each operation or target request counts, including failures. The 60-action
guard is separate. Under the default OpenRouter route, the unmodified upstream
may make up to 3 fetch attempts per dispatched request, so up to 360 explicit
fetch attempts per run. `JEV_MCP_MAX_ATTEMPTS` defaults to 3 and is clamped
1-6; the proxy does not set it. Actual processed requests and billing are
unknown. The 1.7-second per-step startup figure comes from a mocked run only.

## Local additions

- `tests/test_providers.py` tests the gated route against a synthetic stdio
  server and against the reviewed gate proxy over its mocked upstream.
- `tests/test_orca_browser.py` contains offline stubs for the added browser
  behavior.
- `examples/flights.py` is copied unchanged because `tests/test_agent.py`
  imports it.
