# Implementation Plan: Upstream Tools in Place of Own Tooling Code

**Branch**: `feature/upstream-tooling` | **Date**: 2026-09-30 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/023-upstream-tooling/spec.md`

## Summary

Replace each piece of own code that CHE-44 lists with its upstream tool,
used unchanged and pinned, and remove the replaced code and its tests. The
work runs in three waves:

1. **Independent swaps without pending decisions**: check-jsonschema for the
   plugin manifest check, cog regions for the reference documents, and qmd's
   own interface for Wiki search.
2. **Swaps that wait for the user's answers or for machine installs**: mise
   for the environment check, commitizen for the constitution version,
   lefthook for the Git hooks, Vale for the Wiki page rules, and bagit for
   the raw import.
3. **After CHE-42 merges**: Turborepo run summaries for verify's evidence,
   dependency-cruiser's own command and configuration for the import rules
   and the affected-files graph, and import-linter for Python boundaries.

Every tool passed a read-only security review at its pinned version with no
high-severity finding (research.md R0). The repository applies the controls
that went to the user with the findings, which the user accepted on
2026-09-30; the reports name more controls than that list, and the ones not
adopted are named in research.md R0. The research is in
[research.md](research.md).

## Technical Context

**Language/Version**: TypeScript on Node.js 24.12 or later; Python 3.14.

**Primary Dependencies**: check-jsonschema 0.38.2 (PyPI, new), cogapp 3.6.0
and qmd 2.8.3 (pinned already); later mise 2026.9.16, commitizen 4.19.0,
lefthook 2.1.15, Vale 3.23.0, bagit 1.9.0, import-linter 2.15,
dependency-cruiser 18.2.0 and Turborepo 2.11.5.

**Storage**: None new. qmd's index and the Vale run stay in the cache.

**Testing**: `npm run check` and `npm run verify`; the Node and Python suites
minus the removed tests, plus new tests where no existing test shows a
swapped capability.

**Target Platform**: The development machine (Linux x64) and Orca worktrees.

**Project Type**: Repository checks and the work plugin's Wiki tools.

**Constraints**: Offline checks from locked installs; synthetic fixtures
only; runs against the vaults are read-only and report counts only; nothing
installed outside the repository without the user's approval; `requests.py`
unchanged (CHE-39).

**Scale/Scope**: About 3,080 own-code lines in the first two waves and about
1,930 in the third (research.md, per swap).

## Constitution Check

- **I. Proven Dependencies**: every tool pinned (npm lock, uv lock or mise).
  Quarto stays separately installed. Pass.
- **V. Observable Acceptance**: each swap keeps an existing test or adds one
  with positive, negative and boundary cases on synthetic input. Pass.
- **VI. Wiki layers**: raw bags keep their layout and record; the check
  writes nothing; the cache holds only rebuildable data. Pass.
- **VII. Minimum Implementation**: the reuse order is the purpose of the
  feature; the only local code left is named glue. Pass.
- **IX. Layout**: tool configurations at the root or in the owning package;
  tool environments under `tools/`. Pass.
- **Development workflow**: Spec Kit records here; commits by the
  coordinator after reviewing each worker's diff; the develop merge review
  and `git flow feature finish` follow the constitution. Pass.

## Project Structure

### Documentation (this feature)

```text
specs/023-upstream-tooling/
├── spec.md
├── plan.md
├── research.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code (repository root), wave 1

```text
tools/check-jsonschema/        # new uv project pinning check-jsonschema
scripts/validate_plugins.ts    # removed
package.json, package-lock.json, turbo.json  # plugins:validate runs
                               # check-jsonschema; docs:* tasks removed
scripts/docs.ts, scripts/docs_test.ts  # removed
scripts/doc_sources.py, scripts/doc_sources_test.py  # reference generators
scripts/doc_regions.toml       # reference documents as targets
docs/reference/*.md            # cog regions
scripts/cli_contract_test.ts(.snapshot)  # plugins:validate entry removed
orca.yaml                      # syncs tools/check-jsonschema
packages/wiki-consistency/src/wiki_consistency/search.py  # qmd's interface
packages/wiki-consistency/src/wiki_consistency/search.mjs # removed
packages/wiki-consistency/tests/test_search.py
docs/architecture.md, AGENTS.md  # commands renamed (coordinator)
```

Waves 2 and 3 were planned in tasks.md after the user's decisions (spec.md,
Clarifications).

## Validation

1. The locked installs give the pinned versions.
2. `npm run plugins:validate` passes on the three plugins and fails on a
   synthetic manifest that breaks its schema.
3. `npm run doc-regions:check` passes; after a change to a root task, a
   plugin manifest or a documented command's help, it fails until
   `npm run doc-regions:update` runs.
4. The Wiki consistency suite passes with search through qmd's interface.
5. `npm run verify` passes after the final merge of `develop`.
