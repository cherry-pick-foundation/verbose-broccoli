# R3 security review: Vale 3.23.0 and qmd 2.8.3

Review date: 2026-09-30

This is a source-only review of the exact clones and published artifacts named in the task. I did not install, build, test, or run either tool. I downloaded release data and npm tarballs only into `work-R3-vale-qmd/`.

Source paths below are relative to `vale-v3.23.0/`, `qmd-v2.8.3/`, or the named extracted package under `work-R3-vale-qmd/`. A high finding can directly compromise private data or execute untrusted code in the planned use. A medium finding needs a realistic configuration or dependency condition. A low finding is outside the planned path, is already reduced by a planned control, or has limited impact.

## Summary

| Tool | High | Medium | Planned-use verdict |
|---|---:|---:|---|
| Vale 3.23.0 | 0 | 3 | Usable only with explicit config, output, NLP, and symlink controls. Those controls leave no high or medium finding in the stated offline regex-only use. |
| qmd 2.8.3 | 0 | 5 | Usable only with a protected cache, a pinned embedding artifact, native fallback disabled, restricted commands, and a trusted local MCP client. Five medium findings stand until those controls are applied. |

## Vale 3.23.0

Reviewed source: tag `v3.23.0`, commit `2753160f8e5835976340183ddc4a91ed10b7d3ed`. The planned path is the Linux amd64 release binary installed by mise, then offline linting of private Markdown with a repository config and local regex rules.

### 1. Install and build steps

**V-L1 — Low: installation writes version-manager state outside the Wiki, but the release archive has no install hook.** This is low because the write is expected mise state and happens before private pages are read.

- The release configuration builds `linux`/`amd64` and packages an archive; it does not define a binary post-install action (`.goreleaser.yml:31-42`, `.goreleaser.yml:94-111`).
- The downloaded archive contains only `LICENSE`, `README.md`, and `vale`. Evidence: `tar -tzf work-R3-vale-qmd/vale_3.23.0_Linux_64-bit.tar.gz` printed those three entries.
- The exact mise registry entry maps `vale` to Aqua package `vale-cli/vale` (`mise-v2026.9.16/registry/vale.toml:1`; `mise-v2026.9.16/vendor/aqua-registry/registry.yml:101502-101507`). Mise stores downloads and installed versions below its XDG cache/data directories, not the Wiki (`mise-v2026.9.16/crates/mise-util/src/env.rs:142-143`, `mise-v2026.9.16/crates/mise-util/src/env.rs:157-176`).
- The project release workflow invokes GoReleaser on a GitHub release event (`.github/workflows/main.yml:3-26`). Those build hooks run at publication, not when the downloaded archive is installed.

### 2. Downloaded binaries, packages, and integrity

**V-L2 — Low: `vale sync` accepts remote package archives without a package-specific checksum or signature.** It is low for this plan because `vale sync` and remote packages are expressly excluded. If someone later runs `sync`, the risk becomes medium because styles control lint logic and can contain scripts.

- `vale sync` uses a raw GitHub registry by default (`cmd/vale/library.go:5-29`). It downloads an archive with `http.Get`, copies it to a temporary file, and extracts it without checking a digest or signature (`cmd/vale/api.go:73-100`; `cmd/vale/sync.go:121-184`).
- Sync may resolve recursive package dependencies and overwrite files under `StylesPath` (`cmd/vale/sync.go:35-92`, `cmd/vale/sync.go:204-219`). Version resolution can call a package release feed (`cmd/vale/pkgver.go:70-130`, `cmd/vale/pkgver.go:133-174`).
- Extraction rejects traversal and over-large archive members, which limits archive damage but does not authenticate the package (`internal/system/zip.go:12-78`).
- The planned release binary has a SHA-256 entry. The downloaded value was `cc35445a45186b8f0b01e11c01359694cf941e72cf6ab0fc44774f0e54c9d5fc`, and the same value appears in `work-R3-vale-qmd/vale_3.23.0_checksums.txt`. The Aqua record selects GitHub release checksums with `sha256` (`mise-v2026.9.16/vendor/aqua-registry/registry.yml:101769-101784`). Signing limits are covered in point 8.
- Ordinary lint does not invoke the sync downloader. With `sync`, remote styles, and `NLPEndpoint` excluded, no model or data download is reached by the planned lint command (`cmd/vale/sync.go:15-32`; `internal/nlp/http.go:20-72`).

### 3. Network calls, telemetry, and result disclosure

**V-M1 — Medium: several output modes can repeat the matched private text.** This directly conflicts with the planned output rule. It is medium, not high, because the built-in `line` and normal CLI output paths emit the rule message rather than the stored match, and the repository controls its rule messages.

- An alert retains the matching text in its public `Match` field (`internal/core/alert.go:19-35`). JSON serializes the full alert (`cmd/vale/json.go:10-23`, `cmd/vale/json.go:55-70`), and custom templates receive alerts containing that field (`cmd/vale/custom.go:14-66`).
- A rule can also insert the match into its message through format directives (`internal/check/definition.go:292-330`; `internal/core/util.go:153-163`).
- The built-in `line` renderer and normal CLI renderer output `alert.Message`, not `alert.Match` (`cmd/vale/line.go:12-38`; `cmd/vale/color.go:51-84`).
- Required control: use `--output=line`; use literal local rule messages with no match-format directive; run a synthetic canary check that fails if the canary appears in stdout or stderr. Do not use JSON or a custom output template for private pages.

**V-M2 — Medium: an `NLPEndpoint` receives the full text in an HTTP POST request when configured.** This can disclose the private Wiki. It is medium because no endpoint is built in, but Vale always loads a global config unless `--no-global` is set, even when `--config` is supplied.

- `NLPEndpoint` is a config field and is parsed from INI (`internal/core/config.go:243`; `internal/core/ini.go:414-420`).
- The NLP client sends text and language as an HTTP POST query, and the prose/provider paths invoke it (`internal/nlp/http.go:20-72`; `internal/nlp/prose.go:169-200`; `internal/nlp/provider.go:289-302`).
- Vale loads the XDG global config in addition to another config unless `--no-global` is set (`internal/core/source.go:102-174`). The flag is documented in `cmd/vale/flag.go:21-51`.
- Required control: invoke `vale --config <absolute-repository-config> --no-global --output=line ...`; keep `NLPEndpoint` absent from that config and unset `VALE_CONFIG_PATH`. Network-level egress blocking is a useful backstop for the promised offline run.

No telemetry or analytics client was found in the Go runtime source. Evidence: `rg -n -i 'telemetry|analytics|sentry|opentelemetry|posthog|segment\.io|mixpanel' vale-v3.23.0 --glob '*.go' --glob '!**/*_test.go'` returned no matches (exit 1). This negative search does not prove that an externally configured NLP endpoint is safe; that path is the finding above.

### 4. Code execution and shell-outs

**V-L3 — Low: styles can execute Tengo rules and fix actions, while non-Markdown processors can shell out.** It is low for the stated use because the approved styles are local regex-only rules, input is Markdown, and neither actions nor fixes are needed. Treat any future style change as code review, not data-only review.

- A `script` rule compiles and runs Tengo with only `text`, `fmt`, and `math` imports and a two-second timeout; no OS module is exposed (`internal/check/script.go:68-110`, `internal/check/script.go:113-166`).
- Scripted fix actions also run Tengo with restricted imports, but this action path has no matching execution timeout (`internal/check/action.go:201-254`).
- AsciiDoc and reStructuredText processors start helper processes (`internal/lint/proc_pool.go:13-61`). Markdown selects the internal Markdown path instead (`internal/lint/lint.go:275-280`).
- Required control: allow only reviewed `existence`/`occurrence`-style YAML rules. Do not allow `script` rules, scripted actions, `vale fix`, `--apply`, or non-Markdown input in this job.

### 5. Files read and written outside the working folder

**V-M3 — Medium: a lint target can escape the Wiki through a symbolic link.** This may read and report on an unintended private or system file. It is medium because an attacker or mistaken checkout must first place a symlink in the selected input tree.

- Vale resolves a symlink and deliberately follows it, including a link to a directory, before walking the result (`internal/system/walk.go:11-49`). The lint path uses this walker and then reads the selected file with `os.ReadFile` (`internal/lint/lint.go:191-240`; `internal/core/file.go:119-148`).
- Vale's own security policy treats reading outside intended directories as in scope (`SECURITY.md:31-41`).
- Required control: reject symlinks before linting, or pass a generated list of verified regular Markdown files whose resolved paths remain below the Wiki root. Do not give Vale a directory tree containing unchecked links.

Normal linting does not write the pages. Writes are reached by `fix --apply`, `sync`, and optional CPU or memory profiling (`cmd/vale/apply.go:185`; `cmd/vale/sync.go:15-32`; `cmd/vale/profile.go:10-66`). Keep `VALE_CPUPROFILE` and `VALE_MEMPROFILE` unset. Global config/style reads default to XDG config/data paths and may be redirected by `VALE_STYLES_PATH` (`internal/core/config.go:134-163`); `--no-global` prevents the global config from joining the planned run (`internal/core/source.go:102-174`).

### 6. Credentials

No runtime credential, keychain, or token lookup was found on the planned lint path. Repository release automation uses GitHub secrets, but those are publication-time credentials (`.github/workflows/main.yml:3-26`). The network paths above accept public URLs rather than loading a credential store. Keep the offline job's environment minimal and do not use `vale ls-vars`, which prints Vale-related environment/config values (`cmd/vale/command.go:342-364`).

### 7. Published advisories for 3.23.0

No direct advisory was found for the exact Go module/version as of the review date. This is not a guarantee that no undisclosed issue exists.

- `POST https://api.osv.dev/v1/query` with package `github.com/vale-cli/vale/v3`, ecosystem `Go`, and version `3.23.0` returned `{}`; captured as `work-R3-vale-qmd/osv-vale.json`.
- [GitHub Advisory Database search for the exact Go package](https://github.com/advisories?query=ecosystem%3Ago+package%3Agithub.com%2Fvale-cli%2Fvale%2Fv3) returned “No results matched your search”; captured at `work-R3-vale-qmd/ghsa-vale.html:1025`.
- The Aqua registry record has package and checksum metadata but no advisory feed or advisory field (`mise-v2026.9.16/vendor/aqua-registry/registry.yml:101502-101507`, `mise-v2026.9.16/vendor/aqua-registry/registry.yml:101769-101784`). Package-registry advisory coverage is therefore unverified beyond OSV and GitHub.
- Upstream only promises security fixes for the latest release, not continued support for 3.23.0 (`SECURITY.md:3-11`).

### 8. Release signing, provenance, and checksums

**V-L4 — Low: the release checksum is not independently authenticated.** This is low because mise verifies a SHA-256 value and GitHub transport protects ordinary download corruption. A GitHub release compromise could replace both the binary and same-channel checksum.

- `sha256sum work-R3-vale-qmd/vale_3.23.0_Linux_64-bit.tar.gz` returned `cc35445a45186b8f0b01e11c01359694cf941e72cf6ab0fc44774f0e54c9d5fc`, matching the published checksum file.
- The reviewed mise Aqua backend calls checksum verification on the downloaded archive (`mise-v2026.9.16/src/backend/aqua.rs:2702-2779`), and the Vale Aqua entry selects the SHA-256 checksum file (`mise-v2026.9.16/vendor/aqua-registry/registry.yml:101769-101784`). Mise itself was not run.
- `https://github.com/vale-cli/vale/releases/download/v3.23.0/vale_3.23.0_checksums.txt.sig` returned HTTP 404; the captured body is nine bytes, `Not Found`. No release signature or attestation was established in this review.
- `git cat-file -t v3.23.0` returned `commit`, so the tag is lightweight. `git verify-commit 2753160f...` found an RSA signature for key `44B5B5D07573AFC1BEA09E54B44A6E0381723797` but could not verify it because the public key was absent. This source signature therefore was not independently established.
- The release workflow uses floating major action tags (`.github/workflows/main.yml:3-26`), so the checksum does not make the build reproducible from this clone alone.

### Vale verdict and required settings

No high finding stands. Three medium findings stand until the run:

1. uses `--config <absolute-path> --no-global --output=line` with literal, non-interpolating messages;
2. keeps `NLPEndpoint` absent, unsets `VALE_CONFIG_PATH`, and runs without network egress; and
3. rejects symlinks or supplies only verified regular files below the Wiki root.

Also keep `VALE_CPUPROFILE`, `VALE_MEMPROFILE`, and `VALE_STYLES_PATH` unset; allow only reviewed local regex rules; and prohibit `sync`, scripts, actions, fixes, and native-format processors. With these controls, no high or medium finding remains for the stated use.

## qmd 2.8.3

Reviewed source: annotated tag `v2.8.3`, commit `facd35e01359e59d938bc9418e93fb9318addee3`. The planned path uses the pinned npm package with `npm ci --ignore-scripts`, named indexes, cache-local XDG paths, selected CLI commands, or the stdio MCP server.

### 1. Install scripts, build hooks, and native modules

**Q-L1 — Low: qmd and transitive native packages have lifecycle scripts, but `npm ci --ignore-scripts` suppresses them.** It is low only while that install flag remains mandatory. Removing the flag would make the node-llama post-install path a medium code-execution risk.

- qmd declares `prepare` and build scripts, and lists `node-llama-cpp`, `better-sqlite3`, and `sqlite-vec` dependencies (`package.json:28-45`, `package.json:58-78`). The prepare script installs repository Git hooks and the build script invokes TypeScript and Git metadata commands (`scripts/install-hooks.mjs:8-17`; `scripts/build.mjs:9-72`). These scripts are publisher/developer hooks; the packed package has already-built `dist` files.
- `node-llama-cpp` 3.20.0 declares `postinstall`, which loads or builds the native runtime (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/package.json:44-51`; `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/cli/commands/OnPostInstallCommand.js:12-59`).
- The inspected `better-sqlite3` 13.0.3 tarball has no lifecycle script and ships prebuilt `.node` files, including Linux x64. The inspected `node-llama-cpp-linux-x64` 3.20.0 tarball ships `.node` and `.so` files. The `sqlite-vec` umbrella package has platform-specific optional dependencies. Evidence: `tar -tf` listings of the four tarballs under `work-R3-vale-qmd/npm-artifacts/`.
- No first-run downloader was found in the inspected `better-sqlite3` or `sqlite-vec` packages. With lifecycle scripts disabled, npm downloads their package/prebuilt tarballs during `npm ci`; qmd's later executable-download path is node-llama, covered in Q-M4.
- The exact native versions installed by verbose-broccoli remain unverified because qmd uses dependency ranges and this review was forbidden from reading the consuming repository's lockfile. The reviewed tarballs are the current matching registry artifacts, not proof of that lock resolution.
- qmd imports web-tree-sitter and loads WASM parsers for supported code, while Markdown stays on its regex path (`src/ast.ts:10-18`, `src/ast.ts:50-57`, `src/ast.ts:195-235`). Native tree-sitter package install scripts are therefore not reached by the planned Markdown parsing path.
- npm documents that `ignore-scripts` prevents package lifecycle scripts: [npm `ignore-scripts` configuration](https://docs.npmjs.com/cli/v11/using-npm/config#ignore-scripts).

### 2. Model and binary downloads, sources, and integrity

**Q-M1 — Medium: model files are fetched from mutable Hugging Face `main` URLs without a pinned digest or signature.** The indexed text stays local, but loading an unauthenticated artifact into the native model runtime is a supply-chain risk. It is medium because a user must request a model operation and the file must still pass the minimal GGUF check.

- qmd turns an `hf:` model URI into a `https://huggingface.co/.../resolve/main/...` URL and performs HEAD/download requests (`src/llm.ts:341-361`, `src/llm.ts:495-552`). It validates the GGUF magic bytes, not a cryptographic digest or publisher signature (`src/llm.ts:363-445`, `src/llm.ts:1093-1104`).
- The underlying node-llama downloader also defaults to `verify: false` and supports Hugging Face or model endpoint overrides (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/utils/resolveModelFile.js:78-167`; `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/utils/modelDownloadEndpoints.js:2-25`).
- Required control: pre-download the exact Qwen GGUF once in an approved retrieval step, record and verify an independently reviewed SHA-256, store it read-only in the cache, and set `QMD_EMBED_MODEL` to that local file. Do not rely on a mutable `hf:` URL at production run time.

**Q-M2 — Medium: search paths can fetch generation or reranking models without a separate model-download request.** This breaks the stated user-initiated download boundary. It is medium because command choice and environment settings fully control it.

- The default embedding model is `embeddinggemma-300M`, not Qwen. qmd also defines separate generation and reranking defaults; `QMD_EMBED_MODEL`, `QMD_GENERATE_MODEL`, and `QMD_RERANK_MODEL` override them (`src/llm.ts:279-327`). The source gives the exact Qwen example `hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf` (`src/llm.ts:279-285`).
- `qmd pull` resolves and downloads embed, generation, and rerank models (`src/cli/qmd.ts:4660-4679`).
- CLI `qmd search` is lexical and does not load a model (`src/cli/qmd.ts:2798-2828`). CLI `qmd vsearch` calls vector search with query expansion, which can load the generation model before embedding (`src/cli/qmd.ts:2845-2884`; `src/store.ts:5757-5812`). There is no CLI switch that disables expansion on `vsearch`.
- In MCP, a plain query is treated as expansion and reranking defaults on (`src/mcp/server.ts:285-290`, `src/mcp/server.ts:316-397`). Typed `lex:`/`vec:` searches and `rerank: false` avoid the generation/rerank paths; `lex:` avoids all models, while `vec:` uses only the embedding model.
- Required control: set the explicit local `QMD_EMBED_MODEL`; do not run `qmd pull`; use CLI `search` for lexical work; do not use CLI `vsearch` if only one model may exist. For MCP, send typed `lex:` or `vec:` requests with `rerank: false`. If `vsearch` is required, separately approve, pin, and pre-provision its generation model.

### 3. Network calls, telemetry, and MCP transport

**Q-M3 — Medium: CLI JSON and MCP return private snippets or documents to their caller; optional MCP HTTP mode has no application authentication.** The stdio server does not itself expose a network port, but each caller becomes a data-export boundary. This is medium until the coordinator proves that the consumer is local and does not forward output.

- Search JSON contains a snippet by default and can contain a full body (`src/cli/qmd.ts:2447-2527`). MCP resources and tools can return full document content, search snippets, and index paths/status (`src/mcp/server.ts:166-234`, `src/mcp/server.ts:316-397`, `src/mcp/server.ts:404-580`).
- Default `qmd mcp` uses `StdioServerTransport`; it does not listen on a socket (`src/mcp/server.ts:800-827`; `src/cli/qmd.ts:4769-4843`).
- `--http` is a separate opt-in transport. It defaults to localhost and checks origin/host, but the implementation warns that it has no authentication (`src/mcp/server.ts:840-855`, `src/mcp/server.ts:939-970`, `src/mcp/server.ts:1080-1113`). HTTP logging includes query or path previews (`src/mcp/server.ts:898-918`).
- Required control: keep CLI stdout/stderr in a local, access-controlled process and do not retain snippets in shared logs. Use stdio only, never `--http` or `--daemon`, and connect only to a verified local/offline MCP host whose logging and upstream model settings cannot transmit tool data. If that client boundary cannot be proved, use the CLI instead.

Other runtime network paths are the Hugging Face model requests and node-llama native fallback described in points 2 and 4. A source-wide search found no analytics/telemetry client: `rg -n -i 'telemetry|analytics|sentry|opentelemetry|posthog|segment\.io|mixpanel' qmd-v2.8.3/src qmd-v2.8.3/bin work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist --glob '*.ts' --glob '*.js'` returned no matches (exit 1). This does not cover the downstream MCP client.

### 4. Code execution, shell-outs, and config trust

**Q-M4 — Medium: first model use may download or locally compile node-llama native code even though npm install scripts were suppressed.** `npm ci --ignore-scripts` is not enough because qmd explicitly permits a runtime fallback. This is medium because a simple CPU-mode control disables that branch.

- qmd probes whether the `node-llama-cpp` package directory is writable. In the normal writable case it requests `build: "auto"` and `skipDownload: false`; CPU-forced mode uses the no-build path (`src/llm.ts:125-144`, `src/llm.ts:986-1027`). `QMD_FORCE_CPU` selects CPU mode (`src/llm.ts:726-742`).
- node-llama first seeks a prebuilt binary, then may download or compile from source (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/bindings/getLlama.js:100-150`, `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/bindings/getLlama.js:230-335`, `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/bindings/getLlama.js:481-500`).
- The fallback can clone llama.cpp from GitHub and invoke npm/CMake/compiler commands (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/bindings/utils/cloneLlamaCppRepo.js:18-88`, `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/bindings/utils/cloneLlamaCppRepo.js:134-156`; `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/bindings/utils/compileLLamaCpp.js:28-61`, `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/bindings/utils/compileLLamaCpp.js:132-168`). If CMake is absent it runs `npm exec --yes xpm@^0.16.3 install @xpack-dev-tools/cmake@latest`, which is not version-pinned (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/utils/cmake.js:57-80`, `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/utils/cmake.js:117-129`).
- qmd's explicit `skipDownload: false` in writable mode overrides relying only on `NODE_LLAMA_CPP_SKIP_DOWNLOAD=1` (`src/llm.ts:986-1027`; node-llama config at `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/config.js:44-83`).
- Required control: set `QMD_FORCE_CPU=1` or pass qmd's `--no-gpu` option for every model command. If GPU use is required, make the installed package tree read-only and separately verify that the exact platform prebuilt package is present; fail closed rather than allow compilation/download.

**Q-L2 — Low: a trusted qmd config can run an arbitrary shell update hook.** It is low for the plan because an explicit `--index` bypasses project-local `.qmd` discovery and the controlled config directory can omit hooks. A writable or untrusted config directory would raise this to high.

- Without `--index`, qmd searches ancestors for `.qmd/index.yaml`; with an explicit index it uses the selected global config source instead (`src/collections.ts:128-154`; `src/cli/qmd.ts:3090-3105`).
- Local config trust is stored by hash and can be controlled by trust environment options (`src/trust.ts:1-18`, `src/trust.ts:121-159`, `src/trust.ts:176-252`, `src/trust.ts:266-332`). The selected global config is treated as trusted, while sensitive fields from a local config are gated (`src/cli/qmd.ts:748-756`, `src/cli/qmd.ts:799-836`).
- A collection `update:` hook executes through `bash -c` (`src/cli/qmd.ts:895-967`).
- Required control: always pass `--index <fixed-name>`; protect `QMD_CONFIG_DIR` with mode `0700`; keep its index config read-only during checks; define no `update:` or `git` pull hook; and unset qmd trust override variables. Review any config change as executable code.

### 5. Files written outside the working folder

**Q-M5 — Medium: the index stores private content in plaintext and qmd does not set restrictive file modes.** This can expose student data to another local account under a permissive umask. It is medium because the planned dedicated cache can contain all qmd writes when created securely.

- The database defaults below `XDG_CACHE_HOME/qmd` and opens in WAL mode, which can create database, `-wal`, and `-shm` files (`src/store.ts:636-653`; `src/db.ts:76-123`).
- The schema stores document bodies and FTS text, and update inserts plaintext content (`src/store.ts:1181-1223`, `src/store.ts:2902-2930`). The indexer rejects collection symlinks and checks containment, which is a useful boundary (`src/store.ts:1605-1705`).
- Model files use `XDG_CACHE_HOME/qmd/models` (`src/llm.ts:314-327`), and embedding uses a sibling lock file (`src/cli/embed-lock.ts:19-57`). Named collection config uses `QMD_CONFIG_DIR` (`src/collections.ts:112-125`, `src/collections.ts:204-230`). The reviewed `mkdir`/write calls do not pass explicit modes.
- node-llama runtime building uses package-local and OS temporary paths outside the qmd cache (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/config.js:10-21`, `work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/config.js:26-32`). It also defines home-folder paths for its own CLI, but no qmd library path to those CLI files was established (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/config.js:22-25`). Disabling the runtime build as required by Q-M4 removes the package/temp write from the planned path.
- npm uses its own cache unless redirected; see [npm `cache` configuration](https://docs.npmjs.com/cli/v11/using-npm/config#cache).
- Required control: precreate one private root with mode `0700`, run with `umask 077`, point both `XDG_CACHE_HOME` and `QMD_CONFIG_DIR` below it, and set `npm_config_cache` below it for installation. Treat SQLite, WAL/SHM, lock, config, logs, and models as student-record data. The exact resulting modes remain unverified because running qmd was prohibited.

Collection add/remove write the selected config and SQLite database; add indexes files immediately, while remove deletes that collection's indexed rows (`src/cli/qmd.ts:1815-1877`). Update/embed also write the selected database and lock under these paths. `status` and search commands open/initialize the selected store (`src/store.ts:2230-2234`), so even read-looking commands should receive the same cache controls. Project trust approvals write `trusted.json` beside `QMD_CONFIG_DIR` (`src/trust.ts:69-72`, `src/trust.ts:210-226`). Stdio MCP does not create the optional HTTP daemon PID/log state (`src/cli/qmd.ts:208-217`, `src/mcp/server.ts:800-827`).

### 6. Credentials

**Q-L3 — Low: model and native download code automatically consumes environment tokens.** It is low because public artifacts need no token and the planned offline run can start with these variables unset. Accidental token use could still disclose a token to an overridden endpoint.

- node-llama reads `HF_TOKEN`, a token file under `HF_HOME`/XDG state, or `HF_TOKEN_PATH`, then sends a bearer token (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/utils/modelFileAccessTokens.js:7-40`). Its Hugging Face/model endpoints are environment-overridable (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/utils/modelDownloadEndpoints.js:2-25`).
- Native GitHub retrieval can use `GITHUB_TOKEN` or `GH_TOKEN` (`work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist/utils/GitHubClient.js:18-43`).
- No keychain API was found: `rg -n -i 'keychain|keytar|secretservice|credential manager' qmd-v2.8.3/src work-R3-vale-qmd/native-extract/node-llama-cpp-3.20.0/package/dist` returned no matches (exit 1).
- Required control: unset `HF_TOKEN`, `HF_TOKEN_PATH`, `GITHUB_TOKEN`, `GH_TOKEN`, `HF_ENDPOINT`, and `MODEL_ENDPOINT` in the runtime environment. Perform any approved public model retrieval in a separate environment without private Wiki access.

### 7. Published advisories for 2.8.3

No direct advisory was found for `@tobilu/qmd` 2.8.3 as of the review date. This does not cover an unknown consuming lockfile's full transitive graph.

- `POST https://api.osv.dev/v1/query` with npm package `@tobilu/qmd` and version `2.8.3` returned `{}`; captured as `work-R3-vale-qmd/osv-qmd.json`.
- npm's bulk advisory endpoint for `@tobilu/qmd` 2.8.3 returned `{}`; captured as `work-R3-vale-qmd/npm-advisories-qmd.json`.
- [GitHub Advisory Database search for the exact npm package](https://github.com/advisories?query=ecosystem%3Anpm+package%3A%40tobilu%2Fqmd) returned “No results matched your search”; captured at `work-R3-vale-qmd/ghsa-qmd.html:1025`.
- Dependency advisory status is unverified because the consuming repository's lockfile was out of scope. Before adoption, the coordinator should run an advisory check against the actual frozen lock without running lifecycle scripts.

### 8. Release signing, provenance, and checksums

**Q-L4 — Low: npm provides strong integrity and provenance metadata, but this review did not independently perform Sigstore verification or reproduce the build.** This is low because the downloaded digest, registry signature metadata, source commit, and provenance subject agree.

- The npm registry reports SHA-512 integrity `sha512-zjfVwrObPB618B6x8SdhlGv/tX9OxRHsbQnr5DUtBvqPK6HGQ27lM+9/BAY5okpjrHVnW56hLyDkqoTcsrVLzA==`, SHA-1 `7e1515b1daf349a1dc88cff53da925d34f89c948`, a registry signature, `gitHead` `facd35e01359e59d938bc9418e93fb9318addee3`, and a SLSA provenance URL (`work-R3-vale-qmd/qmd-registry.json:4-22`).
- The downloaded tarball's SHA-512 is `ce37d5c2b39b3c1eb5f01eb1f12761946bffb57f4ec511ec6d09ebe4352d06fa8f2ba1c6436ee533ef7f040639a24a63ac75675b9ea12f20e4aa84dcb2b54bcc`, matching the decoded npm integrity and the attestation subject. Its SHA-1 also matches the registry. Evidence: `sha512sum` and `sha1sum` on `work-R3-vale-qmd/tobilu-qmd-2.8.3.tgz`.
- The SLSA statement binds that digest to tag `v2.8.3`, commit `facd35e...`, `.github/workflows/publish.yml`, and a GitHub-hosted runner (`work-R3-vale-qmd/qmd-attestations.json:1`). The workflow grants OIDC and publishes with provenance (`.github/workflows/publish.yml:3-5`, `.github/workflows/publish.yml:11-20`, `.github/workflows/publish.yml:25-40`).
- `diff -q qmd-v2.8.3/bin/qmd work-R3-vale-qmd/package-extract/package/bin/qmd` returned no output and exit 0. The packed build metadata names the reviewed commit. This is a source comparison, not a reproducible-build proof.
- The workflow uses floating major action tags and installs the latest Bun rather than a pinned toolchain (`.github/workflows/publish.yml:11-26`).
- The annotated Git tag contains an SSH signature, but `git verify-tag v2.8.3` could not establish trust because `gpg.ssh.allowedSignersFile` was not configured. The npm Sigstore provenance is the useful published verification path.

### qmd verdict and required settings

No high finding stands. Five medium findings stand until all of these controls are in place:

1. Pre-provision and independently hash the exact Qwen GGUF; set `QMD_EMBED_MODEL` to its local read-only path.
2. Do not use `qmd pull`; use CLI `search`, and use MCP only with typed `lex:`/`vec:` queries plus `rerank: false`. Do not use CLI `vsearch` unless its separate generation model is approved, pinned, and pre-provisioned.
3. Keep `npm ci --ignore-scripts`; set `QMD_FORCE_CPU=1` or `--no-gpu` to disable native fallback. A GPU exception needs a verified platform prebuilt and a read-only package tree.
4. Run with `umask 077`; place `XDG_CACHE_HOME`, `QMD_CONFIG_DIR`, and `npm_config_cache` below one mode-`0700` private cache; always pass `--index <fixed-name>`; allow no config update hook.
5. Keep CLI output out of shared logs. Use stdio MCP only with a verified local/offline client; otherwise use the CLI. Never enable `--http` or `--daemon` for the private index.

Unset all download tokens and endpoint overrides during normal use. With those controls, no high or medium finding remains for lexical CLI operations, controlled embedding, or a trusted local stdio MCP client. The user-initiated model-download boundary is incompatible with CLI `vsearch` as implemented in 2.8.3 unless its generation model is separately approved and pre-provisioned.
