# Report: Backfire Provider Choice by Credit

**Linear issue**: CHE-46 | **Branch**: `feature/backfire-provider-credit`

## Outcome

Backfire now reads one ordered list of provider profiles, shared by the code
and work plugins, from `packages/backfire/src/backfire/config.toml`:
OpenRouter, then Hive. Before it first uses a profile that names a CodexBar
provider, it reads that provider's credit through CodexBar 0.69.0 and skips
the profile when the balance is zero or less or a limit is used up. When the
provider in use answers a status its profile lists as insufficient balance,
backfire sends the same judgment to the next profile and keeps it for the
session; with no profile left, the judgment fails with `no_credit`. Each
result's `provider` field names the profile that answered. Backfire's
Jev-on-Vercel provider (`vercel.py`) is deleted, as the user decided.

The Cloudflare and Vercel profiles with free models, their measurement on the
111-decision set, the account-ID fill and the switch on Cloudflare's code
3036 moved to CHE-51. Moving the offer search in `packages/credit-offers`
onto backfire is a separate feature. [research.md](research.md) is CHE-51's
starting point.

## Tests

`npm run test:backfire`: 185 passed and 1 expected failure. The expected
failure is the existing CHE-38 case in `tests/test_bounded_work.py`, not
part of this feature. New tests: `tests/test_credit.py` (CodexBar reading,
the minimal environment, unknown credit) and `tests/test_order.py` (skip,
switch, concurrent failures, `no_credit`, configuration errors, education
mode after a switch).

## Live calls

| Provider | Calls | Purpose |
| --- | --- | --- |
| Hive | 4 | `jev_decide` choosing the implementer, the research worker, the reviewers and the review fixer, through `develop`'s backfire |
| CodexBar | 3 reads | OpenRouter credit, once per backfire server: the live judgment and the two document-step runs; CodexBar called OpenRouter's key and credits endpoints, not Jev |
| OpenRouter | 9 | The live judgment on 2026-09-30 12:35 KST, `jev_verify` on one synthetic claim: the result named `openrouter`, model `typesafe/jev-1.13`, verdict verified at 0.99, 523 input and 46 output tokens. Then 8 calls for the document judgment step below |
| Vercel | 0 | |
| Cloudflare | 0 | |

## Size and split review

Against `develop`, without the Spec Kit records: code 298 lines added and
240 deleted, tests 831 added and 197 deleted, documents 85 added and 61
deleted. Three whole files were deleted (`vercel.py`, `test_vercel.py`,
`backfire_education/config.toml`), which the split rule counts as about
one line each; without them the change is about 1,500 lines. Non-test code
grows by 58 lines net, because the 125-line Vercel port is gone; about 960
of the changed lines are tests.

The `AGENTS.md` split review: the offer search and the new Cloudflare and
Vercel profiles were already split out (CHE-51 and a separate feature). The
rest is one mechanism, the order, the credit reading and the switch, whose
parts are not useful alone, so it stays one feature.

## Document judgment step

`npm run doc-regions:prepare -- --base develop --max-evidence-chars 40000`
at `develop` `b9a0293` produced 241 units in six `jev_verify` requests and
one `jev_classify` request, sent through this branch's backfire on
2026-09-30: 8 OpenRouter calls, one of them lost to an error in the
coordinator's sending script and sent again.

- One unit was judged contradicted: the constitution's "Retain existing
  source and storage roots unless a specified capability changes them"
  (`.specify/memory/constitution.md:150-151`), against this feature's
  deletion of `backfire_education/config.toml` and `vercel.py`. It stands:
  FR-009 and FR-013 specify both deletions, and constitution findings are
  reported to the user, not changed here.
- 92 other units were flagged for review. They are either outside this
  feature's diff (the constitution, `AGENTS.md`, `README.md` and unrelated
  sections of `docs/architecture.md`) or backfire guide and architecture
  passages this feature wrote, which the coordinator checked against the
  code; none needed a change.
- `jev_classify` suggested `docs/backfire.md:44-49` (the shared order) as a
  mechanical candidate at 0.61 and kept four units as agent regions. It
  stays an agent region: the paragraph explains the order in prose around
  the two profile names.

`npm run doc-regions:audit` (MemoryLint 1.5.1) reported 19 boundary
warnings, all suggesting that constitution passages move to `AGENTS.md`.
They exist on `develop` already, and this feature does not change either
file; they are reported to the user only.

## Workers

| Work | Agent and model | Chosen by | Confidence |
| --- | --- | --- | --- |
| Implementation (T002-T006, T012) | Codex `gpt-6-luna`, xhigh | `jev_decide` | 0.39 |
| Research for CHE-51 | Claude Code Sonnet 5.5, high | `jev_decide` | 0.77 |
| Code review | Claude Code Sonnet 5.5, high | `jev_decide` | 0.48 |
| Records review | Codex `gpt-6-luna`, xhigh | `jev_decide` | 0.48 |
| Review fixes | Codex `gpt-6-luna`, high | `jev_decide` | 0.39 |

## Review

Fresh reviewers, started through Orca in the coordinator's child Run,
reviewed the branch at `c2b7b70` for the merge into `develop`, favoring
speed:

- Code (Claude Code Sonnet 5.5, high effort): approve, with 0 blockers, 0
  majors and 6 minors: the response-cache key on the first call, an empty
  or repeated `order` accepted, a null `providerCost.balance` skipping the
  details fallback, missing tests (skip log line, every profile skipped,
  99.9% used, comma amounts, tertiary window), no switch test through
  PyModel's own OpenRouter provider, and three simplifications. A Codex
  worker (`gpt-6-luna`, high, `jev_decide` confidence 0.39) fixed all six in
  `48da42a` (non-test code +37/-50, 184 tests passing). The coordinator
  reviewed that fix and found that it dropped a guard, so a dollar value
  with no digit would raise instead of counting as unknown credit; the same
  worker fixed it in `8aae2c6` (185 tests passing).
- Documents and records (Codex `gpt-6-luna`, xhigh): request changes, with
  0 blockers, 1 major and 3 minors: the spec's size criterion contradicted
  the measured size; `research.md` cited the wrong guide line; `plan.md`
  kept Vercel status guidance for a profile this feature no longer ships;
  and the guide and skill texts said "the first profile that has credit"
  although unknown credit keeps a profile. The coordinator fixed all four
  in `166e9a0`.
