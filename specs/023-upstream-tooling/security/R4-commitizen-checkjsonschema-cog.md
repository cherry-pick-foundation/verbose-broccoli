# R4 security review: commitizen, check-jsonschema, and cogapp

Review date: 2026-09-30

## Scope and method

This review covers the exact releases and planned uses in CHE-44:

- `commitizen` 4.19.0, tag `v4.19.0`, for `cz bump --files-only` or `cz bump --get-next`, and possibly `cz check --commit-msg-file`.
- `check-jsonschema` 0.38.2, tag `0.38.2`, for local JSON instances and a local 2020-12 schema whose only references are local `#/$defs` fragments.
- `cogapp` 3.6.0, tag `v3.6.0`, for executing repository-owned Python generators in Markdown and checking generated output for drift.

The review was read-only except for downloaded evidence under `work-R4-commitizen-checkjsonschema-cog/` and this report. I did not install or execute any reviewed tool, test, build, or install script. I inspected the tagged source, downloaded the PyPI wheels and source distributions, checked their published SHA-256 values, and compared their importable package trees with the clones.

Severity is relative to the planned use. **High** means likely direct compromise with ordinary planned inputs. **Medium** means meaningful code execution, data exposure, or network risk with a realistic configuration or repository-content precondition. **Low** means an opt-in, constrained, or supply-chain weakness that the planned configuration can avoid.

## Summary

| Tool | High | Medium | Low | Planned-use verdict |
|---|---:|---:|---:|---|
| commitizen 4.19.0 | 0 | 1 | 2 | One medium finding stands: `--files-only` still runs repository-configured pre-bump shell hooks. Keep both hook lists empty and use a locked, isolated environment. |
| check-jsonschema 0.38.2 | 0 | 1 | 2 | One medium finding stands: there is no true offline mode, so a future external `$ref` can make a network request. Use `--no-cache` and enforce network denial outside the tool. |
| cogapp 3.6.0 | 0 | 1 | 2 | One medium finding stands by design: `--check` still executes embedded Python without a sandbox. Run only reviewed generator code in a secret-free, network-denied sandbox. |

Total: **0 high, 3 medium, 6 low** findings.

## Common artifact evidence

Clone identity was checked with `git rev-parse HEAD` and `git describe --tags --exact-match`:

```text
commitizen-v4.19.0      3f5ccc87b27966d9ed21cf5ea8ec2fba38ca65ce  v4.19.0
check-jsonschema-0.38.2 0494aa7fa1314e98913a41227d8f0a515b2c1049  0.38.2
cog-v3.6.0              badd4c31d77dec54f745c03ae673e753df47163d  v3.6.0
```

The downloaded artifacts matched the SHA-256 values returned by each exact PyPI JSON endpoint:

| Artifact | SHA-256 |
|---|---|
| `commitizen-4.19.0-py3-none-any.whl` | `ab17bc6578b6f12bb8ea827197bf899fdf0dd3c5874180023656c40e22f838c1` |
| `commitizen-4.19.0.tar.gz` | `9ed44eea06b5886462c30292a30c389330215e8fa79bcf932dbc4126b11009ef` |
| `check_jsonschema-0.38.2-py3-none-any.whl` | `8edefe154b7117962f2e88318f315fc4bb9615827f932b37cb676a8d42a3a286` |
| `check_jsonschema-0.38.2.tar.gz` | `967176475f9eddd2809baabf7e0d157f7eb482b06ac002a29a79788c0c8a5a90` |
| `cogapp-3.6.0-py3-none-any.whl` | `6ea11c63221f92978d37d8d76208eadeae2a6e4641d323f165738a5464a19d32` |
| `cogapp-3.6.0.tar.gz` | `ec2a9170bfa644bf0d91996fdb5576c13d7e5e848bb2378a6f92727b48f92604` |

Sources: [commitizen PyPI JSON](https://pypi.org/pypi/commitizen/4.19.0/json), [check-jsonschema PyPI JSON](https://pypi.org/pypi/check-jsonschema/0.38.2/json), and [cogapp PyPI JSON](https://pypi.org/pypi/cogapp/3.6.0/json). `diff -qr` returned exit 0 for each clone package tree against both its wheel and source distribution package tree. Every wheel reports `Root-Is-Purelib: true` and `Tag: py3-none-any`; a `find` over the extracted artifacts returned no `.pth`, `.so`, `.dll`, `.dylib`, or `.exe` file.

## commitizen 4.19.0

### Findings

#### C-1 — Medium: `--files-only` executes pre-bump hooks through a shell with the full environment

`Bump` reads `pre_bump_hooks` from configuration at `commitizen/commands/bump.py:98-106`. The command updates version files and the version provider, then runs those hooks, and only afterward exits for `--files-only` or `--version-files-only` at `commitizen/commands/bump.py:351-385`. Each configured hook is passed as a string at `commitizen/hooks.py:13-23`; the hook environment begins as a copy of all `os.environ` at `commitizen/hooks.py:26-34`. A string passed to `run_interactive` runs with `shell=True` at `commitizen/cmd.py:108-130`.

This is arbitrary command execution and can expose inherited credentials. It is medium, not high, for this plan because hooks default to empty (`commitizen/defaults.py:82-111`) and an attacker must change trusted repository configuration or another selected config file. There is no reviewed command-line switch that disables hooks. Require `pre_bump_hooks = []` and `post_bump_hooks = []` in the reviewed configuration, and do not run the bump command on an unreviewed configuration with secrets present. `--get-next` exits at `commitizen/commands/bump.py:251-290` before file writes or hooks, so prefer it when only the computed version is needed.

#### C-2 — Low: plugin discovery eagerly imports installed modules and entry points

At import time, Commitizen enumerates top-level modules on `sys.path`, imports every `cz_*` module, and loads every `commitizen.plugin` entry point (`commitizen/cz/__init__.py:16-43`). It also loads every changelog-format entry point (`commitizen/changelog_formats/__init__.py:58-61`); bump initialization reaches format selection at `commitizen/commands/bump.py:115-121`. `cz check` creates the selected Commitizen implementation at `commitizen/commands/check.py:81-85`.

Importing a Python module executes its top-level code. This is low for the planned use because the environment is intended to be lockfile-pinned and no outside plugins are planned. Run Commitizen in a dedicated locked environment, do not add third-party Commitizen plugins or stray `cz_*` modules, and treat any dependency change as executable-code review. The reviewed source exposes no plugin-discovery-off flag.

#### C-3 — Low: configured version paths and the version provider can write beyond the intended Markdown line

`version_files` entries are expanded with `iglob`, opened, and rewritten without a working-tree containment check at `commitizen/bump.py:65-130`. An absolute path or `..` path supplied by configuration can therefore target another writable file. In addition, bump always calls `provider.set_version` after updating `version_files` (`commitizen/commands/bump.py:351-361`); the default `commitizen` provider writes the version back to the selected configuration (`commitizen/providers/commitizen_provider.py:7-18`).

This is low because CHE-44 plans one reviewed, literal repository-relative Markdown target. Use a literal repository-relative path with no glob, absolute prefix, or `..`; keep `--check-consistency`; and account for the provider's configuration write. If the requirement is strictly one Markdown-line write, choose and review a version-provider setup that does not cause an unintended second file change.

### Eight-point review

1. **Install and build behavior.** The wheel is pure Python and has no project install or post-install script. The source distribution declares `uv_build` as its PEP 517 build backend at `pyproject.toml:135-137`, with only module layout settings at `pyproject.toml:151-154`. Prefer the wheel so installation does not invoke the source build backend. The console entry points are declared at `pyproject.toml:58-60`.

2. **Downloaded binaries, models, or data.** The project declares Python dependencies at `pyproject.toml:15-31`; an installer will obtain those and the Commitizen wheel from its configured package index. The reviewed Commitizen runtime contains no binary, model, or data downloader. A package-source search, `rg -n 'requests\.|httpx\.|urllib\.(request|urlopen)|urlopen\(|socket\.|telemetry|sentry' commitizen`, returned no match. Artifact integrity is covered under point 8.

3. **Network calls and telemetry.** The planned commands have no Commitizen network or telemetry path. `cz bump` shells out to local Git using argument lists for tag and log reads (`commitizen/git.py:240-268` and `commitizen/git.py:331-351`). With `--files-only`, execution exits before Git add, commit, tag, or post-bump hooks (`commitizen/commands/bump.py:377-438`). No telemetry-off setting is needed. Repository-configured hooks or imported plugins remain able to use the network because they are arbitrary code.

4. **Code execution and shell-outs.** The planned bump reads local Git history and tags. The built-in Git calls use argument arrays and `shell=False` through `cmd.run` (`commitizen/cmd.py:75-92`). C-1 covers shell hooks; C-2 covers plugin imports. With no changelog requested, the changelog generation and template-rendering branch at `commitizen/commands/bump.py:313-345` is not reached. `cz check --commit-msg-file` reads the named file at `commitizen/commands/check.py:120-138`; it does not run bump hooks.

5. **Writes outside the working folder.** The reviewed runtime has no home-folder cache or global configuration writer. `--get-next` makes no tool file write. `--files-only` writes matched `version_files` plus the configured version provider as described in C-3. It does not create a commit or tag. Hooks and plugins can write anywhere allowed by the process.

6. **Credentials.** The core tool has no reviewed token, keychain, or credential-store handling. Local Git subprocesses inherit the process environment. More importantly, pre-bump hooks receive the complete environment (`commitizen/hooks.py:26-34`), and imported plugins share the process. Do not expose release, package, or service tokens to a run that consumes unreviewed configuration or plugins.

7. **Published advisories for 4.19.0.** An exact OSV query for PyPI `commitizen` version `4.19.0` returned `{}`. The exact [PyPI JSON record](https://pypi.org/pypi/commitizen/4.19.0/json) has an empty `vulnerabilities` array, and the [repository advisory page](https://github.com/commitizen-tools/commitizen/security/advisories) reports no published repository security advisories. GitHub's unauthenticated REST advisory API returned HTTP 403 due to rate limiting, so a separate live global GitHub API result was not established; OSV and PyPI were the global/version checks available in this run.

8. **Signing, provenance, and checksums.** Both PyPI artifacts have one PyPI Publish attestation. The integrity response names GitHub publisher `commitizen-tools/commitizen`, workflow `pythonpublish.yml`; its certificate subject alternative name is `https://github.com/commitizen-tools/commitizen/.github/workflows/pythonpublish.yml@refs/tags/v4.19.0`. The workflow grants `id-token: write`, builds with `uv build`, and publishes through PyPA's action at `.github/workflows/pythonpublish.yml:18-44`. The Git tag is annotated but contains no PGP or SSH signature block. The downloaded package code matches the tag clone, and its SHA-256 values match PyPI. Evidence endpoints: [wheel provenance](https://pypi.org/integrity/commitizen/4.19.0/commitizen-4.19.0-py3-none-any.whl/provenance) and [sdist provenance](https://pypi.org/integrity/commitizen/4.19.0/commitizen-4.19.0.tar.gz/provenance). PyPI documents that these are publish attestations, not a claim that the build is reproducible or safe: [attestations](https://docs.pypi.org/attestations/) and [security model](https://docs.pypi.org/attestations/security-model/).

**Verdict:** No high finding stands. One medium finding stands for `--files-only`: pre-bump hooks execute before the command exits. Keep both bump-hook lists empty, use a dedicated hash-locked environment with no outside plugins, use literal contained `version_files`, and prefer `--get-next` where no write is needed.

## check-jsonschema 0.38.2

### Findings

#### J-1 — Medium: no true offline mode; a remote or relative `$ref` can trigger unrestricted HTTP(S)

A local `--schemafile` uses `LocalSchemaReader` (`src/check_jsonschema/schema_loader/main.py:93-127` and `src/check_jsonschema/schema_loader/readers.py:36-52`). The registry registers that schema under both its retrieval URI and `$id` (`src/check_jsonschema/schema_loader/resolver.py:14-39`). Therefore, the planned remote-looking `$id` and local `#/$defs` fragments do not themselves require network access.

However, reference retrieval resolves relative references against `$id` and sends any resulting HTTP(S) URI to `CacheDownloader` (`src/check_jsonschema/schema_loader/resolver.py:42-86`). The downloader calls `requests.get(file_url, stream=True)` with no timeout at `src/check_jsonschema/cachedownloader.py:57-74`. The only relevant flag, `--no-cache`, is explicitly documented as "Always download remote schemas" (`src/check_jsonschema/cli/main_command.py:123-127`); it is not an offline flag.

This is medium because today's reviewed schema shape stays local, but a future schema edit can silently add network access, including a request to an attacker-chosen host. Pass `--no-cache` to prevent persistent home-cache writes, keep all references as local fragments, and enforce offline behavior with an operating-system or CI egress deny rule. Do not rely on `--no-cache` for offline operation.

#### J-2 — Low: remote schemas and references have no content checksum or signature verification

Remote content is accepted when it parses (`src/check_jsonschema/cachedownloader.py:206-214`). The cache names files with a SHA-256 of the URL, not the content (`src/check_jsonschema/cachedownloader.py:100-116`), and considers a cache entry current by comparing its writable local mtime with the HTTP `Last-Modified` value (`src/check_jsonschema/cachedownloader.py:88-97`). No expected content digest or signature is checked before validation.

This is low for CHE-44 because the planned schema and every reference are local. `--no-cache` avoids persistent cached copies, but it does not add integrity and instead forces downloads when a remote reference exists. Preserve the local-only schema rule and block egress; if a remote schema is ever required, vendor and hash it first.

#### J-3 — Low: optional validator-class loading imports arbitrary Python

`--validator-class` accepts a module and class name (`src/check_jsonschema/cli/main_command.py:195-203`), then calls `importlib.import_module` at `src/check_jsonschema/cli/param_types.py:70-123`. This is arbitrary top-level Python execution from the active environment.

This is low because the planned command does not pass the option. Do not add `--validator-class`, and keep the execution environment locked.

### Eight-point review

1. **Install and build behavior.** The wheel is pure Python and has no project install or post-install script. The source distribution uses `setuptools.build_meta` with `setuptools>=61.2` (`pyproject.toml:1-3`), without a custom build hook or `setup.py`; the console entry point is at `pyproject.toml:55-56`. Prefer the wheel to avoid a source build.

2. **Downloaded binaries, models, or data.** Installation obtains the declared Python dependencies from the configured package index (`pyproject.toml:39-46`). The project has no model or binary downloader. At runtime it can download a schema or referenced JSON document over HTTP(S), as covered in J-1. The content is parse-checked but not cryptographically verified, as covered in J-2.

3. **Network calls and telemetry.** `CacheDownloader` is the runtime network path; it performs up to three Requests attempts at `src/check_jsonschema/cachedownloader.py:57-74`. A direct remote `--schemafile` selects `HttpSchemaReader` at `src/check_jsonschema/schema_loader/main.py:118-127` and `src/check_jsonschema/schema_loader/readers.py:72-100`. A local schema can reach the same downloader through an external `$ref` at `src/check_jsonschema/schema_loader/resolver.py:59-86`. `$schema` is passed to `jsonschema.validators.validator_for` in `src/check_jsonschema/schema_loader/main.py:155-172`; this source does not send `$schema` to the downloader. No telemetry sender was found. There is no network-off switch.

4. **Code execution and shell-outs.** Normal planned validation parses local JSON and invokes the `jsonschema` validator; input files are parsed then closed at `src/check_jsonschema/instance_loader.py:29-52`. No subprocess or shell API occurs in the package source. J-3 is the optional Python-import path. JSON parsing uses `orjson` if already present, otherwise the standard library (`src/check_jsonschema/parsers/json_.py:1-29`); it does not evaluate input as code.

5. **Writes outside the working folder.** A remote schema is cached under `%LOCALAPPDATA%` or `%APPDATA%` on Windows, `~/Library/Caches/check_jsonschema/{schemas,refs}` on macOS, and `${XDG_CACHE_HOME:-~/.cache}/check_jsonschema/{schemas,refs}` on Linux (`src/check_jsonschema/cachedownloader.py:19-42`). Downloads also use a system temporary file before copying to the cache (`src/check_jsonschema/cachedownloader.py:77-85`). `--no-cache` keeps remote bytes in memory (`src/check_jsonschema/cachedownloader.py:155-170`) and prevents those cache writes. With the planned local schema, local instances, fragment-only references, and `--no-cache`, the core tool has no file-write path.

6. **Credentials.** The reviewed code passes only the URL and `stream=True` to Requests (`cachedownloader.py:57-74`); it has no explicit token, authorization-header, keychain, or credential-store logic. Do not embed credentials in schema URLs. Any behavior inherited from Requests outside this clone, such as environment proxy handling, was not independently audited here.

7. **Published advisories for 0.38.2.** The repository has [GHSA-q6mv-284r-mp36](https://github.com/python-jsonschema/check-jsonschema/security/advisories/GHSA-q6mv-284r-mp36), also `CVE-2024-53848` and `PYSEC-2026-1245`, for cache confusion in versions before 0.30.0; OSV records `fixed: 0.30.0`, so 0.38.2 is not affected. An exact OSV query for 0.38.2 returned `{}`, and the exact [PyPI JSON record](https://pypi.org/pypi/check-jsonschema/0.38.2/json) has an empty `vulnerabilities` array. GitHub's unauthenticated REST advisory API cross-check was rate-limited with HTTP 403.

8. **Signing, provenance, and checksums.** Both PyPI artifacts have one PyPI Publish attestation naming GitHub publisher `python-jsonschema/check-jsonschema` and workflow `publish_to_pypi.yaml`. Its certificate subject alternative name is `https://github.com/python-jsonschema/check-jsonschema/.github/workflows/publish_to_pypi.yaml@refs/tags/0.38.2`. The workflow builds distributions and publishes with OpenID Connect at `.github/workflows/publish_to_pypi.yaml:1-46`. The annotated Git tag contains a PGP signature block, but its signer trust was not verified locally. The downloaded package code matches the tag clone and its SHA-256 values match PyPI. Evidence endpoints: [wheel provenance](https://pypi.org/integrity/check-jsonschema/0.38.2/check_jsonschema-0.38.2-py3-none-any.whl/provenance) and [sdist provenance](https://pypi.org/integrity/check-jsonschema/0.38.2/check_jsonschema-0.38.2.tar.gz/provenance).

**Verdict:** No high finding stands. One medium finding stands because the CLI cannot itself guarantee offline operation. Use `--no-cache`, keep only local fragment references, prohibit `--validator-class`, and enforce egress denial around the process.

## cogapp 3.6.0

### Findings

#### G-1 — Medium: drift-check mode executes embedded Python without a sandbox

Cog compiles the Markdown generator block in `exec` mode and evaluates it at `cogapp/cogapp.py:141-177`. Processing creates an ordinary globals dictionary at `cogapp/cogapp.py:435-449`; Python inserts normal builtins when `eval` receives globals without `__builtins__`, so generator code can import modules, read environment variables, access files, open network connections, or start processes ([Python `eval` documentation](https://docs.python.org/3/library/functions.html#eval)).

`--check` only controls replacement behavior. It still calls `process_string`, which reaches `gen.evaluate`, at `cogapp/cogapp.py:681-704` and `cogapp/cogapp.py:559-569`. Thus a drift check is code execution, not a safe parser check.

This is medium because arbitrary code has high impact, but the planned generators are repository-owned and must be changed before exploitation. If an untrusted pull request can modify those Markdown blocks and the check runs with secrets, treat the run as high risk. Execute Cog only after reviewing generator changes, in a secret-free sandbox with no network and only required filesystem access. Do not infer safety from `--check`.

#### G-2 — Low: optional `-w` uses an operator-supplied shell command

If `-w CMD` is supplied for a non-writable target, Cog replaces `%s` with the filename and passes the resulting string to `os.popen` (`cogapp/cogapp.py:635-645`). A crafted filename can become shell syntax. Options `-p` and `-I` also add executable Python or import paths (`cogapp/cogapp.py:260-306` and `cogapp/cogapp.py:653-676`).

This is low because none of these options is part of the planned invocation and the embedded Python path in G-1 already represents the intended execution boundary. Do not use `-w`, `-p`, or unreviewed `-I` values.

#### G-3 — Low: PyPI artifacts have checksums but no PyPI provenance attestation

The PyPI integrity endpoints for both 3.6.0 artifacts returned HTTP 404 with `No provenance available`. The [PyPI release page](https://pypi.org/project/cogapp/3.6.0/) reports that Trusted Publishing was not used. The release Makefile builds with `python -m build`, uploads with `twine upload`, checks `TWINE_PASSWORD`, and then creates a signed Git tag (`Makefile:53-77`). The cloned tag object contains an SSH signature block, but signer trust was not verified locally.

This is low because both artifact SHA-256 values are available, the downloaded package trees match the tagged package source, and CHE-44 uses a pinned lockfile. Retain the exact artifact hash in the lockfile and prefer the wheel. This does not replace publisher provenance; upstream Trusted Publishing would reduce the gap.

### Eight-point review

1. **Install and build behavior.** The wheel is pure Python and defines only the `cog` console entry point (`pyproject.toml:25-26`). There is no install or post-install script. The source distribution uses `setuptools.build_meta` and dynamically reads the version attribute (`pyproject.toml:38-46`); prefer the wheel so the source build backend is not invoked.

2. **Downloaded binaries, models, or data.** `pyproject.toml:1-46` declares no runtime dependency and the package has no built-in binary, model, or data downloader. The package-source search for Requests, HTTPX, URL-opening, sockets, telemetry, and Sentry returned no match. Embedded generator code has the full Python capability described in G-1 and can download anything its author writes; Cog applies no checksum policy to that user code.

3. **Network calls and telemetry.** Cog's own runtime has no reviewed network or telemetry sender and needs no telemetry-off flag. Embedded code can make arbitrary network calls. Enforce the desired offline policy outside Cog.

4. **Code execution and shell-outs.** Executing embedded Python is Cog's core behavior and remains active under `--check` (G-1). `-p` prepends more Python before compilation (`cogapp/cogapp.py:149-152`), and input-file directories plus `-I` paths are added to `sys.path` (`cogapp/cogapp.py:653-676`). The optional shell path is G-2. These are not sandboxed.

5. **Writes outside the working folder.** Core `--check` reads the input, generates output in memory, compares it, and sets `check_failed` without replacing the file (`cogapp/cogapp.py:681-704`). There is no Cog home cache or global config. Other options can write any supplied output path and create directories (`cogapp/cogapp.py:392-402`), while `-r` replaces the input (`cogapp/cogapp.py:635-651`). Embedded code can write any process-accessible path even during `--check`.

6. **Credentials.** Cog has no runtime token, keychain, or credential-store feature. Embedded code shares the process and can read inherited environment variables or call credential libraries. The `TWINE_PASSWORD` check at `Makefile:73-77` is an upstream release procedure, not installed runtime behavior. Run planned generators without unrelated credentials.

7. **Published advisories for 3.6.0.** An exact OSV query for PyPI `cogapp` version `3.6.0` returned `{}`. The exact [PyPI JSON record](https://pypi.org/pypi/cogapp/3.6.0/json) has an empty `vulnerabilities` array, and the [repository advisory page](https://github.com/nedbat/cog/security/advisories) reports no published repository security advisories. GitHub's unauthenticated REST advisory API cross-check was rate-limited with HTTP 403.

8. **Signing, provenance, and checksums.** G-3 covers the missing PyPI provenance. Both downloaded hashes match PyPI, and the wheel and source-distribution package trees match the `v3.6.0` clone. The tag contains an SSH signature block but was not cryptographically verified against a trusted signer in this run. Pin the wheel hash in the uv lockfile; there is no signature or attestation on the PyPI artifact itself that this review could verify.

**Verdict:** No high finding stands. One medium finding stands by design: even `--check` runs repository-embedded Python with full process authority. Use only reviewed generator blocks, no `-w` or `-p`, and run in a secret-free, egress-denied sandbox with restricted filesystem access.

## Advisory query evidence and limitations

The exact OSV requests were of this form, substituting each package and version:

```sh
curl -sS -X POST https://api.osv.dev/v1/query \
  -H 'Content-Type: application/json' \
  -d '{"package":{"ecosystem":"PyPI","name":"commitizen"},"version":"4.19.0"}'
```

Each exact query returned `{}`. Running `jq '.vulnerabilities | length'` on each exact PyPI JSON response returned `0`. For the historical check-jsonschema advisory, the OSV record for `GHSA-q6mv-284r-mp36` returned aliases `CVE-2024-53848,PYSEC-2026-1245` and fixed version `0.30.0`.

Published-advisory results are a dated lookup, not proof that no undisclosed vulnerability exists. The direct GitHub REST checks were not established because the shared unauthenticated address was rate-limited; this limitation does not change the source findings or the OSV and PyPI exact-version results above.
