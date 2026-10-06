# Research: Clean Architecture Tool Collection

This record lists what each reference document decides or constrains for the
redesign, the dated user decisions the design rests on, and the upstream tools
checked for delivery. The specification and plan cite the rows here by their
ID (for example `R-REPO-01` or `U-2026-10-06a`).

## Method

- The user collected the references in four folders under
  `~/Documents/web-captures/` and named six Clean Architecture sources cached
  in `~/.cache/verbose-broccoli/workspaces/develop/clean-architecture-structure/`.
- HTML and PDF captures were converted with the repository's
  `.venv/bin/markitdown` (markitdown 0.1.8) into session scratch. Locations
  below name the section heading of the original page, with the line range in
  the converted text where a section is long. The converted text is
  reproducible with the same command; it is not committed.
- Every document was read in full on 2026-10-06. Five network-design
  documents do not apply; their rows say why.
- Each structural decision in [spec.md](spec.md) and the plan cites a row
  here or a dated user decision. The citations were checked against the
  extracted passages with Jev; see [Citation check](#citation-check).

## Dated user decisions

| ID | Date and source | Decision |
| --- | --- | --- |
| U-2026-10-06a | 2026-10-06 04:42 KST, main-session conversation | Retire the Agent Plugins (AAIF) implementation, because Claude Code does not load Agent Plugins, and build the capabilities as a collection of tools that agents use. |
| U-2026-10-06b | 2026-10-06 04:42–04:48 KST, proposed by the main session, not yet confirmed by the user | Agent Skills folders for instructions; tools as command-line programs, or FastMCP servers where a tool needs a running process, a login or a filter in front of it; Pydantic AI for model calls inside tools; Vercel's `skills` and Neon's `add-mcp` to install into each agent; leave out Claude Code's own plugin format, Agent Plugins and small all-in-one managers. Open choices go to the user in clarification. |
| U-2026-10-06c | 2026-10-06, relayed by the develop-worktree session | Redesign the repository as a Clean Architecture project: component packages with ports and adapters inside each (domain without I/O, application with use cases and ports, adapters, one composition root reading XDG settings). One package per ring was rejected. Delivery is skills, command-line tools and MCP servers, not plugin roots. |
| U-2026-10-06d | 2026-10-06 | GLM (Z.ai's model on Hive) and Jev are used heavily from the first version; cost is no constraint. One judgment port; configuration chooses Jev on OpenRouter (`typesafe/jev-1.13`) or GLM 5.3 Flash on Hive through TypeSafe's `system-one-adapter` as a System One-compatible endpoint. GLM needs a timeout far above 60 seconds. The education privacy gate sits in front of either backend for student data. Worker model choice stays Jev-only. `system-one-adapter` needs a read-only security review before adoption. |
| U-2026-10-06e | 2026-10-06 | Approved replacement trials: Jev Browser for `packages/jev-ultrafast`, rulesync for `scripts/plugin-clients.ts`, chezmoi for `scripts/secrets-refresh.ts`, session-scan for `session_select.py`. Trial results return to the user before anything is replaced. |
| U-2026-10-06f | 2026-10-06 about 18:30 KST, the orchestrator brief relayed by the develop-worktree session for the user | Small slices, each reviewed and merged on its own; the specification and plan first, with an estimate of locally owned code shown to the user before building. Code that open branches change waits (`plugins/work`, `packages/wiki-consistency`, `packages/jev-ultrafast`); code a trial may replace is left out; the privacy gate waits for its reported metadata bug. Plan the constitution amendment as its own slice and show its text to the user. Behavior is kept, with the same tests passing before and after. |
| U-2026-09-30a | 2026-09-30 | New file and folder names use kebab-case, except names a language, tool or standard fixes. |
| U-2026-10-04a | 2026-10-04 | A skill taken from upstream keeps its upstream name. |
| U-2026-10-04b | 2026-10-04 | Commands Turborepo runs as tasks live in `turbo.json` task commands; `package.json` keeps hand-run entry points. The user accepted that the `command` option is experimental. |

## Clean Architecture sources

| ID | Document | What it contributes | Where |
| --- | --- | --- | --- |
| R-CA-01 | Martin, *The Clean Architecture* (2012) | The dependency rule: source dependencies point inward only, and inner code never names outer code. Use cases hold application rules; adapters convert data; frameworks are tools kept at the edge. Simple data structures cross boundaries. The number of rings is schematic; the rule always applies. Output ports let an inner ring call outward through an interface. | "The Dependency Rule"; "Use Cases"; "Interface Adapters"; "Only Four Circles?"; "Crossing boundaries"; "What data crosses the boundaries" |
| R-CA-02 | Cockburn, *Hexagonal Architecture* (2005) | An application driven equally by people, programs, tests and batch scripts, testable without its devices. A port is a purposeful conversation with several adapters, including test doubles. Primary (driving) and secondary (driven) ports. Two to four ports is typical. Interfaces are designed by purpose, not technology. Wiring by passing the adapter into the application. | "Intent"; "Nature of the Solution"; "The Left-Right Asymmetry"; "How Many Ports?"; "Known Uses"; "Sample Code" stage 3 |
| R-CA-03 | Brown, *Package by component* (Clean Architecture's missing chapter) | Package by component bundles a capability's logic and persistence behind one interface, with the user interface kept separate. Rules enforced by tooling or the compiler beat discipline. One source tree per ring is "idealistic" with real cost. The Périphérique anti-pattern: a shared outer tree lets adapters call each other past the domain. Public versus published types. | "Package by component"; "The devil is in the implementation details"; "Other decoupling modes"; "Summary" |
| R-CA-04 | Percival and Gregory, *Cosmic Python*, appendix B | A Python project as `src/<package>/` with `domain/`, `service_layer/`, `adapters/` and `entrypoints/`, a `config.py` read from the environment with local defaults, the bootstrap script as the only importer of configuration, and tests split into `unit`, `integration` and `e2e`. | "Project tree"; "Config.py"; "Installing Your Source as a Package"; "Tests" |
| R-CA-05 | Anthropic, *Building effective agents* (2024) | Start with the simplest solution and add complexity only when it helps; frameworks can hide prompts, so understand them before use. Tools reach models through MCP. Invest in the agent-computer interface: tool documentation, testing and mistake-proof arguments. | "When (and when not) to use agents"; "When and how to use frameworks"; "Building block: The augmented LLM"; "Appendix 2: Prompt engineering your tools" |
| R-CA-06 | Hive, *Chat Completions (OpenAI-Compatible LLMs)* | Hive serves `zai-org/glm-5.3-flash` and `deepseek-ai/deepseek-v4.1-flash` through an OpenAI-compatible streaming endpoint at `https://api-cdn.thehive.ai/api/v3`; no Jev model. Rate limit 5 requests per second (429); an organization without credit gets 405. | "Available Models"; "Coding Agents"; "Common Errors" |

## Repository conventions (2026-10-06-repo-conventions)

| ID | Document | What it contributes | Where |
| --- | --- | --- | --- |
| R-REPO-01 | Turborepo, *Structuring a repository* | `apps/` for applications and services, `packages/` for libraries and tooling; every folder with a manifest under the globs is a package; no nested packages; a package is a small project with its own manifest, tool configuration and source; `exports` names the entry points and avoids barrel files; avoid `../` across package boundaries and install the package instead. | "Declaring directories for packages"; "Anatomy of a package"; "`exports`"; "Common pitfalls" |
| R-REPO-02 | Turborepo, *Configuring tasks* | A task runs the same-named script in each package; Root Tasks serve root linting, incremental migration and scripts without a package; a package may carry its own `turbo.json`. | "Defining tasks"; "Registering Root Tasks"; "When to use Root Tasks"; "Using Package Configurations" |
| R-REPO-03 | Turborepo, *Configuring turbo.json* | Package Configurations extend the root; the local cache is shared across Git worktrees; strict environment mode is the default; `boundaries` rules allow or deny dependencies between tagged packages; a `description` field documents tasks for agents. The page does not document the `command` task option the repository uses. | "`extends`"; "`cacheDir`"; "`envMode`"; "Boundaries"; "`description`" (converted lines 116–1460) |
| R-REPO-04 | Turborepo, *Internal Packages* | Workspace packages are installed and imported like registry packages. A Just-in-Time package exports TypeScript directly when the consumer understands TypeScript natively, needs no build step, and uses subpath imports instead of TypeScript paths. | "Compilation Strategies"; "Just-in-Time Packages" |
| R-REPO-05 | Turborepo, *Python (Experimental)* | With `experimentalPythonWorkspaces`, uv workspace members become graph packages, with built-in `lint`, `check` and `test` tasks mapped to Ruff, type checkers and pytest; custom uv tasks need `experimentalTaskCommand`. | "Enable uv workspaces"; "Built-in tasks"; "Create your own tasks"; "Caching behavior" |
| R-REPO-06 | uv, *Using workspaces* | Members each have a `pyproject.toml` and share one lockfile; members may be applications or libraries; the layout example puts libraries in `packages/<name>/src/<import_name>/`; uv itself keeps its core library and its command-line interface in separate packages to test them apart; uv cannot stop a member importing another member's undeclared dependencies. | "Getting started"; "Workspace layouts"; "When (not) to use workspaces" |
| R-REPO-07 | uv, *Project structure and files* | `pyproject.toml` marks a project root and declares entry points (commands); `.venv` stays out of version control; `uv.lock` is committed and managed only by uv. | "The `pyproject.toml`"; "The project environment"; "The lockfile" |
| R-REPO-08 | PyPA, *src layout vs flat layout* | The `src/` layout keeps importable code apart from the project root, so tests use the installed package and only intended files are importable; a command-line program then runs from an installation. | Whole page; "Running a command-line interface from source with src-layout" |
| R-REPO-09 | npm, *Workspaces* | Workspaces are folders with a `package.json` listed in the root `workspaces` field, linked into `node_modules`; one workspace depends on another with `npm install <b> -w <a>`; commands run per workspace with `-w` or `--workspaces`. | "Defining workspaces"; "Adding dependencies to a workspace"; "Running commands in the context of workspaces" |
| R-REPO-10 | Node.js, *Modules: Packages* (v26) | A package is the folder tree up to the next `package.json`; always set `"type"`; `"exports"` defines the public interface and blocks other subpaths; `null` targets hide private folders; `"imports"` (`#…`) gives private in-package aliases; `.ts` files load as TypeScript. | "Introduction"; "Package entry points"; "Subpath imports"; "Subpath patterns"; "Determining module system" |
| R-REPO-11 | mise, *Configuration* | `.config/mise.toml` is an accepted grouped location; configuration files in parent folders merge with the child winning; `[tool_config] locked = true` forces tools from the lockfile; mise follows XDG folders. | "`mise.toml`"; "How Configuration Merging Works"; "`[tool_config]`"; "Environment variables" |
| R-REPO-12 | AGENTS.md format | A README for agents in plain Markdown; nested `AGENTS.md` files per package in a large repository, the nearest file winning and the user's prompt overriding; agents run the checks the file lists. | "How to use AGENTS.md?" item 4; FAQ |
| R-REPO-13 | Agent Plugins 1.0 specification | A plugin is a folder with `plugin.json`, `skills/` and `mcp.json`; only Agent Skills and MCP servers are portable component types because both have external specifications and cross-client adoption; skills must follow the Agent Skills specification. Retired here by U-2026-10-06a; its point that the portable units are skills and MCP servers still holds. | §4.2, §6.1, §7, §7.1; "Why only Agent Skills and MCP in v1?" |
| R-REPO-14 | Spec Kit README | Constitution once, then specify, plan, tasks, implement and converge per feature, repeating implement and converge until converged; clarification, checklists and analysis add quality gates. | "Spec-Driven Development" |
| R-REPO-15 | Conventional Commits 1.0.0 | Scope is a noun naming a section of the codebase; a breaking change carries `!` or a `BREAKING CHANGE` footer; a commit that fits several types should be split. | Specification items 4, 11–13; FAQ "more than one of the commit types" |
| R-REPO-16 | Semantic Versioning 2.0.0 | Software must declare a public API; 0.y.z is initial development where anything may change; deprecate in a minor release before removing in a major one. | Specification items 1, 4, 5; FAQ "How should I handle deprecating functionality?" |
| R-REPO-17 | Keep a Changelog 1.1.0 | A changelog is a curated list of notable changes per version, with an Unreleased section and Removed and Deprecated entries. No release has happened yet, so no changelog is added by this feature. | "Guiding Principles"; "Types of changes"; "How can I reduce the effort…" |
| R-REPO-18 | EditorConfig specification 0.17.2 | `.editorconfig` files apply from the file's folder upward until `root = true`, closer files winning. The existing root file covers new packages; a nested one only where a language needs it. | "File Processing"; "Supported Pairs" |
| R-REPO-19 | Git, *gitignore* | Patterns live in `.gitignore` in any folder and apply relative to it; shared patterns in the repository, personal ones in `$XDG_CONFIG_HOME/git/ignore`. Package-local build output may be ignored by the package's own file or the root file. | "DESCRIPTION"; "PATTERN FORMAT" |
| R-REPO-20 | Git, *gitattributes* | Per-path attributes with later lines and closer files winning; `text=auto`, `-diff`, `export-ignore` and macros. No restructuring need for them was found; not applied. | "DESCRIPTION"; "EFFECTS"; "USING MACRO ATTRIBUTES" |
| R-REPO-21 | GitHub, *Default community health files* | CONTRIBUTING, SECURITY and similar files are found in `.github/`, the root or `docs/`; a license must live in each repository. Adding them is outside this feature; not applied. | "About default community health files"; "Supported file types" |
| R-REPO-22 | dot-config proposal | Keep project tool configuration in `.config/` to declutter the root, as an extension of XDG. The repository already follows it; new tool configuration goes there when the tool supports it. | Whole page |

## Operating-system conventions (2026-10-06-os-conventions)

| ID | Document | What it contributes | Where |
| --- | --- | --- | --- |
| R-OS-01 | XDG Base Directory Specification 0.8 | Separate data, configuration, state, cache and runtime base folders; relative values are invalid and ignored; defaults `~/.local/share`, `~/.config`, `~/.local/state`, `~/.cache`; state holds history and resumable state; runtime folder is `0700` and cleared at logout; create missing folders with `0700`; skip unreadable folders when reading. | "Basics"; "Environment variables"; "Referencing this specification" |
| R-OS-02 | Filesystem Hierarchy Standard 3.0 | Files that differ in being shareable or static belong in different folders; caches must be rebuildable and deletable without data loss; state is data programs change, never user-edited configuration. System-level; used only as the rationale for the XDG split. | §2 "The Filesystem"; §3.8 "/home"; §5.5 "/var/cache"; §5.8 "/var/lib" |
| R-OS-03 | UAPI.9 Linux File System Hierarchy | For packages installed in a user's home: configuration in `~/.config/<package>/` must fall back to safe defaults when missing; cache, state and runtime folders per package; `~/.local/bin` only for programs people run from a shell; temporary files with `mkstemp`-style calls and `$TMPDIR`; programs should keep working without write access to cache or logs. | "Home Directory"; "User Packages"; "`/tmp/`"; "Lack of Write Access…" |
| R-OS-04 | systemd, *Using /tmp/ and /var/tmp/ Safely* | Never use guessable names in shared temporary folders; honor `$TMPDIR`; temporary files age out after 10 or 30 days; prefer unlinked files, locks or a folder under `$XDG_RUNTIME_DIR`. | "Common Namespace"; "Automatic Clean-Up" |
| R-OS-05 | freedesktop, *Desktop Application Autostart* | Login autostart through `.desktop` files in `$XDG_CONFIG_HOME/autostart`. No tool here starts at login; not applied. | §2 |
| R-OS-06 | freedesktop, *Desktop Entry Specification* 1.5 | `.desktop` naming and the `Exec` key. Only the existing reference-library shortcut in `infra/` uses it, and this feature leaves `infra/` unchanged; not applied. | §2; §7 |
| R-OS-07 | freedesktop, *Trash Specification* 1.0 | Home trash in `$XDG_DATA_HOME/Trash` with `files/` and `info/`. No tool in scope moves user files to the trash; not applied. | "Trash directories"; "Contents of a trash directory" |
| R-OS-08 | Debian Policy, chapter 9 | Programs on `PATH` must give reasonable defaults without custom environment variables; user configuration as a dot file or dot folder; never rely on `/usr/local` contents. | §9.1.1 item 2; §9.9 "Environment variables" |
| R-OS-09 | PEP 370 | Per-user installs use `~/.local`, with commands in `~/.local/bin`. | "Specification" |
| R-OS-10 | npm, *Folders* | Install locally to import a package, globally to run it from the command line; local commands are linked into `node_modules/.bin`, global ones into `{prefix}/bin`. | "tl;dr"; "Executables" |
| R-OS-11 | Cargo, *Cargo Home* | A tool home that mixes configuration, credentials, programs and caches in one folder. No Rust code here; an example of a tool keeping its own supported location; not applied. | Whole page |
| R-OS-12 | mise, *Directory Structure* | Each folder resolves a tool-specific override first, then the XDG variable plus the tool name, then the default; configuration, cache, state and data stay separate, because cache cleanup deletes contents. | "Directory Structure" table and notes |
| R-OS-13 | Flatpak, *Sandbox Permissions* | Sandboxed applications store cache, configuration and state in XDG folders and avoid sharing configuration with other installs. Nothing here ships as Flatpak; not applied. | "Filesystem access" |
| R-OS-14 | Snap, *Data locations* | Per-application user data folders and snapshots on removal. Nothing here ships as a snap; not applied. | "User data" |

## Google guides (2026-09-29-google-guides)

| ID | Document | What it contributes | Where |
| --- | --- | --- | --- |
| R-GG-01 | Engineering practices, *Small CLs* | A change is one self-contained thing with its tests that keeps the system working; about 100 lines is reasonable and 1,000 usually too large; deleting a whole file counts as about one line; refactorings go in their own change apart from behavior changes; missing tests go in first so a later refactoring can show unchanged behavior; split by stacking, files, layers or features. | "What is Small?"; "When are Large CLs Okay?"; "Splitting CLs"; "Separate Out Refactorings"; "Keep related test code in the same CL" |
| R-GG-02 | Engineering practices, *Writing good CL descriptions* | The first line says what the change does as a short imperative; the body says why; "Moving code from A to B" and "Phase 1" are poor descriptions. | "First Line"; "Body is Informative"; "Bad CL Descriptions" |
| R-GG-03 | Engineering practices, *How to handle reviewer comments* | Answer a reviewer by clarifying the code or adding a comment, not only by replying in the tool. | "Fix the Code" |
| R-GG-04 | Engineering practices, *The Standard of Code Review* | Approve a change that improves overall code health even if imperfect; design questions rest on principles, not taste. | "The Standard"; "Principles" |
| R-GG-05 | Engineering practices, *What to look for in a code review* | Watch for over-engineering and solve today's problem; tests in the same change; update READMEs and generated reference documents when building, testing or use changes. | "Complexity"; "Tests"; "Documentation" |
| R-GG-06 | Engineering practices, *Navigating a CL in review* | Say "no" to a wrong direction early, before much work is done; review the main part first. | "Step One"; "Step Two" |
| R-GG-07 | Engineering practices, *Speed of Code Reviews* | Optimize for team speed; ask for large changes to be split. | "Why Should Code Reviews Be Fast?"; "Large CLs" |
| R-GG-08 | Engineering practices, *How to write code review comments* | Explain why and label severity (Nit, Optional, FYI). | "Explain Why"; "Label comment severity" |
| R-GG-09 | Engineering practices, *Handling pushback* | Clean up now rather than later; new complexity is removed before submission or tracked as a bug. | "Cleaning It Up Later" |
| R-GG-10 | Google documentation guide, *Best practices* | Minimum viable documentation; update documents in the same change as the code; delete dead documentation; a README per folder says what it holds and which files to read first; design documents become archives once code exists. | "Minimum Viable Documentation"; "Update Docs with Code"; "Delete Dead Documentation"; "Documentation is the Story of Your Code" |
| R-GG-11 | Google documentation guide, *Markdown style* | One H1, short introduction, unique headings, fenced code with a language, informative link text, tables only for tabular data. | "Document layout"; "Headings"; "Code"; "Links"; "Tables" |
| R-GG-12 | *Software Engineering at Google*, ch. 11 *Testing Overview* | Tests have a size (resources) and a scope (code validated); small tests run in one process without disk or network; tests are hermetic; roughly 80% narrow, 15% integration, 5% end-to-end; a behavior-preserving refactoring should need no test change. | "Test Size"; "Test Scope"; "Benefits of Testing Code" |
| R-GG-13 | ch. 12 *Unit Testing* | The ideal test never changes during pure refactoring; test through public interfaces, test state rather than interactions, prefer real objects that are fast and deterministic; DAMP over DRY in tests. | "Strive for Unchanging Tests"; "Test via Public APIs"; "Test State, Not Interactions" |
| R-GG-14 | ch. 13 *Test Doubles* | Seams through dependency injection; in Python and JavaScript, replacing functions makes injection less important; use real implementations first; fakes are the preferred double, written at the root of the dependency that cannot run in tests and kept honest by contract tests run against both the fake and the real one; tests should reuse the production construction code. | "Seams"; "Real Implementations"; "Dependency construction"; "Faking"; "Fakes Should Be Tested" |
| R-GG-15 | ch. 14 *Larger Testing* | Configuration is a top cause of outages, so test that each program starts with its configuration; third-party paid APIs are a seam and stay out of automated tests; record and replay or contract tests keep doubles honest; A/B comparison of old and new output suits migrations; make internal timeouts configurable. | "Configuration issues"; "Reducing the size of your SUT at problem boundaries"; "Record/replay proxies"; "Deployment Configuration Testing"; "A/B Diff Regression Testing"; "Speeding up tests" |
| R-GG-16 | ch. 23 *Continuous Integration* | Run only fast, reliable tests before submission and keep slow or nondeterministic ones apart; small repositories avoid mid-air collisions by serializing submissions; hermetic tests and fakes keep the presubmit stable; check that each configuration starts. | "Presubmit versus post-submit"; "Why presubmit isn't enough"; "Hermetic Testing"; "Scenario #1" |
| R-GG-17 | Google TypeScript Style Guide | Relative imports within a project and few `../` steps; named exports only; export only what other modules use; no container classes; split an interface from its implementation (`UserService` and `AjaxUserService`); interfaces are named for why they exist, without an `I` prefix. Its snake_case file names do not override the user's kebab-case rule (U-2026-09-30a). | "Import paths"; "Exports"; "Export visibility"; "Export type"; "Naming style"; "Imports" under Naming |
| R-GG-18 | *Site Reliability Engineering*, *Postmortem Culture* | Blameless reviews that fix systems and processes, with root causes and actions. Applied in [Lessons from the first attempt](#lessons-from-the-first-attempt). | "Google's Postmortem Philosophy"; "Best Practice: Avoid Blame…" |

## Network design (2026-10-06-network-design)

These five documents describe network hardware for the academy, not software
or repository structure. None applies to this feature.

| ID | Document | Why it does not apply |
| --- | --- | --- |
| R-NET-01 | CISA, *Layering Network Security Through Segmentation* (2022) | Network segmentation, demilitarized zones and firewalls. |
| R-NET-02 | Cisco, *Unified Branch Small Branch Deployment Guide* (2026) | Branch routers, switches and access points managed from the Meraki dashboard. |
| R-NET-03 | Meraki, *Small Office Business Reference Architecture* | Office topology, subnets, VLANs, DHCP, firewall and VPN settings. |
| R-NET-04 | NSA, *Network Infrastructure Security Guide* v1.2 (2023) | Device hardening: perimeter, access control, passwords, logging, SSH administration. |
| R-NET-05 | Oppenheimer, *Top-Down Network Design*, 3rd ed., sample pages | Requirements-first network design and the three-layer network model; its requirements-first point is already Spec Kit's process (R-REPO-14). |

## Upstream tools checked for delivery

Read on 2026-10-06 from each project's README; adoption still needs the
read-only security review that root `AGENTS.md` requires.

| ID | Tool | Facts that matter here |
| --- | --- | --- |
| R-UP-01 | Agent Skills specification (`agentskills/agentskills`, Apache-2.0) | A skill is a folder with `SKILL.md` whose `name` (lowercase letters, digits and single hyphens, at most 64 characters) matches the folder; optional `scripts/`, `references/` and `assets/`; keep `SKILL.md` under 500 lines; `skills-ref validate` checks a skill. |
| R-UP-02 | Vercel `skills` command (`vercel-labs/skills`, MIT) | Installs from a GitHub repository or a local path; finds skills in `skills/`, `.agents/skills/`, `.claude/skills/` and others, up to `skills/<category>/<category>/<name>/`; project installs go to `.claude/skills/` for Claude Code and `.agents/skills/` for Codex, global ones to `~/.claude/skills/` and `~/.codex/skills/`; symlinks by default; `metadata.internal` hides a skill; sends anonymous telemetry for public repositories unless `DISABLE_TELEMETRY=1`. |
| R-UP-03 | Neon `add-mcp` (`neondatabase/add-mcp`, Apache-2.0) | Registers a stdio or remote MCP server in Claude Code (`.mcp.json` or `~/.claude.json`), Codex (`.codex/config.toml` or `~/.codex/config.toml`) and others; can pre-approve tools but has no option for denying or disabling tools; `--timeout` applies to remote servers only. |
| R-UP-04 | rulesync (`dyoshikawa/rulesync`, MIT) | Generates rules, MCP, commands, subagents, skills, hooks and permissions for Claude Code, Codex and many other tools from one `.rulesync/` source; its rules feature can write tool-specific instruction files, which this repository must not have (`CLAUDE.md`), so that feature would stay off. |

## Lessons from the first attempt

The first orchestrator's records (commit `5f9ab81`) kept the three plugin
roots as Agent Plugins packages. The cause was systemic, not personal: the
2026-10-06 04:42 decision to retire Agent Plugins existed only in a main
session's conversation and never reached the repository's records or the
orchestrator's brief, and no reference study preceded the specification.
This attempt addresses both: every structural decision cites a row above or
a dated user decision, and the user decisions table records the conversation
decision with its time.

## Citation check

On 2026-10-06 each row's attributions were split into 219 short claims and
sent with the cited passages to `jev_verify` through the gated `jev-mcp`
server (Jev `typesafe/jev-1.13` on OpenRouter, the plain-client route of the
model-choice reference), in 13 requests:

- 217 claims verified with confidence of at least 0.8, 2 verified with lower
  confidence (R-REPO-06 on the layout example, whose wording was then
  narrowed, and R-REPO-08 on running a command from a `src` layout), and none
  contradicted or unsupported.
- A second request checked the specification's 19 cited requirements against
  the rows and dated decisions they cite: all 19 verified.

The same requests were also sent to GLM 5.3 Flash on Hive through the same
gate as a second opinion; its result is recorded below when complete.

The inputs, scripts and raw answers are kept outside the repository in
`$XDG_STATE_HOME/verbose-broccoli/workspaces/feature-clean-architecture/citation-check/attempt-20261006T094848Z/`.
