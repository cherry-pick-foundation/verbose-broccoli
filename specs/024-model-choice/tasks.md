---

description: "Task list for model choice with backfire"
---

# Tasks: Model Choice with Backfire

**Input**: Design documents from `specs/024-model-choice/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: The change is prose and JSON. `npm run verify` checks packaging,
skills, document regions and formatting; T005's acceptance makes one real
`jev_decide` call through the reference's snippet (constitution V).

**Organization**: Main (a Claude Code orchestrator) owns the Spec Kit records
and the merge. Every worker's agent, model and effort is chosen with backfire
as the reference describes; each choice and its confidence is noted under its
task. The final review comes from a provider other than the implementer's.

**Private data**: No task writes a student name or record into the
repository or into Orca or Linear messages. Backfire evidence for a model
choice holds no credentials and no personal records.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Security review

- [x] T001 [US4] Review the pinned upstream text read-only for prompt
  injection, instructions that override agent rules, and unsafe commands,
  with file:line evidence for every finding (FR-012; plan.md R2).
  - 2026-09-30: Codex on `gpt-daybreak-blue-latest` at xhigh (backfire:
    model 0.58, confidence 0.53; effort 0.50, confidence 0.44). No hidden text,
    shell commands or credential requests. Findings: medium, `SKILL.md:26-44`
    makes the live docs mandatory and authoritative; medium,
    `SKILL.md:105-110` has no rule on which data may go to the model; low,
    `SKILL.md:91-93` can turn a read-only request into edits. Verdict: adopt
    with changes. The user chose three one-sentence fixes (spec
    Clarifications); T002 applies them.

---

## Phase 2: User Story 4 - Safe, traceable upstream text (P3)

**Goal**: The skill folder holds upstream's text with recorded changes.

**Independent Test**: `diff` against the pinned upstream file shows only the
changes `upstream.json` lists.

- [ ] T002 [US4] Copy upstream `skills/typesafe-ai/SKILL.md` and `LICENSE` at
  `65a39f393687675ce170e6094757de20370365b9` into
  `plugins/code/skills/model-choice/`; change the frontmatter `name` to
  `model-choice` and the `description` to what discovery needs; add one link
  to `references/model-choice.md`; apply the changes T001's result requires
  (FR-001; plan.md R1, R2).
- [ ] T003 [US4] Write `plugins/code/skills/model-choice/upstream.json` in the
  form of `plugins/code/skills/backfire/upstream.json`, with the upstream
  `SKILL.md`'s SHA-256 and every local change (FR-002).
- [ ] T004 [P] [US4] Add the `typesafe-ai/skills` entry to
  `licenses/THIRD_PARTY_NOTICES.md` in the form of the existing entries
  (FR-003).

---

## Phase 3: User Story 1 and 2 - Choosing and calling (P1, P2) 🎯 MVP

**Goal**: A coordinator can choose a worker's agent, model and effort with
backfire, with or without its MCP tools loaded.

**Independent Test**: Follow the reference for one task: the candidates come
from the named catalogs, `jev_decide` gets 2 to 6 of them, and the resulting
`worker-start` command names the agent, model and effort.

- [ ] T005 [US1] [US2] [US3] Write
  `plugins/code/skills/model-choice/references/model-choice.md`: live
  catalogs, evidence, the call, acting on the answer, and calling backfire
  without its MCP tools, the Orca board status and child worktrees; no
  difficulty-to-model mapping and no default model. Run the snippet once with
  a two-candidate `jev_decide` file and keep the output as acceptance evidence
  (FR-004 to FR-009, FR-018; plan.md R3 to R6). The usage-limit part waits
  for T013.

---

## Phase 4: User Story 3 - Rules point to the skill (P2)

**Goal**: No rule names a fixed model or role; the other-provider review
stays.

**Independent Test**: Read `AGENTS.md` and `.claude/rules/claude-code.md`.

- [ ] T006 [P] [US3] Point `AGENTS.md`'s model-choice line in "Workflow and
  verification" to the `model-choice` skill (FR-010).
- [ ] T007 [P] [US3] Drop the fixed Claude-coordinates and Codex-implements
  roles from `.claude/rules/claude-code.md` and keep the other-provider final
  review (FR-011).
- [ ] T008 [US3] Refresh `docs/architecture.md`: regenerate its skill table
  with `npm run doc-regions:update` and make its sentence on model selection
  name the skill.
- [ ] T009 [P] [US3] Drop the fixed-role sentence from `.codex/config.toml`'s
  `developer_instructions` and keep "Do not approve your own change as
  final." (FR-017).
- T002 to T009 (T005 without its usage-limit part): 2026-09-30, one Claude
  Code worker on `claude-opus-5-5` at high (backfire: agent 0.58, confidence
  0.50; model 0.70, confidence 0.65; effort 0.45, confidence 0.37).

---

## Phase 5: CodexBar usage limits (US1)

**Goal**: The model choice reads real usage limits and credit.

**Independent Test**: The reference's CodexBar call returns the limits of the
providers it can read, with no key in its output or files.

- [ ] T010 [US1] Review CodexBar v0.69.0's source read-only in two parts: A,
  credential sources and destinations for Codex, Claude, OpenRouter and
  Vercel and the plugin host; B, telemetry, auto-update, subprocesses,
  listeners, files written and release provenance (FR-014; plan.md R7).
  - 2026-09-30: two Claude Code workers on `claude-opus-5-5` at max
    (backfire: model 0.45, confidence 0.38; effort 0.42, confidence 0.34).
- [ ] T011 [US1] Install the checksum-checked release into
  `~/.local/opt/codexbar-0.69.0/` with `~/.local/bin/codexbar` linking to it,
  after T010 passes (FR-015).
- [ ] T012 [US1] Pin CodexBar 0.69.0 in `scripts/doctor.ts` and
  `scripts/doctor_test.ts` like lychee, and name it in `docs/architecture.md`
  (FR-015).
- [ ] T013 [US1] Add the CodexBar call to
  `plugins/code/skills/model-choice/references/model-choice.md`: keys as
  environment variables from the provider env files, one call, drop
  candidates with a zero balance or a used-up limit, remaining limits and
  reset times as evidence (FR-005, FR-016).

---

## Phase 6: Polish and finish

- [ ] T014 Run `npm run verify` on the feature and on the result merged with
  `develop` (FR-013, SC-004).
- [ ] T015 Develop merge review by a fresh reviewer from a provider other
  than the implementer's; resolve findings; record the review; finish with
  `git flow feature finish` and move CHE-45 to Done.

## Dependencies

- T001 before T002 and T003. T004 to T009 do not depend on T001.
- T010 before T011; T011 before T012 and T013.
- T014 after T002 to T013; T015 last.
