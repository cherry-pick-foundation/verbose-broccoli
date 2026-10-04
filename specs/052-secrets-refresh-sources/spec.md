# Feature Specification: Multi-source Secrets Refresh

**Feature Branch**: `feature/secrets-refresh-sources`

**Created**: 2026-10-04

**Status**: In progress

**Linear issue**: CHE-85

**Input**: Extend the existing refresh to independently configured sources and a fixed set of local client files.

## User Scenarios & Testing

### User Story 1 - Refresh independent sources (Priority: P1)

The operator refreshes provider and client credentials from several sources in one command, without moving tokens into the repository.

**Why this priority**: Separate credentials must remain bound to their own project and server.

**Independent Test**: Two synthetic sources return different values, with distinct tokens, projects and servers; each configured source is fetched once.

**Acceptance Scenarios**:

1. **Given** two sources, **When** refresh runs, **Then** each receives its own token and explicit HTTPS server, including the default when omitted.
2. **Given** any invalid token or source failure, **When** refresh runs, **Then** all targets retain their bytes and modes; invalid tokens prevent every fetch.

### User Story 2 - Share secrets without erasing settings (Priority: P1)

The operator maps one secret to several variables or files while keeping comments and other settings.

**Why this priority**: Client files also hold settings that refresh must preserve.

**Independent Test**: Shared-secret aliases refresh two variables and two files; comments, blank lines and an unmapped identifier remain byte-for-byte unchanged.

**Acceptance Scenarios**:

1. **Given** an existing variables file, **When** refresh runs, **Then** mapped lines change in place, missing variables append in configured order and unmapped bytes remain unchanged.
2. **Given** an allowed content target, **When** refresh runs, **Then** its non-empty secret is written exactly, including line breaks.
3. **Given** duplicate mapped variables, duplicate resolved targets or both target kinds, **When** refresh runs, **Then** it refuses without changing targets.

### User Story 3 - Keep writes within approved locations (Priority: P1)

The operator can refresh only provider files and the explicitly approved client files.

**Why this priority**: A typo must not turn refresh into a general file writer or overwrite its credentials.

**Independent Test**: Unsafe paths, aliases, file kinds and permissions are rejected; successful files are mode 600 and owned by the operator.

**Acceptance Scenarios**:

1. **Given** a token/operator alias, symlink or unapproved target, **When** refresh runs, **Then** it refuses before writing.
2. **Given** a missing, foreign-owned or writable parent, **When** refresh runs, **Then** it refuses without creating directories.

### Edge Cases

Malformed JSON/schema or fetch responses; unknown sources; empty maps; invalid variable names; missing, duplicate or empty secrets; line breaks in line values; non-absolute or empty XDG configuration root; existing files without final newlines; mixed line endings; symlink parents and hard-link aliases; unused configured sources; temporary-file preparation failure.

## Requirements

### Functional Requirements

- **FR-001**: Configuration MUST use sources with explicit token files, projects and optional HTTPS servers, and files mapping one source to either variables or content. Old single-project configuration is unsupported.
- **FR-002**: Every configured token MUST be a regular file, mode 600, owned by the user and read without following symlinks; all tokens MUST be checked before any fetch.
- **FR-003**: Each configured source MUST be fetched once with only PATH, HOME, its token and an explicit server URL in the child environment; default server is `https://vault.bitwarden.com`; umask is 077 and the token never enters arguments.
- **FR-004**: Every source response and requested value MUST be validated before target changes. Configuration, token, fetch, missing/duplicate/empty value and unsafe/ambiguous target failures MUST leave all target bytes and modes unchanged.
- **FR-005**: Variables targets MUST preserve unmapped bytes and mapped-line positions, reject duplicate mapped variables, append missing variables in configured order, and reject empty or multiline values. A secret MAY feed several variables and files.
- **FR-006**: Content targets MUST write a non-empty value exactly, permitting line breaks.
- **FR-007**: Plain names matching the existing SAFE_FILE rule MUST resolve to providers. Other variables targets MUST be only HOME/.omp/agent/.env, config/ocis-mcp/client.env and config/ocis-mcp/cloudflare-client.env; content MUST be only config/gws/client_secret.json. Config uses absolute XDG_CONFIG_HOME, otherwise HOME/.config.
- **FR-008**: Targets MUST reject token/operator aliases, `..` segments, symlinks including parent aliases, duplicate resolved paths, non-regular or foreign-owned existing files, and missing/foreign-owned/group- or world-writable parents. Kind mismatches, both kinds, unknown fields/sources, empty maps and invalid variable names MUST be refused.
- **FR-009**: All temporary files MUST be prepared before any rename. Written files MUST be mode 600 and user-owned. There is no cross-file transaction or rollback guarantee after renames begin.
- **FR-010**: Output MUST contain only target names/paths and counts on success and sanitized generic failures; no values, tokens, project IDs, server URLs, captured child stderr or unsafe exception payloads.
- **FR-011**: Existing bws pin, Node built-ins and backfire readers MUST remain unchanged; no new dependency, runtime or package script is required.
- **FR-012**: Operator examples MUST use placeholders only and cover two sources, current provider files, OMP aliases, ownCloud shared-secret files, Cloudflare identifier preservation and optional GWS content.

### Key Entities

Source: token-file path, project and optional server. Target: configured key, resolved fixed path, source reference and variables or content mapping. Secret: name/value from one source, never committed.

## Success Criteria

- **SC-001**: Offline fixtures refresh two sources, aliases, preserved settings and exact content with correct owner and mode.
- **SC-002**: Every configured pre-write failure case leaves every target byte and mode unchanged, with zero fetches for token-preflight failures.
- **SC-003**: Success and failure output expose zero synthetic values, tokens, project IDs or server URLs, and arguments expose zero tokens.
- **SC-004**: Narrow tests, lint/type checks and scope checks pass; full repository verification and an independent other-provider review precede integration.

## Assumptions

Token paths and non-provider targets are absolute literal paths; no tilde or environment expansion occurs in JSON. Every configured token is checked, including unused configured sources; all configured sources are fetched. Existing file ownership is required, but existing target modes may be tightened to 600. Concurrent hostile filesystem replacement and rollback after a rename failure are outside this single-user command's contract.
