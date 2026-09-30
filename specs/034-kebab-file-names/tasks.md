---

description: "Task list for Kebab-case file names"
---

# Tasks: Kebab-case file names

**Input**: Design documents from `specs/034-kebab-file-names/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: The naming check itself is the test: it must pass on the renamed
tree inside `npm run verify` and fail on a scratch `Bad_Name.md` (SC-001,
SC-002). The existing checks prove that references still resolve.

**Organization**: Main (a Claude Code orchestrator) owns the records, the
configuration, the renames, the vault commits and integration. Every
worker's agent, model and effort is chosen with the code plugin's
`model-choice` skill; the security review and the final review come from
Codex, the provider other than the implementer's.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US3)

---

## Phase 1: Security check

- [x] T001 [US1] Review ls-lint 2.3.1's source and release read-only
  (FR-001); report in [security/ls-lint-2.3.1.md](security/ls-lint-2.3.1.md).
  - 2026-09-30: Codex `gpt-daybreak-blue-latest` at high (backfire:
    0.78, confidence 0.74), time budget 35 minutes (backfire: 0.51).
    Verdict: acceptable with controls; 0 high, 2 medium (checksum-only
    release; exponential work on names with many dots), 1 low (wildcard
    config paths follow symlinks). The user, through the `develop` session,
    accepted ls-lint with the three controls: every platform checksum locked
    and `--locked` installs, a 60-second timeout that fails the check, and
    literal paths only in `.ls-lint.yml`.

## Phase 2: Naming check

- [x] T002 [US1] Pin ls-lint in `mise.toml` and `mise.lock`, add it to
  `orca.yaml`'s setup and CI's install line (FR-001). The seven locked
  checksums match the reviewed release assets.
- [x] T003 [US1] Write `.ls-lint.yml` with the exception list and its
  reasons, and run it in `npm run verify` (FR-002, FR-003). A probe tree
  confirmed that `Bad_Name.md`, `docs/NewPage.md`, `scripts/new_tool.ts`,
  `Makefile`, `Bad_Dir/`, `.Hidden_Dir/` and `scripts/bad-module.py` fail,
  and that `LICENSE`, `AGENTS.md`, `README.md`, `SKILL.md`, `.github/`,
  snake_case Python files and packages, and `raw_import.py.lock` pass. Before
  the renames it reports exactly the 130 paths of T006 and the Vale style
  folder `Wiki/`.

## Phase 3: Vault schemas

- [x] T004 [P] [US3] Add the naming rule to the schema template and the
  `default`, `chat` and `code` vault schemas (FR-006). 2026-09-30: vault
  commits `9beb59f` (default), `08a8761` (chat) and `2999422` (code). Their
  tracked Wiki files were already kebab-case. Their student-page line still
  names pages by student name until CHE-61's template change reaches them.
- [ ] T005 [US3] Add the naming rule to the `work` vault schema after CHE-61
  has finished (FR-006).

## Phase 4: Renames

- [ ] T006 [US2] In the granted finish slot, merge the newest `develop`,
  rename every remaining non-kebab path with `git mv`, update every
  reference, and commit the renames as one commit (FR-004, FR-005).

## Phase 5: Review and finish

- [ ] T007 Develop merge review by a fresh Codex reviewer; finish into
  `develop`; move CHE-63 to Done.
