# Bug Assessment: A provider reply without an answer is reported as malformed_output

- **Slug**: answerless-provider-reply
- **Created**: 2026-09-29
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-22> (Linear issue
  CHE-22, read with `orca linear issue CHE-22 --json`; host `linear.app`,
  allowlisted)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

CHE-22, "Some backfire_verify requests fail on every attempt
(malformed_output, provider_error)": on 2026-09-28, in the document judgment
step before CHE-10's develop merge review (`deno task doc-regions:prepare --
--base 136866a --max-evidence-chars 20000`, sent through the repository's
`backfire serve-mcp` to DeepSeek V4.1 Flash on Hive), request 1 (84 units,
input digest `3108ade945dc`) failed with `malformed_output` on both attempts,
and request 3 (52 units, digest `686fbfc2359c`) failed with `provider_error`
on both attempts, while request 2 (84 units, digest `95ca6ccb27ab`) passed. In
the records of the `malformed_output` failures, `model` and every `usage`
field are empty. The issue's unverified lead: `provider.py:82-86` raises
`malformed_output` whenever the HTTP body is not a JSON object, so a
provider-side error or a cut-off body may be reported as a malformed model
answer. Expected: the requests are judged or split into requests the provider
accepts, and a provider-side failure is reported as `provider_error`.

## Symptom

When the provider fails after it has already sent HTTP 200, backfire reports
`malformed_output`, whose message tells the caller to check the profile and
model compatibility, instead of `provider_error`, which tells it to check the
provider. The failures themselves were a provider-side episode, not a property
of the requests.

## Reproduction

Local replay, without provider calls:

1. Clone the repository at `0d5cf3e`, the tip of `feature/backfire-chat`
   (CHE-10) when the failures were recorded, and run `doc-regions prepare
   scripts/doc_regions.toml --base 136866a --max-evidence-chars 20000` there.
   All three requests' input digests (`digest({"tool", "arguments"})` from
   `records.py`) match the records: `3108ade945dc`, `95ca6ccb27ab`,
   `686fbfc2359c`. `packages/backfire/src/backfire/`, the runtime package, has
   not changed between `0d5cf3e` and develop `2262815` (only the build tool in
   `backfire_tools/` has), so the replay runs the code that failed.
2. Run each request through `backfire.tools.verify.call` against the test
   provider in `tests/fake_provider.py`
   (`BACKFIRE_TEST_PROVIDER_BASE_URL`) to capture the exact HTTP bodies.
   Size does not explain the failures: failing request 1 is 246 KB, failing
   request 3 is 165 KB, and passing request 2 is 278 KB.
3. The records keep no HTTP status or body, so what the provider sent back
   can only be observed with billed calls.

Billed calls, approved by the user through the develop session on
2026-09-28 at 16:21 UTC (Orca reply `msg_85042e227034` to question
`msg_ba4310755727` in Run `run_8b222073b123`; `orca orchestration inbox
--full` shows both),
raw replies kept outside the repository:

4. The three captured bodies sent directly to the Hive endpoint: all three
   returned HTTP 200 with complete answers in 57-71 s.
5. The three requests through backfire's real judge, twice in a row (six
   calls): all six passed.
6. A third round right after: all three got HTTP 500 within 0.7-0.9 s, with
   the body `{"status_code":500,"message":"Internal Server Error"}`. backfire
   reported `provider_error`, which is correct, and matches request 3's
   records (0.4 s and 4.5 s, one attempt each).
7. Every HTTP 200 reply above starts with 5 to 11 spaces before the JSON,
   about one per 8 s of processing, with `Transfer-Encoding: chunked` through
   CloudFront. The provider commits the 200 status at once and pads the body
   to keep the connection open while the model works.
8. A fourth round: requests 1 and 3 passed. Request 2 got HTTP 200, and its
   body was 8 spaces followed by
   `{"status_code":500,"message":"Internal Server Error"}`. backfire reported
   `malformed_output` after 67.5 s, with no model and no usage: the failure
   in the issue, reproduced.

In total 15 calls completed: 3 direct and 12 through the judge. 11 passed,
3 got a 500 status, and 1 got the padded 500 body. A fifth round was stopped
as soon as it started. It left no capture and no other durable record; only
the coordinator's session saw it, so whether its requests reached the
provider is unknown.

## Suspected Code Paths

Line numbers refer to develop `2262815`.

- `packages/backfire/src/backfire/provider.py:81-86` — a 2xx body that is not
  JSON, or not a JSON object, raises `malformed_output`.
- `packages/backfire/src/backfire/provider.py:105-108, 118-119` — a JSON
  object without a `choices` list leaves `message` empty, and line 119 raises
  `malformed_output`. A body such as Hive's error object above has no
  `model`, `usage` or `choices`, so it ends here with `model` and `usage`
  empty, exactly as in request 1's two records.
- `packages/backfire/src/backfire/failures.py:188-207` — `map_error` passes
  the provider's `JudgmentError` through unchanged, so the provider module's
  choice is what the caller sees.
- `specs/005-jev-decision-backend/contracts/judgment.md:84` and
  `packages/backfire/tests/test_provider.py:107-108, 328` — the contract and
  its tests define "No choices" and a body that is not a JSON object as
  `malformed_output`, so the misreport is specified behavior.

## Root Cause Hypothesis

Two things combine. First, the provider had transient server errors: on
2026-09-28 during 09:22-09:26 UTC and again during this assessment, while the
same inputs passed in 11 of 15 billed calls, and each request both failed and
passed, so neither the inputs nor their size cause the failures. Second, because the provider sends HTTP 200 before
the model finishes, a failure that happens later can only arrive as a 200
body without an answer, and backfire's contract classifies such a reply as a
malformed answer. A `malformed_output` record with no `model` and no `usage`
can only come from a 2xx reply that names no model: a body that is not a JSON
object, or an object without `model` (lines 84, 86 or 119). A normal chat
completion names its model, so request 1's replies were not model answers.
Confidence: high; step 8 reproduced the failure with the provider's padded
error body.

## Proposed Remediation

**Preferred** (the user chose this rule on 2026-09-28 at 16:30 UTC, Orca
reply `msg_645483aa274c` to question `msg_9835910a0f6e` in Run
`run_8b222073b123`): a 2xx reply that
carries no answer at all is `provider_error`. That covers a body that is not
JSON, a body that is not a JSON object, and an object whose answer container
is missing, null or empty: `choices` for Chat Completions, `output` for the
Responses API. This covers an error object of any shape without matching a
vendor's error format. A reply that has choices but empty content, missing
usage, or invalid answers stays `malformed_output`. Change the checks in
`ProfileProvider.request` before the usage and message checks; keep the
record fields and the no-retry policy unchanged. Update feature 005's error
table in `contracts/judgment.md`, the `provider_error` row in
`docs/backfire.md`, and the tests that encode the old classification.

**Alternatives**:
- Treat only a non-JSON body and an object with an `error` member as
  `provider_error`. Not chosen: the provider's error object in step 8 has no
  `error` member, so that case would still be misreported.
- Retry such replies. Not chosen: every attempt is billed, feature 005 never
  retries 5xx or answer failures, and the provider episodes lasted minutes.
- Split the document judgment requests in `doc-regions prepare`. Not needed:
  the failing requests are smaller than the passing one, and they pass when
  the provider is healthy.

**Files likely to change**:
- `packages/backfire/src/backfire/provider.py`
- `packages/backfire/tests/test_provider.py`
- `specs/005-jev-decision-backend/contracts/judgment.md`
- `docs/backfire.md`

**Tests to add or update**:
- A test with the test provider sending HTTP 200, leading spaces, and then an
  error object without `choices`, as observed in step 8; it
  expects `provider_error` with no answer text in the error, and fails on
  develop `2262815` with `malformed_output`.
- Update `test_response_failures_are_fixed_and_never_retried`
  (`empty_choices`, `missing_choices`, `null_choices`) and
  `test_malformed_envelopes_fail_without_raw_diagnostics` (invalid JSON, `[]`,
  `null`) to expect `provider_error`; `{"choices": [None]}` stays
  `malformed_output`.
- A Responses API case for a reply without `output`, if the existing
  Responses test can carry it.

## Risks & Considerations

- This changes a documented contract of feature 005. Callers that branch on
  `malformed_output` for such replies now see `provider_error`; the
  repository's callers only report the error type.
- The test uses the body observed in step 8, but the rule does not depend on
  its shape: any 2xx reply without an answer container is `provider_error`.
- The document judgment step still fails while the provider has an episode.
  The error now names the provider, and the caller reruns later.

## Open Questions

- None. The user chose the classification rule (option A) on 2026-09-28;
  see Proposed Remediation.
