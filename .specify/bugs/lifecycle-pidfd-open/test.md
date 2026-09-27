# Bug Verification: Backfire lifecycle tests need os.pidfd_open

- **Slug**: lifecycle-pidfd-open
- **Tested**: 2026-09-28
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

On uv's managed CPython 3.14.4, which still lacks `os.pidfd_open`, all
lifecycle tests pass after the fix, including the three that failed before.
The full repository check passes on the branch after `develop` (`e0f359c`) was
merged into it.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Interpreter still lacks the wrappers | `packages/backfire/.venv/bin/python -c "import os,sys;print(sys.version.split()[0], hasattr(os,'pidfd_open'))"` | pass | Printed `3.14.4 False`, so the fallback path is the one exercised. |
| Reproduction (post-fix) | `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/backfire --frozen --offline --no-sync pytest packages/backfire/tests/test_lifecycle.py -q` | pass | `10 passed in 17.46s`, run by the coordinator on `fb5a970`. |
| New / updated tests | the same command | pass | Includes `test_pattern_process_without_pidfd_wrappers`. |
| System interpreter | the same file with `/usr/bin/python3.14` in a temporary environment | pass | Run by the implementing worker: `10 passed`; not rerun by the coordinator. |
| Regression suite, lint, type-check | `deno task verify --task CHE-14 --base e959ef4` on `a278631` (the fix merged with `develop` `e0f359c`) | pass | Workflow `VERIFIED`; `deno task check` passed, with `node` 24.19.0 on `PATH`. |

## Output Excerpts

```text
3.14.4 False
..........                                                               [100%]
10 passed in 17.46s
```

## Residual Risks

- The syscall fallback runs only on x86_64; another architecture gets a clear
  `RuntimeError` from the tests instead of a pass. The operator's host and CI
  are x86_64.
- Hosted CI, which installs the same managed interpreter, has not run the fix
  yet.

## Recommendation

Close the bug once the branch is merged into `develop`: the failure no longer
reproduces on the interpreter that caused it, and the full check passes.
