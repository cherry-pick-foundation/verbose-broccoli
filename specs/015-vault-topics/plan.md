# Implementation Plan: Topics in Vault Page Metadata

**Branch**: `feature/vault-topics` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/015-vault-topics/spec.md`

## Summary

Each vault's schema, its `AGENTS.md`, gains YAML front matter that declares
the vault's topics, and every page's front matter gains a required `topics`
list drawn from that declaration. The `wiki-consistency` tool reads both with
the helpers it already has: page validation in `instance._metadata` checks
the list's shape, a new `instance.declared_topics` reads the schema's list
the same way, and `lint.check` and `lint.update` reject a page topic that the
schema does not declare. `sources.page_catalog` groups the index under one
heading per topic. The template, the architecture document and the
consistency skill describe the rule. After the merge, the `default`, `chat`
and `code` vaults get the same schema text with an empty topic list, one
commit each.

## Technical Context

**Language/Version**: Python 3.14 (the `wiki-consistency` uv project);
Markdown for the schema template and documents.

**Primary Dependencies**: PyYAML 6.0.3 and doc-regions, both already used by
`wiki-consistency`; no new dependency.

**Storage**: Vaults under `DATA/vaults/<name>/`, each with its own Git
repository; the tool reads the schema `AGENTS.md` and the pages under
`wiki/`.

**Testing**: `deno task test:wiki-consistency`
(`packages/wiki-consistency/tests/`, pytest with synthetic vaults from
`tests/conftest.py`); `deno task test:wiki-raw-import`, whose test compares a
new vault's `AGENTS.md` with the template byte for byte; `deno task verify`
for the whole repository.

**Target Platform**: Linux, in Claude Code or Codex with the work plugin.

**Project Type**: A change to an existing command-line tool plus schema and
skill text.

**Performance Goals**: None beyond the existing tool; one extra small file
read per `check` and `update`.

**Constraints**: Offline and read-only `check`; deterministic generator
output (no clock or environment); no change to layer folders, the region
call in `index.md`, or the judgment step; the `work` vault untouched;
synthetic fixtures only.

**Scale/Scope**: Vaults of tens to hundreds of pages and a few dozen topics.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
| --- | --- | --- |
| I. Proven dependencies | No new dependency; PyYAML and doc-regions are already pinned. | Pass |
| II. Working capabilities | The check and the grouped index are the delivered capability; vault adoption is recorded separately as operational work after the merge. | Pass |
| III. Sources and ownership | Topic names are exact labels, not normalized identity keys. | Pass |
| IV. Current needs | Built from CHE-27 and the user's 2026-09-29 answers only. | Pass |
| V. Observable acceptance | Positive, negative and boundary cases with synthetic vaults: valid pages, every invalid shape, undeclared names, a malformed schema, an empty vault, a page with several topics, unchanged files after a refused `update`. | Pass |
| VI. Wiki layers | Layer folders and raw rules stay; `index.md` is still regenerated from page metadata; the topic list lives in the schema, not in a separate settings file. | Pass |
| VII. Minimum implementation | Reuses `_front_matter`, `_metadata`, PyYAML and the existing check and update paths; the only new function reads the schema's list. Generated output stays deterministic. | Pass |
| IX. Three plugins | Changes stay in `packages/wiki-consistency` and the work plugin's skill text. | Pass |
| Workflow | Spec, clarify, plan, tasks, analysis, implementation by Codex workers, develop merge review, git flow finish. | Pass |

Post-design recheck: the design below keeps every row as it is.

## Project Structure

### Documentation (this feature)

```text
specs/015-vault-topics/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── topics.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
packages/wiki-consistency/
├── src/wiki_consistency/
│   ├── instance.py      # page topics in _metadata; declared_topics(root)
│   ├── lint.py          # schema and undeclared-topic problems in check and update
│   └── sources.py       # page_catalog groups rows under topic headings
└── tests/
    ├── conftest.py      # synthetic schema with declared topics; pages with topics
    ├── test_instance.py
    ├── test_check.py
    └── test_sources.py

plugins/work/skills/
├── wiki-raw-import/assets/AGENTS.md   # schema template: front matter and page rules
└── wiki-consistency/SKILL.md          # check row names topics

docs/architecture.md                   # Wiki consistency bullets
```

**Structure Decision**: Edit the existing package, template and documents in
place; no new module, package or skill.

## Complexity Tracking

No constitution violations to justify.
