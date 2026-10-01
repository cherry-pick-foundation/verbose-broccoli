# Caddy 2.11.4 security review

- Version: `v2.11.4` (released 2026-06-03, the latest stable release)
- Tag object: `8ec11a4b7e39a5fd00da2fc5cb9b543e31fd7926`
  (`gh api repos/caddyserver/caddy/git/ref/tags/v2.11.4`)
- Review date: 2026-10-01
- Verdict: **acceptable for the planned use with the three controls below**
- Findings: **high 0, medium 1, low 2**
- Difficulty: **medium**

## Scope and method

The planned use is one loopback-only reverse proxy, started by a systemd user
unit from the mise-installed binary, pinned to 2.11.4 in `mise.toml` and
`mise.lock` and installed with `mise install --locked`. It runs the
repository-owned `infra/reference-library/reference-library.caddyfile`: global
options `admin off`, `persist_config off` and `auto_https off`, and one site
`http://127.0.0.1:23191` that binds `127.0.0.1` and reverse-proxies to
`127.0.0.1:23119` with `header_up Host {upstream_hostport}`. It exists only
because Zotero's web server refuses any Host header whose port is not its own,
and `systemd-socket-proxyd` cannot change headers. Its traffic is the user's
own reference-library requests; no student data goes into it.

This review used the release metadata, the release's checksum and signature
files, the binary's own build information, a configuration check and a live
run of the planned configuration, and the OSV database. It did not read
Caddy's source: the review rests on what the planned configuration loads
and on the release's integrity evidence, and says so where it matters.

## Verdict

With the planned configuration the binary opens one loopback TCP listener,
forwards HTTP to one loopback upstream, and has no admin endpoint, no
certificate or ACME activity and no outbound connection other than the
upstream. The release's artifact digest matches the lock and a Sigstore
signature on the checksum list verifies. The Go standard library and
dependencies carry published advisories (F-02), but the planned configuration
reaches only HTTP serving, URL parsing and header reading, and only local
processes can talk to the listener.

## Findings

### F-01 — Medium — Release assets have checksum and signature evidence that mise does not verify

The release workflow `release.yml` at tag `v2.11.4` signs each asset with
Sigstore keyless signing (`.sig` and `.pem` files next to every asset) and
publishes a software bill of materials. The lock entry that mise wrote for the
tool records only a SHA-256 and the download URL: unlike the `uv` entry it has
no `provenance` field, so mise does not check the signature at install. The
checksum list's signature was verified by hand for this review, but a chain to
Sigstore's root and a transparency-log lookup were not (no `cosign`, and the
installed GitHub CLI has no `attestation` command).

Evidence:

```text
$ sha256sum caddy_2.11.4_linux_amd64.tar.gz
527fbf917c39189a1e3b31d34fa955601680b2d5c8055d2a87b8b9588dec7bb9
$ grep linux_amd64.tar.gz caddy_2.11.4_checksums.txt
527fbf917c39189a1e3b31d34fa955601680b2d5c8055d2a87b8b9588dec7bb9  caddy_2.11.4_linux_amd64.tar.gz
$ grep -A1 'linux-x64"\]' mise.lock   # the Caddy block
checksum = "sha256:527fbf917c39189a1e3b31d34fa955601680b2d5c8055d2a87b8b9588dec7bb9"
$ base64 -d caddy_2.11.4_checksums.txt.pem | openssl x509 -noout -ext subjectAltName
URI:https://github.com/caddyserver/caddy/.github/workflows/release.yml@refs/tags/v2.11.4
$ openssl dgst -sha256 -verify pub.pem -signature sig.bin caddy_2.11.4_checksums.txt
Verified OK
```

The certificate's issuer is `sigstore-intermediate`, valid 2026-06-03
04:37:11 to 04:47:11 GMT, which covers the release time. The GitHub release
API shows `github-actions[bot]` as uploader of every asset.

Control: keep the SHA-256 values in `mise.lock`, install only with `--locked`,
and treat a checksum change at the same version as a new review.

### F-02 — Low — Published advisories on Caddy's Go toolchain and dependencies

The binary was built with Go 1.26.3 and links 144 modules (`caddy build-info`).
OSV queried on 2026-10-01 reports no advisory for `caddy/v2` 2.11.4 itself and
advisories for 15 of the other entries. For the planned configuration:

- Reachable in principle, availability only: `GO-2026-6089` (net/http, the
  unencrypted HTTP/2 check on a plain listener lacks `ReadHeaderTimeout`),
  `GO-2026-6218` (net/url, quadratic `resolvePath`), `GO-2026-5039`
  (net/textproto, unescaped input in error text) and `GO-2026-5026` (net/http
  client, Punycode labels; the upstream is the literal `127.0.0.1`). A local
  process could stall the proxy; the proxy would be restarted by the next
  request after the 10-minute idle exit, and a stall affects only the user's
  own reference-library session.
- Not loaded by this configuration: `golang.org/x/crypto` (`ssh`, `openpgp`),
  `google.golang.org/grpc` and OpenTelemetry (tracing and metrics exporters,
  off unless configured), `go-chi/chi` `RealIP`, CEL expressions,
  `klauspost/compress` `s2.NewDict`, `x/text` normalization, TLS handshakes
  (`GO-2026-5037`, `-5856`, `-6090`; `auto_https off` and a plain `http://`
  site), `encoding/asn1`, `encoding/xml`, `html/template`, `os.Root`.

This table of reachability is from advisory text and the configuration, not
from a call-graph tool; no `govulncheck` was run.

Control: re-run the OSV query when the pin moves and treat a newer Caddy that
fixes `GO-2026-6089` as a reason to update.

### F-03 — Low — The server writes small state files outside the repository

Caddy creates a data directory (`caddy/instance.uuid`, `last_clean.json` and
an empty `locks/` folder) and, unless `persist_config off`, an
`autosave.json` in the configuration directory. Two runs under scratch
`XDG_DATA_HOME` and `XDG_CONFIG_HOME` showed it: the first, without
`persist_config off`, also wrote `autosave.json`; the second, with the planned
Caddyfile, wrote only the data-directory files. The planned unit points
`XDG_DATA_HOME` at a systemd runtime directory that is removed when the
service stops, and `admin off` closes the API that could change the
configuration at run time.

Control: keep `admin off`, `persist_config off` and the runtime directory in
the unit; do not add `import`, `{file.*}` or `{env.*}` to the Caddyfile
without a new review.

## What the process can change or reach

- Listens on `127.0.0.1:23191` only (`bind 127.0.0.1`), shown by `ss -ltnp`
  during the run. The socket unit on `127.0.0.1:23190` is the only other way
  in, through `systemd-socket-proxyd`.
- Sends requests only to `127.0.0.1:23119`. With `admin off` it opens no
  administration port (the default `localhost:2019` is not in the `ss` list).
- Reads its configuration once at start. The Caddyfile has no `exec`, `file`,
  or `import` directive. `caddy list-modules` shows 132 standard modules and
  no third-party module.
- Writes only the runtime-directory files above. It does not touch the
  Zotero profile or library; Zotero's API is the only thing it talks to.

## Telemetry, updates and install effects

The planned configuration has no telemetry or update setting. `caddy help`
lists an experimental `upgrade` command that replaces the binary only when
someone runs it, and the unit never does. No telemetry source was read; this
review found none in the configuration or the unit. The archive is a tarball of `caddy`, `LICENSE`
and `README.md`; mise unpacks it into
`~/.local/share/mise/installs/aqua-caddyserver-caddy/2.11.4/` and runs no
install script.

## License

Apache License 2.0 (the archive's `LICENSE`). The repository does not copy the
binary: mise downloads it at install, so no redistribution notice is needed.
If the binary is later redistributed, preserve the license and the notices of
its dependencies.

## Required controls

1. Pin 2.11.4 and every platform SHA-256 in `mise.lock`, install with
   `--locked`, and review any same-version checksum change.
2. Keep the Caddyfile as it is: loopback bind, `admin off`,
   `persist_config off`, `auto_https off`, one site, one upstream. Re-review
   before adding a directive that reads files or the environment, or opens
   another listener.
3. Run it only as a user unit that is stopped when unneeded (`StopWhenUnneeded`)
   with its state in the runtime directory.

## Verification record

Completed checks: tag and release metadata; the Linux release asset's SHA-256
against the checksum list and the lock; the checksum list's Sigstore signature
and certificate identity with `openssl`; `caddy version`, `build-info` and
`list-modules`; `caddy validate` and `caddy fmt --diff` on the planned
Caddyfile; a live run of it against the running Zotero with the Host header
check; listener inspection with `ss`; the files Caddy wrote; OSV queries for
the 144 modules, Go 1.26.3 and Caddy 2.11.4.

Intentionally not run: `cosign`, `govulncheck`, a source review of Caddy,
`npm run workflow` and `npm run verify`.
