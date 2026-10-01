# Tasks: Reference Library for Agents

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Reviews and pins

- [x] T001 Review `zotero-native-mcp` 1.0.1 before pinning
  (`security/zotero-native-mcp-1.0.1.md`, FR-008).
  - By main (Claude Code): 0 high, 2 medium, 2 low; controls: block the three
    delete tools, keep the base URL on loopback, no student data.
- [x] T002 Pin the connector: `plugins/work/package.json` and
  `package-lock.json` (the lock is the one the hand-installed copy under
  `~/.local/share/mcp-servers/zotero/1.0.1` came from; `npm ci` reproduces
  that tree byte for byte), the `reference-library` entry in
  `plugins/work/mcp.json`, the npm install in `orca.yaml` and the CI check
  workflow, and a doctor check in `mise.toml` (FR-005).
- [x] T003 Pin Caddy 2.11.4 (`mise.toml`, `mise.lock`, `orca.yaml`) and review
  it (`security/caddy-2.11.4.md`, FR-010).

## Phase 2: Units (User Story 1)

- [x] T004 `infra/reference-library/`: socket, proxy, gateway and app units,
  the Caddyfile, the shortcut and `install.sh` (FR-001 to FR-004).
  - Two design changes came from live tests: the Host header (Caddy, the
    user's decision) and a proxy left up after an open app closed (the app
    unit now holds a connection to the open app and the proxy is bound to it).
    A shortcut quoting that `desktop-file-validate` accepts but GLib refuses
    was also fixed; `scripts/reference-library-test.ts` runs the shortcut
    through GLib.
- [x] T005 Install on the user's machine and run the live tests
  (`evidence/live-tests.md`, SC-001).

## Phase 3: Clients (User Story 2)

- [x] T006 Deny rules in `.claude/settings.json` and the user's
  `~/.claude/settings.json`, `disabled_tools` and the neutral entry in the
  user's `~/.codex/config.toml` (dated backups `*.bak-2026-10-01`), and the
  evidence that the block works (FR-006, FR-007).
- [x] T007 `scripts/reference-library-test.ts` (new, `npm run
  test:reference-library`), `scripts/plugin-skills-test.ts`, `tsconfig.json`,
  `turbo.json`, `package.json` (FR-009).
- [x] T008 `docs/architecture.md` and the generated `docs/reference/` files
  (`npm run doc-regions:update`).

## Phase 4: Finish

- [ ] T009 Merge `develop`, run `npm run verify`, pass the develop merge review
  by a provider other than Claude Code, commit the review record and finish
  with `git flow feature finish reference-library`.
  - 2026-10-01: `develop` stayed at ab02ad5, so no merge was needed;
    `npm run verify` printed VERIFIED (38 of 38) on the implementation commit
    dd9ec12. `doc-regions:prepare` produced 5 `jev_verify` requests and 1
    `jev_classify` request, all sent to the plugin's backfire (`openrouter`,
    `typesafe/jev-1.13`): 0 units contradicted, 12 verified, 264 unsupported
    (no evidence among the changed files, as designed). `doc-regions:audit`
    reported findings on `AGENTS.md` and the constitution only (not changed by
    this feature; left for the user).
  - Reviewer choice: one `jev_decide` over Codex `gpt-6-luna` medium, Copilot
    auto (balance), Grok `grok-4.7` medium, Cursor auto and Antigravity
    `gemini-3.8-flash-medium`, with usage on 2026-10-01 (Codex weekly 68% used,
    2 reset credits expiring 2026-10-22 and 2026-10-29; Copilot monthly 12.5%;
    Grok weekly 0%; Cursor monthly 0%, free plan; Antigravity unknown). The
    answer named provider `openrouter`, model `typesafe/jev-1.13`; agent:
    Copilot `auto` with the balance tier (probability 0.38, confidence 0.28;
    Grok 0.28, Cursor 0.15, Codex 0.13, Antigravity 0.00). Claude Code
    implemented the feature, so it was not a candidate.
  - Reviewer: a fresh Copilot CLI session (`auto`, balance tier; the status line
    showed `Auto · Balance → gpt-5.6-luna`), started through Orca's terminal
    path, read-only, given the scope `ab02ad5..c3b678f` and the spec. It found
    no findings (high 0, medium 0, low 0) in about 11 minutes and used 2.16 AI
    credits of the Free plan's 200 a month. One path-access prompt for the
    Caddy binary was allowed once.
