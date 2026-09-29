# Bug Assessment: Provider failures in bursts leave units unjudged

- **Slug**: provider-error-bursts
- **Created**: 2026-09-29
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-33> (Linear issue
  CHE-33, read with `orca linear issue CHE-33 --json`; host `linear.app`,
  allowlisted)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

CHE-33, "Backfire calls fail with provider_error in bursts and leave units
unjudged": in CHE-28's judgment step on the work vault, with DeepSeek V4.1
Flash on Hive, 57 of 209 calls failed with `provider_error`, in bursts. CHE-22's
fix (develop `7e4c92b`) made a reply without an answer count as
`provider_error` and did not retry it, and other failures are not retried
either, so each burst leaves units unjudged while the calls are still billed.
Expected: judgment steps finish with few unjudged units under the provider's
normal failures, for example by retrying `provider_error` after a wait or by
pacing requests, chosen after checking whether the bursts follow a documented
rate or concurrency limit. Vendor details stay in configuration. Evidence: the
records under `~/.local/state/verbose-broccoli/backfire/records/` from
2026-09-28, about 19:30 to 20:30 UTC.

## Symptom

During a provider episode, every judgment that is waiting for the provider at
one moment fails with `provider_error` at once, and backfire returns that
failure without another attempt. Expected: a judgment that meets such a
short provider failure is sent again and answered within its deadline.

## Reproduction

The records keep digests and fixed metadata, but no request or reply text and
no HTTP status or body (`records.py:247-278`, `docs/backfire.md:185-186`).
They were read locally with a scratch script outside the repository; only the
counts, timings, outcomes and error types below leave them. The window is 2026-09-28
19:00-21:00 UTC, which holds CHE-28's step and every other backfire session
on the machine in that time, so its counts are larger than the issue's.

1. **Outcomes.** 780 judgment records from 370 server sessions: 590 `ok`,
   175 `provider_error`, 9 `truncated_output`, 4 `cancelled`, 2
   `malformed_output`. The 175 failed judgments held 2,092 of the window's
   6,195 questions. Between 19:30 and 20:30 alone, 169 of 507 judgments
   failed with `provider_error`.
2. **What the failures were.** In 175 of 175, the record shows no answering
   model, no token counts and no thinking evidence (`records.py:265-275`);
   165 had one attempt (10 had earlier attempts
   retried as rate limits or connect failures). `provider.py` records exactly
   this for an HTTP error status that no other type claims, such as 500, and
   for a success reply without an answer. CHE-22's assessment
   (`.specify/bugs/answerless-provider-reply/assessment.md`, steps 6-8)
   captured both from the same provider: HTTP 500 within 0.7-0.9 s, and HTTP
   200 whose padded body ended in `{"status_code":500,...}` after 67.5 s. The
   provider sends the 200 status at once and pads the body while the model
   works, so a failure during generation can only arrive in that second form.
3. **Bursts.** Grouped by end time (a gap over 3 s starts a new group), the
   175 failures form 30 bursts between 19:24:29 and 20:30:08. Within a burst
   the failures end within 0.81 s of each other (median 0.01 s), although
   they started up to 99.7 s apart and came from up to 6 sessions (server
   processes). No judgment that was open at a burst survived it: every
   request waiting at that moment failed. 32 failures took under 1 s; they
   had started during the burst itself.
4. **Recurrence.** From 19:46 to 20:30, 24 of 26 gaps between bursts were
   72.5-123 s (median 90.2 s). After 20:30:08 there was no `provider_error`
   in the window, while 251 more judgments succeeded.
5. **Recovery.** The first judgment started after each burst succeeded in 26
   of 30 cases; the earliest started 2.8 s after its burst.
6. **Our load.** In the 5 s before each burst, 0 judgments started in 19 of
   30 cases, and never more than 2, under the documented 5 requests per
   second. Just before 5 bursts only one judgment was open. Rate limits were
   met and handled: 27 successful judgments needed a second or third attempt
   under the existing retry policy.
7. **Documented limits.** Hive's Chat Completions page
   (`docs.thehive.ai/docs/chat-completions-openai-compatible-llms`, read
   2026-09-29) sets a default limit of 5 requests per second, with 429 when it
   is exceeded, and 405 for an exhausted balance. It states no concurrency
   limit and nothing about 5xx statuses, retries or backoff.

## Suspected Code Paths

Line numbers refer to develop `8605cf2`.

- `packages/backfire/src/backfire/failures.py:134-155` — `retry_policy` builds
  the TypeSafe SDK `RetryPolicy` that the adapter applies to every provider
  request. It retries only 429, statuses the profile maps to `rate_limited`,
  and connect-phase failures (`_connect_failure`, lines 119-131).
- `packages/backfire/src/backfire/failures.py:116` — `map_error` gives
  `provider_error` to every status no other type claims, which includes 5xx.
- `packages/backfire/src/backfire/provider.py:107, 109, 163, 165` —
  `ProfileProvider.request` raises `JudgmentError("provider_error")` for a
  success reply without an answer. It runs inside the adapter's retry loop
  (`system_one_adapter/_client.py`, `run_async` →
  `run_with_retries_async`), so the policy's predicate sees this error.
- `specs/005-jev-decision-backend/spec.md:383-391` (FR-007) and
  `contracts/judgment.md:96-111` — the contract allows retries only for
  network errors and rate limits. `research.md` ("One retry layer and one
  deadline") chose not to retry 5xx because Hive documents no retry
  semantics for them and a request may already have been processed.

## Root Cause Hypothesis

The provider has short, repeated failures in which it drops every open
request at once and answers new requests for under a second with a server
error. The bursts do not follow our request rate or concurrency (step 6), so
they are not the documented rate limit, and no concurrency limit is
documented. Backfire classifies both forms of the failure as `provider_error`,
which the retry policy never retries, so every judgment open at a burst is
lost although the provider answers again seconds later (step 5). Confidence:
high for the pattern and for the missing retry; the provider's reason for the
failures is unknown.

## Proposed Remediation

**Preferred**: retry these failures through the retry layer that already
exists, the TypeSafe SDK `RetryPolicy` built in `retry_policy`, with its
existing limits: four attempts in total including the first, backoff from
1 s doubling with jitter, `Retry-After` honored, and no wait that does not
fit the time left before the call's 118 s deadline. Add every 5xx status to
the policy's `http_statuses`, unless the profile maps that status to a type
other than `rate_limited`, and extend its predicate to accept
`JudgmentError("provider_error")`, which `ProfileProvider.request` raises only
for a success reply without an answer. Everything else stays as it is: other
4xx statuses, read errors and timeouts after sending, and every answer
failure are still never retried, and a valid answer is final. No vendor
detail enters package code: 5xx is the standard server-error class, and a
profile can still take a status out of the retry set through `statuses`.

From the records, one retry after about 1 s would have saved about 144 of the
175 failed judgments (82%). This estimate assumes each retry takes as long as
a successful judgment that had run at least as long, and must end before the
118 s deadline and before the next burst.

This amends feature 005's FR-007 and its contracts. The coordinator updates
the documents listed below.

**Alternatives**:
- Pace requests to the documented rate or cap concurrent requests. Not
  chosen: bursts came with no requests starting beforehand and with one
  request open (step 6), and rate limits are already retried.
- Retry only 5xx statuses. Not chosen: about 143 of the 175 failures took
  over 1 s, and a failure after the provider sent its 200 status arrives as a
  reply without an answer (step 2).
- A profile switch that turns these retries on per provider. Not chosen: it
  adds configuration for standard HTTP semantics; `statuses` already lets a
  profile opt a status out.

**Files likely to change**:
- `packages/backfire/src/backfire/failures.py`
- `packages/backfire/tests/test_failures.py`,
  `packages/backfire/tests/test_judge.py`,
  `packages/backfire/tests/test_provider.py`
- `specs/005-jev-decision-backend/spec.md` (FR-007),
  `contracts/judgment.md`, `contracts/provider-profile.md`,
  `data-model.md`, `research.md`
- `docs/backfire.md`

**Tests to add or update**:
- New, through the real judge and the test provider
  (`tests/fake_provider.py`): an HTTP 500 reply followed by a valid answer
  returns the answer with `attempts` 2, in the result and in the judgment
  record. The same for the padded HTTP 200 body without an answer from
  CHE-22's step 8. Both fail on `8605cf2` with `provider_error` after one
  request.
- New: when every attempt fails that way, the judgment fails with
  `provider_error` after four requests, and a retry wait that does not fit
  the time left ends it early.
- Update the tests that encode the old rule:
  `test_failures.py::test_shipped_profile_non_retryable_statuses_fail_once`
  (5xx leave the list), `test_typed_failures_are_never_retried`
  (`provider_error` leaves it),
  `test_judge.py::test_provider_errors_have_fixed_text_and_no_retry` (500),
  `test_provider.py::test_response_failures_are_fixed_and_never_retried`
  (answerless cases) and
  `test_provider.py::test_answerless_provider_error_body_is_sanitized_and_not_retried`.
- Keep: a profile that maps a 5xx status to `request_rejected` is not
  retried, and 403, 404 and 422 still fail after one request.

## Risks & Considerations

- Cost: each retry is billed again, and the provider may also bill a failed
  long request. A retry that the deadline cuts off is billed without an
  answer and ends as `provider_unavailable` instead of `provider_error`.
- Long judgments: a judgment that fails after 90 s has under 30 s left, so
  its retry often cannot finish. The estimate above counts these as lost.
- A provider outage longer than the backoff window (about 7 s) still fails,
  after four fast attempts instead of one.
- This reverses the CHE-22 decision not to retry replies without an answer.
  That decision rested on episodes that "lasted minutes"; the records show
  such an episode is made of failures under a second, with successes in
  between.

## Open Questions

- None. The issue names retrying with a wait as an expected fix, and the
  evidence rules out pacing.
