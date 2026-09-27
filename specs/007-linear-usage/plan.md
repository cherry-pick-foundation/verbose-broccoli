# Implementation Plan: Linear Usage Through Orca

**Branch**: `feature/linear-usage` | **Date**: 2026-09-28 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/007-linear-usage/spec.md`

## Summary

Carry each Linear rule in the place agents read when it applies, with as
little repository code as possible (research R1):

- The root `AGENTS.md` gains the two lines the user approved under "Records":
  the privacy rule, and the rule that only the main agent writes to Linear
  (one issue per feature or bug, no sub-issues, search first; others report
  through Orca messages).
- A Spec Kit preset, `linear-issue`, appends the issue line to the spec
  template through Spec Kit's own template stack, so every new spec asks for
  the issue ID and says how to find or link it (R2).
- `deno task workflow` prints one more instruction in every mode: the main
  agent's completion order (record, In Review, merge review, finish, Done with
  one completion comment) (R3).
- `docs/architecture.md` gains a "Linear" section that explains the team,
  labels, issue life cycle and where each rule lives (R4).
- Outside the repository, only the auto-archive period is left for the user
  to set in Linear's UI (R5); the labels exist and Codex's cached plugin was
  removed.

## Technical Context

**Language/Version**: TypeScript on Deno 2.9.6 for the one line in
`scripts/workflow.ts` and its test; Markdown and YAML for the rest.

**Primary Dependencies**: Orca 1.4.215's `orca linear` and `orca worktree`
commands (used by agents, not by repository code); the Spec Kit CLI 1.0.12
pinned in `tools/spec-kit/uv.lock` for installing the preset.

**Storage**: Linear (hosted, team `CHE`) for issues; the repository's Spec Kit
records for decisions. No new local storage.

**Testing**: `scripts/workflow_test.ts` (`deno task test:workflow`) for the
printed instruction; `specify preset resolve spec-template` and
`.specify/scripts/bash/resolve-template.sh spec-template` for the preset;
`deno task verify` for the whole change.

**Target Platform**: The development machine: Claude Code and Codex sessions
inside Orca terminals.

**Project Type**: Repository working agreement: agent instructions,
configuration and one printed instruction.

**Performance Goals**: None.

**Constraints**: No new integration besides Orca (decision 1); no Linear write
by repository code or hooks; `AGENTS.md` only for the two approved lines;
nothing private in Linear, in fixtures or in reports.

**Scale/Scope**: About 12 active issues on 2026-09-28 against the free plan's
250; one team; four features in flight.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Status |
| --- | --- |
| I. Proven dependencies | PASS. No new dependency; Spec Kit's preset command is part of the pinned CLI and was probed in a scratch copy (R2). |
| II. Working capabilities | PASS. The preset is checked by resolving the template; the workflow line by its test; the Linear flow by this feature's own finish (SC-002). |
| III. Sources and ownership | PASS. Linear holds to-do entries only; decisions stay in the repository's records (FR-007). Private data never enters Linear (FR-011). |
| IV. Current needs | PASS. Only the user's 2026-09-27 decisions are implemented. |
| V. Observable acceptance | PASS. Quickstart checks each success criterion; SC-003's walkthrough is recorded in `tasks.md`. |
| VI. Wiki layers | PASS. Issue originals never enter a Wiki's `raw/` (FR-007). |
| VII. One owner, minimum implementation | PASS. Each rule has one carrier (R1 table); the only code is one instruction string and its test. |
| VIII. No new exceptions | PASS. |
| IX. Layout | PASS. No plugin or package change; the preset lives under `.specify/`, the tool line under `scripts/`. |
| Product and Data Boundaries | PASS. Linear is an existing user-selected service; no new service is added. |
| Workflow and external messages | PASS. The main agent's Linear writes named in the spec's Assumptions are authorized by the user's decisions; hooks and scripts make none. |
| `AGENTS.md` only for judgment rules | PASS. Both lines need judgment each time and were approved by the user. |

Re-check after design: unchanged; no violations.

## Project Structure

### Documentation (this feature)

```text
specs/007-linear-usage/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── linear-lifecycle.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
AGENTS.md                                   # two lines under "Records"
.specify/presets/.registry                  # written by `specify preset add`
.specify/presets/linear-issue/preset.yml    # append layer for spec-template
.specify/presets/linear-issue/templates/spec-template.md
scripts/workflow.ts                         # one instruction in every mode
scripts/workflow_test.ts                    # test for that instruction
docs/architecture.md                        # "Linear" section; preset in the Spec Kit section
```

**Structure Decision**: Nothing new is built. Each rule goes to an existing
carrier that agents already read at the right moment: `AGENTS.md` (always),
the spec template (when specifying), the workflow tool's output (before
completion) and the architecture document (for readers).

## Complexity Tracking

No violations to justify.
