# Implementation Plan: Offer Search Through Backfire

**Branch**: `feature/offer-search-backfire` | **Date**: 2026-09-30 |
**Spec**: [spec.md](spec.md) | **Linear issue**: CHE-49

## Summary

`credit_offers.main` keeps its tracker search, filters, output and exit
statuses. Only the judgment step changes: instead of posting the request
through `jev_ultrafast.model.request_jev`, it builds PyModel choice
questions and awaits `evaluate` on the provider that backfire's
`provider_factory()` returns, which applies the shared order, the CodexBar
credit check and the switch on insufficient balance. Answers are checked
with PyModel's `validate_choice`.

## Technical Context

**Language/Version**: Python 3.14, uv 0.11.32 or later.

**Primary Dependencies**: the `backfire` workspace package, which brings
jev-judge-mcp 0.6.0 (PyModel); httpx stays for the tracker. The
`jev-ultrafast` dependency is removed from `credit-offers`. No new
third-party dependency; `uv.lock` changes only in `credit-offers`'s
dependency list.

**Testing**: pytest in `packages/credit-offers/tests`, run by
`npm run test:credit-offers` and `npm run verify`. Backfire's provider is a
fake object patched in place of `provider_factory`; no test reads key files
or makes a network call.

## Constitution Check

- **VII, reuse order**: backfire's provider factory and PyModel's question
  type and `validate_choice` are reused as they are; the new code is the
  call and its error mapping. No provider code is added. Pass.
- **IX, package layout**: `credit-offers` uses the shared `backfire`
  package under `packages/`; the web agent keeps `jev-ultrafast`. Pass.
- **Product and Data Boundaries**: offers are public tracker data; no key
  is printed or committed; education mode is not used. Pass.

## Design

### Judgment

```python
questions = {
    o["slug"]: ChoiceQuestion(
        instructions={"offer": o["slug"], "task": "Judge this."},
        criteria=CRITERIA,
    )
    for o in offers
}
async def judge(state, questions):
    provider = providers.provider_factory()(None)  # settings are unused
    try:
        return await provider.evaluate(state, questions, DEFAULT_MODEL, None)
    finally:
        await provider.aclose()

result = asyncio.run(judge(state, questions))
answers = {slug: validate_choice(result.answers[slug], ("qualifies", "excluded"))}
```

- `DEFAULT_MODEL` is PyModel's `jev-latest` (`jev_judge_mcp.providers.resolver`).
- A `timeout` of `None` leaves each attempt to the profile's retry policy.
- `validate_choice` returns `None` for an invalid answer; the search treats
  that as a failure (status 3). The printed line uses the returned
  `ChoiceAnswer`'s `choice` and `probabilities`.
- PyModel's `ProviderError`, whose subclasses cover configuration,
  connection and timeout failures and which carries backfire's
  `no_credit`, joins the search's error tuple, so these end with status 3.
  Backfire redacts provider keys; the search keeps redacting the GitHub
  token.

### Run command

The develop session approved dropping the provider key files and
`JEV_PROVIDER` (spec, Clarifications). The skill's command becomes:

```sh
providers="${XDG_CONFIG_HOME:-$HOME/.config}/verbose-broccoli/providers"
uv run --frozen --offline --no-sync --env-file "$providers/github.env" \
  --package credit-offers credit-offers --notify
```

The automation's precheck is the same command with `$HOME/.local/bin/uv`
and the status mapping `s=$?; [ "$s" -le 1 ] && exit 1; exit "$s"`. It is
sent to the develop session for approval after the finish.

### Files and own-code estimate

| File | Change | Own lines (estimate) |
| --- | --- | --- |
| `packages/credit-offers/src/credit_offers/__init__.py` | judgment through backfire | +15 / -12 |
| `packages/credit-offers/pyproject.toml`, `uv.lock` | `backfire` instead of `jev-ultrafast` | +2 / -2 |
| `packages/credit-offers/tests/test_credit_offers.py` | fake backfire provider; failure cases | about +40 / -20 |
| `plugins/chat/skills/credit-offers/SKILL.md`, `docs/architecture.md` | run command, keys, limits | about +15 / -20 |

### Live check

One run of the search with `--end` on a past block that has at least one
candidate, without `--notify`: one CodexBar read of OpenRouter's credit and
one Jev judgment through backfire. The report counts the calls.

### Parallel work

CHE-44 (tooling), CHE-47, CHE-51, CHE-52 and CHE-57 run at the same time;
CHE-51 changes backfire's profiles but not its library interface. Whoever
finishes later merges `develop` and keeps every change.

## Workers

- Implementation: one worker for T002-T004.
- Review before the develop merge: one fresh reviewer from the other
  provider.

Agents, models and efforts come from the code plugin's `model-choice`
skill and are recorded in `tasks.md`.
