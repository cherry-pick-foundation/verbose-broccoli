# Research: Repository Document Consistency

Probes ran on 2026-09-27 on Linux x86_64 with uv 0.11.32, Node 24.19.0 and the
tools named below, in the scratch directory outside the checkout. Repository
probes ran on a `git archive` copy of `develop` at `07a377d`. The brief is
`briefs/2026-09-27-linear-and-documents.md`, section 2; its decisions are
settled, and this file confirms only what it marks for research.

## R1. Mechanical regions: Cog

- **Decision**: Use Cog (`cogapp` 3.6.0 from PyPI, MIT, released 2025-09-21,
  Python 3.9 or later) for mechanical regions. Markers are HTML comments, so
  they do not render: `<!-- [[[cog ... ]]] -->` opens the generator code,
  `<!-- [[[end]]] -->` closes the output. `cog -r` regenerates in place;
  `cog --check --diff --check-fail-msg=<text>` checks without writing.
- **Rationale**: Probed on a scratch Markdown file whose region lists the
  tasks of a `deno.json`:
  - With a stale region, `--check --diff` printed `Check failed`, a unified
    diff of the region, and exited 5; the file's SHA-256 was unchanged.
  - `-r` rewrote only the region's lines; a following `--check` exited 0.
  - `-I <dir>` puts generator modules on the import path, so generators live
    outside the document.
  - Cog's documented options (<https://cog.readthedocs.io/en/latest/running.html>)
    include `--check-fail-msg`, which lets the failure name the regeneration
    command (FR-006).
- **Aider at commit `5dc9490`** (`5dc9490bb35f9729ef2c95d00a19ccd30c26339c`,
  2026-05-22), read from its raw files. This confirms the brief:
  - `scripts/update-docs.sh` passes `-r` or `--check` to one `cog` call that
    lists every target file, so the target list lives in one place.
  - `aider/website/docs/config/options.md` calls
    `aider.args.get_md_help()`; `aider_conf.md` calls `get_sample_yaml()` and
    also writes `aider/website/assets/sample.aider.conf.yml` from inside the
    block.
  - `README.md`'s block calls `scripts/homepage.py`'s `get_badges_md()`, which
    queries `api.pepy.tech` and `api.github.com`.
  - Outside `--check`, the script first copies `~/.aider/analytics.jsonl` into
    the site and regenerates `faq.md`, so its output also depends on local user
    data.
  So this repository keeps Aider's single target list and `--check`, but a
  mechanical region may only call a registered generator on named repository
  files (R2), and tests check that regeneration writes nothing else and uses
  no network.
- **Alternatives considered**:
  - Extending `scripts/docs.ts`: excluded by the brief, and it regenerates
    whole files, not regions.
  - Cog's checksum option (`-c`): it protects output against hand edits. The
    user decided there are no human-written parts, so it adds nothing.
  - markdown-magic, embedme or mdsh: each replaces regions but needs Node or
    Rust and a local generator protocol; Cog is Python, runs in the same uv
    environment as the unit splitter (R3), and is the tool the brief names.

## R2. How a mechanical region names its source

- **Decision**: The code of every mechanical region is exactly one statement,
  `import <module>; cog.out(<module>.<generator>("<source>", ...))`, where
  every string argument is a repository-relative source path or glob. The
  check parses the code with Python's `ast` module and refuses a region whose
  code is anything else, whose generator is not in the registered generator
  module, or whose source does not exist.
- **Rationale**: Decision 2 requires the marker to name its source. Cog runs
  arbitrary Python, which Aider's blocks use to write files and call the
  network (R1). Restricting the code to one call makes the source visible in
  the document and keeps side effects in reviewed, tested generator
  functions. `ast` is in the standard library, so the local code is a small
  shape check.
- **Alternatives considered**: A separate `source:` comment beside the Cog
  block, which could disagree with the call it describes; a registry of region
  ids in a config file, which would be a second place to edit.

## R3. Units for backfire: markdown-it-py

- **Decision**: Use markdown-it-py 4.2.0 (MIT, released 2026-05-07, Python
  3.10 or later, one dependency `mdurl`) with the `commonmark` preset and the
  `table` rule enabled. A unit is a top-level block token (heading, paragraph,
  list item of a top-level list, table, fenced or indented code, HTML block)
  with its heading path and its `map` line range. Mechanical regions are
  removed before splitting by their marker lines.
- **Rationale**: Probed on the scratch document from R1: the parser returned
  `heading_open [0, 1]`, `paragraph_open [2, 3]`, `html_block [4, 5]`,
  `bullet_list_open [5, 7]`, `html_block [7, 8]` and `paragraph_open [9, 10]`;
  each `map` is a zero-based, end-exclusive line range, and Cog's marker
  comments come out as their own `html_block` tokens, so region boundaries and
  units line up.
- **Alternatives considered**: `mdast` packages already in `deno.json`
  (`mdast-util-to-markdown`, `mdast-util-gfm-table`): usable from Deno, but the
  unit splitter must run in the same environment as Cog, and feature 010's
  Wiki tools are Python beside backfire. Splitting by blank lines: breaks on
  lists, tables and code.

## R4. Local links and paths: lychee

- **Decision**: Use lychee 0.24.2 (released 2026-05-01) as a pinned host tool
  at `~/.local/bin/lychee`, installed from the release archive
  `lychee-x86_64-unknown-linux-gnu.tar.gz` after checking it against the
  release's `.sha256` file (`1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a`).
  The check runs `lychee --offline --include-fragments --no-progress` on the
  target documents. `deno task doctor` checks its version, as it does for
  git-flow.
- **Rationale**: On `README.md` and `docs/architecture.md` at HEAD it found 13
  links, 10 OK, 3 external excluded, in under a second. On a scratch file it
  reported a missing local file and a missing heading fragment (`Cannot find
  fragment`), excluded an external URL, passed a valid fragment, and exited 2.
  `--offline` keeps it deterministic and network-free, as `verify` requires.
- **Changed from the brief**: the brief lists lychee as Apache-2.0. The
  repository holds both `LICENSE-APACHE` and `LICENSE-MIT`; lychee is
  dual-licensed MIT or Apache-2.0. GitHub's license API shows only Apache-2.0.
  Either license fits.
- **Limit**: lychee checks links, not paths written in code spans such as
  `` `scripts/doctor.ts` ``. Those stay with the backfire judgments for target
  documents and with memorylint for the report-only documents (R7).

## R5. Python environment

- **Decision**: The shared component is its own uv project,
  `packages/doc-regions/`, laid out like backfire: `pyproject.toml`,
  `.python-version` (3.14.4, backfire's pin), `uv.lock`, `src/doc_regions/`
  and `tests/`, with `required-version = ">=0.11.32"` for uv. Its locked
  dependencies are `cogapp==3.6.0` and `markdown-it-py==4.2.0`, with `pytest`
  in the dev group at backfire's version. Orca's setup script runs `uv sync
  --locked --project packages/doc-regions`, and `deno task doctor` fails when
  that environment is missing or differs from its lock, as for
  `tools/spec-kit`.
- **Rationale**: Decision 6 says Python tools "can share backfire's uv
  environment and live in `packages/` like backfire". Sharing the same uv, the
  same pinned interpreter and the same offline run pattern
  (`uv run --frozen --offline --no-sync`) gives that. Adding these
  dependencies to backfire's own lock would ship them inside the code plugin,
  whose build copies `packages/backfire/uv.lock`
  (`specs/005-jev-decision-backend/contracts/mcp-server.md` on
  `feature/005-backfire-mcp`). A uv workspace over `packages/` would move that
  lock to the workspace root and change backfire's build contract. A separate
  project also lets feature 010's work-plugin build copy `doc-regions` the
  same way backfire's build copies backfire.
- **Changed from the brief**: "share backfire's uv environment" is read as
  sharing its toolchain and layout, not its `.venv` or `uv.lock`.

## R6. Backfire judgments

Read from `feature/005-backfire-mcp` without changing it: the tool sources
`packages/backfire/src/backfire/tools/verify.py` and `classify.py`, and
`specs/005-jev-decision-backend/contracts/evaluation.md`.

- **Decision**: The preparation command prints arguments that the main agent
  sends through its MCP client:
  - `backfire_verify`: `claims` is a list of unit texts (strings; the tool
    numbers them itself, so results map back by position), `evidence` is a
    list of `{id, text}` items, one per changed file of the feature diff
    against its merge base with `develop`, with the file path as `id`.
  - `backfire_classify`: `items` are `{id, text}` for the units the feature
    added, `id` being `<path>:<first line>-<last line>`, at most 64 items per
    call and text within the tool's 2,000-character truncation; `classes` are
    `mechanical_candidate` (text fully derivable from named repository files
    by a deterministic generator) and `agent_region` (anything else);
    `purpose` names the target document.
  The command splits claims and items into several requests when they pass
  these limits or backfire's request limits (below).
- **Checked after the 005 merge (T001, 2026-09-28)**: the input schemas in
  `packages/backfire/src/backfire/tools/verify.py` and `classify.py` on
  `develop` match the above. One assumption was wrong: `backfire ready` does
  not report request limits. They are fixed in
  `packages/backfire/src/backfire/validate.py` (`OPTION_LIMIT = 250`,
  `CELL_LIMIT = 672`): a Choice has at most 250 options and a request at most
  672 answer cells, and backfire does not split requests
  (`docs/backfire.md`, "Request limits"). In `backfire_verify`, each claim is
  a three-option Choice, and with more than one evidence item also a Choice
  among the items plus `none`. So a request with `C` claims and `E` evidence
  items uses `3C` cells when `E` is 1 and `C(E + 4)` cells otherwise, and `E`
  may be at most 249. The preparation command therefore derives the claims per
  request from the number of evidence items instead of taking a fixed maximum,
  and fails, naming the limit, when the evidence alone has more than 249
  items. In `backfire_classify`, 64 items of two classes use 128 cells, within
  the limit; item text past 2,000 characters is truncated by the tool.
- **Rationale**: In `verify.py`, each claim becomes a Choice among
  `supports`, `contradicts` and `says_nothing`, mapped to `verified`,
  `contradicted` and `unsupported`, with `action` `auto` or `review` at
  `auto_accept` 0.8. For a paragraph judged against a diff, `contradicted` is
  the drift signal and `unsupported` is the normal case (the diff says nothing
  about it). The evaluation contract states that `backfire_classify` never
  approves automatically, so its result is a suggestion the agent acts on.
- **Why the agent calls the tools**: backfire is an MCP server in the code
  plugin, configured with the operator's credential. The agent already has an
  MCP client; a repository script calling backfire would add client and
  credential code. The step is outside `verify` and the finish hook, as
  decision 3 requires.
- **Dependency**: backfire's tools are not on `develop` yet, so
  implementation waits for the 005 merge (FR-018), and the preparation
  command's tests use the tool input schemas as fixtures, not a live server.

## R7. Drift reports for `AGENTS.md` and the constitution

- **Decision**: Use MemoryLint 1.5.1's read-only audit script, run directly,
  not installed as a Spec Kit extension:
  `python3 scripts/audit_workspace.py <repository root> --format json` from
  the release archive
  `https://github.com/RbBtSn0w/spec-kit-extensions/releases/download/memorylint-v1.5.1/memorylint.zip`
  (SHA-256 `df4b31049dcd7f794e7bbed1460b5f5f5008b12a966939366e354926bb5f6648`,
  MIT). The judgment step downloads it into
  `~/.cache/verbose-broccoli/memorylint/1.5.1/`, checks the hash, runs it, and
  reports its findings for `AGENTS.md` and `.specify/memory/constitution.md`
  beside the backfire judgments of those files' paragraphs (R6). docguard is
  not used.
- **Rationale**:
  - MemoryLint's scripts use only the Python standard library. The audit ran
    in 0.06 s on the copy of HEAD and wrote nothing. It reported 21
    `boundary` warnings, all for the constitution's Sync Impact Report
    comment and principle VI's layer list. After a line naming
    `scripts/missing_file.ts` and `deno task nonexistent-task` was added to
    `AGENTS.md`, it reported a `reality` finding with the file, line and
    missing path; it did not flag the unknown task.
  - docguard-cli 0.41.6 (npm, MIT, Node 18 or later; the catalog's version,
    while npm's latest is 0.42.1) runs through `node cli/docguard.mjs verify
    --instructions --format json` without the Spec Kit extension. Its
    instruction audit reads only `AGENTS.md` and `CLAUDE.md`
    (`cli/scanners/instruction-audit.mjs` line 47), not the constitution. On
    the same copy it parsed hard-wrapped lines as separate rules, reported no
    stale pointer for the planted path, and produced three "requires-human"
    pair tasks from line fragments.
  - As the brief notes, docguard as a whole treats documents as the source of
    truth and can scaffold `CLAUDE.md`, which this repository forbids.
- **Cache writer**: the archive is 34,215 bytes and extracts to about
  175 KB. Constitution VII requires a storage budget and cleanup for every
  persistent generated writer, so the audit keeps the directory within 1 MiB,
  checked before each write; it downloads and extracts into a temporary
  sibling directory and renames it into place only after the hash check, and
  removes that temporary directory on failure, SIGINT or SIGTERM. A later run
  first removes leftovers of killed runs. Deleting the directory only costs a
  new download.
- **Boundary warnings**: They restate the constitution's own layout
  (Sync Impact Report, principle VI), so the report lists them separately and
  the user decides whether they matter. This feature does not filter or patch
  MemoryLint.
- **Changed from the brief**: the brief names docguard 0.41.6; npm's latest is
  0.42.1. Neither is adopted.

## R8. Where the judgment step is printed

- **Decision**: Add the step to the REVIEW-mode text of `deno task workflow`
  (`scripts/workflow.ts`, `actions.REVIEW`), which already describes the
  `develop` merge review, and to `docs/architecture.md`. No hook enforces it.
- **Rationale**: The repository's rule is that anything printed workflow text
  can carry goes there, not into `AGENTS.md`. The finish hook runs `verify`
  offline, and a recorded judgment result would be a new artifact to check.
- **Limit**: DIRECT-mode output does not describe the merge review today; this
  feature does not change that.

## R9. First mechanical regions

- **Decision**: After 005 merges, the implementation sends the current units
  of the targets to `backfire_classify` and converts the candidates it
  suggests that the main agent confirms. The skill ownership table in
  `docs/architecture.md` (source: the `SKILL.md` files under
  `plugins/*/skills/`) is converted in any case, so the check has a real
  region from the start.
- **Rationale**: Decision 2 gives `backfire_classify` this role. The ownership
  table is plainly a listing of directories.

## R10. Left out

- **Vale** (MIT): no terminology or style need has shown (decision 5).
- **Code maps** (Aider's repository map, RepoMapper, Serena): left out as the
  brief says; agents' on-demand search is enough at this repository's size.

## For feature 010

Feature 010 reuses, without redefining: the region model (data-model.md), the
marker and source-naming rule (R2), `packages/doc-regions` for the check,
regeneration, unit splitting and request preparation, and lychee. It adds its
own target list and generators, and markitdown and qmd as its brief says.

Feature 010's research (R8 in `specs/010-wiki-consistency/research.md` on
`feature/wiki-consistency`, 2026-09-28) found that the Wiki needs three things
this plan did not state: target globs such as `wiki/**/*.md`, a root other
than the repository with a generator path outside it, and request preparation
with evidence the caller supplies per unit. Feature 010 calls the package's
modules as a library, not its commands. Because User Story 4 requires that
feature 010 need no change to the package, this feature builds all three as
library parameters ([contracts/commands.md](contracts/commands.md), "Library
interface"); its own commands keep the repository as root and the feature
diff as evidence.
