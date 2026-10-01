# Tasks

The develop orchestrator owns final ledger ticks. Unticked entries may have
work in progress; the coverage and verification records carry the evidence.

- [ ] T001 Compare approved source entries with HEAD and obtain the four user decisions.
  Feature orchestrator: Codex gpt-6.1-sol xhigh, selected through OpenRouter
  typesafe/jev-1.13: agent 0.55/confidence 0.44, model 0.81/0.78, effort
  0.82/0.79. Estimated difficulty: difficult. These are dispatch evidence,
  not proof of correctness. Startup usage: Codex weekly 68% used until
  2026-10-03T17:28:48Z; Claude session 16%, weekly 55%.
- [ ] T002 Migrate resolved root and plugin judgment rules and apply user decisions.
- [ ] T003 Correct native launch guidance, deleted pointers and active ownership consumers.
- [ ] T004 Verify source coverage, consumers and the integrated latest-develop tree.
- [ ] T005 Obtain a fresh other-provider final review and request the serialized finish slot.
  Review choice: OpenRouter typesafe/jev-1.13 selected Claude Code
  0.95/confidence 0.94, the live fable alias 0.54/0.42 and high effort
  0.31/0.19. It selected a 30-minute budget 0.65/0.58; the budget is a
  reporting checkpoint, not acceptance or authority to kill a live reviewer.
  These four calls did not escape; their probabilities do not prove quality.
  Live Claude usage at choice: session 23% until 2026-10-01T18:50:00Z,
  weekly 56% and Fable-only 8% until 2026-10-05T23:00:00Z.
  The alias launch answered with Opus despite its receipt; this review is not
  final acceptance. Renewed Jev choice: Claude Code 0.93/0.91,
  claude-sonnet-5-5 0.85/0.81, xhigh 0.30/0.19 and 30 minutes 0.49/0.38.
  All four new calls did not escape. Live usage: session 32%, weekly 57%,
  Fable-only 8%, with the same reset times above. Verify actual response model;
  that field does not prove effort. Probabilities do not prove correctness.

2026-10-02: the user resumed CHE-80, superseding the older CHE-74 start gate.
CHE-74's final develop result was integrated as `18e77dc` before final checks.

## Paused restart handoff, 2026-10-02

Historical checkpoint: resumed by fresh Dispatch `ctx_8d40ee3d2ce3` after the
restart. The final main/main and develop/develop layout is confirmed.

CHE-80 is unfinished and fully paused for Orca's layout restart. The user moved
the main and develop coordinator roles to one Claude session. No child worker,
batch job, ask wait, heartbeat or restart loop is active; nothing could not stop.
Do no task work until that coordinator sends Resume all. Closing Orca ends this
structured session; do not reuse its old Dispatch authority for a new session.

Outgoing agent: Codex gpt-6.1-sol xhigh. Codex session ID:
`01a0f843-26d8-7be3-94dd-90a34f871e2c`; structured session
`f8f33cc7-28fa-41d9-a7e3-92a753fce2bf`. Parent Run `run_8b222073b123`,
Task `task_5d600b95f822`, Dispatch `ctx_27f9101d5cab`; own child-review Run
`run_e0133a7c78cb`. No worker_done or final approval has been sent.

Last checked HEAD is `e371b73d97e75a6ad30865138bbf5be571febc0e`, containing
develop `965afb9938078d8121306e44f680b24b8ff5970e`. Uncommitted owned files:
all 48 `plugins/{code,work,chat}/skills/*/SKILL.md` entrypoints (one relative
plugin-rule pointer each), model-choice's `references/model-choice.md`,
`scripts/plugin-skills-test.ts`, and this feature's `coverage.md`, `plan.md`,
`tasks.md` and `verification.md`. The initial implementation is already
committed. Preserve all ignored `.local/che-80-*` evidence and the copied
`.local/backfire_call.py` helper. Last measured diff: 65 files, 918 insertions
and 46 deletions, before this handoff; remeasure after resumption.

Full verification of the pointer/full-model-ID source passed exclusively:
`3K6aGtfFbMH7OBCGjKaxBdjEBPZ`, 42 successful, five cached, zero failed,
exit 0. The later record edits and this handoff are not yet verified or
committed. Focused packaging tests passed 3/3 after failing on the missing
pointer before the fix. Correct configured lint, names and document checks
passed; 48-pointer byte preservation passed. Details are in verification.md.

First reviewer `task_8d0e161d0495` / `ctx_3734a0a863b4` settled and was
released; its ignored report is `.local/che-80-final-review.md`. It ran Opus
after Orca lost the fable alias and does not count as final review. Its useful
source findings drove the current fixes. No new reviewer has started. New
Jev choices and English-only inputs/results are `.local/che-80-renewed-review-*`:
Claude claude-sonnet-5-5 xhigh, 30-minute reporting checkpoint, recorded above.
Recheck current usage, launch eligibility and implementer providers on resume.
Use native worker-start with full IDs only; check actual assistant message.model
and report effort evidence separately. No alias retry or terminal workaround.

The document-batch ask returned: do not send all 28 regenerated requests;
retain previous dispositions only where both unit text and evidence content
are byte-identical, proved by hashes. Run one bounded Jev verification of new
pointer/full-model-ID claims and any units with changed evidence. Record the
exception, hashes and call count. Unit records alone were identical (331),
but evidence-content hashes have not been compared. Inputs are
`.local/che-80-final-doc-requests.json` and
`.local/che-80-native-id-doc-requests.json`; check actual tool limits and ask the
new coordinator if changed evidence cannot fit the authorized bounded call.
Seventeen Jev calls have succeeded so far. Shared-operations ownership drift
was reported outside writable scope; do not edit shared preferences here.

Next: after Resume all, reread current shared operations and confirm checkout
branches and Orca authority. The planned final layout is main/main with .git
and develop/develop; the last observed temporary layout was reversed. Resolve
the hash-bounded document step, update/read the records, run workflow, inspect
the complete diff and commit with Conventional Commits and task trailers.
Integrate latest develop, verify the final committed tree with the CPU wrapper
and one full verify at a time, then obtain a fresh other-provider final review.
If the measured feature diff reaches 1,000 lines, record the split decision.
Keep the browser off limits unless the coordinator releases CHE-69's slot.
Only after those gates request the serialized finish slot; the coordinator
owns Linear, final ledger ticks and integration. Never self-approve.
