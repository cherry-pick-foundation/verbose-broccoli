# Coordinator context data

Configuration contains standing-note paths, the XDG-relative state namespace and filename, worktree aliases and the three positive compaction thresholds. A path beginning with ~/ resolves under the current home; relative note paths resolve under the hook's repository root. XDG_STATE_HOME is honored only when absolute; otherwise ~/.local/state is used. Primary checkout verbose-broccoli maps to main; develop and feature worktree names remain distinct.

State is Markdown with one exact `Coordinator session: <client>/<session_id>` line and sections for decisions, holds/reasons, live owners, open questions and next steps. Only an explicitly assigned coordinator overwrites it. Prior state remains readable by its replacement. The hook reads but never writes it. Only the matching owner receives its body; other sessions receive conditional assigned-coordinator read/claim instructions, and narrow workers must not read it.

Hook input requires SessionStart, one supported source and a nonempty session_id, with transcript_path supplied by the client. A Codex session_meta payload id establishes transcript ownership. A Claude boundary's sessionId identifies its session; UUID deduplication avoids repeated preserved boundaries. Counts are recomputed from the named transcript and are never persisted.

Hook output is the clients' common SessionStart JSON context. A desktop notification contains the worktree and count only. Failure messages name missing sources but never repeat their content. No network or private-data output writer is added.
