# Bug Assessment: Document judgment step fails on Hangul in docs/backfire.md

- **Slug**: doc-judgment-refusals
- **Created**: 2026-10-01
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-67> (Linear issue
  CHE-67, read with `orca linear issue CHE-67 --json`; host `linear.app`,
  allowlisted)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

CHE-67, "Document judgment step fails on docs/backfire.md's Korean examples
since the Hangul refusal": since CHE-61, backfire refuses any request that
holds Hangul, in both modes (`hangul_remaining`). Eleven units of
`docs/backfire.md`, the privacy rules' Korean examples, hold Hangul, so every
`jev_verify` request that carries them fails. CHE-57 set those units aside and
sent the other 256. Expected: the judgment step runs in full without sending
Hangul. Options named: translate or romanize the examples, or leave such units
out of the requests and report them as not judged. Related: CHE-62.

## Symptom

`npm run doc-regions:prepare -- --base develop --max-evidence-chars <n>` prints
requests whose claims and evidence hold Hangul, so the agent cannot send them.

## Reproduction

On `develop` `f6cb865`, with `--base develop --max-evidence-chars 20000`:

1. `npm run doc-regions:prepare` exits 0 and prints 267 units, 11 of them with
   Hangul (all in `docs/backfire.md`).
2. Those 11 units are in the claims of the printed `jev_verify` requests, and
   `packages/backfire/src/backfire/providers.py:253` raises
   `hangul_remaining` for any request string that matches `_HANGUL`
   (`providers.py:31`).
3. Evidence can hold Hangul too: it is the raw `git diff` of every changed
   non-document file.

## Suspected Code Paths

- `packages/doc-regions/src/doc_regions/requests.py` — `prepare` copies unit
  text and diff text into the requests unchanged.

## Root Cause Hypothesis

`doc-regions` was written before the refusal and sends text as is. Confidence:
high.

## Proposed Remediation

**Preferred**: in `prepare`, spell every Hangul run of the claims and of the
evidence in Latin letters before building the requests, with a published
library (anyascii 0.3.3, ISC, no dependencies). The printed `units` keep their
Hangul so the agent can edit the document. All units are judged, the document
stays as written, and each claim and its evidence are spelled the same way.
Romanize before chunking the evidence, so `--max-evidence-chars` bounds the
text that is sent.

**Alternatives**:
- Translate or romanize the examples in `docs/backfire.md`. Not chosen: the
  examples show what Hangul input backfire replaces, so they must stay Korean.
- Leave Hangul units out and report them as not judged. Not chosen: it never
  judges those units, and the task asks for a full run.
- es-hangul (already a dependency) romanizes better, but it is JavaScript and
  `doc-regions` is Python; calling Node from the package would add a runtime
  dependency that the Wiki instances using it as a library may not have.

## Impact and Risk

Every feature's develop merge review hits the refusal. Risk of the fix is low:
only requests change, and a judge reads romanized claims and evidence alike.
CHE-62 (request size) is separate.

## Documents to Update

- `docs/architecture.md` — the judgment-step bullet.
