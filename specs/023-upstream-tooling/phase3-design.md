# Phase 3 design: upstream workflow and import tooling

**Assumption.** Keep today’s workflow contract and current import rules. Use the pinned tools’ CLI/configuration where they replace a graph engine or a check result; keep local code where it binds results to this repository’s files, task plan, and working-tree state. The static dependency-cruiser config will describe the package manifests present when the swap lands, so future manifest/export changes need a config update.

## Recommendation

Use Turborepo 2.11.5 `--summarize` as the source for the just-completed `check` result, and dependency-cruiser 18.2.0’s CLI for TypeScript import rules and dependency queries. Use import-linter 2.15 with only built-in contracts for the Python package boundaries. Keep the local workflow router, difficulty scorer, path and snapshot guards, symbol query, plan validator, skill triggers, and verification history. This is a partial replacement: the upstream tools replace the check result and dependency-graph/rule engine, while the task-context and safety state remain local. [R: `specs/023-upstream-tooling/spec.md:108-132,211-223`; T: `crates/turborepo-cli/src/cli/args.rs:775-782`, `crates/turborepo-run-summary/src/tracker.rs:65-90,189-205`; D: `doc/cli.md:980-1017`, `doc/options-reference.md:317-347`]

The source pins and licenses are already recorded as Turbo 2.11.5 / MIT, dependency-cruiser 18.2.0 / MIT, and import-linter 2.15 / BSD-2-Clause. Turbo’s review found no high findings and requires telemetry off, agent guidance off, update notices off, credentials/config isolated, and private summaries. The dependency-cruiser review found no high finding and requires JSON configuration, a validated full commit ID for `--affected`, `GIT_OPTIONAL_LOCKS=0`, `--no-cache`, `--no-progress`, stdout output, and no secrets/network for untrusted changes. Import-linter’s review requires built-in contracts only and `--no-cache`; its Grimp 3.17 native wheel has a provenance gap, so pin approved wheel hashes and do not allow source-distribution fallback. [R: `specs/023-upstream-tooling/research.md:19-38`; S: `reports/R2-turborepo-lefthook.md:32-57`, `reports/R5-importlinter-bagit-depcruise.md:19-26,60-76,124-129,243-251,305-313`]

Evidence keys below use paths relative to these roots: **R** is `/home/choi-eunchang/workspaces/verbose-broccoli/feature-upstream-tooling`; **T** is `$SEC/turborepo-v2.11.5`; **D** is `$SEC/dependency-cruiser-v18.2.0`; **I** is `$SEC/import-linter-v2.15`; **S** is `$SEC/reports`. `$SEC` is `<scratch>/security`.

## Capability map

| Current exported capability | Upstream fit | Local code that remains | Old-only behavior and disposition |
|---|---|---|---|
| `buildWorkModeInstructions` | None. Turbo and dependency-cruiser do not provide repository instructions or the loop’s guidance. | Keep `scripts/workflow.ts:53-76`; it explains the workflow, verify, review, and difficulty contracts. | All project-specific instructions remain. No drop. [R: `scripts/workflow.ts:53-76`]
| `selectWorkMode` | None. `--affected` reports graph impact; it does not select DIRECT, DELEGATE, PARALLEL, or REVIEW from path count, changed lines, public entries, and plan errors. | Keep `scripts/workflow.ts:78-109`; continue to consume Git signals and `analyzePlan`. | Keep thresholds/review reasons and plan-scope escalation. No drop. [R: `scripts/workflow.ts:78-109`, `scripts/workflow_test.ts:64-116`]
| `assessDifficulty` | No upstream. The spec explicitly keeps this heuristic. | Keep `scripts/workflow.ts:120-175`. | Keep the five-level thresholds, reason, facts, and uncertainty result. No drop. [R: `scripts/workflow.ts:120-175`, `specs/023-upstream-tooling/spec.md:110-114,211-215`]
| `parseNameStatus`, `sumNumstatLines` | No direct substitute. Turbo summaries do not represent the Git status/numstat input used for routing and difficulty. Depcruiser’s `--affected` is graph impact, not a replacement for these records. | Keep `scripts/workflow.ts:178-210` and the Git collector. | Keep NUL-safe odd filenames, rename handling, binary `null`, and staged/unstaged accounting. No drop. [R: `scripts/workflow.ts:178-210,212-306`, `scripts/workflow_test.ts:118-205`]
| `inspectChanges` | Partial: static dependency-cruiser config can replace `importRules(root)` as the source of public API targets; `--affected <full-sha>` can report files changed since a base and their dependents. Neither replaces Git status, line counts, per-task scoring, nor route selection. | Keep `scripts/workflow.ts:308-397`; move public-entry target lookup into the small depcruiser adapter/config reader. Keep `collectSignals`. | Keep base resolution to a full commit, Git staged/unstaged/untracked changes, path statuses, difficulty, and public-entry review. Drop only automatic public-target discovery from arbitrary future manifests if adopting static rules (see below). [R: `scripts/workflow.ts:308-397`; D: `doc/cli.md:980-1017`; S: `reports/R5-importlinter-bagit-depcruise.md:247-250`]
| `repositoryFileSchema`, `listCodeFiles`, `getFileAccessError` | No complete upstream replacement. Dependency-cruiser scans roots but does not apply this repository’s selected-file schema, ESLint ignore list, or no-symlink write-scope policy. | Keep `scripts/workflow_files.ts:11-60`. | Keep canonical literal paths, supported-code suffix checks, ESLint exclusions, regular-file checks, and symlink-component rejection. No drop. [R: `scripts/workflow_files.ts:7-60`, `scripts/workflow_graph_test.ts:278-335`]
| `repositoryPathspec`, `runGit`, `snapshotWorkingTree` | No replacement. `--affected` invokes Git for a graph query but is not a content/mode snapshot or a concurrency guard. | Keep `scripts/workflow_git.ts:8,46-61,64-149`. | Keep hashing regular file bytes, mode, symlink target, index/status and revision; retain the before/after mutation check. No drop. [R: `scripts/workflow_git.ts:8,46-61,64-149`]
| `graphCommands` | No replacement for the user-facing menu. Update wording only if command names change. | Keep `scripts/workflow_graph.ts:17-40`. | Keep impact/symbol/policy help text. No drop. [R: `scripts/workflow_graph.ts:17-40`]
| `inspectGraph` | Strong partial replacement. Use dependency-cruiser CLI JSON output for the graph and configured rules. Use `--reaches <escaped-target-regex>` for a file’s transitive consumers and `--affected <full-sha>` for base-relative graph impact; `--focus` only considers direct neighbors and is not equivalent. `--reaches` and `--affected` are CLI options (`D: doc/options-reference.md:177-205,317-347; doc/cli.md:980-1017`). | Keep `scripts/workflow_graph.ts:42-69,71-101,103-173` for input validation, Git-versionable and ESLint-scoped source selection, edge-status labels, test-candidate matching, policy result shape, snapshot guard, and JSON workflow report. Replace `analyzeImportGraph` and the library `format` query with a small CLI adapter. `inspectSymbol` remains separate. | Keep local status distinctions (`UNRESOLVED`, `EXTERNAL`, `OUTSIDE_SCOPE`, `RESOLVED_LOCAL`) and the test-path heuristic; the CLI JSON supplies module/dependency data but not these repository labels. No intentional drop. [R: `scripts/workflow_graph.ts:42-101,103-173`; D: `doc/output-format.md:120-145`]
| `planSchema`, `PlanTask`, `PlanResult`, `analyzePlan` | Partial: dependency-cruiser `--reaches` can compute the import-impact set for each task’s escaped file-pattern union. | Keep strict schema, duplicate writable-file checks, file access validation, graph-error handling, task-pair intersection, and reasons in `scripts/workflow_plan.ts:11-88`; replace only graph construction/traversal. | Keep the “shared dependency blocks parallel work” policy and literal task scope. No drop. [R: `scripts/workflow_plan.ts:11-88`; D: `doc/options-reference.md:317-347`]
| `parseCleanCodeScope`, `selectSkills`, `announceSkillTriggers` | No upstream equivalent; spec says skill triggers stay. | Keep `scripts/workflow_skills.ts:27-53,90-127,129-212`. | Keep exact Clean Code scope intersection, review-code trigger, verify trigger, snapshot/idempotence receipts, and fail-to-REVIEW behavior. No drop. [R: `scripts/workflow_skills.ts:27-53,90-212`, `specs/023-upstream-tooling/spec.md:110-114,211-215`]
| `inspectSymbol` | No replacement in the selected upstream tools. Dependency-cruiser reports module edges, not definitions, references, or call hierarchy. | Keep `scripts/workflow_symbol.ts:13-171` and TypeScript Language Service use. | Keep local definitions/references and caller/callee locations, with the existing static-analysis limits. No drop. [R: `scripts/workflow_symbol.ts:13-171`; D: `doc/output-format.md:120-145`]
| `EvidenceRecord`, `evaluateVerification` | Partial: Turbo `--summarize` records run/task exit states and task graph. Run summary version `1` has an execution summary and task summaries; missing task exit code counts as failure. Summary JSON is written under `.turbo/runs/<id>.json`. [T: `crates/turborepo-run-summary/src/tracker.rs:53-90,189-205,418-431,808-844`; `src/task.rs:15-30,93-122`] | Keep `scripts/workflow_verify.ts:21-41,48-122,124-192,194-281` and `scripts/workflow-evidence.schema.json:1-80` for task/base/plan context, local STARTED/FINISHED lifecycle, dirty snapshot, log capture/hash, freshness, phases, failure streak, and lock. Add a small summary reader to `verify()` and bind its run ID, Turbo version, selected task statuses, and exit status to the local record. A `--summarize` run prints the summary path (`T: crates/turborepo-run-summary/src/execution.rs:118-120`); Turbo’s integration test checks it (`T: crates/turborepo/tests/run_summary.rs:50-58`). | Turbo replaces the per-check result source, not evidence-history semantics. Keep fail-closed behavior if summary is absent/malformed or disagrees with the parent process. No intentional drop in the recommended design. [R: `scripts/workflow_verify.ts:124-281`, `scripts/workflow_verify_test.ts:98-327`]
| `importRules`, `analyzeImportGraph` | Replace their dependency-cruiser library use with the pinned CLI and a JSON configuration. The CLI accepts JSON config and JSON/error reporters (`D: doc/cli.md:625-684,1460-1477`; `S: reports/R5-importlinter-bagit-depcruise.md:247,307,313`). | Delete `scripts/clean_architecture.ts`; put the fixed rules in `.dependency-cruiser.json`; keep a small CLI adapter for workflow graph/plan calls and public-entry extraction. The ordinary clean-architecture check can call the CLI directly. | Drop dynamic discovery/validation of future manifests and dynamic alias-conflict checks if no separate local manifest checker is retained. Static rules still enforce the checked-in rule set. Details follow. [R: `scripts/clean_architecture.ts:15-21,61-99,100-139,140-229,232-273`; `scripts/clean_architecture_test.ts:42-205,207-355`]
| `sha256` | No need for an upstream replacement; it is small and used by receipts. | Keep `scripts/hash.ts:3-11`; it remains used by `workflow_git.ts`, `workflow_verify.ts`, `workflow_skills.ts`, and `own_code.ts`. | No drop. [R: `scripts/hash.ts:3-11`, `scripts/workflow_git.ts:7,93,147-149`, `scripts/workflow_verify.ts:7,188-199`, `scripts/workflow_skills.ts:7,174`, `scripts/own_code.ts:8`]
| `own_code.ts` helpers `size`, `approvals` (no exports) | Out of these swaps. `scc` remains the counter. | Keep `scripts/own_code.ts:42-94` and its `check` task. | No drop. The script’s temporary archive is why this review did not run `npm run own-code`: `scripts/own_code.ts:102-110,134-135` creates and removes a temporary tree. [R: `scripts/own_code.ts:14-16,39-41,42-94,102-135`]

## Concrete swaps

### 1. Turborepo check evidence

Add `--summarize` to the root `check` script so the existing `npm run verify` → `workflow_verify` → `npm run check` path receives a summary for the same task run. The current scripts are `workflow`, `verify`, `check`, and `test` at `package.json:20-23,46,51`; `verify()` runs `npm run check` at `workflow_verify.ts:147-170`; root `turbo.json` runs checks as uncached dependencies at `turbo.json:165-180`. Turbo’s integration test proves `--summarize` prints and writes a run summary, including failed tasks (`T: crates/turborepo/tests/run_summary.rs:50-58,128-160`).

Proposed `package.json` values:

```json
{
  "check": "umask 077 && env -u TURBO_BINARY_PATH -u TURBO_TOKEN -u TURBO_TEAM -u TURBO_TEAMID -u VERCEL_ARTIFACTS_TOKEN -u VERCEL_ARTIFACTS_OWNER TURBO_TELEMETRY_DISABLED=1 NO_UPDATE_NOTIFIER=1 turbo run check --summarize",
  "test": "env -u TURBO_BINARY_PATH -u TURBO_TOKEN -u TURBO_TEAM -u TURBO_TEAMID -u VERCEL_ARTIFACTS_TOKEN -u VERCEL_ARTIFACTS_OWNER TURBO_TELEMETRY_DISABLED=1 NO_UPDATE_NOTIFIER=1 turbo run test"
}
```

In `turbo.json`, retain the existing `"agentGuidance": false` at line 3, add `"noUpdateNotifier": true` at the root, and preserve uncached checks. Add `/.turbo/runs/` to `.gitignore` next to the local execution evidence entries. Keep `npm run verify` unchanged. The repository instructions require `npm run verify` to record evidence, the finish hook runs it and fails the finish on nonzero, and the workflow compares snapshots around verify; ignoring the generated summaries prevents them appearing as new untracked inputs in the local snapshot (`R: AGENTS.md:47-52; scripts/git-flow-hooks/pre-flow-feature-finish:80-81; scripts/workflow.ts:487-520; scripts/workflow_git.ts:122-149; .gitignore:17-19`).

The npm command cannot itself guarantee empty Turbo/Vercel config directories. The CI/Orca verification launcher must point `TURBO_CONFIG_DIR_PATH` and `VERCEL_CONFIG_DIR_PATH` at empty per-job directories and assert the locked Turbo platform package exists; the R2 review says to unset the six listed token/team variables, disable telemetry, disable update notices, and keep raw summary files private (`S: reports/R2-turborepo-lefthook.md:44-57`). Keep `.turbo/runs/*.json` local and access-controlled; do not upload or commit raw summaries because they contain paths, commands, SCM state, task graphs, and environment names/hashes (`S: reports/R2-turborepo-lefthook.md:223-245`).

`workflow_verify.ts` should read the summary path printed by the *same* `npm run check` stdout, require Turbo version `2.11.5`, summary version `1`, non-null `execution`, zero run exit code/failures, and successful expected `check` tasks; require consistency with the child exit code and fail closed otherwise. The reviewed package contains versioned Rust serialization structs but no standalone run-summary JSON Schema in that package tree (search command in Verification); keep a small structural guard rather than assuming the summary is a formal JSON-Schema contract (`T: crates/turborepo-run-summary/src/tracker.rs:53-90,189-205`; task exit semantics: `src/task.rs:15-30`; summary path output: `src/execution.rs:118-120`). Save only approved summary fields/run ID in the local evidence record, not a second full copy.

Tests: keep all local lifecycle tests in `workflow_verify_test.ts` and adapt passing/failure fixtures to emit a summary. Add cases for missing summary, wrong version, malformed task list, unsuccessful task despite parent status, and mismatched parent/summary status. Keep coverage for task/plan/base separation, mid-run code changes, altered/missing logs, fail-closed records, interrupted runs, and serialization; those are local behaviors Turbo summaries do not encode (`R: scripts/workflow_verify_test.ts:98-327`). Keep `workflow_test.ts`, `workflow_plan_test.ts`, `workflow_graph_test.ts`, and `workflow_skills_test.ts`; they test behavior outside summary production (`R: scripts/workflow_test.ts:64-496; scripts/workflow_plan_test.ts:39-307; scripts/workflow_graph_test.ts:120-521; scripts/workflow_skills_test.ts:82-378`).

**Old-only verify behaviors:** task/base/plan-scoped context; SHA-256 plan and log binding; before/after working-tree snapshot; STARTED marker so interrupted runs supersede older passes; two-failure REVIEW threshold; local log path/content and integrity check; malformed/unpaired evidence rejection; and serialized concurrent verification. Keep these in the recommended swap because Turbo’s summary has a run/task graph and result, not this workflow state (`R: scripts/workflow_verify.ts:22-41,59-122,124-192,194-281; scripts/workflow-evidence.schema.json:1-80`; Turbo fields: `T: crates/turborepo-run-summary/src/tracker.rs:65-90; src/task.rs:93-122`). If these were all deleted, this proposal would be shorter but `npm run verify`, skill guidance, and the finish hook would lose their current VERIFIED/REPAIR/REVIEW contract; that alternative is not included in the estimate (`R: scripts/workflow.ts:487-533; scripts/workflow_skills.ts:116-124,197-210; scripts/git-flow-hooks/pre-flow-feature-finish:80-81`).

### 2. TypeScript dependency graph and import rules

Add a static `.dependency-cruiser.json`, preferably JSON rather than executable `.cjs` configuration (the review says JSON avoids the config-code execution finding). Carry over the existing `forbidden` rule objects/names for `no-cycles`, domain/application direction, `no-feature-internals`, `no-package-to-plugin`, `no-node-in-inner-layers`, `no-unresolved-local-imports`, and `no-io-packages-in-inner-layers`. Keep `tsPreCompilationDeps`, `exclude: ^scripts/vendor/|\\.md$`, and the current input roots/exclusion boundary. Add explicit current `public-api:<owner>` rules from the manifests at implementation time. The current code’s exact rule names and shapes are at `clean_architecture.ts:105-139,154-164,215-228`; its graph options are at `232-255`; the JSON schema supports these rule shapes and TypeScript config options (`D: doc/cli.md:625-684; doc/options-reference.md:635-665`).

Suggested CLI commands:

```sh
# CI/import-policy task: error reporter, nonzero on an error, no cache/progress.
env GIT_OPTIONAL_LOCKS=0 depcruise --config .dependency-cruiser.json --no-cache --no-progress --output-type err --exit-code packages plugins scripts tests

# Whole-base graph impact: BASE must already be resolved and validated as a full hexadecimal commit ID.
env GIT_OPTIONAL_LOCKS=0 depcruise --config .dependency-cruiser.json --no-cache --no-progress --output-type json --affected "$BASE_SHA" packages plugins scripts tests

# Selected-file impact; quote the escaped repository-relative regex and pass args without a shell.
env GIT_OPTIONAL_LOCKS=0 depcruise --config .dependency-cruiser.json --no-cache --no-progress --output-type json --reaches '^plugins/code/src/file\\.ts$' packages plugins scripts tests
```

`--affected` uses Git-relative changes plus transitive dependents and must receive the resolved full SHA; `--reaches` is the transitive target query; `--focus` is direct-neighbor-only (`D: doc/cli.md:980-1017; doc/options-reference.md:177-205,317-347; S: reports/R5-importlinter-bagit-depcruise.md:247-250`). For `inspectGraph`, use one normal JSON graph call for policy/import edges and a `--reaches` call for dependents; continue to filter to `listCodeFiles()` and map output to the current API. For each plan, pass one safely escaped union regex for its selected files to `--reaches`, then keep the local intersection/reason logic. JSON output includes modules and violation summary (`D: doc/output-format.md:120-145`). Use `--exit-code` with the error reporter for the direct policy task; leave JSON query output on stdout for local parsing (`D: doc/cli.md:1460-1477`).

Concrete files and commands:

- Add `.dependency-cruiser.json`; preserve rule names so graph errors still name the violated rule.
- Add `scripts/workflow_depcruise.ts` as a small `execFile`/JSON adapter for graph and plan queries. Change `workflow_graph.ts`, `workflow_plan.ts`, and the public-entry lookup in `workflow.ts` to use it. The adapter must pass an argument array, never interpolate a shell command; accept only a full validated SHA for `--affected`; use `GIT_OPTIONAL_LOCKS=0`, `--no-cache`, `--no-progress`, and stdout (`S: reports/R5-importlinter-bagit-depcruise.md:247-251,305-313`).
- Change `package.json` `clean-architecture` to the error-reporter command above. Add a root `python:imports` command below and a separate Turbo task. Keep `check` reaching the architecture task through its existing `//#clean-architecture` dependency (`R: package.json:28,46,50; turbo.json:33,47,165-180`).
- Delete `scripts/clean_architecture.ts`; remove its imports from workflow/graph/plan. Replace `scripts/clean_architecture_test.ts` with `scripts/dependency_cruiser_test.ts`, point the existing `test:clean-architecture` script at that CLI contract test, and keep the existing Turbo test target name. Current workflow graph and plan tests remain and must exercise CLI-backed outcomes (`R: scripts/clean_architecture_test.ts:42-205,207-355; scripts/workflow_graph_test.ts:120-335,521-545; scripts/workflow_plan_test.ts:39-210`).

Dependency-cruiser’s reported JSON can replace graph construction and direct-import/reachability computation, but not repository filtering, custom result shaping, test-file classification, snapshot guards, or TypeScript language-service symbol results (`R: scripts/workflow_graph.ts:42-101,103-173; scripts/workflow_plan.ts:29-87; scripts/workflow_symbol.ts:13-171`). The existing policy’s local-only behaviors are: reading every future plugin/package manifest; creating a public API rule from each future manifest’s `exports`; rejecting public export paths outside an owner; synthesizing local/external aliases from dependencies/imports; and rejecting unsupported targets and alias collisions (`R: scripts/clean_architecture.ts:15-58,61-99,140-214`). The proposed static config drops that automatic manifest/export/alias validation; retain only entries for manifests present at implementation time, and add a focused config/CLI fixture proving each fixed rule. The standalone command also loses the wrapper report shape `{violations, error, totalCruised}` when switched to dependency-cruiser’s `err` reporter; retain a thin formatter only if that output is consumed (`R: scripts/clean_architecture.ts:260-273; D: doc/cli.md:1460-1474`). If automatic updates or that report shape are required, keep only the needed glue; do not silently rebuild the current generator.

### 3. Python import boundaries

The existing uv workspace contains `packages/*`; the `backfire` distribution exposes `backfire`, `backfire_tools`, and `backfire_education`; `wiki-consistency` depends on `backfire[education]` and `doc-regions`. Existing Python edges include `wiki_consistency` → `backfire`, `backfire_education`, and `doc_regions`, plus `backfire_education` → `backfire` (`R: pyproject.toml:10-11; packages/backfire/pyproject.toml:9-14,29-31; packages/wiki-consistency/pyproject.toml:9-15,21-29; packages/wiki-consistency/src/wiki_consistency/rules.py:14-21; packages/backfire/src/backfire_education/pseudonymize.py:7-10`). A read-only file inventory showed exactly these top-level source roots: `backfire`, `backfire_tools`, `backfire_education`, `doc_regions`, `wiki_consistency` (command/output in Verification). A package-layer contract is therefore the useful current boundary.

Add `import-linter==2.15` to `packages/wiki-consistency/pyproject.toml`’s `dev` group and lock its reviewed compatible wheels in `uv.lock`; keep the built-in contract set only and avoid the sdist. Put this config in the root `pyproject.toml` because it can configure multiple importable root packages and supports TOML (`I: docs/get_started/configure.md:25-68`; built-ins: `src/importlinter/application/use_cases.py:365-377`; security: `S: reports/R5-importlinter-bagit-depcruise.md:66-68,126-129,311-313`).

```toml
[tool.importlinter]
root_packages = [
  "backfire",
  "backfire_tools",
  "backfire_education",
  "doc_regions",
  "wiki_consistency",
]

[[tool.importlinter.contracts]]
name = "Workspace package layers"
type = "layers"
layers = [
  "wiki_consistency",
  "backfire_education | backfire_tools",
  "backfire | doc_regions",
]

[[tool.importlinter.contracts]]
name = "Python package sibling cycles"
type = "acyclic_siblings"
ancestors = [
  "backfire",
  "backfire_tools",
  "backfire_education",
  "doc_regions",
  "wiki_consistency",
]
```

`|` makes packages within a layer independent; higher layers can depend on lower layers. `acyclic_siblings` catches cycles across sibling modules/packages and descends into subpackages (`I: docs/contract_types/layers.md:258-275,277-304; docs/contract_types/acyclic_siblings.md:1-22`). Run it with:

```sh
uv run --project packages/wiki-consistency --frozen --offline --no-sync lint-imports --config pyproject.toml --no-cache
```

Add `python:imports` to `package.json` with that command; add `//#python:imports` to `turbo.json` with `"cache": false`; add it to `verbose-broccoli-python#check.dependsOn` beside `//#clean-architecture`. Keep `wiki-consistency#test` and add a synthetic violation test there to prove that a forbidden Python import fails; the normal import contract command must also remain in `check` (`R: package.json:42-46; turbo.json:165-184`; `I: docs/get_started/configure.md:46-68`).

Rules with no exact Python equivalent today: `no-node-in-inner-layers` (Node core-module categories), `no-io-packages-in-inner-layers` (the JS/TS `domain` and `application` paths and named npm I/O packages), `no-package-to-plugin` (the current JS/TS `packages/` → `plugins/` rule), `public-api:<owner>` (dynamic `package.json` `exports` targets), and `no-unresolved-local-imports` as currently expressed against dependency-cruiser resolution metadata. The current Python roots are package-level modules, not those JS path layers, and import-linter’s built-ins are only `forbidden`, `layers`, `independence`, `protected`, and `acyclic_siblings`; they do not provide the existing package.json export generator or Node/npm-specific rule (`R: scripts/clean_architecture.ts:105-139,140-170,215-228; Python inventory/edges in Verification; I: src/importlinter/application/use_cases.py:365-377`). `no-cycles` has a partial Python analogue through `acyclic_siblings`, but its scope is cycles between sibling modules and descendants, not a byte-for-byte translation of dependency-cruiser’s arbitrary module-cycle rule (`R: scripts/clean_architecture.ts:105-107; I: docs/contract_types/acyclic_siblings.md:5-22`). The domain/application direction and feature-internal rules have no current Python directory structure to enforce (`R: directory inventory in Verification; scripts/clean_architecture.ts:108-126`).

## Own-code estimate (scc 4.1.0 Code lines)

The point estimate counts source Code lines as CHE-42 does; tests and JSON/TOML config are excluded (`R: scripts/own_code.ts:14-16,39-41,73-79; docs/architecture.md:111-123`). A direct read-only run of `tools/scc/.venv/bin/scc --by-file --format json --no-complexity` reported `scripts/clean_architecture.ts` = 267 Code lines and `scripts/workflow_verify.ts` = 273 Code lines; `scc --version` reported 4.1.0 (exact command and selected output in Verification).

| Swap | Code lines removed | Code lines added (estimate) | Net | Count basis |
|---|---:|---:|---:|---|
| Turbo summary as check-result source | 0 | ~24 | +24 | Small fail-closed summary reader and local-record binding in `workflow_verify.ts`; keep its 273-line lifecycle/state logic. JSON schema edits do not count. |
| Dependency-cruiser CLI/config | 267 | ~35 | −232 | Delete `clean_architecture.ts`; add one shared CLI adapter used by graph, plan, and public-entry lookup. `.dependency-cruiser.json` and command edits do not count. |
| Python import-linter | 0 | 0 | 0 | TOML configuration, pyproject pin, and lock data are not scc Code lines; no custom linter is proposed. |
| **Total** | **267** | **~59** | **~−208** | Point estimate; implementation call-site details may shift the 35-line adapter estimate. |

The estimate is the proposed swap delta, not the branch-wide own-code total. `npm run own-code` was not run because its implementation creates, extracts, then deletes a temporary Git archive (`scripts/own_code.ts:102-110,134-135`); that would cross the task’s write boundary. It is the branch-wide check to run after implementation in its authorized workflow.

## Risks and old-only behaviors to decide

1. **Workflow verify / finish gate.** `npm run verify` means the summary must correspond to the `npm run check` child in that invocation; do not select “latest summary” by directory scan alone. Use the printed path and reject missing, malformed, stale, wrong-version, or inconsistent status. The finish hook gates feature finish on `npm run verify`, so a parser mistake can either block a valid finish or, worse, certify a check it did not run (`R: package.json:20-23,46; scripts/workflow_verify.ts:147-170,220-251; scripts/git-flow-hooks/pre-flow-feature-finish:80-81; T: crates/turborepo/tests/run_summary.rs:50-58`).
2. **Loop evidence does not come from Turbo.** Turbo lacks task ID, plan hash, resolved workflow baseline, staged/unstaged/untracked dirty hash, STARTED/FINISHED recovery, log hash, and serialized per-task workflow history. Removing these loses the current VERIFIED/REPAIR/REVIEW loop even though Turbo’s individual check result is sound (`R: scripts/workflow_verify.ts:22-41,124-192,194-281; T: crates/turborepo-run-summary/src/tracker.rs:65-90; src/task.rs:93-122`).
3. **Summary privacy and generated files.** Turbo summaries contain commands, paths, SCM data, task graphs, and environment names/hash pairs; keep them local, private, ignored, and out of public artifacts/commits. Root `turbo.json` already disables agent guidance; add the no-update setting and set both control variables in every Turbo invocation (`S: reports/R2-turborepo-lefthook.md:41-57,223-245`; `R: turbo.json:3; .gitignore:17-19`). A killed Turbo process may not reach the summary save path, so absence must remain a failed/incomplete verification (`T: crates/turborepo-run-summary/src/tracker.rs:418-431,827-844`).
4. **Static TypeScript configuration drift.** Static public API rules stop auto-tracking new/changed `package.json` exports and stop rejecting unsupported/conflicting manifest aliases. The existing tests explicitly cover those generator properties; decide whether that loss is acceptable or retain a narrowly scoped manifest checker (`R: scripts/clean_architecture.ts:61-99,140-214; scripts/clean_architecture_test.ts:188-205,295-355`).
5. **CLI behavior and filesystem boundary.** `--affected` uses Git and must receive a validated full SHA with `GIT_OPTIONAL_LOCKS=0`; JSON stays on stdout and config stays JSON. Dependency-cruiser follows symlinked directories when gathering initial sources, so retain the current no-symlink file checks and reject symlinked scan roots in tests (`S: reports/R5-importlinter-bagit-depcruise.md:247-251,307-313`; `R: scripts/workflow_files.ts:37-60`; D: `src/extract/gather-initial-sources.mjs:48-72`).
6. **Python contract coverage and supply chain.** The proposed layers follow the observed import edges but will need review if new Python packages/edges are added. Import-linter must stay built-in-only and `--no-cache`; Grimp’s 3.17 platform wheel must be hash-pinned without sdist fallback (`R: packages/wiki-consistency/src/wiki_consistency/rules.py:14-21; packages/backfire/src/backfire_education/pseudonymize.py:7-10; S: reports/R5-importlinter-bagit-depcruise.md:66-68,126-129,311-313`).

The current old-only behaviors and recommendations are therefore: keep the local verify lifecycle/history; keep Git/work-mode/difficulty/path/snapshot/plan/symbol/skill behavior; and decide explicitly whether dynamic TypeScript manifest discovery and alias validation can be dropped. The proposed design intentionally drops only that dynamic manifest automation; the fixed current policy remains in configuration and the Python policy is new (`R: scripts/workflow.ts:53-397; scripts/workflow_files.ts:11-60; scripts/workflow_git.ts:46-149; scripts/workflow_plan.ts:11-88; scripts/workflow_symbol.ts:13-171; scripts/workflow_skills.ts:27-212; scripts/clean_architecture.ts:61-229`).

## Verification and scope

Read the required spec and research first, then read the listed local source/tests, the tagged tool source, and both security reports. No repository files were edited; no tests, `npm run workflow`, `npm run verify`, or `npm run own-code` were run. The allowed read-only counter and inventory commands were:

```text
$ tools/scc/.venv/bin/scc --version
scc version 4.1.0

Selected output:

$ tools/scc/.venv/bin/scc --by-file --format json --no-complexity scripts/workflow.ts scripts/workflow_files.ts scripts/workflow_git.ts scripts/workflow_graph.ts scripts/workflow_plan.ts scripts/workflow_skills.ts scripts/workflow_symbol.ts scripts/workflow_verify.ts scripts/clean_architecture.ts scripts/hash.ts scripts/own_code.ts
... scripts/clean_architecture.ts: Code 267
... scripts/workflow_verify.ts: Code 273

$ rg --files packages/backfire/src packages/doc-regions/src packages/wiki-consistency/src | awk -F/ '{print $1 "/" $2 "/" $3 "/" $4}' | sort -u
packages/backfire/src/backfire
packages/backfire/src/backfire_education
packages/backfire/src/backfire_tools
packages/doc-regions/src/doc_regions
packages/wiki-consistency/src/wiki_consistency

$ find packages/backfire/src packages/doc-regions/src packages/wiki-consistency/src -type d -print | sort
packages/backfire/src
packages/backfire/src/backfire
packages/backfire/src/backfire/tools
packages/backfire/src/backfire_education
packages/backfire/src/backfire_tools
packages/backfire/src/backfire_tools/acceptance
packages/doc-regions/src
packages/doc-regions/src/doc_regions
packages/wiki-consistency/src
packages/wiki-consistency/src/wiki_consistency

Relevant matches from the read-only Python import search:

packages/wiki-consistency/src/wiki_consistency/rules.py:14-21 imports backfire, backfire_education, and doc_regions
packages/wiki-consistency/src/wiki_consistency/sources.py:7-9 imports doc_regions and wiki_consistency
packages/backfire/src/backfire_education/pseudonymize.py:7-10 imports backfire

$ rg --files crates/turborepo-run-summary | rg 'schema|json'
(no output; exit status 1, no matching run-summary schema file in that package tree)
```

The final checkout status command and output were:

```text
$ git status --short --branch
## feature/upstream-tooling
 M packages/wiki-consistency/src/wiki_consistency/search.py
 M packages/wiki-consistency/tests/test_prepare.py
 M packages/wiki-consistency/tests/test_search.py
```

The first-pass status listed the shared-worktree edits above; this follow-up did not touch them. The final read-only `git status --short --branch` returned only `## feature-upstream-tooling`, so the checkout had no current worktree modifications at that point. Read-only `rg -o -F` checks found the Alternative B heading and comparison-row labels. No tests, `npm run verify`, or `npm run own-code` ran.

## Alternative B: maximal replacement

This option makes the Turbo run summary the only durable check evidence and sends dependency-cruiser output to the workflow caller with minimal formatting. It still keeps `assessDifficulty`, `selectWorkMode`, the skill selection and announcement path, and the Git/path safety checks; those behaviors have no upstream replacement or are not supplied by the two graph tools (`R: scripts/workflow.ts:53-175,308-397; scripts/workflow_skills.ts:27-53,90-212; scripts/workflow_files.ts:11-60; scripts/workflow_git.ts:46-149`).

### Commands and files

Keep `npm run verify` as the workflow entry point so `--verify` still makes the verification-before-completion skill trigger. Change `check` to invoke Turbo with `--summarize` and the R2 controls; leave the child exit status as the gate. Turbo writes a versioned summary under `.turbo/runs/` and reports its path, and its run summary records task execution results (`R: package.json:20-23,46; T: crates/turborepo-run-summary/src/tracker.rs:53-90,189-205,418-431,808-844; crates/turborepo-run-summary/src/execution.rs:118-120; crates/turborepo/tests/run_summary.rs:50-58,128-160`).

```json
{
  "verify": "npm run workflow -- --verify",
  "check": "umask 077 && env -u TURBO_BINARY_PATH -u TURBO_TOKEN -u TURBO_TEAM -u TURBO_TEAMID -u VERCEL_ARTIFACTS_TOKEN -u VERCEL_ARTIFACTS_OWNER TURBO_TELEMETRY_DISABLED=1 NO_UPDATE_NOTIFIER=1 turbo run check --summarize",
  "clean-architecture": "env GIT_OPTIONAL_LOCKS=0 depcruise --config .dependency-cruiser.json --no-cache --no-progress --output-type err --exit-code packages plugins scripts tests"
}
```

Add `"noUpdateNotifier": true` beside the existing `"agentGuidance": false` in `turbo.json`. Keep the check tasks uncached, add `/.turbo/runs/` to `.gitignore`, and configure the launcher to use empty per-job `TURBO_CONFIG_DIR_PATH` and `VERCEL_CONFIG_DIR_PATH` directories. R2 requires telemetry and update notices off, credentials/config isolated, and run summaries kept private because they include paths, commands, task/SCM details, and environment names or hashes (`R: turbo.json:3,165-180; .gitignore:17-19; S: reports/R2-turborepo-lefthook.md:32-57,223-245`).

Replace `scripts/workflow_verify.ts` with a thin reader that streams the current `npm run check` output through, buffers only the summary-path line printed by that invocation, then reads that file. Require the path to be under the worktree’s `.turbo/runs/`; accept only Turbo 2.11.5 / summary version 1 with non-null `execution`, zero `execution.failed`, and zero summary and child exit codes; treat a missing, malformed, wrong-version, or nonzero result as failure. Do not scan for the latest summary or write a second local record. Delete `scripts/workflow-evidence.schema.json`; this drops the JSONL lifecycle, persistent log/hash, local evidence schema, history and lock while using Turbo’s own run summary as the evidence (`R: scripts/workflow_verify.ts:30-57,59-122,124-192,194-281; scripts/workflow-evidence.schema.json:1-80; scripts/workflow.ts:501-507,535-568; T: crates/turborepo-run-summary/src/tracker.rs:53-90,189-205; crates/turborepo-run-summary/src/execution.rs:27-46,118-120; crates/turborepo/tests/run_summary.rs:50-58,128-160`).

For graph work, add the same static `.dependency-cruiser.json` proposed in A and reuse its small argument-array CLI adapter for plan queries. Use `--reaches` for transitive dependents, `--affected "$BASE_SHA"` for changes since the already-resolved full commit SHA, and the `err` reporter plus `--exit-code` for policy. Dependency-cruiser supports JSON and error reporters, `--reaches`, and `--affected`; the review requires a full SHA for `--affected`, JSON config, no cache, no progress output, and `GIT_OPTIONAL_LOCKS=0` (`D: doc/options-reference.md:317-347; doc/cli.md:980-1017,1460-1477; doc/output-format.md:120-145; S: reports/R5-importlinter-bagit-depcruise.md:243-251,305-313`).

```sh
env GIT_OPTIONAL_LOCKS=0 depcruise --config .dependency-cruiser.json --no-cache --no-progress --output-type json --reaches '^plugins/code/src/file\.ts$' packages plugins scripts tests
env GIT_OPTIONAL_LOCKS=0 depcruise --config .dependency-cruiser.json --no-cache --no-progress --output-type json --affected "$BASE_SHA" packages plugins scripts tests
env GIT_OPTIONAL_LOCKS=0 depcruise --config .dependency-cruiser.json --no-cache --no-progress --output-type err --exit-code packages plugins scripts tests
```

Delete `workflow_graph.ts`’s local graph builder/result wrapper and route these CLI results directly from `workflow.ts`. Keep the repository-relative path and symbol-coordinate checks already in `workflow.ts`, `getFileAccessError`, and the outer workflow snapshot guard. Keep `workflow_symbol.ts`: dependency-cruiser gives module edges, not TypeScript definitions, references, or calls; feed it the JSON graph when `--graph symbol` is selected (`R: scripts/workflow.ts:430-499,487-518; scripts/workflow_files.ts:11-60; scripts/workflow_graph.ts:103-173; scripts/workflow_symbol.ts:13-171; D: doc/output-format.md:120-145`). The outer before/after guard remains; it is separate from the per-check snapshots being deleted (`R: scripts/workflow.ts:487-518; scripts/workflow_git.ts:101-149`).

In `workflow_plan.ts`, replace only the graph construction and per-task query block with one CLI `--reaches` query per task. Build an anchored escaped union from each task’s literal files, take the returned module-source sets as the affected sets, and keep the local intersection. Keep `planSchema`, duplicate write detection, file access checks, graph-error failure, overlap reasons, and work-mode choice because dependency-cruiser does not accept workflow task plans or decide whether tasks can run in parallel (`R: scripts/workflow_plan.ts:11-51,52-87; scripts/workflow.ts:308-397; D: doc/options-reference.md:317-347`).

For `clean_architecture.ts`, use the same fixed JSON rule config and direct `clean-architecture` command described in A; delete the TypeScript implementation. Reuse A’s built-in-only import-linter TOML contracts and `python:imports` command unchanged, so this option adds no Python code and does not change the listed Python rule gaps (`R: scripts/clean_architecture.ts:105-139,154-164,215-255; scripts/clean_architecture_test.ts:42-205,207-355; this report, “Python import boundaries”; I: src/importlinter/application/use_cases.py:365-377; S: reports/R5-importlinter-bagit-depcruise.md:66-68,126-129,311-313`).

### Caller and test changes

In `workflow.ts`, replace `evaluateVerification` with the `npm run check` child call, remove `loop.phase` and failure-streak mode routing, and report the child status. Keep `inspectChanges` and `selectWorkMode`; route `REVIEW` when the graph policy command fails. Keep the outer snapshot comparison and selected mode path, but remove `loop` phase/history fields and instructions that claim local evidence exists (`R: scripts/workflow.ts:308-397,487-520,535-568`). The git-flow feature-finish hook stays unchanged: it runs `npm run --silent verify` and rejects a nonzero result (`R: scripts/git-flow-hooks/pre-flow-feature-finish:80-81`).

Keep the verify skill trigger in `workflow_skills.ts:116-124`, but change its reason from “read the actual `--verify` result and logs” to “read the Turbo summary and command exit status.” Keep skill announcement receipts and its separate snapshot guard; those are not verification-evidence records (`R: scripts/workflow_skills.ts:129-212; scripts/workflow_skills_test.ts:100-139`). Update `AGENTS.md:47-52` to say `npm run verify` must pass and leaves the Turbo summary as evidence. Update `docs/architecture.md:58-63` to describe workflow mode selection, the direct graph queries, skill triggers, and Turbo-backed verification. `package.json` keeps the `verify` and `test:workflow` entries, changes `check` and `clean-architecture`, and points `test:clean-architecture` to A’s replacement contract test; `turbo.json` adds the notifier setting and retains the uncached check graph (`R: AGENTS.md:47-52; docs/architecture.md:30-63; package.json:20-28,46,50-51; turbo.json:3,165-184`).

Tests: delete the lifecycle-specific `workflow_verify_test.ts` cases for reused evidence, task/base/plan history, snapshots, log integrity, malformed JSONL, interrupted STARTED runs, streaks, and serialization. Replace them with summary-reader checks for the current invocation’s path, version and status, plus child exit-status propagation and missing/malformed summary failure (`R: scripts/workflow_verify_test.ts:98-327; scripts/workflow.ts:501-507,565-568; T: crates/turborepo-run-summary/src/tracker.rs:53-90,189-205; crates/turborepo-run-summary/src/execution.rs:27-46,118-120; crates/turborepo/tests/run_summary.rs:50-58,128-160`). Replace `workflow_graph_test.ts` assertions for local status labels, test candidates, custom report fields, and graph-local snapshots; keep/add tests for path/symlink rejection, raw output pass-through, policy exit status, full-SHA `--affected`, and the symbol adapter (`R: scripts/workflow_graph_test.ts:120-199,201-276,278-335; scripts/workflow.ts:430-473; scripts/workflow_symbol.ts:13-171`). Keep the workflow plan tests for disjoint/overlapping affected sets, duplicate writes, missing or unsupported files, and symlink aliases, but run their fixtures through the CLI adapter (`R: scripts/workflow_plan_test.ts:39-229`). Keep difficulty/mode tests and skill-trigger tests; update only the verify-trigger wording and `workflow.ts` report expectations (`R: scripts/workflow_test.ts:64-496; scripts/workflow_skills_test.ts:100-139`). Replace `clean_architecture_test.ts` with A’s fixed-config/CLI contract tests; delete tests that assert automatic manifest/export discovery and alias conflict checking (`R: scripts/clean_architecture_test.ts:42-205,207-355`). Test source lines do not count toward the scc Code estimate (`R: scripts/own_code.ts:14-16,39-41,73-79`).

### Behaviors B drops and risks

**Verify lifecycle:** B drops task/base/plan-separated reusable history; `STARTED`/`FINISHED` pairing and interrupted-run recovery; captured stdout/stderr logs and SHA-256 integrity; per-check before/after content snapshots; `IMPLEMENT`/`REPAIR`/`VERIFIED`/`REVIEW` phases; the two-failure REVIEW threshold; malformed/unpaired JSONL rejection; and the lock that serializes concurrent checks. These are implemented by `workflow_verify.ts` and covered by `workflow_verify_test.ts`; Turbo stores task/run outcomes but not this workflow history (`R: scripts/workflow_verify.ts:30-41,59-122,124-192,194-281; scripts/workflow_verify_test.ts:98-327; T: crates/turborepo-run-summary/src/tracker.rs:65-90; src/task.rs:93-122`). The skill announcement’s own snapshot and idempotence receipt remain; only the separate verification lifecycle is removed (`R: scripts/workflow_skills.ts:129-212`).

The current loop’s `VERIFIED` mode and “two consecutive failures” review escalation rely on `evaluateVerification` returning the latest matching local history record. B removes that reuse: a plain `workflow` call no longer proves that earlier checks cover this task/base/plan or selects REVIEW from a stored failure streak; each `--verify` run must stand on its current Turbo child status (`R: scripts/workflow_verify.ts:220-277; scripts/workflow.ts:501-520,559-567`).

**Graph and plan presentation:** B drops `graphCommands` help, indexed-file counts, custom `{imports, dependents, test_candidates}` mapping, `UNRESOLVED`/`EXTERNAL`/`OUTSIDE_SCOPE`/`RESOLVED_LOCAL` labels, the test-name heuristic, the `policy: {status, errors, violations}` wrapper, limitation text, and the graph-local snapshot. It passes dependency-cruiser’s own JSON or `err` output through instead. The plan still has task validation and intersection logic, but exact local graph-error reason text may become the CLI’s error text (`R: scripts/workflow_graph.ts:17-40,42-69,71-101,103-173; scripts/workflow_plan.ts:11-51,52-87; D: doc/output-format.md:120-145`).

**Dynamic TypeScript policy:** B has A’s same loss of future-manifest scanning, package-export target generation, unsupported-export rejection, and alias conflict detection. Static rules cover only the checked-in config; adding or changing package exports requires updating it (`R: scripts/clean_architecture.ts:15-58,61-99,140-214; scripts/clean_architecture_test.ts:188-205,295-355`). **No new old-only Python behavior is dropped:** A’s Python gaps and contract limits remain as already listed in “Python import boundaries” (`R: scripts/clean_architecture.ts:105-139,140-170,215-228; I: src/importlinter/application/use_cases.py:365-377`).

The finish gate still has a straightforward failure condition: the same `npm run verify` invoked by the hook must run the check child, read that invocation’s summary, and propagate failure from either source. If the wrapper returns zero without starting Turbo, the hook can finish without checks; test this caller contract. Turbo’s tracker only warns if writing the summary fails, so the reader must fail closed when the path is missing or unreadable even if the child exits zero. Do not accept a stale summary. Unlike A, B has no local code-state hash, log integrity check, or history lock; concurrent invocations have no serialized workflow record. The outer workflow snapshot still catches a working-tree change during its own command, but there is no separately reusable proof tied to a task, plan, or base (`R: scripts/git-flow-hooks/pre-flow-feature-finish:80-81; scripts/workflow.ts:487-518; scripts/workflow_verify.ts:194-281; T: crates/turborepo-run-summary/src/tracker.rs:418-431,827-844; S: reports/R2-turborepo-lefthook.md:223-245`). Raw summaries are sensitive files, so keep `.turbo/runs/` private and ignored; they are execution evidence, not a signed attestation (inference from Turbo serializing and writing JSON without a signature step in the cited path) (`R: .gitignore:17-19; T: crates/turborepo-run-summary/src/tracker.rs:827-844; S: reports/R2-turborepo-lefthook.md:223-245`). `--affected` also depends on the validated full base commit being available to Git; keep argument-array invocation and the R5 `--no-cache`/Git controls (`D: doc/cli.md:980-1017; S: reports/R5-importlinter-bagit-depcruise.md:247-251,305-313`).

### Own-code estimate for B

Deleted-file counts use the read-only `scc 4.1.0` values already reported above (`workflow_verify.ts` 273 Code, `workflow_graph.ts` 168 Code, `clean_architecture.ts` 267 Code). The additional removals in `workflow.ts` and `workflow_plan.ts` are approximate source-line estimates for removed lifecycle/report glue and local graph construction; additions are estimated Code lines for the thin child runner and shared dependency-cruiser invocation adapter. Tests and JSON/TOML/package config do not count (`R: scripts/workflow.ts:487-568; scripts/workflow_plan.ts:52-87; scripts/own_code.ts:14-16,39-41,73-79`; direct scc command/output in Verification).

| B part | Code lines removed | Code lines added | Estimated net | Basis |
|---|---:|---:|---:|---|
| Turbo summary replaces local verification lifecycle | ~288 | ~30 | ~−258 | 273 from `workflow_verify.ts` plus about 15 obsolete loop/report lines in `workflow.ts`; thin same-run summary reader and status call (`R: scripts/workflow_verify.ts:124-281; scripts/workflow.ts:501-520,535-568`). |
| Raw dependency-cruiser graph output | ~184 | ~25 | ~−159 | 168 from `workflow_graph.ts` plus about 16 caller/result-shaping lines; thin CLI route. `workflow_symbol.ts` stays (`R: scripts/workflow_graph.ts:17-173; scripts/workflow.ts:487-500,535-568; scripts/workflow_symbol.ts:13-171`). |
| Plan query uses `--reaches` module sets | ~19 | 0 incremental | ~−19 | Remove local graph setup/query; reuse the shared adapter while retaining task checks/intersection (`R: scripts/workflow_plan.ts:11-87`). |
| Dependency-cruiser import-policy swap | 267 | 35 | −232 | Delete `clean_architecture.ts`; the shared 35-line CLI adapter serves workflow graph/plan. Static JSON config and direct check command are not Code lines (`R: scripts/clean_architecture.ts:15-273; D: doc/cli.md:625-684`). |
| Python import-linter | 0 | 0 | 0 | Same built-in contracts and command as A (`R: packages/wiki-consistency/pyproject.toml:9-29; package.json:42-46; turbo.json:165-184; I: docs/get_started/configure.md:46-68`). |
| **Total B** | **~758** | **~90** | **~−668** | Approximate source Code lines versus current worktree; implementation and caller details may shift it (`R: scripts/own_code.ts:14-16,39-41,73-79`). |

| Comparison | Own-code net | Dropped behaviors | Risk to finish gate |
|---|---:|---|---|
| **A — keep local workflow/verify lifecycle and graph shaping** | **~−208** (`267` removed, `~59` added) | Dynamic TS manifest/export discovery and alias-conflict checks; fixed Python rules have the gaps already listed. Keeps verify history, snapshots, logs, locks, graph labels, test candidates, and result shape (`R: scripts/workflow_verify.ts:124-281; scripts/workflow_graph.ts:42-173; scripts/clean_architecture.ts:61-229`; estimates in Own-code estimate). | Lower: `npm run verify` still checks and records the child result locally; summary parsing/binding can fail closed. The hook still gates on its exit code (`R: scripts/workflow_verify.ts:124-192; scripts/git-flow-hooks/pre-flow-feature-finish:80-81`). |
| **B — maximal replacement** | **~−668** (`~758` removed, `~90` added) | A’s dynamic TS manifest checks plus local verify history/lock/log/snapshot/streak and graph labels, test-candidate heuristic, graph report wrapper, and command menu (`R: scripts/workflow_verify.ts:30-41,124-281; scripts/workflow_graph.ts:17-40,42-101,154-171; scripts/clean_architecture.ts:61-229`). | Higher: the hook depends entirely on `--verify` launching Turbo, validating the same-run summary, and propagating failure; there is no local task/plan/base-bound history or log integrity evidence. Missing summary must fail closed, and `.turbo/runs/` must stay private (`R: scripts/workflow.ts:501-507,565-568; scripts/git-flow-hooks/pre-flow-feature-finish:80-81; T: crates/turborepo-run-summary/src/tracker.rs:418-431,827-844; S: reports/R2-turborepo-lefthook.md:223-245`). |
