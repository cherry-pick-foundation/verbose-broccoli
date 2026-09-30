# Report: Backfire Rebuilt on jev-judge-mcp (CHE-39)

**Branch**: `feature/backfire-rebuild`. **Dates**: 2026-09-29 to
2026-09-30. **Status**: implemented, reviewed and verified; ready to finish into
`develop`.

## Result

Backfire is now a thin layer over PyModel's published
[jev-judge-mcp](https://github.com/PyModel/jev-judge-mcp) 0.6.0 (MIT),
installed from PyPI. `backfire serve-mcp` builds PyModel's own
`JevMCPServer` from PyModel's eleven tools plus `jev_noul`, and plugs in
only through PyModel's extension points: a provider factory and PyModel's
retry policy. Backfire's providers send each judgment to the selected
profile:

- a general-model profile, DeepSeek V4.1 Flash on Hive by default, through
  system-one-adapter, with PyModel's retries plus CHE-33's retry of a
  success reply without an answer;
- a Jev profile naming PyModel's `typesafe`, `openrouter`, `cloudflare` or
  `compatible` provider, or `vercel`, a Vercel AI Gateway provider ported
  from jkudish's jev-agent-tools 0.1.2;
- with `--education` (the work plugin), either kind wrapped by the existing
  pseudonymization module.

Both plugins start backfire straight from `packages/backfire` in the
repository. The server reports PyModel's name `jev-mcp`, and the tools use
PyModel's `jev_` names; the skills, documents, `scripts/workflow.ts` and the
doc-regions and wiki-consistency request builders were changed to match.

## What was removed

The jev-mcp 0.9.0 port, the call boundary (10 MiB message limit, 118-second
call deadline, per-call records), judgment records, the readiness command,
backfire's size limits, the extra Hive checks and fixed error types (except
`JudgmentError`), the acceptance tools and their fixtures, the plugin build
tool, and the vendored copy of PyModel from the first design. Backfire's
own Python and TOML code went from 7,700 lines on `develop` (including the
pseudonymization module) to 791 plus the unchanged pseudonymization module.

## Own code (user's size rule)

Counted with `wc -l` over `packages/backfire/src/backfire/` (Python and
TOML), tests and `backfire_education` excluded: 791 lines at `ed1294f`,
803 after the review fixes at `934c259` (`providers.py` 235,
`__main__.py` 49; the pseudonymization module changed by 20 added and 2
removed lines).

| File | Lines | What it holds |
| --- | --- | --- |
| `providers.py` | 225 | Hive provider, CHE-33 retry, Jev profiles through PyModel's resolver, education wrapper, retry table |
| `noul.py` | 204 | `jev_noul`: jev-mcp 0.9.0's definition text, questions and decision logic |
| `config.py` | 145 | profile selection and `0600` key files |
| `vercel.py` | 125 | Vercel provider, 23 lines of it the MIT license text the port carries |
| `__main__.py` | 47 | the entry point |
| `failures.py` | 23 | `JudgmentError` for pseudonymization and wiki-consistency |
| `config.toml` | 21 | shipped Hive profile and unselected Vercel profile |
| `__init__.py` | 1 | package marker |

This is above the 500-line target. On 2026-09-30 the user accepted about
791 lines plus what the privacy fix needed, and kept `jev_noul`, the Jev
profiles and the Vercel provider.

## Load: CHE-37 and CHE-38

- **CHE-37 (regex time limit)**: the user dropped the `regex` library;
  `jev_extract` uses PyModel's warmed regex worker pool. With 80 busy
  `nice -n 19 yes` processes, 5 runs through backfire's server and 8 runs
  in PyModel's own clone gave no false time-out of a simple pattern, and
  every runaway pattern timed out. CHE-37 is resolved by PyModel's design;
  no fix was needed.
- **CHE-38 (event-loop stall)**: the stall is inside PyModel (quadratic
  duplicate IDs and synchronous parsing). With 16 busy processes, every
  other tool's worst stall over three runs was at most 148 ms
  (`jev_find`); `jev_verify` with 100,000 identical evidence IDs stalled
  2.6 to 5.6 seconds and is a strict expected failure naming CHE-38. The
  prepared PyModel patch
  ([upstream/pymodel.patch](upstream/pymodel.patch),
  [upstream/pull-request.md](upstream/pull-request.md)) brings that case to
  8.3 ms; it applies to v0.6.0 and PyModel's offline suite passes on it
  (4,584 passed). Nothing was published. CHE-38 stays open until a PyModel
  release includes a fix.

## Live checks (billed)

- Hive, shipped profile: one call to each of the twelve tools, all valid;
  12 billed requests, no retries.
- Vercel AI Gateway, with the chat plugin's key file: the gateway accepted
  the key but answered HTTP 429 "No access to this model at this time." for
  `typesafe-ai/jev`; about 6 refused attempts over two runs, no judgment.
  Vercel's free tier does not give access to the Jev model (another session
  got "Free tier users do not have access to this model"), so the user
  decided to record the Vercel live check as not done. The Vercel provider
  passes its stub tests.
- Document judgment step before the merge review: 27 requests over 244
  units, run with the shipped Hive profile. About 20 attempts timed out
  under PyModel's 30-second default before the retry settings were added;
  the rerun made 28 attempts and a follow-up run 7. Details are under T019
  in [tasks.md](tasks.md).
- Billed or possibly billed attempts in total: 12 live Hive tool calls,
  about 55 document judgment attempts, and about 6 refused Vercel attempts.

## Checks

- `npm run verify`: see T019 in [tasks.md](tasks.md) for the three runs in
  a row on the final commit.
- `npm run test:backfire`: 142 passed, 1 strict expected failure (CHE-38).
- doc-regions 106 passed, wiki-consistency 291 passed, `plugins:validate`
  passed.

## Merge review

- Code (fresh Claude Code reviewer, `claude-sonnet-5-5` at medium effort,
  chosen with `jev_decide`): round 1 requested changes: one blocker (the
  work plugin did not pseudonymize PyModel's question text), one major
  (tests missed it) and five minors. All were fixed in `934c259`, with
  tests that failed on the earlier code. Round 2 (a fresh reviewer, same
  model) approved with two minors that stand: the load test measures
  under whatever load the machine has rather than starting load itself,
  as its 16- and 80-process runs are recorded in [tasks.md](tasks.md);
  and the score-legend restore handles list rubrics only, which is what
  PyModel's `jev_score` sends. That reviewer ran all twelve tools in the
  work plugin's mode with a synthetic roster and a recording provider: no
  roster name, guardian, school, phone number or email reached the
  provider, and the answers came back restored.
- Records (fresh Codex reviewer, `gpt-6-luna` at max effort): four majors
  and two minors on the contracts, skills, license rule, report and error
  text, fixed in `f07d66c`.
- The document judgment step flagged principle VI's XDG namespace list in
  the constitution as contradicted; it stays as written unless the user
  says otherwise.

## Known limits and follow-ups

- A client that copies a plugin elsewhere, such as a Codex local
  marketplace install, cannot start backfire, because `mcp.json` names a
  repository path; the plugins are meant to be used from the checkout.
- Very large judgments can still exceed the 110-second attempt on Hive's
  reasoning model; one document request with 69 evidence items did.
- system-one-adapter prints Pydantic serializer warnings to stderr for each
  Hive judgment; they are noise from the adapter's answer models, as
  before the rebuild.
- CHE-38 waits for PyModel; the contribution is ready for the user to
  decide whether to open it.
