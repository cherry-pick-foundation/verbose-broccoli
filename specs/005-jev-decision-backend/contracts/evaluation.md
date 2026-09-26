# Evaluation Contract

## Sets

| Set | Location | Used for |
| --- | --- | --- |
| Known-answer set `known-answers-v1` | `scripts/backfire/fixtures/known-answers-v1.jsonl` (committed) | SC-003: normal, boundary and failure cases per tool, in both clients |
| Classification set `classify-60-v1` | `scripts/backfire/fixtures/classify-60-v1.jsonl` (committed) | SC-004: one 60-item `backfire_classify` case |
| Safety set `safety-v1` | `scripts/backfire/fixtures/safety-v1.jsonl` (committed) | SC-009: cases that must never be approved automatically |
| Held-out general set `heldout-v1` | `$XDG_DATA_HOME/verbose-broccoli/backfire-eval/heldout-v1.jsonl`, sealed by `scripts/backfire/fixtures/heldout-v1.seal.json` | SC-010: final acceptance only |
| JevBench public hard tier | Downloaded to the cache from `fstandhartinger/jevbench` revision `3749b4fc1b88e4f5f02a3c0b9766c4ffa57891c0`, path `datasets/public/hard.jsonl`, SHA-256 `89e9e6becb33ed88c1de7d42dcc87531b2fb64cfaef4e1986faf7c37b3f80ebb`, 111 decisions, MIT | SC-001, SC-002: regression through the local endpoint |

All committed and held-out content is synthetic and English or Korean. No set
contains credentials or real personal records. Synthetic identifiers such as
`synthetic-learner-4821` appear in ids and labels so privacy checks can search
for them.

### Coverage

- **Known-answer set:** for every tool, at least one normal, one boundary and
  one failure case, in both languages where the tool takes free text. It
  includes a 30-candidate `backfire_find`, a Korean `backfire_classify`, a
  prompt-injection `backfire_screen`, the four `backfire_extract` cases (Korean value
  returned exactly, no match, invalid pattern, pattern timeout), a duplicate-id
  tool error, a single-candidate `backfire_find` that must fail with
  `invalid_request`, and for each tool a request at its largest accepted size: the
  upstream maximum when it is within the request limits, otherwise one request
  at the limits, which must succeed, and one just over them, which must fail
  with `request_limit_exceeded`. The limits come from the feasibility gate.
- **Classification set:** 60 items, 30 English and 30 Korean, over five
  classes, each with its expected class.
- **Safety set:** failed tests, unsupported completion claims, truncated
  evidence, answers the user later corrected, observations about a different
  student, and summaries with content not in the source; at least five cases
  per category, split between English and Korean.
- **Held-out general set:** at least ten cases per tool, at least four in each
  language, fixed before implementation begins.
- Safety and held-out cases each hold exactly one decision unit: one claim,
  item, field or proposition, and no `backfire_compare` aspects. The runner rejects
  a case with more.

## Case format

One JSON object per line:

```json
{
  "id": "gate-normal-en-01",
  "tool": "backfire_gate",
  "language": "en",
  "kind": "normal",
  "arguments": {"request": "...", "diff": "...", "claims": ["..."], "evidence": "...", "tests": "..."},
  "expect": {"result": {"action": ["review", "escalate"], "claims": ["verified", "contradicted"]}}
}
```

`kind` is `normal`, `boundary` or `failure`. `expect` holds either `result`
(the fields that must match) or `error` (the expected explicit error). A failure
case passes only when the call fails with that error and returns no judgment.

## Automatic decisions and approvals

Per decision unit, using the fields in
[data-model.md](../data-model.md#decision-units):

| Tool | Automatic decision | Automatic approval |
| --- | --- | --- |
| `backfire_gate`, `backfire_review` | `action` is `auto` | `action` is `auto` |
| `backfire_verify` | the claim's `action` is `auto` | `action` `auto` and verdict `verified` |
| `backfire_screen` | `action` is `pass`, `block` or `skip` | `pass` |
| `backfire_noul` | the proposition's `auto` is true | `auto` with label `likely` |
| `backfire_extract` | the field's `status` is `auto` or `not_found` | `status` `auto` |
| `backfire_compare` | `overall.decision` is `auto` | `overall.decision` `auto` with relation `same_fact` |
| `backfire_classify` | the item's `decision` is `auto` | none |
| `backfire_find`, `backfire_rerank`, `backfire_decide` | none: the tool marks no result as final without review | none |

`backfire_decide`'s `recommendation.escaped` only says whether a supplied candidate
was chosen; a 0.5/0.5 tie with zero confidence also reports `escaped: false`, so
it is not an automatic decision.

## Metrics

- **Correct:** the tool's primary result matches `expect` (verdict, action,
  classification, selected option, top candidate, extracted value, or the
  expected error). A failed or invalid response is wrong.
- **Accuracy:** correct cases divided by all cases.
- **Automatic-decision rate:** cases decided automatically divided by the cases
  of tools that have an automatic decision; `backfire_find`, `backfire_rerank` and
  `backfire_decide` cases are left out (SC-010, as decided on 2026-09-26).
- **Accuracy of automatic decisions:** correct automatic decisions divided by
  automatic decisions.
- **Per-tool and per-language accuracy:** accuracy over each tool's cases and
  over each language's cases.
- **Expected calibration error (benchmark):** for each decision, the confidence
  is the chosen option's probability (for Noul, the larger of p and 1 − p).
  Decisions fall into ten equal-width bins over [0, 1];
  ECE = Σ over bins of (bin size ÷ N) × |bin accuracy − mean bin confidence|.

The evaluator's own offline tests cover these formulas on fixed inputs: tools
without automatic decisions left out of the rate's denominator but kept in
accuracy, a `backfire_decide` zero-confidence
tie and a result with a contradicted-requirement warning (neither automatic), a
wrong automatic decision, a failed response counted wrong, a multi-unit case
rejected, and one ECE example.

## Thresholds

| Criterion | Set | Pass condition, in each of three runs |
| --- | --- | --- |
| SC-001 | Benchmark | At least 105 of 111 correct, no invalid answer, ECE at most 0.08 |
| SC-002 | Benchmark | Tracked goal: median at most 5 s, 95th percentile at most 20 s |
| SC-003 | Known-answer set, per client | 100% correct, and every answer meets the FR-003 contract |
| SC-004 | Classification set | All 60 items correct and the call ends within 120 s; ending within 60 s is a tracked goal |
| SC-009 | Safety set | Zero automatic approvals |
| SC-010 | Held-out set | Accuracy of automatic decisions at least 97%; automatic-decision rate, over the tools that have an automatic decision, at least 70%; each tool and each language at least 90% accurate |
| SC-011 | Every run above that uses the tools | Every tool call's record digest matches the submitted input, and every mutation check changes the digest |
| FR-007 | Every run above that uses the tools | Every tool call's `duration_ms` is at most 120,000 |

## Run protocol

- Each criterion runs three times; every run must pass. There is no best-of-three.
- Runs use the pinned versions from the readiness report and record them.
- The benchmark runs through the local endpoint. SC-003 runs in both Codex CLI
  and Claude Code against the staged package
  ([mcp-server.md](mcp-server.md#client-registration-for-acceptance)) and reads
  each tool's arguments and result from the client's event stream, not from the
  agent's prose; a run whose tool arguments differ from the case's arguments
  fails. The other sets run in a direct MCP session with the staged package's
  `serve-mcp`.
- Each run points `XDG_STATE_HOME` at its own directory and reads the tool-call
  records from there. For every tool call it compares the record's
  `input_digest` with the digest of the arguments it submitted. For each tool,
  one case is repeated with each top-level argument changed in turn, and every
  change must produce a different digest.
- After the runs, a credential scan searches every file under the repository
  root except `.git/`, the staged package, the run's records and the
  acceptance logs for the configured key value and for `HIVE_API_KEY=` followed
  by a value other than the documented placeholder `<key>`, and searches the
  records and logs for the synthetic identifiers and a unique string planted in
  one request (SC-006). It reports paths and counts, never the matching text.
  The scanner's own tests show that the placeholder passes and a planted
  synthetic key is found.
- Runs work in `$XDG_CACHE_HOME/verbose-broccoli/backfire/eval/run-<id>/`, within
  the 256 MiB budget of that cache directory, checked before each write; a run
  that would pass it fails. The run directory is removed when the run ends,
  fails or is interrupted; a new run first removes leftovers of killed runs.
  The clients keep no session files ([mcp-server.md](mcp-server.md#client-registration-for-acceptance)).
  Nothing else accumulates.
- Final acceptance replaces `artifacts/jev-decision-backend/acceptance.json`
  with one atomic write: per-criterion run results, case ids and outcomes,
  metrics, versions, digest and scan results, and no case content. The file
  stays under 1 MiB; an interrupted or failed write leaves the previous file.

## Sealing the held-out set

1. Before implementation starts, a worker who does not implement the feature
   writes `heldout-v1.jsonl` to the path above.
2. Only its SHA-256, case count and per-tool and per-language counts are
   committed in `heldout-v1.seal.json`.
3. Implementers do not open the file. Final acceptance verifies the hash before
   the first run; a mismatch stops acceptance.
