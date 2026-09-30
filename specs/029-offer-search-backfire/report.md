# Report: Offer Search Through Backfire

**Linear issue**: CHE-49 | **Branch**: `feature/offer-search-backfire`

## Outcome

The credit-offer search in `packages/credit-offers` sends its one judgment
per run through backfire's library (`backfire.providers.provider_factory`),
so it follows backfire's shared provider order, the CodexBar credit check
and the switch on insufficient balance. The state, the choice questions,
the printed lines and the exit statuses (0 at least one strong offer, with
or without `--notify`; 1 no strong offer; 2 bad arguments; 3 failed
request) are unchanged. Answers are checked with
PyModel's `validate_choice`. The package depends on `backfire` instead of
`jev-ultrafast`; the web agent keeps `jev-ultrafast` and OpenRouter.

The command no longer reads `JEV_PROVIDER` or provider keys from its
environment, because backfire reads each profile's key file itself. The
develop session decided that the automation's precheck passes only
`github.env` (spec, Clarifications).

## Tests

`npm run test:credit-offers`: 21 passed. The judgment tests replace
`provider_factory` with a fake provider and check the state, questions and
model sent, that the provider is closed once, statuses 0, 1, 2 and 3, and
that configuration, no-credit and timeout failures and an invalid answer
end with status 3 without showing a key.

## Live calls

- One run on the block ending 2026-09-26 12:00 (Asia/Seoul): the tracker
  index did not change between the block's edges, so no judgment was sent
  (two GitHub API requests, status 1).
- One run on the block ending 2026-09-25 06:00: one new offer, one CodexBar
  read of OpenRouter's credit by backfire, and one Jev judgment through
  backfire ("qualifies", 0.98); status 0 without `--notify`. Two GitHub API
  requests and two raw-file requests.
- Finding those blocks: one GitHub API request and 30 raw-file requests.
- Model choice: three `jev_decide` calls through backfire (one repeated
  only to read its full output), each with one CodexBar read of
  OpenRouter's credit, and CodexBar usage reads for Codex (two), Claude
  (two) and OpenRouter (one).

## Document judgment step

`npm run doc-regions:prepare -- --base develop --max-evidence-chars 40000`
at `develop` `0e8e177` produced 238 units in three `jev_verify` requests,
sent through backfire on 2026-09-30: 4 OpenRouter calls, one of them lost
to an error in the coordinator's sending script and sent again. No unit
was new, so no `jev_classify` request was made.

- Three units in `docs/architecture.md` "Chat web agent and credit offers"
  were judged contradicted. Two were fixed: the offer search's paragraph
  now says it asks through backfire's shared provider order, and the "Not
  automated" line no longer says no provider accepts Jev calls. The third,
  the `packages/jev-ultrafast/` paragraph, stands: it describes only the
  web agent, which keeps `JEV_PROVIDER` and OpenRouter.
- 71 units were flagged for review. They lie outside this feature's diff
  (the constitution, `AGENTS.md` and unrelated sections), except the
  backfire guide's "Both plugins read one shipped configuration", which now
  also names the credit-offer search, and one new sentence in its
  introduction.
- The MemoryLint audit (`npm run doc-regions:audit`) is reported under
  "Verification".

## Verification

- `npm run doc-regions:audit` (MemoryLint 1.5.1) reported 19 warnings,
  all "boundary" findings that suggest moving rules from
  `.specify/memory/constitution.md` to `AGENTS.md`. None comes from this
  feature; they are reported to the user and the files are unchanged.

## Develop merge review

Fresh read-only reviewers, started through Orca in the coordinator's child
Run with models chosen by backfire's `jev_decide`, reviewed the branch at
`45c7cd5`:

- Code, tests, skill and the architecture section (written by Codex): a
  Claude Code reviewer (Sonnet, medium effort) approved with 0 blockers,
  0 majors and 2 minors: `credit-offers` imported `jev_judge_mcp` without
  declaring it, and one test's "no key shown" check could not fail. A Codex
  worker (`gpt-6-luna`, medium) fixed both; the fix also adds a test that
  runs the real provider factory with a missing key file.
- Records and document edits (written by the Claude Code coordinator): a
  Codex reviewer (`gpt-6-luna`, medium) requested changes with 1 minor: the
  exit statuses were described as depending on the notification. The spec
  and this report now say status 0 means at least one strong offer, with or
  without `--notify`.

## Size

Own code in `packages/credit-offers/src`: 28 lines added, 21 removed
(+7 net). The whole change against `develop` is far below the 1,000-line
split threshold.

## Handoff

- 2026-09-30: a computer restart ended the first implementation worker
  (Codex `gpt-6-luna`, high) before it committed; a second worker with the
  same choice fixed the lint findings and reviewed the diff. The shared git
  hooks moved to lefthook (CHE-44) during the work, so the implementation
  was committed in `b89c72f` after `develop` was merged (`a50cc59`) and
  the setup script had run.
