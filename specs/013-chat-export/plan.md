# Implementation Plan: ChatGPT Export into the Chat Vault

**Branch**: `feature/chat-export` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-chat-export/spec.md`

## Summary

The user exports all ChatGPT conversations through OpenAI's account data
export, saves the ZIP over one fixed file, and asks the agent to admit it. The
existing raw import copies that file unchanged into the `chat` vault and then
the `work` vault; a later export saved over the same file becomes a new
revision of the same source. The only code change is in the Wiki consistency
tool: a JSON converter makes conversations written with `\uXXXX` escapes
readable as evidence. The rest is text: a ChatGPT export section in the work
plugin's `wiki-raw-import` skill, and the rule, in constitution VI and the
documents that repeat it, that exported conversations are Raw evidence in the
`chat` and `work` vaults.

## Technical Context

**Language/Version**: Python 3.14 (the raw import script and the
`wiki-consistency` uv project); TypeScript on Deno 2.9.6 for repository tests.

**Primary Dependencies**: `bagit==1.9.0` (raw import, unchanged); MarkItDown
0.1.8 (`markitdown[docx,pdf,pptx]`, pinned by `wiki-consistency`), extended
only through its `register_converter` interface; Python's standard `zipfile`
and `json` modules.

**Storage**: Vaults under `DATA/vaults/<name>/`; the evidence cache under
`CACHE/wiki-evidence/`; the fixed export file
`~/Documents/chatgpt/chatgpt-export.zip` in the user's workspace.

**Testing**: `deno task test:wiki-raw-import`
(`scripts/wiki_raw_import_test.ts`); `deno task test:wiki-consistency`
(`packages/wiki-consistency/tests/`); `deno task verify` for the whole
repository. Fixtures are synthetic exports built in temporary folders.

**Target Platform**: Linux, in Claude Code or Codex with the work plugin.

**Project Type**: Agent plugin skill text plus a small change to an existing
command-line tool.

**Performance Goals**: None beyond the existing tools; see research R6 for
size limits.

**Constraints**: No change to the raw import; no chat plugin skill; no real
export, student name or conversation content in the repository, Linear or
Orca; nothing admitted into the real vaults without the user's go-ahead.

**Scale/Scope**: One export at a time, of unknown size (research R6); two
vaults per export.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
| --- | --- | --- |
| I. Proven dependencies | No new dependency; MarkItDown is extended through its own interface. | Pass |
| II. Working capabilities | The real admission is recorded as post-merge work, not counted as done. | Pass |
| III. Sources and ownership | The export is copied, never moved or changed; the fixed file stays in the user's workspace. | Pass |
| IV. Current needs | Built from the user's 2026-09-29 answers; no earlier project is a source. | Pass |
| V. Observable acceptance | Synthetic ZIP fixtures: admission, re-export revision, unchanged rerun, both vaults, escaped and direct JSON, unparsable JSON, originals unchanged. | Pass |
| VI. Wiki layers | Raw stays create-only and one file per source; the rule changes by amendment (below). | Pass after amendment |
| VII. Minimum implementation | Reuse order: the raw import as it is (1), MarkItDown's ZIP and plain-text converters (1), one registered converter as glue (4). Research R3 lists the rejected alternatives. | Pass |
| IX. Three plugin packages | No chat plugin skill; the procedure lives in the work plugin. | Pass |
| Development workflow | Spec, clarification, plan, tasks, analysis, implementation, merge review, git flow finish. | Pass |
| Governance | `feat(constitution)` raises 2.0.0 to 2.1.0 once; the change records the user's reason. | Pass |

**Amendment**: Principle VI's sentence "The `chat` vault is the exception:
exported conversations are its Raw evidence" becomes an exception for the
`chat` and `work` vaults. The Sync Impact Report, the Governance history and
the version change with it. The user decided this on 2026-09-29
(clarification Q6).

Post-design re-check: the design adds no package, service or configuration
and keeps every writer's existing budget; all gates still pass.

## Project Structure

### Documentation (this feature)

```text
specs/013-chat-export/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── export-procedure.md
│   └── evidence-json.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
.specify/memory/constitution.md                    # VI amendment, 2.1.0
docs/architecture.md                               # vault table and rule
plugins/work/skills/wiki-raw-import/
├── SKILL.md                                       # ChatGPT export section, rule
└── assets/AGENTS.md                               # schema template rule
packages/wiki-consistency/
├── src/wiki_consistency/evidence.py               # JSON converter, cache key
└── tests/test_evidence.py                         # escaped, direct, invalid JSON; ZIP export
scripts/wiki_raw_import_test.ts                    # fixed-file export across chat and work
```

**Structure Decision**: Every change goes into an existing file. The
coordinator (Claude Code) writes the constitution, the skill, the schema
template and the architecture document; Codex workers write the code and
tests.

## Complexity Tracking

No violations.
