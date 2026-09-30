# Security review: import-linter, Grimp, bagit-python, and dependency-cruiser

Date: 2026-09-30

## Scope and method

This is a read-only review of the exact releases and planned CHE-44 paths:

- `import-linter` 2.15 at tag `v2.15`, including its required `grimp>=3.17` dependency resolved here as Grimp 3.17 at tag `v3.17`.
- `bagit` 1.9.0 at tag `v1.9.0`, used through `bagit.py` or `python -m bagit` to create and validate private-document bags.
- `dependency-cruiser` 18.2.0 at tag `v18.2.0`, used through `depcruise`, a `.dependency-cruiser.cjs` configuration, and `--affected`.

I inspected the clones, downloaded the published artifacts into `work-R5-importlinter-bagit-depcruise/`, checked their hashes, and extracted them without installing them. I did not execute the packages, their tests, their builds, or their install scripts. Paths below are relative to the supplied `SEC` directory unless they are URLs.

Ratings combine impact with the stated use. “Medium” means the path can execute code, weaken the intended integrity check, or expose private records unless the stated control is applied. “Low” means the path is limited by the trusted-repository or controlled-staging assumptions, or has a small operational effect.

## Summary

| Tool | High | Medium | Low | Planned-use verdict |
|---|---:|---:|---:|---|
| import-linter 2.15 | 0 | 1 | 2 | Use is acceptable only with built-in contracts, or with every plugin treated as executable code. Use `--no-cache`. |
| Grimp 3.17 | 0 | 1 | 3 | One medium supply-chain gap stands: the native wheel has no source provenance. Pin the exact platform wheel hash and do not fall back to the sdist. |
| bagit-python 1.9.0 | 0 | 2 | 3 | Do not use `--fast` as the acceptance check. Protect the plaintext bag and identifiers with external access control and encryption. |
| dependency-cruiser 18.2.0 | 0 | 2 | 3 | Treat `.cjs` configuration as code and pass only a validated full commit ID to `--affected`. Use `--no-cache` and `GIT_OPTIONAL_LOCKS=0`. |

No high finding was found. Six medium findings stand or require an explicit planned-use control.

## Artifact and source identity evidence

The supplied clones resolve to these exact commits:

```text
import-linter v2.15       31927f1457e3df673912cb5efb0afa6dbc37585f
grimp v3.17               286f0f5de79d29dea44cfa6563802e9b4fe37dea
bagit-python v1.9.0       861ddacb339d5b92659f0187a402f501d841abbe
dependency-cruiser v18.2.0 ec603451d07d699280234808f91c4c8d3813f6e8
```

The downloaded hashes matched the registry metadata:

```text
$ sha256sum import_linter-2.15-py3-none-any.whl import_linter-2.15.tar.gz \
    grimp-3.17-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl \
    grimp-3.17.tar.gz bagit-1.9.0.tar.gz
9aaf16a88ac1e99d5a464cd7f66b6a05f7060bfa761162e0ed441773a267ed3b  import_linter-2.15-py3-none-any.whl
1da912bea5e172a82a3ce617b5543f75cf64dc0d8f4d9b46c5578b68ccb81590  import_linter-2.15.tar.gz
6dbf2d93b0ba7f6c1efba9f5b3e07a3da0a157392c650316a5c1478b0ef7e503  grimp-3.17-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
5161e03c6f518fe4da43b06c97ff49a1e224ecb0e4b9fd6ef48235373d1b7b33  grimp-3.17.tar.gz
9455006c2d1df88be95ec1fccabc5ea623389589ea4c85b3d85bd256f29d7656  bagit-1.9.0.tar.gz

$ sha1sum dependency-cruiser-18.2.0.tgz
63d826f6f930567ee446a607212db5e4b02bb68e  dependency-cruiser-18.2.0.tgz

$ openssl dgst -sha512 -binary dependency-cruiser-18.2.0.tgz | base64 -w0
xMDoLD0no6pDInR8/4rIIqZ4mERDnsjezk8PkNORYSfBLvjCOogUxaruepmi1uQtZQlYUgdT2u7G3jTlgKqNjw==
```

`diff -qr import-linter-v2.15/src/importlinter work-R5-importlinter-bagit-depcruise/extracted/import-linter-wheel/importlinter` produced no output. The equivalent Grimp comparison found only the wheel's compiled `_rustgrimp.cpython-313-x86_64-linux-gnu.so`; its Python files matched. The bagit sdist's `bagit.py` and `setup.py` hashes matched the tag. `diff -u -w` found no semantic difference in dependency-cruiser's CLI and option-normalization files; the source tag's `prepack` formats shipped files with tabs (`dependency-cruiser-v18.2.0/package.json:181-184`).

## import-linter 2.15

### Findings

| ID | Rating | Finding and planned-use effect | Evidence | Required control |
|---|---|---|---|---|
| IL-1 | medium | A configured custom contract is arbitrary Python code. The CLI adds the repository root to `sys.path`, imports every `contract_types` module, constructs its class, and calls `check`. A changed config or plugin can therefore run with the linter's environment and credentials. This only ceases to stand if CHE-44 uses built-in contract types exclusively. | `import-linter-v2.15/src/importlinter/cli.py:204-205`; `import-linter-v2.15/src/importlinter/application/use_cases.py:359-416`; contract construction and execution at `use_cases.py:287-310`. | Use only the built-ins listed at `use_cases.py:365-377`. If a plugin is necessary, review it as executable code and do not run it on an untrusted change with secrets present. |
| IL-2 | low | Caching writes import graph data under the repository and is not concurrency-safe. This is a small integrity and worktree-noise risk for parallel lint jobs. | Default `.import_linter_cache` at `import-linter-v2.15/src/importlinter/configuration.py:8-17`; location, opt-out, and concurrency warning at `import-linter-v2.15/docs/caching.md:17-38`. | Run `lint-imports --no-cache`. |
| IL-3 | low | The PyPI wheel and lightweight Git tag have no cryptographic source provenance. The reviewed wheel was pure Python and matched the tagged source byte-for-byte, and its SHA-256 matched PyPI, which limits the residual risk when the lock hash is enforced. | PyPI JSON reports `has_sig=false`; the Integrity API returned HTTP 404, `{"message":"No provenance available for import_linter-2.15-py3-none-any.whl"}`. `git cat-file -t v2.15` returned `commit`, and `git verify-tag v2.15` returned `cannot verify a non-tag object`. Artifact comparison and hash are recorded above. | Keep the exact wheel hash in the uv lock and reject an unexpected sdist or wheel hash. |

### 1. Install and post-install scripts

The release declares Hatchling as its build backend and packages `src/importlinter`; it defines no custom build hook or install-time script (`import-linter-v2.15/pyproject.toml:42-47`). The console entry points at `pyproject.toml:54-56` are runtime commands, not lifecycle scripts. Installing the reviewed pure-Python wheel therefore does not run repository build code. Building the sdist would run the declared Hatchling backend, so the wheel is preferable.

### 2. Downloaded binaries, models, or data

The reviewed `py3-none-any` wheel contains Python and package metadata, not a native binary or model. Its metadata requires `click>=6`, `grimp>=3.17`, `rich>=14.2.0`, and two conditional/support libraries (`import_linter-2.15.dist-info/METADATA:25-29`). Those ranges make the project uv lock, not this package metadata, responsible for exact transitive versions. The optional UI dependencies are separate (`pyproject.toml:36-40`) and are not part of the planned install.

There is no runtime artifact download in the `lint-imports` path. The network scan below returned no match after excluding the optional UI:

```text
$ rg -n '(requests|urllib|socket|httpx|aiohttp|telemetry|analytics|keyring|credential|os\.environ|os\.getenv)' \
    import-linter-v2.15/src/importlinter -g '!**/ui/**'
rg_exit=1
```

### 3. Network calls and telemetry

The planned lint path has no network client or telemetry. The `explore` command imports the optional UI server (`import-linter-v2.15/src/importlinter/cli.py:98-115`), but that extra is excluded from the plan. There is no telemetry switch because no telemetry was found. Keep the job network-disabled to enforce the offline requirement.

### 4. Code execution and shell-outs

IL-1 is the reachable code-execution path. Configuration itself is parsed as INI or TOML data (`import-linter-v2.15/src/importlinter/adapters/user_options.py:43-103`), but `contract_types` values are imported as Python. No subprocess or shell-out was found in the lint path. Import Linter delegates source scanning to Grimp (`import-linter-v2.15/src/importlinter/adapters/building.py:7-24`).

### 5. Writes outside the working folder

Runtime config discovery is limited to the current working directory (`import-linter-v2.15/src/importlinter/application/file_finding.py:16-25`). The only normal runtime write found is IL-2's cache, also in the current working directory unless `--cache-dir` points elsewhere. `--no-cache` maps to no cache (`import-linter-v2.15/src/importlinter/cli.py:227-234`). No home-folder config or global state write was found.

### 6. Credential handling

The lint path does not read tokens, keychains, credential files, or environment variables. A custom contract has ordinary Python access to all of them, which is part of IL-1. Run untrusted changes in a secret-free environment even when built-in contracts are expected.

### 7. Published advisories for 2.15

No exact-version advisory was found on 2026-09-30:

- [GitHub Advisory Database query for `import-linter@2.15`](https://github.com/advisories?query=affects%3Aimport-linter%402.15) returned “No results matched your search,” and the [repository security page](https://github.com/seddonym/import-linter/security) showed no published advisories.
- The exact OSV query `POST https://api.osv.dev/v1/query` with `{"package":{"name":"import-linter","ecosystem":"PyPI"},"version":"2.15"}` returned `{}`.
- [PyPI's exact-version JSON](https://pypi.org/pypi/import-linter/2.15/json) returned an empty `vulnerabilities` array.

These are absence-of-record checks, not proof that the release is vulnerability-free.

### 8. Release signing, provenance, and checksums

IL-3 records the provenance gap. The downloaded wheel's SHA-256 matched PyPI and its Python tree matched the supplied tag. PyPI reports neither a detached signature nor a provenance attestation for the wheel or sdist. The tag is lightweight rather than signed.

### Verdict

Zero high and one medium finding. IL-1 remains until the planned configuration is confirmed to contain only built-in contract types. Use `lint-imports --no-cache`, no UI extra, a network-disabled job, and the exact uv-locked wheel hash.

## Grimp 3.17

### Findings

| ID | Rating | Finding and planned-use effect | Evidence | Required control |
|---|---|---|---|---|
| GR-1 | medium | The platform wheel executes a 5,913,744-byte native extension, but PyPI provides no provenance and the release tag is unsigned. The Python portion matched source, but this review could not establish that `_rustgrimp.so` was built from the reviewed Rust commit. A malicious native extension would run in-process during every lint. | Wheel member and inner RECORD hash at `work-R5-importlinter-bagit-depcruise/extracted/grimp-wheel/grimp/_rustgrimp.cpython-313-x86_64-linux-gnu.so` and `grimp-3.17.dist-info/RECORD`; PyPI Integrity API returned HTTP 404 with “No provenance available”; `git verify-tag v3.17` reported a lightweight commit tag. | Pin the exact platform wheel SHA-256 `6dbf2d...e503`, reject sdist fallback, and install in a low-privilege, secret-free lint environment. Prefer an independently reproducible build or upstream PyPI provenance before treating this as closed. |
| GR-2 | low | An sdist fallback runs Maturin/Cargo and can download 108 registry packages plus five Ruff Git packages. Registry entries have Cargo checksums, while the Ruff packages are fixed by Git commit but have no independent archive checksum. | `grimp-v3.17/pyproject.toml:1-7`; `grimp-v3.17/rust/Cargo.toml:10-39`; Ruff resolves to commit `f82a36b6...` at `rust/Cargo.lock:717-780`. `rg` counted 108 crates.io-index sources, all followed by checksums, and five Ruff Git sources. | Do not permit source builds in the normal install. Preselect and hash the supported wheel for each platform. If a source build is required, isolate it, prefetch reviewed inputs, and use Cargo offline/frozen controls. |
| GR-3 | low | Package walking follows directory symlinks, so a repository symlink can make the linter read Python outside the intended tree or loop. The planned trusted repository lowers the rating. | `grimp-v3.17/src/grimp/adaptors/filesystem.py:23-25`. | Reject directory symlinks in scanned package roots, or run with a filesystem sandbox that exposes only the checkout. |
| GR-4 | low | Grimp writes JSON cache content and marker files. Import Linter overrides Grimp's `.grimp_cache` default with `.import_linter_cache`; a caller-supplied absolute cache path could write elsewhere. | Default and writes at `grimp-v3.17/src/grimp/adaptors/caching.py:68-105,122-155,219-235`; JSON parsing at `grimp-v3.17/rust/src/caching.rs:108-133`; Import Linter passes its cache setting at `import-linter-v2.15/src/importlinter/adapters/building.py:12-24`. | Use Import Linter's `--no-cache`; do not provide an absolute cache directory. |

### 1. Install and post-install scripts

Grimp is a Maturin Rust extension (`grimp-v3.17/pyproject.toml:1-7`). A source build compiles the crate graph and runs the Rust build script, whose body only calls PyO3's extension-link configuration (`grimp-v3.17/rust/build.rs:1-3`). The prebuilt wheel avoids that build. There is no post-install hook in the wheel.

### 2. Downloaded binaries, models, or data

The planned import executes the native `_rustgrimp` shared object noted in GR-1. The whole wheel SHA-256 matched PyPI, and the wheel RECORD supplies an inner SHA-256 for the shared object. These hashes detect later alteration but do not establish source provenance. There are no models or runtime data downloads. GR-2 lists source-build downloads and their origins: the default Cargo registry and `https://github.com/astral-sh/ruff.git`.

### 3. Network calls and telemetry

No Python or Rust runtime network client, telemetry, analytics, credential, or subprocess reference was found:

```text
$ rg -n '(requests|urllib|socket|httpx|aiohttp|telemetry|analytics|keyring|credential|os\.environ|os\.getenv|subprocess|Popen)' \
    grimp-v3.17/src/grimp grimp-v3.17/rust/src
rg_exit=1
```

Only a source build needs the package-fetch network described in GR-2. There is no runtime telemetry setting to disable.

### 4. Code execution and shell-outs

Grimp locates packages with `importlib.util.find_spec` (`grimp-v3.17/src/grimp/adaptors/packagefinder.py:16-37`) and statically scans source through the Rust extension (`grimp-v3.17/src/grimp/application/usecases.py:25-71,109-155`). It does not import each scanned module. No shell-out was found at runtime. The native extension itself is executable code and is the subject of GR-1.

### 5. Writes outside the working folder

GR-4 covers runtime writes. With `lint-imports --no-cache`, no Grimp runtime write was found. Building the sdist would also cause the build frontend and Cargo to write build directories and their configured caches; that behavior belongs to the installer/build tools and is avoided by wheel-only installation.

### 6. Credential handling

Grimp does not read tokens, environment secrets, keychains, or credential files. It can read source outside the checkout through GR-3, so the lint sandbox should not expose sensitive Python trees.

### 7. Published advisories for 3.17

No exact-version advisory was found on 2026-09-30:

- [GitHub Advisory Database query for `grimp@3.17`](https://github.com/advisories?query=affects%3Agrimp%403.17) returned no results, and the [repository security page](https://github.com/python-grimp/grimp/security) showed no published advisories.
- The OSV exact-version query for PyPI `grimp` 3.17 returned `{}`.
- [PyPI's exact-version JSON](https://pypi.org/pypi/grimp/3.17/json) returned an empty `vulnerabilities` array.

### 8. Release signing, provenance, and checksums

GR-1 and GR-2 cover the gap. PyPI JSON reports `has_sig=false` for the reviewed wheel and sdist. Both PyPI Integrity endpoints returned HTTP 404 with no provenance. The downloaded wheel and sdist hashes matched PyPI, but the `v3.17` tag is lightweight and the compiled wheel cannot be derived from source without executing a build, which this review did not do.

### Verdict

Zero high and one medium finding. GR-1 stands for the planned use. Require an exact hashed platform wheel, forbid sdist fallback, run without secrets or network, and use `lint-imports --no-cache`.

## bagit-python 1.9.0

### Findings

| ID | Rating | Finding and planned-use effect | Evidence | Required control |
|---|---|---|---|---|
| BA-1 | medium | `--fast` checks only payload file count and total bytes, then returns without manifest completeness or checksum validation. A same-size alteration can pass, so fast mode does not meet the integrity purpose for private student records. | CLI help explicitly says no corruption detection at `bagit-python-v1.9.0/bagit.py:1462-1468`; early return at `bagit.py:778-795`. | Use full `--validate` as the acceptance check. If `--fast` is retained, label it only as a preliminary presence/size check and always follow it with full validation. |
| BA-2 | medium | BagIt supplies integrity, not confidentiality. The document is moved as-is under `data/`, and external/internal identifiers are written in plaintext `bag-info.txt`. Default informational logs include bag and file paths; `--log` can place them anywhere. This matters because the payload and identifiers are private student records. | In-place move and tag creation at `bagit-python-v1.9.0/bagit.py:211-264`; plaintext tag writing at `bagit.py:1212-1222`; logging choice at `bagit.py:1447-1452,1521-1530`. | Encrypt and permission the staging/storage layer independently of BagIt. Prefer opaque identifiers, use `--quiet`, and omit `--log` or keep it inside the same protected storage boundary. |
| BA-3 | low | Manifest and `fetch.txt` containment uses `os.path.commonprefix`, a string-prefix check. A path such as a sibling whose name begins with the bag path can pass and then be opened for hashing. Symlink targets can reach the same path. The plan creates and validates its own controlled bag, which lowers exposure, but later-tampered or third-party bags are unsafe to validate with broad filesystem access. | Path normalization and `commonprefix` at `bagit-python-v1.9.0/bagit.py:925-940`; manifest use at `bagit.py:620-727`; paths are opened at `bagit.py:860-905,1111-1148`; creation walks file symlinks and opens their targets at `bagit.py:1316-1328,1374-1402`. | Validate only bags created from the controlled staging folder. Reject symlinks and precheck every manifest/fetch path with `realpath` plus `commonpath` in the calling workflow, or isolate validation so no adjacent private files are visible. |
| BA-4 | low | PyPI publishes only an sdist. Its setup path runs repository Python and invokes the first `msgfmt` on `PATH` to compile the included translation catalog. Build requirements are open ranges. | No wheel in [PyPI 1.9.0 JSON](https://pypi.org/pypi/bagit/1.9.0/json); build requirements at `bagit-python-v1.9.0/pyproject.toml:1-3`; shell-out at `setup.py:16-38`; setup calls it at `setup.py:41-52`. The sdist contains `locale/en/LC_MESSAGES/bagit-python.po` and no `.mo`. | Build once in an isolated, reviewed environment with pinned build requirements and a trusted `PATH`; then install the resulting internally hashed wheel. |
| BA-5 | low | Creation is an in-place move of the only copy. Exceptions are logged and re-raised without rollback, so a failed creation can leave the document under a partial `data/` bag layout. The file is not deleted, but an operator can mistake the changed layout for loss. | `bagit-python-v1.9.0/bagit.py:176-269`; CLI describes in-place conversion at `bagit.py:1508-1515`. | Create the staging copy before calling BagIt, verify the resulting full bag, and only then retire any source copy according to the retention procedure. |

### 1. Install and post-install scripts

BA-4 is the install-time path. `setuptools.build_meta` executes project build code because no wheel is published. `setup.py` catches `msgfmt` failure and continues without translations (`setup.py:25-34`), but it still attempts the subprocess. No runtime post-install hook exists.

### 2. Downloaded binaries, models, or data

Installation downloads the sdist plus the configured-index versions of `setuptools>=64` and `setuptools-scm>=8`. No runtime model, binary, or data download exists. `fetch.txt` URLs are parsed and validated but never fetched: `fetch_entries` yields `(url, size, filename)` (`bagit.py:545-572`), and `validate_fetch` only calls `urlparse` (`bagit.py:758-776`). No checksum or signature is applied to remote content because this implementation does not retrieve it.

### 3. Network calls and telemetry

No runtime network client or telemetry was found in `bagit.py`:

```text
$ rg -n '(requests|urlopen|urllib\.request|socket|httpx|aiohttp|telemetry|analytics|keyring|credential|os\.environ|os\.getenv)' \
    bagit-python-v1.9.0/bagit.py
rg_exit=1
```

There is no telemetry opt-out to set. Network-disable the bagging job; validation remains functional because `fetch.txt` is not fetched.

### 4. Code execution and shell-outs

The only package shell-out found is BA-4's build-time `msgfmt`. Runtime can create multiprocessing workers when `--processes` exceeds one (`bagit.py:1225-1239,860-890`), but the planned default is one process. No shell command is constructed from bag metadata or filenames.

BA-3 is a filesystem read boundary rather than a shell injection. `fetch.txt` does not cause URL execution.

### 5. Writes outside the working folder

At runtime, bag creation makes a temporary directory inside the target, moves existing entries to `data/`, and writes bag files inside that directory (`bagit.py:211-264`). It writes outside the bag only if the operator supplies an external `--log` path. No home-folder config, cache, keychain, or global state write was found. Installation writes the normal Python environment and, because `data_files=get_message_catalogs()`, its translation catalog under the install prefix (`setup.py:36-49`).

### 6. Credential handling

The package does not read credential environment variables, token files, or keychains. Bag-info values are ordinary plaintext and may contain the planned identifiers; BA-2 applies. Do not place authentication secrets in bag-info fields.

### 7. Published advisories for 1.9.0

No exact-version advisory was found on 2026-09-30:

- [GitHub Advisory Database query for `bagit@1.9.0`](https://github.com/advisories?query=affects%3Abagit%401.9.0) returned no results, and the [repository security page](https://github.com/LibraryOfCongress/bagit-python/security) showed no published advisories.
- The OSV exact-version query for PyPI `bagit` 1.9.0 returned `{}`.
- [PyPI's exact-version JSON](https://pypi.org/pypi/bagit/1.9.0/json) returned an empty `vulnerabilities` array.

### 8. Release signing, provenance, and checksums

The sdist SHA-256 matched PyPI. PyPI's Integrity API returned a publish attestation for `bagit-1.9.0.tar.gz`, identifying GitHub publisher `LibraryOfCongress/bagit-python`, workflow `pypi-release.yml`, and the same SHA-256. The attestation is a PyPI publish statement, not a full source-build provenance statement. PyPI JSON says `has_sig=false`, and `v1.9.0` is a lightweight Git tag. The extracted `bagit.py` and `setup.py` were byte-identical to the supplied tag.

### Verdict

Zero high and two medium findings. BA-1 and BA-2 stand for the stated private-record use. Use `--sha256`, full `--validate` for acceptance, `--quiet`, no external log, no symlinks, opaque identifiers where possible, and encrypted/permissioned storage. Treat `--fast` only as an optional preliminary check.

## dependency-cruiser 18.2.0

### Findings

| ID | Rating | Finding and planned-use effect | Evidence | Required control |
|---|---|---|---|---|
| DC-1 | medium | The planned `.dependency-cruiser.cjs` file is dynamically imported and executed. JavaScript/TypeScript configs and every `extends` target run with normal Node access to files, network, and environment secrets. A config changed in an untrusted pull request is code execution in the lint job. | `dependency-cruiser-v18.2.0/src/config-utl/extract-depcruise-config/read-config.mjs:9-21`; recursive `extends` loading at `extract-depcruise-config/index.mjs:8-33,53-90`; CLI load at `src/cli/normalize-cli-options.mjs:125-138,216-223`. | Prefer a JSON/JSON5 config if it can express the rules. If `.cjs` is required, protect and review it as code and run untrusted changes without credentials, writable sensitive paths, or network. |
| DC-2 | medium | `--affected` passes its value directly as a positional `git diff` argument without `--end-of-options` or revision validation. A value beginning with `-` is therefore parsed by Git as an option. The spawn does not use a shell, so shell metacharacters are not interpreted, but Git options can change behavior, write output, or enable other Git features. | Dependency-cruiser passes the value at `dependency-cruiser-v18.2.0/src/cli/normalize-cli-options.mjs:228-235`. The shipped `watskeburt` constructs `['diff', pOldRevision, '--name-status']` and calls `spawn('git', args, ...)` at `work-R5-importlinter-bagit-depcruise/extracted/watskeburt/package/dist/git-primitives.js:15-48`. | Resolve the intended base revision before invocation and accept only a full hexadecimal commit ID, such as `^[0-9a-f]{40}$`. Do not pass branch, tag, PR title, or user-controlled text directly. |
| DC-3 | low | `--affected` also runs `git status --porcelain`. By default Git refreshes and writes the index and takes an optional lock, which can mutate shared worktree metadata or contend with another Git process. | `watskeburt` calls status at `dist/main.js:4-17` and `dist/git-primitives.js:4-12`. The official [git-status background refresh documentation](https://git-scm.com/docs/git-status#_background_refresh) says it writes the refreshed index and recommends `git --no-optional-locks status`. | Set `GIT_OPTIONAL_LOCKS=0` for the depcruise process. |
| DC-4 | low | Cache is off by default, but a config can enable it and write `cache.json` under `node_modules/.cache/dependency-cruiser` or an arbitrary configured folder. CLI `--output-to` can overwrite an arbitrary path. | Cache default and opt-out at `dependency-cruiser-v18.2.0/bin/dependency-cruise.mjs:135-150`; disabled-by-default normalization at `src/cli/normalize-cli-options.mjs:175-193`; writes at `src/cache/cache.mjs:21,105-120,146-160`; output default/stdout and file write at `bin/dependency-cruise.mjs:32-42` and `src/cli/utl/io.mjs:1-48`. | Pass `--no-cache` so config cannot enable it, and leave output at `-` unless a reviewed path inside the checkout is required. |
| DC-5 | low | Initial directory gathering uses `statSync`, which follows directory symlinks, and recurses without a visited-set check. A repository symlink can expose files outside the checkout or loop. | `dependency-cruiser-v18.2.0/src/extract/gather-initial-sources.mjs:48-72`. | Reject directory symlinks in input roots and run with a filesystem boundary around the checkout. |

### 1. Install and post-install scripts

The published tarball's `package.json` has only a `test` script and no `preinstall`, `install`, `postinstall`, `prepare`, or native build hook (`work-R5-importlinter-bagit-depcruise/extracted/dependency-cruiser/package/package.json:145-169`). The source tag has `prepare: husky`, but its `prepack` deliberately rewrites the published scripts and its `postpack` restores source (`dependency-cruiser-v18.2.0/package.json:181-185`). Therefore npm installation of the published package does not run dependency-cruiser lifecycle code.

The source `package-lock.json` contains three `hasInstallScript` packages: `@swc/core`, `esbuild`, and `yarn`; all three are marked `dev: true` (`package-lock.json:1594-1603,2711-2724,4877-4889`). The direct runtime helper `watskeburt` 6.0.0 also ships only a `test` script (`work-R5-importlinter-bagit-depcruise/extracted/watskeburt/package/package.json:47-52`). This supports, but does not replace, enforcing the repository's exact lock for the full transitive tree.

### 2. Downloaded binaries, models, or data

npm downloads the JavaScript package and its exact direct dependencies from the configured registry; the package itself downloads no runtime binary, model, or data. The published tarball contains no `.node`, `.so`, `.dll`, or `.exe` file. TypeScript scanning dynamically imports the locally installed `typescript` module if its version is supported (`dependency-cruiser-v18.2.0/src/utl/try-import.mjs:41-65`; `src/extract/transpile/typescript-wrap.mjs:1-48`). Pin that project dependency in the repository lock.

`--affected` uses the system `git` executable. The optional `x-dot-webpage` reporter shells out to system GraphViz `dot` (`src/report/dot-webpage/dot-module.mjs:16-45,55-74`), but the planned default `err` reporter does not reach it.

### 3. Network calls and telemetry

No network-client import/call or telemetry path was found in `bin/` or `src/`:

```text
$ rg -n 'node:(http|https|net|tls|dgram)|\bfetch\s*\(|XMLHttpRequest|WebSocket|telemetry|analytics' \
    dependency-cruiser-v18.2.0/bin dependency-cruiser-v18.2.0/src -g '!**/*.json' -g '!**/*.css'
rg_exit=1
```

`git diff`, `git status`, and `git rev-parse` are local commands in the planned path (`watskeburt/dist/git-primitives.js:4-48`). No telemetry switch is needed. Network-disable the job to contain DC-1 or any optional config loader.

### 4. Code execution and shell-outs

DC-1 and DC-2 are the planned reachable paths. Webpack and Babel configuration, if enabled in `.dependency-cruiser.cjs`, are also executable: webpack configs are dynamically imported or required and function exports are invoked (`dependency-cruiser-v18.2.0/src/config-utl/extract-webpack-resolve-config.mjs:8-27,48-95,119-136`). Do not enable them unless they are reviewed and needed.

The `git` spawn uses an argument array and the default `shell: false`, so no shell injection was found. It resolves `git` through `PATH` and inherits the full environment (`watskeburt/dist/git-primitives.js:44-48`). Use a trusted `PATH`, validate the revision as DC-2 requires, and sanitize secrets because DC-1 can access them.

### 5. Writes outside the working folder

DC-3 and DC-4 cover reachable writes. With `--no-cache`, stdout output, and `GIT_OPTIONAL_LOCKS=0`, no planned runtime write outside the checkout was found. Package-manager installation writes `node_modules` and its configured npm cache; those are npm behaviors rather than dependency-cruiser lifecycle hooks.

### 6. Credential handling

The package has no token, keychain, or credential-store integration. However, DC-1 executes config code with `process.env`, and the `git` child explicitly inherits `process.env` (`watskeburt/dist/git-primitives.js:45-48`). Use a secret-free environment for untrusted changes. No credential is needed for the planned local Git operations.

### 7. Published advisories for 18.2.0

No exact-version advisory was found on 2026-09-30:

- [GitHub Advisory Database query for `dependency-cruiser@18.2.0`](https://github.com/advisories?query=affects%3Adependency-cruiser%4018.2.0) returned no results, and the [repository security page](https://github.com/sverweij/dependency-cruiser/security) showed no published advisories.
- The OSV exact-version query for npm `dependency-cruiser` 18.2.0 returned `{}`.
- The npm bulk advisory endpoint request `{"dependency-cruiser":["18.2.0"]}` returned `{}`.

### 8. Release signing, provenance, and checksums

This release has the strongest artifact evidence in scope. Registry metadata supplies SHA-1, SHA-512 SRI, an ECDSA registry signature, and an npm SLSA provenance URL. The downloaded tarball matched both digests. The SLSA statement names `refs/tags/v18.2.0`, repository `https://github.com/sverweij/dependency-cruiser`, workflow `.github/workflows/release.yml`, and resolved Git commit `ec603451d07d699280234808f91c4c8d3813f6e8`, matching the supplied clone. Its subject SHA-512 also matched the tarball.

The Git tag is annotated and signed, but local `git verify-tag v18.2.0` could not authenticate it because public key `47294DE67E7ED5FCE1FD43C5905463325895C992` was unavailable. npm documents `npm audit signatures` as the command that cryptographically checks registry signatures and provenance ([npm provenance verification](https://docs.npmjs.com/viewing-package-provenance/), [registry signature verification](https://docs.npmjs.com/verifying-registry-signatures/)). This review did not run it because it requires an installed dependency tree, which the task forbids. The registry data, matching digests, and downloaded attestation were inspected but not independently signature-verified.

### Verdict

Zero high and two medium findings. DC-1 and DC-2 stand unless the workflow treats config as trusted code and validates `--affected` as a full commit ID. Use `--no-cache --no-progress`, stdout output, `GIT_OPTIONAL_LOCKS=0`, a trusted `PATH`, a network-disabled and secret-free process for untrusted changes, and the lockfile integrity for 18.2.0.

## Required settings checklist

- Import Linter: exact hashed wheel; exact Grimp platform wheel; no sdist fallback; built-in contracts only unless plugins are reviewed; `lint-imports --no-cache`; no UI extra; network disabled.
- BagIt: controlled regular-file staging copy; reject symlinks; `--sha256 --quiet`; full `--validate` for acceptance; `--fast` only before full validation; no external `--log`; opaque identifiers where possible; encrypted and permissioned storage.
- dependency-cruiser: reviewed `.cjs` or JSON/JSON5 config; full-hex commit ID for `--affected`; `--no-cache --no-progress`; stdout output; `GIT_OPTIONAL_LOCKS=0`; trusted `PATH`; network disabled and secrets removed for untrusted changes.

## Review limits

The exact direct releases and the explicitly scoped Grimp and `watskeburt` paths were reviewed. Other transitive packages were checked for lifecycle-script flags through the supplied lock where available, but they did not receive independent source reviews. Advisory databases can be incomplete or updated after this date. Native Grimp source equivalence remains unverified because building or executing it was outside the allowed review.
