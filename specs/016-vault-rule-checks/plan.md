# Implementation Plan: Vault Page Rule Checks

**Branch**: `feature/vault-rule-checks` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/016-vault-rule-checks/spec.md`

## Summary

`wiki-consistency check` gains the page rules that a pattern can test. A new
module, `rules.py`, blanks out mechanical regions and the front matter's
`sources` field, then looks for phone numbers, email addresses,
registration numbers and postal addresses; Hangul, Chinese and Japanese
letters outside roster names and allowed quotes; school names that are not
domain IDs; dates not written as YYYY-MM-DD; and times without a zone. It
also checks that each student page's student is in the roster. The roster
and the phone, email and name matching come from backfire's work build
(`backfire_education`), so the check sees names and contacts exactly as
backfire replaces them; the only change there moves an inner function to
module level. The schema template, the consistency skill, the example
schema and the architecture document say which rules the check enforces
and which stay with judgment.

## Technical Context

**Language/Version**: Python 3.14 (the `wiki-consistency` uv project);
Python 3.11 or later for `packages/backfire`; Markdown for the template and
documents.

**Primary Dependencies**: doc-regions and PyYAML 6.0.3, already used;
new: the repository's `backfire` package with its `education` extra
(`phonenumbers` 9.0.40) as a path dependency (research R3). Standard
library `unicodedata`, `re` and `datetime` for the rest.

**Storage**: Vaults under `DATA/vaults/<name>/`; the roster CSV named by
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml`, read only.

**Testing**: `deno task test:wiki-consistency`
(`packages/wiki-consistency/tests/`, pytest with synthetic vaults from
`tests/conftest.py` and a synthetic roster in a temporary
`XDG_CONFIG_HOME`); `deno task test:backfire` for the moved span finder and
the plugin build; `deno task verify` for the whole repository.

**Target Platform**: Linux, in Claude Code or Codex with the work plugin.

**Project Type**: A change to an existing command-line tool, a narrow
change to a shared package, and schema and skill text.

**Performance Goals**: Feature 010's SC-002 still holds: `check` of 500
pages in under 10 seconds (spec SC-003); the roster is read once and the
span finder runs once per page.

**Constraints**: `check` stays offline and read-only and needs no cache;
no message repeats matched text; no real vault, roster or configuration is
read by tests or changed by the feature; synthetic fixtures only.

**Scale/Scope**: Vaults of tens to hundreds of pages; rosters of tens to
hundreds of rows.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
| --- | --- | --- |
| I. Proven dependencies | The new dependency is the repository's own backfire package, pinned through `uv.lock`; `phonenumbers` keeps backfire's pin. | Pass |
| II. Working capabilities | The rules in `check` are the delivered capability; rules left to judgment are listed as such, not counted as checked. | Pass |
| III. Sources and ownership | Names match the roster exactly, as backfire does; no normalization becomes an identity key. The roster stays the operator's file, read in place. | Pass |
| IV. Current needs | Built from CHE-26, the schema's current rules and the user's 2026-09-29 answers. | Pass |
| V. Observable acceptance | Positive, negative and boundary cases per rule with synthetic vaults and roster; a missing or malformed roster; unchanged files after the check; each rule's tests seen failing first. | Pass |
| VI. Wiki layers | The check reads `wiki/` and the schema; raw, layer folders and the special pages' rules stay. The roster is configuration, read, not copied. | Pass |
| VII. Minimum implementation | Reuses backfire's roster reader and span finder, doc-regions' region scanner, PyYAML and the standard library; local code is the rule patterns, which no dependency provides (research R5 to R7). | Pass |
| IX. Three plugins | Changes stay in `packages/` and the work plugin; the work build already ships backfire beside `wiki-consistency`. | Pass |
| Product and data boundaries | No student name, roster row or vault content enters fixtures, records, Linear or Orca. | Pass |
| Workflow | Spec, clarify, plan, tasks, analysis, implementation by a Codex worker, develop merge review, git flow finish. | Pass |

Post-design recheck: the design below keeps every row as it is.

## Project Structure

### Documentation (this feature)

```text
specs/016-vault-rule-checks/
├── plan.md
├── research.md
├── quickstart.md
├── contracts/
│   └── page-rules.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
packages/backfire/src/backfire_education/
└── pseudonymize.py      # the span finder moves to module level (research R4)

packages/wiki-consistency/
├── pyproject.toml       # backfire[education] path dependency
├── uv.lock
├── src/wiki_consistency/
│   ├── rules.py         # new: checked text, roster, the page rules
│   └── lint.py          # check() adds the rule problems
└── tests/
    ├── conftest.py      # XDG_CONFIG_HOME in a temporary folder for every test
    └── test_rules.py    # new: per-rule cases

deno.json                # wiki-consistency:install syncs backfire first
orca.yaml                # setup syncs backfire first

plugins/work/skills/
├── wiki-raw-import/assets/AGENTS.md   # student pages; what check enforces
└── wiki-consistency/SKILL.md          # check row; install order

docs/architecture.md                   # Wiki consistency bullets
docs/examples/wiki/AGENTS.md           # the same rules as the template
```

**Structure Decision**: One new module and test file in the existing
package; no new package, skill or command.

## Complexity Tracking

No constitution violations to justify.
