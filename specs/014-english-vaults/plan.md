# Implementation Plan: English Vaults

**Branch**: `feature/english-vaults` | **Date**: 2026-09-29 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/014-english-vaults/spec.md`

## Summary

State the user's rule that vault content is written in English where page
writing is described, and apply it to the three vaults that have no pages yet:

- The schema template's Wiki section gets one rule: write `wiki/` in English,
  leave raw evidence unchanged, keep student and school names in the roster's
  spelling, and allow a short direct quote next to an English translation.
- The `wiki-consistency` skill, `docs/architecture.md` and the example schema
  `docs/examples/wiki/AGENTS.md` state the rule in one sentence each.
- After `git flow feature finish`, the template is copied into the `default`,
  `chat` and `code` vaults, one commit each after the offline `check` passes.

## Technical Context

**Language/Version**: Markdown only; no code changes.

**Primary Dependencies**: The `wiki-consistency` package's `check` (feature
010) for the vaults.

**Storage**: `DATA/vaults/{default,chat,code}/AGENTS.md` under the
`verbose-broccoli` XDG data root, each versioned by its vault's Git
repository.

**Testing**: `deno task verify` for the repository;
`wiki-consistency check --wiki <vault>` for each vault.

**Target Platform**: The development machine (Linux).

**Project Type**: Work-plugin skill template and documents.

**Performance Goals**: None.

**Constraints**: No student name enters the repository, Linear or Orca
messages. The `work` vault and every raw revision stay untouched. CHE-20
(`feature/chat-export`) also edits the `wiki-raw-import` skill; whichever
feature finishes second merges `develop` and keeps both changes.

**Scale/Scope**: Four documents and three vault schema files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Status |
| --- | --- |
| I. Proven dependencies | PASS. No new dependency. |
| II. Working capabilities | PASS. The vault schemas are checked by `check` after the copy. |
| III. Sources and ownership | PASS. Raw evidence stays unchanged, and the rule says so. |
| IV. Current needs | PASS. The user's decision of 2026-09-29. |
| V. Observable acceptance | PASS. Each vault's schema equals the template, its commit exists and `check` exits 0. |
| VI. Wiki layers and storage | PASS. The page language is a page convention, which VI puts in the schema. |
| VII. One owner, minimum implementation | PASS. The template holds the rule; the other documents state it in one sentence and point to the schema. |
| IX. Layout | PASS. No file moves. |
| Governance | PASS. The constitution does not change. |
| Workflow | PASS. Spec Kit flow, git flow feature branch, merge-time review. |

Re-check after design: unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/014-english-vaults/
├── spec.md
├── plan.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
plugins/work/skills/wiki-raw-import/assets/AGENTS.md  # schema template: the rule
plugins/work/skills/wiki-consistency/SKILL.md         # one sentence
docs/architecture.md                                  # one sentence
docs/examples/wiki/AGENTS.md                          # one bullet
```

**Structure Decision**: The template is the rule's one owner. The research,
data-model, contract and quickstart documents are left out: there is no
unknown to research and no interface or data change.

## Work Split and Ownership

Main (Claude Code) writes the documents and makes the vault commits, since the
change is repository prose and a schema copy (`.claude/rules/claude-code.md`).
A fresh Codex reviewer (`gpt-6-luna` at `max`) gives the merge review.

## Review and Finish

- The merge review for `develop` favors speed: a fresh Codex reviewer, given
  only the scope and requirements. Then the review-record commit and
  `git flow feature finish english-vaults` in the `develop` worktree.
- The vault commits happen after the finish, so their evidence goes into
  CHE-25's completion comment, not into this branch's records.

## Complexity Tracking

No constitution violations to justify.
