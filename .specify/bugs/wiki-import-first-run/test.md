# Bug Verification: Wiki raw import test fails when the script environment is missing

- **Slug**: wiki-import-first-run
- **Tested**: 2026-09-28
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The assessment's reproduction no longer fails: with this worktree's script
environment removed, the raw import tests pass 41 of 41 on the first run, where
they failed 1 of 41 before the fix. The full repository check passes with the
fix (`c8b11cb`, on `develop` `7137315`).

## Checks Performed

| Check                              | Command / Action                                                                                                                                                                                                            | Result | Notes                                                                                                                                                             |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reproduction (pre-fix)             | Remove `~/.cache/uv/environments-v2/raw-import-6ed63e8ca35edc30`, the folder `uv python find --offline --script <worktree>/plugins/work/skills/wiki-raw-import/scripts/raw_import.py` names; run the test file at `7137315` | fail   | `FAILED \| 40 passed \| 1 failed`; stderr held `Installed 1 package in 1ms` (coordinator, and again by the implementing worker).                                  |
| Reproduction (post-fix)            | The same removal, confirmed by `uv python find` naming the base interpreter; `deno task test:wiki-raw-import` at `c8b11cb`                                                                                                  | pass   | `ok \| 41 passed \| 0 failed (10s)`; afterwards `uv python find` names the rebuilt environment.                                                                   |
| Regression suite, lint, type-check | `deno task verify --task che-18-first-run --base 7137315` on `c8b11cb`                                                                                                                                                      | pass   | Workflow `VERIFIED`: "Configured checks passed for the current code state." `test:wiki-raw-import` passed 41 of 41.                                               |
| Setup prerequisite                 | `deno task backfire:install`                                                                                                                                                                                                | done   | The first verify stopped at `test:backfire` ("Missing Backfire pytest environment"), because Orca's setup does not build that environment; unrelated to this bug. |

## Output Excerpts

```text
raw import: locked offline help and missing-instance errors => ./scripts/wiki_raw_import_test.ts:223:6
error: AssertionError: Values are not equal.
    [Diff] Actual / Expected
-   Installed 1 package in 1ms\n
FAILED | 40 passed | 1 failed (11s)
```

After the fix, from a removed environment:

```text
ok | 41 passed | 0 failed (10s)
```

## Residual Risks

- `--quiet` also hides uv's warnings in these tests; uv's errors still print and
  fail the run.
- The skill's own commands (`plugins/work/skills/wiki-raw-import/SKILL.md`) are
  unchanged, so a user's first run still shows uv's line on stderr, with exit
  code and stdout unaffected.

## Recommendation

Close the bug once the branch is merged into `develop`: the tests pass on the
first run from a missing script environment, and their checks on the tool's own
output are unchanged.
