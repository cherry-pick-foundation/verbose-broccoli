# Report: Offer Search Through Backfire

**Linear issue**: CHE-49 | **Branch**: `feature/offer-search-backfire`

## Outcome

The credit-offer search in `packages/credit-offers` sends its one judgment
per run through backfire's library (`backfire.providers.provider_factory`),
so it follows backfire's shared provider order, the CodexBar credit check
and the switch on insufficient balance. The state, the choice questions,
the printed lines and the exit statuses (0 notified, 1 nothing new, 2 bad
arguments, 3 failed request) are unchanged. Answers are checked with
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
