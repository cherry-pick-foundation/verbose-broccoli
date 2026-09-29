# Bug Verification: Provider failures in bursts leave units unjudged

- **Slug**: provider-error-bursts
- **Tested**: 2026-09-29
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

Both forms in which the provider's short failures arrive, an HTTP 500 and a
padded HTTP 200 body without an answer, now lead to a second attempt that
answers, through the whole `backfire serve-mcp` and `backfire_verify` path.
Before the fix the same replay failed with `provider_error` after one
request. The new and updated tests fail without the fix and pass with it, the
full repository check passes, and five live calls to the real provider
succeeded. No live provider failure occurred during those calls, so the
retry was not seen against the real provider.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (pre-fix) | A scratch loopback provider, outside the repository, answers the first request with one failure form and later requests with a valid answer; one synthetic `backfire_verify` call through this branch's `backfire serve-mcp`, with `failures.py` from `8605cf2` and a scratch `XDG_STATE_HOME` | fail, as expected | Both forms: tool error `provider_error`, one provider request, record `provider_error` with 1 attempt. |
| Reproduction (post-fix) | The same replay on `f1ec2cd` | pass | Both forms: `verified` 1, two provider requests, record `ok` with 2 attempts. |
| New / updated tests | `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/backfire --frozen --offline --no-sync pytest packages/backfire/tests/test_failures.py packages/backfire/tests/test_judge.py packages/backfire/tests/test_provider.py packages/backfire/tests/test_faults.py packages/backfire/tests/test_adapter_wiring.py -q`, first with `failures.py` from `8605cf2`, then on `a93f7d8` | fail, then pass | `25 failed, 247 passed`, then `272 passed`. |
| Regression suite, lint, type-check | `npm run verify -- --task CHE-33 --base 8605cf2` on `f1ec2cd` | pass | Workflow `VERIFIED`, exit code 0; backfire `1363 passed, 3 deselected`, lint `All checks passed!`. |
| Live provider check | The document judgment step and one `backfire_decide` call, sent through this branch's `backfire serve-mcp` to DeepSeek V4.1 Flash on Hive by a scratch MCP client over stdio | pass | 5 billed calls, each `ok` on its first attempt (7.1-52.9 s); see below. |

## Output Excerpts

```text
pre-fix  padded:  tool_error=True  outcome=provider_error  provider_requests=1  records=[('provider_error', 1)]
pre-fix  http500: tool_error=True  outcome=provider_error  provider_requests=1  records=[('provider_error', 1)]
post-fix padded:  tool_error=False verified=1              provider_requests=2  records=[('ok', 2)]
post-fix http500: tool_error=False verified=1              provider_requests=2  records=[('ok', 2)]

25 failed, 247 passed in 6.89s
272 passed in 27.07s

backfire:test: 1363 passed, 3 deselected in 163.51s
```

## Document Judgment Step

Run on `a93f7d8` against `develop` `8605cf2`, as `npm run workflow`
requires before the develop merge review. `npm run doc-regions:prepare --
--base develop --max-evidence-chars 20000` gave three `backfire_verify`
requests (229 units: 112, 112 and 5), each with the assessment and the
`failures.py` diff as evidence, and no `backfire_classify` request.

- No unit was `contradicted`. 2 were `verified`, 227 `unsupported`.
- Three target units in `docs/backfire.md` were flagged `review`; they stand.
  Lines 182-189 (records) are `verified` at confidence 0.70 and lines 222-223
  at 0.33. Lines 225-242, the troubleshooting table, are `unsupported` at
  0.79: most rows describe behavior this change does not touch. Its changed
  `provider_error` row matches `failures.py` (`max_retries=3`, statuses 500-599,
  the `provider_error` predicate).
- `npm run doc-regions:audit` reported the same 19 MemoryLint `boundary`
  warnings on `.specify/memory/constitution.md` as earlier features. They are
  reported to the user, not acted on.

## Billed Calls

Five calls reached the provider, all through this branch's server. The first
`backfire_verify` request ran twice, because the scratch client stopped on an
attribute error after the first answer and its result was lost; the other
three requests and one `backfire_decide` call, which chose the develop merge
reviewer's model, ran once. Each call answered on its first attempt and
together they used 214,668 input and 44,766 output tokens. The replays above
used only the loopback provider.

## Residual Risks

- A live burst cannot be produced on demand. The replay uses the two failure
  forms captured from this provider in the earlier bug's assessment
  (`.specify/bugs/answerless-provider-reply/assessment.md`, steps 6 and 8).
- A judgment that fails late, after about 90 s, has too little of its 118 s
  deadline left for a retry to finish. It then ends as `provider_unavailable`
  and the retry is billed without an answer.
- An outage longer than the backoff window, about 7 s, still fails after four
  attempts.

## Recommendation

Close the bug once the branch is merged into `develop`: the observed failure
forms now recover end to end, the new tests fail without the fix, and the
full check passes. The next judgment step that meets a provider episode
should show `ok` records with 2 or more attempts where `provider_error`
records stood before.
