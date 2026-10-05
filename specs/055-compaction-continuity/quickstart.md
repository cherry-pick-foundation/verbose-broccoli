# Validation and rollout

Run `npm run test:coordinator-context` under the approved low-priority CPU scope. It uses only synthetic notes, states and transcripts, and a notification stub. Expect both client formats, full middle/end markers, main/develop/feature thresholds, separate session ownership, replacement, missing state, startup/resume/clear and unchanged source bytes to pass.

Run the normal workflow with the feature's exact-file plan, document prepare/audit, then request develop's full verification slot and run `npm run verify`. Acceptance requires exit zero and the same run's summary. A source/schema check does not claim a live compacted model response was tested.

After integration, the user starts fresh main and develop sessions, then feature sessions after receiving develop. Hooks load at start. Only the assigned coordinator claims the single state by writing the hook-provided `Coordinator session: <client>/<session_id>` line while preserving decisions, holds, live owners, questions and next steps. A narrow worker leaves this file alone. At threshold the coordinator updates state, starts no new work and waits for the user to start a replacement. No hook restarts or kills clients.

The central paths and thresholds are in `.config/coordinator-context.json`. Global Codex memories stay off; this feature adds no project setting. No external activation is part of feature acceptance.
