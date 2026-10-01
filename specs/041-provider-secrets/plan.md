# Implementation Plan: Provider Keys from Bitwarden Secrets Manager

**Branch**: `feature/provider-secrets` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Pin bws through mise, then add `npm run secrets:refresh`, a short Node script
that lists the project's secrets with bws and writes the key files that
backfire and the other readers already use. Backfire's code does not change.

## Reuse

| Need | Existing tool | Own code |
| --- | --- | --- |
| Fetch secrets | `bws secret list <project> --output json` (Bitwarden, pinned by mise) | none |
| Key file format | backfire's `load_credential`: a regular file, mode 600, owned by the user, a line `<variable>=<key>` | writes that format |
| Format of bws's own `--output env` | `KEY="value"` with quotes, no escaping, non-shell-safe names commented out | not used: the quotes would become part of the key (`security/bws-2.1.0.md`, F-03) |
| Share one file between profiles | backfire's `credential_file` | not used: each profile already names its file and variable, so sharing removes no code (`cloudflare.env` already holds two variables) |
| JSON, files, processes | Node's `JSON`, `fs`, `child_process` | glue only |
| Offline tests | `node:test`, a fake `bws` shell script | the fake and the cases |
| Tool pin | mise `aqua:bitwarden/sdk-sm` | one line in `mise.toml`, the lock, `orca.yaml`'s install list |

## Constitution Check

- Reuse order: bws and backfire's file format are reused; the script is
  integration glue (about 100 lines).
- No secret value or token in the repository, in arguments, in output or in
  Linear: the operator configuration and the token file sit outside it.

## Project Structure

```text
mise.toml, mise.lock, orca.yaml        bws 2.1.0 pin
scripts/secrets-refresh.ts             the refresh command
scripts/secrets-refresh-test.ts        offline tests with a fake bws
package.json, turbo.json, tsconfig.json   the task and its test
docs/backfire.md, docs/architecture.md    where key files are described
docs/reference/commands.md             regenerated task table
specs/041-provider-secrets/            these records and the security review
```

## Operator configuration (outside the repository)

`$XDG_CONFIG_HOME/verbose-broccoli/secrets.json`:
`{"project": "<project id>", "files": {"hive.env": ["HIVE_API_KEY"], ...}}`.
A secret's name is the variable in the file.

## Workers

Main (Claude Code) implements. The security review is main's own read of the
source; the develop merge reviewer's agent, model and effort come from the
`model-choice` skill with Jev-only judgments, from a provider other than
Claude Code, and reads code only, never keys.
