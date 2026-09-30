# Tasks: Offer Search Through Backfire

**Input**: [spec.md](spec.md) and [plan.md](plan.md) in
`specs/029-offer-search-backfire/`

**Tests**: required; every exit status on the backfire path has a pytest
case in `packages/credit-offers/tests/`.

**Format**: `[ID] [P?] [Story] Description`; `[P]` tasks touch different
files and can run in parallel.

## Phase 1: Setup

- [X] T001 Write spec, plan and tasks; ask the develop session about the
  precheck key files (answered: only `github.env`). Coordinator.

## Phase 2: User Stories 1-2, the judgment through backfire (P1)

- [ ] T002 [US1] [US2] In `packages/credit-offers/pyproject.toml`, replace
  the `jev-ultrafast` dependency and its workspace source with `backfire`;
  refresh `uv.lock` offline. In
  `packages/credit-offers/src/credit_offers/__init__.py`, send the judgment
  as plan.md "Judgment" shows, validate with PyModel's `validate_choice`,
  add PyModel's `ProviderError` to the error tuple, and drop the
  `TYPESAFE_MODEL` lookup.
- [ ] T003 [US1] [US2] Update `packages/credit-offers/tests/test_credit_offers.py`:
  patch backfire's `provider_factory` with a fake provider that records
  each `evaluate` call and is closed once; keep the existing cases on the
  new path; add cases for a `ProviderError` from configuration, no credit
  and a timeout (status 3, no key printed), an invalid answer (status 3),
  and one judgment with the unchanged state and questions (status 0).

## Phase 3: User Story 3, operator documents (P2)

- [ ] T004 [P] [US3] Update `plugins/chat/skills/credit-offers/SKILL.md`
  (Run command without `JEV_PROVIDER` and provider key files; backfire
  reads its keys and follows its order; Limits) and
  `docs/architecture.md` "Chat web agent and credit offers" to match.

## Phase 4: Finish

- [ ] T005 Live run on a past block with a candidate; record the call
  count in `report.md`. Coordinator.
- [ ] T006 Review by a fresh reviewer from the other provider; resolve
  findings. Coordinator.
- [ ] T007 Merge `develop`, `npm run verify`, review record, `git flow
  feature finish`; send the precheck for approval, update the automation,
  close CHE-49. Coordinator.

## Workers

- T002-T004: Codex `gpt-6-luna`, effort high, chosen by backfire's
  `jev_decide` (probability 0.80, confidence 0.78) over Codex `gpt-6-luna`
  xhigh and `gpt-6-sol` high, Claude Code Sonnet high and Opus medium, and
  OMP GLM 5.3 Flash.
