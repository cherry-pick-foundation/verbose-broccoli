# Bug Assessment: doc-regions prepare builds jev_verify requests too large for OpenRouter

- **Slug**: doc-request-batches
- **Created**: 2026-10-02
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-62> (Linear CHE-62,
  read with `orca linear issue CHE-62 --comments --json`; host `linear.app`)
- **Verdict**: valid
- **Severity**: medium

## Report (summarized)

`npm run doc-regions:prepare` built one `jev_verify` request of about 45,800
characters for `docs/architecture.md`; OpenRouter answered
`400 max_tokens_exceeded`. `--max-evidence-chars` did not help because the size
is claim text. A comment adds that `prepare` passes `--no-renames`, so a
rename-heavy diff overflowed the evidence. On 2026-10-02 another feature saw the
same refusal with a 224-claim request while a 110-claim request was answered.

## Reproduction

`verify_requests` at `c0b630b` splits claims only by answer cells
(`672 // 3` = 224 claims with one evidence item). 106 claims of 470 characters
give one request of about 50,000 characters; 224 one-character claims give one
request of 224 claims. `prepare` lists changed files with `--no-renames`, so a
renamed file is evidence twice, as a whole deletion and a whole addition.

## Suspected Code Paths

- `packages/doc-regions/src/doc_regions/requests.py`: `verify_requests`
  (claim batching) and `prepare` (diff options).
- Neither `jev-judge-mcp` 0.6.0 (`limits.py`: `VERIFY` caps are open) nor
  backfire (`docs/backfire.md`: it does not split requests) batches by size, so
  there is no upstream batching to reuse.

## Root Cause Hypothesis

The only bound is the 672-cell rule from the old backfire limits. The provider's
real limit is on tokens, so it depends on the claim characters and the claim
count. Confidence: medium; the limit is not published in the repository, so the
numbers below come from the reported successes and failures.

## Proposed Remediation

**Preferred**: add two bounds to each `jev_verify` request: at most 110 claims
(the largest request known to be answered) and at most 12,000 claim characters
(the four hand-split requests of about 11,500 characters were answered). A
claim above the character bound stops `prepare` with an error naming it, so
nothing is dropped or sent too large.
Evidence is the same in every request of a group, so it is not counted. Replace
`--no-renames` with `-B -M` and read `--name-status` and one full diff split per
file (so renames onto a moved path stay renames), so a renamed file is one
rename diff; a rename is left out only when both its paths are excluded.

**Alternatives**: a `--max-claim-chars` option (more surface, no demand);
splitting evidence per request (changes the judgment).

**Tests**: claim sets of 106 long claims, 224 short claims and one oversized
claim must give requests within both bounds, in order, with no claim lost; a
renamed file must give one small rename diff, also when it moves into an
excluded path. Both fail at `c0b630b`.

## Model choice

Jev (OpenRouter `typesafe/jev-1.13`) chose Claude Code `claude-sonnet-5-5` at
medium effort (score 0.29, confidence 0.20; tied at 0.29 with Codex
`gpt-6.1-sol` at medium). Estimated difficulty: medium. Usage at 04:20 KST on
2026-10-02: Codex weekly 72% used until 2026-10-03T17:28:48Z; Claude session 4%,
weekly 58%, Fable-only 8%.

## Risks & Considerations

- 110 claims and 12,000 characters are measured successes, not a measured
  limit. A live probe was not made (0 paid calls), so the true limit may be
  higher; a smaller request only costs more calls.
- The request size is bounded by claim count and claim characters only. Total
  evidence stays under `--max-evidence-chars` per item and the 249-item cap; a
  very large evidence set can still be refused. Not changed: evidence size has
  its own option, and the reports name claim text as the cause.
- Rename detection pairs files by similarity, so a rename with a heavy edit is
  shown as a delete plus an add, as before.

## Open Questions

- None.
