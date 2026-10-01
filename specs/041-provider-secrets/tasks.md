# Tasks: Provider Keys from Bitwarden Secrets Manager

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: bws (User Story 1)

- [x] T001 [US1] Review bws 2.1.0 read-only; report in
  [security/bws-2.1.0.md](security/bws-2.1.0.md) (FR-001).
  - By main (Claude Code), 2026-10-01. Verdict: acceptable with five
    controls; 0 high, 2 medium (values on the command line for writes; state
    file with default permissions), 3 low (values on standard output; checksum
    without provenance; ambient config can redirect the token). The
    Bitwarden SDK license is not open source; use here is internal and nothing
    is redistributed.
- [x] T002 [US1] Pin bws 2.1.0 in `mise.toml` and `mise.lock` (and `orca.yaml`'s
  install list) from the registry's `aqua:bitwarden/sdk-sm` (FR-001).
  - `mise lock` wrote seven platform checksums that equal the digests GitHub's
    release API reports; `mise install --locked` and `bws --version` printed
    `bws 2.1.0`. CHE-74 will later move `mise.toml` into `.config/`.

## Phase 2: The refresh (User Story 2)

- [x] T003 [US2] Write `scripts/secrets-refresh.ts` and
  `scripts/secrets-refresh-test.ts`; add `secrets:refresh` and
  `test:secrets-refresh` to `package.json`, `turbo.json` and `tsconfig.json`
  (FR-002 to FR-006).
- [x] T004 [US2] Describe the refresh in `docs/backfire.md` and
  `docs/architecture.md`; regenerate `docs/reference/commands.md` (FR-007).

## Phase 3: Import (User Story 3)

- [x] T005 [US3] Save the operator configuration, import the seven key files
  into the project, and show that a refresh reproduces identical hashes (SC-002).
  - 2026-10-01: the token logs in on Bitwarden's United States cloud (the
    default server; the EU server answers 401). `gemini.env` and `vercel.env`
    first got a final line break. Eight `bws secret create` calls (cloudflare
    two, one each for the other six files) put each value on bws's command line
    for that one call (review F-01), with output discarded. `npm run
    secrets:refresh` then rewrote the seven files; SHA-256 of every file equals
    its hash before the refresh, and each file is mode 600 and owned by the
    user. No value or token was printed.
- [x] T006 [US3] After the user switches the machine account to read only, show
  that refresh still works and a write is refused (SC-002).
  - 2026-10-01: with the account read only, `npm run secrets:refresh` wrote the
    seven files again with unchanged checksums, and `bws secret create` with a
    fake value was refused by the server (404 "Resource not found"); the project
    still holds 8 secrets.

## Phase 4: Finish

- [ ] T007 Merge `develop`, run `npm run verify`, pass the develop merge review
  by a provider other than Claude Code, commit the review record and finish with
  `git flow feature finish provider-secrets`.
  - 2026-10-01: merged `develop` da52d3a (conflicts only in `mise.toml`,
    `mise.lock`, `orca.yaml`: both pins kept); `npm run verify` VERIFIED (39 of
    39).
  - Reviewer: a fresh Copilot session (`auto`, efficiency; routed to
    gpt-6-luna), chosen with Jev (Copilot 0.65, confidence 0.58), reviewed
    `ab02ad5..43115bf` read-only and found 2 medium findings: a configured file
    name could leave the providers folder or overwrite the token file, and a
    profile in bws's own config could redirect the token. Both fixed in
    7cc5830 (plain file names only; a server URL on every call, review F-05) with
    tests. The fixes are small, so no second review was run.
