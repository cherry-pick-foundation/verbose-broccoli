# Bug Fix: Name check fails on folders that Git ignores

- **Slug**: name-check-untracked
- **Fixed**: 2026-09-30
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

`npm run lint:names` now runs `scripts/lint-names.sh`. It reads the ignored
paths from Git and gives them to ls-lint as literal `ignore` entries through a
second config on standard input, keeping the 60-second limit. `.ls-lint.yml`'s
ignore list shrinks to `.git`.

## Changes

| File                          | Change        | Notes                                                                                     |
| ----------------------------- | ------------- | ----------------------------------------------------------------------------------------- |
| `scripts/lint-names.sh`       | added         | POSIX `sh`, 8 lines of code plus its comment.                                              |
| `scripts/lint-names-test.ts`  | tests         | Two cases on a temporary Git repository.                                                   |
| `package.json`                | modified      | `lint:names` runs the script; new `test:lint-names`.                                       |
| `turbo.json`, `tsconfig.json` | modified      | The new test joins the `test` task and the TypeScript project.                             |
| `.ls-lint.yml`                | modified      | Ignore list trimmed to `.git`; header comment mentions the generated entries.              |
| `docs/architecture.md`, `docs/reference/commands.md` | documentation | Describe the script and the new command.                                   |

## Tests Added or Updated

- `lint-names skips folders that Git ignores`: an ignored `cache/` holding
  `Bad_File.txt` and `Bad_Folder/` passes. Fails without the fix.
- `lint-names checks untracked files and folders that Git does not ignore`:
  an untracked `Bad_File.txt` and `Bad_Folder` fail, and the ignored `cache/`
  names do not appear in the output. Fails without the fix.

## Deviations from Assessment

None.
