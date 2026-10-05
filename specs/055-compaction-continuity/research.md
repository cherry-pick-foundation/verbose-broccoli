# Hook capability evidence

Checked on 2026-10-05 before implementation. `codex --version` returns 0.160.0; `claude --version` returns 2.1.289. No external client activation was performed.

## Context delivery

Decision: use the common `hookSpecificOutput` shape with `hookEventName: SessionStart` and `additionalContext`. Both clients accept the four requested sources. Codex supports a configurable per-handler approximate token limit; its default is 2,500 and larger output spills to temporary storage. Set a positive limit above the script's bounded output. If context exceeds the bound, require full reads of the original notes/state instead of partial injection.

Sources: [OpenAI Hooks](https://learn.chatgpt.com/docs/hooks), sections Common input fields, Large hook output and SessionStart; [Claude Hooks](https://code.claude.com/docs/en/hooks#sessionstart), input and decision control. Codex's version-matched source confirms the input and output in `codex-rs/hooks/src/events/session_start.rs:45` and `:264`, and the limit in `codex-rs/hooks/src/output_spill.rs:12` and `:70`, at tag `rust-v0.160.0` in [openai/codex](https://github.com/openai/codex/tree/rust-v0.160.0).

The installed Claude executable contains a system message constructor with subtype `compact_boundary` and compactMetadata. The source excerpt was located read-only by searching the installed binary for `subtype:"compact_boundary"`; no user conversation was used. Its standard hook context shape is documented above. The implementation caps context and retains the complete-source fallback rather than assuming unlimited client output.

## Transcript counts

Decision: count Codex top-level `compacted` items, not context_compacted event messages. At the same tag, `codex-rs/history/src/rollout_payload.rs:32` declares snake_case tagged records, including SessionMeta and Compacted. `codex-rs/core/src/session/mod.rs:4190` persists Compacted before queueing a compact SessionStart at `:4214`. Count only a matching session_meta owner. Claude counts unique system/compact_boundary UUIDs with matching sessionId. Missing or damaged transcripts produce an unknown-count warning. The transcript layouts are client implementation details and may change on updates; this is a supported-version limit, not a stable protocol claim.

## Coordinator boundary

Decision: record `Coordinator session: <client>/<session_id>` in the single mutable state. Develop explicitly approved this on 2026-10-05: claiming it is a coordinator action; hooks never claim or write it for workers. Startup may show previous state with coordinator-only instructions; thresholds require the matching owner. This avoids a registry, launch wrapper or inferred role from a worktree name.

## Reuse and scope

No upstream implementation, dependency or tool is adopted. Node's filesystem, readline, path and child-process modules connect the clients' native hooks to installed desktop notifications. The state file is owned by the coordinator, not by the hook. Immutable completed results keep the normal attempt storage. Spec Kit's existing template and agent-context extensions are reused.
