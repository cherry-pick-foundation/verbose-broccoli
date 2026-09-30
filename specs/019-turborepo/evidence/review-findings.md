# Review findings and what backfire selected

Batch 24 of `backfire_classify` ([classify-review.json](classify-review.json))
classified the findings of the final reviews ([CR1](review-cr1.md),
[CR2](review-cr2.md), [CR3](review-cr3.md), [R3](review-r3.md)). Only
`must_change` rows with an `auto` decision are fixed (FIX); `manual_review`
rows went to a decision, D19 to D21 (DECIDE); the other rows stay as they
are and are listed in the report (leave). F1, F2 and F3 are the fix tasks.

- FIX `V01` must_change (auto, 0.97) → F1: package.json:30
- FIX `V02` must_change (auto, 0.96) → F2: scripts/workflow.ts:28-29; scripts/workflow_test.ts:81-85
- FIX `V03` must_change (auto, 0.90) → F2: scripts/clean_architecture.ts:24-25,225,247
- FIX `V04` must_change (auto, 0.97) → F2: scripts/docs.ts:572
- DECIDE `V05` manual_review (review, 0.70) → F1 (D19): scripts/doctor.ts:197-199; turbo.json:22; scripts/git-hooks/commit-msg:15; scripts/doctor_test.ts:115,133
- leave `V06` can_stay (auto, 0.95): scripts/constitution_version.ts:31; doctor.ts:80; docs.ts:176; workflow_git.ts:17; workflow_skills.ts:65; workflow_verify.ts:154; docs.ts:30; workflow_verify.ts:11
- FIX `V07` must_change (auto, 0.85) → F1: scripts/commit_msg_test.ts:192-196; package.json commitlint script
- leave `V08` can_stay (review, 0.75): scripts/docs_test.ts:350; specs/019-turborepo/report.md:175-180
- FIX `V09` must_change (auto, 0.96) → F3: packages/backfire/tests/test_build.py:122-125,143,163
- FIX `V10` must_change (auto, 0.88) → F3: packages/doc-regions/src/doc_regions/__main__.py:25-27; packages/doc-regions/tests/test_requests.py:372
- FIX `V11` must_change (auto, 0.92) → F3: packages/backfire/pyproject.toml:29; packages/doc-regions/pyproject.toml:23; packages/wiki-consistency/pyproject.toml:30
- leave `V12` can_stay (auto, 0.92): scripts/cli_contract_test.ts:210-233
- FIX `V13` must_change (auto, 0.92) → F1, F2: scripts/wiki_raw_import_test.ts:58,148,978,1150 and eight other command helpers
- FIX `V14` must_change (auto, 0.86) → F2: scripts/workflow_verify.ts:71-80
- DECIDE `V15` manual_review (review, 0.60) → F3 (D20): pyproject.toml:2-10
- leave `V16` can_stay (auto, 0.90): scripts/doctor_test.ts:401
- DECIDE `V17` manual_review (review, 0.80) → report (D21): orca.yaml; .github/workflows/check.yml; scripts/workflow_skills.ts:67
- leave `V18` must_change (review, 0.75), an open question: docs/architecture.md:11,22
- leave `V19` must_change (review, 0.55); main completed the evidence record anyway, since it is a record, not a code site: specs/019-turborepo/evidence/decide-d18.json
- leave `V20` can_stay (auto, 0.90): scripts/docs_test.ts:77
- leave `V21` can_stay (review, 0.65): packages/backfire/src/backfire_tools/build.py:66-92
- leave `V22` can_stay (auto, 0.90): packages/backfire/src/backfire/ready.py:186-193,157
- leave `V23` can_stay (review, 0.80): package.json:33-41; turbo.json:48-126
- FIX `V24` must_change (auto, 0.85) → F1: scripts/doctor.ts:286
- leave `V25` can_stay (auto, 0.90): biome.json:49 (deleted Deno entry); scripts/clean_architecture_test.ts:163-170
- FIX `V26` must_change (auto, 0.85) → F1: scripts/doctor.ts (no Turborepo probe)

Batch 25 classified the code findings of the last review ([CR4](review-cr4.md)); [R4](review-r4.md) found only gaps in the report and the task ledger, which the coordinator fixed.

- FIX `V27` must_change (auto, 0.85) → F4: scripts/clean_architecture.ts:248; scripts/clean_architecture_test.ts:124-153
- FIX `V28` must_change (auto, 0.90) → F4: docs/architecture.md:253
- leave `V29` can_stay (review, 0.70): packages/backfire/tests/test_build.py:103-116
- leave `V30` can_stay (auto, 0.95): scripts/doctor.ts:312-329,374
- leave `V31` can_stay (auto, 0.95): scripts/doctor_test.ts:133-136; scripts/cli_contract_test.ts:103-111
