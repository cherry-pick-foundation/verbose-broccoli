# Tasks: Reset Credits in Model Choice

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: The rule (User Story 1)

- [x] T001 In `references/model-choice.md`, "Usage limits": name reset credits
  as evidence with their source fields, give the identity-free read, say who
  spends them, and add them to the evidence given to `jev_decide`; add the
  same to the CodexBar sentence in `docs/architecture.md` (FR-001 to FR-003).
  - By main (Claude Code). The jq read prints `availableCount` and, for each
    available credit, `title`, `reset_type`, `status`, `granted_at` and
    `expires_at`; CodexBar 0.69.0's credits carry no ID or identity.
- [x] T002 Run one model choice for a sample task and record its evidence and
  answer (SC-001).
  - The sample is this feature's develop merge reviewer (difficulty easy, own
    estimate), chosen with one `jev_decide` through `serve-mcp --profile
    openrouter`; the answer named provider `openrouter`, model
    `typesafe/jev-1.13`. The evidence gave usage on 2026-10-01 at 08:05 UTC:
    Codex weekly 67% used with 2 available reset credits ("Full reset",
    `codex_rate_limits`) expiring 2026-10-22 and 2026-10-29; Copilot Chat
    8.7%; Grok weekly 0%; Cursor monthly 0% (free plan, `auto` only);
    Antigravity unknown; every provider but Codex "none reported". Claude Code
    implemented the feature, so the other-provider rule (`AGENTS.md`,
    "Review") kept it out of the candidates.
  - Agent: Cursor (probability 0.39, confidence 0.30; Copilot 0.28, Grok
    0.23, Codex 0.04, Antigravity 0.00). The credits did not lift Codex: the
    judgment weighed its 67% window and the free quotas of the others.

## Phase 2: Finish

- [ ] T003 Merge `develop`, run `npm run verify`, pass the develop merge
  review by a provider other than Claude Code, commit the review record and
  finish with `git flow feature finish model-choice-reset-credits`.
