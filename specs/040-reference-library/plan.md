# Implementation Plan: Reference Library for Agents

**Branch**: `feature/reference-library` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Zotero starts without a window on the first request and stops after about 10
idle minutes, through systemd user units. The work plugin declares the
`zotero-native-mcp` 1.0.1 connector against that socket, pinned by a lock
file; the clients block its delete tools.

## Reuse

| Need | Existing tool | Own code |
| --- | --- | --- |
| On-demand start, idle stop | systemd socket unit, `systemd-socket-proxyd --exit-idle-time`, `StopWhenUnneeded` | unit files |
| Run Zotero without a window | `zotero --headless` | none |
| Wait for the API | `curl --retry --retry-connrefused` in `ExecStartPost` | none |
| Host header Zotero accepts | Caddy 2.11.4 (mise, `reverse_proxy`, `header_up Host`) | a 10-line Caddyfile |
| Adopt an open app | `curl` and `socat` in one `sh -c` line of the app unit | that line |
| Replace the menu shortcut | the package's desktop file, one `Exec` changed | the Exec line |
| Install | `install`, `systemctl` | `install.sh` (about 10 lines) |
| Zotero tools for agents | `zotero-native-mcp` 1.0.1 (npm, MIT) | `mcp.json` entry |
| Block tools | Claude Code `permissions.deny`, Codex `disabled_tools` | settings entries |

The Host header problem was found in the first live test (see the spec); the
alternatives considered were an own Node proxy (more own code) and a connector
patch (breaks the lock pin). The user chose Caddy.

## Constitution Check

- Reuse order: upstream tools and systemd first; the glue is unit files, one
  shell line, a Caddyfile and an install script.
- Principle IX: files for the environment live in `infra/`; the plugin keeps
  only its manifest, lock and `mcp.json`.
- No student data goes into the library; the connector's key file is never
  read or copied.

## Project Structure

```text
infra/reference-library/            units, Caddyfile, shortcut, install.sh
plugins/work/mcp.json               the reference-library server
plugins/work/package.json, package-lock.json   the pin
.claude/settings.json               deny rules (also in the user's settings)
mise.toml, mise.lock, orca.yaml, .github/workflows/check.yml   Caddy, npm install
scripts/reference-library-test.ts, scripts/plugin-skills-test.ts
docs/architecture.md, docs/reference/*   description, generated references
specs/040-reference-library/        these records, security/, evidence/
```

## Workers

Main (Claude Code) implements and runs the live tests, which need the user's
desktop. The develop merge reviewer's agent, model and effort come from the
`model-choice` skill with Jev-only judgments, from a provider other than
Claude Code; `tasks.md` names them.
