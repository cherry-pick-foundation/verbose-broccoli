# Security review: SpecStory CLI v2.15.1 and betterleaks v1.9.0

Stage 1 of Linear CHE-47. Read-only review of the source before installing
either tool. Nothing was built, installed or run.

- SpecStory CLI v2.15.1: `specstoryai/getspecstory`, tag `v2.15.1`, commit
  `ec171381fc713739ce1af0dbba6e874a10df7bc5` (checked with
  `git rev-parse HEAD`). Paths below starting with `specstory-cli/` or `.`
  are relative to that tree.
- betterleaks v1.9.0: `betterleaks/betterleaks`, tag `v1.9.0`, commit
  `81aff7a638638aae3a659845d089043e1d8fe9ac`. Paths starting with
  `betterleaks/` are relative to that tree. SpecStory embeds betterleaks
  v1.8.1 (commit `5eab48332cc48565864514e3bc6de89df091a7c4`), cited as
  `betterleaks@1.8.1/`.
- Scope: the `sync` command, global startup, and the `claude` and `codex`
  providers. Third-party Go modules were not audited, except where noted.

## Verdict

**Pass, on condition that every run uses the command lines in section 7.**
Run with default flags, SpecStory fails: it sends usage analytics to PostHog
(F2), checks GitHub for updates (F3), writes into the project folder (F4), and
copies full, unredacted session text into `~/.specstory/sessions.db` (F1).
The section 7 command lines turn off every network path found and keep every
write inside the chosen output and config folders. betterleaks `dir` mode has
no default network use and passes.

Findings: 2 high, 6 medium, 6 low.

| ID | Severity | Finding |
| --- | --- | --- |
| F1 | high | Full, unredacted session text is written to `~/.specstory/sessions.db`; no flag turns it off |
| F2 | high | PostHog analytics is on by default and sends the command line, working folder and project name |
| F3 | medium | Version check contacts github.com on every start by default |
| F4 | medium | Default writes land in `<cwd>/.specstory/` unless `--output-dir` and `--config-dir` are set |
| F5 | medium | An inherited `OTEL_EXPORTER_OTLP_ENDPOINT` turns on OpenTelemetry, which then includes prompt text |
| F6 | medium | Cloud sync is on by default and uploads Markdown plus raw session JSONL once logged in |
| F7 | medium | Redaction misses file names, personal data, `sessions.db` and debug files, and fails open |
| F8 | medium | SpecStory release has no attestations; its checksum file is unsigned |
| F9 | low | Opt-out flags work before startup only in bare form (`--no-version-check`, not `=true`) |
| F10 | low | Both tools write a WebAssembly compile cache to the user cache folder |
| F11 | low | SpecStory creates `~/.specstory/cli/config.toml` on first run |
| F12 | low | Claude Code sync needs an existing `--project-path`; the flag is hidden |
| F13 | low | betterleaks reads config and ignore files from environment variables and folders |
| F14 | low | betterleaks has signed checksums and a release attestation, but no build provenance |

## 1. Outbound network paths in SpecStory

First-party code that imports `net/http`, `net` or gRPC: `pkg/utils/version_update.go`,
`pkg/telemetry/telemetry.go`, `pkg/cloud/{sync,auth,skills,resume_client}.go`
and `pkg/cmd/session_uri.go` (command: `grep -rln '"net/http"\|"net"\|grpc'
--include=*.go . | grep -v _test`). Plus the PostHog client. `skills`,
`resume_client` and `session_uri` are used only by the `skills`, `resume` and
`search` commands, not by `sync`. No crash or error reporting service was found
(no Sentry or similar); a panic is only logged locally
(`specstory-cli/main.go:1708-1713`).

Startup order in `main()`: a hand-written pre-parse of `os.Args`
(`main.go:1406-1488`), then config files (`main.go:1493-1515`), then
analytics init (`main.go:1669-1679`), OpenTelemetry init (`main.go:1687-1693`),
the version check (`main.go:1704`), and only then cobra parses flags
(`main.go:1796`). Nothing is sent before the pre-parse and config load. The
version check, analytics and telemetry decisions use only the pre-parsed
flags and the config files (see F9).

| Path | Default | Turn off | Evidence |
| --- | --- | --- | --- |
| PostHog analytics (`https://us.i.posthog.com`) | on in release builds | `--no-usage-analytics` (bare form), config `[analytics] enabled = false` | F2 |
| Version check: `HEAD https://github.com/specstoryai/getspecstory/releases/latest` | on | `--no-version-check` (bare form), config `[version_check] enabled = false` | F3 |
| SpecStory Cloud (`https://cloud.specstory.com`): session sizes GET, HEAD, PUT upload, token refresh | on, but sends only when logged in | `--no-cloud-sync`, config `[cloud_sync] enabled = false` | F6 |
| OpenTelemetry OTLP gRPC export | off unless an endpoint is set | `OTEL_SDK_DISABLED=true`; no `--telemetry-endpoint`, no `[telemetry] endpoint` | F5 |
| Login, logout, device refresh (`/api/v1/device-*`) | only from `login`, `logout`, `--cloud-token`, or a lazy refresh during cloud sync | not reachable from `sync` with cloud sync off | `pkg/cloud/auth.go:316,457,685`, `main.go:231-248` |

**F2 (high): PostHog analytics.** The release build injects a PostHog key
(`.goreleaser.yml:24`); without a key analytics is off
(`pkg/analytics/client.go:83-86`). With it, `Init` creates a client that sends
each event at once (`client.go:88-95`; PostHog's default endpoint is
`https://us.i.posthog.com`, `posthog-go` v1.25.2 `config.go:239`). Every event
carries the full command line, the working folder and OS details
(`pkg/analytics/events.go:62-84`). `sync` sends events with session IDs, error
text and counts (`main.go:962-965, 1033-1045, 1362-1375`) and the project name
when a project identity is first created
(`pkg/utils/project_identity.go:254-270`). The command line includes
`--project-path` and `--output-dir`, which may name students or courses.
Default on: `config.go:779-785`.

**F3 (medium): version check.** `utils.CheckForUpdates` sends a HEAD request to
GitHub unless `noVersionCheck` is set (`pkg/utils/version_update.go:13-34`),
blocking at startup (`main.go:1704`). It sends no session data, but reveals the
IP address and use. Default on: `pkg/config/config.go:715-721`.

**F5 (medium): OpenTelemetry.** Telemetry turns on whenever an endpoint is
set (`config.go:789-795`), and the environment variable
`OTEL_EXPORTER_OTLP_ENDPOINT` sets one, overriding config files
(`config.go:572-580`). It then dials the endpoint
(`pkg/telemetry/telemetry.go:187-199`) and exports one span per exchange
with the prompt text, unless
`--no-telemetry-prompts` or `[telemetry] prompts = false` is set
(`main.go:945`, `pkg/telemetry/stats_helpers.go:143-153`). An endpoint set for
another tool would leak prompts. `OTEL_SDK_DISABLED=true` beats every other
setting (`config.go:790`). No `OTEL_*` variable was set in this review's shell
(`env | grep -c '^OTEL_'` printed 0).

**F6 (medium): SpecStory Cloud.** Cloud sync defaults to on
(`config.go:724-730`, `main.go:221`). Each session goes to
`SyncSessionToCloud` (`main.go:1067`), which returns early when sync is off
(`pkg/cloud/sync.go:1178-1186`) or when there is no valid token in
`~/.specstory/cli/auth.json` (`sync.go:1188-1191`, `auth.go:220-284`).
Otherwise it uploads the Markdown, the raw session JSONL and session JSON to
`https://cloud.specstory.com` (`sync.go:664, 803-809, 940-941`), after a bulk
size GET (`main.go:838-857`, `sync.go:323`) and a HEAD (`sync.go:543-544`).
`--cloud-token` authenticates without the file (`main.go:231-248`).

**F9 (low): pre-parse matches only bare flags.** The version check and
analytics start before cobra parses flags, so they see only the hand-parsed
forms: `--no-usage-analytics` and `--no-version-check` exactly
(`main.go:1411-1412, 1421-1422`). `--no-usage-analytics=true` would be missed
at startup, and cobra's later parse does not stop an analytics client that was
already created. The config keys in section 7 cover both cases.

## 2. Files and folders `sync` reads and writes

| What | Default location | Moved or stopped by | Evidence |
| --- | --- | --- | --- |
| User config, read | `~/.specstory/cli/config.toml` | only `HOME` | `config.go:331-344, 388-395` |
| User config, created if missing | same | only `HOME`; pre-create the file | F11, `config.go:333-337, 511-523` |
| Project config, read | `<cwd>/.specstory/cli/config.toml` | `--config-dir` (pre-parsed) | `config.go:347-362, 398-405`, `main.go:1448-1454` |
| Project config, created if missing | `<cwd>/.specstory/cli/config.toml` | `--config-dir`; pre-create the file | `main.go:577`, `config.go:536-560` |
| Markdown files | `<cwd>/.specstory/history/` | `--output-dir` (written flat into it) | `pkg/utils/path_utils.go:136-141`, `main.go:991, 1014` |
| `.project.json` | `<cwd>/.specstory/` | `--output-dir` | `path_utils.go:122-131, 154-156`, `project_identity.go:112-125, 247` |
| `statistics.json` and `statistics.json.lock` | `<cwd>/.specstory/` | `--output-dir`; `--no-stats` stops both | `path_utils.go:164-167`, `main.go:978-981`, `pkg/session/statistics.go:209-219` |
| Write-test temp file `.specstory_write_test_*` | inside `--output-dir` and `--debug-dir` | created and removed | `path_utils.go:72-77` |
| Legacy `.history.json` | deleted from the history folder if present | — | `path_utils.go:188-193` |
| Debug JSON per session | `<cwd>/.specstory/debug/<id>/` | only with hidden `--debug-raw`; `--debug-dir` moves it | `pkg/session/session.go:37-44`, `pkg/spi/path_utils.go:366-371` |
| Debug log | `<debug dir>/debug.log` | only with `--log` | `main.go:189-195`, `path_utils.go:159-161` |
| Session index `sessions.db` (+ `-wal`, `-shm`) | `~/.specstory/sessions.db` | only `HOME`; no flag | F1 |
| Cloud auth, read | `~/.specstory/cli/auth.json` | only `HOME` | `path_utils.go:264-269`, `pkg/cloud/auth.go:220-284` |
| Git metadata, read | `.git` and git config of the project path's repository | `--git-origin` skips the origin read | `project_identity.go:517-603` |
| WebAssembly compile cache | `$XDG_CACHE_HOME` or `~/.cache/com.github.wasilibs` | `XDG_CACHE_HOME` or `HOME` | F10 |

With `--output-dir`, `--config-dir` and a `HOME` inside the config folder, no
write reaches the project folder or any repository: every project-level path
goes through `GetSpecstoryDir()`, which returns the output folder when it is
set (`path_utils.go:122-131`). `--project-path` changes only session discovery
and identity (`main.go:1300`, `project_identity.go:55-68`), not where files go.
The launch folder still matters for the project config read, so run from the
staging folder.

**F1 (high): unredacted session text in `sessions.db`.** Each `sync` opens
`~/.specstory/sessions.db` (`main.go:876`, `pkg/cmd/reindex.go:504-514`,
`pkg/sessionindex/store.go:105-112`) and stores every session's full
conversation text in an FTS5 search table (`store.go:239-246`,
`reindex.go:533-583, 684-697`). This happens at `main.go:953`, before redaction
at `main.go:972-975`, so secrets are stored as they are. No flag or config key
turns it off; failures are silently ignored (`reindex.go:510-514`). Only
redirecting `HOME` moves it.

**F4 (medium): default writes in the project.** Without flags, `sync` writes
Markdown, `.project.json`, `statistics.json` and a config file under
`<cwd>/.specstory/` (table above). Run from a repository, this puts student
data into the working tree.

**F11 (low):** the first run creates a commented-out
`~/.specstory/cli/config.toml`. It holds no data.

## 3. What the `claude` and `codex` providers read

Provider IDs are `claude` and `codex` (`pkg/spi/factory/registry.go:70, 78`).

**Claude Code.** The store root is `$CLAUDE_CONFIG_DIR`, else `~/.claude`
(`pkg/providers/claudecode/path_utils.go:15-24`). The project path is
symlink-resolved and every non-alphanumeric character becomes `-`, giving
`<root>/projects/<encoded>` (`path_utils.go:94-140`). Only that folder is
walked, recursively, for `*.jsonl` (`jsonl_parser.go:104-122`). Sessions
started in a subfolder of the project have their own encoded folder and are
not included. Subagent (sidechain) records are included: the recursive walk
picks up files in nested folders, and sidechain records are merged into the
parent's exchanges (`agent_session.go:115-150`, `jsonl_parser.go:402-410`).
Leading sidechain "warmup" records are dropped (`provider.go:31-49`).

**F12 (low): nonexistent project path.** `filepath.EvalSymlinks` fails for a
path that does not exist (`claudecode/path_utils.go:111-113`), so
`DetectAgent` returns false (`provider.go:240-253`) and `sync` prints "No
Claude Code project found" and exits without error (`main.go:1303-1306`). This
was read from the code, not run. A workaround is to create an empty folder at
that path for the run. Codex does not have this problem: `normalizeCodexPath`
falls back to the cleaned path when symlink resolution fails
(`codexcli/path_utils.go:35-46`). `--project-path` is a hidden flag
(`main.go:1620-1621`) and may change without notice.

**Codex CLI.** The store root is `$CODEX_HOME/sessions`, else
`~/.codex/sessions` (`codexcli/path_utils.go:12-19`). The provider walks every
`YYYY/MM/DD` folder and reads the first line (`session_meta`) of every session
file, for all projects (`provider.go:468-560, 729-760`). A session matches when
its recorded `cwd` equals the project path exactly, ignoring case
(`provider.go:564-571`); subfolder sessions do not match. Full content is read
only for matching sessions. `archived_sessions` is not read.

Neither provider reads `~/.codex/auth.json`, `~/.claude/settings.json`,
Claude's `history.jsonl` or other projects' content (command:
`grep -rn 'auth.json\|settings.json\|history.jsonl\|os.Getenv'
pkg/providers/claudecode pkg/providers/codexcli`). The environment variables
read are `CLAUDE_CONFIG_DIR` and `CODEX_HOME`; the others found
(`HOMEBREW_PREFIX`, `NVM_*`, `PATH`) are in the `run` and `check` code paths
(`codexcli/codex_cli_exec.go:59-143`). Git remotes are read from the local git
config only, for project identity (`project_identity.go:517-603`); nothing is
fetched.

## 4. Secret redaction

On by default: `[redaction] enabled` defaults to true (`config.go:990-998`),
and only `--no-redact-secrets` turns it off (`main.go:1536, 1643`). It uses
betterleaks v1.8.1 (`go.mod:17`) with its embedded default ruleset
(`pkg/redact/redact.go:50-58`; `betterleaks@1.8.1/config/config.go:22, 180-181`).
That ruleset has 417 rules, against 463 in v1.9.0 (command:
`grep -c '^\[\[rules\]\]' config/betterleaks.toml` in each tree). Live
validation is off, because `NewDetector` passes empty `ValidationOptions`
(`betterleaks@1.8.1/detect/deprecated.go:243-245`, `detect/detect.go:313`).
Each secret becomes `[REDACTED:<rule-id>]` (`redact.go:142`).

**F7 (medium): what redaction does not cover.**

- Personal data such as names, student numbers or grades. It detects only
  credential patterns.
- File names: each Markdown file is named from the first four words of the
  first prompt (`pkg/spi/path_utils.go:126-129`, `claudecode/provider.go:577-590`,
  `pkg/session/session.go:64-65`), with no redaction.
- `sessions.db` (F1) and `--debug-raw` debug files (`main.go:949`), both
  written before or without redaction.
- It fails open: if the detector cannot be built, content is written
  unredacted with only a log warning (`redact.go:104-111`).
- A secret longer than the 10,000-character chunk overlap that spans a chunk
  boundary can be missed (`redact.go:21-31`).

Because of these gaps, the betterleaks v1.9.0 scan in section 7 is still
needed.

## 5. betterleaks v1.9.0 `dir` mode

**Network.** `dir` uses the `sources.Files` source (`betterleaks/cmd/directory.go:63-70`),
which has no network code (command: `grep -n 'net/http' sources/file.go`
returns nothing). HTTP downloads live only in the GitHub, GitLab, Hugging Face
and S3 sources (`sources/common.go:156`, callers `sources/github.go:570`,
`gitlab.go:1524`, `huggingface.go:843`). Live secret validation, the only
other network path, is off unless `--validation` is given
(`cmd/root.go:112`, `detect/detect.go:313`). The ruleset is embedded; no rule
or update download exists (`betterleaks/main.go` has no update check; config loading reads
only local files or environment variables, `cmd/root.go:179-250`). Never pass
`--validation`: it sends found secrets to provider APIs.

**Reads.** The scanned folder; a config from `--config`, `BETTERLEAKS_CONFIG`,
`GITLEAKS_CONFIG`, `BETTERLEAKS_CONFIG_TOML`, `GITLEAKS_CONFIG_TOML`, or a
`.betterleaks.toml` / `.gitleaks.toml` in the scanned folder
(`cmd/root.go:179-250, 271-280`); ignore files from `-i` (default `.`, the
launch folder, `cmd/root.go:100`) and the scanned folder
(`cmd/root.go:283-292, 449-469`); a baseline only with `-b`
(`cmd/root.go:472-478`). This is F13 (low): a stray config or ignore
file could hide findings. Run from the staging folder and unset those
variables.

**Writes.** The report file only with `-r`, after a create-and-remove
writability probe (`cmd/root.go:481-490, 610-637`). Temp files in `$TMPDIR`
only when scanning archives (`sources/file.go:164`). Profiles only with
`--diagnostics` (default off, `cmd/root.go:126`). The WebAssembly compile
cache (F10).

**JSON report with redacted matches.** `-f json -r <file> --redact=100`.
Redaction is applied to all findings before the report is written
(`cmd/root.go:589`); it replaces the secret in `Match`, `MatchContext`, capture
groups and component findings with `REDACTED` (`report/finding.go:170-200`).
The full `Line` is never written to JSON (`report/finding.go:34`), and no
non-test code sets the `Fragment` field (command:
`grep -rnE '\bFragment\s*[:=]|\.Fragment\s*=' --include=*.go detect report cmd sources`).
The report still holds file paths, which contain the prompt-derived file names.

**F10 (low): compile cache.** Both tools use `betterleaks/go-re2`
v1.11.0-betterleaks.3 (`specstory-cli/go.mod:48`, `betterleaks/go.mod:64`),
which stores compiled WebAssembly under `os.UserCacheDir()/com.github.wasilibs`
(`internal/re2_wazero.go:184-189` in that module). It holds compiled code, not
scanned data. Set `XDG_CACHE_HOME` to keep it in the config folder.

## 6. Release artifacts

**SpecStory `SpecStoryCLI_Linux_x86_64.tar.gz` (F8, medium).**

- Checksum file: yes, `SpecStoryCLI_2.15.1_checksums.txt`. It lists sha256
  `7d8e842a81a8acd07a868d090ad89552028b22ec22df839f20615977abedd017`, which
  matches GitHub's asset digest (`gh api
  repos/specstoryai/getspecstory/releases/tags/v2.15.1`). The checksum file is
  not signed.
- Attestations: none. `gh api
  repos/specstoryai/getspecstory/attestations/sha256:7d8e842a…` returns 404.
  The release workflow has no attestation or signing step and no `id-token`
  permission (`.github/workflows/release.yml:8-9, 39-46`).
- Build commit: the workflow runs on tag `specstory-cli/v2.15.1`
  (`release.yml:3-6`), which points to commit `2722e748…`, not `ec171381…`.
  Both have the same tree `239f8dca…`; GitHub's compare shows 8 merge-only
  commits and no file changes (`gh api
  repos/specstoryai/getspecstory/compare/ec171381…2722e748…`).
- mise: paranoid mode "rechecks supported provenance" (mise v2026.9.17
  `docs/paranoid.md`), and `locked_verify_provenance` re-verifies provenance
  already recorded in the lockfile (`settings.toml:1751-1763`). With none to
  record, mise can pin only the checksum. Whether mise refuses such a tool in
  paranoid mode was not verified.

**betterleaks `betterleaks_1.9.0_linux_x64.tar.gz` (F14, low).**

- Checksum file: yes, `checksums.txt`, signed keylessly with cosign
  (`checksums.txt.sigstore.json`; `betterleaks/.goreleaser.yml:35-36, 84-97`).
  The tarball's sha256
  `f8b185a39ffcece2a1ca82bf3a4e7435cd81963ffd16b7a9128daf75f35f6de7` matched
  `checksums.txt` (`sha256sum -c --ignore-missing checksums.txt` printed OK).
- Attestations: one, a GitHub release attestation
  (predicate `https://in-toto.io/attestation/release/v0.2`) covering all
  assets. There is no SLSA build-provenance attestation. The local `gh` is
  2.46.0, which has no `gh attestation` command, so the attestation and the
  cosign signature were not cryptographically verified here. Verify with
  `gh attestation verify <file> -R betterleaks/betterleaks` on gh 2.49 or
  later.

## 7. Safe command lines

Choose a staging folder outside every repository, for example
`~/session-staging`. Keep the config folder inside it.

```sh
STAGE="$HOME/session-staging"
CFG="$STAGE/config"
REAL_HOME="$HOME"
mkdir -p "$CFG/home/.specstory/cli" "$CFG/cache" "$STAGE/out"
```

Write this file to both `$CFG/home/.specstory/cli/config.toml` (user level)
and `$CFG/config.toml` (project level, read through `--config-dir`).
Pre-creating both stops SpecStory from writing defaults
(`config.go:333-337, 546-549`).

```toml
[version_check]
enabled = false

[cloud_sync]
enabled = false

[analytics]
enabled = false

[redaction]
enabled = true
```

Run once per project path and provider. Use a fresh output folder per project.

```sh
cd "$STAGE"
env -u OTEL_EXPORTER_OTLP_ENDPOINT -u OTEL_SERVICE_NAME \
  HOME="$CFG/home" XDG_CACHE_HOME="$CFG/cache" OTEL_SDK_DISABLED=true \
  CLAUDE_CONFIG_DIR="$REAL_HOME/.claude" CODEX_HOME="$REAL_HOME/.codex" \
  specstory sync claude \
    --project-path /absolute/project/path \
    --output-dir "$STAGE/out/<project-name>" \
    --config-dir "$CFG" \
    --no-usage-analytics --no-version-check --no-cloud-sync --no-stats
```

For Codex, replace `sync claude` with `sync codex`. Write the flags exactly as
shown, without `=true` (F9: the pre-parse at `main.go:1411, 1421` matches only
the bare form). The config file is a second guard. Do not add `--log`,
`--debug`, `--debug-raw`, `--telemetry-endpoint` or `--cloud-token`.

After each run, delete `$CFG/home/.specstory/sessions.db*` (F1). Before
publishing anything, review file names in `$STAGE/out` for personal data
(F7).

Scan the Markdown:

```sh
cd "$STAGE"
env -u BETTERLEAKS_CONFIG -u GITLEAKS_CONFIG \
  -u BETTERLEAKS_CONFIG_TOML -u GITLEAKS_CONFIG_TOML \
  XDG_CACHE_HOME="$CFG/cache" \
  betterleaks dir "$STAGE/out" -i "$STAGE/out" --no-banner \
    --redact=100 -f json -r "$STAGE/betterleaks-report.json"
```

The exit code is 1 when leaks are found (`cmd/root.go:82`). Do not add
`--validation`.

With these lines, the only network paths found are disabled, and writes are
limited to `$STAGE/out`, `$CFG`, and `betterleaks-report.json`. Files in
`$TMPDIR` appear only if an archive is scanned. This was checked by reading
the code; it was not confirmed by running under a network sandbox. A first
run under `unshare -rn` or with the network off would confirm it.

## Not verified

- Runtime behavior. Nothing was run, including the nonexistent-path behavior
  in F12.
- Third-party modules beyond `posthog-go`'s default endpoint and `go-re2`'s
  cache path, for example `charmbracelet/fang`.
- Whether `~/.specstory/cli/auth.json` exists on this laptop. It was not
  opened, per the task rules. If it exists, F6 applies in full without
  `--no-cloud-sync`.
- Cryptographic checks of the betterleaks cosign signature and release
  attestation (F14), and how mise paranoid mode treats a tool without
  provenance (F8).

## Addendum: `sync -s <id> --print`

Added by the coordinator on 2026-09-30, after the develop merge review of the
code noted that sections 1 to 7 do not cover `--print`. The selection
procedure runs `specstory sync <claude|codex> -s <id> --print` with the flags
and environment of section 7, but without `--output-dir`, and writes the
printed Markdown itself.

- `--print` skips the output setup and the live session index: with it,
  `SetupOutputConfig` and `NewLiveIndexer` are not called
  (`specstory-cli/main.go:632-656`), so this path writes no history folder,
  `.project.json`, `statistics.json` or `sessions.db`.
- The print branch generates the Markdown, redacts it unless
  `--no-redact-secrets` is given, and writes it to standard output
  (`main.go:747-781`, redaction at `main.go:763-769`). Cloud sync and file
  writes happen only in the other branch (`main.go:782-792`).
- `--print` cannot be combined with `--only-stats`, `--only-cloud-sync` or
  `--console` (`main.go:113-121`).
- What remains: the analytics events of the print branch (`main.go:778-781`),
  which section 7's flag and configuration turn off; debug data only with
  `--debug-raw` (`main.go:749`), which the procedure never passes; and the user
  configuration file of F11, which the procedure writes first inside the
  staged home.

Observed on this laptop on 2026-09-30: the procedure rendered 1,467 sessions
inside `bwrap --unshare-net`, where a connection attempt failed with "Network
is unreachable". Afterwards `~/.specstory` did not exist, the staged home held
only `.specstory/cli/`, and the Claude Code mirror folders were empty.

The verdict stands: pass, with the procedure's command line.
