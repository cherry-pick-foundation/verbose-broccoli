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
  2026-10-02: latest develop `c0b630b` is integrated; `b6d2f57` passed 47/47
  full-check tasks. Final integrated review and the finish slot remain.
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

2026-10-02: a fresh Dispatch resumed the paused feature after the layout restart.
The pointer and native-model fixes are committed in `b687dea`; latest develop
`c0b630b` is integrated. Review corrections, committed-tip verification and a
fresh integrated-tree review remain; evidence is in verification.md.
