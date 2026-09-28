---

description: "Task list for Wiki document consistency"
---

# Tasks: Wiki Document Consistency

**Input**: Design documents from `specs/010-wiki-consistency/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Start condition**: Do not start any task until all three gates hold on
`develop`:

1. **Feature 009, Wiki storage** (CHE-7, `feature/wiki-storage`) has merged:
   the instance layout, the bags and the schema template come from it.
2. **CHE-9, backfire for education work** (feature 011,
   `feature/backfire-education`) has merged: its work-plugin backfire replaces
   personal identifiers before the provider call (FR-019), it declares
   backfire in the work plugin, and it adds the per-plugin build whose
   work-plugin list this feature extends; that build's interface is fixed
   only in 011's plan, and no task here assumes it before T002 reads it.
3. **Feature 008, repository document consistency** (CHE-6,
   `feature/doc-consistency`) has merged: `packages/doc-regions` and lychee
   come from it.

Feature 005 (backfire) has already merged (`8ab332b`). Read the other
branches with `git show <branch>:<path>`; never edit them or their worktrees.

**Tests**: Required. The root `AGENTS.md` asks for tests with every code
change, and each user story names an independent test.

**Organization**: Tasks are grouped by user story. Main (Claude Code) owns
shared files (`deno.json`, `orca.yaml`, the package's `pyproject.toml`,
`package.json` and locks), installs, Git operations, repository prose, the
schema template and every write outside the repository; Codex workers own the
code tasks in the Worker Assignment section.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US5)

---

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Confirm the three gates (`git merge-base --is-ancestor <branch>
  develop` for `feature/wiki-storage`, `feature/backfire-education` and
  `feature/doc-consistency`), merge `develop` into `feature/wiki-consistency`,
  and run `deno task backfire:install` and `deno task verify`.
  - 2026-09-28: all three merged by `develop` `1166a84`, merged here at
    `1dfc5f7`; `deno task verify` passed after one rerun of the CHE-18
    first-install flake in `test:wiki-raw-import`.
- [x] T002 Recheck the interfaces this plan assumes and record every
  difference in [research.md](research.md), then update the contracts before
  workers start: feature 009's bag fields, revision names, `log.md`
  convention and schema template (R1, R2); `packages/doc-regions`' modules
  against the three needs in R8; feature 011's pseudonymization and its
  work-plugin backfire declaration and build (R7, R9); backfire's input
  schemas and limits (R6).
  - 2026-09-28: 011's spec is `075896f` on `feature/backfire-education`. Its
    orchestrator reports that pseudonymization runs only in the work build,
    on every request at backfire's exit to the provider, and hides
    identifiers only (student and guardian names and schools from the roster,
    phone numbers and emails by format); learning content such as scores and
    observations is sent as is. So FR-019 must keep personal records out of
    010's calls itself. 011's plan will fix the build interface.
  - 2026-09-28: 011's plan is `87563f8`. Its build takes only packages under
    `packages/backfire/src/` (research.md R7), it has no withhold policy, and
    both plugins name their server `backfire` (R9).
  - 2026-09-28: rechecked on `develop` `1166a84`; differences in research.md
    R11, contracts updated.
- [x] T003 Apply the amendment the user chose (spec.md Clarifications): amend
  point 2 of principle VI in
  `.specify/memory/constitution.md` as [research.md](research.md) R2 says, in
  its own `docs` commit (patch bump; the commit-msg hook checks it), with the
  Sync Impact Report and the Governance record updated. Check first whether
  the constitution cleanup feature changed that sentence on `develop`. As of
  2026-09-28 the develop session expects that feature to merge first: it
  only drops the tail "under the selected operation's scope", so the sentence
  reads "The LLM maintains pages, cross-references, `index.md`,
  `overview.md`, and the append-only `log.md`.", and it sets the version to
  1.0.0, so this `docs` amendment would make it 1.0.1. Merge `develop` into
  this branch before amending.
  - 2026-09-28: amended in `c80e051` (version 1.0.1).
- [x] T004 Prove qmd's semantic search (constitution I; R4): in a scratch
  folder with the pinned `package-lock.json`, `npm ci --ignore-scripts`, run
  `qmd embed` and `qmd vsearch --json` on synthetic Korean and English pages
  with `QMD_EMBED_MODEL` set to the Qwen3 embedding model and the cache
  variables of R4; record the download size, time, whether the held-back
  install scripts matter, and the result in research.md R4; set the model in
  the contract, or record that semantic search stays off.
  - 2026-09-28: proved; semantic search is on with the Qwen3 model. The CLI
    loads the model per query, so `prepare` searches through qmd's library
    API in one Node process (research.md R4).
- [x] T005 Create `packages/wiki-consistency/`: `pyproject.toml` (console
  script `wiki-consistency = "wiki_consistency.__main__:main"`, dependencies
  `doc-regions` as a path source `../doc-regions`,
  `markitdown[docx,pdf,pptx]==0.1.8`, `bagit==1.9.0`, PyYAML pinned, dev group
  `pytest` at backfire's version, `required-version = ">=0.11.32"`),
  `.python-version` `3.14.4`, an empty `src/wiki_consistency/__init__.py`,
  `uv.lock`, and `package.json` with `@tobilu/qmd` `2.8.3` exactly plus
  `package-lock.json`; confirm `uv sync --locked --project
  packages/wiki-consistency` and `npm ci --ignore-scripts --prefix
  packages/wiki-consistency` work.
  - 2026-09-28: `requires-python` is `>=3.14`: with `>=3.13` uv resolved
    onnxruntime 1.20.1, which has no Python 3.14 wheel; 1.30.0 now.
- [x] T006 Update `deno.json` (a `wiki-consistency:install` task running both
  installs, `test:wiki-consistency` added to `test`) and `orca.yaml`'s setup
  script (both installs, after the `doc-regions` line); ignore
  `packages/wiki-consistency/node_modules/` in `.gitignore`.
  - 2026-09-28: `.gitignore` already ignores every `node_modules/`.
    `test:wiki-consistency` joins the `test` list with T008's first tests,
    since pytest fails when it collects none.
- [ ] T007 [P] Extend `scripts/doctor.ts` and `scripts/doctor_test.ts`: fail
  when `packages/wiki-consistency/.venv` or `node_modules` is missing or
  differs from its lock, and when `node` is older than 22. Tests first.

**Checkpoint**: The environment exists; workers can run their suites.

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T008 Write `packages/wiki-consistency/tests/test_instance.py` and a
  test helper that builds synthetic instances in temporary XDG roots (feature
  009's layout, bags made with bagit, a Git repository): XDG roots and
  `--wiki` resolve; pages, front matter and citations parse; the special
  pages are recognized; bags and their revisions are listed from `raw/`
  alone. Fails before T009.
- [ ] T009 Implement `packages/wiki-consistency/src/wiki_consistency/instance.py`
  per [data-model.md](data-model.md). T008 passes.

**Checkpoint**: Every command can read an instance.

---

## Phase 3: User Story 1 - The offline check refuses a stale or broken Wiki (Priority: P1) 🎯 MVP

**Goal**: `check` fails on stale regions, broken links, bad metadata, bad
cited bags and a changed `log.md`, and lists orphans and stale citations,
without writing or network.

**Independent Test**: `deno task test:wiki-consistency` and the quickstart's
"Offline check".

- [ ] T010 [US1] Write `tests/test_sources.py` for `page_catalog` and
  `source_provenance`: fixture instances give the exact expected text, sorted
  by path or revision; the special pages are left out of the catalog; a
  missing source raises; no network, clock or environment use. Fails before
  T011.
- [ ] T011 [US1] Implement `src/wiki_consistency/sources.py` per
  [data-model.md](data-model.md). T010 passes.
- [ ] T012 [US1] Add to `packages/doc-regions/src/doc_regions/regions.py` a
  backward-compatible keyword for the command that the stale-region failure
  message names (research.md R11; default "deno task doc-regions:update"),
  passed from `check` through `process` to `cog`, with a test in
  `packages/doc-regions/tests/`; feature 008's own tests keep passing. The
  three needs of R8 are already in 008's package.
- [ ] T013 [US1] Write `tests/test_lint.py` and `tests/test_check.py`: every
  failure case in [contracts/commands.md](contracts/commands.md) "`check`"
  fails naming page and line; a passing instance passes; orphans and stale
  citations are listed and do not fail; a changed or removed earlier
  `log.md` line fails, an appended entry passes, and an instance without
  commits skips that check; `update` changes only region lines and a second
  run changes nothing. Every `check` case compares a hash of the instance and
  cache before and after and runs with `socket.socket` patched to raise.
  Fails before T014.
- [ ] T014 [US1] Implement `src/wiki_consistency/lint.py` and the `check` and
  `update` commands in `__main__.py`: `doc_regions` for regions, lychee
  offline for links, markdown-it-py link tokens for the orphan graph, bagit
  fast validation for cited bags, `git show HEAD:wiki/log.md` for the log
  prefix; output and exit codes per the contract. T013 passes (depends on
  T011, T012).

**Checkpoint**: User Story 1 works on its own.

---

## Phase 4: User Story 2 - Changed Wiki text is judged against its evidence (Priority: P1)

**Goal**: `convert`, `index` and `prepare --scope changed` print valid,
split backfire requests.

**Independent Test**: `deno task test:wiki-consistency` and the quickstart's
"Judgment step" steps 1 to 4.

- [ ] T015 [P] [US2] Write `tests/test_evidence.py`: synthetic DOCX, PPTX and
  text PDF fixtures (generated in the test or committed as small synthetic
  files) convert with their text; plain text and Markdown pass through; an
  image-only PDF and an unsupported format get an unreadable mark with the
  reason; converted files are never rewritten; the 1 GiB budget check (with a
  small budget injected), a failure and SIGTERM leave no temporary file, and
  leftovers are removed at the next start; nothing is written outside the
  evidence cache; no socket opens. Fails before T016.
- [ ] T016 [P] [US2] Implement `src/wiki_consistency/evidence.py` and the
  `convert` command per research.md R3. T015 passes.
- [ ] T017 [P] [US2] Write `tests/test_search.py` with the pinned qmd: the
  `pages` and `evidence` collections are created with the cache variables of
  R4 and `--index <wiki-id>`; nothing is written into the instance; `search`
  hits map to the unit containing the hit line; a deleted index is rebuilt;
  the 3 GiB budget refuses before `update` or `embed`; without the embedding
  model, semantic search is reported unavailable and keyword search still
  works; many queries run in one Node process through qmd's library API and
  give the same hits as the CLI. Fails before T018.
- [ ] T018 [P] [US2] Implement `src/wiki_consistency/search.py`, the Node
  script `src/wiki_consistency/search.mjs` it runs for batched `searchLex`
  and `searchVector` queries (research.md R4), and the `index` command.
  T017 passes.
- [ ] T019 [US2] Write `tests/test_prepare.py`: scope `changed` selects
  units differing from the instance's `HEAD` and every unit of pages with a
  stale citation, whose evidence includes the latest revision; evidence is
  whole under `--max-evidence-chars` and matching passages above it; page
  requests carry up to `--candidates` units of other pages; units of
  `overview.md` get the pages it links to as evidence; units whose
  sources are all unreadable are listed as `unverifiable` and in no request;
  mechanical-region text and `log.md` never appear; requests stay within the
  672-cell limit and the 64-item classify limit; every
  in-scope unit is in exactly one evidence request or listed; `calls` counts
  the requests; every `arguments` object validates against backfire's input
  schemas (imported from `packages/backfire` or copied as fixtures in T002);
  two runs give byte-identical output; without `convert` or `index` it
  refuses and names the step; no file changes and no socket opens. Fails
  before T020.
- [ ] T020 [US2] Implement `src/wiki_consistency/requests.py` and the
  `prepare` command per [contracts/commands.md](contracts/commands.md), using
  `doc_regions` for units and request splitting. T019 passes (depends on
  T009, T016, T018).

**Checkpoint**: The agent can run the per-change judgment step.

---

## Phase 5: User Story 3 - A lint operation reviews the whole Wiki (Priority: P2)

**Goal**: `prepare --scope lint` covers every unit and adds cross-reference
suggestions.

**Independent Test**: The quickstart's "Judgment step" step 5.

- [ ] T021 [US3] Extend `tests/test_prepare.py`: lint scope covers every
  unit except `log.md` exactly once; for two related pages that do not link
  to each other, each page's `crossref` request lists the other; a page with
  fewer than two candidates gets no `crossref` request. Fails before T022.
- [ ] T022 [US3] Implement lint scope and `crossref` requests in
  `requests.py`. T021 passes.

---

## Phase 6: User Story 4 - Personal data and credentials stay where the user allows (Priority: P2)

**Goal**: Requests hold only page text and cited converted evidence, and go
to the work plugin's backfire server.

**Independent Test**: `deno task test:wiki-consistency` (the data-boundary
tests).

- [ ] T023 [US4] Write `tests/test_boundary.py`: with synthetic
  configuration, state and credential files containing a marker string, no
  request contains the marker (depends on T020).
- T024 Removed on 2026-09-28: feature 011 withholds no data, and the user
  chose to rely on its pseudonymization (spec.md Clarifications).

---

## Phase 7: User Story 5 - The tooling ships with the work plugin (Priority: P3)

**Goal**: A work plugin built outside the repository runs the tool without
the code plugin; the schema and the skill describe the procedure.

**Independent Test**: The quickstart's "Build".

- [ ] T025 [P] [US5] In feature 011's plugin table in
  `packages/backfire/src/backfire_tools/build.py`, add a second kind of
  entry, a per-plugin list of `packages/<name>` projects copied beside
  `backfire/` without `.venv` and `node_modules` (research.md R7), and list
  `doc-regions` and `wiki-consistency` in the work row; 011's own build tests
  keep passing. Add a test that builds into a temporary folder,
  installs offline from the locks and runs `check` on a synthetic instance
  with no code plugin present.
- [ ] T026 [US5] Write `plugins/work/skills/wiki-consistency/SKILL.md`: when
  to use it, the commands with the plugin-relative project path, the
  judgment step and the lint operation of
  [contracts/commands.md](contracts/commands.md), and what the agent reports
  to the user.
- [ ] T027 [US5] Extend feature 009's schema template
  `plugins/work/skills/wiki-raw-import/assets/AGENTS.md` with
  [contracts/pages.md](contracts/pages.md), keeping its raw rules; update
  feature 009's template test if it checks the text.
- [ ] T028 [US5] Ask the user to approve applying the extended schema to the
  default instance (a write outside the repository). After approval, update
  the instance's `AGENTS.md`, run `update` (the first `index.md` region),
  `check`, append one `log.md` entry and commit the instance; record only
  counts in this file.
- [ ] T029 [US5] Document the feature in `docs/architecture.md` (the Wiki
  consistency section: generators, the check before each instance commit,
  the judgment step, lint, cache budgets, what stays manual; the skill table,
  regenerated with `deno task doc-regions:update` if feature 008 made it a
  region), and add markitdown, qmd and PyYAML to
  `licenses/THIRD_PARTY_NOTICES.md` with source, version and license.

---

## Phase 8: Polish and Integration

- [ ] T030 Run the quickstart, `deno task verify` and `deno task docs:check`
  on the combined result; rerun `deno task workflow` with the same task and
  base; repair until they pass. Check SC-002 on a synthetic instance of 500
  pages.
- [ ] T031 SC-005: on a synthetic instance with one paragraph contradicting
  its source and one pair of contradicting pages, run `prepare` and send the
  requests three times; both must come back `contradicted` or `review` every
  time, and `backfire_compare` must confirm the pair. Record the results in
  this file.
- [ ] T032 Run feature 008's judgment step on this feature's repository
  changes, then the merge review for `develop`, favoring speed: fresh
  reviewers from the other provider for the Codex code and for main's prose,
  given only the scope and requirements; resolve findings; add the
  review-record commit and finish with `git flow feature finish
  wiki-consistency` from the `develop` worktree.

---

## Dependencies & Execution Order

- Nothing starts before the three gates hold; T001, then T002.
- T003 and T004 follow T002 and are independent of each other; T005 follows
  T004 (the model decision) and T006 follows T005; T007 is independent.
- T008 → T009 need T005.
- US1: T010 → T011; T012 after T002; T013 → T014 need T009, T011 and T012.
- US2: T015 → T016 and T017 → T018 are parallel after T005; T019 → T020 need
  T009, T016 and T018.
- US3: T021 → T022 need T020. US4: T023 needs T020.
- US5: T025 after T014; T026 and T027 can be written while workers work;
  T028 needs T014 and T027; T029 needs T026.
- T030 needs all implementation; T031 and T032 follow T030.

## Worker Assignment

| Worker | Tasks | Writable files |
| --- | --- | --- |
| Codex A | T008 to T014 | `packages/wiki-consistency/src/wiki_consistency/{instance,sources,lint,__main__}.py`, their tests and helper; `packages/doc-regions/src/`, `packages/doc-regions/tests/` for T012 only |
| Codex B | T015 to T018 | `src/wiki_consistency/{evidence,search}.py`, `src/wiki_consistency/search.mjs` and their tests |
| Codex C | T019 to T023 | `src/wiki_consistency/requests.py`, `tests/test_prepare.py`, `tests/test_boundary.py`, `tests/fixtures/`; the `convert`, `index` and `prepare` entries in `__main__.py` |
| Codex D | T007, T025 | `scripts/doctor.ts`, `scripts/doctor_test.ts`, `packages/backfire/src/backfire_tools/build.py` and its tests |
| Main | T001 to T006, T026 to T032 | shared files, the skill, the schema template, `docs/`, `licenses/`, the constitution, prose, Git, the instance |

Wave 1 runs Codex A, Codex B and Codex D's T007 in parallel. Wave 2 starts
after A and B finish: Codex C, who also adds the `convert`, `index` and
`prepare` entries to `__main__.py` (A creates it with `check` and `update`),
and Codex D's T025, whose test runs A's `check`. The workers share the module
interfaces in [data-model.md](data-model.md); Codex B keeps its fixtures in
its own test files, since Codex A owns `tests/conftest.py` and the instance
helper.

## Parallel Example

```text
After T006: Codex A takes T008 to T014; Codex B takes T015 to T018; Codex D
takes T007; main writes T026 and T027. After A and B finish: Codex C takes
T019 to T023; Codex D takes T025.
```

## Implementation Strategy

1. After the gates: T001 to T007.
2. MVP: User Story 1, so every instance commit is checked offline.
3. User Story 2, then 3 and 4.
4. Packaging, skill, schema and documentation; the default instance with the
   user's approval.
5. Verify, SC-005, judgment step, merge review, review record, finish.

## Notes

- 2026-09-28 (specification): specified, planned and broken into tasks by a
  Claude Code worker from the brief's section 3; no implementation. Blocked
  on the three gates above; the user answered the five Clarifications
  questions (all recommended options). Next: the orchestrator starts implementation after
  the gates hold.
- 2026-09-28 (handoff): coordination moved from the feature-linear-usage
  orchestrator to this worktree's own orchestrator; no worker was running and
  no user question was open. Feature 008's orchestrator agreed to add R8's
  three needs to `packages/doc-regions` (research.md R8); feature 011's
  orchestrator will send its build interface when its plan is committed.
  Next: wait for the three gates.
