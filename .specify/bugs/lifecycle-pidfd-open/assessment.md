# Bug Assessment: Backfire lifecycle tests need os.pidfd_open

- **Slug**: lifecycle-pidfd-open
- **Created**: 2026-09-28
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-14> (Linear issue
  CHE-14, read with `orca linear issue CHE-14 --full --json`; host
  `linear.app`, allowlisted)
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

CHE-14, "Backfire lifecycle tests fail on uv-managed Python without
os.pidfd_open": `deno task verify` fails in any worktree whose backfire
environment uses uv's managed CPython 3.14.4, so no feature can finish there.
Three tests in `packages/backfire/tests/test_lifecycle.py` fail with
`AttributeError: module 'os' has no attribute 'pidfd_open'`. Expected: the
tests pass, or detect process death another way, on both uv-managed and system
CPython 3.14.4. Only the tests call `os.pidfd_open`; backfire's runtime code
does not. Workaround: create the environment with the system interpreter.

A comment on the issue adds that uv's managed CPython 3.14.6 and 3.13.14 and
the system `/usr/bin/python3` 3.14.4 all have `os.pidfd_open`; only uv's
managed 3.14.4 build lacks it, and `packages/backfire/.python-version` pins
3.14.4, so every fresh `deno task backfire:install` picks that build.

## Symptom

With the environment that `deno task backfire:install` creates, three
lifecycle tests fail before they check anything, because the interpreter's
`os` module has no `pidfd_open`. They should pass on uv's managed CPython
3.14.4 as well as on the system build.

## Reproduction

1. In a worktree at develop `8ab332b`, run `deno task backfire:install`. uv
   picks `~/.local/share/uv/python/cpython-3.14.4-linux-x86_64-gnu`.
2. Run `uv run --project packages/backfire --frozen --offline --no-sync pytest
   packages/backfire/tests/test_lifecycle.py -m 'not slow'`.
3. Observed on 2026-09-28 (kernel 7.0.0-34-generic): 3 failed, 6 passed. The
   failures are `test_client_end_kills_active_pattern_child[eof]`,
   `test_client_end_kills_active_pattern_child[kill]` and
   `test_killed_server_leaves_pattern_child_to_its_own_timer`.

In the same interpreter, `hasattr(os, "pidfd_open")` and
`hasattr(signal, "pidfd_send_signal")` are both false, while
`/usr/bin/python3.14` (3.14.4) has `os.pidfd_open`. The kernel supports the
syscalls: calling `syscall(434, pid, 0)` (pidfd_open) and `syscall(424, fd,
SIGKILL, NULL, 0)` (pidfd_send_signal) through `ctypes` in that interpreter
returned a pidfd, killed the process and made the pidfd readable.

The hosted CI job installs the same managed build (`uv python install --no-bin
"$(cat packages/backfire/.python-version)"` in `.github/workflows/check.yml`),
so the failure is expected there too; hosted runs are unobserved.

## Suspected Code Paths

- `packages/backfire/tests/test_lifecycle.py:158` — `pattern_process()` calls
  `os.pidfd_open(pid)`.
- `packages/backfire/tests/test_lifecycle.py:163` — the same helper's cleanup
  calls `signal.pidfd_send_signal(descriptor, signal.SIGKILL)`, which the
  managed build also lacks; it runs only when the child is still alive.
- `packages/backfire/tests/test_lifecycle.py:242` — the same file already uses
  `ctypes.CDLL(None, use_errno=True)` to call `prctl`, the idiom a fallback
  can follow.

## Root Cause Hypothesis

uv's managed CPython 3.14.4 build was compiled without the `pidfd_open` and
`pidfd_send_signal` wrappers (they are compiled in only when the build's
headers define the syscalls), so the attributes are missing although the
running kernel supports them. The tests assume the wrappers exist.
Confidence: high for the missing attributes and for the kernel support, both
observed; medium for the exact build cause, which was not traced in the
build's configuration.

## Proposed Remediation

**Preferred**: In `pattern_process()`, open the pidfd with `os.pidfd_open`
when the interpreter has it, and otherwise with the Linux `pidfd_open`
syscall (number 434 on x86_64) through the `ctypes` libc handle the file
already uses; do the same for `pidfd_send_signal` (424). Check the syscall's
return value and raise `OSError` with `ctypes.get_errno()` on failure, so a
real error is not hidden. The pidfd keeps the tests' current guarantee: no
race with PID reuse, and `select` waits for the process to exit.

**Alternatives**:
- Pin another interpreter, such as uv's managed 3.14.6, in `.python-version`.
  This changes feature 005's pinned runtime, which needs its own
  re-verification, and it only works around the tests' reliance on an optional
  wrapper.
- Detect process death by polling `os.kill(pid, 0)` for `ESRCH`. This loses
  the pidfd's protection against PID reuse and needs a polling loop.
- Tell uv to prefer the system interpreter. The package would then depend on
  a system Python 3.14.4 being present, which hosted CI does not provide.

**Files likely to change**:
- `packages/backfire/tests/test_lifecycle.py`

**Tests to add or update**:
- The three failing tests themselves are the regression check: they must pass
  on uv's managed CPython 3.14.4 and on `/usr/bin/python3.14`.
- A small test of the helper that forces the syscall path (for example by
  hiding `os.pidfd_open` with `monkeypatch`) and checks that it opens a pidfd
  for a short-lived child, that the pidfd becomes readable after the child is
  killed, and that an invalid PID raises `OSError`.

## Risks & Considerations

- Syscall numbers can differ by architecture. 424 and 434 come from the
  kernel's shared table for syscalls added since Linux 5.1, but only x86_64
  was observed. The tests already run only on Linux (`pytestmark` skips other
  platforms), and the operator's host and CI are x86_64. The fallback should
  name the numbers it uses and fail with a clear message on a machine other
  than x86_64 instead of calling an unverified syscall.
- The change is test-only; backfire's runtime and feature 005's pins do not
  change.

## Open Questions

- None.
