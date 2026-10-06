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
other-provider review with only the slice's scope and requirements; resolve
findings and verify again; commit the review record; ask the develop
orchestrator for the finish slot; after the finish, `develop` verifies
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
- [ ] T003 [US1] Amend `.specify/memory/constitution.md` with the approved text: replace principle IX, change the wording of VI, VII and Governance, add the dated Governance paragraph, update the Sync Impact Report, and set version 3.0.0 with `npm run constitution:bump -- MAJOR` in a `!` commit (FR-015). Depends on T002.
- [ ] T004 [P] [US1] Change the opening line and the plugin packaging rule of `AGENTS.md` as approved; leave the pointers and "code plugin's" phrases for S2b (FR-001, FR-015). Depends on T002.
- [ ] T005 [P] [US1] Retitle `docs/architecture.md` and rewrite its opening and "Package and runtime ownership" to describe skill areas, component packages and the holds, keeping the plugin sections S2a removes (FR-001, FR-016).
- [ ] T006 [US1] **Finish** slice S1, including a Jev check of the final rule text against its cited rows (SC-005). Depends on T003 to T005.

## Phase 2: Slice S2a — plugin packaging removed (User Story 2, P1)

**Goal**: no plugin manifest, generator or distribution route remains, and
agents still find every skill and server.

**Independent test**: quickstart scenario 2; the skill links and skills
validate as before; the reference-library guard test still passes.

- [ ] T007 [US2] Read-only security review of `skills-ref` 0.1.1 and its dependencies (`click`, `strictyaml`) with evidence for every finding, in `specs/060-clean-architecture/security/skills-ref-review.md` (FR-018). The reviewer stays on Claude Code or Codex (security judgment).
- [ ] T008 [US2] Record the before-inventory from `develop`: `ls .agents/skills`, `claude mcp list`, `codex mcp list`, in the slice's evidence folder under `$XDG_STATE_HOME/verbose-broccoli/workspaces/feature-clean-architecture/` (SC-001).
- [ ] T009 [US2] Recheck that no open feature branch changes `plugins/work/plugin.json`, `plugins/work/mcp.json`, `plugins/work/skills/jev` or `plugins/work/AGENTS.md` (plan Holds, "H2 exception"); stop and report if one does (FR-016).
- [ ] T010 [US2] With the develop orchestrator, run the existing `npm run plugins:clean-codex` and delete the ignored `.mcp.json` in each prepared checkout (develop, feature-clean-architecture, document-pdf-fidelity, evp-oewn-senses, exam-calendar, korean-web-wiki, weekly-tool-update; the primary checkout had no generated block on 2026-10-06, recheck it) while the command still exists in each, and record the evidence (FR-005). In this worktree it runs before T011.
- [ ] T011 [US2] Delete the plugin packaging: `plugins/*/plugin.json`, `plugins/code/mcp.json`, `plugins/work/mcp.json`, `plugins/code/package.json`, `scripts/plugin-clients.ts`, `scripts/plugin-skills-test.ts`, `scripts/plugins-validate-test.ts`, `scripts/vendor/agent-plugins/`, `tools/check-jsonschema/`, `docs/reference/plugins.md`, `doc_sources.plugin_table` and its tests in `scripts/doc_sources_test.py`; remove their `package.json` scripts, `turbo.json` tasks, the `scripts/doc-regions.toml` target and the `check-jsonschema` lines of `scripts/toolchain.sh` and `.config/mise.toml` (setup and doctor), and the `public-api:plugins/code` entry of `.config/dependency-cruiser.json` that reads the deleted manifest (FR-005). Depends on T009, T010.
- [ ] T012 [US2] Rewrite `scripts/reference-library-test.ts` so it no longer reads `plugins/work/mcp.json`, keeping its checks of the connector pin and lock in `plugins/work/package.json`, of the blocked tools in the pinned connector, and of the deny rules in `.claude/settings.json` (FR-004). Depends on T011.
- [ ] T013 [US2] Add `tools/skills-ref/` (a uv project pinning `skills-ref` 0.1.1), a `skills:validate` task over `skills/*/*/`, `tools/ponytail/skills/*/` and `plugins/*/skills/*/`, and `scripts/skills-links-test.ts` checking that each `.agents/skills` link resolves to exactly one allowed skill folder, that no name repeats and that no skill folder lacks a link, with the allowed folders read from one list that S2b extends (FR-002, FR-003; contracts/delivery.md). Depends on T007.
- [ ] T014 [US2] Update the documents for the removal: `docs/architecture.md` (remove the generator text of "Live checkout discovery" and "Optional copied client packages"; keep the skills table), `README.md` (installing elsewhere with `skills` and `add-mcp`), `docs/reference/commands.md` (regenerate), and `scripts/clean-architecture-test.ts` and other tests that name removed rules or files (FR-003, FR-005).
- [ ] T015 [US2] Run quickstart scenario 2 (FR-003 to FR-005). Depends on T010 to T014.
- [ ] T016 [US2] **Finish** slice S2a. Depends on T015.

## Phase 3: Slice S2b — skills moved into areas (User Story 2, P1)

**Goal**: each skill exists once at `skills/<area>/<name>/` (or in the
Ponytail bundle), found through `.agents/skills`.

**Independent test**: quickstart scenario 1; fresh Claude Code and Codex
sessions list the same skill and server names as before S2a, once each
(SC-001, SC-002 second part).

- [ ] T017 [US2] Move the code area: `git mv plugins/code/skills/<name> skills/code/<name>` for every skill except Ponytail's four, `plugins/code/AGENTS.md` to `skills/code/AGENTS.md`; change each skill's rules pointer to `../AGENTS.md` and fix relative links in `skills/code/model-choice/references/` and other moved files (FR-003a, FR-002). Depends on T002 (Ponytail decision).
- [ ] T018 [P] [US2] Move the chat area: `plugins/chat/skills/*`, `plugins/chat/AGENTS.md` and `plugins/chat/LICENSE` to `skills/chat/` (FR-003a).
- [ ] T019 [P] [US2] Move Ponytail as one unchanged upstream bundle to `tools/ponytail/` (`hooks/`, `tests/`, `skills/ponytail{,-audit,-debt,-review}/`, licenses, `upstream.md`), retarget `.agents/ponytail` to `../tools/ponytail` so `.codex/hooks.json` stays byte-identical, and update `upstream.md` (plan Decision 10); or apply the alternative the user chooses in T002. Depends on T002.
- [ ] T020 [US2] Retarget every link in `.agents/skills/` to `skills/<area>/<name>`, `tools/ponytail/skills/<name>` or, for held work skills, `plugins/work/skills/<name>`; delete the duplicate `plugins/work/skills/jev`; extend the link test's allowed folders (FR-002, FR-003). Depends on T017 to T019.
- [ ] T021 [US2] Update every remaining `plugins/code` or `plugins/chat` path: `.config/dependency-cruiser.json`, `eslint.config.js`, `eslint.ignores.js`, `tsconfig.json`, `.github/workflows/audit.yml`, `pyproject.toml`, `package.json` (workspaces gain `skills/code/clean-code`; the `clean-architecture` script also scans `skills` and `tools/ponytail`), `scripts/workflow.ts` (import the CLI serializer by package name), `scripts/workflow-skills.ts`, `scripts/doc-regions.toml` (`report_only` glob for area `AGENTS.md` files), the tests under `scripts/` that name these paths, `docs/examples/wiki/AGENTS.md`, and `licenses/third-party-notices.md` (plan Decision 9).
- [ ] T022 [US2] Update the rule pointers and documents: `docs/architecture.md` "Skill source ownership" and its Cog skill table glob, root `AGENTS.md` pointers, lessons line and "code plugin's" phrases, `.claude/rules/claude-code.md`, and the area `AGENTS.md` files' plugin wording (FR-003, FR-011, SC-002).
- [ ] T023 [US2] Run quickstart scenario 1 and record the after-inventory from fresh Claude Code and Codex sessions; report any installed plugin copies in user folders to the user without removing them (SC-001, spec Edge Cases). Depends on T020 to T022.
- [ ] T024 [US2] **Finish** slice S2b. Depends on T023.

## Phase 4: Slice S3 — dependency checks (User Story 3, P2)

**Goal**: verification fails when a dependency rule breaks.

**Independent test**: quickstart scenario 3; each of D1 to D6 fails on its
fixture in one run (SC-004).

- [ ] T025 [P] [US3] Extend `.config/dependency-cruiser.json` with the ring-direction rules for `domain`, `application`, `adapters`, `entrypoints` and `bootstrap`, the D6 group-matching rule, severity `error` on each; replace `no-package-to-plugin` with a rule that lets `packages/` import `skills/` only for the `workflow` to `clean-code` edge; drop ring names no code uses (FR-007; contracts/dependency-rules.md).
- [ ] T026 [P] [US3] Extend the import-linter contracts in `pyproject.toml`: one `layers` contract over the moved components with optional layers, `protected` contracts for the input and output libraries (D2, D3), and one `protected` contract per Python package with its published modules listed beside it (D4), keeping `acyclic_siblings` (FR-007).
- [ ] T027 [US3] Add one breaking fixture per rule and a test that runs each checker on it and expects failure, in `scripts/clean-architecture-test.ts` and a Python fixture test under `scripts/`; include fixtures that settle cross-root cycles for `acyclic_siblings` and how by-name workspace imports resolve (SC-004). Depends on T025, T026.
- [ ] T028 [US3] **Finish** slice S3. Depends on T027.

## Phase 5: Slice S4 — credit-offers into rings (User Story 3, P2)

**Independent test**: quickstart scenarios 4 and 5 for `credit-offers`
(SC-003).

- [ ] T029 [US3] Split `packages/credit-offers/src/credit_offers/__init__.py` into `domain/` (block boundaries, new-offer selection, answer validation), `application/` (the find-offers use case and its judge port), `adapters/` (tracker HTTP, gated MCP judge, desktop notifier), `entrypoints/cli.py` and `bootstrap.py` with overridable adapters; keep the `credit-offers` command and its output unchanged; read settings through `platformdirs`; add `packages/credit-offers/AGENTS.md` and `README.md` (FR-006, FR-008 to FR-011; plan Decisions 4, 5, 13).
- [ ] T030 [US3] Move `packages/credit-offers/tests/test_credit_offers.py` into `tests/unit/`, `tests/integration/` and `tests/e2e/` with unchanged assertions and the judge faked at its port (FR-013, FR-023). Depends on T029.
- [ ] T031 [US3] **Finish** slice S4. Depends on T030.

## Phase 6: Slice S5 — doc-regions into rings (User Story 3, P2)

- [ ] T032 [US3] Arrange `packages/doc-regions/src/doc_regions/` into rings and `bootstrap.py`, keeping the modules that `wiki-consistency` imports (`config.files`, `regions.scan`, `regions.check`, `regions.update`, `regions.shape`, `regions._split_lf_lines`, `requests.classify_requests`, `requests.verify_requests`, `requests.MAX_CLAIM_CHARS`, `units.split`) importable unchanged; add `packages/doc-regions/AGENTS.md` (pointing to the published list in `pyproject.toml`) and `README.md`. It reads no user settings, only the repository's `scripts/doc-regions.toml` (FR-006, FR-011, D4).
- [ ] T033 [US3] Move `packages/doc-regions/tests/` into scope folders with unchanged assertions; `wiki-consistency`'s tests pass untouched (FR-013). Depends on T032.
- [ ] T034 [US3] **Finish** slice S5. Depends on T033.

## Phase 7: Slice S6 — workflow package (User Story 3, P2)

- [ ] T035 [US3] Create `packages/workflow/` (`package.json`, `src/{domain,application,adapters,entrypoints}/`, `bootstrap.ts`, `AGENTS.md`, `README.md`) from `scripts/workflow*.ts` and `scripts/hash.ts`, keeping `npm run workflow` and `npm run verify` and their CLI contract unchanged; it reads no user settings (FR-006, FR-011; docs/architecture.md "CLI contract").
- [ ] T036 [US3] Move the workflow tests and the CLI-contract snapshots with unchanged assertions; update `package.json`, `turbo.json` and `.config/dependency-cruiser.json` (FR-013). Depends on T035.
- [ ] T037 [US3] **Finish** slice S6. Depends on T036.

## Phase 8: Held work (User Story 4 and the work area)

Each task starts only after its hold is released (FR-016; plan Holds), with
its own plan update and slice.

- [ ] T038 [US4] H1: after the gate's metadata bug is fixed and `system-one-adapter` (or a Pydantic AI provider found first under the reuse order) passes its security review, add the second gated judgment server, the provider profile, the time-limit settings and the judgment port per [contracts/judgment.md](contracts/judgment.md); the user approves its registration in both agents (FR-019 to FR-022, FR-024, SC-007).
- [ ] T039 [US3] H2: after `document-pdf-fidelity`, `exam-calendar`, `korean-web-wiki` and `lexical-semantics` merge and the session-scan trial is decided, move the work skills and `plugins/work/AGENTS.md` to `skills/work/`, decide where the pinned reference-library connector (`plugins/work/package.json` and lock) lives, and arrange `packages/wiki-consistency` into rings.
- [ ] T040 [US3] H3: after `lexical-semantics` merges and the Jev Browser trial is decided, arrange or replace `packages/jev-ultrafast`.
- [ ] T041 [US3] H4: after the chezmoi trial is decided, keep or replace `scripts/secrets-refresh.ts`.

## Dependencies

- S1 (T002 approval) comes first; S2a, S2b and S3 to S6 follow in order, each
  after the previous slice's finish, so each starts from verified `develop`.
- T010 runs in every prepared checkout before S2a reaches `develop`.
- S3 lands before S4 to S6 so every move is checked.
- The held phase depends on events outside this feature; the develop
  orchestrator reports merges and bug fixes, the user reports trial verdicts.

## Parallel opportunities

- S1: T004 and T005 after the approval.
- S2a: T007, T008 and T009 at once.
- S2b: T018 and T019 beside T017.
- S3: T025 and T026.

## Implementation strategy

S1, S2a and S2b make the user's retirement decision real (the minimum useful
result). S3 then makes the structure checkable, and S4 to S6 move one
component each, smallest first. A slice that grows past 1,000 changed lines
gets a split review before its develop merge review (root `AGENTS.md`).

## Task ledger

- 2026-10-06: T001 done (see above). Next: T002, the user's approval, asked
  through the develop-worktree coordinator.
