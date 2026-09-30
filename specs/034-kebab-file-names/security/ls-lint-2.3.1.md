# ls-lint 2.3.1 security review

- Version: `v2.3.1`
- Commit: `b530dd769e259aa9fc546cc3c0098e6a0c82870e`
- Review date: 2026-09-30
- Verdict: **acceptable for the planned use with the three controls below**
- Findings: **high 0, medium 2, low 1**
- Difficulty: **difficult**

## Scope and method

This was a read-only source, release, dependency, and package review. The
planned use is mise 2026.9.16's first registry backend,
`aqua:loeffel-io/ls-lint`, pinned to 2.3.1 in `mise.toml` and `mise.lock`, then
run offline from the repository root with a repository-owned `.ls-lint.yml`.
The repository contains public-grade code and records, not private vault data.

The review read the complete small runtime, the release and npm packaging,
the release workflow, `go.mod`, `go.sum`, and the Bazel module files. Release
and npm artifacts were downloaded only below `.local/ls-lint/`. They were
inspected with `file`, `sha256sum`, `strings`, `tar`, `cmp`, and OpenSSL, and
were never executed. The working copies under `.local/ls-lint/` were removed
after the review; a path such as `.local/ls-lint/src-v2.3.1/<path>` is `<path>`
in the upstream repository at tag `v2.3.1`.

The source assumption was verified before use:

```text
$ git -C .local/ls-lint/src-v2.3.1 rev-parse HEAD
b530dd769e259aa9fc546cc3c0098e6a0c82870e
$ git -C .local/ls-lint/src-v2.3.1 tag --points-at HEAD
v2.3.1
$ git -C .local/ls-lint/src-v2.3.1 show-ref --verify refs/tags/v2.3.1
b530dd769e259aa9fc546cc3c0098e6a0c82870e refs/tags/v2.3.1
```

No `ls-lint`, mise install, npm install, Go, Bazel, repository workflow, or
repository verification command was run. Runtime effects were established
from source, not from executing the reviewed program.

## Verdict

The tool is small and has no runtime network, telemetry, update, or write
path. Its three Go module dependencies have no current OSV advisory for the
pinned versions, its regex engine is linear-time, and the release binaries
match the published checksums. The planned checksum lock is therefore a
reasonable integrity control after the initial review.

Two risks remain material. The release has no signature or artifact
attestation, so its checksum does not independently authenticate the
publisher. A filename with many dots also causes exponential work before a
rule is selected. Wildcard config paths have a lower-severity symlink escape
because the exact doublestar call follows directory symlinks.

## Findings

### F-01 — Medium — Release assets have checksum integrity but no independent provenance

The tagged workflow builds the binaries, creates `checksums.txt`, uploads both
through `gh release create`, and publishes npm from the same job. The workflow
uses mutable major action tags and has no explicit `permissions` block. Thus a
single workflow and credential boundary produces both artifact and digest.
There is no detached signature, Sigstore bundle, or software bill of
materials in the release assets. GitHub's attestation API returned HTTP 404
for every lock-relevant artifact digest, and the installed GitHub CLI cannot
perform local attestation verification.

Evidence: `.local/ls-lint/src-v2.3.1/.github/workflows/bazel.yml:87-107`
defines the tag-triggered release and npm publish job;
`.local/ls-lint/src-v2.3.1/deployments/github/github.sh:4-7` creates the
release; `.local/ls-lint/src-v2.3.1/deployments/github/BUILD.bazel:4-33`
uploads the checksum and artifacts. The release API reported uploader
`github-actions[bot]` for every asset. The lightweight tag points directly at
a commit whose GitHub SSH verification is valid, but that commit signature
does not bind the built bytes.

```text
$ gh attestation verify .local/ls-lint/release-v2.3.1/ls-lint-linux-amd64 -R loeffel-io/ls-lint
unknown command "attestation" for "gh"
$ gh api repos/loeffel-io/ls-lint/attestations/sha256:b5a0d2e4427ad039fbc574551f17679f38f142b25d15e0e538769f8cf15af397
{"message":"Not Found",..."status":"404"}
```

Mise can verify GitHub attestations, SLSA, Cosign, and Minisign when Aqua
metadata supplies the required identity material. For this package the exact
vendored Aqua record supplies only a GitHub checksum asset. Mise's own
implementation chooses provenance only from registry metadata, so
`paranoid = true` and `locked_verify_provenance = true` re-run supported
provenance but cannot add a method that this entry does not define.

Evidence: mise v2026.9.16 `registry/ls-lint.toml:1-7` selects Aqua before npm;
its vendored Aqua snapshot is commit
`59172dbefd9a52cd07326472f19b9c5997a04a3a`, and the `loeffel-io/ls-lint`
record at generated `registry.yml:64724-64738` selects the raw
`ls-lint-{{.OS}}-{{.Arch}}` asset and `checksums.txt` SHA-256. It has no
attestation, SLSA, Cosign, or Minisign field. Mise v2026.9.16
`src/backend/aqua.rs:1340-1403` shows that those methods require registry
metadata; `docs/paranoid.md:69-81` says paranoid mode does not add unsupported
verification.

Control: retain the reviewed SHA-256 values in `mise.lock`, install only with
`--locked`, and treat a checksum change at the same version as a new security
review. The feature specification already accepts this checksum-only boundary.

### F-02 — Medium — Dotted filenames cause exponential CPU and allocation work

For every walked file, the linter splits the basename at each dot, computes
`2^N`, and allocates a length-`N` slice in every iteration until it finds a
matching extension rule. This occurs before the code knows whether any rule
matches. One short tracked filename containing dozens of dots can therefore
stall a local or continuous-integration verification run. The effect is
availability only; no persistent data change was found.

Evidence: `.local/ls-lint/src-v2.3.1/internal/linter/linter.go:141-170`
derives `N`, calculates `math.Pow(2, N)`, and loops through every combination;
`:291-358` applies that function to every non-ignored file in the tree.

Control: run the ls-lint verification step with a fixed process timeout and
make timeout a failing result. Revisit the pin when upstream bounds or removes
the extension-combination search.

### F-03 — Low — Wildcard config paths can follow directory symlinks outside the work tree

The main walk itself does not follow directory symlinks. Before that walk,
however, ls-lint expands wildcard rule and ignore paths with
`doublestar.Glob` without `WithNoFollow`. Doublestar 4.8.1 follows directory
symlinks by default. Because `os.DirFS` is not a chroot, a wildcard that
reaches a repository symlink can enumerate names outside the repository. The
tool does not read file contents, write them, or send them over a network, so
the direct impact is limited to filesystem metadata and possible error/debug
output.

Evidence: `.local/ls-lint/src-v2.3.1/internal/glob/glob.go:12-32` and
`:59-79` call `doublestar.Glob` without options, while
`.local/ls-lint/deps/doublestar-4.8.1/glob.go:387-399` follows symlinks unless
`noFollow` is set. The exact Go 1.24.3 documentation says `WalkDir` does not
follow discovered symlinks (`src/io/fs/walk.go:111-116`) but `DirFS` does not
prevent symlink escape (`src/os/file.go:688-699`). The current tracked tree has
one symlink, `.agents/ponytail -> ../plugins/code`, whose target remains inside
the repository:

```text
$ git ls-files -s | awk '$1==120000 {print $4}'
.agents/ponytail
```

Control: keep rule-path and ignore keys literal; do not use `*`, `**`, or
`{...}` in `.ls-lint.yml`. If wildcard paths later become necessary, first
reject tracked symlinks or move to a version that passes `WithNoFollow`.

## Install path and artifact checks

Mise 2026.9.16's registry entry resolves `ls-lint` to
`aqua:loeffel-io/ls-lint` before `npm:@ls-lint/ls-lint`. The baked Aqua entry
uses raw release assets and the release checksum file. The expected mise lock
matrix maps Linux GNU and musl keys to the same Linux raw binary, plus macOS
arm64/x64 and Windows x64. Five unique assets were downloaded and checked:

```text
ls-lint-linux-amd64       b5a0d2e4427ad039fbc574551f17679f38f142b25d15e0e538769f8cf15af397
ls-lint-linux-arm64       2abdb71243c619f0bb29587be5c228bec84c107985f2c066139ef0ec35fd3a99
ls-lint-darwin-amd64      fc17fc642e95fd8bf7030ed661e86758bee654f6e11f1e31a5f21887f47f73ae
ls-lint-darwin-arm64      e4ed2ce2b7b61d6685769e34c6375ccecb14a3f00ee59438cf82d01d6236a3c4
ls-lint-windows-amd64.exe 94e5cfb9468e597cb513fb7a8bf26499c9315ebd505d960c74e2d4849167bd31
```

Each digest matched both the downloaded `checksums.txt` entry and the current
GitHub release API digest. `file` identified the Linux files as stripped,
statically linked ELF executables, the macOS files as Mach-O executables, and
the Windows file as a PE32+ console executable. `strings` found `v2.3.1`, Go
`1.24.3`, and the three expected module names. No asset was executed.

## Runtime behavior

`cmd/ls_lint/main.go:24-100` parses flags, reads one or more config files,
unmarshals YAML, constructs `os.DirFS(workdir)`, and runs the linter. The
runtime source imports no network package and contains no HTTP client,
telemetry, analytics, updater, or write call. Its only repository read outside
the walk is `os.ReadFile` for config at `:72-83`. Output goes to standard output
or standard error.

YAML uses `gopkg.in/yaml.v3` 3.0.1. The config accepts only `ls` and `ignore`
data in `internal/config/config.go:12-25`, then converts leaf strings to a
fixed rule table at `:98-141`. Malformed types or rules fail or can panic, but
the planned config is repository-owned and reviewed.

Custom regex rules use Go's standard `regexp.MatchString` at
`internal/rule/regex.go:74-89`. Go 1.24.3 documents this engine as guaranteed
linear in input length, so ordinary backtracking ReDoS does not apply. Pattern
compilation still occurs per filename, so extremely large trusted patterns or
trees can consume proportionate resources.

Exit behavior is source-defined. A clean result exits 0; lint failures exit 1
and write to stderr; `--warn` changes lint failures to stdout and exit 0
(`cmd/ls_lint/main.go:102-166`). Flag parse errors use Go's `ExitOnError` and
exit 2, while config, YAML, walk, and output errors call `log.Fatal` and exit 1.

## Dependencies and Bazel pins

`go.mod:1-9` pins only `github.com/bmatcuk/doublestar/v4 4.8.1`,
`golang.org/x/sync 0.14.0`, and `gopkg.in/yaml.v3 3.0.1`; all module and
manifest hashes are present in the eight-line `go.sum`. Read-only OSV queries
on 2026-09-30 returned no advisory for any of those three exact versions:

```text
github.com/bmatcuk/doublestar/v4@4.8.1 {"vulns":[]}
golang.org/x/sync@0.14.0 {"vulns":[]}
gopkg.in/yaml.v3@3.0.1 {"vulns":[]}
```

OSV lists advisories against Go stdlib 1.24.3, but the reviewed program does
not import their network, TLS, mail, SQL, template, archive, XML, ASN.1, or
process-execution paths. The `os` advisories concern file creation or the newer
`os.Root` API; this program only reads config and uses `os.DirFS`. No reachable
stdlib advisory was found for this runtime.

The release build pins Go 1.24.3 and eight direct Bazel modules in
`MODULE.bazel:1-22,31-57`. `MODULE.bazel.lock` is a 53,104-byte Bazel lockfile
with SHA-256 hashes for registry metadata and source descriptions. The three
extra GitHub CLI archives and three coreutils archives have explicit SHA-256
values at `MODULE.bazel:63-126`. The npm build lock has no third-party package
entries. These are release-build inputs; the planned prebuilt runtime does not
load them.

## Release publication and npm alternative

Any actor allowed to create a protected `v*` tag can trigger the release job.
That job receives the repository GitHub token, Google cache credential, and
`NPM_TOKEN`; public API access cannot identify the exact collaborators or
secret holders. Current public rulesets protect creation, update, and deletion
of `refs/tags/v*`, but they do not establish who had publish rights in 2025.
The Actions run for the old release is no longer available through the public
run API.

The alternative `@ls-lint/ls-lint@2.3.1` tarball has no lifecycle or install
scripts and no JavaScript dependencies. It ships all seven release binaries,
the checksum file, wrapper, README, and LICENSE. `bin/cli.js:21-55` selects a
binary only from `process.platform` and `process.arch`, and `:7-18` spawns it
with the original arguments. The wrapper collapses every nonzero child status
to exit 1, unlike the raw binary.

All five lock-relevant npm binaries were byte-identical to the GitHub release
assets; the other two are Linux ppc64le and s390x. The package SHA-512 matched
the registry integrity field, and its npm registry ECDSA signature verified
with the current registry key. The npm attestation endpoint returned 404, so
the registry signature authenticates npm metadata but does not prove a build
from this Git tag. Aqua remains the smaller runtime path because it installs
one binary and keeps the raw exit behavior.

## License

The project is MIT licensed; `LICENSE:1-21` contains the full grant and notice,
and `deployments/npm/package.json:5-7` declares MIT. The npm tarball's LICENSE
and README are byte-identical to the tag. The planned mise download does not
copy the tool into this repository, so it creates no repository redistribution
notice. Preserve the MIT license and dependency notices if the binary is later
redistributed.

## Required controls

1. Pin 2.3.1 and every platform SHA-256 in `mise.lock`, use `mise install
   --locked`, and require a new review for any same-version URL or digest
   change.
2. Put a fixed timeout around the ls-lint step and treat timeout as failure.
3. Keep `.ls-lint.yml` rule paths and ignore entries literal, without `*`,
   `**`, or `{...}`. Re-review symlink behavior before adding wildcard paths.

## Verification record

Completed checks: exact clone commit and tag; release metadata, tag, commit
signature, current tag rulesets, and asset API records; five lock-relevant
downloads and SHA-256 comparisons; file and strings inspection; attestation
CLI and API checks; mise 2026.9.16 registry and Aqua verification behavior;
complete runtime source review; exact-version OSV queries; Bazel and Go pin
review; npm metadata, tar listing, binary comparisons, integrity hash, and
registry signature verification; and license comparison.

Intentionally not run: ls-lint, mise install, npm install, Go, Bazel,
`npm run workflow`, and `npm run verify`. No runtime, hosted workflow,
performance, or private-data acceptance is claimed.
