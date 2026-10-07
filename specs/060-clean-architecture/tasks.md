# Tasks: Clean Architecture Tool Collection

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), the [contracts](contracts/) and
[quickstart.md](quickstart.md).

**Organization**: one phase per slice of the plan, each a separate finish into
`develop` (FR-014; plan "Slice mechanics"). Slices S1, S2a and S2b serve User
Stories 1 and 2; S3 to S6 serve User Story 3; User Story 4 and the work-area
move wait for their holds.

Each task's implementer, reviewer, model and effort are chosen with Jev
through the model-choice skill when the task is dispatched, with the user's
free-quota priority as evidence and Cursor and Copilot offered only on Auto;
the pick, its probability and confidence are recorded under the task. The
final review of each slice comes from a provider other than the
implementer's. Batch commands start with
`systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7`;
one `npm run verify` runs at a time.

Every slice ends with the same finish steps, written once here and referred
to as **Finish**: merge current `develop` into the branch; run
`npm run workflow` and follow it; run `npm run verify`; measure locally owned
code with the session's `code-size/measure.py` and report it (FR-017,
SC-008); run `npm run doc-regions:prepare -- --base develop
--max-evidence-chars <n>` and `npm run doc-regions:audit` and resolve their
judgments; check any new cited claim with Jev (SC-005); get the fresh
other-provider review with only the slice's scope and requirements (for a
slice Claude built, Codex's built-in `codex review --base develop` with the
scope and boundaries in `-c developer_instructions="..."`, since it takes no
prompt together with `--base`); resolve
findings and verify again; commit the review record; ask the develop
orchestrator for the full-check and finish slots; while develop holds a
slot for this worktree, commit nothing and change no ref, because a moved tip
fails its snapshot guard (2026-10-07); after the finish, `develop` verifies
(SC-006).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel with other [P] tasks of the same phase
- **[Story]**: the user story the task serves

## Phase 1: Slice S1 — rules (User Story 1, P1)

**Goal**: the constitution and root `AGENTS.md` describe a tool collection,
not plugins.

**Independent test**: no constitution principle or root `AGENTS.md` rule
requires a plugin root, plugin ID or plugin manifest; each new structural
rule names its source; the constitution is 3.0.0 with the user's dated
approval; verification passes (SC-002, first part).

- [x] T001 [US1] Record the reference review and plan in `specs/060-clean-architecture/` (research rows with Jev-checked claims, plan, data model, contracts, quickstart, tasks) (FR-015 to FR-018, SC-005).
  Ledger 2026-10-06: committed in 64690aa, 6c8cc77 and 3f39ba4 by the orchestrator (Claude Opus 5.5, the user's choice for this role); reading workers on Claude Code Sonnet 5.5 medium, picked by Jev (probability 0.61 for page digests, 0.36 for examples) after Antigravity's quota and Cursor's free-plan limit refused; consistency analysis by a Claude Code Sonnet 5.5 medium worker (Jev 0.70), its 24 findings resolved in the planning records.
- [x] T002 [US1] Get the user's approval of the rule text in `specs/060-clean-architecture/plan.md` "Rule changes for the user's approval" and its open points, with the baseline measurement (11,351 source and 21,030 test lines) and the estimate, through the coordinator; record it as a dated user decision in `specs/060-clean-architecture/research.md` (FR-015, SC-008).
  Ledger 2026-10-06: the user chose A at about 20:10 KST (U-2026-10-06k); the empty-placeholder rule is kept in the new IX as the main session asked.
- [x] T003 [US1] Amend `.specify/memory/constitution.md` with the approved text: replace principle IX, change the wording of VI, VII and Governance, add the dated Governance paragraph, update the Sync Impact Report, and set version 3.0.0 with `npm run constitution:bump -- MAJOR` in a `!` commit (FR-015). Depends on T002.
- [x] T004 [P] [US1] Change the opening line and the plugin packaging rule of `AGENTS.md` as approved; leave the pointers and "code plugin's" phrases for S2b (FR-001, FR-015). Depends on T002.
- [x] T005 [P] [US1] Retitle `docs/architecture.md` and rewrite its opening and "Package and runtime ownership" to describe skill areas, component packages and the holds, keeping the plugin sections S2a removes (FR-001, FR-016).
- [x] T006 [US1] **Finish** slice S1, including a Jev check of the final rule text against its cited rows (SC-005). Depends on T003 to T005.
  Follow-through 2026-10-07: the user's chosen built-in review (`codex review --base`, gpt-6.1-sol medium, scope in `developer_instructions`) ran in a scratch clone at the reviewed 122daa3 against develop d9392f1, without changing history: exit 0, approve. Receipt: `slices/s1/builtin-review-20261006T180528Z/` in the feature's state folder.

## Phase 2: Slice S2a — plugin packaging removed (User Story 2, P1)

**Goal**: no plugin manifest, generator or distribution route remains, and
agents still find every skill and server.

**Independent test**: quickstart scenario 2; the skill links and skills
validate as before; the reference-library guard test still passes.

- [x] T007 [US2] Read-only security review of `skills-ref` 0.1.1 and its dependencies (`click`, `strictyaml`) with evidence for every finding, in `specs/060-clean-architecture/security/skills-ref-review.md` (FR-018). The reviewer stays on Claude Code or Codex (security judgment).
  Ledger 2026-10-06: Claude Code Sonnet 5.5 high (Jev probability 0.46, confidence 0.36); stopped by the user's pause after the substance was complete, before a second read-through. Verdict: adopt with conditions (0 high, 3 medium, 3 low, 7 info; none blocks); the conditions are in T013.
- [x] T008 [US2] Record the before-inventory from `develop`: `ls .agents/skills`, `claude mcp list`, `codex mcp list`, in the slice's evidence folder under `$XDG_STATE_HOME/verbose-broccoli/workspaces/feature-clean-architecture/` (SC-001).
  Ledger 2026-10-06: done by the orchestrator from `develop` d9392f1 in `skills-inventory/` (47 skill links; both agents list `jev-mcp` and `reference-library`; inside `develop` Claude Code reports `reference-library` at both user and project scope, which S2a removes).
- [x] T009 [US2] Recheck that no open feature branch changes `plugins/work/plugin.json`, `plugins/work/mcp.json`, `plugins/work/skills/jev` or `plugins/work/AGENTS.md` (plan Holds, "H2 exception"); stop and report if one does (FR-016).
  Ledger 2026-10-06: no open branch changes them (`skills-inventory/h2-exception-check-*.txt`); repeat when S2b starts.
- [x] T010 [US2] With the develop orchestrator, run the existing `npm run plugins:clean-codex` and delete the ignored `.mcp.json` in each prepared checkout (develop, feature-clean-architecture, document-pdf-fidelity, evp-oewn-senses, exam-calendar, korean-web-wiki, weekly-tool-update; the primary checkout had no generated block on 2026-10-06, recheck it) while the command still exists in each, and record the evidence (FR-005). In this worktree it runs before T011.
  Ledger 2026-10-06: this worktree is cleared (Codex block removed with `npm run plugins:clean-codex`, `.mcp.json` deleted, copies in `slices/s2a/`); develop runs the cleanup in the other checkouts and confirms before granting the S2a finish slot. At 22:02 KST develop had cleared develop and the five older prepared checkouts (receipts kept); one newer checkout for the gate fixes waits for its owner.
- [x] T011 [US2] Delete the plugin packaging: `plugins/*/plugin.json`, `plugins/code/mcp.json`, `plugins/work/mcp.json`, `plugins/code/package.json`, `scripts/plugin-clients.ts`, `scripts/plugin-skills-test.ts`, `scripts/plugins-validate-test.ts`, `scripts/vendor/agent-plugins/`, `tools/check-jsonschema/`, `docs/reference/plugins.md`, `doc_sources.plugin_table` and its tests in `scripts/doc_sources_test.py`; remove their `package.json` scripts, `turbo.json` tasks, the `scripts/doc-regions.toml` target and the `check-jsonschema` lines of `scripts/toolchain.sh` and `.config/mise.toml` (setup and doctor), and the `public-api:plugins/code` entry of `.config/dependency-cruiser.json` that reads the deleted manifest (FR-005). Depends on T009, T010.
- [x] T012 [US2] Rewrite `scripts/reference-library-test.ts` so it no longer reads `plugins/work/mcp.json`, keeping its checks of the connector pin and lock in `plugins/work/package.json`, of the blocked tools in the pinned connector, and of the deny rules in `.claude/settings.json` (FR-004). Depends on T011.
- [x] T013 [US2] Add `tools/skills-ref/` (a uv project pinning `skills-ref` 0.1.1, `click` 8.5.0, `strictyaml` 1.7.3, `python-dateutil` 2.9.0.post0 and `six` 1.17.0 by hash, with uv `no-build = true`), a `skills:validate` task that runs the package's `agentskills validate <skill-dir>` command (not `skills-ref`) over `skills/*/*/` and `plugins/*/skills/*/`, leaving out the unchanged upstream Ponytail bundle whose skills carry an `argument-hint` key the validator rejects; one passing and one failing skill run under Python 3.14 with the output kept; the one-time `uv sync --project tools/skills-ref --frozen` in mise setup and `_AGENTSKILLS_COMPLETE` unset in verification (security review conditions); and `scripts/skills-links-test.ts` checking that each `.agents/skills` link resolves to exactly one allowed skill folder, that no name repeats and that no skill folder lacks a link, with the allowed folders read from one list that S2b extends (FR-002, FR-003; contracts/delivery.md). Depends on T007.
- [x] T014 [US2] Update the documents for the removal: `docs/architecture.md` (remove the generator text of "Live checkout discovery" and "Optional copied client packages"; keep the skills table), `README.md` (installing elsewhere with `skills` and `add-mcp`), `docs/reference/commands.md` (regenerate), and `scripts/clean-architecture-test.ts` and other tests that name removed rules or files (FR-003, FR-005).
- [x] T015 [US2] Run quickstart scenario 2 (FR-003 to FR-005). Depends on T010 to T014.
  Ledger 2026-10-06: T011 to T015 implemented by Claude Code Sonnet 5.5 high (Jev probability 0.33, confidence 0.25) in e3324d1, 5165be4, e02e17b, 9252dfc, cae6ca6 and 9f57051. The duplicate `plugins/work/skills/jev` was deleted here instead of in T020 (it is in the H2 exception; the orchestrator approved it). Owned code: 11,351 to 10,721 source lines and 21,030 to 18,904 test lines. Python 3.14 validator runs passed and failed as expected; quickstart scenario 2 passed. Evidence: `slices/s2a/ctx_fb4a3194057a/` in the feature's state folder.
- [x] T016 [US2] **Finish** slice S2a. Depends on T015.
  Note: removing the plugin-discovery commit hook changes the shared Git hooks, so `npm run verify` stops only at the doctor's Lefthook check until develop installs the hooks from the develop worktree at the finish slot, as in specs/056-guarded-mise-trust T005; the other 43 checks pass. Full checks in this worktree wait for a slot from develop.

## Phase 3: Slice S2b — skills moved into areas (User Story 2, P1)

**Goal**: each skill exists once at `skills/<area>/<name>/` (or in the
Ponytail bundle), found through `.agents/skills`.

**Independent test**: quickstart scenario 1; fresh Claude Code and Codex
sessions list the same skill and server names as before S2a, once each
(SC-001, SC-002 second part).

- [x] T017 [US2] Move the code area: `git mv plugins/code/skills/<name> skills/code/<name>` for every skill except Ponytail's four, `plugins/code/AGENTS.md` to `skills/code/AGENTS.md`; change each skill's rules pointer to `../AGENTS.md` and fix relative links in `skills/code/model-choice/references/` and other moved files (FR-003a, FR-002). Depends on T002 (Ponytail decision).
- [x] T018 [P] [US2] Move the chat area: `plugins/chat/skills/*`, `plugins/chat/AGENTS.md` and `plugins/chat/LICENSE` to `skills/chat/` (FR-003a).
- [x] T019 [P] [US2] Move Ponytail as one unchanged upstream bundle to `tools/ponytail/` (`hooks/`, `tests/`, `skills/ponytail{,-audit,-debt,-review}/`, licenses, `upstream.md`), retarget `.agents/ponytail` to `../tools/ponytail` so `.codex/hooks.json` stays byte-identical, and update `upstream.md` (plan Decision 10); or apply the alternative the user chooses in T002. Depends on T002.
- [x] T020 [US2] Retarget every link in `.agents/skills/` to `skills/<area>/<name>`, `tools/ponytail/skills/<name>` or, for held work skills, `plugins/work/skills/<name>`; extend the link test's allowed folders (FR-002, FR-003). The duplicate `plugins/work/skills/jev` was already deleted in S2a. Depends on T017 to T019.
- [x] T021 [US2] Update every remaining `plugins/code` or `plugins/chat` path: `.config/dependency-cruiser.json`, `eslint.config.js`, `eslint.ignores.js`, `tsconfig.json`, `.github/workflows/audit.yml`, `pyproject.toml`, `package.json` (workspaces gain `skills/code/clean-code`; the `clean-architecture` script also scans `skills` and `tools/ponytail`), `scripts/workflow.ts` (import the CLI serializer by package name), `scripts/workflow-skills.ts`, `scripts/doc-regions.toml` (`report_only` glob for area `AGENTS.md` files), the tests under `scripts/` that name these paths, `docs/examples/wiki/AGENTS.md`, and `licenses/third-party-notices.md` (plan Decision 9).
- [x] T022 [US2] Update the rule pointers and documents: `docs/architecture.md` "Skill source ownership" and its Cog skill table glob, root `AGENTS.md` pointers, lessons line and "code plugin's" phrases, `.claude/rules/claude-code.md`, and the area `AGENTS.md` files' plugin wording (FR-003, FR-011, SC-002).
- [x] T023 [US2] Run quickstart scenario 1 and record the after-inventory from fresh Claude Code and Codex sessions; report any installed plugin copies in user folders to the user without removing them (SC-001, spec Edge Cases). Depends on T020 to T022.
  Ledger 2026-10-07: T017 to T023 implemented by Claude Code Sonnet 5.5 high (Jev probability 0.61, confidence 0.54) in 3541b4a, 01fa65d, 94854ad, 9df3edc, daf3b31 and 10202a0; Ponytail's bundle is unchanged under `tools/ponytail/` with a new one-line `tools/ponytail/AGENTS.md` that its skills and hook loader resolve to. Narrow checks pass; 47 skill names are the same before and after; 43 non-Ponytail skills validate. Owned code: 10,740 to 10,750 source and 19,043 to 19,050 test lines. A fresh Claude Code session (Haiku 4.5) listed all 47 skills; a fresh Codex session (gpt-6-luna, low) listed all but `gws-shared`, a work skill whose link and folder this slice did not change (the list is the model's own answer, so a missing name is a limit of this check). User-scope links in `~/.agents/skills` point into develop's old plugin folders and will break after the merge; the user was asked how to retarget them. Evidence: `slices/s2b/ctx_9bbc09c6beb1/` and `skills-inventory/` in the feature's state folder.
- [x] T024 [US2] **Finish** slice S2b. Depends on T023.
  User-scope follow-up 2026-10-07 (U-2026-10-07b): after the merge the main session retargeted the user's skill links to the new folders, removed two broken ones and removed the old Codex plugin entries and cached copies, with backups.

## Phase 4: Slice S2c — Spec Kit 1.1.0 (User Story 2, P1)

**Goal**: Spec Kit's command line and project files are at 1.1.0, installed
by Spec Kit's own commands through the `.agents/skills` links
(U-2026-10-06l).

**Independent test**: `specify` reports 1.1.0 for the integration and
extensions; the skills link test and `skills-ref validate` pass; every
`speckit-*` skill still points to its area rules.

- [x] T025 [US2] Read-only security review of the upstream change from Spec Kit 1.0.1 project files and the 1.0.12 command line to 1.1.0, including the agent-context extension 1.0.1 to 1.0.2, with evidence for every finding, in `specs/060-clean-architecture/security/spec-kit-1.1.0-review.md` (FR-018). The reviewer stays on Claude Code or Codex.
  Ledger 2026-10-07: Claude Code Sonnet 5.5 high (Jev probability 0.60, confidence 0.53). Verdict: adopt with conditions (1 high, 3 medium, 4 low, 6 info): no telemetry, new host, dependency or install-time code; license unchanged. The high finding: run through the `.agents/skills` links, `specify integration upgrade` records resolved paths and its stale-file cleanup deletes the ten core `SKILL.md` files it has just written; conditions C1 to C7 are carried into T028.
- [x] T026 [US2] Check whether a Spec Kit preset with prepend command overrides, beside the existing `linear-issue` preset in `.specify/presets/`, can carry the area-rules pointer for the 20 `speckit-*` skills; if it can, plan moving the pointer there so upgrades stop overwriting local edits (U-2026-10-06l).
  Ledger 2026-10-07: Claude Code Sonnet 5.5 medium (Jev probability 0.71, confidence 0.65). Answer: partly. A preset with prepend overrides can add the pointer and `specify integration upgrade` reapplies enabled presets after rewriting skills, but the pointer line would be duplicated unless removed, and the preset skill writer refuses linked skill folders, so T028 tests it on the scratch copy first. Findings: `slices/s2c/t026/ctx_73be36b124e1/findings.md` in the feature's state folder.
- [x] T027 [US2] Ask the develop orchestrator how its weekly tool-update job will treat Spec Kit, so its first Spec Kit update does not collide with this slice.
  Ledger 2026-10-07: develop keeps the order S2c before the weekly tool-update job (CHE-50); that job needs the same scratch-copy step for Spec Kit (U-2026-10-07a), so S2c records the step for develop to reuse.
- [x] T028 [US2] Pin `specify-cli` at v1.1.0 in `tools/spec-kit/pyproject.toml` (the `uv.lock` entry must name commit `f1d3a4f8337ebbd3ae22760a9c12e3352b93a175` and nothing else in the lock may change). Run `specify integration upgrade --script sh` and `specify extension add agent-context --force` (never `self upgrade` or `check`) in a scratch copy of the repository where the ten core `speckit-*` skill folders are real folders, try T026's preset there, then copy the resulting `SKILL.md` files into `skills/code/` and keep every `.agents/skills` entry a link (U-2026-10-07a; review conditions C1 to C5). Afterwards: `git status` shows no deleted `SKILL.md`; the area-rules pointer is in all 20 skills (by the preset if it works, otherwise re-added); the `.cache/` rule of `.specify/.gitignore` is back; no real `.agents/skills/speckit-git-*` folders remain; `agent-context-config.yml` and root `AGENTS.md` are unchanged; the two agent-context hooks in `.specify/extensions.yml` are set back to `optional: false` by hand (accepted, U-2026-10-07a); `licenses/third-party-notices.md` and `docs/architecture.md` name 1.1.0; installed files match v1.1.0 by hash (C6, C7). Write the scratch-copy procedure into `docs/architecture.md` so develop's weekly tool-update job can reuse it. `taskstoissues` stays in the core in 1.1.0 and the new GitHub extension is opt-in, so nothing changes for it. Depends on T025 to T027.
  Ledger 2026-10-07: implemented by Claude Code Sonnet 5.5 medium (Jev probability 0.40, confidence 0.30) in 45b1391, f146120 and 1e2016f. The upgrade ran in a scratch clone with real `speckit-*` folders; the 20 skills and `.specify/` changes were copied back with every link kept and no skill file deleted; the `speckit-git-*` skills were left out; the `.cache/` rule and the two `optional: false` hooks were restored; `agent-context-config.yml` and root `AGENTS.md` are unchanged; installed files match v1.1.0 by hash. The new `.specify/presets/area-rules-pointer` preset carries the area-rules pointer in all 20 skills, but only when the agent-context extension is re-added before `integration upgrade`, and it adds a generated "# Speckit X Skill" heading; `specify extension add` has no `--script` option in 1.1.0. The procedure is in `docs/architecture.md` for develop's weekly tool-update job. Owned code: no change (the preset is data). Evidence: `slices/s2c/ctx_32ab202265ae/` in the feature's state folder.
- [ ] T029 [US2] **Finish** slice S2c. Depends on T028.

## Phase 5: Slice S3 — dependency checks (User Story 3, P2)

**Goal**: verification fails when a dependency rule breaks.

**Independent test**: quickstart scenario 3; each of D1 to D6 fails on its
fixture in one run (SC-004).

- [ ] T030 [P] [US3] Extend `.config/dependency-cruiser.json` with the ring-direction rules for `domain`, `application`, `adapters`, `entrypoints` and `bootstrap`, the D6 group-matching rule, severity `error` on each; replace `no-package-to-plugin` with a rule that lets `packages/` import `skills/` only for the `workflow` to `clean-code` edge; drop ring names no code uses (FR-007; contracts/dependency-rules.md).
- [ ] T031 [P] [US3] Extend the import-linter contracts in `pyproject.toml`: one `layers` contract over the moved components with optional layers, `protected` contracts for the input and output libraries (D2, D3), and one `protected` contract per Python package with its published modules listed beside it (D4), keeping `acyclic_siblings` (FR-007).
- [ ] T032 [US3] Add one breaking fixture per rule and a test that runs each checker on it and expects failure, in `scripts/clean-architecture-test.ts` and a Python fixture test under `scripts/`; include fixtures that settle cross-root cycles for `acyclic_siblings` and how by-name workspace imports resolve (SC-004). Depends on T030, T031.
- [ ] T033 [US3] **Finish** slice S3. Depends on T032.

## Phase 6: Slice S4 — credit-offers into rings (User Story 3, P2)

**Independent test**: quickstart scenarios 4 and 5 for `credit-offers`
(SC-003).

- [ ] T034 [US3] Split `packages/credit-offers/src/credit_offers/__init__.py` into `domain/` (block boundaries, new-offer selection, answer validation), `application/` (the find-offers use case and its judge port), `adapters/` (tracker HTTP, gated MCP judge, desktop notifier), `entrypoints/cli.py` and `bootstrap.py` with overridable adapters; keep the `credit-offers` command and its output unchanged; read settings through `platformdirs`; add `packages/credit-offers/AGENTS.md` and `README.md` (FR-006, FR-008 to FR-011; plan Decisions 4, 5, 13).
- [ ] T035 [US3] Move `packages/credit-offers/tests/test_credit_offers.py` into `tests/unit/`, `tests/integration/` and `tests/e2e/` with unchanged assertions and the judge faked at its port (FR-013, FR-023). Depends on T034.
- [ ] T036 [US3] **Finish** slice S4. Depends on T035.

## Phase 7: Slice S5 — doc-regions into rings (User Story 3, P2)

- [ ] T037 [US3] Arrange `packages/doc-regions/src/doc_regions/` into rings and `bootstrap.py`, keeping the modules that `wiki-consistency` imports (`config.files`, `regions.scan`, `regions.check`, `regions.update`, `regions.shape`, `regions._split_lf_lines`, `requests.classify_requests`, `requests.verify_requests`, `requests.MAX_CLAIM_CHARS`, `units.split`) importable unchanged; add `packages/doc-regions/AGENTS.md` (pointing to the published list in `pyproject.toml`) and `README.md`. It reads no user settings, only the repository's `scripts/doc-regions.toml` (FR-006, FR-011, D4).
- [ ] T038 [US3] Move `packages/doc-regions/tests/` into scope folders with unchanged assertions; `wiki-consistency`'s tests pass untouched (FR-013). Depends on T037.
- [ ] T039 [US3] **Finish** slice S5. Depends on T038.

## Phase 8: Slice S6 — workflow package (User Story 3, P2)

- [ ] T040 [US3] Create `packages/workflow/` (`package.json`, `src/{domain,application,adapters,entrypoints}/`, `bootstrap.ts`, `AGENTS.md`, `README.md`) from `scripts/workflow*.ts` and `scripts/hash.ts`, keeping `npm run workflow` and `npm run verify` and their CLI contract unchanged; it reads no user settings (FR-006, FR-011; docs/architecture.md "CLI contract").
- [ ] T041 [US3] Move the workflow tests and the CLI-contract snapshots with unchanged assertions; update `package.json`, `turbo.json` and `.config/dependency-cruiser.json` (FR-013). Depends on T040.
- [ ] T042 [US3] **Finish** slice S6. Depends on T041.

## Phase 9: Held work (User Story 4 and the work area)

Each task starts only after its hold is released (FR-016; plan Holds), with
its own plan update and slice.

- [ ] T043 [US4] H1: after the gate's metadata bug is fixed and `system-one-adapter` (or a Pydantic AI provider found first under the reuse order) passes its security review, add the second gated judgment server, the provider profile, the time-limit settings and the judgment port per [contracts/judgment.md](contracts/judgment.md); the user approves its registration in both agents (FR-019 to FR-022, FR-024, SC-007).
- [ ] T044 [US3] H2: after `document-pdf-fidelity`, `exam-calendar`, `korean-web-wiki` and `lexical-semantics` merge and the session-scan trial is decided, move the work skills and `plugins/work/AGENTS.md` to `skills/work/`, decide where the pinned reference-library connector (`plugins/work/package.json` and lock) lives, and arrange `packages/wiki-consistency` into rings.
- [ ] T045 [US3] H3: after `lexical-semantics` merges and the Jev Browser trial is decided, arrange or replace `packages/jev-ultrafast`.
- [ ] T046 [US3] H4: after the chezmoi trial is decided, keep or replace `scripts/secrets-refresh.ts`.

## Dependencies

- S1 (T002 approval) comes first; S2a, S2b, S2c and S3 to S6 follow in order, each
  after the previous slice's finish, so each starts from verified `develop`.
- T010 runs in every prepared checkout before S2a reaches `develop`.
- S3 lands before S4 to S6 so every move is checked.
- The held phase depends on events outside this feature; the develop
  orchestrator reports merges and bug fixes, the user reports trial verdicts.

## Parallel opportunities

- S1: T004 and T005 after the approval.
- S2a: T007, T008 and T009 at once.
- S2b: T018 and T019 beside T017.
- S2c: T025, T026 and T027 at once.
- S3: T030 and T031.

## Implementation strategy

S1, S2a and S2b make the user's retirement decision real (the minimum useful
result). S3 then makes the structure checkable, and S4 to S6 move one
component each, smallest first. A slice that grows past 1,000 changed lines
gets a split review before its develop merge review (root `AGENTS.md`).

## Task ledger

- 2026-10-06: T001 done (see above). Next: T002, the user's approval, asked
  through the develop-worktree coordinator.
- 2026-10-06 about 20:30 KST: T002 to T005 done by the orchestrator (Claude
  Opus 5.5): constitution 3.0.0 in 2b4e96b, AGENTS.md and the architecture
  document in 75f26a1. T006 in progress: the document judgments found the new
  principle IX contradicted only by the plugin packages that S2a and S2b
  remove; the audit's 20 warnings concern constitution lines this slice did
  not change; Jev verified the 8 rule-text claims. Reviewer picked by Jev:
  Codex gpt-6.1-sol medium (probability 0.50, confidence 0.41).
- 2026-10-06 about 20:25 KST: the S1 review (Codex gpt-6.1-sol medium)
  approved after one fix: the quickstart's before-inventory moves from `/tmp`
  to the feature's state folder. The user added the Spec Kit 1.1.0 step
  (U-2026-10-06l) as slice S2c, renumbering later tasks.
- 2026-10-06 about 20:45 KST: a fresh Codex confirmation (gpt-6.1-sol
  medium) found two more quickstart problems (the after-S2b block relied on a
  variable from an earlier shell; a relative `XDG_STATE_HOME` was accepted);
  both fixed as it recommended. Both reviewers' Jev review calls were refused
  by the privacy gate; they finished with their own assessment, as allowed.
- 2026-10-06: T006 finished into develop at 8988dbd, review record f2be377
  for 122daa3. Guarded finish and merged develop each passed 46/46 checks;
  merged run 3KJzXQqB2AxyiiWRCJ4AxGrETUo. CHE-93 remains open; S2a is next.

- 2026-10-07: S2a finished into develop at 6929592, review record d22d90b
  for the built-in-reviewed 07ed1d5/tree 19a2f3f. T010 cleanup is confirmed
  in all prepared checkouts; reviewed Lefthook hooks are installed. Source
  retry, mandatory finish and merged develop each passed 45/45 tasks; merged
  summary 3KKaBgNUHEnOrjbz1CX1Cqzg4fP. The first source command
  passed its tasks but failed after an empty ref change; its logs are kept.
  The built-in review's ungranted full attempt was sandbox-blocked, not a
  passing full run. Authoritative receipts: `$XDG_STATE_HOME/verbose-broccoli/
  workspaces/develop/clean-architecture-s2a/attempt-20261006t164714z/`.
  CHE-93 stays open for S2b and later slices; S1's historical built-in
  follow-through remains with the architecture owner.

- 2026-10-07: S2b finished into develop at 83b6fba, review record 23acde5
  for 1f63043 (renewed Codex built-in review, no actionable defects). Source,
  mandatory finish and merged develop passed 45/45 tasks; merged summary
  3KLPlrXrroNPzXpelDwfASA0xG0. The mandatory hook summary
  3KLOvXnZdApIXcUzq5QxfWQOpIw ran inside the finish command despite no
  pre-hook output in its log. Receipts: `$XDG_STATE_HOME/verbose-broccoli/
  workspaces/develop/clean-architecture-s2b/attempt-20261007t002945z/`.
  The existing owner continues with S2c; CHE-93 stays open.
