# Implementation Plan: Jev Ultrafast web agent and API credit offer search

**Branch**: `feature/chat-jev-ultrafast` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/021-chat-jev-ultrafast/spec.md`

## Summary

Copy Jev Ultrafast at a fixed upstream revision into a new uv workspace
package and patch two places: `model.py` sends Jev calls to a provider chosen
from a configuration file (TypeSafe as upstream, or Vercel AI Gateway in
jev-mcp 0.9.0's format), and `browser.py` opens, attaches to and closes its
own tab in Orca's built-in browser unless Chrome is selected. A second small
package, `credit-offers`, finds offers that entered the freetokens tracker's
index during the latest 6-hour block, asks Jev once whether each costs nothing
and states no time limit, and sends a desktop notification for strong ones.
The chat plugin gets two skills that document both. An Orca automation runs
the search every 6 hours after the user approves it. The research, the offer
history and the interval calculation are in [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (the repository's `.python-version` is
3.14.4; upstream requires 3.12 or later)

**Primary Dependencies**: Jev Ultrafast (copied, MIT);
`browser-harness==0.1.13` (MIT) and `httpx[http2]` (upstream's
dependencies); the standard library's `tomllib`, `json`, `subprocess` and
`datetime`; the host's `orca` CLI and `notify-send`

**Storage**: None. Credentials in the shared provider folder
`~/.config/verbose-broccoli/providers/`, one `0600` file per provider,
outside the repository (user decision, 2026-09-30; it replaced the chat
plugin's own `jev.env`)

**Testing**: pytest with `httpx.MockTransport` and stubbed subprocess and CDP
calls; no paid calls in tests

**Target Platform**: The user's Ubuntu GNOME laptop with Orca 1.4.216

**Project Type**: Two libraries in the root uv workspace, one with a console
script; two plugin skills

**Performance Goals**: A run with no new offer ends in under 30 seconds with
no Jev call (SC-002)

**Constraints**: At most one Jev call per run; no writes; keys never printed;
GitHub's API limit of 60 unauthenticated requests an hour, or 5,000 with
the optional `GITHUB_TOKEN` (a run uses two);
no own-code line limit (the user's 300-line limit was replaced by a splitting
review for changes of 1,000 lines or more, CHE-44)

**Scale/Scope**: 4 runs a day; about 4 new tracker offers a day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. Proven dependencies | uv lock pins `browser-harness`, `httpx` and their tree; no new storage | Pass |
| II. Working capabilities | The live provider check waits for a key and is listed as not performed | Pass, recorded |
| IV. Current needs | No earlier project is a source; upstream Jev Ultrafast and jev-mcp are third-party sources | Pass |
| V. Observable acceptance | Positive, negative and boundary tests; live checks on own Orca tabs; unperformed checks recorded | Pass |
| VI. Storage | Nothing is written; the credential file is configuration under the XDG config root | Pass |
| VII. Minimum implementation | Upstream copied with a recorded patch; local code limited to the search and glue; vendor details in configuration | Pass |
| IX. Three plugin packages | Skills added to `plugins/chat`; implementation in `packages/<name>/src/`; both packages join the uv workspace because they hold Python code | Needs the amendment below |
| Product boundaries | No private data or keys in fixtures or records | Pass |
| Workflow and git flow | Spec Kit flow, Codex workers, `npm run verify`, merge review, `git flow feature finish` | Pass |

**Amendment**: Principle IX says "The chat package has no skills yet and no
MCP declaration or scripts". This feature changes it to name the chat
package's two skills, by the user's decision in CHE-41. The commit is `feat`,
so the version goes from 2.2.0 to 2.3.0, and Governance records the decision.

## Project Structure

### Documentation (this feature)

```text
specs/021-chat-jev-ultrafast/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── offer-history.tsv
├── contracts/
│   ├── providers.md
│   ├── orca-browser.md
│   └── credit-offers-cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
packages/jev-ultrafast/
├── LICENSE                     # upstream, unchanged
├── UPSTREAM.md                 # revision, original hashes, differences
├── pyproject.toml              # upstream's, adapted to the workspace
├── src/jev_ultrafast/          # upstream package; model.py and browser.py patched
│   └── providers.toml          # new: provider details
├── examples/run.py             # upstream, unchanged
├── scripts/check_guards.py     # upstream, unchanged
└── tests/
    ├── test_agent.py           # upstream, unchanged
    ├── test_providers.py       # new
    └── test_orca_browser.py    # new
packages/credit-offers/
├── pyproject.toml
├── src/credit_offers/
│   ├── __init__.py             # search, judgment, notification, CLI
│   └── tracker.toml            # tracker details
└── tests/test_credit_offers.py
plugins/chat/
├── plugin.json                 # description updated
└── skills/
    ├── web-agent/SKILL.md
    └── credit-offers/SKILL.md
```

Repository integration: `package.json` scripts `test:jev-ultrafast` and
`test:credit-offers`, their `turbo.json` tasks, `ruff.toml` source roots,
linter and formatter exclusions for the copied upstream files,
`licenses/THIRD_PARTY_NOTICES.md`, `docs/architecture.md`, the regenerated
`docs/reference/`, the constitution, and `uv.lock`.

**Structure Decision**: Two packages under `packages/`, because constitution
IX puts implementation there and keeps the upstream copy apart from local
code; the skills under `plugins/chat/skills/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| A patched copy of upstream code | Jev Ultrafast is not on PyPI, and uv cannot patch a Git dependency | A run-time monkeypatch cannot remove `choose()`'s direct read of `TYPESAFE_API_KEY` and hides the difference |
| A second new package (`credit-offers`) | Local search code must not mix with the upstream copy, and it needs its own tests | Putting it in the upstream copy would blur the recorded difference |
