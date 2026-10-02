# Feature Specification: Live Plugin Discovery

**Feature Branch**: `feature/live-plugin-discovery`
**Created**: 2026-10-02
**Status**: Implementation committed; follow-up safety and integration gates pending
**Issue**: CHE-82

## Assumptions

Use `backfire-code` and `backfire-education` as the distinct skill names.
Support the installed Linux clients first; document other platforms only when
their behavior has evidence. Local discovery uses the current checkout and its
installed dependencies. Existing client installations may also expose packaged
skills; acceptance must identify canonical local source paths explicitly.

## User Scenarios & Testing

### User Story 1 - Edit one skill source (Priority: P1)

A developer edits a skill in its owning plugin and both native clients can read
that edit through shared local discovery without reinstalling a plugin.

**Independent test**: In fresh Codex and Claude sessions, inspect skill discovery
and paths. Change a synthetic source skill and observe changed content through
each native client, including normal invocation when installed copies remain
enabled.

**Acceptance scenarios**:

1. A prepared checkout contains a real `.agents/skills` directory whose individual
   relative links resolve to canonical plugin skill directories, and
   `.claude/skills` is a relative link to that shared directory.
2. Both clients discover distinct Backfire skills with matching folder and
   frontmatter names and descriptions that distinguish their data boundaries.
3. Relative assets, helpers, plugin rules and references resolve from each
   canonical skill directory; package resources remain inside their plugin root.

### User Story 2 - Discover local tools (Priority: P1)

A developer opens the repository and each native client discovers the existing
code Backfire, education Backfire and reference-library servers from supported
project configuration, resolved to that checkout.

**Independent test**: Native config/server discovery and metadata-only tools
listing identify all three servers, distinct mode arguments and tool names.

**Acceptance scenarios**:

1. Each mode has one canonical server declaration reused by the local generator.
2. Code retains its student-data prohibition and education retains its privacy
   gate; reference-library retains destructive-tool denials.
3. No real library, vault, student or provider operation is needed for acceptance.

### User Story 3 - Prepare safely and distribute separately (Priority: P2)

A developer runs reviewed setup in a fresh checkout or worktree, then reruns it
without losing user-owned skill directories or server configuration. Optional
copied distribution remains separately available and validates as before.

**Independent test**: Synthetic moved checkout, rerun, broken/stale links and
conflict fixtures; existing distribution regression checks.

## Requirements

- **FR-001**: Keep one canonical skill body in its owning plugin; create only
  relative directory links in the shared local index and Claude discovery root.
- **FR-002**: Rename Backfire folders/frontmatter and active references to unique,
  standards-valid names; preserve historical records, attribution, licenses and
  shared tool-reference equality.
- **FR-003**: Reuse `scripts/plugin-clients.ts`, Node filesystem support and
  existing setup. Add no installer, dependency, framework or Windows copy layer.
- **FR-004**: Separate live local discovery from copied installation/distribution.
  Document actual session/reload boundaries and duplicate packaged entries.
  Normal native invocation must select the live source with installed copies
  enabled; source listings alone do not establish this behavior.
- **FR-005**: Generate supported project MCP configuration from canonical plugin
  declarations with current checkout paths and no global client mutation.
- **FR-006**: Preserve existing user-owned directories/files and fail clearly on
  unsafe conflicts. Detect broken/stale links, duplicate names and declarations.
- **FR-007**: Preserve portable packaging, plugin-local resources, mode separation
  and reference-library destructive-tool restrictions.
- **FR-008**: Add meaningful source-visibility, resource-resolution, fresh-location,
  idempotence and conflict regression checks; verify actual native client behavior.
- **FR-009**: No credentials or private data reads, global installs/uninstalls,
  client restart, new providers, external runtime changes, push or publication.
  Publication manifests and release/version automation remain deferred.
- **FR-010**: Keep discovery ownership receipts and retained acceptance/judgment
  evidence in persistent state; keep reproducible copied distribution in cache.
  Honor absolute XDG roots, using standard home defaults for unset, empty or
  relative values. Namespace each by project, worktree and task. Project client
  configuration keeps its supported location; `.local/` holds disposable copies.
  Removing disposable copies must not lose ownership, progress or paid results.
- **FR-011**: Permanent producer state/cache use a stable operation namespace.
  Different checkout paths must have separate receipt, output, staging and
  recovery paths even when their folder basenames match. Moving a configured
  checkout requires explicit receipt transfer; do not borrow another's ownership.

## Success Criteria

- **SC-001**: Fresh local sessions of both installed clients identify unique
  local skills and their canonical source paths, with visible source edits.
- **SC-002**: Native MCP config/discovery lists all existing servers and
  metadata-only health/tools evidence, without data operations.
- **SC-003**: Focused regressions and one same-run full verification pass on
  the integrated snapshot; material limits are recorded explicitly.
- **SC-004**: Fresh cross-provider review completes with actionable findings
  resolved; develop receives the reviewed clean tip for its integration slot.
- **SC-005**: Storage regressions establish rerun durability, safe legacy receipt
  import, XDG defaults, same-name worktree isolation and reproducible distribution.
