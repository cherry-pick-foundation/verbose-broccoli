# Feature Specification: Model Choice with Backfire

**Feature Branch**: `feature/model-choice`

**Created**: 2026-09-30

**Status**: Draft

**Linear issue**: CHE-45

**Input**: Linear issue CHE-45, "Choose agents, models and efforts for Orca
workers and orchestrators with backfire, through a skill adapted from
TypeSafe's agent skill", and the develop session's task brief of 2026-09-30.
On 2026-09-30 the user abolished the fixed model rules for Orca workers and
orchestrators: Codex workers always on gpt-6-luna at max effort, security
reviews on Daybreak Blue, Claude Code as the only orchestrator and Codex as
the only implementer. From now on the agent (Codex, Claude Code or OMP), the
model and the reasoning effort of every worker and orchestrator are chosen per
task with backfire's judgment tools. The user kept one rule: a change's final
review comes from a different provider than the one that implemented it
(`AGENTS.md`, "Review"). On 2026-09-28 the user rejected a mapping table from
task difficulty or risk to a model; backfire weighs the facts each time.

The user chose the form: a new code-plugin skill adapted from TypeSafe's
upstream agent skill (<https://github.com/typesafe-ai/skills>,
`skills/typesafe-ai/SKILL.md` and its MIT `LICENSE`) at a pinned revision. The
model-choice content goes into a reference file of that skill, so the
upstream `SKILL.md` changes only in what discovery needs (name and
description) and a link to the reference. The source revision and every local
change are recorded in `upstream.json`, like
`plugins/code/skills/backfire/upstream.json`, with the notice entry that
`licenses/THIRD_PARTY_NOTICES.md` keeps for copied upstream text. Before the
upstream text is adopted, a read-only security review checks it for prompt
injection, instructions that override agent rules, and unsafe commands.

The same day the user added a scope: model choice reads real usage limits and
credit before choosing. The repository adopts the command-line tool of
CodexBar (<https://github.com/steipete/CodexBar>, MIT) unchanged, pinned like
its other host tools. `codexbar usage --format json` reports Codex's and
Claude's session and weekly limits, OpenRouter's credits and the Vercel AI
Gateway's balance; it has no Hive or Cloudflare provider. A read-only review
of the pinned release's source (where it sends credentials, telemetry or
auto-update, and what it writes to disk) comes first; the user approved
installing it on this laptop once that review passes. API keys reach it as
environment variables from `~/.config/verbose-broccoli/providers/*.env`,
never through CodexBar's own config file, and are never printed. CodexBar
replaces reading Codex's session logs. A separate feature, CHE-46, makes
backfire's own provider choice use CodexBar and depends on this install.

## Clarifications

### Session 2026-09-30

- Q: How should the security review's three findings in the upstream text be
  handled? → A: Three one-sentence fixes in `SKILL.md`, each recorded in
  `upstream.json`: the live docs become optional reference data, never
  instructions; before the state guidance, "Never send credentials. Send
  personal records only through a provider profile the user has approved for
  them (backfire's education mode pseudonymizes names at its exit), and keep
  the state minimal."; and "For a concrete implementation request within the
  user's scope".
- Q: Does `.codex/config.toml`'s fixed-role sentence go too? → A: Yes. Drop
  "You usually work here as an implementation worker, and the coordinator
  reviews your change." and keep "Do not approve your own change as final."
- Q: CodexBar's security review allows one provider per call; does that
  replace "one CodexBar call"? → A: Yes. "One call" was the develop session's
  wording, not the user's; the review's six limits stand (plan.md R7).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A coordinator chooses a worker's agent, model and effort (Priority: P1)

A coordinator (the develop session or a worktree orchestrator) is about to
start a worker, a reviewer or an orchestrator. It loads the code plugin's
`model-choice` skill, builds the candidates from the live catalogs, gives
backfire the evidence and the user's priorities, and starts the worker with
the chosen agent, model and effort passed explicitly.

**Why this priority**: This is the whole purpose of the change; without it the
abolished fixed rules leave no procedure.

**Independent Test**: Follow the skill's reference for one real task: the
candidates come from the catalogs it names, the `jev_decide` call succeeds
with 2 to 6 candidates, and the resulting `worker-start` command names the
agent, model and effort explicitly.

**Acceptance Scenarios**:

1. **Given** a task spec and the live catalogs, **When** the coordinator
   follows the reference, **Then** it lists candidates only from those
   catalogs and never from a written model list or difficulty table.
2. **Given** more than six plausible candidates, **When** the coordinator
   prepares the call, **Then** it narrows them first (for example with
   `jev_rerank`) or decides in two steps, so each `jev_decide` call has 2 to 6
   candidates.
3. **Given** backfire's answer, **When** it selects a candidate, **Then** the
   coordinator starts the worker with that agent, model and effort passed
   explicitly and reports the pick with its probability and confidence.
4. **Given** backfire escapes (`ask_user`, `investigate` or `none`), **When**
   the coordinator reads the answer, **Then** it asks the user instead of
   re-calling or picking a default.

---

### User Story 2 - A coordinator calls backfire when its MCP tools are not loaded (Priority: P2)

A coordinator session has no backfire MCP tools loaded. It calls backfire from
the repository package, without a marketplace or client installation.

**Why this priority**: Claude Code sessions in this repository load the plugin
skills but not always backfire's MCP server; the choice must still be
possible.

**Independent Test**: Run the reference's call instructions from a worktree
root with a two-candidate `jev_decide` argument file; backfire returns a
recommendation.

**Acceptance Scenarios**:

1. **Given** a session without backfire's MCP tools, **When** the coordinator
   follows the reference, **Then** it reaches `backfire serve-mcp` from
   `packages/backfire` and gets a `jev_decide` result.
2. **Given** an existing entry point that can call the tool, **When** the
   reference is written, **Then** it uses that entry point instead of new
   code.

---

### User Story 3 - The repository rules point to the skill (Priority: P2)

A reader of `AGENTS.md` or `.claude/rules/claude-code.md` finds how models are
chosen and finds no fixed coordinator or implementer role, while the
other-provider final review stays.

**Why this priority**: Rules that still name fixed roles would contradict the
user's decision.

**Independent Test**: Read both files: the model-choice line points to the
skill; `.claude/rules/claude-code.md` no longer says that Claude Code
coordinates and Codex implements, and it still requires a final review from a
different provider.

**Acceptance Scenarios**:

1. **Given** `AGENTS.md`, **When** a reader looks for how a worker's model is
   chosen, **Then** the line in "Workflow and verification" names the code
   plugin's `model-choice` skill.
2. **Given** `.claude/rules/claude-code.md`, **When** a reader looks for roles,
   **Then** it states no fixed role and keeps the other-provider review.

---

### User Story 4 - The upstream text is safe and traceable (Priority: P3)

A maintainer can see where the skill text came from, what changed locally,
under which license, and what the security review found.

**Why this priority**: Adopting third-party instructions needs provenance and
a safety check, but it does not change what coordinators do.

**Independent Test**: `upstream.json` names the repository, tag, revision,
path and the upstream file's SHA-256, and lists every local change; the
notice file has an entry; the security review's result is recorded in this
feature's records.

**Acceptance Scenarios**:

1. **Given** the adopted `SKILL.md`, **When** it is compared with the pinned
   upstream file, **Then** every difference appears in `upstream.json`'s
   `local_modifications`.
2. **Given** the security review, **When** it reports a finding, **Then** the
   finding is resolved in the adopted text or recorded with the reason it
   stands.

### Edge Cases

- A provider's balance is zero or its limit is used up: drop its candidates
  before the call; this is a plain fact check, not a threshold table.
- CodexBar cannot read a provider (no login, no key, an error): give that as
  evidence and do not guess the limit.
- A model's effort exceeds what Orca's `worker-start` catalog accepts: launch
  through the terminal path with the effort on the command line.
- Backfire fails (`invalid_response` or a transport error): report the failure
  and ask the user; do not fall back to a default model.
- Evidence for a model choice needs no credentials and normally no personal
  records; never send credentials, and send personal records only through a
  provider profile the user has approved for them.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The code plugin MUST gain a skill whose `SKILL.md` is TypeSafe's
  `skills/typesafe-ai/SKILL.md` at a pinned revision, changed only in the
  frontmatter `name` and `description`, a link to its reference file, and any
  change the security review requires.
- **FR-002**: The skill MUST carry the upstream `LICENSE` unchanged and an
  `upstream.json` in the form of `plugins/code/skills/backfire/upstream.json`,
  naming the source repository, tag, revision, path, the upstream
  `SKILL.md`'s SHA-256 and every local change.
- **FR-003**: `licenses/THIRD_PARTY_NOTICES.md` MUST gain an entry for the
  copied text with its source, revision, reused files, adaptations, copyright
  and license link.
- **FR-004**: A reference file of the skill MUST tell a coordinator to build
  the candidates from live catalogs: `~/.codex/models_cache.json` (models,
  supported efforts, descriptions), Claude Code's `--model` and `--effort`,
  OMP's models (`~/.omp/agent/models.yml`, `omp models`), and the launch
  limits that `~/.claude/rules/worker-dispatch.md` records (Orca's catalog caps
  some efforts; those go through the terminal path).
- **FR-005**: The reference MUST name the evidence to give backfire: the task
  spec, the remaining usage limits and credit with their reset times from
  `codexbar usage --format json` (FR-016), track records in this repository,
  and the user's standing priorities.
- **FR-006**: The reference MUST describe the call: `jev_decide` takes 2 to 6
  candidates, so narrow first (for example with `jev_rerank`) or decide in two
  steps, and it MUST point to the `jev_decide` and `jev_rerank` blocks of
  `plugins/code/skills/backfire/reference/tools.md`.
- **FR-007**: The reference MUST say how to act on the answer: pass the chosen
  agent, model and effort explicitly, never a default; ask the user when
  backfire escapes; report the pick and its confidence.
- **FR-008**: The reference MUST say how to call backfire when its MCP tools
  are not loaded, from the repository package and never through a
  marketplace or client installation, preferring an existing entry point over
  new code.
- **FR-009**: The reference MUST NOT contain a mapping from task difficulty or
  risk to a model, agent or effort, and MUST NOT fix a default model.
- **FR-010**: `AGENTS.md`'s model-choice line in "Workflow and verification"
  MUST point to the skill.
- **FR-011**: `.claude/rules/claude-code.md` MUST drop the fixed
  Claude-coordinates and Codex-implements roles and keep the other-provider
  final review.
- **FR-012**: A read-only security review of the upstream text, by a
  reviewer chosen with backfire, MUST precede adoption, with evidence for
  every finding.
- **FR-013**: `npm run verify` MUST pass on the merged result.
- **FR-014**: A read-only security review of CodexBar's pinned release
  source, by reviewers chosen with backfire, MUST pass before installation. It
  covers where credentials are read and sent, telemetry and auto-update,
  subprocesses, and what the tool writes to disk, with evidence for every
  finding.
- **FR-015**: CodexBar's command-line tool MUST be installed unchanged from
  its pinned Linux release after a checksum check, and pinned the way the
  repository pins its other host tools, so that `npm run doctor` fails when
  another version is installed.
- **FR-016**: The reference MUST read the limits with CodexBar, one call per
  provider under the security review's limits, passing `OPENROUTER_API_KEY`
  and `AI_GATEWAY_API_KEY` as environment variables from
  `~/.config/verbose-broccoli/providers/*.env`, each only to its own call,
  and never printing them; drop candidates whose provider balance is zero or
  whose limit is used up; and give the remaining limits and reset times to
  `jev_decide` as evidence.
- **FR-017**: `.codex/config.toml` MUST drop its fixed-role sentence and keep
  "Do not approve your own change as final."
- **FR-018**: The reference MUST tell a coordinator to keep its worktree's
  Orca board status in step with its Linear issue (`in-review` at In Review,
  `completed` right after the finish) and to create extra worktrees as
  children of its own.

### Key Entities

- **Candidate**: one agent, model and effort that a catalog offers, with the
  catalog's description and launch path.
- **Evidence**: facts for one choice: the task spec, the Codex weekly limit
  use, track records and the user's priorities.
- **Pick**: backfire's recommendation with its probabilities and confidence,
  or an escape.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Following the reference end to end, a coordinator starts one
  worker whose launch receipt shows the agent, model and effort that backfire
  chose.
- **SC-002**: `diff` between the adopted `SKILL.md` and the pinned upstream
  file shows only changes that `upstream.json` lists.
- **SC-003**: Neither `AGENTS.md` nor `.claude/rules/claude-code.md` names a
  fixed model, a fixed coordinator or a fixed implementer.
- **SC-004**: `npm run verify` reports VERIFIED on the result merged with
  `develop`.
- **SC-005**: `codexbar usage --format json`, run as the reference says,
  returns the limits of the providers it can read, and no API key appears in
  its output or in any file CodexBar writes.

## Assumptions

- The skill is named `model-choice` and lives in
  `plugins/code/skills/model-choice/`, with the reference at
  `references/model-choice.md`.
- Only the code plugin gets the skill; the work plugin's coordinators are the
  same Claude Code and Codex sessions that load the code plugin.
- `~/.claude/rules/worker-dispatch.md` is outside the repository and belongs
  to the develop session; this feature does not edit it and reports what in it
  should change.
- The user's standing priorities come from the user's own instructions and
  the repository rules; the skill does not invent them.
