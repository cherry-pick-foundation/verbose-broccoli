# Implementation Plan: Backfire for Education Work

**Branch**: `feature/backfire-education` | **Date**: 2026-09-28 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/011-backfire-education/spec.md`,
with the user's answers of 2026-09-28.

## Summary

The one backfire package in `packages/backfire/` builds a backfire server per
plugin. `deno task backfire:build -- <plugin> <output>` takes `code` or
`work`. The code build is feature 005's build: the shared core
`src/backfire/` and the development profile. The work build adds the new
package `src/backfire_education/`, which holds the pseudonymization module and
the education profile, and ships that profile as the build's
`backfire/src/backfire/config.toml`. A top-level `pseudonymize = true` in that
file makes the shared judge send every judgment through the pseudonymization
module. The module replaces roster names, derived given names, guardian names,
schools, phone numbers and email addresses in the state and questions with
stable pseudonyms from a local keyed mapping table. It then restores question
keys, option labels and level descriptions in the answers. The work plugin
declares the same `backfire serve-mcp` server and a vendored copy of the
backfire skill with education guidance. Decisions and evidence are in
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14.4 in `packages/backfire/`, as feature 005
pins it; Deno 2.9.6 for repository tasks and the plugin checks.

**Primary Dependencies**: feature 005's pinned set, plus `phonenumbers` 9.0.40
(Apache-2.0) as the optional extra `education`, installed only in the work
build and in the development environment. Standard library for roster
reading (`csv`), detection (`re`), the mapping table (`hmac`, `hashlib`,
`secrets`, `json`, `fcntl`) and replacement.

**Storage**: Files only. Configuration:
`$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml` (roster path) and
`education.env` (the education profile's credential). Data:
`$XDG_DATA_HOME/verbose-broccoli/backfire/pseudonyms.json` (mode `0600`, at
most 1 MiB) with its lock file. The roster is the operator's file, read in
place. Records stay as in feature 005.

**Testing**: Offline pytest in `packages/backfire/tests/`, run by `deno task
test:backfire`: unit tests of detection, derivation, the table and restoration,
and end-to-end tests of a built work plugin's server against feature 005's
scripted OpenAI-compatible provider, which records every request. Deno tests
for the plugin layout (`scripts/plugin_skills_test.ts`). Live, on demand with
the user's go-ahead: the client check and the education measurement.

**Target Platform**: The operator's Linux x86_64 host; Codex CLI and Claude
Code opened in Orca, as in feature 005.

**Project Type**: The implementation package `packages/backfire/` (a Python src
layout), distributed into the code and work plugins by the build.

**Performance Goals**: None beyond feature 005's. Pseudonymization reads a
small roster and table per judgment and runs off the event loop.

**Constraints**: Fail closed (FR-011): no provider request when the roster,
the table or the shipped module is unusable, or when replacement would merge
keys or labels. No names, pseudonyms or table entries in records, logs or
errors. The table stays within 1 MiB. The code build's behavior and tests do
not change (FR-002).

**Scale/Scope**: One operator; a roster of tens of students; eleven tools in
two builds.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

Checked against constitution **0.22.0** on 2026-09-28, and re-checked
against **1.0.0** the same day after `develop` was merged in. Version 1.0.0
only deletes rules, among them principle VIII and principle III's sentences on
a second student register and relationship inference.

| Principle | Design alignment |
| --- | --- |
| I. Proven dependencies and storage | `phonenumbers` 9.0.40 is pinned in `pyproject.toml` and `uv.lock`, and its use was proved in a scratch environment on CPython 3.14.4 (research.md). Presidio was evaluated and not adopted. No relational storage. |
| II. Working capabilities and data | Nothing planned is counted as implemented; the client check and the measurement stay open until they run. |
| III. Sources and data ownership | No search normalization becomes an identity key; identifiers are normalized only to derive stable pseudonyms. The roster is read in place and never copied, and the mapping table holds keyed digests and pseudonyms, no names or contact details. Sending pseudonymized learning content to the selected provider is the user's decision (CHE-9). |
| IV. Capabilities from current needs | Specified from the user's current needs. The roster format is not the legacy files' format, and no code depends on earlier projects. No user data is imported. |
| V. Observable acceptance | Synthetic rosters and records only; positive, negative and boundary cases; failures at each fail-closed point; interrupted table writes; concurrent sessions; readback of the recorded provider requests. |
| VI. Wiki layers and storage | Not Wiki content. Configuration and durable data use the `verbose-broccoli` XDG roots; the operator's roster keeps its own location. No private user data enters the repository. |
| VII. One owner and minimum implementation | Standard library and `phonenumbers` do the work; local code is glue and the domain rules (given names, pseudonym kinds). The table has a 1 MiB budget, all-or-nothing writes, and a lock. The education profile repeats the development profile's values, by the user's choice of a separate table (research.md). |
| IX. Three plugin packages | New code lives in `packages/backfire/src/backfire_education/`. The work plugin gains an MCP declaration and a skill for a selected capability and works without the code plugin. Chat is unchanged. |
| Product and data boundaries | No real student data in fixtures, tests, reports or Linear; credentials stay in the operator's files. |
| Development workflow | git flow feature branch into `develop` with the merge review and review-record commit; `Spec-Kit-Task` trailers. Installing into saved client settings and billed runs need the user's approval. |

Post-design re-check (after Phase 1): the contracts keep every row above. The
only core changes are the judge's pseudonymization call, the shipped-only
`pseudonymize` key, one error type (`pseudonym_conflict`) and the build table.

## Project Structure

### Documentation (this feature)

```text
specs/011-backfire-education/
├── spec.md
├── plan.md                 # this file
├── research.md             # decisions, evidence and, later, results
├── data-model.md           # entities and rules
├── quickstart.md           # validation guide
├── contracts/
│   ├── build.md            # per-plugin build interface
│   ├── pseudonymization.md # roster, detection, pseudonyms, table, restore, failures
│   ├── configuration.md    # work build's shipped and operator files
│   └── measurement.md      # education set format and run protocol
├── checklists/requirements.md
└── tasks.md                # created by speckit-tasks
```

### Source Code (repository root)

```text
packages/backfire/
├── pyproject.toml                 # extra "education" = phonenumbers 9.0.40; packages.find adds backfire_education
├── uv.lock                        # relocked with the extra
└── src/
    ├── backfire/                  # shared core, as in feature 005
    │   ├── judge.py               # calls pseudonymization when the shipped config asks for it
    │   ├── config.py              # accepts pseudonymize only in the shipped file
    │   ├── failures.py            # adds pseudonym_conflict
    │   └── config.toml            # development profile (code build)
    ├── backfire_education/        # work only
    │   ├── __init__.py
    │   ├── pseudonymize.py        # detection, replacement, restoration, the judge hook
    │   ├── roster.py              # education.toml, the roster CSV, given names
    │   ├── table.py               # mapping table: key, counters, lock, budget
    │   └── config.toml            # education profile, pseudonymize = true
    └── backfire_tools/
        ├── build.py               # per-plugin table
        └── acceptance/
            └── measure_education.py   # two-arm measurement runner
└── tests/                         # new and updated pytest suites

plugins/work/
├── mcp.json                       # declares backfire, same command as code
├── plugin.json                    # description mentions Backfire
└── skills/backfire/               # vendored skill copy with education guidance
    ├── SKILL.md
    ├── reference/tools.md         # identical to the code plugin's copy
    ├── references/verbose-broccoli.md
    ├── LICENSE
    └── upstream.json

scripts/backfire/fixtures/
├── education-v1.jsonl             # synthetic education measurement set
└── education-roster-v1.csv        # its synthetic roster

scripts/plugin_skills_test.ts      # work declares backfire; shared skill files stay identical
deno.json                          # backfire:install adds --extra education
docs/backfire.md                   # build per plugin; work build setup, data sent, limits
docs/architecture.md               # per-plugin build
docs/reference/                    # regenerated
licenses/THIRD_PARTY_NOTICES.md    # phonenumbers; the skill's second copy
specs/005-jev-decision-backend/spec.md   # FR-015 and the assumption marked superseded
```

**Structure Decision**: Constitution IX keeps reusable implementation under
`packages/<name>/src/`. The work-only code is a sibling package of the core
inside the same Python project, so one `pyproject.toml` and one `uv.lock` serve
both builds, and the build copies only the packages a plugin needs
([contracts/build.md](contracts/build.md)). The work plugin carries its own
copy of the backfire skill because plugins may not link to each other's files
(`scripts/plugin_skills_test.ts` refuses links); a test keeps the two copies'
shared files identical.

## Implementation Order and Gates

1. Build per plugin, with the code build's output checked against feature
   005's contract before anything else changes.
2. Pseudonymization module with its unit tests, then the judge hook and the
   shipped-only key.
3. End-to-end tests of the built work server with the recording provider:
   SC-001 to SC-004.
4. Work plugin files, documentation, notices and 005's superseded notes.
5. With the user's go-ahead: the client check (SC-006) and the education
   measurement (SC-007), whose set is written and committed before the first
   run.

## Complexity Tracking

No constitution violations need justification.
