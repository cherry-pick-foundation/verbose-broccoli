# Bug Verification: Document judgment step fails on Hangul in docs/backfire.md

- **Slug**: doc-judgment-refusals
- **Tested**: 2026-10-01
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

`npm run doc-regions:prepare` now prints requests with no Hangul, and all 267
units, including the 11 Hangul units of `docs/backfire.md`, were judged
through `backfire serve-mcp` with no refusal. The new test fails without the
fix and passes with it, and `npm run verify` is `VERIFIED`.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| New test, without the fix | `PYTHONDONTWRITEBYTECODE=1 uv run --frozen --offline --no-sync --package doc-regions pytest -p no:cacheprovider packages/doc-regions/tests/test_requests.py -q` with `requests.py` from `f6cb865` | fail, as expected | `1 failed, 20 passed`: `test_prepare_sends_hangul_in_latin_letters`. |
| New test, with the fix | the same command on `abde3dd` | pass | `21 passed`. |
| Real run | `npm run doc-regions:prepare -- --base develop --max-evidence-chars 20000`, then a scratch client outside the repository sent each request to `backfire serve-mcp` | pass | 267 units (11 with Hangul in `units`, 0 in requests), 4 `jev_verify` requests (84, 84, 84, 15 units); every request answered, 0 `invalid_response`. |
| Full check | `npm run verify` | pass | Workflow `VERIFIED`, 37 tasks successful. |

## Document Judgment Step

Run on `abde3dd` (develop `f6cb865` is its parent), with `--max-evidence-chars
20000`. No `jev_classify` request: no target unit consists only of added
lines (the change edits one existing bullet in `docs/architecture.md`).

- 10 units `verified`, 256 `unsupported`, 1 `contradicted`.
- The contradicted unit is `docs/architecture.md:304-310`, about the work
  plugin's backfire server. This change does not touch it and its evidence
  does not mention it (`missing_evidence: needs_diff`, confidence 0.59); it
  stands.
- The unit this change added (`docs/architecture.md`, the judgment-step
  bullet) is not flagged.
- `npm run doc-regions:audit` reported the same MemoryLint findings on the
  constitution and `AGENTS.md` as earlier features; they are reported to the
  user, not acted on.
