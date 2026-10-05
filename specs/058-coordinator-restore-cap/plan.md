# Plan

Select maxContextBytes by the already validated client in the existing configuration. Keep the existing byte measurement and output paths. Validate each selected bound against its client ceiling.

Extend the existing observable hook-output test, without a new harness or dependency. Compare Codex's hook token limit against ceil(bytes / 4), and assert its unchanged exact value. Cached Codex rust-v0.160.0 implements this count in codex-rs/utils/string/src/truncate.rs:71 and uses it in codex-rs/hooks/src/output_spill.rs:70; 200,000 bytes is 50,000 approximate tokens.

Workflow task: coordinator-restore-cap. Comparison base: 568c97da88efa755e07c4c4e62e724b0963e9272. Preserve the existing exact-file workflow plan. Focused checks precede develop's full verification slot and independent review. Develop owns commits, integration and final ledger ticks.
