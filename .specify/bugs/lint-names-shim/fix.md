# Bug Fix: lint-names test fails where ls-lint resolves through the mise shim

- **Slug**: lint-names-shim
- **Fixed**: 2026-09-30
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

`scripts/lint-names-test.ts` now resolves the pinned `ls-lint` once with
`mise which ls-lint` from the repository root, and gives every command it runs
a PATH with that binary's folder first, then mise's shims folder, then the
caller's PATH. The shims folder in second place is the setup that failed before
the fix; the binary's folder in first place is the fix. `scripts/lint-names.sh`,
the 60-second timeout and the literal-paths control are unchanged.

## Changes

| File                         | Change   | Notes                                                            |
| ---------------------------- | -------- | ---------------------------------------------------------------- |
| `scripts/lint-names-test.ts` | modified | Resolve `ls-lint` with `mise which`; set PATH for every command. |

## Tests Added or Updated

- No new case. The two existing cases run with the shims folder on PATH. With
  the binary's folder left out of PATH, both fail with `No version is set for
shim: ls-lint`; with it, both pass.

## Local Verification

- Shim-first PATH (`env -i … PATH="$SHIM:/usr/bin:/bin"`): before the fix
  `fail 2`; after it `pass 2`. See test.md.

## Deviations from Assessment

- None.

## Follow-ups

- None.
