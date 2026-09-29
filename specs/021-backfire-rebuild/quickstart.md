# Quickstart: Validate the Rebuilt Backfire

All commands run from the repository root of the feature worktree.

```sh
npm run backfire:install        # uv sync with the education extra
npm run test:backfire           # tools, providers with stubs, noul, regex, load cases
npm run verify                  # everything; three runs in a row (SC-005)
```

## Start it as the plugins do

```sh
uv --directory packages/backfire run --frozen --offline --no-sync backfire serve-mcp
uv --directory packages/backfire run --frozen --offline --no-sync backfire serve-mcp --education
```

Expected: an MCP server named `jev-mcp` listing PyModel's eleven tools and
`jev_noul` ([contracts/tools.md](contracts/tools.md)).

## Load checks (CHE-37, CHE-38)

```sh
for i in $(seq 16); do nice -n 19 yes >/dev/null & done
PYTHONDONTWRITEBYTECODE=1 nice -n 19 uv run --frozen --offline --no-sync \
  --package backfire pytest packages/backfire/tests/test_bounded_work.py -q -s
kill $(jobs -p)
```

Expected: every tool but `jev_verify` stays under 1 second of stall in 3
of 3 runs; `jev_verify` shows as an expected failure naming CHE-38. Repeat
the extract case with 80 processes: 5 of 5 runs find the simple pattern.

## Upstream contribution

Apply `specs/021-backfire-rebuild/upstream/pymodel.patch` to a clone of
PyModel at `v0.6.0`, run its tests, and run backfire's `jev_verify` load
case against it; it passes.

## Live checks (billed, final step only)

One judgment per tool through the shipped Hive profile (at most 15 calls)
and one judgment through the Vercel profile; report the call counts.
