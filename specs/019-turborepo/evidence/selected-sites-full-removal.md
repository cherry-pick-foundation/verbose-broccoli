# Selected change sites: full Deno removal

Generated on 2026-09-29 from [classify-full-removal.json](classify-full-removal.json), the classification of the merged tree (after `develop` 8ce9b2a) for removing Deno completely. SELECT means must_change or delete with an `auto` decision. Rows re-asked with their file context (batch 21) replace their first result. `SELECT(user rule)` rows stayed `review` after the re-ask and are selected by the user's rule instead (see `user_rule` in the JSON). `leave` rows stay unchanged.

Counts: SELECT: 182; SELECT(user rule): 5; leave: 5 (total 192).

## `.github/workflows/audit.yml`

- SELECT `X084` deno_cli: must_change (auto, 0.87); lines 45,46
- SELECT `X127` deno_version: delete (auto, 0.87); lines 30,32
- SELECT `X162` deno_prose: must_change (auto, 0.99); lines 30,32,34,35,45,46

## `.github/workflows/check.yml`

- SELECT `X086` deno_cli: must_change (auto, 0.87); lines 56
- SELECT `X116` deno_config: must_change (auto, 1.00); lines 56
- SELECT `X128` deno_version: delete (auto, 0.87); lines 31,33
- SELECT `X164` deno_prose: must_change (auto, 0.99); lines 31,33,35,36,56

## `.github/workflows/docs-check.yml`

- SELECT `X085` deno_cli: must_change (auto, 0.87); lines 36
- SELECT `X115` deno_config: must_change (auto, 1.00); lines 36
- SELECT(user rule) `X129` deno_version: delete (review, 0.53); lines 28,30
- SELECT `X163` deno_prose: must_change (auto, 0.99); lines 28,30,31,32,36

## `.gitignore`

- SELECT `X165` deno_prose: delete (auto, 0.87); lines 1,5

## `AGENTS.md`

- leave `X088` deno_cli: manual_review (auto, 0.87); lines 50,51
- leave `X138` deno_prose: manual_review (review, 0.77); lines 3,50,51

## `README.md`

- SELECT `X167` deno_prose: must_change (auto, 0.87); lines 3

## `biome.json`

- SELECT(user rule) `X107` deno_config: delete (review, 0.47); lines 9
- SELECT(user rule) `X140` deno_prose: delete (review, 0.47); lines 8,51

## `deno.json`

- SELECT `W2:deno.json` whole_file: delete (auto, 0.91); lines 1

## `docs/architecture.md`

- SELECT `X091` deno_executable: must_change (auto, 0.87); lines 497
- SELECT `X141` deno_prose: must_change (auto, 0.93); lines 11,22,27,48,264,295,497

## `docs/backfire.md`

- SELECT `X144` deno_prose: must_change (auto, 0.80); lines 5

## `docs/reference/commands.md`

- SELECT `X122` deno_version: must_change (auto, 0.93); lines 24
- SELECT `X149` deno_prose: must_change (auto, 0.87); lines 24,93

## `orca.yaml`

- SELECT `X090` deno_executable: must_change (auto, 0.91); lines 9,10,11,12,36,39
- SELECT `X104` deno_config: must_change (auto, 0.87); lines 39
- SELECT(user rule) `X120` deno_version: must_change (review, 0.60); lines 14
- SELECT `X137` deno_prose: must_change (auto, 0.89); lines 9,10,11,12,14

## `package.json`

- SELECT `P:task:doctor` develop_task_delta: must_change (auto, 1.00); lines 1
- SELECT `P:task:format` develop_task_delta: must_change (auto, 1.00); lines 1
- SELECT `P:task:format:check` develop_task_delta: must_change (auto, 1.00); lines 1
- SELECT `P:task:lint` develop_task_delta: must_change (auto, 1.00); lines 1
- SELECT `P:task:lint:fix` develop_task_delta: must_change (auto, 1.00); lines 1
- SELECT `P:task:test` develop_task_delta: must_change (auto, 1.00); lines 1
- SELECT `P:task:test:ruff` develop_task_delta: must_change (auto, 1.00); lines 1
- SELECT `P:task:wiki-consistency:install` develop_task_delta: must_change (auto, 1.00); lines 1
- SELECT `W2:package.json#devDependencies:@deno/shim-deno` whole_file: delete (auto, 0.85); lines 1
- SELECT `W2:package.json#devDependencies:@std/fs` whole_file: delete (auto, 0.85); lines 1
- SELECT `X078` deno_shim: must_change (auto, 0.95); lines 9,10,11,12,13,14,15,16,18,19,23,24,45,47,48,49,50,57
- SELECT `X087` deno_cli: must_change (auto, 0.89); lines 25,27
- SELECT `X093` deno_executable: must_change (auto, 0.89); lines 9,47,48
- SELECT `X117` deno_config: must_change (auto, 1.00); lines 25,27,47,48
- SELECT `X133` deno_permission_flags: must_change (auto, 0.96); lines 25,27
- SELECT `X166` deno_prose: must_change (auto, 0.95); lines 9,25,27,47,48,57

## `packages/backfire/src/backfire_tools/build.py`

- SELECT `RUFF:packages/backfire/src/backfire_tools/build.py:194` ruff_finding: must_change (auto, 1.00); lines 194
- SELECT `RUFF:packages/backfire/src/backfire_tools/build.py:236` ruff_finding: must_change (auto, 1.00); lines 236
- SELECT `RUFF:packages/backfire/src/backfire_tools/build.py:241` ruff_finding: must_change (auto, 1.00); lines 241
- SELECT `RUFF:packages/backfire/src/backfire_tools/build.py:34` ruff_finding: must_change (auto, 1.00); lines 34
- SELECT `RUFF:packages/backfire/src/backfire_tools/build.py:37` ruff_finding: must_change (auto, 1.00); lines 37
- SELECT `RUFF:packages/backfire/src/backfire_tools/build.py:78` ruff_finding: must_change (auto, 1.00); lines 78

## `packages/backfire/tests/test_build.py`

- SELECT `RUFF:packages/backfire/tests/test_build.py:129` ruff_finding: must_change (auto, 1.00); lines 129

## `packages/doc-regions/src/doc_regions/__main__.py`

- SELECT `X136` deno_prose: must_change (auto, 0.87); lines 25

## `packages/wiki-consistency/pyproject.toml`

- SELECT `W2:packages/wiki-consistency/pyproject.toml#backfire-source` whole_file: must_change (auto, 1.00); lines 1

## `plugins/code/deno.json`

- SELECT `W2:plugins/code/deno.json` whole_file: delete (auto, 0.91); lines 1

## `plugins/code/skills/clean-code/SKILL.md`

- SELECT `X089` deno_cli: must_change (auto, 0.93); lines 16,27
- SELECT `X118` deno_config: must_change (auto, 1.00); lines 27
- SELECT `X134` deno_permission_flags: must_change (auto, 0.96); lines 27
- SELECT `X168` deno_prose: must_change (auto, 0.96); lines 16,27

## `plugins/code/skills/clean-code/deno.json`

- SELECT `W2:plugins/code/skills/clean-code/deno.json` whole_file: delete (auto, 0.87); lines 1

## `plugins/code/skills/clean-code/deno.lock`

- SELECT `W2:plugins/code/skills/clean-code/deno.lock` whole_file: delete (auto, 0.93); lines 1

## `plugins/code/skills/clean-code/scripts/clean_code.ts`

- SELECT `X028` deno_api_fs: must_change (auto, 0.96); lines 243,337
- SELECT `X059` deno_api_process: must_change (auto, 0.96); lines 346
- SELECT `X066` std_fs_import: must_change (auto, 0.96); lines 2

## `plugins/code/skills/clean-code/scripts/clean_code_test.ts`

- SELECT `X029` deno_api_fs: must_change (auto, 0.96); lines 134,149,152,168,197,202,204,205,214,219,230,231,233,237,238,250,255,257,258,273
- SELECT `X036` deno_api_test: must_change (auto, 1.00); lines 133,148,201,218,254

## `plugins/code/skills/clean-code/scripts/cli.ts`

- SELECT `X060` deno_api_process: must_change (auto, 0.96); lines 29,47

## `scripts/clean_architecture.ts`

- SELECT `X017` deno_api_fs: must_change (auto, 0.95); lines 245
- SELECT `X053` deno_api_process: must_change (auto, 1.00); lines 283
- SELECT `X065` std_fs_import: must_change (auto, 0.96); lines 6
- SELECT `X109` deno_config: must_change (auto, 0.93); lines 77,78,79,80
- SELECT `X139` deno_prose: must_change (auto, 0.87); lines 35,86,260

## `scripts/clean_architecture_test.ts`

- SELECT `X004` deno_api_fs: must_change (auto, 1.00); lines 28,29,94,95,97,137,138,143,145,146,147,153,158,176,181,182,199,204,206,232,236,242,251,262
- SELECT `X040` deno_api_process: must_change (auto, 1.00); lines 160,162,173
- SELECT `X108` deno_config: must_change (auto, 0.89); lines 32,41,76,148,237,252
- SELECT `X157` deno_prose: must_change (auto, 0.96); lines 27,161,163,171

## `scripts/cli_contract_test.ts`

- SELECT `X016` deno_api_fs: must_change (auto, 0.97); lines 129,132,133,134,135,149,187,189,235,242,271,272,280,281,284,288,307
- SELECT `X046` deno_api_process: must_change (auto, 1.00); lines 44,55,244
- SELECT `X075` deno_shim: must_change (auto, 0.92); lines 83
- SELECT `X082` deno_cli: must_change (auto, 0.81); lines 61,62,63,250,251,252
- SELECT `X101` deno_env: must_change (auto, 0.93); lines 43
- SELECT `X113` deno_config: must_change (auto, 1.00); lines 60,134,237,238,249
- SELECT `X131` deno_permission_flags: must_change (auto, 0.93); lines 64,65,66,67,68,253,254
- SELECT `X151` deno_prose: must_change (auto, 0.93); lines 184,209

## `scripts/cli_contract_test.ts.snapshot`

- SELECT `X142` deno_prose: must_change (auto, 0.84); lines 10

## `scripts/commit_msg_test.ts`

- SELECT `X014` deno_api_fs: must_change (auto, 0.97); lines 119,138,169,171,176,177,186,188,194,198,199,203,232,237,364,446,456,467,472,533,538,557,572
- SELECT `X045` deno_api_process: must_change (auto, 1.00); lines 11,12,13
- SELECT `X072` deno_shim: must_change (auto, 0.87); lines 127,182
- SELECT `X096` deno_executable: must_change (auto, 0.93); lines 12
- SELECT `X100` deno_env: must_change (auto, 0.84); lines 12,17,133
- SELECT `X154` deno_prose: must_change (auto, 0.97); lines 12,444

## `scripts/commitlint.config.mjs`

- SELECT `X055` deno_api_process: must_change (auto, 1.00); lines 6

## `scripts/constitution_version.ts`

- SELECT `X050` deno_api_process: must_change (auto, 1.00); lines 133,134

## `scripts/deno_shim.ts`

- SELECT `W2:scripts/deno_shim.ts` whole_file: delete (auto, 0.92); lines 1
- SELECT `X030` deno_api_types: delete (auto, 0.96); lines 7,8
- SELECT `X073` deno_shim: delete (auto, 0.92); lines 1,7,8
- SELECT `X150` deno_prose: delete (auto, 0.97); lines 1,3,6,7,8,10,13,20

## `scripts/docs.ts`

- SELECT `X025` deno_api_fs: must_change (auto, 0.95); lines 52,55,73,163,437,450,454,499,500,503,504,509,541,543,552,555,643,650,655,657,664,667
- SELECT `X047` deno_api_process: must_change (auto, 1.00); lines 60,138,175,176,712
- SELECT `X077` deno_shim: must_change (auto, 0.92); lines 200
- SELECT `X083` deno_cli: must_change (auto, 0.84); lines 185,186,187
- SELECT `X097` deno_executable: must_change (auto, 0.91); lines 176,177
- SELECT `X102` deno_env: must_change (auto, 0.87); lines 137,143
- SELECT `X105` deno_config: must_change (auto, 0.92); lines 86,87,88,132,184
- SELECT `X130` deno_permission_flags: must_change (auto, 0.93); lines 188,189,190
- SELECT `X155` deno_prose: must_change (auto, 0.95); lines 176,177

## `scripts/docs_test.ts`

- SELECT `X003` deno_api_fs: must_change (auto, 1.00); lines 45,56,57,61,64,73,74,75,79,86,93,100,109,111,119,124,157,176,255,256,257,261,287,297,322,335,336,338,340,354,359,364,365,369,373,398,431,433,471,485…
- SELECT `X039` deno_api_process: must_change (auto, 1.00); lines 69,88,280,282,305,309,310,318,319,486
- SELECT `X062` std_fs_import: must_change (auto, 0.96); lines 12
- SELECT `X070` deno_shim: must_change (auto, 0.89); lines 617,736
- SELECT `X079` deno_cli: must_change (auto, 0.89); lines 689
- SELECT `X106` deno_config: must_change (auto, 0.95); lines 62,689
- SELECT `X121` deno_version: must_change (auto, 0.87); lines 684
- SELECT `X147` deno_prose: must_change (auto, 0.97); lines 375,472,500,535,563,684,689

## `scripts/doctor.ts`

- SELECT `X026` deno_api_fs: must_change (auto, 0.95); lines 19,54,62,223,224,286,299,301
- SELECT `X049` deno_api_process: must_change (auto, 1.00); lines 19,407
- SELECT `X098` deno_executable: must_change (auto, 0.87); lines 19,59,308,331
- SELECT `X124` deno_version: must_change (auto, 0.93); lines 24,323,360
- SELECT `X159` deno_prose: must_change (auto, 0.97); lines 19,24,36,59,60,308,331,360,386,394,400

## `scripts/doctor_test.ts`

- SELECT `X009` deno_api_fs: must_change (auto, 0.97); lines 35,39,45,57,97,98,102,103,105,106,127,130,175,193,202,221,224,227,229,441,442,450,464,470,496,497,512,517,563,574
- SELECT `X035` deno_api_test: must_change (auto, 1.00); lines 375
- SELECT `X057` deno_api_process: must_change (auto, 0.96); lines 8,83,112,202,242,247,291,324,335,350,365,380,395,410,426,457,500,515,563
- SELECT `X074` deno_shim: must_change (auto, 0.92); lines 77
- SELECT `X095` deno_executable: must_change (auto, 0.95); lines 101,104,112,195,228,281
- SELECT `X123` deno_version: must_change (auto, 0.93); lines 132,207,281
- SELECT `X156` deno_prose: must_change (auto, 0.97); lines 101,104,112,189,190,195,196,197,205,207,223,228,231,280,281,523

## `scripts/git_flow_test.ts`

- SELECT `X005` deno_api_fs: must_change (auto, 1.00); lines 87,106,119,123,127,128,130,131,133,136,141,142,145,153,158,159,163,178,186,230,394,537
- SELECT `X056` deno_api_process: must_change (auto, 1.00); lines 12,13
- SELECT `X071` deno_shim: must_change (auto, 0.87); lines 151
- SELECT `X094` deno_executable: must_change (auto, 0.93); lines 13
- SELECT `X103` deno_env: must_change (auto, 0.84); lines 13,24
- SELECT `X153` deno_prose: must_change (auto, 0.97); lines 13

## `scripts/plugin_skills_test.ts`

- SELECT `X010` deno_api_fs: must_change (auto, 0.97); lines 12,17,24,28,31,38,69,77,78
- SELECT `X042` deno_api_process: must_change (auto, 1.00); lines 13
- SELECT `X063` std_fs_import: must_change (auto, 0.96); lines 4

## `scripts/ruff_test.ts`

- SELECT `X018` deno_api_fs: must_change (auto, 0.97); lines 34,40,55,76,80,103,117,129,144,145,170,171,172,173,177,181,194
- SELECT `X033` deno_api_types: must_change (auto, 1.00); lines 26
- SELECT `X034` deno_api_test: must_change (auto, 1.00); lines 33
- SELECT `X044` deno_api_process: must_change (auto, 1.00); lines 9
- SELECT `X080` deno_cli: must_change (auto, 0.87); lines 14

## `scripts/validate_plugins.ts`

- SELECT `X011` deno_api_fs: must_change (auto, 0.97); lines 28,31
- SELECT `X048` deno_api_process: must_change (auto, 1.00); lines 33,82

## `scripts/wiki_raw_import_test.ts`

- SELECT `X015` deno_api_fs: must_change (auto, 0.97); lines 54,58,66,74,77,144,145,148,155,158,167,168,278,280,281,300,301,304,321,342,343,345,368,373,409,419,438,439,440,442,443,452,453,479,484,485,486,487,489,523…
- SELECT `X043` deno_api_process: must_change (auto, 1.00); lines 895,1223
- SELECT `X064` std_fs_import: must_change (auto, 0.96); lines 4
- SELECT `X160` deno_prose: must_change (auto, 0.93); lines 847

## `scripts/workflow-evidence.schema.json`

- SELECT `X126` deno_version: must_change (auto, 0.87); lines 29,37

## `scripts/workflow.ts`

- SELECT `X006` deno_api_fs: must_change (auto, 1.00); lines 266,475,486,487
- SELECT `X041` deno_api_process: must_change (auto, 1.00); lines 569
- SELECT `X158` deno_prose: must_change (auto, 0.80); lines 28

## `scripts/workflow_files.ts`

- SELECT `X001` deno_api_fs: must_change (auto, 1.00); lines 47
- SELECT `X037` deno_api_process: must_change (auto, 1.00); lines 52
- SELECT `X061` std_fs_import: must_change (auto, 0.96); lines 1

## `scripts/workflow_git.ts`

- SELECT `X021` deno_api_fs: must_change (auto, 0.95); lines 69,80,90
- SELECT `X031` deno_api_types: must_change (auto, 0.93); lines 67
- SELECT `X052` deno_api_process: must_change (auto, 1.00); lines 71

## `scripts/workflow_graph.ts`

- SELECT `X020` deno_api_fs: must_change (auto, 0.95); lines 104
- SELECT `X161` deno_prose: must_change (auto, 0.80); lines 166

## `scripts/workflow_graph_test.ts`

- SELECT `X022` deno_api_fs: must_change (auto, 0.96); lines 44,48,49,55,159,292,293,418,422,460,463,467,487,529
- SELECT `X069` deno_shim: must_change (auto, 0.89); lines 82
- SELECT `X111` deno_config: must_change (auto, 0.91); lines 103,336
- leave `X032` deno_api_types: can_stay (auto, 0.80); lines 334,446

## `scripts/workflow_plan.ts`

- SELECT `X007` deno_api_fs: must_change (auto, 1.00); lines 45

## `scripts/workflow_plan_test.ts`

- SELECT `X027` deno_api_fs: must_change (auto, 0.93); lines 25,28,29,33,196,215,238,342
- leave `X114` deno_config: can_stay (auto, 0.80); lines 125
- leave `X146` deno_prose: can_stay (auto, 0.89); lines 157

## `scripts/workflow_skills.ts`

- SELECT `X024` deno_api_fs: must_change (auto, 0.95); lines 177,192
- SELECT `X054` deno_api_process: must_change (auto, 1.00); lines 65,66,197
- SELECT `X081` deno_cli: must_change (auto, 0.84); lines 50,74,75,76,99
- SELECT `X092` deno_executable: must_change (auto, 0.95); lines 66,67
- SELECT `X112` deno_config: must_change (auto, 0.92); lines 71,73
- SELECT `X132` deno_permission_flags: must_change (auto, 0.93); lines 77,78
- SELECT `X143` deno_prose: must_change (auto, 0.96); lines 50,66,67,99

## `scripts/workflow_skills_test.ts`

- SELECT `X002` deno_api_fs: must_change (auto, 1.00); lines 64,68,69,75,240,253,268,311,365
- SELECT `X038` deno_api_process: must_change (auto, 1.00); lines 253
- SELECT `X068` deno_shim: must_change (auto, 0.89); lines 263,279

## `scripts/workflow_symbol.ts`

- SELECT `X008` deno_api_fs: must_change (auto, 1.00); lines 24
- SELECT `X148` deno_prose: must_change (auto, 0.87); lines 163

## `scripts/workflow_test.ts`

- SELECT `X013` deno_api_fs: must_change (auto, 0.97); lines 47,51,52,58,139,141,142,143,160,162,181,191,195,196,211,225,291,292,322,341,342,375,377,378,397,401,437,441,442
- SELECT `X110` deno_config: must_change (auto, 0.91); lines 81,82,207,284
- SELECT `X145` deno_prose: must_change (auto, 0.87); lines 204

## `scripts/workflow_verify.ts`

- SELECT `X012` deno_api_fs: must_change (auto, 0.97); lines 60,98,169,185,199,202,233
- SELECT `X058` deno_api_process: must_change (auto, 0.96); lines 61,188
- SELECT `X125` deno_version: must_change (auto, 0.93); lines 27,188
- SELECT `X152` deno_prose: must_change (auto, 0.97); lines 188

## `scripts/workflow_verify_test.ts`

- SELECT `X019` deno_api_fs: must_change (auto, 0.96); lines 46,49,50,54,56,70,75,113,132,152,159,200,226,228,244,264,276,282
- SELECT `X051` deno_api_process: must_change (auto, 1.00); lines 125,159
- SELECT `X076` deno_shim: must_change (auto, 0.92); lines 55

## `scripts/worktree_branch_test.ts`

- SELECT `X023` deno_api_fs: must_change (auto, 0.96); lines 55,72,81,87,194

## `tsconfig.json`

- SELECT `W2:tsconfig.json#files` whole_file: must_change (auto, 0.87); lines 1
- SELECT `X067` deno_shim: delete (auto, 0.83); lines 12

## `turbo.json`

- SELECT(user rule) `X099` deno_env: delete (review, 0.53); lines 10
- SELECT `X119` deno_version: must_change (auto, 0.87); lines 23
- SELECT `X135` deno_prose: must_change (auto, 0.87); lines 23
