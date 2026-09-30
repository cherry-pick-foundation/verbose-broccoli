# Implementation Plan: Session Selection for the Wiki Vaults

**Branch**: `feature/session-wiki` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

## Summary

Amend constitution principle VI so exported Claude Code and Codex sessions
are Raw evidence in any vault they belong to, adopt SpecStory's command-line
tool after a security review, and add a selection procedure to the work
plugin's `wiki-raw-import` skill: render, scan, digest and classify the
sessions, then hand the user lists to approve. Existing tools do almost all
of the work; the repository adds one glue script.

## Reuse

| Need | Existing tool | Own code |
| --- | --- | --- |
| Render sessions to Markdown | SpecStory CLI 2.15.1 (`sync -s <id>`), which also redacts secrets | none |
| Secret scan | betterleaks 1.9.0 `dir` with a JSON report | none |
| Pin and install both tools | mise with a reviewed `mise.lock`, as CHE-44 pins tools | none |
| Roster check for student data | backfire's `backfire_education` roster matcher | a call |
| Classification with pseudonyms | backfire `serve-mcp --education`, `jev_classify` | an MCP client call |
| Raw admission | the skill's `raw_import.py` | none |
| Listing sessions, skipping running ones, mapping a session to its Markdown, cutting digests, batching | none found | the glue script |

No upstream tool lists both agents' sessions with their project paths, turns
SpecStory output into bounded digests or batches them into `jev_classify`, so
that part is glue: `plugins/work/skills/wiki-raw-import/scripts/session_select.py`,
run inside backfire's uv environment so it needs no new lock. Estimate: about
200 lines of script and about 200 lines of tests on synthetic fixtures.

SpecStory already redacts secrets with the betterleaks ruleset. The separate
betterleaks scan reports what remains, so that a session with a finding is
held back instead of sent. No scanner existed in the repository or in CHE-44;
betterleaks is the maintained successor line of gitleaks by the same authors
and is what SpecStory embeds.

## Technical Context

- Sessions: 166 Claude Code and 1,313 Codex session files on 2026-09-30;
  Codex sessions come from 258 project paths, 163 of which no longer exist.
- Limits: `jev_classify` takes up to 64 items per call, cuts each item at
  2,000 characters and allows 250 classes; five classes are used.
- Staging: `~/.cache/verbose-broccoli/sessions/`, mode `0700` (user decision).
- mise: paranoid mode with content-bound trust. The branch first added a
  root `mise.toml` with the two tools and its `mise.lock` while CHE-44 was
  unmerged; the user allowed `mise trust` on this worktree's file after each
  reviewed change. After CHE-44 reached `develop`, the merge combined both
  `[tools]` tables, regenerated the lock (CHE-44's entries unchanged) and
  added both tools to the `mise install --locked` line in `orca.yaml`.
- Constitution version: the `feat` commit raised it by hand from 2.3.0 to
  2.4.0 while commitizen was not yet on `develop`; the merge with CHE-44's
  2.3.1 set 2.4.0 again with `npm run constitution:bump -- MINOR`.

## Constitution Check

- **I. Proven Dependencies**: both tools pinned through mise with a reviewed
  lock; the script runs in backfire's locked environment.
- **V. Observable Acceptance**: tests on synthetic fixtures; the sample run is
  the operational check.
- **VI. Wiki Layers**: amended by this feature; the staging folder is cache
  (temporary, rebuildable work); raw admission stays with `raw_import.py`.
- **VII. Minimum Implementation**: one glue script; no retries, caches or
  settings beyond the procedure.
- **Product and Data Boundaries**: no session contents, names or secrets in
  fixtures, records or messages.

## Project Structure

```text
.specify/memory/constitution.md                       # principle VI, 2.4.0
docs/architecture.md, docs/examples/wiki/AGENTS.md   # the rule
mise.toml, mise.lock                                  # SpecStory, betterleaks
turbo.json, package.json                              # MISE_* and the test task
plugins/work/skills/wiki-raw-import/
├── SKILL.md, assets/AGENTS.md                        # the rule, a pointer
├── references/session-selection.md                   # the procedure
├── references/session-catalog.json                   # the catalog
├── scripts/session_select.py                         # the glue
└── scripts/session_select_test.py                    # its tests
specs/026-session-wiki/                                # these records
```

## Workers

| Work | Agent, model, effort | backfire `jev_decide` confidence |
| --- | --- | --- |
| Security review of SpecStory and betterleaks | Claude Code, Opus 5.5, high | 0.49 |
| Glue script and tests | Codex, gpt-6-luna, xhigh | 0.39 |
| Develop merge review of the code | Claude Code, Sonnet 5.5, medium | 0.56 |
| Develop merge review of the records | Codex, gpt-6-luna, medium | 0.52 |

The two review picks were made again after `develop` brought in the code
plugin's `model-choice` skill, with its evidence: live model catalogs,
usage limits from CodexBar (Codex weekly window 37% used; Claude session 9%
and weekly 21% used) and earlier reviewers' track records.

The coordinator (Claude Code) writes the constitution change, the documents,
the procedure and the catalog, and reviews the Codex code before it is
committed. At the develop merge review, a Claude Code reviewer takes the
Codex-written code and a Codex reviewer takes the coordinator's records.

## Stage 2 needs

Stage 2 runs in an Orca folder workspace on the vaults folder: the pinned
tools installed from the merged lock; the four vaults' own `AGENTS.md`
updated to the new rule; the full render, scan, digest and classify run after
the user's go on the sample's estimate; the user's decisions on every
`review` result; one selection and raw import per vault; then page writing
with the `wiki-consistency` skill.
