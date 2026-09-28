# Implementation Plan: Wiki Vaults

**Branch**: `feature/vaults` | **Date**: 2026-09-28 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/012-wiki-vaults/spec.md`

## Summary

Rename the Wiki storage folder from `wikis/` to `vaults/`, make the raw
import default to the `work` vault, and rewrite the policies for four vaults:

- `raw_import.py` builds its data and state paths from `vaults/` and defaults
  `--wiki` to `work`; nothing else in the script changes
  ([contracts/raw-import-cli.md](contracts/raw-import-cli.md)).
- The black-box tests follow the new paths and add two cases: a run without
  `--wiki` lands in `work`, and a synthetic exported conversation is admitted
  into `chat` (R3).
- Constitution VI, IX and Governance, `AGENTS.md`, `docs/architecture.md`,
  the skill, its schema template and every other document that names the
  storage folder change as the spec's FR-005 to FR-011 say. Backfire's
  classification before editing found the units to change (R1); its
  verification after editing checks them (R2).
- After `git flow feature finish`, the live instance and its state folder move
  by rename to `vaults/work/`, and `init` creates the three empty vaults (R4).

## Technical Context

**Language/Version**: Python 3.14 through uv 0.11.32 for the script (feature
009); TypeScript on Deno 2.9.6 for its tests.

**Primary Dependencies**: Unchanged from feature 009: bagit 1.9.0 pinned by
`raw_import.py.lock`, the Python standard library, Git. Backfire (the code
build's development profile, run from `packages/backfire`) and feature 008's
`doc-regions` package make the document judgments.

**Storage**: `DATA/vaults/<name>/` and `STATE/vaults/<name>/` under the
`verbose-broccoli` XDG roots ([data-model.md](data-model.md)).

**Testing**: `deno task test:wiki-raw-import` with synthetic fixtures in a
temporary home; `deno task verify` for the whole repository.

**Target Platform**: The development machine (Linux), one user, one file
system for the home folder and the XDG roots.

**Project Type**: Work-plugin skill with a command-line glue script, plus
governance documents.

**Performance Goals**: None; the move is a rename.

**Constraints**: No student name or record enters the repository, Linear or
Orca messages. The move keeps the instance's Git history and the user's
uncommitted edits, and runs only after the merge into `develop`.

**Scale/Scope**: Two lines of path code and one default in the script, one
test file, about fifteen documents, the constitution, and the one-time move.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Status |
| --- | --- |
| I. Proven dependencies | PASS. No new dependency. |
| II. Working capabilities | PASS. Tests run the real script on synthetic files; the move is checked by Git and `verify` on the live data. |
| III. Sources and ownership | PASS. Raw revisions are renamed with their folder, never rewritten; sources keep their IDs. |
| IV. Current needs | PASS. The live data is the user's own current Wiki, moved as the user decided; no earlier project is a source. |
| V. Observable acceptance | PASS. Default-vault, named-vault, chat admission and old-path cases in tests; before-and-after Git comparison and `verify` for the move. |
| VI. Wiki layers and storage | CHANGES. This feature amends VI as the user decided (spec Input 1 to 3): `vaults/` replaces `wikis/default/`, and the conversation-records rule no longer covers the chat vault. Each vault keeps the three layers; cache and state rules are unchanged. |
| VII. One owner, minimum implementation | PASS. The script keeps one code path for every vault; no migration code is added, because the move is a one-time rename done by hand. |
| IX. Layout | CHANGES. IX's sentence that the chat package has no persistent state changes (spec Input 5); the chat package still has no skills, Deno or MCP declarations or scripts. |
| Governance | The constitution commit is `feat(constitution)!`, 1.0.1 to 2.0.0, approved by the user (spec Clarifications). |
| Workflow | PASS. Spec Kit flow, git flow feature branch, merge-time review. |

Re-check after design: unchanged; the two principle changes are the feature's
purpose, not violations.

## Project Structure

### Documentation (this feature)

```text
specs/012-wiki-vaults/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── raw-import-cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
plugins/work/skills/wiki-raw-import/
├── SKILL.md                     # vaults/, default work, chat vault rule
├── assets/AGENTS.md             # schema template: chat vault rule
└── scripts/raw_import.py        # vaults/ paths, --wiki default work
scripts/wiki_raw_import_test.ts  # new paths, default and chat cases
.specify/memory/constitution.md  # VI, IX, Governance, 2.0.0
AGENTS.md                        # Records: the code vault
docs/architecture.md             # vault storage, chat package state
specs/009-wiki-storage/          # folder rename only
```

**Structure Decision**: The raw import stays the work plugin's skill; the
user decided that vaults are shared Wiki storage it may write for any vault
(spec Clarifications), so no chat-plugin copy is added.

## Work Split and Ownership

Main (Claude Code) owns the Spec Kit records, the constitution, `AGENTS.md`,
the other documents, the backfire judgments and every write outside the
repository. A Codex worker (`gpt-6-luna` at `max`) implements the script and
test change (`.claude/rules/claude-code.md`).

1. **Codex worker**: `raw_import.py` and `scripts/wiki_raw_import_test.ts`
   against the contract.
2. **Main, in parallel**: the documents and the constitution.
3. **Main, after verification**: backfire's verification of the changed
   documents, then the merge review, the review record and the finish.
4. **Main, after the finish**: the move of the live data (R4).

## Review and Finish

- Before each commit, the implementer or the orchestrator reviews the diff.
- The merge review for `develop` favors speed: a fresh Claude Code reviewer
  for the Codex-written script and tests, and a fresh Codex reviewer for the
  documents main wrote, each given only the scope and requirements. Then the
  review-record commit and `git flow feature finish vaults`.
- The move happens after the finish, so its evidence goes into CHE-19's
  completion comment and the develop session's report, not into this
  branch's records.

## Complexity Tracking

No constitution violations to justify.
