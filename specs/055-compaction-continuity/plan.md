# Implementation Plan: Coordinator compaction continuity

**Branch**: `feature/compaction-continuity` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

## Summary

Use one Node standard-library hook for both clients. Restore complete standing notes and the worktree's mutable state, with an explicit full re-read fallback for oversized output. Only the client/session owner recorded in that state receives threshold instructions and notifications. The hook never writes state or starts another client.

## Technical Context

**Language/Version**: TypeScript on the existing Node 24 toolchain.
**Primary Dependencies**: Node standard library; existing Codex and Claude Code hooks; installed Linux notify-send. No adoption or runtime changes.
**Storage**: One coordinator-owned mutable Markdown state under the approved XDG state root; the hook reads only.
**Testing**: Node's built-in test runner and synthetic files/transcripts; notification executable replaced with a local test stub.
**Target Platform**: Linux Orca worktrees, Codex 0.160.0 and Claude Code 2.1.289.
**Project Type**: Repository automation.
**Performance Goals**: Hook completes within the configured timeout; stream the transcript rather than retain its conversation text.
**Constraints**: No external activation, global settings, memories override, new dependency, private source fixture, automatic restart or counter files.
**Scale/Scope**: Main, develop and feature coordinators; narrow workers in the same worktree remain nonowners.

## Constitution Check

Before and after design: pass. Standard-library glue connects existing client hooks and notifications. Synthetic acceptance checks isolation, missing sources, full content and unchanged originals. State remains private and mutable, completed evidence stays in immutable attempt storage. No upstream source is adopted. Spec Kit and Git hold feature records. Develop owns integration and final task ticks; Claude gives independent review of Codex implementation.

## Project Structure

`.config/coordinator-context.json` holds notes paths, state namespace/file, worktree aliases and thresholds. `scripts/coordinator-context.ts` reads hook stdin and emits the common SessionStart JSON shape. `scripts/coordinator-context-test.ts` supplies synthetic acceptance. `.codex/hooks.json` and `.claude/settings.json` call the hook for startup/resume/clear/compact; existing handlers remain intact. `AGENTS.md` holds only the main/develop message judgment rule. `turbo.json`, `package.json` and the owned generated command table register verification. Spec Kit's adopted agent-context hook owns `.claude/rules/current-plan.md`.

## Design

Use `Coordinator session: <client>/<session_id>` as a single exact owner line in state. Startup restores prior state and instructs only an assigned coordinator to overwrite that line with its current owner, retaining decisions and owners. No automatic claim occurs. Every session reads the notes, but a narrow worker is explicitly forbidden from claiming or editing coordinator state. Compaction thresholds operate only for the matching owner.

Codex counts top-level `compacted` records after the matching `session_meta` header. Claude counts unique system/compact_boundary UUIDs bearing the input sessionId. Do not count text mentions, completion events or other sessions. Resume retains that transcript's count; new/clear sessions use their new transcript. Missing or malformed transcripts report unknown counts, never zero as evidence. The source-specific record layout is an installed-client compatibility limit.

Full injection is preferred. Codex's handler limit is set above the script's context byte cap, so supported outputs do not spill. If sources grow beyond the cap, output exact paths and a required full re-read, in chunks with no omitted middle. Missing files are named. Notification failure leaves the save-state instruction visible. Notifications contain only the worktree identifier and count, never notes, state or transcript contents.

## Execution and Verification

Run the smallest hook/transcript tests, then type/style/graph checks, required document prepare/audit and one full verification in a develop-granted slot. Batch commands use the approved low-priority CPU scope. Commit the feature record, request In Review through develop, obtain a fresh native Claude built-in /code-review, resolve findings, then align current develop and create the content-free review-record tip. Develop alone finishes the feature.

Initial estimate: source 50–70 lines, test 60, hook 20 and rule 3–5. This is advisory; report actual size and review splitting only under the existing 1,000-line rule.

## Acceptance record (2026-10-05)

Develop f868ec043769c03d62ecfe8e45a6c0393524944e was merged at 89c2dee. The sole generated-table conflict was aborted, reported and retried with develop's explicit permission to regenerate that region from both merged manifests. The foreign generated Codex discovery block remains unstaged.

Full verification attempt 1 stopped on a missing newly merged Python package. The locked workspace sync and installed privacy child corrected the environment; the affected 42-case session-selection check passed. Attempt 2 exited zero with workflow phase VERIFIED and a same-run Turbo summary: 46/46 successful, 0 cached, 5m54.467s. Hook acceptance covers both formats, complete notes/state, all four sources, thresholds, replacement, narrow workers, missing/damaged sources and notification failure. Hook processes have no filesystem write permission. Scoped lint and TypeScript passed; mechanical document checks report no problems.

Current document preparation produced 11 gated Jev calls, retained without repeats: 333 units, 55 review flags. The 52 low-subject flags do not establish drift. The three related flags concern unchanged connector/discovery guidance; retain canonical documentation because the foreign checkout-local block predates privacy and is not the canonical generator. MemoryLint's 21 existing constitution placement warnings are report-only. Disposition and receipts are in the current attempt directory. Tool-reported document usage: 211,146 input and 59,673 output tokens.

Owned size before this record: 161 source lines, 261 test lines, 26 hook lines and three rule sentences; the whole feature is below the existing 1,000-line split-review threshold. The complexity-only diff inspection found no speculative abstraction or added dependency. No source cut is required for that scope.

Evidence: ~/.local/state/verbose-broccoli/workspaces/feature-compaction-continuity/compaction-continuity/ctx_14adf1f5da09/acceptance-after-privacy-01/ contains document requests, receipts and disposition; acceptance-after-privacy-02/ contains the successful verification log and immutable Turbo summary. Live compacted model responses and desktop display were not exercised; capability/source evidence and synthetic notification checks are recorded accurately. Client activation remains a user-owned rollout after integration.

Independent native Claude built-in review remains pending. The saved choice is claude-sonnet-5-5 medium (probability 0.88, confidence 0.85). Develop owns final ticks, Linear and finish; this record is not the implementer's final approval.
