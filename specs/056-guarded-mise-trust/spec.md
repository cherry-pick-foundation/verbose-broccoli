# Feature Specification: Guarded mise trust

**Feature Branch**: `feature/guarded-mise-trust`
**Created**: 2026-10-05
**Status**: Verified; independent review accepted by develop; integration pending
**Issue**: CHE-89
**Input**: Renew mise trust after checkout or merge only for changed configuration whose current bytes equal committed local develop.

## User Scenarios & Testing

### User Story 1 - Keep reviewed tools usable (Priority: P1)

A developer switches branches or merges reviewed configuration without having to trust identical reviewed content again.

**Why this priority**: Lost trust blocks the tools needed to run the existing hooks.
**Independent Test**: Install hooks in a synthetic repository and check matching and differing checkout/merge content while Node is unavailable.

**Acceptance Scenarios**:

1. Given changed configuration matching local develop exactly, when a branch checkout or merge finishes, then trust is renewed for that file only.
2. Given unreviewed feature or dirty working content, when either event finishes, then no trust is granted.
3. Given unchanged branch configuration or no committed local develop configuration, when either event finishes, then no trust is granted.
4. Given unavailable Node and Python runtimes, when eligible content arrives, then the trust hook still works.
5. Given an ordinary commit, linked worktree or Ponytail resume, when the existing behavior runs, then the feature preserves it.

### Edge Cases

Missing configuration, symbolic links, invalid branch/merge event revisions and missing develop fail closed. Initial all-zero checkout revisions remain on the existing setup/manual trust path. Checkout and merge must not fail in a worktree lacking installed dependencies; commit checks still refuse. Exact bytes matter even with Git attributes or line-ending conversion. A failed trust command reports failure. Configuration that changes only on an unreviewed branch requires manual trust.

## Requirements

### Functional Requirements

- **FR-001**: Renew trust after configuration-changing branch checkout or merge; safely renew matching trust after file-only checkout.
- **FR-002**: The current regular file must equal the committed local develop bytes before trust is invoked.
- **FR-003**: Differing, missing or uncheckable content must remain manually trusted.
- **FR-004**: The entry path must work before Node/Python through mise are trusted.
- **FR-005**: Reuse the existing hook installer and preserve commit checks, shared-hook worktree behavior and the Ponytail resume matcher.
- **FR-006**: Coordinate shared installation with develop after independent review; install before full verification so the existing doctor can validate it.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All eligible checkout and merge fixtures renew trust for exactly one file.
- **SC-002**: All differing, unchanged-branch and missing-reference fixtures make zero trust calls.
- **SC-003**: Existing commit acceptance and refusal cases continue to pass.

## Assumptions

Local `develop` is the reviewed authority. Branch events compare the event's old/new committed trees. File-only checkout events provide no prior file snapshot; they safely renew trust only for current committed-develop bytes, even when unchanged. The existing installed native Lefthook package and system shell/Git/mise are available. No runtime installation, global configuration, account change, push or deployment is authorized.
