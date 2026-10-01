# bws 2.1.0 security review

- Version: `bws-v2.1.0` (Bitwarden Secrets Manager CLI, released 2026-05-21)
- Commit: `0520690b9710af7a8b1e47aad776f002f369688f`
- Review date: 2026-10-01
- Verdict: **acceptable for the planned use with the four controls below**
- Findings: **high 0, medium 2, low 2**
- Difficulty: **medium**

## Scope and method

The planned use is mise's `aqua:bitwarden/sdk-sm` backend (the registry entry
`bitwarden-secrets-manager`), pinned to 2.1.0 in `mise.toml` and `mise.lock`.
Agents run `bws secret list <project> --output json` through
`npm run secrets:refresh` with a machine account's access token, and a
one-time import runs `bws secret create`.

The review read the whole `crates/bws` source (about 1,550 lines) at the tag
above, and the parts of the Bitwarden crates it depends on that hold state,
network headers and logging (`bitwarden-core` 3.0.0, `bitwarden-sm`,
`bitwarden-cli`, `bitwarden-auth`; each `.crate` file's SHA-256 matched
`Cargo.lock`). A path such as `crates/bws/src/main.rs:264-279` is that file in
the upstream repository at the tag. The release workflows and release
metadata were read. The pinned binary was installed with `mise install
--locked` and run once, as `bws --version`, which printed `bws 2.1.0`; nothing
else was executed and no network call was made, so runtime effects below come
from source, not from observation. No build from source was made, so the
binary is not shown to match the source.

## Verdict

bws sends the access token's identifiers and requests to Bitwarden's API and
identity servers only, and keeps one encrypted state file. It has no
telemetry, update check or other network path. The risks are about where a
secret value can appear: on a command line (`secret create` and `secret
edit`), on standard output (`secret list`, `secret get`), and in a state file
written with the process's default permissions. The four controls keep keys
off shared surfaces.

## Findings

### F-01 — Medium — Secret values travel in command-line arguments for writes

`secret create <key> <value>` and `secret edit --value` take the value as an
argument, and there is no option to read it from standard input or a file. A
command line shows in the process list for any process of the same user (and
of other users when `/proc` is not mounted with `hidepid`). Only the one-time
import and later key rotations by hand use these commands; the refresh
command reads only.

Evidence: `crates/bws/src/cli.rs:127-151` (`Create { key, value, ... }`, `Edit
{ ..., value, ... }`). The access token has the opposite design: it is read
from the environment variable `BWS_ACCESS_TOKEN` (`cli.rs:51`, whose help
does not print the value), though `-t/--access-token` still accepts it on the
command line.

Control 1: never pass the token with `-t`; keep it in the environment. Run
the import in one short session on this single-user laptop, with no other
users or untrusted processes, and prefer Bitwarden's web interface for a
rotation. Record the exposure in the task that imports.

### F-02 — Medium — The state file holds a bearer token and is created with default permissions

After a login, bws writes `~/.config/bws/state/<access token ID>` (the folder
comes from `state_dir` in bws's config, and `create_dir_all` makes it). The
file holds `{version, token, encryption_key}`, encrypted with the access
token's own key, so it is useful only to someone who also holds the access
token, and it exists to avoid login rate limits. It is written with
`std::fs::write`, so its mode comes from the process's umask (typically 644),
and the folder with `create_dir_all` (typically 755).

Evidence: `crates/bws/src/state.rs:1-32` (path and `create_dir_all`);
`crates/bws/src/main.rs:264-279` (state file use and the opt-out
`state_opt_out`); `bitwarden-core-3.0.0/src/secrets_manager/state.rs:14-81`
(content, encryption with `access_token.encryption_key`, `std::fs::write`).

Control 2: `secrets:refresh` runs `process.umask(0o077)` before it starts
bws, so the file is private.

### F-03 — Low — Output formats print values, and `--output env` does not fit key files

`secret list` and `secret get` fetch the values and print them whatever the
format. `--output env` prints `KEY="value"` lines: it wraps the value in
double quotes without escaping, and comments out a key whose name is not
`[A-Za-z_][A-Za-z0-9_]*`. Backfire's `load_credential` takes everything after
`NAME=`, so quotes would become part of the key. The refresh reads `--output
json` instead. Any other use of these commands in a terminal puts values in
the scrollback and in agent transcripts.

Evidence: `crates/bws/src/render.rs:412-438` (the `Env` branch), `:462-472`
(plain `print!`), `crates/bws/src/command/secret.rs:488-522` (`list` fetches
values with `get_by_ids`).

Control 3: agents run `secret list` and `secret get` only inside the refresh
command, whose output goes to a pipe, never to a terminal or a log.

### F-04 — Low — Release assets have a checksum but no independent provenance

The release has no signature or attestation: GitHub's attestation API
returned HTTP 404 for the Linux x86-64 asset's digest, and the mise lock
records only a checksum for each asset (no `provenance` line, unlike the
uv and Google Workspace CLI entries). The assets were uploaded by
`bre-deploy[bot]`. The tag points at a commit with a verified signature.
Bitwarden signs macOS and Windows binaries with code-signing certificates
(`.github/workflows/build-cli.yml:229,243,397,412`), which does not cover the
Linux asset used here.

Control 4: keep every platform SHA-256 in `mise.lock`, install with
`mise install --locked`, and treat a changed checksum at the same version as
a new review. The recorded digests equal the digests GitHub's release API
reports for the assets.

## What bws sends where

- Servers: `https://identity.bitwarden.com` (login with the access token) and
  `https://api.bitwarden.com` (project and secret calls) by default
  (`bitwarden-core-3.0.0/src/client/client_settings.rs:53-57`). `BWS_SERVER_URL`
  or a config profile changes them (`crates/bws/src/cli.rs:66`,
  `config.rs:152-174`); `secrets:refresh` sets neither and runs bws with an
  environment of `PATH`, `HOME` and `BWS_ACCESS_TOKEN` only.
- Headers: `Device-Type`, `Bitwarden-Client-Name`, `Bitwarden-Client-Version`
  and a `Bitwarden Rust-SDK` user agent
  (`bitwarden-core-3.0.0/src/client/builder.rs:185-228`). No telemetry,
  analytics or crash-report code was found in `crates/bws` or the three
  crates read (`bitwarden-core`, `bitwarden-sm`, `bitwarden-auth`), and the binary's strings contain no `sentry`, `telemetry` or
  `analytics`.
- Secrets are decrypted on this machine with a key derived from the access
  token (`state.rs` above), so Bitwarden's servers hold only encrypted values.

## Where it keeps state

- `~/.config/bws/config`, only if `bws config` was run (`config.rs:59-102`).
- `~/.config/bws/state/<access token ID>`, unless `state_opt_out` is set
  (F-02).
- Nothing else: `bws run` and `secret` commands write no other file.

## How a value can leak

- Command line: `secret create` and `secret edit` (F-01). `bws run` joins its
  command into one `sh -c` argument and injects values into the child's
  environment (`crates/bws/src/command/run.rs:99-137`), so a secret can
  appear in `/proc/<pid>/environ` of that child; the refresh does not use it.
- Output: `secret list` and `secret get` (F-03).
- Logs: `main.rs:201` starts `env_logger` at `info`. The `bitwarden-core` code
  logs through `tracing`, which `env_logger` does not receive. Its `debug!`
  and `info!` calls found in `bitwarden-core`, `bitwarden-sm` and
  `bitwarden-cli` log account key-management state and `get_user_api_key`
  input, not secrets-manager values, and none of those paths is reached by
  `secret list`. This was read, not run with `RUST_LOG`. The refresh sets no
  `RUST_LOG`.
- Errors: failures print through `color-eyre`; `bws` forwards its message
  to standard error and the refresh passes standard error through. The error
  paths read for `secret list` carry no value.
- Shell history: a value typed in a command is saved by the shell (F-01).

## License

`LICENSE` is the Bitwarden Software Development Kit License Agreement,
Version 1 (17 March 2023), referred to by `Cargo.toml` as `license-file`;
it is not an open source license. Section 3.1 grants a limited,
non-transferable license to use the SDK to develop, test and run a
Compatible Application (one that interoperates with current Bitwarden
servers and meets Bitwarden's acceptable use policy) for personal use by
family, for demonstration, or for an organization's internal operations with
a paid Bitwarden server license, and never to offer it to a third party.
Section 3.4 forbids copying, modifying, redistributing or making derivative
works of the SDK, except for components under open source licenses (3.5; the
release ships `THIRDPARTY.html`). The planned use is an internal tool of the
user's own Bitwarden Secrets Manager organization against Bitwarden's own
servers, so it fits (c). The repository never contains bws: mise downloads
Bitwarden's release asset on each machine, and nothing here modifies or
redistributes it. Do not vendor the binary or source into the repository,
and re-read the agreement if a future use serves anyone else.

## Required controls

1. Keep the access token in `BWS_ACCESS_TOKEN` (the environment), never in
   `-t`; keep writes (`secret create`, `edit`) to one short import on this
   machine.
2. Run bws with `umask 077` so its state file is private (done in
   `scripts/secrets-refresh.ts`).
3. Run `secret list` and `secret get` only in a pipe, as the refresh does.
4. Keep the `mise.lock` checksums and install with `--locked`.

## Verification record

Completed checks: tag commit and signature; release asset list, digests and
uploader; attestation API (404); `Cargo.lock` crate checksums against the
downloaded `.crate` files; read of `crates/bws` in full and of the state,
header and logging code in `bitwarden-core`; license read; `mise lock`
checksums against the release digests; `mise install --locked` and `bws
--version`.

Intentionally not run: any bws command that needs a token or the network, a
source build, `RUST_LOG` runs. No claim is made about Bitwarden's server side.
