# Research: Multi-source Secrets Refresh

## Decisions

**Decision**: Reuse bws 2.1.0 and its existing JSON list command once per configured source. **Rationale**: The source review and pin already exist in [041](../041-provider-secrets/security/bws-2.1.0.md); no new upstream adoption is needed. **Alternatives considered**: Direct SDK integration and credential-reader changes add ownership without meeting a new need.

**Decision**: Keep the proposed sources/files shape, require literal absolute token paths and reject unknown fields. **Rationale**: Small schema validation catches typos before authentication. **Alternatives considered**: Legacy compatibility and path interpolation add ambiguous behavior; main will replace the operator file separately.

**Decision**: Use lstat, O_NOFOLLOW, fstat, realpath and inode comparisons from Node fs. **Rationale**: Lexical names alone miss symlink parents and hard-link aliases. Refuse symlink paths, and compare tokens/operator with resolved targets before writing. **Alternatives considered**: Allowing arbitrary paths under HOME does not meet the fixed allowlist.

**Decision**: Preserve existing line bytes using Buffer slices with Latin-1 indexing, and encode only replacement values as UTF-8. **Rationale**: UTF-8 decoding of unrelated bytes can alter a file. Preserve line endings and append a separator only when a missing variable follows an unterminated line. **Alternatives considered**: dotenv serializers erase comments/order and add a dependency.

**Decision**: Capture and suppress both bws streams on failure and catch exceptions with a fixed message. **Rationale**: Error payloads can carry credentials. **Alternatives considered**: Forwarding stderr or JSON parse errors is unsafe.

**Decision**: Prepare every same-directory exclusive temporary file, then rename; clean up remaining temporary files on ordinary failures. **Rationale**: No requested validation failure may partially update files. **Alternatives considered**: Distributed transactions, backups and recovery journals are outside scope. Process interruption may leave private temporary files; no automatic interrupted-run recovery is promised.

## Evidence and limits

Read scripts/secrets-refresh.ts and its offline tests and all records under specs/041-provider-secrets. No live credential/operator file, real bws command or Bitwarden service was accessed. This design relies on the existing security review rather than claiming fresh service or binary acceptance.
