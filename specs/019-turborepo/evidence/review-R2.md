# CHE-32 merge review R2

Assumption: I treated FR-011 and FR-013 as acceptance requirements even where the remaining work is outside the 16 conflict resolutions. The review is pinned to merge commit `cfbb1c7` and its parents; other in-progress worktree changes were left untouched.

## Findings

1. **Blocker — Deno is still required despite FR-011.** The merged `deno.json:1-5` remains with a Deno compiler configuration. The selected Orca setup site S138 still adds `$deno_bin` to `PATH` and runs `deno install` (`orca.yaml:36,39`); the doctor defaults to Deno 2.9.6 and probes/reports it (`scripts/doctor.ts:18-28,331-337,360`). The root `doctor` command also resolves `deno`, several root scripts still invoke `deno run`/`deno test`, and the root package still depends on and preloads `@deno/shim-deno` (`package.json:9,25,27,47-57`; `scripts/deno_shim.ts:1-20`). The stale Deno claims remain in `docs/architecture.md:48` and `docs/reference/commands.md:24`. This fails the stated no-Deno requirement and the Node-with-Deno-hidden scenario. No exception in the brief covers the selected S138 site. Remove those runtime/setup dependencies, move any needed Node type setting out of `deno.json`, and update generated references.

2. **Should-fix — the root lock regresses five develop versions.** `pyproject.toml:4-8` constrains the root workspace to `typesafe-sdk==0.7.1`, `starlette<=0.52.1`, `openai<=3.19.2`, `pyjwt<=2.15.0`, and `sse-starlette<=3.4.11`; `uv.lock` resolves those older versions at lines 855-856, 1077-1078, 1338-1339, 1351-1352, and 1402-1404. Develop's `packages/wiki-consistency/uv.lock` at `8ce9b2a` has `openai 3.20.0`, `pyjwt 2.15.1`, `sse-starlette 3.5.0`, `starlette 1.7.0`, and `typesafe-sdk 0.7.2` (lines 829-830, 1051-1052, 1312-1313, 1325-1326, 1376-1377). FR-013 requires those newer versions unless a failing test and exception are recorded; the reviewed research notes the old constraints but no such test exception (`research.md:208-211`). Revisit the constraints, regenerate the root lock, and record any test-backed exception.

3. **Note — the generated doctor description omits Ruff and still advertises Deno.** The merged command reference says the doctor verifies Deno and lists no Ruff environment (`docs/reference/commands.md:24`; source description `turbo.json:22-24`), while the doctor now checks Ruff (`scripts/doctor.ts:341,369`) and the merged architecture text documents Ruff. Update the Turbo task description and regenerate the command reference.

## Resolution coverage

The incoming Ruff doctor check and assertion are retained in `scripts/doctor.ts` and `scripts/doctor_test.ts`; the Ruff environment is synced in `orca.yaml:43`. The CHE-26 dependency is retained as `backfire[education]` with a workspace source in `packages/wiki-consistency/pyproject.toml`. The Python files listed below carry the feature's workspace/Node edits with Ruff formatting applied. The known non-porting of Ruff tasks from develop's `deno.json`, Deno test registration in the new Ruff tests, the `build.py` work-plugin source rewrite, and seven Ruff findings are not treated as findings here, as the brief specified.

| Resolved file | Selected site IDs covered |
| --- | --- |
| `deno.json` | `deno.json#exclude`, `#fmt`, `#imports`, `#nodeModulesDir`, `#workspace`, and all selected `#task:*` entries listed in `selected-sites.md:45-91`. `#compilerOptions` was left under review. |
| `docs/architecture.md` | `S137`, `S150:35`, `S150:130`, `S150:436-437` |
| `docs/reference/commands.md` | `S140`, `S151` |
| `orca.yaml` | `S138`, `S193`, `S201` |
| `packages/backfire/src/backfire/ready.py` | `F:T002:ready.py:90-101`, `S177`, `S189` |
| `packages/backfire/src/backfire_tools/build.py` | `F:T002:build.py:103-110`, `S123`, `S184` |
| `packages/backfire/tests/test_build.py` | `F:T002:test_build.py:107-118`, `F:py_venv:packages/backfire/tests/test_build.py:58-70`, `F:py_venv:packages/backfire/tests/test_build.py:72-106`, `F:py_venv:packages/backfire/tests/test_build.py:135-189`, `F:py_venv:packages/backfire/tests/test_build.py:190-230`, `S113` |
| `packages/backfire/tests/test_education_e2e.py` | `S112` |
| `packages/backfire/tests/test_load.py` | `S114`, `S173` |
| `packages/backfire/tests/test_ready.py` | `S174`, `S187` |
| `packages/doc-regions/src/doc_regions/regions.py` | `S111` |
| `packages/doc-regions/tests/test_regions.py` | `S110` |
| `packages/wiki-consistency/pyproject.toml` | `S167`, `S171`, `W:packages/wiki-consistency/pyproject.toml#build-system`, `W:packages/wiki-consistency/pyproject.toml#sources` |
| `scripts/doctor.ts` | `S044`, `S059`, `S095:121`, `S095:245`, `S095:295`, `S126`, `S149`, `S182`, `S192`, `S200` |
| `scripts/doctor_test.ts` | `F:T004:doctor_test.ts:100-110`, `F:T004:doctor_test.ts:182-195`, `F:T004:doctor_test.ts:385-397`, `F:T004:doctor_test.ts:398-410`, `F:T004:doctor_test.ts:474-476`, `F:T004:doctor_test.ts:477-491`, `S045`, `S049`, `S069`, `S106`, `S115`, `S160`, `S181`, `S191` |
| `uv.lock` | New root lock; consolidates selected deletions `W:packages/backfire/uv.lock`, `W:packages/doc-regions/uv.lock`, and `W:packages/wiki-consistency/uv.lock`. |

## Selected sites left unchanged

- `deno.json#compilerOptions` was classified `must_change` but its decision was `review` (0.76), so it was left unchanged under FR-001. Its retention conflicts with FR-011 and is covered by Finding 1.
- Selected site `S138` was not fully applied: `orca.yaml:36,39` still requires Deno. No documented reason was given; this is covered by Finding 1.
- Aggregate site `S150` stayed under review; its split children `S150:35`, `S150:130`, and `S150:436-437` were reclassified and updated.
- `S183` in `test_build.py` stayed unchanged after a `review` decision (0.76); retaining standalone copied plugin locks is still required by the D7 design.
- `F:py_outside:packages/backfire/src/backfire_tools/build.py:31-74` stayed unchanged after a `review` decision (0.67). Separately, the brief says the copied work-plugin workspace-source rewrite is pending; I did not report that known gap.

## Commands and verification

All commands below exited 0. The per-file loops compare each listed resolution against both parents; the focused `git show` and lock comparisons supplied the cited evidence. `git diff --check` reported no whitespace errors. No tests were run in this read-only review.

```sh
git show --no-patch --pretty=raw cfbb1c7

files=(deno.json docs/architecture.md docs/reference/commands.md orca.yaml packages/backfire/src/backfire/ready.py packages/backfire/src/backfire_tools/build.py packages/backfire/tests/test_build.py packages/backfire/tests/test_education_e2e.py)
for f in "${files[@]}"; do
  git show cfbb1c7 -- "$f"
  git diff d6d1eba cfbb1c7 -- "$f"
  git diff 8ce9b2a cfbb1c7 -- "$f"
done

files=(packages/backfire/tests/test_load.py packages/backfire/tests/test_ready.py packages/doc-regions/src/doc_regions/regions.py packages/doc-regions/tests/test_regions.py packages/wiki-consistency/pyproject.toml scripts/doctor.ts scripts/doctor_test.ts uv.lock)
for f in "${files[@]}"; do
  git show cfbb1c7 -- "$f" >/dev/null || exit
  git diff d6d1eba cfbb1c7 -- "$f" >/dev/null || exit
  git diff 8ce9b2a cfbb1c7 -- "$f" >/dev/null || exit
done

git diff --check d6d1eba cfbb1c7 -- deno.json docs/architecture.md docs/reference/commands.md orca.yaml packages/backfire/src/backfire/ready.py packages/backfire/src/backfire_tools/build.py packages/backfire/tests/test_build.py packages/backfire/tests/test_education_e2e.py packages/backfire/tests/test_load.py packages/backfire/tests/test_ready.py packages/doc-regions/src/doc_regions/regions.py packages/doc-regions/tests/test_regions.py packages/wiki-consistency/pyproject.toml scripts/doctor.ts scripts/doctor_test.ts uv.lock
git diff --check 8ce9b2a cfbb1c7 -- deno.json docs/architecture.md docs/reference/commands.md orca.yaml packages/backfire/src/backfire/ready.py packages/backfire/src/backfire_tools/build.py packages/backfire/tests/test_build.py packages/backfire/tests/test_education_e2e.py packages/backfire/tests/test_load.py packages/backfire/tests/test_ready.py packages/doc-regions/src/doc_regions/regions.py packages/doc-regions/tests/test_regions.py packages/wiki-consistency/pyproject.toml scripts/doctor.ts scripts/doctor_test.ts uv.lock

git grep -n -e '@deno/shim-deno' -e 'deno_shim.ts' cfbb1c7 -- ':!specs/**'

git show cfbb1c7:uv.lock | rg -n -A4 'name = "(openai|starlette|typesafe-sdk|pyjwt|sse-starlette)"'
git show 8ce9b2a:packages/wiki-consistency/uv.lock | rg -n -A4 'name = "(openai|starlette|typesafe-sdk|pyjwt|sse-starlette)"'
```

Additional focused source inspection used `git show cfbb1c7:<path> | nl -ba` with `sed` for the cited lines in `deno.json`, `orca.yaml`, `scripts/doctor.ts`, `package.json`, `scripts/deno_shim.ts`, `docs/architecture.md`, `docs/reference/commands.md`, and `pyproject.toml`; these commands exited 0.
