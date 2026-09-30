# Implementation Plan: Own-Code Limit per Feature

**Branch**: `feature/own-code-limit` | **Date**: 2026-09-30 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/022-own-code-limit/spec.md`

## Summary

Add one repository check, `npm run own-code`, to `npm run check`, so that
`npm run verify` and the feature finish hook, which runs `npm run verify`,
enforce the 300-line own-code limit:

- `scripts/own_code.ts` extracts the merge base of `HEAD` and `develop` into
  a temporary directory with `git archive`, measures the own-code size of that
  tree and of the worktree, prints both and the net change, and fails when the
  net change exceeds the limit.
- scc 4.1.0 counts the code lines, pinned like ShellCheck: `tools/scc/` is a
  uv project whose `uv.lock` pins `scc-bin` 4.1.0, the PyPI wheels of scc's
  release binaries.
- GitHub Linguist's language data, pinned as the npm package
  `linguist-languages` 9.5.0, decides which of scc's languages are code.
- Upstream copies are files whose SHA-256 appears in an upstream record of the
  same tree; tests are paths under `tests/` or named `*_test.*` or `*.test.*`.
- Approval lines added to the branch's Spec Kit records raise the limit.
- `scripts/own_code_test.ts` exercises the check on synthetic Git
  repositories.

Research and rejected alternatives are in [research.md](research.md).

## Technical Context

**Language/Version**: TypeScript 6.0.3 on Node.js 24.12 or later, like the
other checks in `scripts/`.

**Primary Dependencies**: scc 4.1.0 (`scc-bin` 4.1.0 through uv 0.11.32);
`linguist-languages` 9.5.0; Git.

**Storage**: None. One temporary directory per run in the OS temporary
directory, removed when the run ends.

**Testing**: `node:test` in `scripts/own_code_test.ts` with synthetic Git
repositories in temporary directories; `npm run check` and
`npm run verify`.

**Target Platform**: The development machine (Linux) and Orca worktrees.

**Project Type**: Repository check.

**Performance Goals**: A few seconds on the current repository (about 700
tracked files).

**Constraints**: Offline; read-only for the repository and the Git index;
own code of the check itself within the 300-line limit (FR-012).

**Scale/Scope**: One script of about 70 code lines, one doctor line, one
setup line, and configuration.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Proven Dependencies**: scc and Linguist's data are pinned by
  `tools/scc/uv.lock` and `package-lock.json`. Pass.
- **II. Deliver Working Capabilities**: No planned-only capability is counted
  as done. Pass.
- **V. Observable Acceptance**: Synthetic repositories cover positive (under
  the limit), negative (over), boundary (300 and 301), approval, stale
  approval, test, upstream copy, patched copy and non-code cases, plus a
  missing `develop`. The backfire rebuild case (SC-004) is checked once on its
  real tree. Pass.
- **VII. Minimum Implementation**: The check reuses scc, Git and Linguist;
  the script only lists files, reads records, and adds numbers. The temporary
  tree is not persistent output and is removed on success and on failure; an
  interrupted run can leave one copy in the OS temporary directory. Pass.
- **IX. Layout**: The check is repository automation in `scripts/`; scc's
  environment is a development program in `tools/`. Pass.
- **Development Workflow**: git flow feature branch, Codex implementation,
  a fresh Claude Code reviewer for the develop merge review, finish with
  `git flow feature finish`. The finish hook is unchanged. Pass.

Post-design re-check: no change; no violations.

## Project Structure

### Documentation (this feature)

```text
specs/022-own-code-limit/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── own-code-check.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
scripts/
├── own_code.ts          # the check (own code, counted)
└── own_code_test.ts     # its tests (not counted)
tools/scc/
├── pyproject.toml       # pins scc-bin 4.1.0
└── uv.lock
package.json             # own-code and test:own-code scripts; linguist-languages
package-lock.json
turbo.json               # //#own-code in check, //#test:own-code in test
scripts/doctor.ts        # checks the tools/scc environment
scripts/doctor_test.ts
orca.yaml                # setup syncs tools/scc
docs/architecture.md     # describes the check
docs/reference/commands.md  # regenerated
```

**Structure Decision**: The check follows the existing pattern of
TypeScript checks in `scripts/` run through `package.json` and Turborepo, and
the ShellCheck pattern for a binary tool pinned through uv in `tools/`.

## Complexity Tracking

No violations.
