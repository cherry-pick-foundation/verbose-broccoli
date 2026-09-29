# Feature Specification: Backfire Rebuilt From jev-judge-mcp

**Feature Branch**: `feature/backfire-rebuild`

**Created**: 2026-09-29

**Status**: Draft

**Linear issue**: CHE-39

**Input**: Linear issue CHE-39, "Rebuild backfire on FastMCP from PyModel's
jev-judge-mcp", written from the user's decisions of 2026-09-29, and the
develop session's task brief of the same day. Backfire, the judgment server
in `packages/backfire`, is rebuilt from the source of PyModel's
[jev-judge-mcp](https://github.com/PyModel/jev-judge-mcp) (MIT), release
0.6.0 at commit `fd6829c3fd1c3eb244f0feb011b6ca55298459f8`, a Python
implementation of jkudish/jev-mcp. It replaces backfire's own Python port of
jev-mcp 0.9.0. The user's decisions:

1. Replace backfire in place: the same server name and plugin setup, and
   backfire's own additions kept: saved judgment records, education
   pseudonymization, the readiness check, configuration and provider
   profiles, and judgments on general models (for example DeepSeek on Hive)
   through system-one-adapter.
2. Tool behaviour follows jev-judge-mcp as it is (jev-mcp 0.5.0 plus
   PyModel's recorded divergences and its extra score tool), with two
   additions: keep `backfire_noul`, and fix PyModel's quadratic handling of
   duplicate IDs. Tools keep the `backfire_` names. The port of 0.9.0 is
   removed.
3. The server layer is the official MCP Python SDK's `MCPServer`, which
   PyModel also uses, with tools defined by exact schemas rather than
   generated from type hints.
4. Backfire's model connection attaches through PyModel's provider seam and
   keeps CHE-33's retries for server failures and replies without an answer.
5. PyModel's source is reused with the smallest adaptation (root `AGENTS.md`,
   "Reuse Before Implementing"): it is vendored with its license and notices,
   every change from upstream is recorded, and nothing that can be kept is
   rewritten.
6. The rebuilt server fixes CHE-37 and CHE-38, each with a test that fails
   before the fix.

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

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agents use backfire's tools from the reused upstream (Priority: P1)

An agent in the code or work plugin starts backfire the way it does today and
calls its judgment tools. It gets the tool set, arguments, results and errors
of jev-judge-mcp 0.6.0 under `backfire_` names, plus `backfire_noul`. Each
judgment goes to the model named by backfire's provider profile, and the
work build still pseudonymizes education data before it leaves the machine.

**Why this priority**: It is the purpose of the rebuild; without it nothing
else matters.

**Independent Test**: Start the server with a scripted test provider, list
its tools, and call each tool with a synthetic input; compare the tool list
with jev-judge-mcp 0.6.0's definitions after the name change, and check
each result against the upstream tool's behaviour for the same answers.

**Acceptance Scenarios**:

1. **Given** a client that starts `backfire serve-mcp` as the plugins'
   `mcp.json` does, **When** it initializes and lists tools, **Then** the
   server calls itself `backfire` and lists exactly the eleven tools of
   jev-judge-mcp 0.6.0 with `jev_` replaced by `backfire_`, plus
   `backfire_noul`.
2. **Given** any of those eleven tools and an input the upstream accepts,
   **When** the model's answers are the same, **Then** the result's fields,
   values and order equal the upstream tool's result, apart from recorded
   changes.
3. **Given** an input the upstream rejects, or a tool name that does not
   exist, **When** it is called, **Then** the error result is the upstream's,
   apart from recorded changes, and the server keeps serving later calls.
4. **Given** the shipped or operator provider profile, **When** a tool asks a
   judgment, **Then** the request goes to that profile's endpoint and model
   through system-one-adapter, and no provider that jev-judge-mcp ships
   (TypeSafe, OpenRouter, Cloudflare or its compatible provider) is used.
5. **Given** the work build with pseudonymization on, **When** a tool's input
   names a rostered student, **Then** the provider sees only pseudonyms and
   the result the agent receives has the original names restored.
6. **Given** the provider answers with a server failure or a reply without
   an answer, **When** retries are left in the call's budget, **Then** the
   judgment is retried as CHE-33 made it do.

---

### User Story 2 - Tools stay responsive and fair under machine load (Priority: P1)

The machine is busy, for example during a full `npm run verify` or with other
agents running. `backfire_extract` still finds matches for simple patterns,
still stops runaway patterns, and no tool call blocks the server from
answering other messages for a second or more.

**Why this priority**: The user decided that the rebuild must fix CHE-37 and
CHE-38, not only re-check them; both made full verification runs fail at
random.

**Independent Test**: Run the bounded-work checks with 16 and with 80 busy
low-priority processes started, as the CHE-37 assessment describes, on the
code before each fix and after it.

**Acceptance Scenarios**:

1. **Given** 80 busy processes and a document of 50,000 characters, **When**
   `backfire_extract` runs a pattern that needs at most 2 ms of processor
   time, **Then** it returns the pattern's matches and never a time-out,
   however long the server waits before matching starts.
2. **Given** a pattern that runs away in the regex engine the server uses,
   **When** `backfire_extract` runs it, **Then** that field reports the
   time-out reason and the call still completes within the call deadline.
3. **Given** 16 busy processes, **When** any tool is called with a
   10 MiB message, **Then** the server's event loop is never blocked for
   1 second or more.
4. **Given** the code before each fix, **When** the new test for that fix
   runs, **Then** it fails; after the fix it passes.

---

### User Story 3 - Backfire's own services keep working (Priority: P2)

An operator relies on backfire's records, readiness check, limits and build
for each plugin. After the rebuild the records are written as before, the
readiness check passes against the configured provider, oversized messages
and slow calls end the same way, and each plugin build still contains a
working server.

**Why this priority**: The user kept these additions explicitly; losing one
would be a regression, but the tools come first.

**Independent Test**: Run the existing record, boundary, readiness, build
and education tests against the rebuilt server, changed only where the
result fields they read have changed.

**Acceptance Scenarios**:

1. **Given** a session with tool calls and judgments, **When** the session
   ends, **Then** the records directory holds one content-free record per
   tool call and per judgment, with the same kinds, fields, storage budget and
   file rules as before, and decision summaries cover every tool, including
   `backfire_score`.
2. **Given** a message over 10 MiB, a call past its 118-second deadline, a
   cancellation or a stop signal, **When** it happens, **Then** the server
   answers or ends as it does today.
3. **Given** a valid configuration and credential, **When** `backfire ready`
   runs, **Then** it passes; given a missing or invalid one, it fails and
   names what to fix.
4. **Given** `npm run backfire:build -- code <dir>` or `work <dir>`, **When**
   the built server is installed and started, **Then** it serves the rebuilt
   tools.

---

### User Story 4 - A maintainer can trace every line back to its upstream (Priority: P2)

A maintainer who later updates backfire, or checks its license, can see
which files came from jev-judge-mcp, at which revision, under which license,
and exactly how each one was changed.

**Why this priority**: It is required by the MIT license and by the
repository's reuse rule, and it keeps later upstream updates cheap.

**Independent Test**: Compare each vendored file with the same file at the
upstream revision; every difference must be listed in the upstream record,
and every unchanged file must match byte for byte.

**Acceptance Scenarios**:

1. **Given** the repository, **When** a maintainer reads the upstream record,
   **Then** it names the upstream repository, release, commit, the files
   taken, and each change with its reason.
2. **Given** a vendored file changed without a record entry, **When** the
   checks run, **Then** they fail and name the file.
3. **Given** the license notices, **When** a maintainer reads them, **Then**
   jev-judge-mcp's MIT license and its own third-party notice for jev-mcp
   are present, and the old port's jev-mcp 0.9.0 record is gone.

### Edge Cases

- A call supplies thousands of items with the same ID: the server gives them
  unique IDs in the same way as upstream, in time that grows linearly with
  the number of items.
- Several runaway patterns arrive at once, in one call or in concurrent
  calls: simple patterns waiting behind them still match and are not
  reported as timed out, and every runaway pattern still ends with the
  time-out reason.
- `regex` accepts a pattern that jev-mcp's engine would run for longer than
  the limit, such as `(a+)+$`: it returns its matches, as recorded in the
  upstream record.
- A tool's arguments contain keys that the schema does not list: the server
  handles them as jev-judge-mcp 0.6.0 does.
- The client sends `arguments: null`, omits `arguments`, or cancels a call
  while its pattern is running: the server answers as jev-judge-mcp 0.6.0
  does, and a cancelled pattern's process is killed.
- The configuration or credential is missing: tools that ask a judgment fail
  with backfire's fixed configuration error; `backfire_extract` without any
  candidates still answers without asking.
- Pseudonymization finds two keys that become equal: the call fails with
  backfire's existing conflict error.

## Requirements *(mandatory)*

### Functional Requirements

**Tools**

- **FR-001**: The server MUST be named `backfire`, start with the existing
  `backfire serve-mcp` command, and keep the plugins' `mcp.json` entries
  unchanged.
- **FR-002**: The server MUST list exactly twelve tools: the eleven tools of
  jev-judge-mcp 0.6.0 with the `jev_` prefix replaced by `backfire_`
  (`backfire_verify`, `backfire_screen`, `backfire_find`,
  `backfire_classify`, `backfire_decide`, `backfire_rerank`,
  `backfire_compare`, `backfire_extract`, `backfire_review`,
  `backfire_gate`, `backfire_score`) and `backfire_noul`.
- **FR-003**: For the eleven upstream tools, the tool definitions (title,
  description, input schema and execution settings), argument handling,
  questions sent to the model, decision logic, result payloads and error
  results MUST be those of jev-judge-mcp 0.6.0, except for the tool-name
  mapping and the changes this specification requires. Each such change MUST
  be recorded (FR-015).
- **FR-004**: `backfire_noul` MUST keep its current definition, questions,
  decision logic and result fields, and MUST be served, validated and
  reported through the same tool framework as the other tools.
- **FR-005**: Giving items unique IDs MUST take time that grows linearly with
  the number of items, and MUST assign the same IDs, in the same order, as
  jev-judge-mcp 0.6.0 does.
- **FR-006**: Every judgment MUST go through backfire's provider profiles and
  system-one-adapter, with CHE-33's retries for server failures and replies
  without an answer and backfire's fixed judgment error types. Providers that
  jev-judge-mcp ships MUST NOT be selectable.
- **FR-007**: When the shipped build enables pseudonymization, education data
  MUST be pseudonymized before a judgment leaves the machine and restored in
  the answers, as it is today.

**Backfire's own services**

- **FR-008**: The server MUST keep writing content-free tool-call and
  judgment records with today's record kinds, fields, storage budget,
  locking and failure behaviour; decision summaries MUST read the rebuilt
  tools' result fields and cover all twelve tools.
- **FR-009**: The server MUST keep the 10 MiB message limit, the 118-second
  call deadline, cancellation, stop-signal handling and session-end
  behaviour.
- **FR-010**: `backfire ready` MUST check the rebuilt server and the
  configured provider as it does today.
- **FR-011**: Both plugin builds MUST contain everything the rebuilt server
  needs, including the vendored upstream and its license files.

**Load fixes**

- **FR-012** (CHE-37): `backfire_extract` MUST match patterns with the
  `regex` library in a thread, without blocking the event loop, and its
  1-second regex limit MUST be `regex`'s own timeout, so it counts processor
  time from the start of matching and never process start-up, imports or
  waiting for a thread. A pattern that needs at most 2 ms of processor time
  MUST NOT time out under machine load. A pattern that runs away MUST still
  be stopped with the upstream's time-out reason, and each test of that MUST
  use a pattern that runs away under `regex`. The result fields, caps and
  error texts MUST stay jev-judge-mcp 0.6.0's.
- **FR-013** (CHE-38): No tool, `backfire_verify` included, MAY block the
  server's event loop for 1 second or more while handling a 10 MiB message
  with 16 busy processes on the development laptop (8 cores).
- **FR-014**: Each of FR-012 and FR-013 MUST have a test that fails on the
  code before the fix and passes after it; the failing run MUST be recorded.

**Upstream record**

- **FR-015**: The vendored jev-judge-mcp source MUST keep its upstream form
  except for recorded changes, MUST carry its MIT license and its own
  third-party notice, and MUST be credited in
  `licenses/THIRD_PARTY_NOTICES.md`. One upstream record MUST name the
  upstream repository, release, commit, the files taken with their upstream
  hashes, and each change with its reason; it replaces the record of the
  jev-mcp 0.9.0 port. An automated check MUST fail when a vendored file
  differs from upstream without a record entry.
- **FR-016**: Backfire's port of jev-mcp 0.9.0 (its tools, shared helpers,
  captured upstream cases and the tests that only cover the port) MUST be
  removed, leaving no unused code.

**Boundaries**

- **FR-017**: Vendor and provider details MUST stay in configuration, not in
  package code.
- **FR-018**: Private backfire records, student data and evaluation data
  MUST NOT enter committed fixtures, snapshots or reports; no implementer
  opens the held-out evaluation file.
- **FR-019**: The repository's documents and the plugins' backfire skill
  files MUST NOT contradict the rebuilt tool set; where they describe tools,
  results or the upstream, they MUST be updated.
- **FR-020**: The workspace packages that call backfire (doc-regions and
  wiki-consistency) MUST keep passing their tests; any request limit they
  assume MUST still hold on the rebuilt server.

### Key Entities

- **Vendored upstream**: the files taken from jev-judge-mcp 0.6.0, kept in
  their upstream form except for recorded changes, with the upstream license
  and notices.
- **Upstream record**: the document that names the upstream revision, the
  files taken, their upstream hashes, and every change with its reason.
- **Provider seam**: the point where the upstream tool runtime asks a
  provider for a judgment; backfire's provider profiles, retries,
  pseudonymization and judgment records attach there.
- **Tool-call and judgment records**: backfire's existing content-free
  session records.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The tool list has exactly twelve tools, and each of the eleven
  upstream tools' definitions equals jev-judge-mcp 0.6.0's after the name
  mapping and recorded changes, checked automatically.
- **SC-002**: The vendored upstream's own tests for the files taken pass in
  the repository, adapted only where recorded.
- **SC-003**: The CHE-37 test fails on the code before its fix and passes
  after it; with 80 busy processes, 5 of 5 runs of the bounded-work extract
  case find the simple pattern's match, and runaway patterns time out in
  every run.
- **SC-004**: The CHE-38 test fails on the code before its fix and passes
  after it; with 16 busy processes, every tool's worst event-loop stall stays
  under 1 second in 3 of 3 runs.
- **SC-005**: At least three full `npm run verify` runs in a row pass
  without a rerun.
- **SC-006**: A final live check through the configured provider, with no
  more than 15 billed calls, returns valid judgments; the number of billed
  calls is reported.
- **SC-007**: The upstream-record check passes, and changing any vendored
  file without a record entry makes it fail.
- **SC-008**: No source file of the jev-mcp 0.9.0 port remains, and the
  tests of doc-regions and wiki-consistency pass.

## Assumptions

- The `regex` library replaces only where patterns run; PyModel's
  translation of the pattern dialect, its candidate pipeline and its caps
  stay.
- The official MCP SDK version stays at backfire's pinned `mcp` 2.2.0, which
  jev-judge-mcp 0.6.0 supports; its `MCPServer` is in `mcp.server.mcpserver`.
- Only the parts of jev-judge-mcp that serving the tools needs are vendored.
  Its installer, command-line subcommands, HTTP transport, calibration,
  completion hook and packaged skills are not, because backfire's plugins,
  build and readiness check already cover those needs.
- Result payloads change from jev-mcp 0.9.0's to jev-judge-mcp 0.6.0's where
  they differ; that follows from the user's decision that tool behaviour
  follows jev-judge-mcp as it is.
- Tool calls run on the development laptop and in the repository's checks;
  the load targets use the CHE-37 assessment's method (`nice -n 19` busy
  processes on the 8-core laptop).
- New runtime dependencies that the vendored source needs are pinned like
  backfire's other dependencies.
