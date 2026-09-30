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
- `src/jev_ultrafast/model.py`: select TypeSafe, Vercel, OpenRouter or
  Cloudflare from `providers.toml`, send OpenRouter's configured model through
  the upstream system-one protocol, pass configured request headers, adapt
  Vercel choice answers to Jev's TypeSafe answer shape, and support
  Cloudflare's `ai-run` protocol. TypeSafe remains the default.
- `src/jev_ultrafast/browser.py`: use Orca's private runtime folder and an
  owned Orca tab by default; read that tab's CDP address, attach to its page,
  and close the tab and daemon. `JEV_BROWSER=chrome` retains upstream target
  creation and close behavior.

## Local additions

- `src/jev_ultrafast/providers.toml` holds provider addresses, headers, model
  and key-variable names.
- `tests/test_providers.py` and `tests/test_orca_browser.py` contain offline
  stubs for the added provider and browser behavior.
- `examples/flights.py` is copied unchanged because the unchanged
  `tests/test_agent.py` imports it.
