# Bug Fix: Wiki raw import test fails when the script environment is missing

- **Slug**: wiki-import-first-run
- **Fixed**: 2026-09-28
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The raw import tests now run the tool with uv's `--quiet` flag added to
`uv run --locked --offline --script`. When uv has to build the script
environment first, it no longer prints `Installed 1 package …` on stderr, so the
tests' empty-stderr checks see only the tool's own output. uv's errors, and the
tool's stdout, stderr and exit code, pass through as before.

## Changes

| File                              | Change   | Notes                                                       |
| --------------------------------- | -------- | ----------------------------------------------------------- |
| `scripts/wiki_raw_import_test.ts` | modified | `Fixture.command` adds `--quiet` to the `uv run` arguments. |

## Tests Added or Updated

- No new test, as the assessment planned. The existing test "raw import: locked
  offline help and missing-instance errors" is the case that fails without the
  fix when the script environment is missing.

## Local Verification

- Reported by the implementing Codex worker (gpt-6-luna, max effort; Orca
  dispatch `ctx_8187b2930e52`): with this worktree's script environment removed,
  `deno task test:wiki-raw-import` failed before the change with
  `FAILED | 40 passed | 1 failed` and `Installed 1 package in 1ms` in the diff,
  and passed after it, again from a removed environment, with
  `ok | 41 passed | 0 failed`. `deno task format:check` and `deno task lint`
  passed. The coordinator removed the environment both times, because the
  worker's command safety check refused the removal.
- The worker's own `deno task verify` stopped at `test:plugin-skills` with
  `mise ERROR No version is set for shim: node`, a setting of its shell; the
  same check passed in the coordinator's `deno task verify` (see test.md).

## Deviations from Assessment

- None.

## Follow-ups

- None.
