# Feature Specification: Clean Architecture Tool Collection

**Feature Branch**: `feature/clean-architecture`

**Created**: 2026-10-06

**Status**: Draft

**Linear issue**: none yet; the develop orchestrator creates it

**Input**: User decisions of 2026-10-06 (see [research](research.md#dated-user-decisions)):
retire the Agent Plugins implementation and build the capabilities as a
collection of tools that agents use (U-2026-10-06a); redesign the repository
as a Clean Architecture project of component packages with ports and adapters
inside each (U-2026-10-06c); let configuration send judgments to Jev or GLM
behind one judgment port (U-2026-10-06d).

## User Scenarios & Testing *(mandatory)*

The people and programs served are the user, who owns and maintains the
capabilities, and the coding agents (Claude Code and Codex) that use them in
this repository's worktrees.

### User Story 1 - Rules describe a tool collection, not plugins (Priority: P1)

The user reads the repository's rules (the constitution, the root
`AGENTS.md` and the architecture document) and finds the structure they
decided: capabilities delivered as skills, command-line tools and MCP
servers, each code-bearing capability in one component package with an
inward dependency rule, and no requirement for Agent Plugins roots, plugin
IDs or plugin manifests.

**Why this priority**: Every later change would otherwise break a written
rule. The first attempt failed because the retirement decision never reached
the records (see [research](research.md#lessons-from-the-first-attempt)).

**Independent Test**: Read the three rule documents after the change: no
sentence requires a plugin root, plugin ID or plugin manifest; each new
structural rule names its source; the constitution's version shows a breaking
change the user approved; verification passes.

**Acceptance Scenarios**:

1. **Given** the current constitution requires exactly three Agent Plugins
   roots, **When** the amendment lands, **Then** that principle is replaced by
   one describing component packages, skills, command-line tools and MCP
   servers, and the version records a breaking change with the user's approval.
2. **Given** a capability whose code is still held (see FR-016), **When** an
   agent reads the rules, **Then** the rules say where held code lives until it
   moves and what releases the hold.

---

### User Story 2 - Agents keep every capability without plugin packaging (Priority: P1)

An agent starts a fresh session in any worktree of this repository and finds
the same skills and MCP servers as before, now delivered without plugin
roots: each skill exists once, each MCP server is registered for both agents,
and the plugin manifests, the manifest schema check and the plugin
generation and distribution code are gone.

**Why this priority**: This is the user's retirement decision
(U-2026-10-06a) made real; Claude Code does not load Agent Plugins, so the
packaging adds work and no value.

**Independent Test**: Record the skill names and MCP server names a fresh
Claude Code session and a fresh Codex session report before the change;
repeat after the change; the lists match, contain no duplicate skill, and no
plugin manifest or plugin-only check remains in the repository.

**Acceptance Scenarios**:

1. **Given** a skill that two plugins carried as identical copies, **When**
   the change lands, **Then** one copy remains and both agents still find it.
2. **Given** the gated judgment server and the reference-library server,
   **When** a fresh session starts in a worktree, **Then** both servers are
   available to both agents, and the reference library's delete and
   empty-trash tools stay blocked.
3. **Given** a worktree that the old plugin generator prepared, **When** the
   generator is removed, **Then** its generated configuration is cleaned up
   without touching unrelated settings, and nothing outside the repository is
   changed without the user's approval.

---

### User Story 3 - Each capability is one checked component package (Priority: P2)

The user or an agent changes a capability and finds all of its code in one
component package: business rules without input or output, use cases with
the ports they need, adapters at the edge, and one composition root that
reads settings from the user's XDG folders. A change that breaks the
dependency rule fails verification before review.

**Why this priority**: This is the structure the user chose
(U-2026-10-06c); it makes each capability testable on its own and keeps
adapters from reaching past the domain (R-CA-01, R-CA-03).

**Independent Test**: For one migrated component, the behavior tests that
existed before the move pass afterwards with unchanged assertions; a fixture
that imports an adapter from the domain, or another component's private
module, makes verification fail.

**Acceptance Scenarios**:

1. **Given** a capability spread across a plugin folder and a script folder,
   **When** it migrates, **Then** its code, tests, package rules and README
   live in one component package and its command keeps the same behavior.
2. **Given** no settings file, **When** a component's command starts, **Then**
   it runs with safe defaults; if a credential it needs is missing, only that
   command fails, with a message naming the missing setting.
3. **Given** code another open feature branch is changing, **When** this
   feature plans its moves, **Then** that code stays where it is until the
   hold is released.

---

### User Story 4 - Judgments go to Jev or GLM by configuration (Priority: P2)

When a tool asks for a judgment, configuration decides whether Jev on
OpenRouter or GLM 5.3 Flash on Hive answers, through one judgment interface.
Student data always passes the education privacy gate, whichever model
answers, and choosing models for agent workers stays with Jev.

**Why this priority**: The user wants both models used heavily from the
first version (U-2026-10-06d). It depends on the privacy gate's reported
metadata bug being fixed and on a security review of the adapter that lets
GLM answer Jev-style requests.

**Independent Test**: The same judgment request runs once through each
backend in a counted live check and returns results that name their
provider and model; within verification, a fake backend answers instead; a
student-data request that would bypass the gate is refused.

**Acceptance Scenarios**:

1. **Given** configuration selects GLM, **When** a judgment takes 90 seconds,
   **Then** it completes instead of timing out.
2. **Given** a request containing a registered student's name, **When** it is
   sent to either backend, **Then** the gate replaces the name before the call
   and restores it in the answer.
3. **Given** a worker model choice, **When** it is judged, **Then** only Jev
   answers.

---

### Edge Cases

- Open feature branches (`lexical-semantics`, `korean-web-wiki`,
  `document-pdf-fidelity`, `exam-calendar`) change `plugins/work`,
  `packages/wiki-consistency`, `packages/jev-ultrafast` and shared files such
  as `docs/architecture.md`, `turbo.json` and `package.json`. This feature
  merges `develop` into itself when they land and never rebases.
- A replacement trial (U-2026-10-06e) succeeds or fails after this feature
  has started: code it would replace is not migrated first.
- Two skills with the same name come from different sources: only one may
  remain, and an upstream skill keeps its upstream name (U-2026-10-04a).
- An agent keeps an old installed plugin copy in its own user folders: it is
  reported to the user, not removed without approval.
- An XDG variable is set to a relative path: it is ignored and the default
  is used (R-OS-01).
- Hive answers 429 or 405, or OpenRouter credit runs out: the tool reports
  it; it does not switch to another paid provider on its own.
- The privacy gate is unavailable: student-data judgments are refused, not
  sent ungated.
- A migrated test needed an assertion change to pass: the move is not a pure
  refactoring and goes back for review (R-GG-13).

## Requirements *(mandatory)*

### Functional Requirements

**Delivery**

- **FR-001**: Capabilities MUST reach agents as Agent Skills, command-line
  tools, and MCP servers only where a tool needs a running process, a login
  or a filter in front of it; Agent Plugins packages and client-specific
  plugin formats MUST NOT be used (U-2026-10-06a, U-2026-10-06b).
- **FR-002**: Every skill MUST follow the Agent Skills specification and
  exist once in the repository; upstream skills keep their names and
  recorded provenance (R-UP-01, U-2026-10-04a).
- **FR-003**: Claude Code and Codex MUST find every skill and MCP server in
  each worktree of this repository after the documented setup, using
  [NEEDS CLARIFICATION: how skills and MCP servers reach the agents: rulesync
  (the approved trial), Vercel's `skills` plus Neon's `add-mcp`, or committed
  project discovery with no installer for this repository].
- **FR-004**: The reference library's destructive tools MUST stay blocked in
  both agents, and every judgment server registered for the agents MUST run
  behind the education privacy gate.
- **FR-005**: Plugin manifests, the plugin manifest schema check and the
  plugin generation and distribution code MUST be removed once the delivery
  in FR-003 replaces them; generated configuration in prepared worktrees MUST
  be cleaned up without touching unrelated settings.

**Structure**

- **FR-006**: Each capability with code MUST live in one component package
  containing a domain without input or output, an application layer with use
  cases and the ports they need, adapters, and one composition root
  (U-2026-10-06c, R-CA-01, R-CA-02, R-CA-04).
- **FR-007**: Verification MUST fail when inner code depends on outer code,
  when domain code performs input or output, or when one component imports
  another component's non-public modules (R-CA-01, R-CA-03, R-REPO-03).
- **FR-008**: A port MUST exist only where its adapter is slow, paid,
  nondeterministic or has two real implementations; no shared framework or
  package is created without a second real consumer (R-CA-05, R-GG-05,
  R-GG-14).
- **FR-009**: Each composition root MUST read settings from the
  `verbose-broccoli` namespace under the XDG configuration, state, cache and
  data folders, honoring absolute XDG variables and the specification's
  defaults, and MUST run with safe defaults when optional settings are
  missing (R-OS-01, R-OS-03, R-OS-08, R-OS-12).
- **FR-010**: A missing required credential or endpoint MUST stop only the
  capability that needs it, with a message naming the missing setting.
- **FR-011**: Each component package MUST carry its own `AGENTS.md` with its
  rules and a `README.md` saying what it holds and which entry points to use
  (R-REPO-12, R-GG-10).
- **FR-012**: Names of new files and folders MUST be kebab-case except where
  a language, tool or standard fixes the name (U-2026-09-30a).

**Behavior and process**

- **FR-013**: Each move MUST keep behavior: the component's existing behavior
  tests pass before and after with unchanged assertions; only import paths
  may change, and tests SHOULD reach the component through its public entry
  (U-2026-10-06f, R-GG-12, R-GG-13).
- **FR-014**: The work MUST be split into small slices, each reviewed by a
  provider other than the implementer's and finished into `develop` on its
  own, refactoring kept apart from behavior changes (U-2026-10-06f,
  R-GG-01, root `AGENTS.md` "Review").
- **FR-015**: The constitution change MUST be its own slice, its text shown
  to the user, and its breaking change approved by the user before it merges
  (U-2026-10-06f, constitution Governance).
- **FR-016**: Code that an open branch changes, that a replacement trial may
  replace, or that waits for the privacy gate's metadata bug MUST NOT move
  until that hold is released; the plan records each hold and its release
  condition (U-2026-10-06f).
- **FR-017**: Locally owned code MUST be measured before building and after
  each slice, and the measurement shown to the user (U-2026-10-06f, root
  `AGENTS.md` "Necessary work and code size"; a report, not a cap).
- **FR-018**: Adopting third-party code or tools for this feature MUST wait
  for a read-only security review with evidence for every finding (root
  `AGENTS.md` "Upstream adoption and attribution").

**Judgments**

- **FR-019**: Tools MUST request judgments through one judgment interface
  whose backend comes from configuration: Jev on OpenRouter
  (`typesafe/jev-1.13`) or GLM 5.3 Flash on Hive through a System
  One-compatible endpoint (U-2026-10-06d, R-CA-06). [NEEDS CLARIFICATION: how
  agents reach both backends: two gated servers side by side, or one server
  whose backend is set in configuration; and which backend is the default]
- **FR-020**: GLM calls MUST allow at least 300 seconds before timing out,
  and the limit MUST be a setting, not code (U-2026-10-06d, R-GG-15).
- **FR-021**: Every judgment that may contain student data MUST pass the
  education privacy gate, whichever backend answers; no route bypasses it.
- **FR-022**: Worker model-choice judgments MUST use Jev only.
- **FR-023**: Paid model calls MUST NOT run inside repository verification;
  live checks are separate runs whose call count is reported (R-GG-15,
  R-GG-16).
- **FR-024**: Tools that call a model directly MUST use [NEEDS
  CLARIFICATION: Pydantic AI from now on, or adopt it only when a tool first
  needs a direct model call] (U-2026-10-06b).

### Key Entities

- **Component package**: one capability's code, tests, rules and README,
  with its domain, application, adapters and composition root; installed
  and tested on its own.
- **Skill**: an Agent Skills folder of instructions, and optionally scripts,
  references and assets, that tells an agent when and how to use a tool.
- **Command-line tool**: a component's entry point that people and agents
  run; its output contract stays stable across moves.
- **MCP server**: a component's entry point for tools that need a running
  process, a login or a filter, registered for each agent.
- **Port**: an interface owned by the application layer for one purposeful
  conversation with the outside (R-CA-02).
- **Adapter**: an implementation of a port, or a driver of the application,
  for one technology.
- **Composition root**: the one place in a component that reads settings and
  wires adapters to use cases.
- **Settings**: values read from the XDG folders under `verbose-broccoli`,
  with defaults.
- **Judgment backend**: the model service answering judgments (Jev on
  OpenRouter or GLM on Hive), always behind the privacy gate for student
  data.
- **Hold**: a recorded reason a piece of code cannot move yet, with the
  condition that releases it.
- **Slice**: one reviewed and finished change into `develop`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In fresh Claude Code and Codex sessions, 100% of the skills and
  MCP servers available before the change are available after it, under the
  same names, with no duplicates.
- **SC-002**: After the rules slice, no rule document requires a plugin root,
  plugin ID or plugin manifest.
- **SC-003**: For every migrated component, 100% of its pre-move behavior
  tests pass after the move with unchanged assertions.
- **SC-004**: For each dependency rule, a deliberate violation makes
  verification fail in a single run.
- **SC-005**: Every structural decision in this specification and the plan
  cites a reference row or a dated user decision, and Jev finds each cited
  claim supported by the cited passage.
- **SC-006**: After each slice's finish, `develop` passes verification.
- **SC-007**: Once the judgment slice lands, the same request completes
  through each backend in a counted live check, and verification passes with
  no live model call.
- **SC-008**: The user sees the locally owned code measurement before the
  first build slice and after each slice.

## Assumptions

- The target agents are Claude Code and Codex on the user's Linux laptop,
  in this repository's worktrees and the wiki folders; other agents may use
  the skills but are not acceptance targets.
- The user already registers the gated judgment server and the reference
  library at user scope for both agents; changing user-scope settings needs
  the user's approval.
- No release has happened, so no changelog or published package versions are
  added (R-REPO-17).
- `infra/`, the wiki data under the XDG data folder, and the network-design
  documents are outside this feature.
- Cost is no constraint for judgments, but paid calls are still counted and
  kept out of verification.
- The develop coordinator owns Linear, finishes and merges; while it is
  down, slices wait for its finish or continue in a child worktree as the
  plan describes.

## Dependencies

- The four open feature branches named under Edge Cases, for code under
  `plugins/work`, `packages/wiki-consistency` and `packages/jev-ultrafast`.
- The replacement trials of U-2026-10-06e, for `scripts/plugin-clients.ts`,
  `scripts/secrets-refresh.ts`, `session_select.py` and
  `packages/jev-ultrafast`.
- The fix of the privacy gate's metadata bug, for
  `packages/education-privacy-gate` and User Story 4.
- Read-only security reviews of `system-one-adapter` and any installer or
  framework adopted.
