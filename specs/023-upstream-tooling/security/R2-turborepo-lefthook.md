# Security review: Turborepo 2.11.5 and lefthook 2.1.15

Reviewed 2026-09-30 for CHE-44. The supplied source clones resolve exactly to:

- Turborepo tag `v2.11.5`, commit
  `8492b42667210270f4169f0df8c0edf725ff2f41`.
- lefthook tag `v2.1.15`, commit
  `d050364655420db8a4241f2480942a8d8ddb3486`.

Assumption: Linux x64 is the deployment platform used for the artifact
comparison. The source review covers the selectors for every npm-supported
platform, but another deployed platform needs the same artifact comparison.

This was a read-only review. I did not run either tool, its tests, its build,
or its install scripts. I downloaded npm tarballs, registry metadata, advisory
responses, checksums, and one Turborepo release archive under
`work-R2-turborepo-lefthook/`. `go version -m` inspected the lefthook binary's
embedded build information without executing it. I did not inspect the
repository lockfile because the task prohibited touching the repository; the
reported registry SRI values are the values that its exact lock entries should
contain.

## Executive summary

| Tool | High | Medium | Low | Verdict for the planned use |
|---|---:|---:|---:|---|
| Turborepo 2.11.5 | 0 | 3 | 3 | Usable after telemetry and agent guidance are disabled, ambient remote-cache credentials are isolated, and raw run summaries are handled as sensitive evidence. |
| lefthook 2.1.15 | 0 | 1 | 4 | Usable if hook installation is explicit and serialized across linked worktrees, auto-install is disabled, and the generated hook is pinned to the repository's npm wrapper. |

No high finding stands. Four medium findings stand across the two tools.

## Turborepo 2.11.5

### Verdict and required controls

Three medium findings stand for the planned use:

- **T-M1:** telemetry is enabled by default and sends events to Vercel;
- **T-M2:** a detected coding agent causes a default write to root
  `AGENTS.md`; and
- **T-M3:** `--summarize` writes commands, paths, source-control data, and
  environment-name/hash pairs.

Use these controls:

1. Set `TURBO_TELEMETRY_DISABLED=1` for every invocation.
2. Add `"agentGuidance": false` and `"noUpdateNotifier": true` to the root
   `turbo.json`; also set `NO_UPDATE_NOTIFIER=1` in verification jobs.
3. Unset `TURBO_BINARY_PATH`, `TURBO_TOKEN`, `TURBO_TEAM`, `TURBO_TEAMID`,
   `VERCEL_ARTIFACTS_TOKEN`, and `VERCEL_ARTIFACTS_OWNER` in the verification
   environment. Point `TURBO_CONFIG_DIR_PATH` and `VERCEL_CONFIG_DIR_PATH` to
   an empty, job-scoped directory so old home-folder auth cannot link the run.
4. Assert that the locked platform package exists before invoking Turbo. Do
   not allow the wrapper's repair-time `npm install` in the verification job.
5. Treat `.turbo/runs/*.json` as sensitive. Keep raw files access-controlled
   and out of public artifacts or commits; publish only approved fields if the
   evidence must leave the job.

The requested eight review areas follow.

### 1. Install and post-install scripts

The source `turbo` package declares only `postversion` and `prepack`; neither
is an install lifecycle hook. It selects exact-version platform packages as
optional dependencies (`packages/turbo/package.json:9-29`). The published
`turbo@2.11.5` manifest contains only `postversion`, and published
`@turbo/linux-64@2.11.5` has no scripts. Therefore
`npm ci --ignore-scripts` executes no Turbo lifecycle code.

The release workflow builds Rust binaries, moves them into the release tool's
input tree, enables npm trusted-publishing provenance, and publishes through
the release tool (`.github/workflows/turborepo-release.yml:566-635`). Those are
publisher build steps, not consumer install steps.

Registry evidence, captured on 2026-09-30:

```text
$ jq '{name,version,scripts,optionalDependencies}' npm-metadata/turbo-2.11.5.json
name=turbo version=2.11.5 scripts={postversion:"node bump-version.js"}
optional dependency @turbo/linux-64=2.11.5

$ jq '{name,version,scripts,os,cpu}' npm-metadata/turbo-linux-64-2.11.5.json
name=@turbo/linux-64 version=2.11.5 scripts=null os=[android,linux] cpu=[x64]
```

### 2. Binaries, models, and data downloaded

Normal installation downloads `turbo@2.11.5` and the exact optional platform
package from the npm registry. The JavaScript wrapper resolves
`@turbo/<platform>-<arch>/bin/turbo`, with a legacy package-name fallback
(`packages/turbo/bin/turbo:73-99` and `packages/turbo/bin/turbo:116-153`). No
models or other runtime data are downloaded in the planned path.

**T-L1 — Runtime repair can invoke npm despite `--ignore-scripts` (low).** If
the platform package is absent when Turbo runs, the wrapper executes
`npm install --prefer-offline` inside the installed `turbo` package and then
resolves the binary again (`packages/turbo/bin/turbo:19-32` and
`packages/turbo/bin/turbo:155-194`). This is low for the planned use because a
successful locked `npm ci` should provide the exact platform package. It still
creates an unexpected network and write path after installation. Assert the
platform binary is present and deny package-registry egress during the check.

The npm tarball SHA-512 values matched the registry `dist.integrity` values.
The downloaded Linux x64 npm binary also matched the GitHub release archive
byte for byte:

```text
turbo-2.11.5.tgz sha512
  a8b5e17aacf74d4bc9a47215e8c501c24364bf02b13151bf42c8a6ca2293f437
  cd58f1c9dbde06fe2e670da1fe7db1c9b77507ee8aee6cd37102a6246d434601
@turbo/linux-64-2.11.5.tgz sha512
  51bd9dfe701b7562da4b2b5c11a3e9d709bf62e22f1c422a36b091308fd480e1
  b215d3a18319bc57258f0098a5416458c5856ba84528cb62b94b92bc486e74ac

npm Linux binary sha256
  479733d3000c9393afb0c421d003cd26417bdb9e0ff525cf1445a7e1f29bb8bc
GitHub archive binary sha256
  479733d3000c9393afb0c421d003cd26417bdb9e0ff525cf1445a7e1f29bb8bc
cmp exit=0
```

The GitHub archive itself had SHA-256
`073462a95b865ffc4be3caedb3dce1a8d98de00f79436550b681fdfc1f35466c`,
matching `turbo-2.11.5-x86_64-unknown-linux-musl.tar.gz` in the published
`SHA256SUMS` file.

### 3. Network calls and telemetry

**T-M1 — Telemetry is enabled and persistent by default (medium).** On first
use, Turbo creates a telemetry identifier and private salt, enables telemetry,
and writes them to the platform config directory under
`turborepo/telemetry.json` (`crates/turborepo-telemetry/src/config.rs:22-54`,
`crates/turborepo-telemetry/src/config.rs:63-110`, and
`crates/turborepo-telemetry/src/config.rs:239-262`). It POSTs JSON events to
`https://telemetry.vercel.com/api/turborepo/v1/events` with persistent and
session identifiers (`crates/turborepo-cli/src/cli/mod.rs:115-130` and
`crates/turborepo-api-client/src/telemetry.rs:8-40,64-90`). Events include
platform, CPU count, Turbo version, which flags are set, CI vendor, detected AI
agent, link state, and remote-cache URL. Values marked sensitive are salted
before transmission (`crates/turborepo-telemetry/src/events/generic.rs:46-65`
and `crates/turborepo-telemetry/src/events/generic.rs:123-246`); the repository
identifier is also salted (`crates/turborepo-telemetry/src/events/repo.rs:61-76`).

This is medium because verification runs that are intended to be local still
make external requests and expose stable operational metadata. Set
`TURBO_TELEMETRY_DISABLED=1` or `DO_NOT_TRACK=1`. The environment check happens
before the config is loaded, so this also prevents creation of
`telemetry.json` (`crates/turborepo-telemetry/src/lib.rs:138-179` and
`crates/turborepo-telemetry/src/config.rs:265-269`).

**T-L2 — Interactive update checks use the network and a global cache (low).**
When stdout is a terminal and `CI`/`NO_UPDATE_NOTIFIER` is absent, Turbo checks
`https://turborepo.dev/api/binaries/version` with an 800 ms timeout and a
24-hour interval (`crates/turborepo-updater/src/lib.rs:20-27`,
`crates/turborepo-updater/src/lib.rs:58-103`, and
`crates/turborepo-updater/src/lib.rs:179-203`). The shim invokes that path for
normal local runs (`crates/turborepo-shim/src/run.rs:594-623`). Its exact pinned
`update-informer` dependency is commit
`7a78e90e62479e022bae77ada824c9df53036f96` (`Cargo.lock:9286-9296`), which
creates and updates a platform cache file. See the exact dependency source at
<https://github.com/nicholaslyang/update-informer/blob/7a78e90e62479e022bae77ada824c9df53036f96/src/version_file.rs#L15-L57>.
This is low because CI and non-terminal runs skip it. Set
`"noUpdateNotifier": true` for a deterministic default.

**T-L3 — Ambient config can link an otherwise local run (low).** Turbo merges
environment, repository, global auth, global config, and `turbo.json` values;
global auth and config are consulted before shared configuration
(`crates/turborepo-config/src/lib.rs:809-858`). `TURBO_TOKEN`, `TURBO_TEAM`,
and `TURBO_TEAMID` populate link credentials
(`crates/turborepo-config/src/env.rs:16-23` and
`crates/turborepo-config/src/override_env.rs:10-18,85-115`). A linked auth
object initializes the HTTP client even when remote cache use is otherwise
unneeded, and linked runs start analytics
(`crates/turborepo-run/src/builder.rs:506-513` and
`crates/turborepo-run/src/builder.rs:2035-2067`). This is low because no such
credential is part of the plan, but "no login" does not rule out old home
state. Isolate both config directories and unset the listed variables.

All task definitions have `cache: false`, so no task artifact should be read
from or written to either local or remote cache. That does not disable the
independent telemetry, update, linked-client, or agent-guidance paths above.

### 4. Code execution and shell-out paths

The npm wrapper spawns the selected native binary with the user's arguments
and inherited environment (`packages/turbo/bin/turbo:413-435`).
`TURBO_BINARY_PATH` overrides selection with any existing executable
(`packages/turbo/bin/turbo:101-113`), so the planned environment should unset
it.

`turbo run check` and `turbo run test` intentionally execute repository task
commands. The executor resolves package-manager/toolchain commands or the
configured experimental command override, sets its working directory and
environment, and passes it to the operating-system process API
(`crates/turborepo-task-executor/src/command.rs:151-175,244-323` and
`crates/turborepo-process/src/command.rs:128-159`). The future
`experimentalTaskCommand` flag makes configured argv authoritative
(`crates/turborepo-engine/src/builder/definitions.rs:394-442,996-1036`). This
is an expected trust boundary, not a separate finding: `turbo.json`, workspace
manifests, package scripts, lockfiles, and invoked toolchains are executable
inputs and must be reviewed with the change.

Run-summary source-control capture also invokes `git` to obtain branch and SHA
when CI variables are unavailable (`crates/turborepo-run-summary/src/scm.rs:21-56`).
`turbo run` no longer starts the Turbo daemon
(`crates/turborepo-run/src/builder.rs:1009-1012`).

### 5. File writes outside the task working folders

**T-M2 — Agent guidance mutates repository instructions by default (medium).**
For repository-scoped commands, Turbo detects a coding agent, loads root
configuration, and calls agent-guidance maintenance before the command runs
(`crates/turborepo-cli/src/cli/mod.rs:184-224,433-443`). The setting defaults
to enabled (`crates/turborepo-config/src/lib.rs:706-712`). The implementation
locks at root, reads or creates root `AGENTS.md`, appends or replaces a managed
block, writes a root temporary file, and renames it over `AGENTS.md`
(`crates/turborepo-cli/src/cli/agent_guidance.rs:36-55,88-150,153-215`). This
is medium in Orca because agent detection is expected and an evidence command
can silently alter a tracked policy file before checks. Add
`"agentGuidance": false`; the exact opt-out is tested at
`crates/turborepo-config/src/turbo_json.rs:348-377`.

**T-M3 — Raw run summaries contain sensitive operational metadata (medium).**
With `--summarize`, Turbo writes
`.turbo/runs/<run-id>.json` (`crates/turborepo-run-summary/src/tracker.rs:418-431,808-813`).
Each task entry contains input paths and hashes, raw task command, pass-through
CLI arguments, output paths, working directory, dependency graph, framework,
and environment names (`crates/turborepo-run-summary/src/task.rs:93-121,148-156`
and `crates/turborepo-run-summary/src/task_factory.rs:103-109,130-203`). The
summary also contains the synthesized invocation, repository-relative path,
timing, exit code, CI user, branch, and commit SHA
(`crates/turborepo-run-summary/src/tracker.rs:65-90,130-205`,
`crates/turborepo-run-summary/src/execution.rs:25-70`, and
`crates/turborepo-run-summary/src/scm.rs:13-56`).

Environment values are not written in clear text by this path, but selected
values become unsalted SHA-256 hashes of the value and are paired with their
names (`crates/turborepo-env/src/lib.rs:129-151`,
`crates/turborepo-task-hash/src/lib.rs:1041-1053`, and
`crates/turborepo-run-summary/src/task.rs:250-279`). Low-entropy values can be
guessed offline, while command lines and pass-through arguments can contain
clear-text secrets if callers put them there. This is medium because the plan
would retain these files as evidence. Do not pass secrets on command lines;
keep raw summaries private or derive a minimal evidence record containing only
the run ID, tool version, task names, exit status, times, and approved hashes.

Other writes reachable from the plan are the task processes' own outputs and
the working-tree `.turbo/runs` files. The telemetry config, update cache,
`AGENTS.md`, and repair-time `node_modules` writes are covered above.

### 6. Credential handling

Turbo accepts tokens from `TURBO_TOKEN` or `VERCEL_ARTIFACTS_TOKEN`, team data
from their companion variables, repository `.turbo/config.json`, global Turbo
auth/config, and legacy Vercel auth (`crates/turborepo-config/src/lib.rs:809-858`,
`crates/turborepo-config/src/file.rs:113-171`, and
`crates/turborepo-config/src/override_env.rs:10-18`). I found no keychain use in
the planned path. The token type redacts `Debug`, `Display`, and serialization
and zeroizes its owned source string (`crates/turborepo-types/src/secret.rs:6-31,46-55`).

The planned use needs no credential. The controls under T-L3 prevent accidental
inheritance and make the no-remote-cache claim enforceable.

### 7. Published security advisories for 2.11.5

No advisory was returned for exact `turbo@2.11.5` or
`@turbo/linux-64@2.11.5` by OSV, and npm's bulk advisory endpoint returned an
empty object on 2026-09-30:

```text
$ jq '[.results[] | ((.vulns // []) | length)]' advisories/osv-querybatch.json
[0,0,0,0,0]
# Request order: turbo, @turbo/linux-64, lefthook, lefthook-linux-x64,
# github.com/evilmartians/lefthook/v2.

$ jq 'keys' advisories/npm-advisories.json
[]
```

The repository has three published GitHub advisories. Two affect the `turbo`
package but are fixed in 2.9.14, so 2.11.5 is outside their vulnerable ranges:

- [GHSA-3qcw-2rhx-2726](https://github.com/vercel/turborepo/security/advisories/GHSA-3qcw-2rhx-2726),
  unexpected local execution during Yarn Berry detection, affects `turbo`
  from 1.1.0 and is fixed in 2.9.14.
- [GHSA-hcf7-66rw-9f5r](https://github.com/vercel/turborepo/security/advisories/GHSA-hcf7-66rw-9f5r),
  login callback CSRF/session fixation, is fixed in 2.9.14; login is also
  outside the plan.
- [GHSA-5xc8-49mv-x4mm](https://github.com/vercel/turborepo/security/advisories/GHSA-5xc8-49mv-x4mm)
  concerns the Turborepo VS Code extension, not the npm `turbo` CLI package.

This is a point-in-time search, not proof that no undisclosed issue exists.

### 8. Release signing, provenance, and published checksums

Both `turbo@2.11.5` and `@turbo/linux-64@2.11.5` registry records contain npm
registry signatures, Subresource Integrity (SRI) SHA-512 values, npm publish
attestations, and SLSA provenance attestations. The provenance names
`.github/workflows/turborepo-release.yml`, GitHub-hosted runner invocation
`36361927571`, and source commit
`a50ee6536eac2f7f3168cc38087ee7d8397fc0e9`. That is the parent of the signed
release commit because the workflow publishes npm first and creates the tag
afterward (`.github/workflows/turborepo-release.yml:1-14,566-635`).

The downloaded wrapper was byte-identical to tagged
`packages/turbo/bin/turbo` (SHA-256
`dd000efaa64f567f0986a84d363bbe7cf95a831010f6f6dbfd21770c89a8523d`,
`cmp` exit 0). The platform binary comparison is recorded in area 2.

The tag points at a commit with an embedded GitHub OpenPGP signature. Local
signature validation was **unverified** because the review keyring lacks the
public key:

```text
$ git verify-commit v2.11.5
gpg: using RSA key B5690EEEBB952194
gpg: Can't check signature: No public key
exit=1
```

Likewise, I decoded and inspected the npm attestation claims but did not
cryptographically validate their Sigstore bundles because no verifier was
installed and this review prohibited installing tools. SRI was independently
recomputed, and the npm binary was independently tied to the tagged release
through the matching GitHub archive.

## lefthook 2.1.15

### Verdict and required controls

One medium finding stands: linked worktrees share the hooks and info paths,
while normal hook execution can automatically rewrite that shared state.

Use these controls:

1. Keep `npm ci --ignore-scripts`; then install deliberately with the local
   wrapper, for example `./node_modules/.bin/lefthook install`, not an `npx`
   command that may fetch a missing package. npm documents that missing
   requested packages are installed into its cache before execution:
   <https://docs.npmjs.com/cli/v11/commands/npm-exec#description>.
2. Before install, assert that the exact platform binary exists. On Linux x64
   that is `node_modules/lefthook-linux-x64/bin/lefthook`.
3. In `lefthook.yml`, set:

   ```yaml
   lefthook: node_modules/lefthook/bin/index.js
   no_auto_install: true
   assert_lefthook_installed: true
   ```

4. Install once from the designated owner worktree and serialize installation
   with any other worktree operation. Run `check-install` after installation.
5. Do not use `install --force` or `install --reset-hooks-path`. Inspect both
   local and global `core.hooksPath` first and resolve any conflict explicitly.
6. Unset `LEFTHOOK_BIN`, `LEFTHOOK_CONFIG`, and `LEFTHOOK_VERBOSE`; ensure no
   `lefthook-local.{yml,yaml,json,jsonc,toml}` exists; keep `remotes` absent.

### 1. Install and post-install scripts

The main npm package has a `postinstall` script. It selects the platform binary
and runs `lefthook install` in `INIT_CWD` or the current directory. It skips CI
only when `CI` is truthy and `LEFTHOOK` is not explicitly enabled
(`packaging/registries/npm/lefthook/package.json:30-44` and
`packaging/registries/npm/lefthook/postinstall.js:1-22`). The platform package
has no lifecycle script
(`packaging/registries/npm/lefthook-linux-x64/package.json:1-22`).

The planned `npm ci --ignore-scripts` prevents this repository mutation. Keep
that flag; otherwise a dependency install can write Git hooks before the
caller reviews `core.hooksPath` and worktree ownership.

Publisher build steps run `go generate`, then GoReleaser builds a
`no_self_update` binary for npm (`.goreleaser.yml:1-35`). The packaging script
copies those binaries into platform packages and calls `npm publish`
(`packaging/scripts/lib/Constants.rakumod:10-24` and
`packaging/scripts/lib/Registries/NPM.rakumod:51-76,106-125`). These do not run
on consumer installation.

Published metadata captured on 2026-09-30 agrees:

```text
lefthook@2.1.15 scripts={postinstall:"node postinstall.js"}
lefthook-linux-x64@2.1.15 scripts=null os=[linux] cpu=[x64]
```

### 2. Binaries, models, and data downloaded

The main package pins each optional platform package to 2.1.15
(`packaging/registries/npm/lefthook/package.json:30-40`). `get-exe.js` maps
Node's OS and architecture to `lefthook-<os>-<arch>/bin/lefthook` and uses
`require.resolve` (`packaging/registries/npm/lefthook/get-exe.js:1-20`). It has
no Turbo-like runtime download or repair path. No models or data are
downloaded.

The downloaded npm tarball SHA-512 values matched their registry SRI values:

```text
lefthook-2.1.15.tgz sha512
  97f05294e641a2edf32c3b92215f15fa46cdc82e948850800951eef1d554083c4
  7e7ef2a657989afc8913abb88ffb86fe96edcdec565553fbaf81a5584665198
lefthook-linux-x64-2.1.15.tgz sha512
  a328599fa9283665ef4a54905de4cbd599b19a5a75cac2278d90844f07c08631
  9be6be361d7d9ca1a3f33b47ba76fa0fe9ba843bc7325a8aaa8fe158573f678a
```

### 3. Network calls and telemetry

No telemetry path was found in the planned npm binary. A source search for
`telemetry|analytics|sentry|segment|datadog|opentelemetry` found only the
unrelated documentation build setting `docmd.config.js:58`.

Remote configuration is network-capable only when `remotes` is configured.
Install and automatic sync enumerate configured remotes
(`internal/command/install.go:44-68,159-265`); the implementation shells out to
Git clone, fetch, pull, and checkout and stores clones under Git's info folder
(`internal/git/remote.go:8-84`). The plan has no remotes, so this path is not
reached. There is no separate remote-disable flag; absence of `remotes` is the
control.

The full release binary has a `self-update` command that queries GitHub, then
downloads a binary and same-release checksum file and compares SHA-256
(`internal/updater/updater.go:28-38,86-120,206-314`). The npm binary is built
with `no_self_update`; that build excludes the command
(`cmd/commands_without_self_update.go:1-17`). Embedded build information from
the exact npm Linux binary confirms `-tags=no_self_update`, version 2.1.15,
source revision `d050364655420db8a4241f2480942a8d8ddb3486`, and
`vcs.modified=false`. Therefore self-update is not reachable in the planned
package.

### 4. Code execution and shell-out paths

The npm wrapper spawns the resolved native binary with all CLI arguments
(`packaging/registries/npm/lefthook/bin/index.js:1-16`). `install` uses system
Git commands to resolve repository paths and configuration, and to manage any
configured remotes (`internal/git/paths.go:8-36`,
`internal/command/install.go:503-550`, and `internal/git/remote.go:24-84`).

**L-L1 — The generated hook can select an unpinned executable or package
runner (low).** Unless `lefthook` is configured explicitly, the hook tries
`LEFTHOOK_BIN`, then `lefthook` on `PATH`, then repository npm binaries. If
those fail, it tries Go, Bundler, Yarn, pnpm, Swift, Mint, uv, mise, and devbox
(`internal/templates/hook.tmpl:16-110`). Several fallbacks can fetch or build
code according to their own configuration. This is low because the pinned npm
binary should exist, but PATH is checked before it. Pin
`lefthook: node_modules/lefthook/bin/index.js`, unset `LEFTHOOK_BIN`, assert the
platform package exists, and install through `./node_modules/.bin/lefthook`.
The upstream documentation identifies the `lefthook` field as the way to force
a dependency version (`docs/configuration/lefthook.md:13-30`).

The planned `commit-msg` command is executable repository configuration.
lefthook joins configured command text and arguments, performs substitutions,
and runs the result through `sh -c` on Unix
(`internal/run/controller/command/build_command.go:14-49` and
`internal/run/controller/exec/exec_unix.go:79-128`). This is expected for a
hook runner. Review `lefthook.yml` changes as code and keep the commitlint
command fixed to the message-file input.

### 5. File writes outside the working folder

**L-M1 — Linked worktrees share mutable hook state (medium).** lefthook asks
Git for absolute `hooks`, `info`, and Git-directory paths
(`internal/git/paths.go:8-36`). In a linked worktree, Git resolves hooks and
info to the common repository while keeping a worktree-specific Git directory.
A synthetic fixture using the exact Git command returned:

```text
main hooks:   synthetic-worktree/repo/.git/hooks
main info:    synthetic-worktree/repo/.git/info
linked hooks: synthetic-worktree/repo/.git/hooks
linked info:  synthetic-worktree/repo/.git/info
linked git:   synthetic-worktree/repo/.git/worktrees/linked
```

Install creates the common hooks directory, replaces hook files, preserves a
non-lefthook hook as `<hook>.old`, and writes a checksum/timestamp file under
the common info directory (`internal/command/install.go:289-365,399-500` and
`internal/command/lefthook.go:121-165`). Normal hook execution automatically
synchronizes and rewrites hooks when configuration changes unless the CLI or
config disables it (`internal/command/run.go:99-110` and
`internal/config/config.go:47-57`). This is medium because one worktree can
change executable hook state for all linked worktrees, and concurrent branches
can race on that shared state. Set `no_auto_install: true`; designate and
serialize explicit installation; then use `check-install` as the read-mostly
environment check (`internal/command/check_install.go:15-46`).

The default install checks local and global `core.hooksPath` and stops on a
conflict. `--force` bypasses that protection, while `--reset-hooks-path`
unsets local and global values (`internal/command/install.go:503-550,591-614`).
Neither flag belongs in the plan.

If no config exists, `install` creates a default `lefthook.yml` in the worktree
root (`internal/command/install.go:104-156`). The planned config already exists.
Remote clones, when configured, go under `.git/info/lefthook-remotes`; none are
planned. `check-install` itself reads config and checksum, although repository
initialization can create the Git info directory if it is absent
(`internal/git/repo.go:88-103`). No lefthook home-folder cache or global state
write was found in the planned path.

### 6. Credential handling

**L-L2 — Hook commands inherit all ambient credentials (low).** Configured
hook commands run with `os.Environ()` plus hook-specific values
(`internal/run/controller/exec/exec_unix.go:79-84`). `LEFTHOOK_VERBOSE=1`
enables shell tracing in the generated hook, and `LEFTHOOK_BIN` overrides the
executable (`internal/templates/hook.tmpl:1-5,16-25`). This is low because the
planned commitlint command should not consume credentials, but every ambient
token remains available to it and its dependencies. Keep a minimal hook
environment, do not put secrets in command arguments, and leave verbose mode
off.

lefthook has no token store or keychain integration in this path. Git remote
configuration, if enabled, delegates authentication to system Git and inherits
the process environment except for `GIT_DIR` and `GIT_INDEX_FILE`
(`internal/git/remote.go:24-84` and `internal/system/command.go:36-73`). No
remote is planned.

**L-L3 — Optional local configuration can change commands and executable
selection (low).** The loader always looks for local config after the main,
extended, and remote configuration, and `LEFTHOOK_CONFIG` can replace the main
config (`internal/config/loader.go:104-151,154-200`). The `lefthook` executable
field is intentionally allowed from local config
(`docs/configuration/lefthook.md:13-17`). This is low because the plan excludes
such files, but the exclusion is only operational. Unset `LEFTHOOK_CONFIG` and
assert that no supported `lefthook-local` file exists before install and
`check-install`.

### 7. Published security advisories for 2.1.15

OSV returned no advisory for exact npm `lefthook@2.1.15`, exact
`lefthook-linux-x64@2.1.15`, or Go module
`github.com/evilmartians/lefthook/v2@v2.1.15`. npm's bulk endpoint likewise
returned none; the command output is shown in Turborepo area 7. The
[repository advisory page](https://github.com/evilmartians/lefthook/security/advisories)
reported no published GitHub Security Advisory on 2026-09-30. This is a
point-in-time search, not proof that no undisclosed issue exists.

### 8. Release signing, provenance, and published checksums

**L-L4 — npm artifacts lack source-to-package provenance (low).** The main and
Linux platform registry records have SRI SHA-512 values and npm registry
signatures, but neither record exposes an npm attestation or SLSA provenance
URL. The release workflow grants attestation permission and attests artifacts
listed in `dist/lefthook_checksums.txt`, then a separate job packages the
`no_self_update` binaries and publishes npm with an API key
(`.github/workflows/release.yml:8-12,38-52,60-88`). The packaging publisher
uses plain `npm publish --access public`, with no provenance option
(`packaging/scripts/lib/Registries/NPM.rakumod:119-125`).

The npm Linux binary SHA-256 is
`07ab10bed9de8fd3938f4a65eeb82785aaf6d995e19009bc961aeb3f1cd7f643`.
That hash is not in the GitHub release checksum manifest because the manifest
covers the full self-update-capable Linux binary, whose SHA-256 is
`df981b477c236546435047fb8c8ee1f6f902e17faebb1b07b6bf2165832e8fe3`.
The npm binary's embedded Go build information nevertheless names exact module
version 2.1.15, exact tag commit, `no_self_update`, and an unmodified source
tree. The npm JavaScript wrapper, resolver, and postinstall files were all
byte-identical to the tag (`cmp` exit 0).

The exact tag is annotated and contains an OpenPGP signature. Local
verification was **unverified** because the review keyring lacks its public
key:

```text
$ git verify-tag v2.1.15
gpg: using EDDSA key 592F16576A2486E75CC1B5907194E002B1A9D769
gpg: Can't check signature: No public key
exit=1
```

This is low rather than medium because registry SRI can bind the locked bytes,
registry signatures are present, tagged wrapper files match, and Go build
metadata identifies the exact clean revision. Build metadata is self-reported,
not an independent signature. The remaining gap is cryptographically verified
source-to-npm provenance. Preserve the exact integrity values in the lockfile
and use `npm ci`; if policy requires verified provenance for every executable,
this package needs upstream npm provenance or a separately approved digest.

## Artifact and query evidence

All paths in this section are below `work-R2-turborepo-lefthook/`.

- Registry metadata:
  `npm-metadata/{turbo-2.11.5,turbo-linux-64-2.11.5,lefthook-2.1.15,lefthook-linux-x64-2.1.15}.json`.
- npm attestations:
  `npm-metadata/{turbo-2.11.5,turbo-linux-64-2.11.5}-attestations.json`.
- Exact tarballs: `tarballs/*.tgz`; unpacked copies: `extracted/`.
- Release evidence:
  `github/turborepo-v2.11.5-SHA256SUMS`,
  `github/turbo-2.11.5-x86_64-unknown-linux-musl.tar.gz`, and
  `github/lefthook-v2.1.15-checksums.txt`.
- Advisory responses: `advisories/osv-querybatch.json` and
  `advisories/npm-advisories.json`.
- Linked-worktree fixture: `synthetic-worktree/`.

The following checks were run without executing reviewed binaries:

```text
$ git -C ../turborepo-v2.11.5 describe --tags --exact-match HEAD
v2.11.5
$ git -C ../turborepo-v2.11.5 rev-parse HEAD
8492b42667210270f4169f0df8c0edf725ff2f41
$ git -C ../lefthook-v2.1.15 describe --tags --exact-match HEAD
v2.1.15
$ git -C ../lefthook-v2.1.15 rev-parse HEAD
d050364655420db8a4241f2480942a8d8ddb3486

$ cmp downloaded-turbo-wrapper tagged-turbo-wrapper
exit=0
$ cmp npm-turbo-linux-binary github-release-turbo-linux-binary
exit=0
$ cmp downloaded-lefthook-js-files tagged-lefthook-js-files
exit=0 for bin/index.js, get-exe.js, and postinstall.js

$ go version -m extracted/lefthook-linux-x64/package/bin/lefthook
path github.com/evilmartians/lefthook/v2
mod github.com/evilmartians/lefthook/v2 v2.1.15
build -tags=no_self_update
build vcs.revision=d050364655420db8a4241f2480942a8d8ddb3486
build vcs.modified=false
```

The registry signature fields were observed in downloaded metadata but were
not cryptographically verified. `npm audit signatures` was not run because it
requires an installed dependency tree, and installing the reviewed packages
was prohibited.
