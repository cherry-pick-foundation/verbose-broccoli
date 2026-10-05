# Codex coordinator restore cap

Issue: CHE-91

Codex coordinators must receive complete standing notes and owned state when the full restore is at most 200,000 UTF-8 bytes. Claude keeps its 65,536-byte bound and existing output behavior. Above either bound, preserve the complete re-read guidance and source paths.

Keep owner matching, narrow-worker isolation, unavailable-state handling, compaction counting, restart thresholds and notifications. Keep Codex additionalContextLimit exactly 65,536 approximate tokens. Do not change hooks, global settings, private sources, dependencies or the constitution.

Acceptance uses synthetic sources through the existing Node hook harness: roughly 115,000-byte Codex restore with start/middle/end and state markers; exact client boundaries; above-bound fallback; multibyte sizing; leading guidance; existing isolation and threshold cases. The large restore must fail with the previous hook and pass with the correction.
