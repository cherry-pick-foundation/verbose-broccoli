# Security review: mise 2026.9.16

Reviewed 2026-09-30 for CHE-44. The source is the supplied `mise-v2026.9.16`
clone at tag `v2026.9.16`, commit
`2184db810a7e2c29475abdba53e5af910e96859a`. All source paths below are relative
to that clone.

## Scope and method

This is a read-only source review of the paths reached by the planned use:

- install uv 0.11.32, lychee 0.24.2, and Vale 3.23.0 through the Aqua backend;
- install git-flow-next 2.1.0 through the GitHub backend;
- install Node.js 24 through the core Node backend;
- optionally use a committed `mise.lock` with `mise install --locked`;
- trust the repository configuration and run `mise doctor project` checks;
- do not use mise tasks, environment plugins, hooks, or `[env]` scripts.

I inspected the clone, the installed Debian package, its cached `.deb`, and
public release metadata. I did not run mise, any installed tool, any test, any
build, or any install script. I also did not inspect the internals of the five
downloaded tools; this review covers mise's acquisition and execution of them.

Finding counts: **0 high, 4 medium, 3 low**.

## Verdict

**mise 2026.9.16 has four medium findings for this planned use.** The release
is usable if the repository treats `mise.toml` and `mise.lock` as executable
supply-chain inputs, uses content-bound trust, rechecks supported provenance,
and accepts or separately closes the remaining upstream authenticity gaps.
The exact Debian package has no install scripts and the installed binary
matches the cached package.

Required settings and operating rules are listed under [Required controls](#required-controls).

## Findings

### M-1 — Trusted project diagnostics execute repository shell commands

**Severity: medium.** Once trusted, `[doctor.checks]` commands run as the user,
with the project environment and installed tools, without a sandbox. Normal
trust is path-based, so a later branch checkout or edit remains trusted. This
is a direct user-level code-execution path in the planned use.

Evidence:

- Normal execution commands can persist trust automatically, while paranoid
  mode disables that behavior: `src/config/config_file/mod.rs:518-571`.
- Normal trust records the path; only paranoid trust also records the file's
  SHA-256 hash: `src/config/config_file/mod.rs:848-860`.
- A configured trusted path matches every canonicalized descendant:
  `src/config/config_file/mod.rs:574-652` and
  `src/config/config_file/mod.rs:677-703`.
- Even in paranoid mode, `trusted_config_paths` remains a path-based exception:
  `docs/paranoid.md:7-10` and `docs/paranoid.md:28-43`.
- `mise doctor project` loads installed tools and runs checks concurrently:
  `src/cli/doctor/project.rs:120-217`.
- Each check is handed to `CmdLineRunner` with the project environment and an
  optional working directory: `src/cli/doctor/project.rs:220-262`.
- The project-diagnostics documentation states that checks are not sandboxed
  and that `dir` may escape the repository root:
  `docs/configuration/project-diagnostics.md:65-81`.

Mitigation: enable global `paranoid = true`; inspect with `mise trust --show`;
trust the specific reviewed `mise.toml`; re-review and re-trust after every
content change. Do not use `trusted_config_paths` or monorepo-root trust for
this repository because both bypass the content hash. Review
`[doctor.checks]`, `shell`, and `dir` as executable code.

### M-2 — Lockfile provenance is trusted instead of reverified by default

**Severity: medium.** The optional lockfile contains download URLs, checksums,
and provenance labels. Aqua and GitHub installs reuse its URLs. When a platform
entry already has a checksum and provenance, the default is to trust that
record without repeating the cryptographic check. A malicious or incorrectly
generated repository lockfile can therefore select executable bytes and make
them appear previously verified.

Evidence:

- A lock entry stores `url`, `url_api`, `checksum`, and `provenance`:
  `src/lockfile.rs:465-485`.
- Aqua uses the existing lockfile URL in locked mode:
  `src/backend/aqua.rs:402-425`.
- The GitHub backend likewise constructs the release asset from the lockfile
  URL: `src/backend/github.rs:918-934`.
- The GitHub install path skips provenance detection when the lockfile has only
  a checksum, and reuses recorded provenance unless forced:
  `src/backend/github.rs:1734-1797`.
- The Aqua install path has the same reuse behavior:
  `src/backend/aqua.rs:2702-2779`.
- `locked_verify_provenance` defaults to `false`; the setting description says
  that the lockfile is trusted to avoid the repeat check:
  `settings.toml:1751-1765`.
- Paranoid mode forces supported provenance checks again, but cannot add a
  verification method the backend does not support:
  `docs/paranoid.md:69-81`.

Mitigation: generate the lockfile only from a reviewed configuration, review
all URL/checksum/provenance changes, commit it, and use `--locked`. Set
`locked_verify_provenance = true` or use paranoid mode. This improves uv and
other supported paths, but does not repair the unsupported provenance noted in
M-3 or Node's separate lock behavior in M-4.

### M-3 — Three planned binary paths do not establish publisher identity

**Severity: medium.** Every affected archive gets an integrity check, but
lychee and git-flow-next have no attestation for the exact Linux asset, and
Vale's available GitHub attestation is not requested by mise's Aqua metadata.
Checksums or API digests delivered through the same GitHub release channel
detect corruption but do not independently authenticate the publisher. These
archives become executable user-level tools.

Evidence from the embedded Aqua registry:

- uv 0.11.32 uses a per-asset SHA-256 file and requires a GitHub attestation
  from `astral-sh/uv/.github/workflows/release.yml`:
  `vendor/aqua-registry/registry.yml:17396-17422`.
- lychee 0.24.2 has an archive mapping but no checksum or provenance stanza:
  `vendor/aqua-registry/registry.yml:65284-65300`.
- Vale 3.23.0 has a release checksum file but no provenance stanza:
  `vendor/aqua-registry/registry.yml:101769-101784`.
- Aqua provenance detection depends on registry metadata:
  `src/backend/aqua.rs:1337-1365`. GitHub release assets can still use the
  GitHub API digest as a checksum: `src/backend/aqua.rs:255-297`.
- The generic GitHub backend attempts an attestation when one is available but
  accepts an artifact with no required provenance:
  `src/backend/github.rs:1279-1388` and
  `src/backend/github.rs:2690-2900`.

Exact public release metadata was queried through the same mise-versions API
that mise uses. The relevant Linux x86-64 results were:

```text
uv uv-x86_64-unknown-linux-musl.tar.gz
  sha256:1fd052f196108d87e61fc3d98fe06b4ec758c9a1eb1466a6fd1a436fe45885f2 attestations=2
lychee lychee-x86_64-unknown-linux-musl.tar.gz
  sha256:73657a111819a30c47c08352896796f23d64e4eb2b3ed39b6d32149241566fc5 attestations=0
vale vale_3.23.0_Linux_64-bit.tar.gz
  sha256:cc35445a45186b8f0b01e11c01359694cf941e72cf6ab0fc44774f0e54c9d5fc attestations=1
git-flow-next git-flow-next-v2.1.0-linux-amd64.tar.gz
  sha256:e335b5818f2b2f820c17844c194030d0db78f3cdfa9bb999fcb9ce092ba9ecd2 attestations=0
```

Reproducible query pattern, run on 2026-09-30:

```sh
curl -fsS \
  "https://mise-versions.jdx.dev/api/github/repos/OWNER/REPO/releases/TAG" |
  jq -r --arg asset "ASSET" '.assets[] | select(.name==$asset) | [.name,.digest]'
curl -fsS \
  "https://mise-versions.jdx.dev/api/github/repos/OWNER/REPO/attestations/DIGEST" |
  jq '.attestations | length'
```

Mitigation: keep all checksum and attestation settings enabled. For uv, require
the configured GitHub attestation and recheck it at install time. For Vale,
patch or update the registry metadata to require its exact release workflow
before relying on the attestation. For lychee and git-flow-next, obtain a
publisher-authenticated signature or attestation, or independently approve and
pin the exact archive digest above. A checksum copied only from the same GitHub
release is not an independent substitute.

### M-4 — A Node lock entry bypasses the normal OpenPGP check

**Severity: medium.** Without a matching lock entry, Node 24 downloads
`SHASUMS256.txt` and normally verifies its OpenPGP signature with bundled Node
keys. Lock generation records a checksum from that unsigned manifest. A later
install with the same lock URL/checksum skips `get_checksum`, so it also skips
the signature check. On the unlocked path, an HTTP 404 for the signature is
only a warning and verification continues.

Evidence:

- `fetch_tarball` calls `get_checksum` only when the lock entry lacks a matching
  checksum, URL, or install mode: `src/plugins/core/node.rs:262-314`.
- `get_checksum` downloads `SHASUMS256.txt`; Node versions beginning with `2`
  enter OpenPGP verification unless explicitly disabled:
  `src/plugins/core/node.rs:358-383`.
- A missing `.sig` response with status 404 warns and succeeds:
  `src/plugins/core/node.rs:385-408`.
- The verifier uses bundled Node keys in process, not an external `gpg` command:
  `crates/mise-util/src/gpg.rs:10-64`.
- Lock generation fetches the checksum manifest and records its value without
  calling the signature verifier: `src/plugins/core/node.rs:870-930`.
- Node verification defaults on: `settings.toml:2124-2128`. The OpenPGP option
  is documented at `settings.toml:2063-2067`.

Mitigation: keep `node.verify = true` and set `node.gpg_verify = true`, but do
not treat a mise-generated Node lock checksum as publisher-authenticated.
Before committing the Node 24 lock entry, independently verify the exact Node
`SHASUMS256.txt.sig` against the official Node release keys and approve the
recorded archive digest. Otherwise omit the Node entry from the lock until mise
verifies the signature during lock generation or install.

### L-1 — Anonymous install tracking is on by default

**Severity: low.** A successful install sends the tool identifier, requested
form, version, operating system, and architecture to
`mise-versions.jdx.dev`. The service documentation also says it derives a
daily hashed IP. This is metadata disclosure, not code execution or credential
loss.

Evidence:

- `track_install` is fire-and-forget and posts the fields to
  `https://mise-versions.jdx.dev/api/tools/<tool>`:
  `src/versions_host.rs:152-225`.
- `use_versions_host_track` defaults to true and documents the collected data:
  `settings.toml:4000-4016`.

Mitigation: set `use_versions_host_track = false` or
`MISE_USE_VERSIONS_HOST_TRACK=false`. The separate
`use_versions_host = true` metadata cache can remain enabled for version,
digest, and attestation queries.

### L-2 — The APT package is repository-signed, not individually attested

**Severity: low.** The Debian package has no maintainer scripts and APT uses a
dedicated signing key. The release workflow signs APT `Release` metadata that
contains package-index hashes. The `.deb` itself is not individually signed or
included in the GitHub release attestation set, so the exact historical
signature chain cannot be reconstructed from the cached package alone after
the live APT index advances. This is an auditability gap; it is not evidence
that APT skipped verification at install time.

Evidence:

- The configured source is `https://mise.jdx.dev/deb` with
  `Signed-By: /var/lib/extrepo/keys/mise.asc`:

  ```text
  $ nl -ba /etc/apt/sources.list.d/extrepo_mise.sources
       1  Components: main
       2  Enabled: yes
       3  Signed-By: /var/lib/extrepo/keys/mise.asc
       4  Suites: stable
       5  Types: deb
       6  Uris: https://mise.jdx.dev/deb
  ```

- The Debian build creates `Packages`, hashes it into `Release`, then signs
  `Release.gpg` and `InRelease`: `scripts/build-deb.sh:37-51` and
  `packaging/deb/generate-release.sh:8-34`.
- The `.deb` job uses a digest-pinned container and commit-pinned GitHub
  Actions: `.github/workflows/release.yml:386-410`.
- The GitHub release assets are assembled separately from tar/zip artifacts
  and attested from `SHASUMS256.txt`:
  `.github/workflows/release.yml:526-533` and
  `.github/workflows/release.yml:606-623`. The APT pool is uploaded separately:
  `scripts/publish-s3.sh:61-62`.
- The exact cached package hash is:

  ```text
  $ sha256sum /var/cache/apt/archives/mise_2026.9.16_amd64.deb
  a2e39998fb9653c3377df3f1ab3218a73466c9ff7911a06532b3a6b3f67baf48  /var/cache/apt/archives/mise_2026.9.16_amd64.deb
  ```

Mitigation: keep APT signature checking enabled and pin the exact package
version. If long-term auditability matters, retain the signed `InRelease`,
`Release`, and `Packages` files that authenticated this `.deb`, or ask upstream
to include the `.deb` in its GitHub artifact attestation.

### L-3 — Node installation can run unplanned local package and build commands

**Severity: low.** The planned Node install is a prebuilt archive, but mise may
fall back to a source build when the prebuilt asset is missing unless
compilation is disabled. It also reads the user's default npm package file and
runs `npm install --global` for every entry. Those npm packages may have their
own lifecycle scripts. This needs local configuration or a missing prebuilt
archive and is outside the stated repository plan, so low fits.

Evidence:

- A missing prebuilt archive falls back to source compilation when not locked
  and compilation is not disabled: `src/plugins/core/node.rs:120-152`.
- Source installation extracts input, applies patches, and executes configure,
  make, and make-install commands: `src/plugins/core/node.rs:175-220` and
  `src/plugins/core/node.rs:317-355`.
- The default package path is normally `~/.default-npm-packages` and each line
  is passed to `npm install --global`: `settings.toml:2036-2055` and
  `src/plugins/core/node.rs:449-477`.
- Every Node install also executes the installed `node -v` and `npm -v`, writes
  an npm shim by default, and can enable Corepack:
  `src/plugins/core/node.rs:480-535` and
  `src/plugins/core/node.rs:706-751`.

Mitigation: set `node.compile = false`; ensure all legacy default npm package
files are absent, or set `node.default_packages_file` to a reviewed empty file.
Leave `node.corepack` off unless it is intentionally needed.

## Coverage of the requested review points

### 1. Install, post-install, and build scripts

The installed artifact is a Debian binary package. Its control archive has no
`preinst`, `postinst`, `prerm`, or `postrm` files:

```text
$ dpkg-deb --ctrl-tarfile /var/cache/apt/archives/mise_2026.9.16_amd64.deb | tar -tf -
./
./control
./md5sums
```

The cached package reports version 2026.9.16. The packaged binary and installed
binary match:

```text
$ dpkg-deb --fsys-tarfile /var/cache/apt/archives/mise_2026.9.16_amd64.deb | tar -xOf - ./usr/bin/mise | sha256sum
b6f8757201f6a2ee799f45f3f52ef7ca0b4071523637dc3b0b24264dd3333518  -
$ sha256sum /usr/bin/mise
b6f8757201f6a2ee799f45f3f52ef7ca0b4071523637dc3b0b24264dd3333518  /usr/bin/mise
```

The source has a Rust `build.rs`. It generates compiled-in data; on macOS only,
it invokes the compiler and `/usr/bin/codesign` and writes under Cargo's
`OUT_DIR`: `build.rs:20-40` and `build.rs:62-135`. That build hook does not run
when installing the reviewed `.deb`. The repository `package.json` has only
test and documentation scripts, with no npm lifecycle script:
`package.json:10-15`.

The Aqua and GitHub paths download and extract release archives; they do not
run an upstream installer from those archives in the reviewed paths. Node's
post-download executions are described in L-3.

### 2. Binaries, models, or data downloaded and their verification

No models are downloaded. The planned downloads are executable archives plus
release metadata, checksums, signatures, or attestations.

| Tool | Source | Integrity check | Publisher authentication in this mise path |
|---|---|---|---|
| uv 0.11.32 | `github.com/astral-sh/uv` release archive via Aqua | Per-asset SHA-256 and GitHub API digest | GitHub attestation required by embedded Aqua metadata |
| lychee 0.24.2 | `github.com/lycheeverse/lychee` release archive via Aqua | GitHub API digest | None found for exact Linux asset |
| Vale 3.23.0 | `github.com/vale-cli/vale` release archive via Aqua | Release checksum file and GitHub API digest | Exact asset has an attestation, but Aqua metadata does not request it |
| git-flow-next 2.1.0 | `github.com/gittower/git-flow-next` release archive via GitHub backend | GitHub API digest or release checksum | None found for exact Linux asset |
| Node.js 24 | `nodejs.org/dist` by default | SHA-256 from `SHASUMS256.txt` | Built-in OpenPGP verification only on the unlocked checksum-fetch path; see M-4 |

`node@24` is a fuzzy request rather than an immutable patch release; mise's
architecture distinguishes a request such as `node@24` from its resolved
`ToolVersion`: `docs/architecture.md:92-94`. The reviewed lockfile flow can
record the exact resolved version. Without a reviewed lock entry, later clean
installs may select a newer Node 24 patch release.

Aqua downloads before verifying and then extracts the verified archive:
`src/backend/aqua.rs:402-584`. The GitHub equivalent is
`src/backend/github.rs:1669-1807`. Verification failures are fatal in these
paths; missing configured provenance is the gap, not a swallowed mismatch.

### 3. Network calls and telemetry

Expected network destinations are:

- `mise-versions.jdx.dev` for cached version lists, public GitHub release
  metadata, attestations, and enabled install tracking
  (`src/versions_host.rs:64-225` and `settings.toml:3964-4016`);
- `api.github.com`, `github.com`, and GitHub release-asset hosts for Aqua and
  GitHub release discovery, downloads, digests, checksums, and attestations;
- `nodejs.org/dist` for Node archives, checksums, and signatures
  (`src/config/settings.rs:1615` and `src/plugins/core/node.rs:358-408`);
- any explicitly configured mirror, URL replacement, credential command,
  Node patch URL, or doctor command destination.

Install tracking is the only default telemetry found and is covered by L-1.
OpenTelemetry traces and logs default off and apply to `mise run`, not the
planned doctor path: `settings.toml:2297-2332` and
`src/otel/mod.rs:22-35`. Automatic self-update defaults off and is global-only:
`settings.toml:297-310`.

`MISE_OFFLINE=1` blocks tracking and normal network use, but it is not suitable
for a first install. `use_versions_host = false` disables the metadata cache as
well as tracking; prefer disabling only `use_versions_host_track` unless the
cache itself is prohibited.

### 4. Code execution and shell-out paths

Reachable execution paths are:

- arbitrary doctor-check shell commands from trusted `mise.toml` (M-1);
- every downloaded tool binary when a doctor command calls it;
- Node's installed `node`, `npm`, optional Corepack, default npm packages, and
  source-build shell commands (L-3);
- a global-only `github.credential_command`, if the operator configures one,
  executed through `sh -c`: `settings.toml:925-942`.

The stated plan does not reach mise tasks, task hooks, environment plugins, or
`[env]` scripts. Project diagnostics do not install tools or run task
dependencies or hooks, but environment directives still evaluate:
`docs/configuration/project-diagnostics.md:65-68`.

### 5. Writes outside the working folder

On Linux, mise writes outside the repository by design:

- data, installs, downloads, plugins, shims, and command wrappers under
  `$MISE_DATA_DIR` (normally the XDG data directory, commonly
  `~/.local/share/mise`);
- caches under `$MISE_CACHE_DIR` (normally `~/.cache/mise`);
- global configuration and token fallback files under `$MISE_CONFIG_DIR`
  (normally `~/.config/mise`);
- trust records, OAuth tokens, tracked-config state, and other state under
  `$MISE_STATE_DIR` (normally `~/.local/state/mise`);
- temporary data under `$MISE_TMP_DIR` or the system temporary directory.

The environment-variable defaults are implemented at
`crates/mise-util/src/env.rs:142-182`; the derived install, download, and trust
paths are at `crates/mise-util/src/dirs.rs:9-27`. Trust itself writes under the
state directory: `src/config/config_file/mod.rs:848-860` and
`src/config/config_file/mod.rs:900-906`. Node writes its npm shim inside the
mise-managed Node install: `src/plugins/core/node.rs:480-484`.

The reviewed plan does not write system-wide locations during `mise install`.
Installing or upgrading the Debian package through APT is a separate privileged
operation that writes `/usr/bin/mise`, `/usr/lib/mise`, package-manager state,
and the manual page.

### 6. Credential handling

Public releases do not require credentials. If credentials are available,
mise can read `MISE_GITHUB_TOKEN`, `GITHUB_TOKEN`, its own token TOML, the `gh`
CLI config, native OAuth state, an explicit credential command, and—only when
enabled—Git credential helpers:
`crates/mise-util/src/github.rs:1137-1270`.

Authorization headers are limited to the relevant GitHub API and raw-content
hosts, not GitHub release-asset CDN hosts:
`crates/mise-util/src/github.rs:1284-1318`. Native OAuth tokens are stored in
`$MISE_STATE_DIR/github-oauth-tokens.toml` with Unix mode 0600:
`crates/mise-util/src/github/oauth.rs:480-533`. The fallback mise token file is
read from `$MISE_CONFIG_DIR/github_tokens.toml`:
`crates/mise-util/src/github.rs:1336-1356`.

The `gh` CLI token fallback defaults on:
`settings.toml:944-958`. Since all planned repositories are public, set
`github.gh_cli_tokens = false`, leave `github.credential_command` empty, and do
not export GitHub tokens for normal installation. If a token is needed for rate
limits, use a read-only, least-privilege token.

### 7. Published advisories for exact version 2026.9.16

No published GitHub advisory reviewed on 2026-09-30 lists 2026.9.16 as
affected. All nine repository advisories target earlier versions:

| Advisory | Severity | Fixed line shown by GitHub | Exact version result |
|---|---:|---:|---|
| [GHSA-6986-cq7v-7cj9](https://github.com/jdx/mise/security/advisories/GHSA-6986-cq7v-7cj9) | High | 2026.9.7 | 2026.9.16 is later |
| [GHSA-w8pw-h853-frw2](https://github.com/jdx/mise/security/advisories/GHSA-w8pw-h853-frw2) | Moderate | 2026.8.9 | 2026.9.16 is later |
| [GHSA-g74g-rg72-j2p3](https://github.com/jdx/mise/security/advisories/GHSA-g74g-rg72-j2p3) | High | 2026.7.14 | 2026.9.16 is later |
| [GHSA-9mm4-fgvc-x7rp](https://github.com/jdx/mise/security/advisories/GHSA-9mm4-fgvc-x7rp) | Moderate | 2026.7.1 | 2026.9.16 is later |
| [GHSA-77g9-363w-rccq](https://github.com/jdx/mise/security/advisories/GHSA-77g9-363w-rccq) | High | 2026.6.4 | 2026.9.16 is later |
| [GHSA-f94h-j2qg-fxw3](https://github.com/jdx/mise/security/advisories/GHSA-f94h-j2qg-fxw3) | Moderate | 2026.6.1 | 2026.9.16 is later |
| [GHSA-29hf-rm4x-xxph](https://github.com/jdx/mise/security/advisories/GHSA-29hf-rm4x-xxph) | Moderate | 2026.6.4 | 2026.9.16 is later |
| [GHSA-436v-8fw5-4mj8](https://github.com/jdx/mise/security/advisories/GHSA-436v-8fw5-4mj8) | High | 2026.6.4 | 2026.9.16 is later |
| [GHSA-fjj5-v948-whjj](https://github.com/jdx/mise/security/advisories/GHSA-fjj5-v948-whjj) | Critical | 2026.3.10 | 2026.9.16 is later |

The exact OSV query also returned no vulnerabilities:

```text
$ curl -fsS https://api.osv.dev/v1/query \
    -H 'Content-Type: application/json' \
    --data '{"version":"2026.9.16","package":{"name":"mise","ecosystem":"crates.io"}}' |
    jq '{vulns: [.vulns[]?.id]}'
{"vulns":[]}
```

The unauthenticated crates.io API returned HTTP 403 during this review, so a
separate crates.io registry advisory assertion is **unverified**. crates.io is
not the installed channel here. The installed channel is the upstream APT
repository described in L-2; no separate advisory feed was found for it.

### 8. Release signing, provenance, and checksums for installed mise

The supplied tag is annotated and embeds a PGP signature:

```text
$ git rev-parse 'refs/tags/v2026.9.16^{commit}'
2184db810a7e2c29475abdba53e5af910e96859a
$ git cat-file -p refs/tags/v2026.9.16 | rg -n 'BEGIN PGP SIGNATURE|END PGP SIGNATURE'
65:-----BEGIN PGP SIGNATURE-----
80:-----END PGP SIGNATURE-----
```

The tag signature's signer identity was not independently validated because an
out-of-band maintainer key was not supplied. For generic tar/zip releases, the
workflow produces SHA-256 and SHA-512 manifests, PGP-clearsigns them, adds a
Minisign signature, and signs the source tarball:
`scripts/release.sh:53-87`. GitHub Actions then attests the release asset
checksums: `.github/workflows/release.yml:606-623`.

The actual installed artifact is the APT `.deb`, not one of those generic
release archives. Its applicable chain is the APT `InRelease`/`Release` and
`Packages` hash chain in L-2. The cached `.deb` and installed binary hashes were
verified locally, but the exact historical signed index was not retained, so
independent end-to-end validation of that old APT transaction is unverified.

## Required controls

For this planned use:

1. Set global `paranoid = true`. Use direct, content-bound `mise trust` for the
   reviewed `mise.toml`; do not use `trusted_config_paths` or monorepo-root
   trust.
2. Set `locked_verify_provenance = true`. Generate and review `mise.lock`, then
   install with `--locked`; treat every URL, checksum, and provenance change as
   executable-code review.
3. Set `use_versions_host_track = false`. Keep `use_versions_host = true` only
   if the metadata cache is acceptable.
4. Keep `aqua.cosign`, `aqua.slsa`, `aqua.minisign`,
   `aqua.github_attestations`, and `github_attestations` enabled. They default
   on at `settings.toml:129-150`, `settings.toml:221-224`, and
   `settings.toml:1076-1085`. Do not downgrade after a verification failure.
5. Keep `node.verify = true` and set `node.gpg_verify = true`; set
   `node.compile = false`; remove or redirect the default npm package file to a
   reviewed empty file.
6. Set `github.gh_cli_tokens = false` and leave
   `github.credential_command` unset for these public repositories.
7. Close M-3 before treating all downloads as publisher-authenticated. In
   particular, add Vale's attestation metadata and obtain independent signed
   provenance or approved digests for lychee and git-flow-next.
8. Independently authenticate the Node archive digest recorded in the lockfile,
   because mise 2026.9.16 does not authenticate it during lock generation.

With these controls, uv's planned path has both integrity and authenticated
provenance. The remaining medium findings stand for trusted doctor commands,
lockfile handling, lychee/Vale/git-flow-next provenance, and Node lockfile
signature handling.

## Final per-tool verdict

**mise 2026.9.16: 0 high findings; 4 medium findings stand for the planned
use.** Set `paranoid = true`, `locked_verify_provenance = true`,
`use_versions_host_track = false`, `node.verify = true`,
`node.gpg_verify = true`, `node.compile = false`, and
`github.gh_cli_tokens = false`; use direct content-bound trust and `--locked`
only with a reviewed lockfile. These settings do not by themselves close the
upstream provenance gaps in M-3 or authenticate the Node checksum described in
M-4.
