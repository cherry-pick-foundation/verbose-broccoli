# Feature Specification: Backfire Rebuilt on jev-judge-mcp

**Feature Branch**: `feature/backfire-rebuild`

**Created**: 2026-09-29

**Status**: Draft (redesigned 2026-09-30)

**Linear issue**: CHE-39

**Input**: Linear issue CHE-39, "Rebuild backfire on FastMCP from PyModel's
jev-judge-mcp", the develop session's task brief of 2026-09-29, and the
user's decisions of 2026-09-29 and 2026-09-30 recorded under
Clarifications. Backfire, the judgment server in `packages/backfire`, is
rebuilt on PyModel's [jev-judge-mcp](https://github.com/PyModel/jev-judge-mcp)
0.6.0 (MIT), a Python implementation of jkudish/jev-mcp, replacing
backfire's own Python port of jev-mcp 0.9.0.

The first design (2026-09-29) vendored a copy of PyModel's code and kept
backfire's tool names, boundary, records and readiness check. On
2026-09-30 the user replaced it: backfire depends on the published
`jev-judge-mcp==0.6.0` package and plugs into PyModel only through its own
extension points, without editing PyModel; backfire keeps only what it
needs to function; what cannot plug in becomes a prepared contribution to
PyModel. Backfire's own code targets about 300 to 500 lines, not counting
tests or the existing pseudonymization module, under the user's new rule
that a feature asks before adding more than 300 net lines of own code.

The read-only evaluation of jev-judge-mcp of 2026-09-29 is copied into this
feature's `research.md`.

## Clarifications

### Session 2026-09-29

- Q: Which regex engine should `backfire_extract` use? PyModel runs each
  pattern with Python's `re` in a pool of pre-started worker processes, and
  its 1-second wall-clock limit also counts queueing and worker restarts
  (the CHE-37 problem). → A: Replace PyModel's worker pool with the `regex`
  library's own timeout (PyPI `regex`, pinned like the other dependencies),
  run in a thread with `concurrent=True` so the event loop stays free, with
  the 1-second limit counted by `regex`'s timeout, which measures process
  CPU time through C `clock()`. Record the change from PyModel, including
  that some patterns jev-mcp stops, such as `(a+)+$`, finish at once. Tests
  use a pattern that still runs away under `regex`, for example `(a|aa)+$`
  on 60 `a` characters followed by `b`, which stopped at 1.00 s of CPU in
  the user's check. Keep the result fields, caps and error text. (User's
  answer, relayed by the develop session.)

### Session 2026-09-30

- Q: The user asked to add Vercel AI Gateway as a provider, next to
  PyModel's TypeSafe, OpenRouter, Cloudflare and compatible providers, based
  on jev-mcp 0.9.0's own Vercel code (which comes from jkudish's
  `jev-agent-tools` 0.1.2, MIT). Should PyModel's other Jev providers also
  become selectable, or only Vercel? → A: Backfire profiles gain a second
  kind, a Jev profile that names its provider (`typesafe`, `openrouter`,
  `cloudflare`, `vercel` or `compatible`), served by PyModel's providers
  plus the ported Vercel provider, credited. Jev profiles use PyModel's
  retries; the shipped default stays DeepSeek on Hive, and a Jev profile is
  used only when the operator selects it. No Vercel or TypeSafe key exists
  on the laptop: a Vercel key would go in a new `0600` credential file in
  `~/.config/verbose-broccoli/backfire/` that the user creates, so the
  Vercel path is tested against a local stub, the expected file and
  variable are documented, and no live Jev check runs unless a key is
  added.
- Redesign (user's decision, relayed by the develop session): stop copying
  PyModel and use it as a library. Depend on the published
  `jev-judge-mcp==0.6.0` (pinned, MIT) and remove the vendored files and
  their tests. Build backfire from PyModel's own plug-in points without
  editing PyModel: an entry point of about 20 lines that constructs
  `JevMCPServer(toolset=Toolset(Runtime(settings, provider_factory=...,
  regex_executor=...), TOOLS + [noul]))` and runs PyModel's `serve()`; a
  provider factory for Hive profiles (system-one-adapter with
  pseudonymization) and for Jev profiles (PyModel's `resolve_provider` plus
  the Vercel provider); a regex executor on the `regex` library (CHE-37);
  and the Noul tool added to the list. Accept PyModel's `jev_` tool names
  and behaviour, including its own input limits. What cannot plug in (the
  quadratic duplicate-ID handling behind CHE-38, the stdin line limit, the
  missing `exclusiveMinimum` keyword) becomes a prepared upstream
  contribution to PyModel: the patch and the pull-request text are written,
  nothing is opened on GitHub.
- Conflicts with the 2026-09-29 decisions, resolved by the user: the server
  reports PyModel's name `jev-mcp` under the plugin key `backfire` and
  serves PyModel's packaged skill resources; tools use PyModel's `jev_`
  names, with the backfire skills, documents and the doc-regions and
  wiki-consistency request builders updated; CHE-38 stays open until PyModel
  releases the contribution, and the `jev_verify` load case is marked as a
  known failure that names CHE-38; backfire's call boundary goes (the
  10 MiB message limit, the 118-second call deadline and per-call records).
- Keep only what backfire needs to function (user's decision): keep the
  entry point, the Hive provider with profiles and key file, the
  pseudonymization hook, Jev profiles and the Vercel provider, the regex
  executor and the Noul tool. Remove the acceptance tools and their
  fixtures, the judgment and per-call records, the readiness command, and
  the extra Hive checks (thinking evidence, reported model, cut-off output,
  refusal, special status codes, fixed error types); PyModel's answer
  validation and retries stand in for them. Keep the small `JudgmentError`
  class that the pseudonymization module and wiki-consistency use. Keep
  CHE-33's retry of a normal-looking reply without an answer, with its
  existing failing-then-passing test.
- Plugins (user's decision): run both plugins straight from the
  repository. Their `mcp.json` points at `packages/backfire`; `serve-mcp`
  gets an option that turns on the work plugin's education settings
  (pseudonymization and its profile); the wiki-consistency skill's commands
  point at `packages/`; the plugin build tool and its tests are removed.
  The held-out evaluation file outside the repository stays untouched.
- Vercel key (user's decision): a Vercel AI Gateway key now exists as
  `AI_GATEWAY_API_KEY` in `~/.config/verbose-broccoli/chat/jev.env` (mode
  `0600`), created for the chat plugin (CHE-41). Backfire's Vercel profile
  names that file as its key file instead of copying the key, and once the
  Vercel provider works, one live Jev judgment runs through it and its call
  count is reported. The key is never read into logs or output.
- Regex engine, revised (user's decision): the `regex` library has no other
  use in the repository, so it is dropped: no `regex` dependency, no custom
  regex executor and no copy of PyModel's candidate loop. `jev_extract`
  uses PyModel's own default regex executor (its warmed worker pool with
  Python's `re`) unchanged. This replaces the 2026-09-29 choice of the
  `regex` library. CHE-37's heavy-load reproduction is rerun against
  PyModel's executor: if simple patterns no longer time out falsely, the
  record says PyModel's warmed pool resolves CHE-37; if they still do, the
  smallest fix (for example counting only the worker's own CPU time) goes
  into the PyModel contribution, not into local code.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agents use PyModel's Jev tools through backfire (Priority: P1)

An agent in the code or work plugin starts backfire from the repository and
calls its judgment tools. It gets jev-judge-mcp 0.6.0's server and tools,
plus `jev_noul`. Each judgment goes to the model the selected backfire
profile names: DeepSeek on Hive by default, or a Jev provider when the
operator selects a Jev profile. The work plugin pseudonymizes education
data before it leaves the machine.

**Why this priority**: It is the purpose of the rebuild.

**Independent Test**: Start `backfire serve-mcp` as each plugin's
`mcp.json` does, with a local stub provider; list the tools and call each
with synthetic input.

**Acceptance Scenarios**:

1. **Given** a client that starts the server as the plugins' `mcp.json`
   does, **When** it initializes and lists tools, **Then** the server is
   PyModel's (it reports `jev-mcp`) and lists PyModel's eleven tools and
   `jev_noul`.
2. **Given** any PyModel tool and an input PyModel accepts, **When** the
   provider's answers are the same, **Then** the result equals what
   PyModel's own server returns, because the tool code is PyModel's,
   unchanged.
3. **Given** the shipped profile, **When** a tool asks a judgment, **Then**
   it goes to the profile's Hive endpoint and model through
   system-one-adapter, with the key from the profile's credential file.
4. **Given** a Jev profile that names `typesafe`, `openrouter`,
   `cloudflare` or `compatible`, **When** a tool asks a judgment, **Then**
   PyModel's own provider of that name sends it, configured from the
   profile and its credential file; PyModel's environment variables do not
   choose the provider.
5. **Given** a Jev profile that names `vercel`, **When** a tool asks a
   judgment, **Then** the request reaches the profile's Vercel AI Gateway
   address in the form jev-agent-tools 0.1.2 sends, and the answers come
   back in PyModel's answer format.
6. **Given** the work plugin, **When** a tool's input names a rostered
   student, **Then** the provider sees only pseudonyms and the result has
   the original names restored, whichever profile kind is selected.
7. **Given** a Hive reply that is a normal-looking success without an
   answer, **When** retries are left, **Then** the judgment is retried as
   CHE-33 made it do; server failures are retried by PyModel's policy.

---

### User Story 2 - Fair regex limits under load, and CHE-38 handed upstream (Priority: P1)

The machine is busy. `jev_extract` still finds matches for simple patterns
and still stops runaway patterns (CHE-37), with PyModel's own regex worker
pool. The event-loop stall behind
CHE-38 lives in PyModel's own code, so its fix is prepared as a
contribution to PyModel, and backfire's load check records it as a known
failure until PyModel releases the fix.

**Why this priority**: The user decided CHE-37 must be resolved and CHE-38
handed upstream, both without local code in backfire.

**Independent Test**: Run the bounded-work checks with 16 and with 80 busy
low-priority processes, as the CHE-37 assessment describes.

**Acceptance Scenarios**:

1. **Given** 80 busy processes and a document of 50,000 characters,
   **When** `jev_extract` runs a pattern that needs at most 2 ms of
   processor time, **Then** it returns the pattern's matches and never a
   time-out.
2. **Given** a pattern that runs away under Python's `re`, **When**
   `jev_extract` runs it, **Then** that field reports PyModel's time-out
   reason.
3. **Given** CHE-37's heavy-load reproduction, **When** it runs against
   PyModel's executor, **Then** its numbers are recorded, and any false
   time-out has a fix in the PyModel contribution with a test that fails
   before it.
4. **Given** the `jev_verify` load case with 100,000 identical evidence
   IDs, **When** the checks run, **Then** it is reported as a known failure
   naming CHE-38, and every other tool's worst event-loop stall stays under
   1 second with 16 busy processes.
5. **Given** the prepared contribution, **When** a maintainer applies its
   patch to PyModel's 0.6.0 source, **Then** PyModel's own tests pass and
   the `jev_verify` load case passes against the patched PyModel.

---

### User Story 3 - Backfire stays small and runs from the repository (Priority: P2)

The user wants backfire used straight from the repository package, never
installed, and wants the repository to own as little code as possible.
After the rebuild both plugins start backfire from `packages/backfire`, and
backfire's own code is the glue alone.

**Why this priority**: It follows the user's reuse rule and new size rule;
it matters after the tools work.

**Independent Test**: Start each plugin's `mcp.json` command from the
repository; count backfire's own lines against `develop`.

**Acceptance Scenarios**:

1. **Given** the code plugin's `mcp.json`, **When** a client starts it from
   the repository, **Then** backfire serves with the shipped Hive profile
   and no pseudonymization.
2. **Given** the work plugin's `mcp.json`, **When** a client starts it,
   **Then** backfire serves with the education profile and pseudonymization
   on.
3. **Given** the work plugin's wiki-consistency skill, **When** its
   commands run, **Then** they use `packages/doc-regions` and
   `packages/wiki-consistency` from the repository.
4. **Given** the finished branch, **When** backfire's own code is counted
   against `develop` (Python and TOML, tests and the pseudonymization module
   excluded), **Then** it is about 300 to 500 lines, and the count and its
   file list are reported.

### Edge Cases

- The selected profile, its credential file or a Jev profile's provider
  name is missing or invalid: tools that ask a judgment fail with backfire's
  configuration error naming the profile or file, before anything is sent;
  `jev_extract` without candidates still answers without asking.
- Pseudonymization finds two keys that become equal: the call fails with the
  existing conflict error.
- Several runaway patterns arrive at once, in one call or in concurrent
  calls: the numbers for simple patterns waiting behind them are recorded
  with CHE-37's reproduction.
- `jev_noul`'s `auto_accept` of exactly 0.5 is rejected and 0.51 is
  accepted, although PyModel's argument compiler lacks `exclusiveMinimum`.

## Requirements *(mandatory)*

### Functional Requirements

**Server and tools**

- **FR-001**: `backfire serve-mcp` MUST construct PyModel's `JevMCPServer`
  with a `Toolset` over PyModel's `Runtime` and run PyModel's `serve()`;
  backfire MUST NOT edit or copy PyModel's code.
- **FR-002**: The server MUST list PyModel 0.6.0's eleven tools, unchanged,
  followed by `jev_noul`.
- **FR-003**: `jev_noul` MUST keep jev-mcp 0.9.0's Noul definition,
  questions, labels, invalid-answer handling and budget error, defined
  through PyModel's tool framework. Where PyModel's argument compiler cannot
  enforce a keyword (`exclusiveMinimum`), the same bound MUST be enforced
  with PyModel's refinement mechanism, and the difference in the published
  schema MUST be recorded.
- **FR-004**: `jev_extract` MUST use PyModel's own default regex executor
  unchanged; backfire adds no regex engine or executor.

**Providers**

- **FR-005**: The provider factory MUST load the selected backfire profile
  and its `0600` credential file from backfire's configuration, and MUST
  NOT let PyModel's provider environment variables choose the provider. A
  profile MAY name another `0600` key file by path (the Vercel profile
  names the chat plugin's `jev.env`); the key is never logged or printed.
- **FR-006**: A Hive (general-model) profile MUST send judgments through
  system-one-adapter with the profile's address, model and extra request
  fields; failures MUST be retried by PyModel's retry policy, and a
  normal-looking reply without an answer MUST be retried as CHE-33 made it
  do, with its existing failing-then-passing test kept.
- **FR-007**: A Jev profile MUST name `typesafe`, `openrouter`,
  `cloudflare`, `compatible` or `vercel`; the first four MUST be PyModel's
  own providers, obtained through PyModel's `resolve_provider` from
  settings built from the profile; `vercel` MUST be a provider ported from
  jev-agent-tools 0.1.2's Vercel driver, credited with its MIT license.
- **FR-008**: When a plugin turns education settings on, pseudonymization
  MUST wrap whichever provider the profile selects: education data is
  replaced before a request leaves and restored in the answers.
- **FR-009**: The shipped configuration MUST keep selecting DeepSeek on
  Hive; vendor and provider details MUST stay in configuration, not in
  package code.

**Removal and plugins**

- **FR-010**: Backfire's port of jev-mcp 0.9.0, its call boundary, its
  judgment and per-call records, its readiness command, its size limits,
  its extra Hive checks and fixed error types (except the `JudgmentError`
  class), its acceptance tools and their fixtures in
  `scripts/backfire/fixtures/`, the plugin build tool and its tests, and
  the vendored copy of PyModel with its tests MUST be removed, leaving no
  unused code.
- **FR-011**: Both plugins' `mcp.json` MUST start backfire from
  `packages/backfire` in the repository; the work plugin MUST pass the
  `serve-mcp` option that turns on education settings; the work plugin's
  wiki-consistency skill MUST run the repository's `packages/doc-regions`
  and `packages/wiki-consistency`.
- **FR-012**: Everything that names backfire's tools MUST use the `jev_`
  names: the backfire skills in both plugins, repository documents,
  `scripts/workflow.ts`, and the doc-regions and wiki-consistency request
  builders, whose tests MUST pass.

**Load**

- **FR-013** (CHE-37): CHE-37's heavy-load reproduction MUST be rerun
  against PyModel's executor and its numbers recorded. If simple patterns
  still time out falsely, the smallest fix MUST go into the PyModel
  contribution with a test that fails before it; otherwise the record
  states that PyModel's warmed pool resolves CHE-37. Tests of runaway
  patterns use a pattern that runs away under Python's `re`.
- **FR-014** (CHE-38): the fixes that need PyModel's code (linear
  duplicate IDs, the stdin line limit, `exclusiveMinimum`, moving the
  measured synchronous steps off the event loop, and CHE-37's fix if
  FR-013's numbers call for one) MUST be prepared as a
  patch against PyModel 0.6.0 with its own tests and a pull-request text,
  stored in this feature's records; nothing is opened on GitHub. The
  bounded-work check MUST mark the `jev_verify` case as a known failure
  naming CHE-38 and MUST check every other tool.

**Boundaries**

- **FR-015**: `jev-judge-mcp==0.6.0` MUST be pinned in
  `packages/backfire/pyproject.toml` and `uv.lock`. License notices in
  `licenses/THIRD_PARTY_NOTICES.md` MUST cover only code copied into the
  repository (user's decision, 2026-09-30): the Vercel provider ported from
  jev-agent-tools 0.1.2 and the backfire skill text and Noul tool from
  jev-mcp 0.9.0, each with its source revision; no notice for jev-judge-mcp
  or system-one-adapter, which are installed. The other entries for
  installed packages are left to a separate cleanup (CHE-43), as the user
  directed; until then this feature only updates the python-phonenumbers
  entry's wording to match what remains after the build tool goes.
- **FR-016**: Private backfire records, student data and evaluation data
  MUST NOT enter fixtures, snapshots or reports; no implementer opens the
  held-out evaluation file.
- **FR-017**: Backfire's own code MUST be reported as a net line count
  against `develop` with its file list; going above 500 lines needs the
  user's approval first.

### Key Entities

- **Backfire profile**: a TOML table in the shipped or operator
  configuration: a Hive (general-model) profile with address, model, key
  variable and extra request fields, or a Jev profile naming its provider
  and that provider's settings; its key lives in a `0600` credential file.
- **Provider factory**: the function PyModel's `Runtime` calls to get its
  provider; backfire's builds the Hive or Jev provider from the selected
  profile and wraps it with pseudonymization when education settings are on.
- **Upstream contribution**: a patch against PyModel 0.6.0 plus its tests
  and pull-request text, kept in this feature's records.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The tool list is PyModel 0.6.0's eleven tools followed by
  `jev_noul`, checked automatically against the installed package.
- **SC-002**: Each profile kind and each named Jev provider, Vercel
  included, passes a test against a local stub; no billed call is made
  outside the final live check.
- **SC-003**: With 80 busy processes, CHE-37's reproduction against
  PyModel's executor is recorded; either 5 of 5 runs find the simple
  pattern's match, or the contribution's fix makes them do so against a
  patched PyModel. Runaway patterns time out in every run.
- **SC-004**: With 16 busy processes, every tool except the known CHE-38
  case keeps its worst event-loop stall under 1 second in 3 of 3 runs; the
  contribution's patch makes the `jev_verify` case pass against a patched
  PyModel.
- **SC-005**: At least three full `npm run verify` runs in a row pass
  without a rerun.
- **SC-006**: A final live check through the shipped Hive profile, with no
  more than 15 billed calls, returns valid judgments, and one live Jev
  judgment through the Vercel profile succeeds; the number of billed calls
  of each is reported. No other live Jev provider is checked, because no
  other Jev key is configured.
- **SC-007**: Backfire's own code is about 300 to 500 lines net of
  pseudonymization and tests, reported with its file list; no vendored copy
  of PyModel remains.
- **SC-008**: The doc-regions and wiki-consistency tests pass, and both
  plugins start backfire from the repository.

## Assumptions

- `jev-judge-mcp` 0.6.0 from PyPI runs with backfire's pinned `mcp` 2.2.0
  and `typesafe-sdk` 0.7.1 on Python 3.14.4, as the evaluation checked.
- PyModel's `serve()` provides stdio, signal handling and shutdown; its own
  argument validation and input limits replace backfire's.
- The Hive provider's retries use PyModel's retry policy through its
  `JevProvider.evaluate`, with CHE-33's answerless-reply rule added as the
  only extra case.
- Plugins are used from the repository checkout, never installed, so a
  plugin's `mcp.json` may name repository paths.
