# Implementation Plan: Kebab-case file names

**Branch**: `feature/kebab-file-names` | **Date**: 2026-09-30 |
**Spec**: [spec.md](spec.md) | **Linear issue**: CHE-63

## Summary

Pin ls-lint through mise after a security review, configure it in
`.ls-lint.yml` with the short exception list, run it in `npm run verify`
through Turborepo, rename the remaining non-kebab paths in one commit, and add
the naming rule to the Wiki schema template and the four vault schemas.

## Technical Context

- **Tool**: ls-lint 2.3.1 (MIT), a Go binary, through mise's
  `aqua:loeffel-io/ls-lint` backend, locked in `mise.lock`. The security
  review is [security/ls-lint-2.3.1.md](security/ls-lint-2.3.1.md).
- **How ls-lint reads a name**: it checks the part of a file name before the
  first dot against the rules for the rest (the extension), trying each
  extension part in turn with `*`; folder names are checked whole, so hidden
  folders such as `.github` need their own pattern; files without a dot use
  the `.` key. Source: `internal/linter/linter.go` at tag `v2.3.1`.
- **Configuration**: `.ls-lint.yml` at the root; the ignore list holds only
  untracked build and tool folders (`.git`, `node_modules`, `.venv`, caches).
- **Wiring**: an npm script `lint:names`, a Turborepo task in the `check`
  graph, the tool in `orca.yaml`'s setup and CI's `mise install` line.
- **Vault files**: `AGENTS.md` of `default`, `chat`, `code` and `work` under
  `~/.local/share/verbose-broccoli/vaults/`, each its own Git repository, and
  their template `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`.

## Constitution Check

- Reuse before implementing: ls-lint is upstream and unchanged; the
  repository adds only its configuration and the wiring lines. No local
  checker.
- Upstream tools: pinned once in `mise.toml` with its lock, after a security
  review (as in feature 023).

## Exceptions

| Name | Reason |
| --- | --- |
| `*.py`, `*.py.lock`, folders under `packages/*/src/` | Python modules and packages are imported by name, and a hyphen is not valid in an import name (PEP 8 names modules in lowercase with underscores); uv names a script's lock `<script>.py.lock`. |
| `AGENTS.md` | The AGENTS.md convention; Codex and Claude Code look it up by this name. |
| `SKILL.md` | The Agent Skills format fixes a skill's entry file name. |
| `README.md` | The convention that code hosts render by this name. |
| `LICENSE` | The convention for a license text, kept as upstream ships it. |

## Approach

1. A Codex worker reviews ls-lint 2.3.1's source and release read-only.
2. After it clears, pin ls-lint, write `.ls-lint.yml`, and wire it into
   `npm run verify`.
3. Add the naming rule to the template and the `default`, `chat` and `code`
   vault schemas; the `work` vault after CHE-61.
4. After the `develop` session grants a finish slot: merge the newest
   `develop`, rename with `git mv`, update every reference, regenerate the
   generated documents, and commit the renames as one commit.
5. A Codex reviewer gives the develop merge review; then finish into
   `develop`.
