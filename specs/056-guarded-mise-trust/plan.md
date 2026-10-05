# Implementation Plan: Guarded mise trust

**Branch**: `feature/guarded-mise-trust` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

## Summary

Use the existing Lefthook configuration and native npm-installed binary. Post-checkout supplies old/new revisions and its branch/file flag; post-merge compares ORIG_HEAD with the current working file, including squash merges whose HEAD has not moved. One shell script checks the config changed for branch/merge events, requires a regular non-symlink file, resolves `refs/heads/develop:.config/mise.toml`, and compares that Git blob ID with `git hash-object --no-filters` over the current bytes before invoking `mise trust .config/mise.toml`.

## Technical Context

POSIX shell and existing Git/mise/Lefthook 2.1.15; Node's existing test harness runs synthetic acceptance. No new dependencies or durable storage. Native launcher derives OS/architecture using the same uname/tr/sed mapping as Lefthook's installed hook template; current Linux is the acceptance platform. Existing commit commands remain intact. The supported folded shell launcher skips only checkout/merge when its native binary is absent, leaving commits fail closed and new-worktree setup usable.

## Constitution Check

Reuse native tools and supported upstream configuration; locally owned implementation is narrow integration glue. No private fixtures, persistent data writer, plugin/package changes or constitution amendment. Positive, negative and runtime-boundary checks belong in the existing commit-hook test harness. Develop owns serialized verification, independent-review integration and shared installation.

## Project Structure

Change `.config/lefthook.yml`, add `scripts/guarded-mise-trust.sh`, and extend `scripts/commit-msg-test.ts`. Feature records live in this directory; the agent-context extension updates `.claude/rules/current-plan.md` through its supported command.

## Research and Design

The old shared commit-msg hook selects `node_modules/lefthook/bin/index.js` before native fallback, which requires Node. `node_modules/lefthook/get-exe.js` selects the installed native platform package. Lefthook's supported `lefthook` option accepts Bourne-shell commands: <https://lefthook.dev/configuration/lefthook/>. Its installer creates shared Git hooks while preserving supported existing-hook handling; do not hand-edit those hooks. The pre-change shared-hook inventory included only commit-msg and samples.

Comparing raw Git blob hashes reuses Git rather than a temporary-file lifecycle and avoids filters changing the comparison. Missing references and event-diff errors skip trust. One script serves both events; no broad trust guard or resume changes.

## Consistency Analysis

FR-001–004 map to T001–T003; FR-005 to existing and added harness acceptance; FR-006 to T005. No unresolved required input. File-only checkout cannot detect prior bytes; it idempotently renews identical reviewed content without tracking state. Supported `mise trust --show` reports current trust, not an event's old bytes. An isolated real mise smoke confirmed paranoid-mode trust success and differing-byte refusal. The approved estimate is about 15–25 implementation lines plus a regression, not a cap.
