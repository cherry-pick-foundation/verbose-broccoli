# Quickstart: Validate the Rebuilt Backfire

All commands run from the repository root of the feature worktree.

## Prerequisites

```sh
npm run backfire:install    # uv sync with the education extra
```

## 1. Tools and upstream behaviour (US1, SC-001, SC-002)

```sh
npm run test:backfire
```

Expected: all tests pass, including `tests/upstream/` (the vendored
upstream tests), the tool-list test (twelve tools, upstream definitions
after the name mapping) and the per-tool call tests with a scripted
provider. See [contracts/tools.md](contracts/tools.md).

## 2. Upstream record (US4, SC-007)

The hash test runs in step 1. To see it fail, change one byte of an
`unchanged` vendored file and run
`npm run test:backfire -- -k upstream_record`; it names the file. Restore
the file afterwards.

## 3. Load fixes (US2, SC-003, SC-004)

Start busy low-priority processes as the CHE-37 assessment does, then run
the bounded-work checks:

```sh
for i in $(seq 16); do nice -n 19 yes >/dev/null & done
PYTHONDONTWRITEBYTECODE=1 nice -n 19 uv run --frozen --offline --no-sync \
  --package backfire pytest packages/backfire/tests/test_bounded_work.py -q -s
kill $(jobs -p)
```

Expected: every tool's `worst_lag_ms` stays under 1,000 in 3 of 3 runs.
Repeat the `-k extract` case with 80 processes: 5 of 5 runs find the simple
pattern's match, and the runaway fields report the time-out reason. The
feature's `tasks.md` records the failing runs from before each fix.

## 4. Backfire's own services (US3)

```sh
npm run test:backfire-slow        # deadline and other long cases
npm run backfire:ready            # needs the configured credential; billed
```

Expected: the slow tests pass; `backfire:ready` passes with a valid
configuration. The ready check makes billed calls, so it runs only in the
final live check (SC-006), where the number of billed calls is reported.

## 5. Plugin builds (FR-011)

```sh
npm run backfire:build -- code "$(mktemp -d)/code-plugin"
npm run backfire:build -- work "$(mktemp -d)/work-plugin"
```

Expected: both builds contain `backfire/src/jev_judge_mcp/` with its
`LICENSE`, `THIRD_PARTY_NOTICES.md` and `UPSTREAM.md`, and the build tests
in step 1 start the copied server and list its twelve tools.

## 6. Everything

```sh
npm run verify    # three runs in a row without a rerun (SC-005)
```
