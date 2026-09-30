# Bug Verification: Name check fails on folders that Git ignores

- **Slug**: name-check-untracked
- **Tested**: 2026-09-30
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: pass

## Summary

`npm run lint:names` no longer reports names inside git-ignored folders and
still reports untracked files and folders that Git does not ignore. The new
tests fail without the fix and pass with it, and `npm run verify` ends
`VERIFIED` in a worktree that holds six untracked `.venv` folders (the root and
`tools/*`).

## Checks Performed

| Check                | Command / Action                                                                                                 | Result | Notes                                                                                     |
| -------------------- | ---------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------- |
| New tests, without   | `npm run test:lint-names` with `scripts/lint-names.sh` replaced by `timeout 60 ls-lint`                           | fail   | Both tests fail; the output names `cache/Bad_File.txt` and `cache/Bad_Folder`.            |
| New tests, with      | `npm run test:lint-names`                                                                                        | pass   | 2 passed.                                                                                 |
| Names check          | `npm run lint:names` in the worktree with six untracked `.venv` folders                                          | pass   | Exit 0.                                                                                   |
| Full verification    | `npm run verify` at `4f12cb2` plus this change                                                                   | pass   | 34 of 34 Turborepo tasks succeeded; workflow phase `VERIFIED`.                            |

## Residual Risks

- An ignored path whose name holds a newline is not skipped (Git C-quotes
  it), so the check reports it instead of skipping it. That fails loud.
- A git-ignored path whose own name holds a wildcard character is handed to
  ls-lint as an ignore entry; see the assessment's risks.
- ls-lint checks a folder only when it walks the folder, so a tool that
  writes an untracked, unignored folder with a non-kebab-case name is reported
  until it is added to `.gitignore`. That is the intended behavior.

## Recommendation

Merge the fix.
