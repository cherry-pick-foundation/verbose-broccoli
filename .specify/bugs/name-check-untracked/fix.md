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

- `lint-names skips folders that Git ignores` also holds an ignored folder
  with a Korean name and a non-kebab-case file. Added after the develop merge
  review (below); fails without `core.quotepath=off`, because Git then prints
  the name C-quoted and it matches no path.

## Review

A fresh Codex reviewer (gpt-6-luna, medium; backfire `jev_decide` 0.99)
reviewed `735b412` read-only: 0 blockers, 0 majors, 1 minor. Names that hold
a newline are C-quoted by Git even with `core.quotepath=off`, so they cannot
match an ignore entry and stay checked, and a non-kebab name under such an
ignored path is reported, never skipped. This is left as it is and noted in
the script; the non-ASCII case is fixed.

## Deviations from Assessment

None.
