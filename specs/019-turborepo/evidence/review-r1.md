# CHE-32 integration review R1

Assumption: the review is limited to the coordinator-owned integration edits listed in the brief. I made no source or configuration edits; this report is the only file I created.

## Finding

1. **should-fix — stale root lockfile wording remains in the updated architecture text.** At `docs/architecture.md:34-35`, the changed Biome sentence calls Biome an npm dependency but then says `deno.lock` pins its native binary. At `docs/architecture.md:437`, the changed command now says `npm run commitlint` while the same sentence still says dependencies are pinned in `deno.json` and `deno.lock`; the broader claim remains at line 130. The root `deno.lock` is deleted, while `package.json` and `package-lock.json` contain the Biome and commitlint versions (see the lockfile evidence command below). These lockfile claims are in `S150`, which the ledger says to leave pending review (`selected-sites.md:100-101`). **Suggested change:** ask the develop session to reselect or reclassify S150, then replace the stale root lockfile references with `package-lock.json`; keep S150 unchanged in this trial until that selection changes.

## Scope and selected-site mapping

| File | Site mapping | Review result |
| --- | --- | --- |
| `turbo.json` | New root config; no pre-existing site ID | `agentGuidance: false` at line 3 is correct; the installed guide says this opts out of Turborepo's managed `AGENTS.md` block (`node_modules/turbo/docs/guides/ai.mdx:21`). All four uv test tasks resolve from their package directories to the repository root. |
| `package.json` | New root config; no pre-existing site ID | `test:git-flow` passes. Its current fixture creates a `node_modules` symlink; the scoped Node permission attempt failed because Node requires full filesystem read and write permission for `fs.symlink`. The `NODE_OPTIONS` prefixes on `test:cli-contract` and `test:docs` are needed to keep `SecurityWarning` output from breaking their exact stream assertions. |
| `docs/architecture.md` | `S137` selected; `S150` left for review | The `npm run` command substitutions match the root scripts. The stale lockfile claims above remain an open S150 issue. |
| `docs/backfire.md` | `S139` selected | The changed `npm run backfire:*` commands match the root scripts at `package.json:28-30`. No finding. |
| `AGENTS.md` | `S136` left for manual review | Unchanged from `HEAD`, consistent with spec FR-009. |

No selected site in this scope was left unchanged: S137 and S139 were changed. The leave entries S136 and S150 remain unchanged; S136 stays untouched because it is a governance file and the ledger marks it `manual_review`. S150 stays untouched because its ledger status is `leave`/`review`, although the stale claims now need a new selection before they can be edited.

Other than S150, I found no unselected site in this review scope that needs a change.

## Commands and results

- `git status --short --branch` — exit 0; confirmed branch `feature/turborepo` and the uncommitted snapshot.
- `git diff -- turbo.json package.json AGENTS.md docs/architecture.md docs/backfire.md` — exit 0; reviewed the tracked diff. The two root config files are new and therefore do not appear in this command's diff output.
- `git diff --check` — exit 0.
- `node -e 'JSON.parse(require("node:fs").readFileSync("package.json")); JSON.parse(require("node:fs").readFileSync("turbo.json")); console.log("valid JSON")'` — exit 0; `valid JSON`.
- `node -e 'const scripts = require("./package.json").scripts; const names = ["check","lint:shell","docs:generate","docs:check","test:cli-contract","wiki-consistency:install","doctor","test:wiki-consistency","backfire:build","test:plugin-skills","verify","test:git-flow","test:worktree-branch","commitlint","test:commit-msg","workflow","doc-regions:update","doc-regions:check","doc-regions:prepare","doc-regions:audit","backfire:install","backfire:ready"]; const missing = names.filter(name => !(name in scripts)); if (missing.length) { console.error(missing.join("\n")); process.exit(1); } console.log(`${names.length} documented npm scripts exist`);'` — exit 0; all 22 concrete npm task names in S137/S139 exist in the root scripts.
- `git status --short -- deno.lock package.json package-lock.json && rg -n '"@biomejs/biome"|"@commitlint/cli"|"conventional-changelog-conventionalcommits"' package.json package-lock.json` — exit 0; `deno.lock` is deleted and the npm package files contain the current pins.
- `TURBO_TELEMETRY_DISABLED=1 ./node_modules/.bin/turbo run test test:slow --dry=json --filter=backfire --filter=doc-regions --filter=wiki-consistency | node -e 'let s=""; process.stdin.on("data", d => s += d).on("end", () => { const r = JSON.parse(s); for (const t of r.tasks) console.log(`${t.taskId}\t${t.directory}\t${t.command}`); })'` — exit 0; dry-run showed `backfire#test`, `backfire#test:slow`, `doc-regions#test`, and `wiki-consistency#test` running from their `packages/<name>` directories with `uv --directory ../..`.
- From `packages/backfire`: `uv --directory ../.. run --no-project python -c 'import os; print(os.getcwd())'` — exit 0; printed the repository root.
- `git diff --exit-code HEAD -- AGENTS.md` — exit 0; `AGENTS.md` is unchanged.
- `npm_config_cache=/tmp/che32-review-npm-cache npm run --silent test:git-flow` — exit 0; 20 passed, 0 failed.
- `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=. --allow-fs-read=node_modules --allow-fs-read=/tmp --allow-fs-write=/tmp --allow-child-process --import ./scripts/deno_shim.ts --test scripts/git_flow_test.ts` — exit 1; all cases stopped at the fixture symlink (`scripts/git_flow_test.ts:142`) with `fs.symlink API requires full fs.read and fs.write permissions`.
- Without the `NODE_OPTIONS` prefix: `env -u NODE_OPTIONS npm_config_cache=/tmp/che32-review-npm-cache node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --import ./scripts/deno_shim.ts --test scripts/cli_contract_test.ts` — exit 1; 2 passed and 12 failed because `SecurityWarning` text appeared in child-process output.
- `npm_config_cache=/tmp/che32-review-npm-cache npm run --silent test:cli-contract` — exit 0; 14 passed, 0 failed.
- Without the `NODE_OPTIONS` prefix: `env -u NODE_OPTIONS npm_config_cache=/tmp/che32-review-npm-cache node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --permission --allow-fs-read=* --allow-fs-write=* --allow-child-process --import ./scripts/deno_shim.ts --test scripts/docs_test.ts` — exit 1; 13 passed and 1 failed because `SecurityWarning` text appeared before the expected JSON diagnostic.
- `npm_config_cache=/tmp/che32-review-npm-cache npm run --silent test:docs` — exit 0; 14 passed, 0 failed.

`deno task workflow` and `deno task verify` were not run: the read-only brief prohibits repository writes, and these commands write workflow evidence. The tests above use temporary fixtures; the npm cache was directed to `/tmp`.
