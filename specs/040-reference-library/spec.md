# Feature Specification: Reference Library for Agents

**Feature Branch**: `feature/reference-library`

**Created**: 2026-10-01

**Status**: In progress

**Linear issue**: CHE-76

**Input**: Linear issue CHE-76, "Work plugin: an on-demand reference library
for agents (Zotero without a window)", and the develop session's brief of
2026-10-01. Facts checked on 2026-10-01: Zotero 10.0.5 is installed with its
local API on `127.0.0.1:23119` enabled; `zotero --headless` runs it without a
window and the API answers within 2 seconds; `systemd-socket-proxyd` (systemd
259) supports `--exit-idle-time`; the connector `zotero-native-mcp` 1.0.1 (MIT)
reads and writes through the local API and accepts `ZOTERO_LOCAL_BASE_URL`.
The user decided the same day:

- Agents use the user's Zotero library at any time without the Zotero window.
  Zotero starts without a window on the first request and stops after about 10
  idle minutes, through systemd only.
- Zotero's own port stays 23119, so the app and the browser extension keep
  working. If the app is already open, no second copy starts. Opening the app
  while the background copy runs stops the background copy first.
- Added the same day, after the first live test: Zotero's web server answers
  only a Host header whose port is its own 23119 (`127.0.0.1:23190` gets `400
  Bad Request`), and `systemd-socket-proxyd` cannot change headers. The user
  chose an upstream reverse proxy over own proxy code: Caddy, config only,
  pinned through mise and security-reviewed, behind `systemd-socket-proxyd`
  (which keeps the idle exit), rewriting Host to `127.0.0.1:23119`. Caddy
  listens on loopback only, with its admin endpoint and automatic HTTPS off,
  and starts and stops with the background Zotero.
- The develop session recorded the user's approval to install the units and
  the shortcut, to add the deny rules to `~/.claude/settings.json` and to edit
  `~/.codex/config.toml`, each with a dated backup, and to run the live tests.
- The unit files and the app shortcut are tracked in `infra/` and installed
  with one command.
- The work plugin declares the connector, pinned by a lock file the repository
  controls. Clients block its delete and empty-trash tools.
- Names are provider-neutral; Zotero details stay inside configuration values.
- The connector gets a security review before it is pinned. Writes are tested
  on a throwaway item moved to Zotero's trash; no student data goes into
  Zotero.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The library answers without the window (Priority: P1)

An agent calls a reference-library tool while Zotero is closed. Zotero starts
in the background, answers, and stops itself after about 10 idle minutes.

**Independent Test**: With Zotero closed, send one request to the socket's
port; the API answers and a background copy runs. Ten idle minutes later no
Zotero process is left.

**Acceptance Scenarios**:

1. **Given** Zotero is closed, **When** a request reaches the socket,
   **Then** the background copy starts and the request is answered.
2. **Given** the open app answers on 23119, **When** a request reaches the
   socket, **Then** no second copy starts and the open app answers.
3. **Given** the background copy runs, **When** the user opens the app from its
   menu shortcut, **Then** the background copy stops first and one window
   opens.

### User Story 2 - The work plugin declares the connector, safely (Priority: P2)

The work plugin declares `zotero-native-mcp` 1.0.1 as the `reference-library`
server, pinned by a repository lock file. Claude Code and Codex cannot call its
delete-items, delete-collection or empty-trash tools.

**Independent Test**: A Claude Code and a Codex session that load the server
refuse those three tools and still list and read items.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `infra/reference-library/` MUST hold the systemd user units and
  the app shortcut, and one command, `install.sh`, MUST install them and
  start the socket.
- **FR-002**: The socket MUST listen on its own loopback port, not 23119; the
  first request MUST start `zotero --headless` and forward only after the
  local API answers; the services MUST stop when nothing needs them, about 10
  idle minutes after the last request.
- **FR-003**: When an open app already answers on 23119, no second copy MUST
  start and the request MUST reach the open app; when that app closes, the
  next request MUST start a background copy.
- **FR-010**: A gateway on its own loopback port MUST give Zotero the Host
  header it accepts, with Caddy pinned in `mise.toml` and `mise.lock`, a
  security review in `security/caddy-2.11.4.md`, its admin endpoint and
  automatic HTTPS off, and its state in a systemd runtime directory.
- **FR-004**: The shortcut MUST stop the background copy before it opens the
  app, and MUST keep every other field of the package's shortcut.
- **FR-005**: `plugins/work/mcp.json` MUST declare the connector as
  `reference-library`, started with `node`, with `ZOTERO_LOCAL_BASE_URL` at the
  socket's port and a neutral `ZOTERO_LOCAL_APP_NAME`; `plugins/work/package.json`
  and `package-lock.json` MUST pin version 1.0.1 and its dependency tree.
- **FR-006**: The user's Claude Code settings MUST deny, and the user's Codex
  entry MUST disable, `zotero_delete_items`, `zotero_delete_collection` and
  `zotero_empty_trash`; the block MUST be shown to work for the plugin's
  server.
- **FR-007**: The user's Codex entry MUST point at the same pinned copy and the
  socket's port.
- **FR-008**: `specs/040-reference-library/security/zotero-native-mcp-1.0.1.md`
  MUST review the connector before the pin, in the form of
  `specs/034-kebab-file-names/security/ls-lint-2.3.1.md`.
- **FR-009**: The plugin reference MUST list the new server, and
  `scripts/plugin-skills-test.ts` MUST expect it.

## Success Criteria *(mandatory)*

- **SC-001**: The live tests in `evidence/live-tests.md` show the on-demand
  start, the idle stop, the app-already-open case, the app closing, the app
  opened over the background copy, reads, and one write on a throwaway item
  that ends in Zotero's trash.
- **SC-002**: `npm run verify` prints VERIFIED.

## Assumptions

- The user's Zotero has the local API enabled and a persistent write key
  approved on 2026-09-11 (`~/.config/zotero-native-mcp/keys.json`, never read
  or printed by this work).
- Claude Code 2.1.286 reads a plugin's `.mcp.json`, not Agent Plugins'
  `mcp.json`; see the evidence for how the block was shown.
