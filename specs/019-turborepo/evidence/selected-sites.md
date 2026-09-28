# Selected change sites

Generated on 2026-09-29 from [classify.json](classify.json), the backfire_classify results over every candidate site (exact rg matches, backfire_find hits by meaning, and whole-file items). SELECT means must_change or delete with an `auto` decision: only these sites may change. `leave` means can_stay, or any `review` decision: these stay unchanged, and `review` rows are open questions for the report. Row S095 was split into S095:121, :245, :295 and :341 and classified again with measured shim values (batch 3); the split rows replace it.

Correction: batch 1's context said that `Deno.execPath()` returns the Node executable under the shim. Measured afterwards, it returns the `deno` executable on PATH (`which.sync('deno')`), and `Deno.version` reports the shim's fixed `1.40.2`. The error can only have marked a site must_change that needs no edit (a spawn of the clean-code skill through Deno keeps working); workers leave such sites unchanged and say so.

Counts: SELECT delete auto: 8; SELECT must_change auto: 170; leave can_stay auto: 108; leave can_stay review: 21; leave delete review: 7; leave manual_review auto: 1; leave must_change review: 9 (total 324).

## `.claude/settings.json`

- leave `S179` py_package_venv: can_stay (auto, 0.97); lines 3

## `.codex/config.toml`

- leave `S178` py_package_venv: can_stay (auto, 0.97); lines 36

## `.github/workflows/audit.yml`

- SELECT `S131` deno_cli: must_change (auto, 0.93); lines 33,34,39,40

## `.github/workflows/check.yml`

- SELECT `S134` deno_cli: must_change (auto, 0.93); lines 49,50,51,53,55
- leave `S152` deno_config: can_stay (auto, 0.93); lines 50

## `.github/workflows/docs-check.yml`

- SELECT `S133` deno_cli: must_change (auto, 0.95); lines 29,30,32
- leave `S153` deno_config: can_stay (auto, 0.93); lines 30

## `.gitignore`

- SELECT `S135` deno_cli: delete (auto, 0.84); lines 4

## `AGENTS.md`

- leave `S136` deno_cli: manual_review (auto, 0.93); lines 50,51

## `biome.json`

- leave `S146` deno_config: delete (review, 0.67); lines 9

## `deno.json`

- SELECT `deno.json#exclude` deno_config: delete (auto, 0.80); lines 4
- SELECT `deno.json#fmt` deno_config: must_change (auto, 0.81); lines 95
- SELECT `deno.json#imports` deno_config: must_change (auto, 0.95); lines 99
- SELECT `deno.json#nodeModulesDir` deno_config: delete (auto, 0.95); lines 3
- SELECT `deno.json#task:backfire:build` deno_task: must_change (auto, 0.91); lines 28
- SELECT `deno.json#task:backfire:eval` deno_task: must_change (auto, 0.91); lines 31
- SELECT `deno.json#task:backfire:install` deno_task: must_change (auto, 0.91); lines 29
- SELECT `deno.json#task:backfire:ready` deno_task: must_change (auto, 0.91); lines 30
- SELECT `deno.json#task:check` deno_task: must_change (auto, 1.00); lines 53
- SELECT `deno.json#task:clean-architecture` deno_task: must_change (auto, 1.00); lines 24
- SELECT `deno.json#task:clean-code` deno_task: must_change (auto, 0.91); lines 25
- SELECT `deno.json#task:clean-code:scope` deno_task: must_change (auto, 0.91); lines 26
- SELECT `deno.json#task:commitlint` deno_task: must_change (auto, 0.96); lines 14
- SELECT `deno.json#task:doc-regions:audit` deno_task: must_change (auto, 1.00); lines 46
- SELECT `deno.json#task:doc-regions:check` deno_task: must_change (auto, 1.00); lines 34
- SELECT `deno.json#task:doc-regions:prepare` deno_task: must_change (auto, 1.00); lines 42
- SELECT `deno.json#task:doc-regions:update` deno_task: must_change (auto, 1.00); lines 38
- SELECT `deno.json#task:docs:check` deno_task: must_change (auto, 1.00); lines 91
- SELECT `deno.json#task:docs:generate` deno_task: must_change (auto, 1.00); lines 90
- SELECT `deno.json#task:doctor` deno_task: must_change (auto, 0.96); lines 6
- SELECT `deno.json#task:format` deno_task: must_change (auto, 1.00); lines 69
- SELECT `deno.json#task:format:check` deno_task: must_change (auto, 1.00); lines 70
- SELECT `deno.json#task:lint` deno_task: must_change (auto, 1.00); lines 20
- SELECT `deno.json#task:lint:fix` deno_task: must_change (auto, 1.00); lines 68
- SELECT `deno.json#task:lint:shell` deno_task: must_change (auto, 1.00); lines 21
- SELECT `deno.json#task:plugins:validate` deno_task: must_change (auto, 1.00); lines 23
- SELECT `deno.json#task:test` deno_task: must_change (auto, 1.00); lines 72
- SELECT `deno.json#task:test:backfire` deno_task: must_change (auto, 0.91); lines 32
- SELECT `deno.json#task:test:backfire-slow` deno_task: must_change (auto, 1.00); lines 33
- SELECT `deno.json#task:test:clean-architecture` deno_task: must_change (auto, 1.00); lines 71
- SELECT `deno.json#task:test:clean-code` deno_task: must_change (auto, 0.91); lines 27
- SELECT `deno.json#task:test:cli-contract` deno_task: must_change (auto, 1.00); lines 18
- SELECT `deno.json#task:test:commit-msg` deno_task: must_change (auto, 0.96); lines 15
- SELECT `deno.json#task:test:doc-regions` deno_task: must_change (auto, 1.00); lines 52
- SELECT `deno.json#task:test:docs` deno_task: must_change (auto, 0.96); lines 92
- SELECT `deno.json#task:test:doctor` deno_task: must_change (auto, 0.96); lines 11
- SELECT `deno.json#task:test:git-flow` deno_task: must_change (auto, 0.96); lines 12
- SELECT `deno.json#task:test:plugin-skills` deno_task: must_change (auto, 0.96); lines 10
- SELECT `deno.json#task:test:wiki-consistency` deno_task: must_change (auto, 1.00); lines 51
- SELECT `deno.json#task:test:wiki-raw-import` deno_task: must_change (auto, 0.96); lines 93
- SELECT `deno.json#task:test:workflow` deno_task: must_change (auto, 1.00); lines 19
- SELECT `deno.json#task:test:worktree-branch` deno_task: must_change (auto, 0.96); lines 13
- SELECT `deno.json#task:typecheck` deno_task: must_change (auto, 1.00); lines 22
- SELECT `deno.json#task:verify` deno_task: must_change (auto, 1.00); lines 17
- SELECT `deno.json#task:wiki-consistency:install` deno_task: must_change (auto, 1.00); lines 50
- SELECT `deno.json#task:workflow` deno_task: must_change (auto, 0.96); lines 16
- SELECT `deno.json#workspace` deno_config: delete (auto, 0.88); lines 2
- leave `deno.json#compilerOptions` deno_config: must_change (review, 0.76); lines 96

## `deno.lock`

- SELECT `W:deno.lock` whole_file: delete (auto, 0.84); lines 1

## `docs/architecture.md`

- SELECT `S137` deno_cli: must_change (auto, 0.87); lines 28,34,38,57,58,117,118,121,124,234,235,236,250,333,369,383,408,413,423,437,479,482,513,524,550,551,555,558,566,572
- leave `S150` deno_config: must_change (review, 0.73); lines 35,130,436,437
- leave `S180` py_package_venv: can_stay (auto, 0.97); lines 364
- leave `S188` py_uv_project: can_stay (auto, 0.92); lines 367,371

## `docs/backfire.md`

- SELECT `S139` deno_cli: must_change (auto, 0.87); lines 20,21,22,88
- leave `S190` py_uv_project: can_stay (review, 0.53); lines 31,34

## `docs/reference/commands.md`

- SELECT `S140` deno_cli: must_change (auto, 0.93); lines 3,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47…
- SELECT `S151` deno_config: must_change (auto, 0.80); lines 5

## `docs/reference/plugins.md`

- SELECT `S141` deno_cli: must_change (auto, 0.87); lines 3

## `orca.yaml`

- SELECT `S138` deno_cli: must_change (auto, 0.80); lines 9,10,12,36,38,39,49
- SELECT `S193` py_uv_project: must_change (auto, 0.87); lines 42,43
- SELECT `S201` npm_prefix: must_change (auto, 0.93); lines 44

## `packages/backfire/.python-version`

- leave `W:packages/backfire/.python-version` whole_file: can_stay (review, 0.47); lines 1

## `packages/backfire/pyproject.toml`

- SELECT `S168` py_egg_base: must_change (auto, 0.96); lines 31
- SELECT `S175` py_package_venv: must_change (auto, 0.97); lines 31
- SELECT `W:packages/backfire/pyproject.toml#build-system` whole_file: must_change (auto, 0.96); lines 1
- leave `F:py_venv:packages/backfire/pyproject.toml:25-29` find_py_venv: delete (review, 0.27); lines 25,29
- leave `W:packages/backfire/pyproject.toml#constraints` whole_file: must_change (review, 0.73); lines 1

## `packages/backfire/src/backfire/__main__.py`

- leave `F:py_venv:packages/backfire/src/backfire/__main__.py:6-29` find_py_venv: can_stay (auto, 0.87); lines 6,29

## `packages/backfire/src/backfire/judge.py`

- leave `F:py_outside:packages/backfire/src/backfire/judge.py:1-17` find_py_outside: can_stay (auto, 0.87); lines 1,17
- leave `F:py_outside:packages/backfire/src/backfire/judge.py:84-121` find_py_outside: can_stay (auto, 0.87); lines 84,121

## `packages/backfire/src/backfire/ready.py`

- SELECT `S177` py_package_venv: must_change (auto, 0.97); lines 77
- SELECT `S189` py_uv_project: must_change (auto, 0.95); lines 275
- leave `F:py_outside:packages/backfire/src/backfire/ready.py:1-39` find_py_outside: can_stay (review, 0.73); lines 1,39
- leave `F:py_outside:packages/backfire/src/backfire/ready.py:211-239` find_py_outside: can_stay (review, 0.60); lines 211,239
- leave `F:py_outside:packages/backfire/src/backfire/ready.py:40-75` find_py_outside: can_stay (review, 0.73); lines 40,75

## `packages/backfire/src/backfire/validate.py`

- leave `F:py_outside:packages/backfire/src/backfire/validate.py:1-16` find_py_outside: can_stay (auto, 0.87); lines 1,16

## `packages/backfire/src/backfire_education/pseudonymize.py`

- leave `F:py_outside:packages/backfire/src/backfire_education/pseudonymize.py:1-15` find_py_outside: can_stay (auto, 0.89); lines 1,15

## `packages/backfire/src/backfire_tools/acceptance/capture_upstream.py`

- leave `S186` py_uv_project: can_stay (review, 0.53); lines 4
- leave `S198` npm_prefix: can_stay (auto, 0.80); lines 97,110

## `packages/backfire/src/backfire_tools/acceptance/measure_education.py`

- leave `F:py_outside:packages/backfire/src/backfire_tools/acceptance/measure_education.py:1-31` find_py_outside: can_stay (auto, 0.87); lines 1,31

## `packages/backfire/src/backfire_tools/build.py`

- SELECT `S123` deno_cli: must_change (auto, 0.92); lines 145
- SELECT `S184` py_package_lock: must_change (auto, 0.95); lines 107
- leave `F:py_outside:packages/backfire/src/backfire_tools/build.py:1-22` find_py_outside: can_stay (review, 0.60); lines 1,22
- leave `F:py_outside:packages/backfire/src/backfire_tools/build.py:31-74` find_py_outside: must_change (review, 0.67); lines 31,74
- leave `S176` py_package_venv: can_stay (auto, 0.93); lines 117

## `packages/backfire/tests/test_boundary.py`

- leave `F:py_venv:packages/backfire/tests/test_boundary.py:1-36` find_py_venv: can_stay (review, 0.73); lines 1,36
- leave `F:py_venv:packages/backfire/tests/test_boundary.py:88-124` find_py_venv: can_stay (review, 0.73); lines 88,124

## `packages/backfire/tests/test_build.py`

- SELECT `F:py_venv:packages/backfire/tests/test_build.py:135-189` find_py_venv: must_change (auto, 0.89); lines 135,189
- SELECT `F:py_venv:packages/backfire/tests/test_build.py:190-230` find_py_venv: must_change (auto, 0.89); lines 190,230
- SELECT `F:py_venv:packages/backfire/tests/test_build.py:58-70` find_py_venv: must_change (auto, 0.80); lines 58,70
- SELECT `F:py_venv:packages/backfire/tests/test_build.py:72-106` find_py_venv: must_change (auto, 0.84); lines 72,106
- SELECT `S113` deno_cli: must_change (auto, 0.95); lines 248
- leave `S172` py_package_venv: can_stay (review, 0.73); lines 112,123
- leave `S183` py_package_lock: must_change (review, 0.76); lines 12,119
- leave `S196` npm_prefix: can_stay (auto, 0.80); lines 128

## `packages/backfire/tests/test_capture_upstream.py`

- leave `S197` npm_prefix: can_stay (auto, 0.87); lines 125

## `packages/backfire/tests/test_deadline.py`

- leave `F:py_outside:packages/backfire/tests/test_deadline.py:61-79` find_py_outside: can_stay (auto, 0.89); lines 61,79

## `packages/backfire/tests/test_doubles.py`

- leave `F:py_venv:packages/backfire/tests/test_doubles.py:1-27` find_py_venv: can_stay (auto, 0.96); lines 1,27
- leave `F:py_venv:packages/backfire/tests/test_doubles.py:170-172` find_py_venv: can_stay (auto, 0.87); lines 170,172
- leave `F:py_venv:packages/backfire/tests/test_doubles.py:173-197` find_py_venv: can_stay (auto, 0.96); lines 173,197

## `packages/backfire/tests/test_education_e2e.py`

- SELECT `S112` deno_cli: must_change (auto, 0.95); lines 133
- leave `F:py_venv:packages/backfire/tests/test_education_e2e.py:87-110` find_py_venv: can_stay (auto, 0.87); lines 87,110

## `packages/backfire/tests/test_entry.py`

- leave `F:py_venv:packages/backfire/tests/test_entry.py:1-14` find_py_venv: can_stay (auto, 0.80); lines 1,14
- leave `F:py_venv:packages/backfire/tests/test_entry.py:16-30` find_py_venv: can_stay (auto, 0.93); lines 16,30
- leave `F:py_venv:packages/backfire/tests/test_entry.py:32-47` find_py_venv: can_stay (review, 0.73); lines 32,47

## `packages/backfire/tests/test_failures.py`

- leave `F:py_venv:packages/backfire/tests/test_failures.py:30-35` find_py_venv: can_stay (auto, 0.96); lines 30,35

## `packages/backfire/tests/test_judge.py`

- leave `F:py_outside:packages/backfire/tests/test_judge.py:346-368` find_py_outside: can_stay (auto, 0.89); lines 346,368

## `packages/backfire/tests/test_lifecycle.py`

- leave `F:py_outside:packages/backfire/tests/test_lifecycle.py:62-74` find_py_outside: can_stay (auto, 0.89); lines 62,74
- leave `F:py_outside:packages/backfire/tests/test_lifecycle.py:75-114` find_py_outside: can_stay (auto, 0.89); lines 75,114

## `packages/backfire/tests/test_load.py`

- SELECT `S114` deno_cli: must_change (auto, 0.95); lines 80,94
- SELECT `S173` py_package_venv: must_change (auto, 0.96); lines 29,42
- leave `F:py_venv:packages/backfire/tests/test_load.py:50-77` find_py_venv: can_stay (review, 0.73); lines 50,77

## `packages/backfire/tests/test_probe_provider.py`

- leave `F:py_outside:packages/backfire/tests/test_probe_provider.py:274-293` find_py_outside: can_stay (auto, 0.89); lines 274,293

## `packages/backfire/tests/test_ready.py`

- SELECT `S174` py_package_venv: must_change (auto, 0.96); lines 43,74
- SELECT `S187` py_uv_project: must_change (auto, 0.92); lines 85

## `packages/backfire/tests/test_records.py`

- leave `F:py_outside:packages/backfire/tests/test_records.py:27-42` find_py_outside: can_stay (auto, 0.89); lines 27,42

## `packages/backfire/tests/test_score_boundary.py`

- leave `F:py_outside:packages/backfire/tests/test_score_boundary.py:26-62` find_py_outside: can_stay (auto, 0.89); lines 26,62
- leave `F:py_outside:packages/backfire/tests/test_score_boundary.py:63-90` find_py_outside: can_stay (auto, 0.89); lines 63,90

## `packages/backfire/tests/test_server_faults.py`

- leave `F:py_outside:packages/backfire/tests/test_server_faults.py:37-59` find_py_outside: can_stay (auto, 0.92); lines 37,59
- leave `F:py_outside:packages/backfire/tests/test_server_faults.py:60-85` find_py_outside: can_stay (auto, 0.92); lines 60,85

## `packages/backfire/tests/test_tools_part2.py`

- leave `F:py_outside:packages/backfire/tests/test_tools_part2.py:136-147` find_py_outside: can_stay (auto, 0.92); lines 136,147

## `packages/backfire/uv.lock`

- SELECT `W:packages/backfire/uv.lock` whole_file: delete (auto, 0.84); lines 1

## `packages/doc-regions/.python-version`

- leave `W:packages/doc-regions/.python-version` whole_file: delete (review, 0.60); lines 1

## `packages/doc-regions/pyproject.toml`

- SELECT `S166` py_egg_base: must_change (auto, 0.96); lines 25
- SELECT `S170` py_package_venv: must_change (auto, 0.95); lines 25
- SELECT `W:packages/doc-regions/pyproject.toml#build-system` whole_file: must_change (auto, 0.96); lines 1
- leave `F:py_venv:packages/doc-regions/pyproject.toml:20-23` find_py_venv: delete (review, 0.67); lines 20,23

## `packages/doc-regions/src/doc_regions/regions.py`

- SELECT `S111` deno_cli: must_change (auto, 0.95); lines 126,163,212

## `packages/doc-regions/tests/test_regions.py`

- SELECT `S110` deno_cli: must_change (auto, 0.95); lines 58

## `packages/doc-regions/uv.lock`

- SELECT `W:packages/doc-regions/uv.lock` whole_file: delete (auto, 0.84); lines 1

## `packages/wiki-consistency/.python-version`

- leave `W:packages/wiki-consistency/.python-version` whole_file: delete (review, 0.60); lines 1

## `packages/wiki-consistency/package.json`

- leave `W:packages/wiki-consistency/package.json` whole_file: can_stay (review, 0.60); lines 1

## `packages/wiki-consistency/pyproject.toml`

- SELECT `S167` py_egg_base: must_change (auto, 0.96); lines 30
- SELECT `S171` py_package_venv: must_change (auto, 0.95); lines 30
- SELECT `W:packages/wiki-consistency/pyproject.toml#build-system` whole_file: must_change (auto, 0.96); lines 1
- SELECT `W:packages/wiki-consistency/pyproject.toml#sources` whole_file: must_change (auto, 0.93); lines 1
- leave `F:py_venv:packages/wiki-consistency/pyproject.toml:25-28` find_py_venv: delete (review, 0.67); lines 25,28

## `packages/wiki-consistency/src/wiki_consistency/lint.py`

- leave `F:py_outside:packages/wiki-consistency/src/wiki_consistency/lint.py:165-197` find_py_outside: can_stay (auto, 0.92); lines 165,197

## `packages/wiki-consistency/src/wiki_consistency/requests.py`

- leave `F:py_outside:packages/wiki-consistency/src/wiki_consistency/requests.py:21-27` find_py_outside: can_stay (auto, 0.92); lines 21,27

## `packages/wiki-consistency/src/wiki_consistency/search.py`

- SELECT `F:py_venv:packages/wiki-consistency/src/wiki_consistency/search.py:31-34` find_py_venv: must_change (auto, 0.87); lines 31,34
- SELECT `F:py_venv:packages/wiki-consistency/src/wiki_consistency/search.py:58-79` find_py_venv: must_change (auto, 0.87); lines 58,79
- leave `F:py_venv:packages/wiki-consistency/src/wiki_consistency/search.py:218-238` find_py_venv: can_stay (auto, 0.80); lines 218,238

## `packages/wiki-consistency/tests/test_boundary.py`

- leave `F:py_outside:packages/wiki-consistency/tests/test_boundary.py:7-29` find_py_outside: can_stay (auto, 0.92); lines 7,29

## `packages/wiki-consistency/tests/test_prepare.py`

- leave `F:py_outside:packages/wiki-consistency/tests/test_prepare.py:65-75` find_py_outside: can_stay (auto, 0.92); lines 65,75

## `packages/wiki-consistency/tests/test_search.py`

- leave `F:py_outside:packages/wiki-consistency/tests/test_search.py:216-221` find_py_outside: must_change (review, 0.76); lines 216,221
- leave `F:py_outside:packages/wiki-consistency/tests/test_search.py:407-459` find_py_outside: can_stay (auto, 0.87); lines 407,459

## `packages/wiki-consistency/uv.lock`

- SELECT `W:packages/wiki-consistency/uv.lock` whole_file: delete (auto, 0.84); lines 1

## `plugins/code/deno.json`

- leave `W:plugins/code/deno.json` whole_file: delete (review, 0.47); lines 1

## `plugins/code/skills/clean-code/SKILL.md`

- leave `S142` deno_cli: can_stay (auto, 0.93); lines 16,27
- leave `S165` deno_config: can_stay (auto, 0.95); lines 27

## `plugins/code/skills/clean-code/deno.json`

- leave `S108` jsr_npm_specifier: can_stay (auto, 0.93); lines 4,5,6,7,8,9,10,11
- leave `S164` deno_config: can_stay (auto, 0.93); lines 2

## `plugins/code/skills/clean-code/scripts/clean_code.ts`

- leave `S027` deno_api_fs: can_stay (auto, 0.93); lines 243,337
- leave `S096` deno_api_process: can_stay (auto, 0.97); lines 346
- leave `S103` import_meta_main: can_stay (auto, 0.96); lines 328

## `plugins/code/skills/clean-code/scripts/clean_code_test.ts`

- leave `S028` deno_api_fs: can_stay (auto, 0.93); lines 134,149,152,168,197,202,204,205,214,219,230,231,233,237,238,250,255,257,258,273
- leave `S074` deno_api_test: can_stay (auto, 0.92); lines 133,148,201,218,254

## `plugins/code/skills/clean-code/scripts/cli.ts`

- SELECT `R:plugins/code/skills/clean-code/scripts/cli.ts:6` ts_non_erasable: must_change (auto, 0.89); lines 6
- leave `S097` deno_api_process: can_stay (auto, 0.93); lines 26,44

## `plugins/code/skills/speckit-implement/SKILL.md`

- leave `S203` npm_prefix: can_stay (auto, 0.97); lines 141

## `plugins/work/skills/wiki-consistency/SKILL.md`

- SELECT `S202` npm_prefix: must_change (auto, 0.93); lines 35
- leave `S194` py_uv_project: can_stay (review, 0.47); lines 27

## `scripts/clean_architecture.ts`

- SELECT `S155` deno_config: must_change (auto, 0.87); lines 42,43,44,45,46,47
- leave `F:ts_deno:scripts/clean_architecture.ts:28-39` find_ts_deno: must_change (review, 0.47); lines 28,39
- leave `S012` deno_api_fs: can_stay (auto, 1.00); lines 208
- leave `S079` deno_api_process: can_stay (auto, 0.96); lines 246
- leave `S102` import_meta_main: can_stay (auto, 0.95); lines 235

## `scripts/clean_architecture_test.ts`

- SELECT `S042` deno_api_command: must_change (auto, 0.95); lines 163
- SELECT `S055` deno_api_execpath: must_change (auto, 1.00); lines 163
- SELECT `S065` deno_api_test: must_change (auto, 1.00); lines 8,123,136,199
- SELECT `S105` jsr_npm_specifier: must_change (auto, 0.92); lines 15,16,17,18,204,206,211,214,221,239,240
- SELECT `S147` deno_config: must_change (auto, 0.93); lines 3,12,21,22,57,127,167,226,230,236,245
- leave `S009` deno_api_fs: can_stay (auto, 1.00); lines 9,10,75,76,78,118,119,124,126,132,137,155,160,161,195,200,202,225,229,235,244,255
- leave `S082` deno_api_process: can_stay (auto, 0.87); lines 139,141,152

## `scripts/cli_contract_test.ts`

- SELECT `S031` deno_api_command: must_change (auto, 0.95); lines 20,62,77
- SELECT `S050` deno_api_execpath: must_change (auto, 1.00); lines 20,28
- SELECT `S068` deno_api_test: must_change (auto, 1.00); lines 124,142,176,201,236,272
- SELECT `S161` deno_config: must_change (auto, 0.95); lines 44,45,104,156,206,207,217
- leave `S004` deno_api_fs: can_stay (auto, 1.00); lines 100,103,104,105,119,156,158,204,211,239,240,248,249,252,256,275
- leave `S086` deno_api_process: can_stay (auto, 0.80); lines 28
- leave `S130` deno_cli: can_stay (auto, 0.80); lines 27

## `scripts/commit_msg_test.ts`

- SELECT `S035` deno_api_command: must_change (auto, 1.00); lines 7,104,134,145
- SELECT `S054` deno_api_execpath: must_change (auto, 1.00); lines 104
- SELECT `S067` deno_api_test: must_change (auto, 1.00); lines 31,98,237,403,427
- SELECT `S162` deno_config: must_change (auto, 0.95); lines 163,164,167,168
- leave `S002` deno_api_fs: can_stay (auto, 1.00); lines 99,120,153,155,160,161,162,166,171,177,181,182,186,215,220,347,429,439,450,455,516,521,540,555
- leave `S084` deno_api_process: can_stay (auto, 0.80); lines 9,10,11
- leave `S129` deno_cli: can_stay (review, 0.73); lines 10,15,113

## `scripts/commitlint.config.mjs`

- leave `S089` deno_api_process: can_stay (auto, 0.95); lines 6

## `scripts/constitution_version.ts`

- SELECT `S030` deno_api_command: must_change (auto, 0.93); lines 23
- leave `S075` deno_api_process: can_stay (auto, 0.96); lines 109,110

## `scripts/doc_sources.py`

- leave `F:py_outside:scripts/doc_sources.py:4-20` find_py_outside: can_stay (auto, 0.87); lines 4,20

## `scripts/doc_sources_test.py`

- leave `F:py_outside:scripts/doc_sources_test.py:6-31` find_py_outside: can_stay (auto, 0.87); lines 6,31

## `scripts/docs.ts`

- SELECT `F:ts_deno:scripts/docs.ts:1-14` find_ts_deno: must_change (auto, 0.80); lines 1,14
- SELECT `S048` deno_api_command: must_change (auto, 0.95); lines 119
- SELECT `S058` deno_api_execpath: must_change (auto, 0.97); lines 119
- SELECT `S124` deno_cli: must_change (auto, 0.89); lines 19,138,144,335
- SELECT `S148` deno_config: must_change (auto, 0.80); lines 68,69,70,71,72,115,116,286,288,327,506
- leave `S021` deno_api_fs: can_stay (auto, 0.95); lines 37,40,58,362,375,378,422,423,426,427,432,464,466,475,478,522,557,564,569,571,578,581
- leave `S094` deno_api_process: can_stay (auto, 0.93); lines 45,139,626
- leave `S099` import_meta_main: can_stay (auto, 0.95); lines 609

## `scripts/docs_test.ts`

- SELECT `S034` deno_api_command: must_change (auto, 1.00); lines 99,375,379,381,551,625,636,653
- SELECT `S053` deno_api_execpath: must_change (auto, 1.00); lines 551,625,636,653
- SELECT `S062` deno_api_test: must_change (auto, 0.97); lines 117,165,206,239,259,290,312,367,407,434,474,501,532,593
- SELECT `S120` deno_cli: must_change (auto, 0.92); lines 136,619,621,651
- SELECT `S145` deno_config: must_change (auto, 0.93); lines 26,30,127,182,215,216,556,594,658
- leave `F:ts_deno:scripts/docs_test.ts:1-16` find_ts_deno: can_stay (auto, 0.93); lines 1,16
- leave `S007` deno_api_fs: can_stay (auto, 1.00); lines 22,27,29,32,41,42,43,47,54,61,68,77,79,87,92,127,146,219,220,221,225,251,261,284,297,298,300,302,316,321,326,327,331,335,360,385,387,414,428,441…
- leave `S081` deno_api_process: can_stay (review, 0.73); lines 37,56,244,246,265,267,271,272,280,281,429

## `scripts/doctor.ts`

- SELECT `S044` deno_api_command: must_change (auto, 0.95); lines 68,93,112,114,139,179,196
- SELECT `S059` deno_api_execpath: must_change (auto, 0.95); lines 18,243
- SELECT `S095:121` deno_api_process: must_change (auto, 0.98); lines 121
- SELECT `S095:245` deno_api_process: must_change (auto, 0.96); lines 245
- SELECT `S095:295` deno_api_process: must_change (auto, 0.80); lines 295
- SELECT `S126` deno_cli: must_change (auto, 0.91); lines 146,287
- SELECT `S149` deno_config: must_change (auto, 0.95); lines 214
- SELECT `S182` py_package_venv: must_change (auto, 0.96); lines 106
- SELECT `S192` py_uv_project: must_change (auto, 0.93); lines 91
- SELECT `S200` npm_prefix: must_change (auto, 0.97); lines 146,150,152
- leave `S023` deno_api_fs: can_stay (auto, 0.95); lines 53,61,150,151,215,233,235,243
- leave `S095:341` deno_api_process: can_stay (auto, 0.95); lines 341
- leave `S100` import_meta_main: can_stay (auto, 0.95); lines 314

## `scripts/doctor_test.ts`

- SELECT `S045` deno_api_command: must_change (auto, 0.95); lines 8,51,70,88
- SELECT `S049` deno_api_execpath: must_change (auto, 1.00); lines 6
- SELECT `S069` deno_api_test: must_change (auto, 1.00); lines 76,100,149,182,216,233,284,310,325,340,355,370,382,424,436,466
- SELECT `S106` jsr_npm_specifier: must_change (auto, 0.93); lines 144
- SELECT `S115` deno_cli: must_change (auto, 0.95); lines 365,377
- SELECT `S160` deno_config: must_change (auto, 0.95); lines 11,12
- SELECT `S181` py_package_venv: must_change (auto, 0.89); lines 120,125,130,135,191,198
- SELECT `S191` py_uv_project: must_change (auto, 0.87); lines 320,335,350
- leave `S022` deno_api_fs: can_stay (auto, 0.95); lines 15,19,25,37,80,81,85,86,106,109,143,158,167,186,189,192,194,386,387,395,409,415,441,442,457,462,488,495
- leave `S078` deno_api_process: can_stay (auto, 0.96); lines 64,90,140,141,167,207,212,256,289,300,315,330,345,360,372,402,445,460,488
- leave `S199` npm_prefix: can_stay (auto, 0.93); lines 388,394

## `scripts/git-flow-hooks/pre-flow-feature-finish`

- SELECT `S128` deno_cli: must_change (auto, 0.96); lines 75,80

## `scripts/git-hooks/commit-msg`

- SELECT `R:scripts/git-hooks/commit-msg` deno_cli: must_change (auto, 0.96); lines 14,15,16,17,19,23

## `scripts/git_flow_test.ts`

- SELECT `S040` deno_api_command: must_change (auto, 1.00); lines 18,33
- SELECT `S066` deno_api_test: must_change (auto, 1.00); lines 184,198,214,240,250,263,274,284,293,311,325,343,361,376,395,410,492,496,500,529
- SELECT `S092` deno_api_process: must_change (auto, 0.84); lines 10,11,117
- SELECT `S158` deno_config: must_change (auto, 0.95); lines 115,119,122,139,140
- leave `F:ts_deno:scripts/git_flow_test.ts:1-3` find_ts_deno: can_stay (review, 0.77); lines 1,3
- leave `S020` deno_api_fs: can_stay (auto, 0.95); lines 69,88,101,105,109,110,112,113,115,118,122,124,129,130,134,148,156,200,364,507
- leave `S122` deno_cli: can_stay (auto, 0.80); lines 11,22

## `scripts/plugin_skills_test.ts`

- SELECT `S047` deno_api_command: must_change (auto, 0.95); lines 58
- SELECT `S070` deno_api_test: must_change (auto, 1.00); lines 7,20,71
- leave `F:ts_deno:scripts/plugin_skills_test.ts:1-4` find_ts_deno: can_stay (review, 0.77); lines 1,4
- leave `S013` deno_api_fs: can_stay (auto, 1.00); lines 10,15,22,26,29,36,66,74,75
- leave `S087` deno_api_process: can_stay (auto, 0.87); lines 11

## `scripts/validate_plugins.ts`

- leave `F:ts_deno:scripts/validate_plugins.ts:1-15` find_ts_deno: must_change (review, 0.53); lines 1,15
- leave `S008` deno_api_fs: can_stay (auto, 1.00); lines 28,31
- leave `S085` deno_api_process: can_stay (auto, 0.87); lines 33,82
- leave `S101` import_meta_main: can_stay (auto, 0.95); lines 58

## `scripts/wiki_raw_import_test.ts`

- SELECT `R:scripts/wiki_raw_import_test.ts:72` ts_non_erasable: must_change (auto, 0.93); lines 72
- SELECT `S043` deno_api_command: must_change (auto, 0.95); lines 14,24,95,571,609,637,835,934,1074,1208
- SELECT `S073` deno_api_test: must_change (auto, 0.95); lines 231,251,320,352,366,378,419,445,459,491,506,541,565,660,695,716,740,777,812,895,947,983,1004,1051,1195,1259
- leave `F:ts_deno:scripts/wiki_raw_import_test.ts:1-4` find_ts_deno: can_stay (review, 0.77); lines 1,4
- leave `S018` deno_api_fs: can_stay (auto, 0.95); lines 39,43,51,59,62,132,133,136,143,146,155,156,266,268,269,288,289,292,306,309,330,331,333,356,361,397,407,426,427,428,430,431,440,441,467,472,473,474,475,477…
- leave `S090` deno_api_process: can_stay (auto, 0.91); lines 880,1202

## `scripts/workflow-evidence.schema.json`

- SELECT `S117` deno_cli: must_change (auto, 0.93); lines 38

## `scripts/workflow.ts`

- SELECT `S127` deno_cli: must_change (auto, 0.92); lines 48,66,69,70
- leave `S010` deno_api_fs: can_stay (auto, 1.00); lines 266,475,486,487
- leave `S083` deno_api_process: can_stay (auto, 0.87); lines 569
- leave `S098` import_meta_main: can_stay (auto, 0.95); lines 398

## `scripts/workflow_files.ts`

- leave `F:ts_deno:scripts/workflow_files.ts:1-5` find_ts_deno: can_stay (review, 0.77); lines 1,5
- leave `S001` deno_api_fs: can_stay (auto, 1.00); lines 47
- leave `S076` deno_api_process: can_stay (auto, 0.96); lines 52

## `scripts/workflow_git.ts`

- SELECT `S039` deno_api_command: must_change (auto, 1.00); lines 12
- leave `S014` deno_api_fs: can_stay (auto, 1.00); lines 36,38,49,59
- leave `S088` deno_api_process: can_stay (auto, 0.87); lines 40

## `scripts/workflow_graph.ts`

- SELECT `S125` deno_cli: must_change (auto, 0.93); lines 20,28,35,169
- leave `S019` deno_api_fs: can_stay (auto, 0.95); lines 104

## `scripts/workflow_graph_test.ts`

- SELECT `S041` deno_api_command: must_change (auto, 0.95); lines 11,63
- SELECT `S056` deno_api_execpath: must_change (auto, 1.00); lines 63,76
- SELECT `S063` deno_api_test: must_change (auto, 0.97); lines 85,138,164,203,235,262,294,433,471
- SELECT `S107` jsr_npm_specifier: must_change (auto, 0.80); lines 206,208,215,306,323,324
- SELECT `S159` deno_config: must_change (auto, 0.95); lines 68,89,92,206,303,314
- leave `S015` deno_api_fs: can_stay (auto, 1.00); lines 35,39,40,46,148,275,276,312,396,400,424,438,441,445,465,507

## `scripts/workflow_plan.ts`

- leave `S005` deno_api_fs: can_stay (auto, 1.00); lines 45

## `scripts/workflow_plan_test.ts`

- SELECT `S038` deno_api_command: must_change (auto, 1.00); lines 330
- SELECT `S064` deno_api_test: must_change (auto, 0.97); lines 35,51,67,102,147,180,206,259,278,306
- SELECT `S156` deno_config: must_change (auto, 0.95); lines 77,123,288
- leave `S017` deno_api_fs: can_stay (auto, 0.95); lines 23,26,27,31,194,213,236,341

## `scripts/workflow_skills.ts`

- SELECT `S036` deno_api_command: must_change (auto, 1.00); lines 57
- SELECT `S057` deno_api_execpath: must_change (auto, 0.97); lines 57
- leave `S016` deno_api_fs: can_stay (auto, 1.00); lines 156,171
- leave `S091` deno_api_process: can_stay (auto, 0.93); lines 176
- leave `S121` deno_cli: can_stay (review, 0.73); lines 49,78
- leave `S157` deno_config: can_stay (auto, 0.95); lines 62,64

## `scripts/workflow_skills_test.ts`

- SELECT `S032` deno_api_command: must_change (auto, 0.93); lines 30,258
- SELECT `S052` deno_api_execpath: must_change (auto, 1.00); lines 258,271
- SELECT `S060` deno_api_test: must_change (auto, 0.97); lines 70,88,129,168,208,228,248,316,369
- SELECT `S116` deno_cli: must_change (auto, 0.95); lines 253
- SELECT `S144` deno_config: must_change (auto, 0.93); lines 252,263
- leave `S003` deno_api_fs: can_stay (auto, 1.00); lines 55,59,60,66,231,244,257,303,357
- leave `S077` deno_api_process: can_stay (auto, 0.96); lines 244

## `scripts/workflow_symbol.ts`

- leave `S006` deno_api_fs: can_stay (auto, 1.00); lines 24

## `scripts/workflow_test.ts`

- SELECT `S033` deno_api_command: must_change (auto, 1.00); lines 13
- SELECT `S061` deno_api_test: must_change (auto, 0.97); lines 53,104,122,149,162,180,195,213,228,280,302,311,323,364,379,413,426,438,446,485
- SELECT `S132` deno_cli: must_change (auto, 0.91); lines 452
- leave `S011` deno_api_fs: can_stay (auto, 1.00); lines 38,42,43,49,130,132,133,134,151,153,172,182,186,187,202,216,282,283,313,332,333,366,368,369,388,392,428,432,433
- leave `S154` deno_config: must_change (review, 0.67); lines 72,73,198,275

## `scripts/workflow_verify.ts`

- SELECT `S029` deno_api_command: must_change (auto, 0.95); lines 122
- SELECT `S051` deno_api_execpath: must_change (auto, 1.00); lines 122
- SELECT `S118` deno_cli: must_change (auto, 0.95); lines 159,225
- leave `S024` deno_api_fs: can_stay (auto, 0.95); lines 47,85,139,155,169,171,199
- leave `S080` deno_api_process: can_stay (auto, 0.96); lines 48,158

## `scripts/workflow_verify_test.ts`

- SELECT `S037` deno_api_command: must_change (auto, 1.00); lines 12
- SELECT `S072` deno_api_test: must_change (auto, 1.00); lines 82,114,159,188,208,223,240,263
- SELECT `S119` deno_cli: must_change (auto, 0.95); lines 49
- SELECT `S163` deno_config: must_change (auto, 0.95); lines 47
- leave `S026` deno_api_fs: can_stay (auto, 0.89); lines 37,40,41,45,46,60,65,103,122,142,149,190,216,218,234,254,266,272
- leave `S093` deno_api_process: can_stay (auto, 0.87); lines 115,149

## `scripts/worktree_branch_test.ts`

- SELECT `S046` deno_api_command: must_change (auto, 0.95); lines 8,31
- SELECT `S071` deno_api_test: must_change (auto, 1.00); lines 140,182,231
- leave `S025` deno_api_fs: can_stay (auto, 0.89); lines 55,72,81,87,194
