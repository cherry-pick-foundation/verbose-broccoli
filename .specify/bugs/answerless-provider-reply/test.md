# Bug Verification: A provider reply without an answer is reported as malformed_output

- **Slug**: answerless-provider-reply
- **Tested**: 2026-09-29
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The reply that reproduced the bug, HTTP 200 with padding and then the
provider's error object, is now `provider_error` instead of `malformed_output`
when it is replayed through the whole `backfire_verify` tool path. The new and
updated tests fail on the source before the fix and pass after it, and the
full repository check passes. During the document judgment step the fixed
server met two live provider failures and reported both as `provider_error`.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (pre-fix) | The reply captured in the assessment's step 8 (status 200, body of 8 spaces and `{"status_code":500,"message":"Internal Server Error"}`), served on loopback by `tests/fake_provider.py`, sent through `backfire.tools.verify.call` with CHE-10's request 2 and the real judge, with `provider.py` from `712c3ed` | fail, as expected | `malformed_output`, one request. |
| Reproduction (post-fix) | The same replay on `a0d0d83` | pass | `provider_error`, one request, no retry. No billed call. |
| New / updated tests | `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/backfire --frozen --offline --no-sync pytest packages/backfire/tests/test_provider.py -q`, first with `provider.py` from `712c3ed`, then on `0eb9b8b` | fail, then pass | `18 failed, 102 passed`, then `120 passed`. The 18 are exactly the new and changed cases. |
| Regression suite, lint, type-check | `deno task verify --task CHE-22 --base 2262815` with a plan covering the changed files, on `0eb9b8b` | pass | Workflow `VERIFIED`, exit code 0; backfire `1351 passed, 3 deselected`. `node` 24.19.0 from `mise` was first on `PATH`. |
| Live provider failure (fixed server) | The document judgment step below, through `backfire serve-mcp` from this branch | pass | Two of five calls failed at the provider: one after 31.4 s with no model and no usage, like request 1's records, and one after 15.1 s. Both are recorded as `provider_error`. |

## Output Excerpts

```text
before fix (712c3ed): malformed_output | requests sent: 1
after fix (HEAD a0d0d83): provider_error | requests sent: 1

18 failed, 102 passed in 4.03s
120 passed in 3.62s

1351 passed, 3 deselected in 137.47s (0:02:17)
```

## Document Judgment Step

Run on `a0d0d83` against `develop` `2262815`, as `deno task workflow`
requires before the develop merge review. `deno task doc-regions:prepare --
--base develop --max-evidence-chars 20000` gave three `backfire_verify`
requests (228 units) and no `backfire_classify` request. They went to
`backfire serve-mcp` from this branch (DeepSeek V4.1 Flash) through a scratch
MCP client over stdio, because this session has no backfire MCP tools.
Request 1 failed once with `provider_error` and passed on a rerun; request 3
likewise. The session records are in
`~/.local/state/verbose-broccoli/backfire/records/`:
`2026-09-28T17:39:37.840609Z-294c…` (request 1, `provider_error`),
`2026-09-28T17:40:16.388016Z-7a1d…` (requests 1 and 2 `ok`, request 3
`provider_error`) and `2026-09-28T17:41:57.269429Z-b7d8…` (request 3 `ok`).
Line numbers are at `a0d0d83`.

- No unit was `contradicted`.
- One target unit was flagged `review` and stands: `docs/backfire.md:225-242`,
  the troubleshooting table whose `provider_error` row this fix changed. It is
  `verified` at confidence 0.55 against the diff, and it matches the code.
- `docs/backfire.md:222-223` is `verified` (0.85). Every other unit is
  `unsupported`, because this change's diff says nothing about it.
- `deno task doc-regions:audit` reports 19 MemoryLint findings, all in the
  report-only `.specify/memory/constitution.md` (rules it suggests moving to
  `AGENTS.md`). This fix does not touch that file; the findings are left for
  the user.

## Billed Calls

The user allowed as many billed calls as needed. The assessment made 15
complete calls (3 sent directly, 12 through backfire's judge), and a fifth
round of 3 was stopped after its requests were sent. The judgment step made 5
calls. The provider reported 571,292 input tokens for the 11 assessment calls
that answered and 156,042 for the 3 judgment calls that answered; failed calls
report no usage. Raw replies stayed in the session's temporary folder.

## Residual Risks

- A live padded failure cannot be produced on demand. The post-fix check
  replays the reply captured from the provider; the 31.4 s live failure during
  the judgment step matches that pattern, but its body was not captured.
- The document judgment step still fails while the provider has an episode of
  server errors. The error now names the provider, and a rerun passes.

## Recommendation

Close the bug once the branch is merged into `develop`: the captured failing
reply is now reported as `provider_error`, the new tests fail without the fix,
and the full check passes.
