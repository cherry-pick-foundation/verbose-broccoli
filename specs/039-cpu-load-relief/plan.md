# Implementation Plan: CPU Load Relief

**Branch**: `feature/cpu-load-relief` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Turn on Turborepo's local cache for every verification task whose inputs can
be declared, declare the inputs Turborepo does not see by itself, and keep
the rest uncached with the reason in the task's description
([research.md](research.md)). Review System76's scheduler for the user's
install decision.

## Reuse

| Need | Existing tool | Own code |
| --- | --- | --- |
| Cache results, share them across worktrees | Turborepo 2.11.5 local cache (default shared worktree cache) | none |
| Hash repository files and workspace dependencies | Turborepo's default inputs and Python workspace support | `inputs` for `doc-regions#test` |
| Hash installed environments | `globalDependencies` over npm's hidden lockfiles and installed `METADATA` | config lines |
| Hash programs outside the repository | `globalEnv` | `scripts/toolchain.sh` (one hash over version commands) |
| Prove invalidation | `turbo run --dry=json`, Node's test runner | `scripts/turbo-cache-test.ts` |
| Keep batch work off the performance cores | `systemd-run --user --scope`, `nice`, `taskset` (develop session's rule) | none |

## Constitution Check

- Reuse order: Turborepo's own cache and inputs; local code only for the
  fingerprint that Turborepo has no input for, and for the tests.
- Verification still passes only on the exit status and the same run's
  summary.
- Third-party tools get a security review before install (System76's
  scheduler); no agent runs sudo.

## Project Structure

```text
turbo.json                     cache, inputs, globalDependencies, globalEnv
package.json                   turborepo script passes the fingerprint; test:turbo-cache
scripts/toolchain.sh           the fingerprint
scripts/turbo-cache-test.ts    invalidation tests
tsconfig.json                  type-checks the new test
.gitignore                     /.turbo/
docs/                          command reference and architecture note
specs/039-cpu-load-relief/     these records and security/
```

## Workers

Main (Claude Code) implements the caching change. A Codex worker writes the
scheduler's security review; the user chose its model after backfire's
judgment failed. The develop merge reviewer comes from a provider other than
Claude Code, chosen with the `model-choice` skill; `tasks.md` names each.
