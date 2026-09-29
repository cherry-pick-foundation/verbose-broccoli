## Reviewer rules

You are a reviewer. Do not edit, stage, commit or format any file, and do not run commands that write to the repository (read-only git commands, and tests or builds that write only to temporary directories, are fine). Every finding needs a file:line or a command with its output as evidence. Write your findings to the one report file named above (the only file you may create) and summarize them in `worker_done`.

Repository: /home/choi-eunchang/workspaces/verbose-broccoli/feature-turborepo, branch `feature/turborepo` at commit `9d8af61`. Do not check out another branch. The feature's changes are `git diff 8ce9b2a 9d8af61` (`8ce9b2a` is `develop`, already merged into the branch).

**Requirements**: `specs/019-turborepo/spec.md` (FR-001 to FR-014), the decisions in `specs/019-turborepo/research.md`, and the rules in `AGENTS.md` (reuse before implementing, the smallest change, no reimplementation of what a runtime or dependency provides). Only the sites listed as `SELECT` in `specs/019-turborepo/evidence/selected-sites.md` and `selected-sites-full-removal.md` were meant to change. Tools: Node.js 24.19.0, npm 12.1.0, uv 0.11.32; do not change global tools or user configuration.

**Look for**: behavior that differs from `develop` without a requirement or decision behind it; requirements the change misses; checks that were weakened or dropped; code that is more complex than it needs to be, or local code where a runtime or dependency feature exists; and changes outside the selected sites.

**Acceptance**: a findings list (possibly empty), each with a severity (blocker, should-fix, note), evidence and a suggested resolution; plus the commands you ran with their exit codes.

Orca: copy the heartbeat and `worker_done` commands from your preamble verbatim, including `--dispatch-capability`. The Orca `check` errors `stable_pane_required` and `consumer_fenced` are expected; ignore them. Send `worker_done` exactly once, with `--outcome succeeded` (a finished review with findings is still succeeded), a three-sentence summary, and `--files-modified` naming only your report file.
