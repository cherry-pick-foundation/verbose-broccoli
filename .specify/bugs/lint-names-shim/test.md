# Bug Verification: lint-names test fails where ls-lint resolves through the mise shim

- **Slug**: lint-names-shim
- **Tested**: 2026-09-30
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

With mise's shims folder ahead on PATH, the two `lint-names` cases failed with
`No version is set for shim: ls-lint` before the fix and pass after it. The full
repository check passes in a shell where `ls-lint` resolves through the shim.

## Checks Performed

| Check                   | Command / Action                                                                                                  | Result | Notes                                                                              |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------- |
| Reproduction (pre-fix)  | `env -i HOME=$HOME PATH="$SHIM:/usr/bin:/bin" node --permission … --test scripts/lint-names-test.ts` at `a5b4600` | fail   | `fail 2`; `mise ERROR No version is set for shim: ls-lint`.                        |
| Reproduction (post-fix) | The same command with the fix                                                                                     | pass   | `pass 2`, `fail 0`.                                                                |
| Full check              | `PATH="$SHIM:$PATH" npm run verify`                                                                               | pass   | Turbo `34 successful, 34 total`; workflow `VERIFIED`; `//#test:lint-names` passed. |

## Residual Risks

- On a machine with no mise shims folder the test still passes but is not a
  regression check for the shim.

## Recommendation

Close the bug once the branch is merged into `develop`.
