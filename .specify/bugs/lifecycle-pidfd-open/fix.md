# Bug Fix: Backfire lifecycle tests need os.pidfd_open

- **Slug**: lifecycle-pidfd-open
- **Fixed**: 2026-09-28
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The lifecycle tests' `pattern_process()` helper now uses `os.pidfd_open` and
`signal.pidfd_send_signal` when the interpreter has them, and otherwise calls
the Linux `pidfd_open` (434) and `pidfd_send_signal` (424) syscalls through
`ctypes`, checking their results. So the tests run on uv's managed CPython
3.14.4, which lacks both wrappers, as well as on the system build.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/backfire/tests/test_lifecycle.py` | modified | New `pidfd_syscall()` helper; `pattern_process()` falls back to it; new regression test. |

## Diff Highlights (optional)

`pidfd_syscall()` refuses to run on a machine other than x86_64, sets
`libc.syscall.restype` to `c_long`, and raises `OSError` with
`ctypes.get_errno()` when the syscall returns -1. Each wrapper is checked on
its own with `hasattr`, so a build with only one of them still works.

## Tests Added or Updated

- `packages/backfire/tests/test_lifecycle.py::test_pattern_process_without_pidfd_wrappers`
  — with both wrappers removed by `monkeypatch`, the fallback opens a pidfd for
  a live child, the pidfd becomes readable after the helper kills the child
  (exit by `SIGKILL`), an invalid PID raises `OSError` with `EINVAL`, and a
  reported machine other than x86_64 raises `RuntimeError` before any syscall.
- The three tests the assessment names,
  `test_client_end_kills_active_pattern_child[eof]`, `[kill]` and
  `test_killed_server_leaves_pattern_child_to_its_own_timer`, are the
  regression check for the original failure.

## Local Verification

Reported by the implementing Codex worker (Orca dispatch `ctx_c413365999a2`):

- `pytest packages/backfire/tests/test_lifecycle.py` on uv's managed CPython
  3.14.4: before the fix 3 failed, 6 passed; after it 10 passed.
- The new test alone before the fix: 1 failed; after it: 1 passed.
- The same file with the system interpreter `/usr/bin/python3.14` in a
  temporary environment: 10 passed; the environment was removed afterwards.
- `deno task verify --task CHE-14 --base e959ef4`: passed once `node` was on
  `PATH` (see Follow-ups).

The coordinator's own verification is in [test.md](test.md).

## Deviations from Assessment

None.

## Follow-ups

- `deno task verify` first failed in this worktree in `test:plugin-skills`,
  because the shell's `mise` had no Node version selected for the directory,
  so `node` was not found. It passed with Node 24.19.0 from `mise` put on
  `PATH`. This is an environment issue outside this bug.
