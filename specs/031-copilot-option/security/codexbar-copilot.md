# CodexBar v0.69.0 Copilot provider security review

Date: 2026-09-30. Scope: Linear CHE-60.

Assumption: the command is exactly `codexbar usage --provider copilot --format json` on Linux. No CodexBar config file exists. `~/.config/codexbar/providers/` is empty. The process receives only the Copilot credential and normal runtime variables. The current directory is outside every repository.

## Scope and method

The reviewed source is tag `v0.69.0`, commit `48ded68da6932a4fe5de9037d06c4ac48bd36e90`, at `.local/copilot-option/codexbar-src`. Source references below are relative to that directory.

This was a static, read-only review. CodexBar, `CodexBarCLI`, and any Copilot CLI were not run. Nothing was built, installed, or fetched. No credential store was read. In particular, this review did not read `~/.copilot`, `~/.config/gh`, `~/.codex`, `~/.claude`, `~/.config/verbose-broccoli/providers`, or a system keyring. The source and `docs/copilot.md` were treated as untrusted data.

The earlier CodexBar reviews already cover release provenance and shared CLI behavior. This report does not repeat their shared findings. It names a shared behavior only where question 4 requires it.

## Finding

### F1 (low): the caller can give the command a GitHub token with more rights than it needs

The provider accepts any nonempty `COPILOT_API_TOKEN`. It trims the string but does not check its token type or scope (`Sources/CodexBarCore/Providers/Copilot/CopilotProviderDescriptor.swift:3-16,128-133`; `Sources/CodexBarCore/Providers/ProviderCredentialAdapter.swift:277-310`). It sends that value as `Authorization: token <value>` (`Sources/CodexBarCore/Providers/Copilot/CopilotUsageFetcher.swift:58-68`).

The only token-creation flow in the source uses GitHub OAuth, the Visual Studio Code client ID, and the scope `read:user` (`Sources/CodexBarCore/Providers/Copilot/CopilotDeviceFlow.swift:6-10,84-101`). The source calls this a GitHub OAuth token, not a Copilot service token (`CopilotUsageFetcher.swift:63-65`). It does not show that a classic or fine-grained personal access token is required.

Impact: a broad personal access token would add needless impact if the environment or process were later exposed. CodexBar does not broaden the token itself, and the reviewed request sends it only to GitHub. This keeps the severity low.

Limit: a user must provision a dedicated GitHub OAuth token accepted by the Copilot internal endpoint. Prefer a token produced by the shown device flow, with the shown `read:user` request. Do not give the agent a general GitHub personal access token with repository or administration rights.

## 1. Credential

Under the stated conditions, the only credential source is `COPILOT_API_TOKEN` in the process environment.

The command first tries to load one CodexBar config path. The path order is `$CODEXBAR_CONFIG`, absolute `$XDG_CONFIG_HOME/codexbar/config.json`, `~/.config/codexbar/config.json`, then legacy `~/.codexbar/config.json` (`Sources/CodexBarCore/Config/CodexBarConfigStore.swift:20-34,74-113`). When no file exists, the CLI builds an in-memory default and does not save it (`Sources/CodexBarCLI/CLIHelpers.swift:443-450`; `Sources/CodexBarCore/Config/CodexBarConfig.swift:123-132,268-276`).

Credential precedence, if the preconditions drift, is:

1. A selected or active Copilot token account from CodexBar config. It replaces `COPILOT_API_TOKEN` in the fetch environment (`Sources/CodexBarCLI/TokenAccountCLI.swift:73-80,86-127`; `Sources/CodexBarCore/Providers/ProviderEnvironmentResolver.swift:10-29`).
2. `providers[].apiKey` for Copilot in CodexBar config. The default projection uses config precedence and overwrites the same environment key (`Sources/CodexBarCore/Providers/ProviderCredentialAdapter.swift:3-32,277-304`).
3. The caller's `COPILOT_API_TOKEN` (`Sources/CodexBarCore/Providers/Copilot/CopilotProviderDescriptor.swift:5-16,128-133`).

There is no configured account or API key in this review, so steps 1 and 2 are absent. The caller must supply step 3. The code does not read `GITHUB_TOKEN`, `GH_TOKEN`, GitHub CLI login files, `~/.copilot`, another tool's login, or a keychain on this path.

The macOS app has a legacy Copilot keychain store and a device-login user interface. They are in the app target, not the Linux CLI path (`Sources/CodexBar/CopilotTokenStore.swift:1-21`; `Sources/CodexBar/Providers/Copilot/CopilotLoginFlow.swift:1-14`).

## 2. Network

### Request made by the reviewed command

The command makes one initial request. A same-origin HTTPS redirect can add another request on the same host:

| Method | Host and path | Headers | Credential |
|---|---|---|---|
| `GET` | `https://api.github.com/copilot_internal/user` | `Authorization: token <COPILOT_API_TOKEN>`; `Accept: application/json`; `Editor-Version: vscode/1.96.2`; `Editor-Plugin-Version: copilot-chat/0.26.7`; `User-Agent: GitHubCopilotChat/0.26.7`; `X-Github-Api-Version: 2025-04-01` | The GitHub OAuth token is sent only in `Authorization`. |

Evidence: `Sources/CodexBarCore/Providers/Copilot/CopilotUsageFetcher.swift:41-68,162-168`. No `httpMethod` is set, so `URLRequest` uses `GET`. The response must be HTTP 200. HTTP 401 and 403 become a generic authentication error. Other statuses become a generic server error (`CopilotUsageFetcher.swift:68-79`). Response bodies and headers are not put into the error.

The shared client allows redirects only when both URLs use HTTPS and the scheme, host, and port stay the same (`Sources/CodexBarCore/ProviderHTTPClient.swift:212-235`). The source does not prove whether Foundation keeps the `Authorization` header on a same-origin redirect.

### Network code that does not run here

- `--status` would add `GET https://www.githubstatus.com/api/v2/status.json`. The exact command has no `--status`, so the branch is off (`Sources/CodexBarCLI/CLIUsageCommand.swift:83-85`; `Sources/CodexBarCLI/CLIUsageFetchSetup.swift:37-39`; `Sources/CodexBarCore/ProviderStatusFetcher.swift:46-59`; `Sources/CodexBarCore/Providers/Copilot/CopilotProviderDescriptor.swift:52-53`). No credential is attached to that request.
- Budget enrichment first needs a Copilot settings snapshot, the public GitHub host, `budgetExtrasEnabled == true`, and a cookie source other than off (`CopilotProviderDescriptor.swift:135-158`). The reviewed CLI builds no Copilot credential-settings contribution: the descriptor supplies only a cookie reader, while that registration's credential builder defaults to `nil` (`CopilotProviderDescriptor.swift:18-25`; `Sources/CodexBarCore/Providers/ProviderSettingsSnapshot.swift:99-112`; `Sources/CodexBarCLI/TokenAccountCLI.swift:130-147`). The guard therefore stops this branch.
- In an app-supplied budget context, identity lookup would use `GET https://api.github.com/user` with the GitHub token and `Accept: application/json` (`CopilotProviderDescriptor.swift:176-189`; `CopilotUsageFetcher.swift:136-159`). It would then use GitHub web cookies for `GET https://github.com/settings/billing/budgets` and the same path with `page`, `page_size=10`, and `scope=customer`. Those requests set `Cookie`, `Accept`, `User-Agent`, and, for JSON, `Referer`, `X-Requested-With`, `GitHub-Verified-Fetch`, and an optional `X-Fetch-Nonce` (`Sources/CodexBarCore/Providers/Copilot/CopilotBudgetWebFetcher.swift:441-495`). Browser import is compiled only for macOS (`CopilotBudgetWebFetcher.swift:754-801`). None of this runs here.
- Device login would use `POST https://github.com/login/device/code` and `POST https://github.com/login/oauth/access_token`. Both send form data with `Accept: application/json` and `Content-Type: application/x-www-form-urlencoded` (`Sources/CodexBarCore/Providers/Copilot/CopilotDeviceFlow.swift:51-56,84-130`). Only the AppKit login flow calls it (`Sources/CodexBar/Providers/Copilot/CopilotLoginFlow.swift:1-14,21-53`). The Linux usage command cannot start it.
- No telemetry or identity lookup runs on the reviewed path. The main request decodes usage and plan data directly. Identity lookup is only in the stopped budget branch or the macOS login flow.

## 3. Storage and output

### Writes

The Copilot provider does not explicitly write its token, response, usage snapshot, or config on this path. The CLI calls `load`, not `loadOrCreateDefault`, and creates the default only in memory (`Sources/CodexBarCLI/CLIHelpers.swift:443-450`; `Sources/CodexBarCore/Config/CodexBarConfigStore.swift:32-50`). No token updater is used by the single Copilot API strategy.

One shared startup write still applies: every resolved CLI command refreshes user plugins before command dispatch (`Sources/CodexBarCLI/CLIEntry.swift:48-54`). Discovery creates `~/.config/codexbar/providers/` and lists `.js` and `.ts` files (`Sources/CodexBarCore/Plugins/UserProviderPlugins.swift:231-239,275-304,439-450`). The directory is already empty under the stated conditions. This is the shared low finding already covered by the earlier reports, so it is not repeated as a new finding here.

The CLI logs to standard error at level `error` unless logging flags change it (`Sources/CodexBarCLI/CLIEntry.swift:409-423`). A file-log handler exists, but its sink starts disabled and the CLI does not enable it (`Sources/CodexBarCore/Logging/CodexBarLog.swift:78-107,149-157`; `Sources/CodexBarCore/Logging/FileLogHandler.swift:4-35`). The successful Copilot request does not log the token or response.

The shared HTTP client uses `URLSessionConfiguration.default`, not an explicit no-cache session (`Sources/CodexBarCore/ProviderHTTPClient.swift:168-205`). The source does not establish whether swift-corelibs Foundation writes an authenticated response to disk on this Linux host. This was not tested. It is not a confirmed write or finding.

### JSON account identity

The output is a JSON array. Its provider object can carry an outer `account` field and a `usage` object (`Sources/CodexBarCLI/CLIPayloads.swift:4-34,67-96`). With no config or token account, outer `account` is `nil` and Swift omits it.

The Copilot snapshot creates this identity only:

- `usage.identity.providerID`: `copilot`
- `usage.identity.loginMethod`: the capitalized `copilot_plan` value
- legacy `usage.loginMethod`: the same plan label

It sets `accountEmail` and `accountOrganization` to `nil`, and leaves `accountID` at its `nil` default (`Sources/CodexBarCore/Providers/Copilot/CopilotUsageFetcher.swift:116-129`; `Sources/CodexBarCore/ProviderIdentitySnapshot.swift:3-29`). The encoder omits the nil email and organization fields but emits the plan through `loginMethod` (`Sources/CodexBarCore/UsageFetcher.swift:370-388`). The plan label is subscription data, not a GitHub login, email, numeric user ID, or organization.

On this exact path, the JSON therefore carries no account identity. A future CodexBar token account would change this: its saved label becomes outer `account` and can also fill `usage.accountEmail` (`Sources/CodexBarCLI/CLIUsageCommand.swift:443-488`; `Sources/CodexBarCore/UsageSnapshot+AccountLabel.swift:3-17`). Keeping the config absent is part of the verdict.

## 4. Accidental triggers

- Other providers do not run. `copilot` parses as one provider and `asList` returns only that provider (`Sources/CodexBarCLI/CLIOptions.swift:60-100`; `Sources/CodexBarCLI/CLIHelpers.swift:18-29`).
- No Copilot CLI or other subprocess runs. The Copilot descriptor has one API strategy and no version detector (`Sources/CodexBarCore/Providers/Copilot/CopilotProviderDescriptor.swift:92-97`).
- No interactive prompt, browser opening, device flow, or keychain prompt runs. The CLI marks the fetch as background (`Sources/CodexBarCLI/CLIUsageCommand.swift:83-112`). The interactive flow is AppKit-only, as shown above.
- No file in another tool's directory is read or written. The reviewed code has no current-directory or Git-repository lookup. Running outside a repository adds defense but does not change this path.
- The shared plugin scan still creates and reads `~/.config/codexbar/providers/`. If that directory later contains a `.js` or `.ts` file, startup loads it before provider dispatch. Keep it empty and user-owned.
- Do not add `--status`, `--provider all`, account-selection flags, logging flags, or a config file. They change the reviewed path.

## 5. Verdict and limits for the planned use

**PASS, with the limits below.** There are no high or medium findings. F1 is low. The exact use sends one dedicated GitHub OAuth token to one GitHub API origin and returns quota and plan data without GitHub account identity.

### Limits for the planned use

1. Run exactly `codexbar usage --provider copilot --format json`. Do not add `--status`, account flags, `--verbose`, `--log-level`, or another provider.
2. Supply only `COPILOT_API_TOKEN` as a credential. Keep `CODEXBAR_CONFIG` unset. Keep every CodexBar config location absent, including an `$XDG_CONFIG_HOME` override.
3. Use a dedicated GitHub OAuth token accepted by the Copilot internal endpoint. Prefer the source's device-flow token with its `read:user` request. Do not use a broad personal access token. This closes F1.
4. Allow outbound HTTPS only to `api.github.com:443` for this call. Do not set proxy or certificate-routing variables unless they are part of the trusted host setup.
5. Keep `~/.config/codexbar/providers/` empty, user-owned, and mode 0700. The command may create it if it is missing.
6. Treat the result as subscription and usage data. It contains the Copilot plan under `usage.identity.loginMethod` and `usage.loginMethod`, but no login, email, numeric account ID, or organization under these conditions.
7. Keep the reviewed `CodexBarCLI` and its matching resource bundle together in the already reviewed, user-owned install directory. Do not replace either item independently.

## Clean checks

These checks were read-only. Commands 3 through 7 were run from `.local/copilot-option/codexbar-src`.

1. Commit and tag matched:

   ```sh
   GIT_OPTIONAL_LOCKS=0 git -C .local/copilot-option/codexbar-src rev-parse HEAD
   GIT_OPTIONAL_LOCKS=0 git -C .local/copilot-option/codexbar-src tag --points-at HEAD
   ```

   Result: `48ded68da6932a4fe5de9037d06c4ac48bd36e90` and `v0.69.0`.

2. The target clone was clean:

   ```sh
   GIT_OPTIONAL_LOCKS=0 git -C .local/copilot-option/codexbar-src status --short --branch
   ```

   Result: `## HEAD (no branch)` with no changed paths.

3. No GitHub CLI, foreign Copilot file, or keychain source appeared in the reviewed Linux path:

   ```sh
   rg -n 'GITHUB_TOKEN|GH_TOKEN|/\.config/gh|/\.copilot|KeychainCopilotTokenStore|KeychainStringStore|gh[[:space:]]+auth' \
     Sources/CodexBarCLI/CLIUsageCommand.swift \
     Sources/CodexBarCLI/CLIUsageFetchSetup.swift \
     Sources/CodexBarCLI/TokenAccountCLI.swift \
     Sources/CodexBarCore/Providers/Copilot \
     Sources/CodexBarCore/CopilotUsageModels.swift
   ```

   Result: no matches; `rg` exit 1.

4. No subprocess or prompt primitive appeared in the reviewed Linux path:

   ```sh
   rg -n 'TTYCommandRunner|Process\(|readLine\(|NSAlert|NSWorkspace|standardInput|standardOutput' \
     Sources/CodexBarCLI/CLIUsageCommand.swift \
     Sources/CodexBarCLI/CLIUsageFetchSetup.swift \
     Sources/CodexBarCLI/TokenAccountCLI.swift \
     Sources/CodexBarCore/Providers/Copilot \
     Sources/CodexBarCore/CopilotUsageModels.swift
   ```

   Result: no matches; `rg` exit 1.

5. No common telemetry or crash-reporting SDK name appeared in the reviewed path:

   ```sh
   rg -n -i '\b(sentry|crashlytics|bugsnag|posthog|mixpanel|amplitude|datadog|appcast|sparkle|telemetrydeck|firebase)\b' \
     Sources/CodexBarCLI/CLIUsageCommand.swift \
     Sources/CodexBarCLI/CLIUsageFetchSetup.swift \
     Sources/CodexBarCLI/TokenAccountCLI.swift \
     Sources/CodexBarCore/Providers/Copilot \
     Sources/CodexBarCore/CopilotUsageModels.swift
   ```

   Result: no matches; `rg` exit 1.

6. Device-flow caller search found only the AppKit login flow and the Core definitions:

   ```sh
   rg -n 'CopilotDeviceFlow\(|requestDeviceCode\(|pollForToken\(' \
     Sources/CodexBarCLI Sources/CodexBarCore Sources/CodexBar
   ```

   Result: the caller is `Sources/CodexBar/Providers/Copilot/CopilotLoginFlow.swift`; there is no `Sources/CodexBarCLI` caller.

7. No current-directory or repository lookup appeared in the reviewed path:

   ```sh
   rg -n 'currentDirectory|workingDirectory|/\.git/|\.git/config|git[[:space:]]+(rev|status|log|show|config)' \
     Sources/CodexBarCLI/CLIUsageCommand.swift \
     Sources/CodexBarCLI/CLIUsageFetchSetup.swift \
     Sources/CodexBarCLI/TokenAccountCLI.swift \
     Sources/CodexBarCore/Providers/Copilot \
     Sources/CodexBarCore/CopilotUsageModels.swift
   ```

   Result: no matches; `rg` exit 1.

## Not run or not verified

- `npm run workflow` and `npm run verify` were not run. They write repository receipts, and verification would also exceed this static review's no-build and no-execution boundary.
- The installed binary was not run. Live token acceptance, GitHub response shape, DNS, transport security, proxy behavior, and server-side logging were not verified.
- Linux Foundation locations and persistence for `UserDefaults` and the default `URLSession` cache were not verified.
- Release provenance and binary-to-source evidence were not repeated. The task states that the release tarball was already reviewed for provenance.
