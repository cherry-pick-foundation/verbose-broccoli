# Dependency security review: CHE-86 (Jev MCP behind a privacy proxy)

Date: 2026-10-04. Independent, read-only review (task W6). Nothing was installed, imported, built or run from these packages.
`EV` means the evidence folder `results/w6-security/attempt-1/` under the feature's state directory
(`$XDG_STATE_HOME/verbose-broccoli/workspaces/feature-jev-mcp-privacy/jev-mcp-privacy/`). Raw JSON, scripts and logs are there. W1 and W2 are the earlier research workers (upstream Jev MCP; FastMCP gate fit); their folders are `results/w1-upstream-jev-mcp/` and `results/w2-fastmcp-gate-fit/` beside it.
Package-internal references look like `jev-mcp dist/provider.js:269`; anyone can re-download the pinned artifact and open that line.

## How I reviewed
- Downloaded only: 9 npm tarballs and 78 PyPI wheels, by `curl` from registry URLs. No `npm install`, no `pip`, no builds, no imports.
- Every download matches its registry checksum. npm tarballs also match the lockfile and the registry's ECDSA signature (`openssl`). Wheels also match the hashes `uv` writes (`uv pip compile --no-build --generate-hashes`). Files: `EV/npm/npm-artifacts.json`, `EV/npm/npm-signature-check.json`, `EV/python/python-artifacts.json`, `EV/python/uv-hash-cross-check.json`. One row per artifact (URL, checksum, license, hooks, natives, entry points, scan counts, release dates, provenance, advisories): `EV/per-package-facts.tsv`.
- I read code by `grep` and by hand. Helpers: `gh api` (public data), `uv` with `--no-build` (resolver only), and Node's built-in type stripper (a text transform) to compare TypeScript source with built JavaScript.
- Limits. This is a static review. Native `.so` files were not decompiled. Provenance statements were decoded, not checked against the Sigstore root. "No advisory" means none on 2026-10-04.

## 1. Verdicts
| Package or group | Verdict | Reason |
|---|---|---|
| `@jkudish/jev-mcp` 0.13.0 | Adopt with conditions | One network target on the chosen route (`openrouter.ai`), no file writes, no telemetry. New, one maintainer, no provenance. See F1, F3, F4, F14. |
| `@jkudish/jev-agent-tools` 0.1.4 | Adopt with conditions | Same code quality. Ships one file with no source in git (F2). |
| `@typesafe-ai/sdk`, `@modelcontextprotocol/server`, `@modelcontextprotocol/core`, `zod` | Adopt | Loaded in stdio mode. All four have npm provenance. No network, file or process use in the loaded code (zod's JIT: F15). |
| `@modelcontextprotocol/node`, `@hono/node-server`, `hono` | Adopt (installed, not loaded) | Only loaded by `--http` mode (`jev-mcp dist/index.js:11-12`). `hono` 4.13.13 is hours old (F8). |
| `fastmcp` + `fastmcp-slim` 4.0.10 | Adopt with conditions | `fastmcp-slim` wheel equals the tag byte for byte (266 files). `fastmcp` is an empty meta wheel. See F4, F5, F6. |
| 30 other new FastMCP dependencies (list in section 4) | Adopt with conditions | No `.pth`, no install hooks, all wheels. CLI, OAuth and HTTP code is not on our path. See F8, F9. |
| `mcp` / `mcp-types` 2.2.0 (already locked) | Keep as is | Satisfy FastMCP's range; `jev-judge-mcp` 0.6.0 needs them (F7). Wheel hashes are in `uv.lock`; no hooks (`EV/python/python-mcp22-artifacts.json`). |
| `Faker` 40.40.0 | Adopt | No network, no file writes on the generation path (Q4). |
| `phonenumbers` 9.0.40 | Adopt (already locked) | Wheel hash is in `uv.lock`. No network or file writes (Q4). |
| `koroman` 1.0.16 (MIT) | Adopt with conditions | Pure code. Global dictionary state (F11). |
| `namefyi` 0.1.3 (MIT) | Adopt with conditions | Pure `engine.py`. New, 0 stars, no git tags (F12). |
| `korean-romanizer` 0.28.0 (GPL-3.0-or-later) | Do not adopt now | The code is clean. The license needs your decision first (Q3). |

## 2. Findings
| ID | Severity | Finding and evidence | Required condition |
|---|---|---|---|
| F1 | Medium | The two Jev packages are new and have no npm provenance. First releases 2026-09-17 (`jev-mcp`, 14 releases) and 2026-09-24 (`jev-agent-tools`, 5). One publisher account. Both tagged commits are not GitHub-verified (reason "unsigned"). Evidence: `EV/npm/npm-artifacts.json` (`has_attestations` false), `EV/github/jev-mcp-tag-ref.txt`. The tarball bytes do match the signed registry record, and the tags resolve to the commits npm names (`gitHead`). | Install from a lockfile with `npm ci --ignore-scripts`. Never `npx -y`. Re-read the diff at each bump. |
| F2 | Low | `jev-agent-tools@0.1.4` ships `dist/transports/siliconflow.js`, which calls `api.siliconflow.cn` (line 15). No source exists at the tag or in git history (`EV/github/siliconflow-src-commit-count.txt` = 0; `dist/` is in `.gitignore`). It is not imported (`dist/provider.js:1-5` has four drivers) and `package.json:14-19` exports only `.`. | Never deep-import. A test with a recording `fetch` must see only `openrouter.ai`. |
| F3 | Medium | Routing and endpoints come from env vars: `JEV_PROVIDER`, `JEV_OPENROUTER_BASE_URL`, `JEV_API_BASE_URL`, `TYPESAFE_*`, `CLOUDFLARE_*` (`jev-mcp dist/provider.js:195-213,269,310,367`). `JEV_MCP_TRANSPORT=http` or `--http` opens a listener (`dist/index.js:11`). A stray base-URL variable would send the key and the masked text elsewhere. | Pass the child exactly `JEV_PROVIDER=openrouter`, `OPENROUTER_API_KEY`, `JEV_MCP_MODEL`. Run `node <absolute path>/dist/index.js`. Set a neutral `cwd`. |
| F4 | Medium | Log paths. The child's stderr goes to the proxy's stderr by default (`fastmcp client/transports/stdio.py:262-263`; `mcp` 2.2.0 `client/stdio.py:345`). Jev writes one ready line (`dist/index.js:18`). FastMCP and the MCP SDK print tracebacks with exception text (`fastmcp server/server.py:1551`; `mcp` 2.2.0 `shared/jsonrpc_dispatcher.py:754`). Validation logs drop input values (`server.py:129-139`). | Pass `log_file=` for the child and send proxy stderr to a controlled sink. Gate code raises fixed-text errors only. Add a test that plants a synthetic name and searches all stderr for it. |
| F5 | Medium | The FastMCP banner runs an update check: GET `https://pypi.org/pypi/fastmcp/json` (`utilities/version_check.py:16,69`) from `log_server_banner` (`utilities/cli.py:205`) when `show_banner` is true (`server/mixins/transport.py:231-234`; default true, `settings.py:312`). It writes `version_cache.json` under the FastMCP data dir (`version_check.py:26,46-51`). No tool data, but a second destination and a file write. | `run(..., show_banner=False)` and `FASTMCP_CHECK_FOR_UPDATES=off` (`settings.py:326-337`). |
| F6 | Low | `import fastmcp` reads `.env` from the working directory (`settings.py:18,37-40`, `__init__.py:20`). Only `FASTMCP_*` keys are used. | Set `FASTMCP_ENV_FILE` to an empty file or start in a neutral directory. |
| F7 | Medium | MCP version. `jev-judge-mcp` 0.6.0 requires `mcp<2.3,>=2.2` (`EV/python/jev-judge-mcp-0.6.0-requires.json`), so the lock stays on 2.2.0 while it is present. W2's prototype ran on 2.3.0. Static check: 357 of 357 names `fastmcp-slim` imports from `mcp` exist in 2.2.0 (`EV/python/static-import-compat.json`). The CHE-86 set resolves with `mcp` 2.2.0 and the lock's other versions (`EV/python/che86-universal-lockkeep.txt`). Runtime is untested. | Re-run W2's synthetic probe against mcp 2.2.0 before acceptance. |
| F8 | Low | 13 of the reviewed artifacts are under 7 days old (`EV/release-age-days.json`). `hono` 4.13.13 (2026-10-04) is the newest; 4.13.12 is 4 days old and inside `^4.11.4`. | Accept knowingly, or step back one release. |
| F9 | Low | Native code in new wheels: `watchfiles` (Rust `.so`; reload feature only) and `caio` (three C `.so`; used by `aiofile`). Not decompiled. `caio` links libc only. | Wheels only. Set uv `no-build-package` for the new packages so no sdist is ever built. |
| F10 | Info | No install-time hooks. No `.pth` file in 78 wheels; every `RECORD` hash is consistent (`EV/python/python-wheel-scan*.json`). No npm `preinstall/install/postinstall`; `jev-mcp`'s `prepare` (`package.json:32`) runs only for local or git installs. Entry points: console scripts `fastmcp`, `faker`, `kroman`, `namefyi`; Faker's `pytest11` plugin adds an autouse session fixture (`faker/contrib/pytest/plugin.py:8-14`). | None. Faker's plugin loads in every pytest run of that environment. |
| F11 | Low | `koroman` keeps a module-level custom dictionary (`koroman/core.py:379-420`). | Never call `set_/add_custom_dictionary`. Call `romanize(text, use_custom_dictionary=False)`. |
| F12 | Low | `namefyi`: first release 2026-03-05, 3 releases, repo has 0 stars and no tags. `__init__.py:15-25` imports only `engine.py`. `api.py:19,38` opens `httpx` to `namefyi.com` if imported. `__version__` says 0.1.0 inside the 0.1.3 wheel. | Import only `namefyi.engine.romanize_korean`. Never install its extras. Test that `namefyi.api` is not in `sys.modules`. |
| F13 | Low | `koroman` GitHub `LICENSE` at HEAD has merge-conflict markers (`EV/github/lic-koroman/LICENSE`). The wheel's LICENSE is clean MIT. | If a notice is ever needed, copy the wheel's text. |
| F14 | Medium | The upstream skill registers `npx -y @jkudish/jev-mcp` as server `jev` (`skills/jev/SKILL.md:4-8`). It bypasses the proxy and the pin. Same as W1. | Strip that `mcpServers` block when copying the skill. |
| F15 | Info | Dynamic code. The MCP SDK's default validator (Ajv) uses `new Function` (`@modelcontextprotocol/server dist/ajvProvider-*.mjs:2594`) for server-side JSON Schema checks (`mcp-DIH4cS6P.mjs:1528`). Jev uses none of that (0 hits for `elicit`, `outputSchema` in `dist/*.js`). `zod` 4 compiles parsers with `new Function` and falls back without it (`zod v4/core/util.js:219`); the schemas are Jev's own. Jev's regex worker uses `eval: true` on a fixed program (`dist/lib.js:329-361`); the caller's pattern is only a `RegExp`, with a 1 s timer (`lib.js:169`). | Never pass caller-supplied JSON Schema to the SDK. |
| F16 | Info | Advisories: none for all 83 exact pins (9 npm, 74 PyPI), plus the six versions the lock keeps (OSV batch, npm bulk endpoint, GitHub Advisory Database). Positive controls (PyYAML 5.3, fastmcp 2.10.0, hono 4.0.0) return hits, so the queries work (`EV/advisories/`). | Re-run at implementation time. |
| F17 | Info | Telemetry. Only `opentelemetry-api` is in the closure, so spans are no-ops. Span attributes carry no arguments (`tools/base.py:489-493`). The default mode is `native` (`settings.py:154-175`). | Do not add `opentelemetry-sdk` or exporters. Set `FASTMCP_TELEMETRY_MODE=off`. |
| F18 | Info | Name and owner checks found no typosquat sign. `httpx2` and `httpcore2` (first release 2026-05-11): author Tom Christie, maintainer Pydantic Services Inc., repo `pydantic/httpx2` (1,516 stars), and `httpx2` is already in `uv.lock:605`. `griffelib` is by Timothée Mazzucotelli (repo `mkdocstrings/griffe`). `uncalled-for` is by Chris Guidry (repo `chrisguidry/uncalled-for`, PEP 740 attestation). `fastmcp` and `fastmcp-slim` list `PrefectHQ/fastmcp`. The `@jkudish` packages' registry `repository` URLs equal their GitHub repos. Evidence: `EV/github/repo-facts.tsv`, `EV/python/pypi-json/`. PyPI JSON does not show owner changes, so I could not check those. | None. |

## 3. Answers to the focus questions
**Q1. Can anything read, forward or log arguments or results besides the OpenRouter call?** I found nothing on the planned route, if the conditions above hold.
- The only call that carries tool content: POST `https://openrouter.ai/api/alpha/decisions` with `{model, state, questions}` (`jev-mcp dist/provider.js:269-279`). `state` and `questions` hold the tool arguments. Up to 3 attempts (`provider.js:27,174-193`). Errors are fixed text (`provider.js:280-293`). Headers: bearer key, fixed `HTTP-Referer` and `X-Title`.
- Other destinations exist but only if configured: `api.typesafe.ai`, `api.cloudflare.com`, `ai-gateway.vercel.sh`, `JEV_API_BASE_URL`, `JEV_OPENROUTER_BASE_URL` (all in `EV/npm/npm-static-scan.json`), and the unreachable `api.siliconflow.cn` (F2).
- No file writes, `child_process` or telemetry in any stdio-loaded npm code. The regex Worker runs in process. `@typesafe-ai/sdk` is used only for pure builders `choice/noul/score` (`index.mjs:313-345`).
- Stderr writes: the Jev ready line, and static `console.warn` text from the MCP SDK (`src-Cqbh3MYc.mjs:5385,7258-7262`). Python side: F4 and F5.
- Child environment. `mcp` 2.2.0 `client/stdio.py:40-55,75-86,128` (same code in 2.3.0) passes only `HOME, LOGNAME, PATH, SHELL, TERM, USER` from the parent, plus whatever `env=` adds. FastMCP forwards `env` unchanged (`fastmcp client/transports/stdio.py:255-260`). `keep_alive` defaults to true, so one child serves many calls (`:64-66`). `cwd` is inherited unless set. Node 24 has a `--use-env-proxy` option that reads `HTTP(S)_PROXY` (`node --help`), so do not pass proxy variables or `NODE_OPTIONS` to the child.
- With stdio, FastMCP starts no listener. Its `httpx2` use sits in HTTP transports, auth providers, OpenAPI and the update check (F5).

**Q2. `uv.lock` versus what fastmcp 4.0.10 requires.** The repository can stay on its pin, and must while `jev-judge-mcp` stays.
- `uv.lock`: `mcp` 2.2.0 (`uv.lock:991`), `mcp-types` 2.2.0 (`:1016`), `httpx2` 2.13.1 (`:605`), `requires-python >=3.14` (`:3`). `jev-judge-mcp` 0.6.0 (`:672`) is required by `packages/backfire/pyproject.toml:10` and `packages/credit-offers/pyproject.toml:10`.
- `fastmcp==4.0.10` requires `fastmcp-slim[client,server]==4.0.10`. `fastmcp-slim` requires `mcp<3.0.0,>=2.0.0`, `mcp-types<3.0.0,>=2.0.0`, `httpx2>=2.5.0`, `starlette>=1.0.1`, `pydantic[email]>=2.12.0`, `python-dotenv>=1.1.0`, `websockets>=15.0.1`, `uvicorn>=0.35`, `py-key-value-aio[filetree,keyring,memory]<0.5.0,>=0.4.4`, `pyyaml<7.0,>=6.0`, `authlib>=1.6.11`.
- `mcp` 2.3.0 itself needs `mcp-types==2.3.0` and `httpx2>=2.10.0`. `jev-judge-mcp` needs `mcp<2.3,>=2.2`.
- Experiment (`EV/python/with-jev-judge.txt`, `without-jev-judge.txt`): with `jev-judge-mcp`, uv resolves `mcp==2.2.0`; without it, 2.3.0. Adding FastMCP and the romanizers adds 36 new packages (`EV/python/closure-vs-repo-lock.json`). A fresh resolve prefers newer `cryptography`, `python-dotenv`, `websockets` and `tzdata`, but the set also resolves with the lock's versions (`EV/python/che86-universal-lockkeep.txt`). A full-workspace `uv lock --no-build` in a scratch copy failed on the existing sdist-only `bagit` (`EV/python/uv-lock-scratch-a.log`), so these are `uv pip compile --universal` results, not a real lock. No advisories for the lock's versions (`EV/advisories/lock-versions-osv.json`).

**Q3. Romanizer license facts.** Facts only; I draw no legal conclusion.

| | `namefyi` 0.1.3 | `koroman` 1.0.16 | `korean-romanizer` 0.28.0 |
|---|---|---|---|
| Shipped text | MIT, "Copyright (c) 2026 FYIPedia" | MIT, "Copyright (c) 2025 Donghe Youn (Daissue)" | `LICENSE` (14 lines): "Copyright (C) 2020 Ilkyu Ju", GPL "either version 3 … or (at your option) any later version". `COPYING`: GPLv3 text, 674 lines. No GPL header in the `.py` files. |
| Registry metadata | MIT | MIT classifier | `License: GNU GPLv3`; classifier "GPLv3+" |
| GitHub license field | MIT; HEAD file equals wheel | NOASSERTION; HEAD file has conflict markers | NOASSERTION; HEAD files equal the wheel's |
| Source vs wheel | 4 of 5 files equal HEAD; `mcp_server.py` differs (docstring, not imported) | `core.py` equals tag `python-v1.0.16` except CRLF line ends | all 5 files equal tag `v0.28.0` |
| Maintenance | 3 releases, 0 stars, pushed 2026-07-19 | 5 releases, 10 stars, pushed 2026-05-28 | 15 releases since 2020, 115 stars, pushed 2026-07-24 |
| Code safety | Pure `engine.py`; no I/O (F12) | Pure; global store (F11) | Pure `Romanizer(text)`; no globals; CLI only prints |
- MIT text: "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software." Installed only, this repository holds no copy. If code is copied, the notice travels with it.
- GPLv3 text in `COPYING`: you "may make, run and propagate covered works that you do not convey, without conditions" (line 164); "convey" means propagation that lets others "make or receive copies" (99-100); §5(c) "You must license the entire work, as a whole, under this License" for a work based on the Program (222); an "aggregate" of separate works is treated apart (235). FSF's FAQ (`gnu.org/licenses/gpl-faq.html`, fetched 2026-10-04) says: "Linking a GPL covered work statically or dynamically with other modules is making a combined work based on the GPL covered work. Thus, the terms and conditions of the GNU General Public License cover the whole combination." It also says private modification and use need no release. I did not assess how that applies to a Python `import`. Excerpts: `EV/licenses/`.
- This repository: Apache License 2.0 (`LICENSE:1-3`; `README.md:31-33`). The GitHub repository is public, and `README.md:24` describes optional copied packages (`plugins:distribute`). Whether Python dependencies would ever ship inside those packages is unknown to me. FSF's license list calls Apache-2.0 "compatible with version 3 of the GNU GPL".
- Notice policy, `AGENTS.md:98-103`: `licenses/third-party-notices.md` lists code "actually copied, ported or vendored", with source repository, exact revision and the shipped license. "Installed dependencies do not get an entry solely for being installed." `AGENTS.md` has no rule on GPL dependencies.

**Q4. Do Faker, phonenumbers or the romanizers write files, cache to disk or use the network?** Not on their normal paths.
- Faker: no HTTP client, socket or `urllib` use (scan: 0 hits). File writes exist only in `faker/sphinx/documentor.py:90-164` (docs builder, not imported). `eval` appears only in `faker/sphinx/docstring.py:199`. Locale modules load by `import_module` from names that `pkgutil` lists inside the package (`faker/factory.py:67-110`). The one cache in its core is in memory (`lru_cache`, `factory.py:66`). Its debug logs name only locale and module (`factory.py:76-106`). The scan found no file write outside the docs builder.
- phonenumbers: no network, no writes. Region data loads lazily by `__import__("region_%s")` from its own `data/` package (`phonenumbers/data/__init__.py:22`).
- `namefyi`: `import namefyi` loads only `engine.py` (`unicodedata`). `namefyi.api` is the one network module (F12).
- `koroman`, `korean-romanizer`: no file, network, subprocess or logging calls in library code; `korean-romanizer`'s `print` is in `cli.py:13` only.

## 4. Final pins
Install wheels only. The wheel hash is the one for Linux x86_64 and Python 3.14, or the pure wheel. `uv lock` will also record other platforms; native wheels for other platforms are not reviewed.

**npm** (9 packages; W1's `package-lock.json` in `results/w1-upstream-jev-mcp/attempt-1/` has the same integrity values):

| Package | Version | Tarball integrity (sha512, verified) | Source |
|---|---|---|---|
| `@hono/node-server` | 1.19.17 | `sha512-dSneS5qhiauZWGDCeK4o695Xd9nUNjviSZCMQrj10eetr8Uln1ucn6bbphOM6UynAMMtNIzZNSpL9vnASJwrPQ==` | npm registry; honojs/node-server @ v1.19.17 |
| `@jkudish/jev-agent-tools` | 0.1.4 | `sha512-0or+T8XCU8jLwhBA5t0x6E/51fpa/3iYDe8i2CCQaME317TBRrNU5406S/nD+LRbZrTFjxuPdT64rzbJeKQmCw==` | npm registry; jkudish/jev-agent-tools @ 7a9d1c4 (v0.1.4) |
| `@jkudish/jev-mcp` | 0.13.0 | `sha512-0fFOAJwlsntMdHu4+t40H4BObOowfqVsZdMnU1tbqIHojbWotRia8quh8/SjEtwpC0CbemZF9TpBDbFNBhnRGw==` | npm registry; jkudish/jev-mcp @ 5e0ca5c (v0.13.0) |
| `@modelcontextprotocol/core` | 2.3.0 | `sha512-09BHFaNVBe5pB2AhzCfLj0cqmsKLERvZQ4FblzP90UMGLaXVqdZPByFjURwsUYCmxonUW2yAwgTTvle+8O2/8w==` | npm registry; modelcontextprotocol/typescript-sdk (provenance) |
| `@modelcontextprotocol/node` | 2.1.1 | `sha512-EY92OAXN2xYL7tNS/MVsWJW1v8VHAPwl9B4Ca3pCrjmvqyC+S1C/6UHsMxF2GoFPraS5Yyg56vFz9brVpFojMA==` | npm registry; modelcontextprotocol/typescript-sdk (provenance) |
| `@modelcontextprotocol/server` | 2.3.0 | `sha512-+6b0LdsQLmHsvS7J6sQJ4weTpzUn61fU1JKS+321/+IyDYoHW5CR2Tgqcs6GgAAQvlesCo6yX3xttgmx+XGtJw==` | npm registry; modelcontextprotocol/typescript-sdk (provenance) |
| `@typesafe-ai/sdk` | 0.6.0 | `sha512-IddX+Q0XM+VagOUZFeP7wZjaO4SHMdvnh2zEBdrZZnXedWI3BNK1lKhMx3ayrkFWvVLbVcUHJy6AVZlY+e6Jaw==` | npm registry; typesafe-ai/typesafe-sdk-js @ v0.6.0 |
| `hono` | 4.13.13 | `sha512-CQ46U0ZkAGmbT/4UxdzzGJpacP2IeKgY4a5/tOI9AABbpOMfK739wfDXmv1usCk+3RkKj1hQy4/fjhiwa2xlrA==` | npm registry; honojs/hono @ v4.13.13 |
| `zod` | 4.6.5 | `sha512-v5l/aFXZQeai4awLbOpSoHecE9UiMrnfx75tEXLjNonXVARxQ5mOeipTjROUchszUNCqnE+hqAMujRsRHsut2Q==` | npm registry; colinhacks/zod (provenance) |

**Python, new to the repository** (35; pick one romanizer; `korean-romanizer` excluded; the other 41 resolved packages, including `mcp`, `mcp-types` and `phonenumbers`, stay as in `uv.lock`):

| Package | Version | Wheel sha256 (verified against PyPI and uv) | Wheel tag |
|---|---|---|---|
| `aiofile` | 3.12.3 | `5c1bcc9e929c50834608e8cc1a4cc1d7503eb60c15a535b779fd39e2f372c017` | py3-none-any |
| `authlib` | 1.8.0 | `88aebbd9af6757e14e912d5dc007ae1dc1f3e27e3b2152ce7c552ee2c3b3c121` | py3-none-any |
| `beartype` | 0.22.9 | `d16c9bbc61ea14637596c5f6fbff2ee99cbe3573e46a716401734ef50c3060c2` | py3-none-any |
| `cachetools` | 7.2.0 | `3045213f186b89fdd95d94441354c4bd87c570b7a38d8c3fd1d9dd37f6dc90d8` | py3-none-any |
| `caio` | 0.12.9 | `4a69de19ef8780ea67f5fffa6fed95af32ed4c036e338a361307314306ac816c` | cp314/cp314 manylinux x86_64 |
| `cyclopts` | 5.1.1 | `ff0da67b2d2d8fe716d20ab82c698277ef30a8fb75d24e9b38a06f56c44931fd` | py3-none-any |
| `dnspython` | 2.8.0 | `01d9bbc4a2d76bf0db7c1f729812ded6d912bd318d3b1cf81d30c0f845dbf3af` | py3-none-any |
| `docstring-parser` | 0.18.0 | `b3fcbed555c47d8479be0796ef7e19c2670d428d72e96da63f3a40122860374b` | py3-none-any |
| `email-validator` | 2.3.0 | `80f13f623413e6b197ae73bb10bf4eb0908faf509ad8362c5edeb0be7fd450b4` | py3-none-any |
| `exceptiongroup` | 1.3.1 | `a7a39a3bd276781e98394987d3a5701d0c4edffb633bb7a5144577f82c773598` | py3-none-any |
| `faker` | 40.40.0 | `cd45ebdd1363f92a45740ac49945e49fa18f7e10771884a83c796a235550d7b7` | py3-none-any |
| `fastmcp` | 4.0.10 | `1f8462e3d97394a637e1b0f1eaea0002da661c8d98000ad43f0aa3fa1ff523e8` | py3-none-any |
| `fastmcp-slim` | 4.0.10 | `c2abd40302b8f06b0291413cf537d57bc0f171b5fd98af5cfef3b2b6b506122f` | py3-none-any |
| `griffelib` | 2.3.0 | `1b8f9cd525681c26b1d6d574faa1371651e8459ca51d209684f50b8096ae06e0` | py3-none-any |
| `jaraco-classes` | 3.4.0 | `f662826b6bed8cace05e7ff873ce0f9283b5c924470fe664fff1c2f00f581790` | py3-none-any |
| `jaraco-context` | 6.1.2 | `bf8150b79a2d5d91ae48629d8b427a8f7ba0e1097dd6202a9059f29a36379535` | py3-none-any |
| `jaraco-functools` | 4.6.0 | `99e3dc0060c5cbe8fcd1cdb36258e2a65ca40f1566b2033b12abb1bb44dd3c30` | py3-none-any |
| `jeepney` | 0.9.0 | `97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683` | py3-none-any |
| `joserfc` | 1.7.5 | `add2c2c84e8373b084d526a8b53daba5d7a513a118cd2dcd9fc9f979d0922159` | py3-none-any |
| `jsonref` | 1.1.0 | `590dc7773df6c21cbf948b5dac07a72a251db28b0238ceecce0a2abfa8ec30a9` | py3-none-any |
| `jsonschema-path` | 0.5.0 | `2790a070bc7abb08ea3dbe4d340ece4efadf639223001f020c7503229ba068e2` | py3-none-any |
| `keyring` | 25.7.0 | `be4a0b195f149690c166e850609a477c532ddbfbaed96a404d4e43f8d5e2689f` | py3-none-any |
| `koroman` | 1.0.16 | `c718185d3c2dd713caf58c66c09804ffd8a49641da5cca0b25d938e66b79c6fa` | py3-none-any |
| `more-itertools` | 11.1.0 | `4b65538ae22f6fed0ce4874efd317463a7489796a0939fa66824dd542125a192` | py3-none-any |
| `namefyi` | 0.1.3 | `a5ef20c18938f806bcbe921faaf47641bb3e781d1c23f00149e318f85f673e36` | py3-none-any |
| `openapi-pydantic` | 0.6.0 | `8bd6d548a250da37db96f461bcd52b3468e8834ad7d6db14b00a6b2ebbd163a3` | py3-none-any |
| `pathable` | 0.6.0 | `82c4ca6c98c502ad12e0d4e9779b6210afee93c38990988c8c5d1b49bdcdf566` | py3-none-any |
| `platformdirs` | 4.12.3 | `080f3b39423b5abfca9a23d84c4e9795f54d395cd8459867a8ded44084fcd5f8` | py3-none-any |
| `py-key-value-aio` | 0.4.6 | `820b30c7959fc738ea3d00160cdb10cd258f51e38737b2add530defeea1ded77` | py3-none-any |
| `pyperclip` | 1.11.0 | `299403e9ff44581cb9ba2ffeed69c7aa96a008622ad0c46cb575ca75b5b84273` | py3-none-any |
| `pywin32-ctypes` | 0.2.3 | `8a1513379d709975552d202d942d9837758905c8d01eb82b8bcc30918929e7b8` | py3-none-any |
| `rich-rst` | 2.2.0 | `1ea1c43813dc4a8d86475fce27ffb74e0ada3d4656c9f8130ba2a59868055fe9` | py3-none-any |
| `secretstorage` | 3.5.0 | `0ce65888c0725fcb2c5bc0fdb8e5438eece02c523557ea40ce0703c266248137` | py3-none-any |
| `uncalled-for` | 0.4.0 | `16c4bb3337532e4bd5569adc192285976f3ad5305402256d34c67a12b5c968bd` | py3-none-any |
| `watchfiles` | 1.3.0 | `b5768b49e426fd5b550b012c866db347cdf15c398ef98dc557b6e6b72fa74cd1` | cp310/abi3 manylinux x86_64 |

## 5. Reconciliation with earlier research
Agreements:
- W1's 9-package closure, integrity values and "no install scripts, no telemetry, no file writes" all hold. W1's retained copies are byte-identical to my tarballs (22 + 25 files; `EV/npm/reconcile-w1-copies.json`). Its line references are valid.
- W2's 72 shared wheel hashes are identical to mine (`EV/python/reconcile-w2.json`). No `.pth` files. License findings for the three romanizers match, including the koroman HEAD file. No advisories for 4.0.10.
Differences and additions:
- The earlier scratch runs executed dependency code before this review. W2 installed 77 distributions, built the `kroman` sdist and ran probes (W2 `report.md`, "Security review sequence and limits"). W1 started the `jev-mcp` server and probe scripts after `npm install --ignore-scripts`, with a dummy key and replaced `fetch` (`report-v2.md:66,216-218`). I found nothing harmful in what they ran, but neither run captured network traffic, so "no unexpected traffic" is unproven. Their `/tmp` scratch folders are disposable.
- New: `siliconflow.js` has no source in git (F2); the update check (F5); `.env` read (F6); the `mcp<2.3` cap (F7, W2's open question); fresh releases (F8); koroman global state (F11); `namefyi.api` (F12); Faker's pytest plugin (F10).
- W2 listed six compiled packages. `caio` and `websockets` also have compiled cp314 wheels; W2 reviewed the pure fallbacks. I reviewed the compiled ones (`websockets` is already locked).
- Closure size: W2's Linux closure had 68 distributions. Against `uv.lock` only 35 are new for the adopted set (including `pywin32-ctypes`, win32 only, found by the universal resolve).

## 6. Open questions
1. Do you accept GPL-3.0-or-later for `korean-romanizer`? Until then use `koroman` or `namefyi` (or neither).
2. Does `jev-judge-mcp` 0.6.0 stay (credit-offers uses it)? That decides mcp 2.2.0 versus 2.3.0 (F7).
3. Could `plugins:distribute` ever bundle the Python dependencies?
4. OpenRouter's retention of the masked text was not reviewed.
5. Do you want the npm closure vendored with a lockfile, and which Node (>=22) runs it?
