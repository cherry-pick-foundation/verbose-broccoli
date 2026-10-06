# Data Model: Clean Architecture Tool Collection

The "data" of this feature is the repository's structure. Each entity below
names what it is, where it lives, its rules, and how a check can tell whether
an instance is valid. Citations use the IDs in [research.md](research.md).

## Component package

One capability's code: a folder `packages/<name>/` with its own manifest.

| Field | Rule | Source |
| --- | --- | --- |
| `name` | kebab-case folder; the Python import name is the snake_case form; the npm name is the folder name | U-2026-09-30a, R-REPO-06, R-REPO-01 |
| manifest | `pyproject.toml` (uv workspace member) or `package.json` (npm workspace), never both unless the package really has code in both languages | R-REPO-06, R-REPO-09, constitution IX |
| source | `src/<import_name>/` for Python, `src/` for TypeScript, holding `domain/`, `application/`, `adapters/`, `entrypoints/` and one `bootstrap` module; a ring without code is not created | R-CA-04, R-REPO-08, U-2026-10-06c |
| public entry | Python: the modules the package lists as published in its `AGENTS.md`; TypeScript: the `exports` map of `package.json`; command-line entry points in `[project.scripts]` or `bin` | R-CA-03, R-REPO-10, R-REPO-07 |
| `AGENTS.md` | the package's rules for agents | R-REPO-12 |
| `README.md` | what the package holds, its entry points, how to run its tests | R-GG-10 |
| tests | `tests/unit/`, `tests/integration/`, `tests/e2e/` by scope; unit tests reach the package through its public entry where possible | R-CA-04, R-GG-12, R-GG-13 |

Valid when the dependency checks pass (see [dependency rules](contracts/dependency-rules.md)),
its tests pass, and nothing outside the package imports an unpublished module.

## Ring

A folder inside a component's source. Dependencies point inward only.

| Ring | May import | Must not | Source |
| --- | --- | --- | --- |
| `domain/` | the standard library's pure modules and pure third-party libraries | input or output of any kind: files, network, processes, clock, environment | R-CA-01, R-GG-12 |
| `application/` | `domain/`; its own port definitions | adapters, entry points, bootstrap, input or output | R-CA-01, R-CA-02, R-ARCH-04 |
| `adapters/` | `application/`, `domain/`, third-party I/O libraries | entry points, bootstrap; another component's unpublished modules | R-CA-03 (Périphérique), R-ARCH-04 |
| `entrypoints/` | `bootstrap`, `adapters/`, `application/`, `domain/`, the command-line or MCP library | being imported by any other ring; building use cases itself (it calls `bootstrap`) | R-CA-04 ("Project tree"), R-ARCH-04 (driving adapters), R-CP-17 |
| `bootstrap` | everything in its package; settings through the [settings contract](contracts/settings.md) | being imported by `domain/`, `application/` or `adapters/` | R-CA-04 ("bootstrap … only place … config is imported") |

## Port

An interface owned by `application/` for one purposeful conversation with the
outside that a use case starts (R-CA-02, R-ARCH-04). Cockburn also calls the
user-side conversation a (primary) port; here that side is the entry point's
call into a use case, which needs no interface of its own (R-ARCH-04
"Without a Command/Query Bus"). Cosmic Python keeps ports in the same file as
their adapters (R-CP-07); this repository keeps them in `application/` so the
checkers can tell them apart. Exists only when a use case must reach outside its package
while it runs; data that can be gathered first is passed in as plain values
(FR-008, R-CA-01). Named for its purpose, never with an `I` prefix (R-GG-17).
Each port has at least one real adapter; a fake exists only where the real
adapter is slow, paid or nondeterministic, and one shared test runs the same
cases against the real adapter and the fake (R-GG-14, R-EX-12). Fakes stand
in for the package's own ports, never for a third-party library's interface
(R-CP-09 "don't mock what you don't own").

## Adapter

Code that implements a port (driven, in `adapters/`) or calls the
application (driving, in `entrypoints/`: a command-line entry point or an MCP
server). Named for its technology (R-GG-17). Driving adapters keep their
existing input and output contract (the CLI contract in
`docs/architecture.md`). An MCP tool function closes over a use case built by
`bootstrap` and returns a transport model defined in `entrypoints/`, because
a tool's return type becomes its public output schema (R-FMCP-02); refusals
and missing settings come back as tool execution errors the model can read
(R-ARCH-14).

## Composition root

The one `bootstrap` module per package that reads settings and wires adapters
to use cases; "composition root" in the specification means this module, and
entry points are the driving adapters that call it (R-CA-02 sample code; R-CA-04 bootstrap). Its function takes
each adapter as an optional argument with the production default, so tests
call the same function with fakes (R-CP-17, R-EX-11, R-EX-12). A stdio MCP
server runs it at the start of every client session (R-FMCP-08). Reads settings only through
the [settings contract](contracts/settings.md). Tests reuse it with
replacement adapters instead of building their own object graph (R-GG-14).

## Settings

Values a composition root reads.

| Kind | Location | On absence |
| --- | --- | --- |
| optional setting | `$XDG_CONFIG_HOME/verbose-broccoli/config.toml` (existing file) under the package's table | built-in safe default (R-OS-03, R-OS-08) |
| credential | `$XDG_CONFIG_HOME/verbose-broccoli/providers/<provider>.env` (existing shared folder) | only the capability needing it fails, naming the file and variable (FR-010) |
| state | `$XDG_STATE_HOME/verbose-broccoli/…` | created with mode 0700 when first written (R-OS-01) |
| cache | `$XDG_CACHE_HOME/verbose-broccoli/…` | rebuilt; deleting it loses nothing (R-OS-02) |

Relative XDG values are ignored and defaults used (R-OS-01).

## Skill

An Agent Skills folder: `SKILL.md` whose `name` equals the folder name, plus
optional `scripts/`, `references/` and `assets/` (R-UP-01). Exists once in
the repository (FR-002), at `skills/<area>/<name>/` (U-2026-10-06h), except
skills inside an upstream bundle under `tools/` (plan Decision 10). An
upstream skill keeps its upstream name and its recorded provenance
(U-2026-10-04a). A skill that must work when copied elsewhere keeps its code
in its own `scripts/` folder (plan Decision 9). See
[delivery](contracts/delivery.md).

## Skill area

`code`, `work` or `chat`: the groups that were plugins, at `skills/<area>/`.
Each area keeps the rules its plugin's `AGENTS.md` held, in
`skills/<area>/AGENTS.md`; a skill points to them as `../AGENTS.md`. Wikis
keep their names (constitution VI).

## MCP server

A driving adapter that needs a running process, a login or a filter in front
of it (U-2026-10-06b). Registered once per agent in the user's own settings
(U-2026-10-06g). Every judgment server runs behind the education privacy
gate (FR-004, FR-021).

## Judgment backend

Who answers a judgment: Jev (`typesafe/jev-1.13`) on OpenRouter or GLM 5.3
Flash on Hive through a System One-compatible endpoint (U-2026-10-06d,
R-CA-06). Chosen by a setting; the GLM request timeout is a setting of at
least 300 seconds (FR-020). See the [judgment contract](contracts/judgment.md).

## Hold

A recorded reason code cannot move yet; the plan's Holds table lists H1 to
H4.

| Field | Meaning |
| --- | --- |
| paths | the code held |
| reason | open branch, replacement trial, or bug |
| release | the observable event that releases it (a merge into `develop`, a trial result the user accepts, a fix merged) |
| owner | who reports the release (the develop orchestrator for merges and bugs; the user for trials) |

State: `held` → `released` → `moved`. Only a released hold's code may move
(FR-016).

## Slice

One reviewed change finished into `develop` (FR-014).

| Field | Rule |
| --- | --- |
| scope | one story's part, or one component's move; refactoring kept apart from behavior change (R-GG-01) |
| size | measured with the code-size script before and after; reported, not capped (FR-017) |
| review | a fresh reviewer from a provider other than the implementer's, given only scope and requirements |
| finish | `git flow feature finish` from the `develop` worktree after a review record; one finish at a time |

State: `planned` → `building` → `reviewed` → `finished`.
