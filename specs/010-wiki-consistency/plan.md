# Implementation Plan: Wiki Document Consistency

**Branch**: `feature/wiki-consistency` | **Date**: 2026-09-28 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/010-wiki-consistency/spec.md`

## Summary

Keep the pages of a Wiki instance (feature 009's layout) consistent with their
raw evidence and with each other, using feature 008's region model:

- Mechanical regions are Cog blocks calling this feature's generators on
  instance files: the `index.md` catalog from page metadata, and provenance
  blocks in source pages from the BagIt bags. An offline check, run before
  every commit of the instance, checks regions, links, page metadata, cited
  bags and the append-only `log.md`, and lists orphan pages and stale
  citations.
- An offline preparation command converts cited raw revisions to Markdown
  with markitdown into the cache, finds candidate passages with qmd, and
  prints backfire requests: units against their evidence, units against
  candidate units of other pages, and, in lint scope, cross-reference
  suggestions. The agent sends them through its MCP client and fixes or
  reports the results.
- The code is a Python package, `packages/wiki-consistency/`, that uses
  `packages/doc-regions` (feature 008) as a library and ships in the work
  plugin through the build copy; a work-plugin skill holds the procedure, and
  the schema template of feature 009 gains the page metadata and the steps.

Implementation waits for features 009, 011 (CHE-9) and 008 to merge
(FR-023; tasks.md names the gates). Research: [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14.4 through uv 0.11.32 (as backfire and
`doc-regions`); Node 22 or later for qmd (24.19.0 on the development machine).

**Primary Dependencies**: `doc-regions` (feature 008, relative path source:
Cog 3.6.0, markdown-it-py 4.2.0); markitdown 0.1.8 with `docx`, `pdf` and
`pptx` extras (R3); bagit 1.9.0 (feature 009's pin); PyYAML; qmd 2.8.3 through
npm (R4); lychee 0.24.2 as a host tool (feature 008); backfire's
`backfire_verify`, `backfire_compare`, `backfire_find` and `backfire_classify`,
called by the agent (R6).

**Storage**: Nothing added to the repository. Reads the instance under
`$XDG_DATA_HOME/verbose-broccoli/wikis/<wiki-id>/`; writes Wiki pages only
through `update` (mechanical regions) and the agent; writes the cache folders
`wiki-evidence/` (1 GiB budget) and `qmd/` (3 GiB budget) under
`$XDG_CACHE_HOME/verbose-broccoli/` ([data-model.md](data-model.md)).

**Testing**: pytest in the package's uv environment with synthetic instances
built in temporary XDG roots (pages, bags made with bagit, a Git repository),
socket access blocked for the offline commands, and tree hashes compared
before and after `check` and `prepare`; a qmd test that runs the pinned qmd on
a synthetic instance; a build test that runs `check` from a work plugin built
outside the repository.

**Target Platform**: The development machine (Linux x86_64), one user.

**Project Type**: A runtime package under `packages/` shipped in the work
plugin, plus a work-plugin skill.

**Performance Goals**: `check` under 10 s for 500 pages (SC-002).

**Constraints**: `check` and `prepare` use no network and write no Wiki file;
`update` writes only region text; nothing reads credentials, configuration or
state into a request; `log.md` is never rewritten; locally owned code is glue
(generators, page metadata and link-graph checks, evidence selection, request
shaping, cache budgets).

**Scale/Scope**: One package (about six modules and their tests), one skill,
schema-template and architecture-document edits, `deno.json` tasks, `orca.yaml`
setup lines, doctor checks, an entry in feature 011's work-plugin build, and
a constitution patch amendment.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or rule | Status |
| --- | --- |
| I. Proven dependencies | PASS with a recorded gap: markitdown and qmd keyword search probed (R3, R4); qmd `embed`/`vsearch` are proved in the first implementation task before adoption, and are optional until then. |
| II. Working capabilities | PASS. Tests run real Cog, markitdown, bagit, qmd and lychee on synthetic instances; requests are checked against backfire's published input schemas. |
| III. Sources and ownership | PASS. Raw bags are read, never written; source IDs and revisions come from the bags; nothing infers identity from converted text. |
| IV. Current needs | PASS. No earlier project is a source; no user data is imported. |
| V. Observable acceptance | PASS. Positive, negative and boundary cases per story; no-network runs; unchanged files; interrupted cache writes; SC-005 runs real backfire three times. |
| VI. Wiki layers and storage | PASS after the patch amendment the user chose for `index.md` (R2), applied as the first implementation task. Converted text, indexes and models live in the cache; direct reading and the check need no cache. |
| VII. One owner, minimum implementation | PASS. Each region has one generator and named sources; cache writers have budgets and cleanup (R3, R4); `doc-regions` owns region, unit and request logic. |
| VIII. No new exceptions | PASS. None claimed. |
| IX. Layout | PASS. Runtime package in `packages/wiki-consistency/src/`; procedure in the work plugin; the work plugin gains no Deno configuration. |
| Product and Data Boundaries | PASS. Synthetic fixtures only; personal identifiers are replaced by the work plugin's backfire as feature 011 defines (R9). |
| Governance | A patch amendment of principle VI, point 2, chosen by the user (R2); a `docs` commit, so a patch bump. |

Re-check after design: unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/010-wiki-consistency/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── pages.md
│   └── commands.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
packages/wiki-consistency/
├── pyproject.toml, .python-version, uv.lock
├── package.json, package-lock.json      # qmd 2.8.3
├── src/wiki_consistency/
│   ├── __main__.py      # check, update, convert, index, prepare
│   ├── instance.py      # XDG roots, instance paths, page and bag reading
│   ├── sources.py       # generators: page_catalog, source_provenance
│   ├── lint.py          # metadata, links graph, orphans, stale citations, log prefix
│   ├── evidence.py      # markitdown conversion into the cache
│   ├── search.py        # qmd collections, search, vsearch
│   └── requests.py      # scope, evidence selection, backfire requests
└── tests/
plugins/work/skills/wiki-consistency/SKILL.md
plugins/work/skills/wiki-raw-import/assets/AGENTS.md   # feature 009's template, extended
deno.json                # wiki-consistency:install, test:wiki-consistency
orca.yaml                # uv sync and npm ci for the package
scripts/doctor.ts        # environment and lock checks for the package
docs/architecture.md     # Wiki consistency section, skill table row
.specify/memory/constitution.md   # principle VI patch
```

**Structure Decision**: The runtime is a package under `packages/` because
the work plugin's build copies it next to `packages/doc-regions`, which it
depends on by relative path (R7); backfire is the precedent. The procedure is
a work-plugin skill because Wiki maintenance is a work capability
(constitution IX; brief section 3).

## Design Decisions

- **Page conventions** ([contracts/pages.md](contracts/pages.md)): YAML front
  matter with `title`, `summary` and `sources` (source ID and revision); the
  three special pages; marker placement.
- **Commands** ([contracts/commands.md](contracts/commands.md)):
  `wiki-consistency check|update|convert|index|prepare <instance>`.
  `check` and `update` are offline; `convert` writes only the evidence cache;
  `index` may download the embedding model once; `prepare` is offline and
  prints the requests.
- **Scopes**: `changed` (units changed against the instance's `HEAD`, plus
  units of pages citing a source with a newer revision) and `lint` (every
  unit except `log.md`).
- **Procedure** (skill and schema): after an operation, `update`, `check`,
  `convert`, `index`, `prepare`; send the requests; fix or report; `check`
  again; append one `log.md` entry; commit the instance.
- **Data boundary**: requests hold only page text and cited converted
  evidence and go to the work plugin's backfire server, which replaces
  personal identifiers as feature 011 defines (R9).

## Work Split and Ownership

Main (Claude Code) owns shared files, installs, Git operations, repository
prose, the schema template and every write outside the repository; Codex
workers implement code in disjoint files through Orca orchestration
(`.claude/rules/claude-code.md`).

1. **Main, first**: confirm the gates, merge `develop`, apply the
   constitution amendment, run the qmd model probe, recheck
   feature 008's and 011's interfaces, create the package's `pyproject.toml`,
   `package.json` and locks, and add the tasks and setup lines.
2. **Workers in parallel**: generators and lint checks; evidence conversion
   and search; request preparation; the build entry and doctor checks.
3. **Main**: the skill, the schema template, the documentation, and the first
   real judgment step on a synthetic instance (SC-005).

Every Codex worker, implementer or reviewer, runs on `gpt-6-luna` at `max`
effort, as the user decided on 2026-09-28. It starts through the terminal
path of the user's `~/.claude/rules/worker-dispatch.md`, because Orca 1.4.215
rejects `--effort max` for this model: `orca-ide terminal create` with the
command `codex -m gpt-6-luna -c model_reasoning_effort=max
--dangerously-bypass-approvals-and-sandbox`, `orca-ide terminal wait --for
tui-idle`, then `orca-ide orchestration worker-start --terminal <handle>`.
The worker's status line must read "GPT-6-Luna max". Time budgets come from
backfire's judgments.

## Review and Finish

- Before each commit, the implementer or the orchestrator reviews the diff.
- Merge review for `develop` (favoring speed) by fresh reviewers from the
  other provider, given only the scope and requirements; then the
  review-record commit and `git flow feature finish wiki-consistency` from
  the `develop` worktree.

## Complexity Tracking

No constitution violations to justify.
