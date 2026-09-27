# Research: Linear Usage Through Orca

## R1. Where each rule lives

- **Decision**: One carrier per rule, chosen by when an agent needs it:

  | Rule (spec) | Carrier | Read when |
  | --- | --- | --- |
  | Privacy (FR-011) | Root `AGENTS.md`, "Records" | Always |
  | Only the main agent writes; one issue per feature or bug; no sub-issues; search first; others report through Orca messages (FR-002, FR-003) | Root `AGENTS.md`, "Records" | Always, by main agents and workers alike |
  | Issue ID line in the spec; link the worktree (FR-004) | Spec Kit preset `linear-issue` on the spec template | When a spec is created |
  | Completion order (FR-006) | `deno task workflow` instruction, every mode | Before editing and before completion |
  | Bug records cite the issue (FR-005) | Spec Kit bug extension's `assessment.md` | When a bug is assessed |
  | Records hold only what the repository lacks; cite the ID (FR-007) | Existing `AGENTS.md` "Records" rule, the spec line and the bug assessment | Always |
  | Archive, never delete; auto-archive 1 month (FR-008) | Linear's team setting; Orca cannot delete | Configuration |
  | Single team, labels (FR-009) | Linear configuration, done 2026-09-28 | Configuration |
  | No monitoring; a failed creation is the signal (FR-010) | Orca's error at creation; `docs/architecture.md` | When it happens |
  | Orca only (FR-001, FR-013) | Client configuration (no Linear plugin enabled), `docs/architecture.md` | Configuration |
  | Explanation (FR-014) | `docs/architecture.md`, "Linear" | For readers |

- **Rationale**: The brief asks that `AGENTS.md` take only rules that always
  need judgment. The two approved lines do: deciding whether a finding is out
  of scope, whether an existing issue is similar and what may be written to
  an external service cannot be checked mechanically. The rule on who writes
  must also reach workers: Orca's bundled `orca-linear` skill tells any agent
  in a linked worktree to create a parented follow-up issue, which this
  repository forbids. The other rules have a mechanical carrier that agents
  meet at the right moment.
- **Alternatives considered**:
  - A check in `deno task check` that every new spec has a Linear line: it
    fires only at verification, and a spec is the moment the ID is known;
    rejected as extra code once the template carries the line.
  - A `post-flow-feature-finish` git-flow hook that prints or performs the Done
    step: git-flow-next 2.1.0 runs post hooks (`RunPostHook` in the binary),
    but a second carrier for the same flow adds code without adding a reader;
    performing Linear writes from a hook would also make an external write
    outside the main agent's control. Rejected.
  - A checklist in each feature's `tasks.md` through a tasks-template preset:
    `speckit-tasks` treats template phases as examples to rewrite, so the text
    is not reliably kept. Rejected.
  - Checks that no Linear plugin or Spec Kit Linear extension is enabled:
    nothing is enabled, and a check for an absent thing guards against no
    observed failure. Rejected (constitution VII, minimum implementation).

## R2. The spec line through a Spec Kit preset

- **Decision**: A local preset `linear-issue` with one `append` layer for
  `spec-template`, installed with `uv run --project tools/spec-kit specify
  preset add --dev <source>`. Spec Kit copies it to
  `.specify/presets/linear-issue/` and records it in
  `.specify/presets/.registry`; both are committed. The appended text holds
  the line `**Linear issue**: [CHE-###]` and a comment telling the author how
  to get the ID (`orca linear issue --current`), what to do when the worktree
  is not linked (the main agent runs `orca worktree set --worktree current
  --linear-issue <ID>`; others ask it), and to move the line up to the header
  after `**Status**`, where features 006 to 010 keep it.
- **Rationale**: Presets are Spec Kit's own customization mechanism, and
  `create-new-feature.sh` and the `speckit-specify` skill both resolve the
  template through that stack. An `append` layer adds text without copying
  the upstream template, so a Spec Kit upgrade still reaches the rest of it.
  Probe (2026-09-28, scratch copy of `.specify/`): `specify preset add --dev`
  installed the preset at priority 10, `specify preset resolve spec-template`
  listed the core template and the `append` layer, and
  `.specify/scripts/bash/resolve-template.sh spec-template` ended with the
  appended line.
- **Alternatives considered**:
  - `.specify/templates/overrides/spec-template.md`: an override replaces the
    whole template, so it is a full copy that silently hides upstream changes.
  - Editing `.specify/templates/spec-template.md` in place: a Spec Kit refresh
    overwrites it, and the patch is invisible as a customization.
  - `prepend` or `wrap` layers: they can only add text before or around the
    whole template, not after `**Status**`; `append` with a move instruction
    is the closest fit.

## R3. The completion order in the workflow tool's output

- **Decision**: `buildWorkModeInstructions` in `scripts/workflow.ts` adds one
  instruction in every mode: "Linear, main agent only: before the develop
  merge review, commit the feature's record and move its Linear issue to In
  Review; after git flow feature finish, move the issue to Done with one
  completion comment giving the merge commit and the record location instead
  of a PR link." A test in `scripts/workflow_test.ts` checks that every mode
  prints it.
- **Rationale**: The root `AGENTS.md` makes every agent run `deno task
  workflow` before completion, which is exactly when the In Review move is
  due; the brief names "printed workflow text" as a carrier. Printing it in
  every mode, not only REVIEW, keeps it visible when a small final change runs
  in DIRECT mode. "Main agent only" keeps workers, who see the same output,
  from acting on it. The instruction list is data in the tool, so the change
  is one string and one test.
- **Alternatives considered**: See R1 (post-finish hook, tasks template).

## R4. The architecture section

- **Decision**: `docs/architecture.md` gets a section "Linear — 2026-09-27"
  after "Commit messages", covering the team and labels, the issue life cycle
  with Orca's commands (see [contracts/linear-lifecycle.md](contracts/linear-lifecycle.md)),
  the free plan's limit and archiving, and the R1 table in prose. The Spec Kit
  extensions section names the `linear-issue` preset.
- **Rationale**: Principle VII keeps design decisions in authored documents;
  readers at HEAD need one place that explains the flow the carriers
  implement.

## R5. Settings outside the repository

- **Decision**: The user sets the auto-archive period in Linear's UI: Team
  Settings (team `cherry-pick-foundation`) > Issue statuses & automations >
  auto-archive closed issues after 1 month. Linear applies a change at its
  next auto-archive run, usually within 24 hours
  (<https://linear.app/docs/delete-archive-issues>). The labels `code`, `work`
  and `chat` were created in Linear's UI on 2026-09-28. Codex's cached
  `linear` plugin folder was moved to the trash on 2026-09-27.
- **Rationale**: Orca cannot change team settings, and no Linear API key is
  configured; the user's memory notes that settings should be applied
  directly when a programmatic route exists, and none does here.
- **Observation**: Codex refreshed every cached plugin of its
  `openai-curated-remote` marketplace on 2026-09-27 (all folders share one
  timestamp), so the `linear` folder may return. It stays unused because
  `~/.codex/config.toml` has no `[plugins."linear@…"]` entry. Claude Code's
  `enabledPlugins` has no Linear plugin.

## R6. Similar-issue search

- **Decision**: Before creating an issue, the main agent runs `orca linear
  list-issues --team CHE --query "<words>" --include-archived --json`, since
  `orca linear search` has no archive option, and reuses an open match or
  links to an archived one in the new issue's body.
- **Rationale**: Archived issues are the long-term record of Linear's side;
  a closed duplicate is best found there before a new issue is written.
