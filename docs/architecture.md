# Agent tool workspace

The repository is a collection of agent tools: Agent Skills, command-line
tools and MCP servers in three skill areas, `code`, `work` and `chat`
(constitution IX). Feature 060 moves it there from three Agent Plugins
packages in slices ([plan](../specs/060-clean-architecture/plan.md)). The
plugin manifests, the generator and the copied client packages are gone. The
`code` and `chat` skills live in `skills/<area>/`, Ponytail's upstream bundle
in `tools/ponytail/`, and the `work` skills stay in `plugins/work/skills/`
until the work area's hold is released.
Each capability is specified anew from current needs as a
feature under `specs/`; earlier projects are not requirement, evidence or
implementation sources.

## Current skeleton

Each area keeps its skills and its rules file together: `skills/code/`,
`skills/chat/` and, until its hold is released, `plugins/work/`. The clean-code
skill has its own npm package manifest with the skill's dependencies; it is an
npm workspace member that exports its command-line serializer as
`clean-code-skill/cli`.
The `code` area contains the adapted Wondel Clean Code skill
and `clean-code.ts`, the Spec Kit, Ponytail, commit and verification skills, and
and the upstream `jev` skill, which uses the gated `jev-mcp` server.
The `work` area contains the `quarto-authoring`, `session-migrate`,
`wiki-raw-import` and `wiki-consistency` skills, the `google-workspace`
skill with ten copied `gws-*` skills
(see [Google Workspace through gws](#google-workspace-through-gws--2026-09-30)),
and uses the same gated
`jev-mcp` server, always protected by education privacy middleware, and the
`reference-library` server (see
[Reference library](#reference-library--2026-10-01)); its other business capabilities have no
implementation until new features specify them. A small
`package.json` and lock file in `plugins/work` pin the reference-library connector.
The `chat` area contains the `web-agent` and `credit-offers` skills
(see [Chat web agent and credit offers](#chat-web-agent-and-credit-offers--2026-09-30));
it has no package manifest or scripts, and its
persistent state is the `chat` wiki (see [Wiki storage](#wiki-storage)).
No release has occurred. Agents find skills through the checkout's links and
servers through the user's own settings (see
[Sharing and distribution](#sharing-and-distribution)).

`npm run check` (`turbo run check
--summarize`) runs the environment check, formatting, lint, the file-name
check, the shell check, type checks, skill validation and the skill link test, Clean Code,
the TypeScript and Python import checks, the test suites and the document
region check, which also covers the generated references (see
[Document consistency](#document-consistency--2026-09-28)). gts 7.0.0 lints
JavaScript and TypeScript with Google's TypeScript rules and Prettier
formatting; its configuration bans runtime and I/O globals in `domain/`
folders. Prettier uses gts's settings for JSON and YAML. gts, ESLint 10.10.0
and Prettier 3.9.9 are pinned npm dependencies in `package.json`, with their
dependency tree pinned in `package-lock.json`.
Ruff 0.16.9 lints and formats Python; `tools/ruff/uv.lock` pins its environment.
The Clean Code skill keeps its own ESLint-based checker. ShellCheck 0.11.0,
which the Google shell style guide recommends, checks the repository's own
shell scripts: `npm run lint:shell` runs it on every `*.sh` file and on the
hooks in `scripts/git-flow-hooks/`, but not on Spec
Kit's vendored scripts under `.specify/`. The root `.shellcheckrc` turns on
four optional checks for guide rules: `${var}` braces, quoted variables,
explicit `-z` or `-n` tests, and `[[ … ]]` in Bash or Ksh scripts. The scripts stay
POSIX `sh`, so the guide's Bash-only rule is not applied; neither are its
formatting rules, which ShellCheck does not check. `tools/shellcheck/` is a uv
project whose `uv.lock` pins `shellcheck-py` 0.11.0.1, the PyPI wheels of the
official binary; `mise run setup` syncs it. ls-lint 2.3.1 checks that
every file and folder name is kebab-case: `npm run lint:names` runs it with
a 60-second limit and `.config/ls-lint.yml`, which gives the reason for
each name a language, tool or standard fixes (Python files and packages,
`AGENTS.md`, `SKILL.md`, `README.md` and `LICENSE`). ls-lint has no
`.gitignore` support, so `scripts/lint-names.sh` passes it the paths that Git
ignores, such as `.venv`, as literal `ignore` entries; untracked files that Git
does not ignore are checked, and `npm run test:lint-names` covers both.

mise owns the environment. `.config/mise.toml` pins every development tool
the repository needs (uv, Caddy, ls-lint, lychee, Vale, git-flow-next, gws,
betterleaks, Bitwarden's `bws` and SpecStory's command-line tool) and
`.config/mise.lock` records each download's URL, checksum and provenance; no
other file repeats a version, and `scripts/root-config-test.ts` fails when
one does. Node.js stays on the user's mise Node 24 (the root `package.json`
requires 24.12 or later), and Quarto stays a separately installed converter
whose version and installer checksum sit in the same file's `[env]`. The
`setup` task, `mise run setup`, installs those tools from the lock (and only
those, never the user's global tools) and then every dependency tree; Orca's
setup script and the hosted check workflow call it after `mise trust`, and
the doctor hints name it. `npm run doctor` runs `mise doctor project`, whose
`[doctor.checks]` entries in `.config/mise.toml` check Quarto's and CodexBar's
versions, that the pinned tools are installed and that the uv on `PATH` has
the pinned version, the locked uv environments, the npm trees, the git-flow
configuration and lefthook's hooks, and name the repair command for each
failure. The user's machine runs mise in paranoid mode, so each worktree
trusts its `.config/mise.toml` by content; Orca's setup script does that
first. The user's shell pins mise's and rustup's folders (`MISE_*`,
`RUSTUP_HOME`, `CARGO_HOME`), and Turborepo passes them to tasks, so tests
that use a temporary `HOME` still find mise's configuration and do not
download toolchains.

The repository root holds only the files that a tool or editor reads there
(`package.json`, `pyproject.toml`, `turbo.json`, `tsconfig.json`, the ESLint
files, `.editorconfig`, `.shellcheckrc` and the like). Ruff's and
commitizen's settings are the `[tool.ruff]` and `[tool.commitizen]` tables of
`pyproject.toml`, Prettier's the `prettier` key of `package.json`, and the
mise, lefthook, ls-lint and dependency-cruiser configuration lives in
`.config/`. `package.json` holds each command once and `turbo.json` holds
only the check graph: every task of it runs a `package.json` script, and each
Python package has its own `test` and `check` tasks (a Python package's test
runs its root script through `npm --prefix ../.. run`).

`workflow` supplies execution mode, graph queries and three additive skill
triggers. `verify` runs `npm run check` through Turborepo with a run summary
and passes only when the checks exit 0 and the same run's summary under
`.turbo/runs/` (ignored by Git) reports no failure; it prints VERIFIED. The
Turborepo runs turn telemetry and update notices off and ignore remote-cache
credentials. Turborepo replays a check from its local cache when none of the
check's inputs changed, and linked worktrees share the main worktree's
`.turbo/cache`. Besides the repository's files, `turbo.json` hashes the
installed uv environments' files and `scripts/toolchain.sh`'s hash of the
installed npm trees and of the programs and Git configuration outside the
repository; the checks that read
anything else stay uncached and say why in their description
([research](../specs/039-cpu-load-relief/research.md)). dependency-cruiser 18.2.0 answers the graph queries and checks
TypeScript and JavaScript imports with the rules in `.config/dependency-cruiser.json`
(`npm run clean-architecture`); a new package's public entries need a line
there. import-linter 2.15 checks the Python packages' layers and cycles with
the contracts in the root `pyproject.toml` (`npm run python:imports`). In
REVIEW mode it asks the implementer or the orchestrator to review the
diff before each commit and leaves the independent review to the merge into `develop` or
`main` (see [Git flow](#git-flow--2026-09-27)). Reuse those commands for later
feature work.

The [command reference](reference/commands.md) lists every root task and the
help text of the repository's own commands. It is a Cog region (see
[Document consistency](#document-consistency--2026-09-28)): `npm run
doc-regions:update` refreshes it, and `npm run doc-regions:check` rejects
stale output without writing. `check`, `verify` and the PR documentation job
run that check. The job definition alone does not establish
a successful hosted run or required branch protection.

Workflow difficulty is independent of execution mode, verification and model
selection. The same Git collector supplies workspace routing and each declared
plan task's literal file scope. Without a plan, difficulty describes the whole
workspace, including unrelated changes. It measures observed staged, unstaged
and untracked changes against the selected base, not future work. Reversals
between index and worktree are counted separately. Public-entry detection is a
file-path signal, not proof of a changed API signature.

Policy `coding-difficulty/1` evaluates the following conditions in order:

| Level | Mechanical condition | CLI guidance |
| --- | --- | --- |
| Unassessed (`null`) | Invalid plan/scope, no changed files, or unknown text line count | Gather observable changes before assessing |
| `very_difficult` | More than 20 files or 2,000 changed lines | Split and review the large scope |
| `difficult` | Public entry, deletion/rename/type/conflict, more than 5 files or 500 lines | Review the entry, structure or large change |
| `medium` | More than 2 files or 100 lines | Check related changes together |
| `easy` | More than 1 file or 20 lines | Implement and check the bounded change |
| `very_easy` | Remaining observed changes | Check the small single-file change |

The five labels reuse LOM vocabulary only. These initial project thresholds are
not a standardized or calibrated measure of coding difficulty. They infer no
runtime complexity, graph independence or model capability. The JSON result
includes the policy version, scope, level, Korean description and measured facts.
A required REVIEW can coexist with `very_easy`; difficulty never relaxes gates
or selects a model by itself. Agents, models and efforts are chosen with the
code area's `model-choice` skill, whose Jev judgment takes the level as
evidence together with each candidate's remaining usage.
CodexBar 0.69.0, a host tool at `~/.local/bin/codexbar` linking to
`~/.local/opt/codexbar-0.69.0/`, gives that skill most usage limits and Codex's
reset credits; Orca's
`orca account list` gives Grok's and Cursor's. It is the
release's x86_64 Linux (glibc) archive, extracted whole after checking it
against the release's checksum file.

## CLI contract

The repository-owned entrypoints `workflow` (and its `verify` alias) and
`clean-code` (including `--scope`)
use pinned Cliffy for help and parsing. A small shared serializer owns JSON
output, error serialization and exit classification; it is exported only as
the clean-code skill's `scripts/cli.ts`, which `workflow` imports, and
bundled in the portable clean-code skill.

| Outcome | Exit | stdout | stderr |
| --- | --- | --- | --- |
| `--help` / `-h` | 0 | Plain-text Cliffy help | Empty |
| Completed successfully | 0 | One command-specific JSON object | Empty |
| Invalid options, arguments or input-plan schema | 2 | Empty | Error JSON |
| Execution failure | 1 | Empty | Error JSON |
| Checks found violations | 1 | Empty | Error JSON with the full report in `details` |

Errors use `{ "error": { "code": "INVALID_ARGUMENT", "message": "..." } }`.
Codes are `INVALID_ARGUMENT`, `EXECUTION_FAILED` and `CHECK_FAILED`. The
`details` field sits beside `error` and keeps the checker or workflow report,
including graph diagnostics and skill guidance when a workflow gate fails. A selected REVIEW mode is not a failed check and still exits 0.
Use `npm run --silent <command>` for machine consumption; npm's own banners
and launch failures are outside this contract, and gts, Prettier and Node
test output keep their native form.

`npm run test:cli-contract` checks these rules with real child processes, and
help snapshots freeze the presentation. A copied-skill test checks that
clean-code runs outside the repository. Update the snapshots only after review
with `npm run test:cli-contract -- --update`, then rerun without updating.
The Clean Code skill and checker share mechanically selected files; see
the `code` area's [Clean Code skill](../skills/code/clean-code/SKILL.md). Adding a
workspace member does not make it an independently published JSR package.

The root README is a short project summary; use specs and docs for detailed
documentation. The dependency pins remain in `package.json` and
`package-lock.json`.

## Package and runtime ownership

Each capability with code lives in one component package under
`packages/<name>/`, with its dependencies pointing inward: a domain without
input or output, an application layer with its use cases and ports, adapters,
entry points and one `bootstrap` module that reads settings (see the
[dependency rules](../specs/060-clean-architecture/contracts/dependency-rules.md)).
Packages move into that shape one slice at a time. Code that an open branch
changes, that a replacement trial may replace, or that waits for the privacy
gate's fix stays where it is until its hold is released (plan "Holds").
Skills carry the instructions; command-line tools and MCP servers are the
packages' entry points. Final checks cover Codex CLI and Claude Code: the
skills and MCP servers each agent actually loads, required hooks and
permission and data paths; a file or manifest check alone is insufficient.
Business capabilities belong to the `work` area once features specify them.
Create entry points, source folders and rings only when a specified
capability has an actual consumer. Selected Wiki storage follows constitution
principle VI; restructuring code does not move live data or other external
operational or source roots.

### Wiki storage

The Wiki instances live in
`$XDG_DATA_HOME/verbose-broccoli/llm-wiki/` (by default under
`~/.local/share`), outside the repository, one folder per wiki:

| Wiki | Holds |
| --- | --- |
| `default` | Knowledge that belongs to no single plugin |
| `chat` | Exported conversations as raw evidence and the pages written from them; the chat package's persistent state |
| `code` | Coding knowledge for work in any project: libraries, patterns, decisions. It is not this repository's development memory, which stays in the Spec Kit records, code and Git |
| `work` | Education work: the raw imports, including exported conversations, and the per-student pages |

Each wiki's schema `AGENTS.md` owns the roles of `raw/{web,files,notes,assets}/`,
`text/`, `wiki/` and `site/`. Raw is immutable create-only BagIt originals outside
Git. Wiki-local Git with no remote versions schema, full original-language
`text/<source-id>/<revision>.qmd` extractions and English `wiki/**/*.qmd` pages
with topics. `site/` is Korean delivery derived from chosen English versions,
with tags and no `ko/` tree. F2/CHE-12 owns freshness, rendering and publishing;
new real conversion, student/audience and publication decisions stay with main.
A plugin's Wiki skills use the wiki named after the plugin
unless the user selects another; `default` is always selected by name. Wikis
are the user's shared Wiki storage, not a plugin's private store, so any
plugin's Wiki tool may write a wiki the user selects.

The work plugin's `wiki-raw-import` skill creates a wiki and copies documents
the user confirms into its `raw/`, in `work` unless another wiki is named.
Only the `chat` and `work` wikis admit exported conversations; the skill
admits each ChatGPT export into both. Exported Claude Code and Codex
sessions, rendered to Markdown by SpecStory's command-line tool, may go into
any wiki they belong to; the skill's session selection reference picks
them with `jev-mcp`, and the user approves the list. Each copy is one
read-only BagIt bag whose `bag-info.txt` records the source ID, the original
path and modification time, and the admission time, and whose manifest holds
the SHA-256 digest. The bags
are the only record of sources and revisions. The user's exclusions live in
`$XDG_CONFIG_HOME/verbose-broccoli/config.toml`; import staging lives under
the cache root. The import makes each bag with bagit 1.9.0's own `make_bag`;
it no longer locks out a second run into the same wiki, cleans up staging
left by a crash, or hashes the original again after copying.

### Wiki consistency

Wiki pages follow the region model of repository documents (below): each part
is a mechanical region that a generator rebuilds from named instance files, or
agent-written text that Jev MCP judges. The engine is the uv project
`packages/wiki-consistency/`, which calls `packages/doc-regions/` as a library
with the instance as its root; the work plugin's build ships both projects,
and the plugin's `wiki-consistency` skill runs the commands. The instance's
`AGENTS.md`, from the `wiki-raw-import` skill's template, states the rules.

- Pages are written in English, whatever the language of the raw evidence,
  which stays unchanged; student names use the roster's romanized spelling,
  the Korean spelling stays only in the roster, a school is written as its
  domain ID, and a short direct quote may stay next to its translation.
- Pages carry YAML front matter with a title, a one-line summary, the
  source revisions they cite and one or more topics. A wiki groups its
  pages by topic instead of splitting into more wikis; the front matter of
  its `AGENTS.md` declares the topics its pages may list, and the layer
  folders stay as they are. `index.qmd` is one mechanical region,
  `page_catalog`, built from that metadata, which lists the pages under a
  heading per topic; a source page may hold a `source_provenance` region
  built from its bags. `overview.qmd` is written by the agent, and `log.qmd`
  is append-only and never judged.
- `check` runs before every commit of the instance. It fails on a stale or
  malformed region, a broken link (lychee, offline), missing or unresolvable
  page metadata, a missing or malformed topic list in `AGENTS.md`, a page
  topic that list does not declare, a cited bag that fails BagIt's fast
  validation, or a changed earlier `log.qmd` entry, and it lists orphan pages
  and citations of non-latest revisions. It also runs the page rules as
  Vale 3.23.0 rules (`packages/wiki-consistency/vale/`), outside mechanical
  regions, the front matter and `log.qmd`: phone numbers, email and postal
  addresses and registration numbers; Hangul, Chinese or Japanese text other
  than one quote with its English translation in parentheses beside it;
  roster school names in Hangul outside such a quote, instead of domain IDs; and dates not written as YYYY-MM-DD or times
  without a zone. The privacy and time rules also check code and link
  targets; the language, school and date rules skip them. A small Python
  step reads the work-owned domain roster only when a page needs it, checks that a
  student page is `wiki/students/s-<EduOK student number>.qmd` with a number
  from the roster's `id` column, reports the Korean spelling of a roster
  student, given or guardian name anywhere in a page, quotes and front matter
  included, and gives Vale the roster's schools through a private temporary
  folder that it removes afterwards. Vale runs offline with
  `--no-global` and line output, on regular files only (symbolic links are
  skipped), and a failure never repeats the matched text. The rules are
  patterns: an impossible date such as 2026-02-30 in the YYYY-MM-DD shape
  passes, a registration-number shape is flagged even with an impossible
  birth date, phone and email detection is Vale's, not the gate's, and only
  the student-name rule reads the front matter's title and summary. The
  check creates temporary rule and link-check files, leaves maintained wiki
  source unchanged, and uses no network.
  `update` regenerates stale regions. `check` is the offline structural,
  metadata and rule stage; it does not prove exact sentence evidence or
  semantic correctness.
  Every leftover `wiki/**/*.md` fails migration before catalog or privacy checks.
  The Markdown parser rejects executable Quarto cells and includes/shortcodes
  in Wiki source, allowing inert code examples and preserving source bytes.
  Original-language `text/` does not inherit Wiki language restrictions.
- The judgment step runs at the end of an operation that changed pages, and
  over the whole Wiki in a lint. `convert` turns cited revisions into
  full returned original-language `.qmd` in `text/<source-id>/<revision>.qmd`,
  reusing existing retained output. PDFs use the existing `pdftotext -raw`
  content-stream order, with the actual backend version recorded; the command
  must be on `PATH`. Missing/failed backends remain unreadable, and warnings
  mark output partial. Other formats keep MarkItDown/JSON/python-hwpx paths;
  failure diagnostics use cache. Front matter records raw
  identity/hash, converter/version, conversion status/warnings and original review.
  `conversion-status: extracted` means backend output, not completeness or review;
  partial and unknown remain explicit. Scanned PDFs remain unreadable. Corrections
  are local Git history, never raw edits or default reconversion replacement.
  `evidence.read(instance, source_id, revision, review=...)` reads the full body.
  A true review flag requires actual caller evidence with raw `sha256`, full-file
  `extraction-sha256` and nonempty `evidence`; corrections invalidate earlier
  evidence, and unknown legacy facts are never promoted to reviewed.
  `prepare --review-receipts <path>` accepts optional JSON mapping canonical
  `source-id/revision` keys to real `sha256`, `extraction-sha256` and `evidence`
  receipts; the API accepts `reviews=...`. Missing or stale receipts leave true
  review status unresolved, and a receipt does not promote unchecked text.
  `index` builds qmd 2.8.3
  collections of English `.qmd` pages and retained text under
  `$XDG_CACHE_HOME/verbose-broccoli/qmd/` (3 GiB budget, a folder only the
  user can read), with the multilingual
  Qwen3 embedding model, a 610 MB download only when `index` is asked to
  download it. The check uses qmd's own command line and one stdio MCP
  session per search, with typed keyword and vector queries, reranking off
  and qmd's CPU mode, so no other model is downloaded. Without the model,
  keyword search alone finds no other page for a whole paragraph, so
  `prepare` then checks units only against their evidence and says that it
  searched no other pages. `prepare` prints
  `jev_verify` requests (units against their cited evidence, and against
  candidate units of other pages), `jev_find` cross-reference requests
  in a lint, and `jev_classify` requests for new units. qmd only finds
  candidates; Jev MCP judges. The API records `outcome: unverifiable` units
  and their reasons. The CLI prints diagnostic JSON on stdout and exits 1 when
  any unit is unverifiable; boundary, bag, index and execution errors use stderr
  diagnostics and exit 1, while invalid command-line arguments exit 2.
  Missing inline citations and unchecked review status are operational limits,
  not permission to invent citations, receipts or another batch. Claim/item and
  decision limits and caller evidence budgets differ from complete serialized
  tool-argument character/byte measurements; none establishes a whole-body cap
  or the provider's unknown HTTP/token expansion limits.
- The agent sends prepared requests to the shared `jev-mcp` proxy without
  requiring translation of Korean evidence. Its mandatory gate replaces registered
  person/school spellings and phone, e-mail, ten-digit EduOK and resident-number
  patterns before the provider call, then restores result text. Korean text,
  grades, classes and school years remain unchanged; unknown spellings can pass.
  The agent confirms a contradiction between two pages with `jev_compare`.
- `npm run wiki-consistency:install` installs both environments, after
  the education privacy gate's; Wiki domain checks remain work-owned and
  separate from the gate's minimal registered list. `mise run setup` runs the
  same installs, and `npm run doctor` checks them. `npm run test:wiki-consistency` runs
  the package's tests.
- Not automated: sending the requests and acting on the results, accepting
  suggestions, updating stale citations, writing `log.qmd` entries, applying a
  new schema template to an existing instance, and converting scanned PDFs.

Folder defaults use `_metadata.yml`. The checker merges root-to-folder defaults
and page front matter itself, without per-page `quarto inspect`. Mappings recurse,
arrays merge uniquely in order, empty/null array overrides preserve inheritance,
scalar/list pairs combine and ordinary page scalars override. Preserve meaningful
overrides, including `profile.checker: none`. The public
`read_metadata(instance, document, named_defaults=...)` returns the full mapping
and problems for a literal Wiki-relative `.qmd` path. `metadata_sources` lists
safe ordered ancestors without content reads. Cog remains one catalog region
with `wiki/**/*.qmd` plus actual existing literal metadata inputs where consumed;
no absent glob, unnamed input or Quarto listings replacement.

Supported knowledge sentences end with canonical citations whose keys come only
from bags as `source-id/revision`. Exact declared `p.`, `pp.` and `sec.` locators
use `evidence.read_located(..., locator, max_chars=..., review=...)`, never a
whole-source, latest-revision or search fallback. Page/section headings and page
fenced div markers are supported; PDF formfeeds do not establish missing markers.
Arbitrary inline markers, section divs and lone-CR mappings remain unresolved.
Existing valid retained text remains available for direct local reading when a locator cannot resolve. Native Pandoc
parsing uses restricted literal alignment of plain paragraphs and simple list
items; pySBD proposes candidate spans checked against exact source slices and
citation coverage. Unsupported or ambiguous formatting, headings, tables,
callouts, quotes and source maps, or lost text/citation coverage, are explicit
unresolved failures, never a quiet zero-request success or a sentence-completeness
claim. Source stays inert without executable
cells, heavy includes or shortcodes.

`evidence.bibliography(instance, revisions, budget_bytes=..., env=...)` yields a
fresh private cache run's `sources.json` only within its context, cleaned on
success, failure and catchable interruption. CSL entries use `id: source-id/revision`,
`type: document`, the BagIt payload filename as `title`, and custom provenance;
no invented author/date, sender or absolute paths. Earlier output is never
new-run authority; no bibliography belongs in wiki Git. F2 supplies renderer
source and audience selection.
`prepare` consumes a bibliography scoped to its selected revisions; index and
search do not build an unused whole-wiki bibliography.

The grammatical-competence consumer reads `.qmd` through shared metadata and
retained evidence, without a separate PDF bypass. Its run's `extractions.json`
pins raw/extraction hashes and revision; later raw revisions cannot silently
retarget a recorded profile. Missing legacy provenance is refused/unresolved,
not a reason to rerun paid proposals. Reference pages link
`../../text/<source-id>/<revision>.qmd`; section indexes use exact full-file lines,
including front matter. Moves or header changes need verified reconciliation,
never guessed offsets. JSON Lines order, repeats, empty entries and checker `none`
remain unchanged. The absent held lexical-semantics skill is not rebuilt here.

### Jev MCP server

One judgment server named `jev-mcp` serves the Code and Work areas; each agent
registers it once in the user's own settings. The installed uv
package `packages/education-privacy-gate/` runs a FastMCP proxy with mandatory
education privacy middleware. It launches the unmodified pinned npm package
`@jkudish/jev-mcp` 0.13.0 as a hidden stdio child, with OpenRouter and
`typesafe/jev-1.13` fixed. There is no direct registered child or provider fallback.

The gate masks registered person and school spellings, phone and e-mail patterns,
isolated ten-digit EduOK numbers and resident-number patterns per call.
Each person gets one default-English Faker first name across their registered
forms; schools use `School NN` labels. Korean text, grades, classes and school
years remain unchanged. Every result text field is traversed for restoration.
Only the source-backed registered list persists outside Git; pairs stay in memory
for one call. Unknown spellings and identifying context remain residual risks.

The [Jev MCP operator guide](jev-mcp.md) gives commands, twelve upstream tools,
restoration rules, bounds and the independent dependency review. `jev_score` is
absent; `jev_audit` audits extraction. The legacy judgment implementation and
its dependencies have been removed. External activation waits for the first
official release.

### Google Workspace through gws — 2026-09-30

Feature 027 ([spec](../specs/027-google-workspace/spec.md)) lets agents work
in the user's Google Workspace through gws, the Google Workspace CLI. gws is
a host tool pinned through mise, not a dependency of any package, and keeps
its OAuth client file and tokens in its own folder `~/.config/gws/`, outside
the repository. The work package carries ten of gws's agent skills, copied
from the pinned tag with an `upstream.json` each, and the local
[`google-workspace` skill](../plugins/work/skills/google-workspace/SKILL.md)
with this repository's rules: the approved scopes, how to invoke gws, and
when to ask the user first. The security check of the pinned release is in
`specs/027-google-workspace/security/`.

### Reference library — 2026-10-01

Feature 040 ([spec](../specs/040-reference-library/spec.md)) lets agents use
the user's Zotero library without the Zotero window. The chain, all through
systemd user units kept in `infra/reference-library/`:

1. `reference-library.socket` listens on `127.0.0.1:23190`. The first request
   starts `reference-library.service`, which runs `systemd-socket-proxyd
   --exit-idle-time=10min` toward the gateway on `127.0.0.1:23191`.
2. `reference-library-gateway.service` runs Caddy (pinned in `mise.toml`) with
   `reference-library.caddyfile`. Zotero's web server answers only a Host
   header with its own port 23119, and the socket proxy cannot change
   headers, so Caddy rewrites it and forwards to `127.0.0.1:23119`.
3. `reference-library-app.service` runs `zotero --headless` and holds the
   proxy back until the local API answers. If the app is already open, it
   holds one idle connection to it instead, so no second copy starts and the
   chain ends when the app closes. Both services stop when nothing needs them
   (`StopWhenUnneeded`); the proxy is bound to the app unit.
4. `reference-library-app.desktop` replaces the app's menu shortcut for this
   user: it stops the background copy, then opens the app.

`sh infra/reference-library/install.sh` copies the units, the Caddyfile and the
shortcut to the user's folders and starts the socket. To uninstall: `systemctl
--user disable --now reference-library.socket reference-library.service`,
then delete `~/.config/systemd/user/reference-library*`,
`~/.config/reference-library/` and `~/.local/share/applications/zotero.desktop`,
and run `systemctl --user daemon-reload`. If the Caddy pin changes, change the
version in `reference-library-gateway.service` too; `npm run
test:reference-library` checks that they agree.

The `zotero-native-mcp` 1.0.1 connector is the `reference-library` server.
Both agents' registrations in the user's own settings run a separate install
of that version under `~/.local/share/mcp-servers/zotero/1.0.1`, pointed at
the socket's port. `plugins/work/package.json` and its lock pin the same
version in the repository (installed by
`npm ci --ignore-scripts --prefix plugins/work`) so that
`npm run test:reference-library` can check the pin, the lock and the tool
names. Its delete-items, delete-collection and empty-trash tools are blocked
in each client's own settings: Claude Code's permission deny rules
(`.claude/settings.json` and the user's settings) and Codex's
`disabled_tools` in the user's `~/.codex/config.toml`. The test also checks that each blocked name is a tool of the pinned connector
and that the repository's deny rules list it. See
[Sharing and distribution](#sharing-and-distribution) for how servers reach
agents.
The security checks of the connector
and of Caddy are in `specs/040-reference-library/security/`.

### Chat web agent and credit offers — 2026-09-30

Feature 021 ([spec](../specs/021-chat-jev-ultrafast/spec.md)) gives the chat
package two skills backed by two uv workspace packages.

- `packages/jev-ultrafast/` is Browser Use's Jev Ultrafast (MIT) copied at a
  fixed revision and patched in two modules; its
  [`upstream.md`](../packages/jev-ultrafast/upstream.md) lists the revision,
  the original file hashes and every difference. Browser-choice judgments
  call `jev_classify` through the gated `jev-mcp` proxy.
  By default the agent opens its own
  tab in Orca's built-in browser and attaches to it through that tab's own
  browser control address; `JEV_BROWSER=chrome` keeps upstream's Chrome
  connection. The `web-agent` skill runs it.
- `packages/credit-offers/` checks the freetokens tracker over plain HTTP for
  offers that entered its published list during the latest 6-hour block,
  asks once per run through the gated proxy's `jev_classify` whether each costs
  nothing and states no time limit or end date, and sends a desktop
  notification for those that do. It saves
  nothing. The `credit-offers` skill runs it, and the user approved an Orca
  automation on the laptop that runs it every 6 hours as a precheck; the
  interval comes from the tracker's history
  ([research R9](../specs/021-chat-jev-ultrafast/research.md#r9-the-schedule-interval)).
- Keys live in the shared provider folder
  `$XDG_CONFIG_HOME/verbose-broccoli/providers/` (by default under
  `~/.config`), one `0600` file per provider (`vercel.env`, `cloudflare.env`,
  `openrouter.env`, `hive.env`, `github.env` for the offer search's
  optional GitHub token, and `copilot.env` for CodexBar's Copilot usage
  call), which every plugin uses. Credit offers passes only the optional
  `github.env`. Both callers pass only an absolute `XDG_CONFIG_HOME` to the
  gated `jev-mcp` launcher, which loads its protected OpenRouter key itself.
  `npm run secrets:refresh` refreshes provider and approved client files from
  multiple Bitwarden Secrets Manager sources with the existing pinned `bws`
  (feature 052, [spec](../specs/052-secrets-refresh-sources/spec.md)). The
  external `verbose-broccoli/secrets.json` names each source's private token
  file, project and optional HTTPS server, plus variable or whole-file mappings.
  Every token preflights before any fetch, and every configured source is
  collected before requested values are validated. Variable mappings preserve
  unmapped bytes and support aliases. Targets are restricted to provider names,
  the OMP agent `.env`, the two ownCloud client env files and optional GWS
  `client_secret.json`; see the [operator contract](../specs/052-secrets-refresh-sources/contracts/operator-config.md).
  All private temporary files are prepared before rename, with mode `0600`
  outputs; validation failures preserve targets, while rename-time filesystem
  failures have no multi-file rollback. Provider-key storage remains unchanged.
- Ultrafast browser-choice judgments use the gated `jev-mcp` proxy.
  The text-generation helper stays held, with no
  authorized ungated student-data route. See the
  [migration handoffs](../specs/053-jev-mcp-privacy/contracts/migration.md#chat-handoffs-exact-dependency-edges).
- `npm run test:jev-ultrafast` and `npm run test:credit-offers` run the
  offline tests; both are part of `npm run check`.
- Not automated: live provider calls, which spend paid credit; catching up
  blocks the laptop slept through; screenshots and scrolling
  in an Orca tab that is not drawn on screen.

## Sharing and distribution

Reuse existing dependencies directly first. Constitution IX puts reusable
implementation packages, including libraries and MCP servers, under
`packages/<name>/src/`; add one only for a concrete shared need. A package joins
a toolchain workspace only when it has executable code for that toolchain, so
the Python package `packages/education-privacy-gate/` joins the root uv
workspace; its npm manifest pins the hidden upstream judgment server.
Shared packages are implementation dependencies, not a fourth skill area. An
area does not deep-import another area's private files or open another area's
private operational store; Wiki instances are not such a store (see [Wiki storage](#wiki-storage)).

### Live checkout discovery

Edit skills in `skills/<area>/<name>/`, their canonical source folders
(Ponytail's four in `tools/ponytail/skills/`, the work area's in
`plugins/work/skills/` while it is held). The repository's `.agents/skills` is
a real directory of relative links, such as
`jev -> ../../skills/code/jev`, and `.claude/skills ->
../.agents/skills` gives Claude Code the same index. The links stay inside the
checkout and show source edits at once, with no copy, installer or version
bump. Codex and Claude Code read the links from the checkout's own folders, so
a new checkout needs no preparation step beyond `mise run setup`.

Two checks cover the skills. `npm run test:skills-links` fails when an
`.agents/skills` entry is not a relative link, does not reach exactly one
skill folder with a `SKILL.md`, repeats a name, or when a skill folder has no
link. `npm run skills:validate` runs `agentskills validate` from `skills-ref`
0.1.1, the Agent Skills reference validator, over every skill under `skills/`
and `plugins/work/skills/`. Ponytail's four unchanged upstream skills live in
`tools/ponytail/skills/`, outside those folders, so they are not validated;
the validator rejects their `argument-hint` key. `tools/skills-ref/` is a uv project whose `uv.lock` pins the validator
and its four dependencies by hash with `no-build`; `mise run setup` syncs it
once and `npm run doctor` checks it. Upstream calls the library a
demonstration, so it is a development-time check only, never imported by
shipped code (see the
[security review](../specs/060-clean-architecture/security/skills-ref-review.md)).
Keep `_AGENTSKILLS_COMPLETE` unset: when set, the validator's command-line
library runs a shell for completion.

The repository adds no project MCP configuration: no root `.mcp.json` and no
generated block in `.codex/config.toml`. `jev-mcp` and `reference-library` are
registered once per agent in the user's own settings (`~/.claude.json` and
`~/.codex/config.toml`); see the
[delivery contract](../specs/060-clean-architecture/contracts/delivery.md).
Changing a registration needs the user's approval. Use a fresh session to
check changed MCP configuration; skill-text reload does not prove a server
configuration has reloaded. Receipts that earlier discovery runs left under
`$XDG_STATE_HOME/verbose-broccoli/workspaces/*/plugin-discovery/` stay as
history; deleting them is the user's choice.

Keep folder and frontmatter names equal. Local invocation uses
`$jev` in Codex and `/jev` in Claude Code. Model-choice judgments still forbid
student data and other personal records; the shared gate does not relax that
boundary.

Claude's shared `.claude/rules/claude-code.md` requires filesystem `realpath`
of a linked project skill directory before constructing relative Read or Bash
paths for rules, references, helpers or assets. Use that canonical base rather
than the session's working directory or the shared index. For example,
`model-choice`'s `../AGENTS.md` names its owning area's rules. Root `AGENTS.md`
also requires reading those rules; discovering a skill alone does not prove
the client loaded them.

The canonical-path guidance for Claude is a rule that depends on the model
following it; no client mechanism enforces it. It was tested in two fresh
Sonnet 5.5 sessions at high effort, and only those two cases. Other models,
helper or asset execution, client file watchers and other platforms are not
verified.

[Codex's skill documentation](https://learn.chatgpt.com/docs/build-skills)
supports symlinked skill folders under `.agents/skills`, scanned from the
working directory up to the repository root. It says skill changes are detected
automatically, with a restart fallback if an update is missing. Existing context
can still contain older instructions; use a fresh session and inspect the
canonical source path when checking an edit.

[Claude Code's skill documentation](https://code.claude.com/docs/en/skills)
supports symlinked project skill entries. It describes live `SKILL.md` updates
outside bare mode and `/reload-skills` for a discovery directory created after
session start. This checkout also links the discovery root; check the installed
client's behavior rather than assuming its watcher follows every target edit.
Use a fresh session if reload does not expose the canonical source.

Plugin copies installed earlier in a user folder may coexist with the links.
Claude keeps both local and namespaced skills, such as `/jev` and `/code:jev`;
enterprise skills win over personal, which win over project skills of the same
name. Codex does not merge equal skill names and can show both entries. Inspect
paths before invoking; an installed copy is not evidence of the live source.
Nothing in this repository uninstalls or disables user packages.

Linux native clients are the acceptance target. Relative links are filesystem
links, not a Windows copy fallback; macOS, Windows and remote or web clients
need their own discovery and resource-resolution evidence. Filesystem checks
alone do not establish native client acceptance.

### Skill source ownership — 2026-09-14

Maintain each skill body only in its owning area. The shared local discovery
index links to those folders; it does not hold another source tree. Each skill
exists once, so `jev` lives in `skills/code/jev` and `.agents/skills`
links to it from every checkout. `scripts/skills-links-test.ts` checks that
one-to-one match.

<!-- [[[cog import doc_sources; cog.out(doc_sources.skill_table("skills/*/*/SKILL.md", "tools/ponytail/skills/*/SKILL.md", "plugins/work/skills/*/SKILL.md")) ]]] -->
| Package | Owned skills |
| --- | --- |
| `plugins/work/skills` | `google-workspace`, `grammatical-competence`, `gws-calendar-insert`, `gws-docs`, `gws-docs-write`, `gws-drive-upload`, `gws-forms`, `gws-shared`, `gws-sheets`, `gws-sheets-append`, `gws-sheets-read`, `gws-slides`, `quarto-authoring`, `session-migrate`, `wiki-consistency`, `wiki-raw-import` |
| `skills/chat` | `credit-offers`, `web-agent` |
| `skills/code` | `clean-code`, `git-commit`, `jev`, `model-choice`, `speckit-agent-context-update`, `speckit-analyze`, `speckit-assess-decide`, `speckit-assess-define`, `speckit-assess-intake`, `speckit-assess-research`, `speckit-assess-shape`, `speckit-bug-assess`, `speckit-bug-fix`, `speckit-bug-test`, `speckit-checklist`, `speckit-clarify`, `speckit-constitution`, `speckit-converge`, `speckit-git-validate`, `speckit-implement`, `speckit-plan`, `speckit-specify`, `speckit-tasks`, `speckit-taskstoissues`, `verification-before-completion` |
| `tools/ponytail/skills` | `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-review` |
<!-- [[[end]]] -->

`session-migrate` owns task handoff and resumption, including checks of current
sources.

Ponytail is one unchanged upstream bundle in `tools/ponytail/`: its hooks in
`hooks/`, its tests in `tests/` and its four skills in `skills/`. Its skills
and instruction loader find `tools/ponytail/AGENTS.md`, the only file added to
the bundle, which points to the code area's rules. `.agents/ponytail` is a
compatibility link to that folder, so the commands in `.codex/hooks.json` and
their trust hashes stay unchanged. The shared discovery index points to the
canonical Ponytail skill directory. Runtime state remains in the Git-local `ponytail` directory.
Client hook registration remains project configuration, not a new portable
hook manifest. The existing project policy hook is separate from this migration.

Skill licenses, provenance, templates, references and invocation metadata move
with their sources. Spec Kit continues to operate on the target project's
initialized `.specify` scripts, templates and constitution. Quarto retains its
existing host runtime requirement.

`npm run test:skills-links` compares the `.agents/skills` links with the skill
folders under `skills/*`, `tools/ponytail/skills` and `plugins/work/skills`,
the roots listed once in the test, and
`npm run skills:validate` validates each skill's front matter. Neither replaces
fresh native client discovery and invocation evidence.


### Spec Kit extensions — 2026-09-27

The project uses Spec Kit's bundled `agent-context`, `assess`, `bug` and `git`
extensions, installed under `.specify/extensions/`. `specify extension add`
writes their skills to `.agents/skills`; following the table above, the ten in
use live in `skills/code` instead.

- `assess` and `bug` run only when invoked. They keep their records in
  `.specify/assessments/<slug>/` and `.specify/bugs/<slug>/`.
- One local preset, `linear-issue` in `.specify/presets/`, adds an `append`
  layer to the spec template for the feature's Linear issue line (see
  [Linear](#linear--2026-09-27)). Spec Kit's `specify preset add --dev`
  installed it and wrote `.specify/presets/.registry`; `specify preset resolve
  spec-template` shows the layers.
- Every `git` hook is disabled in `.specify/extensions.yml`. Each worktree is
  created on its own feature branch, and the `before_specify` hook would create
  and switch to another branch inside it; the auto-commit hooks would bypass
  the constitution's commit rules. Only `speckit-git-validate` is packaged; it
  checks numeric or timestamp-prefixed branches against matching spec directory
  prefixes, so it does not validate unnumbered `feature/<name>` branches.
- `agent-context` writes its current-plan pointer to the gitignored
  `.claude/rules/current-plan.md`, which Claude Code loads and Codex does not.
  The pointer differs per worktree, and the root `AGENTS.md` is maintained as
  the user supplied it. Both after hooks are enabled and non-optional. They run
  Python with PyYAML from `SPECKIT_PYTHON`, which `.claude/settings.json` and
  `.codex/config.toml` set to `tools/spec-kit/.venv/bin/python`.
- `tools/spec-kit/` is a uv project whose `uv.lock` pins the Spec Kit CLI
  1.0.12 (commit `e77daa9`), PyYAML and Python 3.14. `mise run setup` runs `uv sync --locked --project
  tools/spec-kit` in each worktree to create the gitignored `.venv`, and
  `npm run doctor` fails when that environment is missing or differs from the
  lock. Run Spec Kit from the repository root as
  `uv run --project tools/spec-kit specify …`.

### Git flow — 2026-09-27

Features are finished into `develop` with git-flow-next 2.1.0
(<https://github.com/gittower/git-flow-next>, BSD-2-Clause). Its source is
unchanged; repository-local settings and pre- and post-finish hooks adapt it
to the constitution's git flow rule and safe cleanup procedure.

- git-flow-next is pinned through mise (see the mise paragraph under
  [Current skeleton](#current-skeleton)); the mise copy is byte-identical to
  the earlier host copy in `~/.local/bin`. `mise run setup` trusts the
  committed hook path and runs `git flow config sync`, and `npm run doctor`
  checks that the local Git config matches `.gitflow`.
- `.gitflow` configures only `main`, `develop` and `feature/`. Features merge
  with `--no-ff`, keep their branch, never fetch or push, and are updated from
  `develop` by merge, not rebase. Release and hotfix types are left out, so
  `git flow release` and `git flow hotfix` refuse to run; the constitution has
  releases and hotfixes finished by hand.
- Before the finish, a fresh reviewer from a provider other than the
  implementer's (Claude Code, Codex, Copilot, Antigravity, Grok or Cursor),
  given only the scope and requirements, reviews the feature tip, favoring
  speed. After its findings are resolved, a content-free commit records the
  review:

  ```sh
  git commit --allow-empty -m 'chore(review): record develop merge review' \
    -m "Reviewed-by: <reviewer, for example provider and model>
  Reviewed-commit: $(git rev-parse HEAD)"
  ```

  Any later commit on the feature, including a merge of `develop`, needs a new
  review and a new record.
- Run `git flow feature finish <name>` in the `develop` worktree. The hook
  `scripts/git-flow-hooks/pre-flow-feature-finish` refuses the finish unless
  that worktree is on `develop` with no uncommitted changes, `develop` is an
  ancestor of the feature, the feature is checked out in a clean worktree, its
  tip is a review record, and `npm run verify` passes there. A review record has one parent and the same tree as
  that parent, exactly one non-empty `Reviewed-by` trailer, and exactly one
  `Reviewed-commit` trailer that resolves to the parent. The merge then has
  Git's default message, its parents are `develop` and then the review record,
  and its tree is the reviewed and verified feature tree. `npm run
  test:git-flow` checks these cases with the real binary.
- Orca's setup script gives a new worktree's branch its git flow name, because
  `orca worktree create` has no branch option and turns a `/` in `--name` into
  `-`. `scripts/worktree-branch.sh` maps the worktree's folder name:
  `release-<rest>` becomes `release/<rest>`, `hotfix-<rest>` becomes
  `hotfix/<rest>`, and any other name becomes `feature/<name>` without a
  leading `feature-`. It renames only a branch that has no upstream and no
  commits of its own, never `develop` or `main`, and changes nothing on a
  second run; folder names stay flat. Remove the script and its setup line
  once `orca worktree create` offers a branch option. `npm run
  test:worktree-branch` checks it.
- Not automated: deciding that a feature is ready, running the merge review,
  updating a feature after `develop` moves (merge `develop` into it, verify,
  review, then finish again), resolving conflicts, releases, hotfixes, the
  review before a release or hotfix merges into `main`, and pushing.

### Commit messages — 2026-09-27

Every commit in a set-up worktree passes the `commit-msg` hook that lefthook
2.1.15 (<https://github.com/evilmartians/lefthook>, MIT) installs from the
`.config/lefthook.yml`. It runs commitlint 21.2.3
(<https://github.com/conventional-changelog/commitlint>, MIT) with
`@commitlint/config-conventional` and the Conventional Commits parser preset
from `conventional-changelog-conventionalcommits` 10.4.0, pinned in
`package.json` and `package-lock.json`.

- Headers must follow Conventional Commits 1.0.0 as `config-conventional`
  defines it. Any trailer is accepted, including `Spec-Kit-Task`,
  `Reviewed-by`, `Reviewed-commit` and `Co-Authored-By`. commitlint's default
  ignores skip Git's default merge messages, so git-flow finishes and
  hand-finished merges pass. At commit time, commitlint's default ignores also
  skip other messages, such as those starting with `fixup!`, `squash!`,
  `amend!`, `Revert ` or `Reapply `.
- The constitution's version rule (see its Governance section) is not
  checked by a hook. The author writes the new version with commitizen 4.19.0
  (<https://github.com/commitizen-tools/commitizen>, MIT): `npm run
  constitution:bump -- PATCH`, `MINOR` or `MAJOR` rewrites the `**Version**:`
  line and the version in `[tool.commitizen]` of `pyproject.toml`, with no commit, tag, changelog or hooks.
  Reviewers check that the step matches the commit type. `tools/commitizen/`
  is a uv project whose `uv.lock` pins it.
- The configuration is `scripts/commitlint.config.mjs`. commitlint loads a
  TypeScript configuration through jiti, which cannot resolve `npm:`
  specifiers, and resolves the preset's package name with `require.resolve`,
  which needs `node_modules`; so the configuration is plain JavaScript and
  passes the preset's parser options directly.
- lefthook installs its hooks into the Git hooks folder that all worktrees
  share, and each hook reads the running worktree's `.config/lefthook.yml` and runs
  its npm-installed native `node_modules/lefthook-<os>-<arch>/bin/lefthook`,
  without requiring Node to launch. When a worktree lacks that binary, the hook
  refuses the commit (`assert_lefthook_installed`) instead of skipping the
  check, and lefthook never installs itself (`no_auto_install`). Checkout
  and merge hooks quietly skip when that native binary is missing;
  new worktrees still use the existing setup
  and manual trust path until dependencies are installed. Because the
  hooks are shared, they are installed once, by hand, from the `develop`
  worktree with `./node_modules/.bin/lefthook install` (again only when
  lefthook, its launcher or configured hook names change); Orca's setup script does not install them, and `npm run
  doctor` checks the installation.
- `npm run test:commit-msg` checks commit messages through lefthook in
  temporary repositories, including linked worktrees. It also checks guarded
  mise trust with Node and Python unavailable: post-checkout and post-merge
  renew trust for `.config/mise.toml` only when its current regular-file bytes
  equal committed local `develop`. Branch checkout and merge skip unchanged
  configuration; file-only checkout has no prior-byte snapshot and safely
  renews matching trust even when unchanged. Differing feature or dirty bytes,
  missing develop and symlinks remain manually trusted.

### Linear — 2026-09-27

The project tracks its work in Linear's free plan, in the workspace
`verbose-broccoli` with one team, `cherry-pick-foundation` (key `CHE`), and
reaches it only through Orca: the `orca linear` commands and Orca's
`orca-linear` skill. No Claude Code or Codex Linear plugin and no Spec Kit
Linear extension is used. The design and its reasons are in
[specs/007-linear-usage/](../specs/007-linear-usage/).

- An issue is a to-do entry for one feature or bug; `tasks.md` stays the
  detailed task record. There are no sub-issues. Each issue has one type label
  (Feature, Bug or Improvement) and a plugin label (`code`, `work`, `chat`) for
  each plugin the work concerns; repository-wide tooling has none.
- Only the develop orchestrator writes to Linear, after searching for similar issues,
  including archived ones (`orca linear list-issues --team CHE --query <words>
  --include-archived`). Workers report out-of-scope bugs to it through Orca
  messages. Linear is an external service, so issues and comments never hold
  operational data or secret values. Both rules are in the root `AGENTS.md`.
- A feature's worktree is linked to its issue when it is created (`orca
  worktree create … --linear-issue CHE-<n>`, or `orca worktree set` later),
  and its spec names the ID in one header line, `**Linear issue**: CHE-<n>`.
  The Spec Kit preset `linear-issue` in `.specify/presets/` appends that line,
  with instructions, to the spec template. Commits and branch names carry no
  issue ID; a bug's `assessment.md` keeps the issue URL.
- Merging into `develop` completes the issue. The feature orchestrator commits
  its record on the feature branch and obtains the merge review. The develop
  orchestrator moves the issue to In Review and grants the serialized finish
  slot; the feature orchestrator runs the finish described under
  [Git flow](#git-flow--2026-09-27). Develop then moves the issue to Done with one completion comment giving the merge commit
  and the record location instead of a PR link. `npm run workflow` prints
  this order in every mode. The commands are in
  [the life-cycle contract](../specs/007-linear-usage/contracts/linear-lifecycle.md).
- Issues are archived, never deleted. The free plan counts only non-archived
  issues toward its limit of 250, and Linear archives closed issues one month
  after they close (Team Settings > Issue statuses & automations); archived
  issues stay readable with `--include-archived`. Nothing monitors the count:
  a failed creation at the limit is the signal, and the develop orchestrator reports it
  to the user.
- Orca cannot archive or delete issues or create labels, projects, documents,
  cycles or milestones. Label, project and team-setting changes happen in
  Linear's UI, and no other Linear integration is added; the same `npm run
  workflow` instruction says so.

### Document consistency — 2026-09-28

`README.md`, `docs/architecture.md` and `docs/jev-mcp.md` follow one region
model, from [feature 008](../specs/008-doc-consistency/spec.md). Every part of
these target documents is either a mechanical region, written by a generator,
or an agent region, written by agents. No part is human-written.

- A mechanical region is a Cog block (cogapp 3.6.0, MIT) in HTML comments. Its
  code is one call of a function in `scripts/doc_sources.py`, whose arguments
  name the repository files or globs it reads. The marker syntax and its rules
  are in the [regions contract](../specs/008-doc-consistency/contracts/regions.md).
  Documents link to it instead of quoting a marker, because Cog would run a
  quoted marker as a region.
- Everything else is an agent region. Jev MCP judges it before each `develop`
  merge review.
- `scripts/doc-regions.toml` lists the targets, including the generated
  `docs/reference/` pages, and root and area `AGENTS.md` files and the
  constitution as report-only documents. `specs/` and vendored skills are not
  listed. Other plugin documents become targets when explicitly configured.
- To add a mechanical region, add a function to `scripts/doc_sources.py` and a
  test to `scripts/doc_sources_test.py` with fixture sources, the exact output,
  and a missing source that raises. The function reads only its named sources
  and uses no network, clock or environment; `command_help` runs each named
  command with `--help` in a fixed environment. Then put the markers around the
  text in a target and run `npm run doc-regions:update`.
- `npm run check`, and so `npm run verify`, runs `npm run
  doc-regions:check`. It fails when a region differs from its generator's
  output, a marker is malformed or names a missing source, or a target links
  to a missing local file or heading (lychee 0.24.2, offline). It writes
  nothing and uses no network. `npm run doc-regions:update` regenerates
  stale regions.
- Before each `develop` merge review, the feature orchestrator runs the judgment step
  that `npm run workflow` prints in REVIEW mode. `npm run
  doc-regions:prepare -- --base develop --max-evidence-chars <n>` splits the
  agent regions into units with markdown-it-py 4.2.0 (MIT). It prints
  `jev_verify` requests, with units as claims and the feature diff as
  evidence, and `jev_classify` requests for the units the feature added.
  Korean text is allowed; no provider-era Hangul transliteration is required.
  `--max-evidence-chars` bounds the total evidence text in each generated
  `jev_verify` request. Evidence groups keep all evidence, so claim and unit IDs
  repeat across groups. Consider every group's formal verdict and action for
  each repeated claim ID: a verified result in one group must not hide a
  contradiction or an unresolved review from another. Unsupported is silence.
  Treat a subject-demoted relation flag as unsupported and needing review,
  never as a formal contradiction. When a claim stands, record the reason or
  disposition. No code combines the results.
  Send requests through the gated `jev-mcp` proxy.
  Each `jev_verify` request holds at most 110 claims and 12,000 claim
  characters, below the sizes OpenRouter refused (the real limit is not
  published); a longer claim stops the command with an error naming it.
  The agent sends them through its MCP client. It corrects target units judged
  contradicted or flagged for review, or records why they stand, and decides
  which suggested candidates become mechanical regions.
- `npm run doc-regions:audit` runs MemoryLint 1.5.1's read-only audit (MIT)
  on root and area `AGENTS.md` files and the constitution. It downloads the pinned archive once
  into `~/.cache/verbose-broccoli/memorylint/1.5.1/` after a hash check.
  Findings for these rule files, from the audit or from Jev MCP, are only
  reported to the user; the tooling never changes them.
- The engine is the uv project `packages/doc-regions/`. `mise run setup`
  syncs it, `npm run doctor` checks its environment, and mise pins lychee.
  Feature 010 calls its modules as a library, with a Wiki instance as the root
  and its own targets, generators and evidence.
- Not automated: sending the Jev MCP requests and acting on the results,
  reporting drift in root and area `AGENTS.md` files and the constitution, and
  choosing which candidates become mechanical regions.
