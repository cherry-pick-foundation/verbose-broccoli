# Feature Specification: Provider Keys from Bitwarden Secrets Manager

**Feature Branch**: `feature/provider-secrets`

**Created**: 2026-10-01

**Status**: In progress

**Linear issue**: CHE-77

**Input**: Linear issue CHE-77, "Provider keys from Bitwarden Secrets Manager
through bws, with one refresh command". Provider API keys live only in
locked-down files under `~/.config/verbose-broccoli/providers/` (seven files
on 2026-10-01), with no backup and no single place to change them. The user
decided the same day:

- Agents get keys through Bitwarden Secrets Manager, with a machine account
  that reaches one project holding only the provider keys: read and write for
  the first import, then read only.
- The machine account's access token is saved by the user in
  `providers/bitwarden.env` as `BWS_ACCESS_TOKEN=...` (mode 600). Nobody
  prints or copies it.
- The tool is `bws`, pinned through mise from Bitwarden's release files after
  a short security review.
- One refresh command rewrites the key files from Secrets Manager, so backfire
  and the other key readers keep working unchanged.
- The project ID and the secret-to-file mapping live outside the repository,
  and repository names stay provider-neutral.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - bws is reviewed and pinned (Priority: P1)

The user can read why bws 2.1.0 is safe enough to run on this laptop, and every
machine installs the same bytes.

**Independent Test**: `mise install --locked` installs `bws 2.1.0`; the review
record cites file and line for what bws sends where, where it keeps state, how
a value can leak and its license.

**Acceptance Scenarios**:

1. **Given** the pinned lock, **When** a machine installs bws, **Then** mise
   checks each asset's SHA-256 from `mise.lock`.
2. **Given** the review, **When** an agent plans to use a bws command, **Then**
   the record says which commands expose a value and how to avoid it.

### User Story 2 - One command rewrites the key files (Priority: P1)

An agent or the user runs `npm run secrets:refresh` and every key file named in
the operator configuration is rewritten from the Secrets Manager project, so
backfire reads it as before.

**Independent Test**: With a fake `bws` and fake keys, the command writes each
file as `<variable>=<key>` lines with mode 600, owned by the user, and prints no
value.

**Acceptance Scenarios**:

1. **Given** a project with the mapped secrets, **When** the command runs,
   **Then** each key file holds exactly its mapped variables in the configured
   order and passes backfire's `load_credential` checks.
2. **Given** a mapped secret that is missing, or a failing `bws`, **When** the
   command runs, **Then** it exits non-zero, names the secret (never a value)
   and leaves every key file as it was.
3. **Given** the access token file is not mode 600, **When** the command runs,
   **Then** it refuses before it starts `bws`.

### User Story 3 - The current keys move into the project (Priority: P2)

The seven current key files are imported once; the refresh then reproduces
files with identical contents. Afterwards the machine account is read only,
refresh still works and a write is refused.

**Independent Test**: SHA-256 of each key file before the refresh equals the
hash after; a `secret create` with the read-only token fails.

### Edge Cases

- A key file that lacked a final line break (`gemini.env`, `vercel.env` on
  2026-10-01) is rewritten with one; backfire strips it, so its behavior does
  not change. The import normalizes the two files first, so the hash check
  compares like with like.
- A value that is empty or holds a line break would corrupt the one-line
  format: the command refuses it.
- Two secrets with the same name in the project: the command refuses.
- A secret in the project that no file maps (an unused key) is ignored.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST pin bws 2.1.0 through mise from Bitwarden's
  release files, with every platform's SHA-256 in `mise.lock`, and MUST hold a
  security review of it in `security/bws-2.1.0.md`.
- **FR-002**: `npm run secrets:refresh` MUST rewrite each key file named by the
  operator configuration from `bws secret list <project> --output json`, one
  `<secret name>=<value>` line per mapped secret in the configured order.
- **FR-003**: The command MUST write each file by creating a mode 600 temporary
  file in the same folder and renaming it, and MUST write no file when any
  mapped secret is missing, empty, duplicated or holds a line break.
- **FR-004**: The command MUST read the access token only from
  `providers/bitwarden.env` (mode 600, regular file, owned by the user), pass it
  to bws through the environment (never an argument) and start bws with an
  environment of `PATH`, `HOME` and the token only.
- **FR-005**: The command MUST print file names and counts only, never a
  secret value or the token.
- **FR-006**: The project ID and the secret-to-file mapping MUST come from
  `$XDG_CONFIG_HOME/verbose-broccoli/secrets.json`, outside the repository.
- **FR-007**: Backfire's documentation MUST describe the refresh and the
  operator configuration where it describes key files.

## Success Criteria *(mandatory)*

- **SC-001**: The offline tests (fake `bws`, fake keys) pass inside
  `npm run verify`.
- **SC-002**: After the import, a refresh leaves every key file's SHA-256
  unchanged; after the user switches the machine account to read only, refresh
  still works and a write is refused.
- **SC-003**: `npm run verify` prints VERIFIED.

## Assumptions

- `bws secret list <project>` returns a secret's `key` and `value` in JSON
  (`crates/bws/src/render.rs:395-407`; checked against the fake in the tests,
  and against the real service in SC-002).
- The access token is not a secret that the repository can hold; the user
  saves it, and a rotated token only needs the file replaced.
