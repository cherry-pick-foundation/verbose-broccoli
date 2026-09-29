# Quickstart: Own-Code Limit per Feature

## Prerequisites

- The repository set up by Orca's setup script, or at least
  `uv sync --locked --project tools/scc` and `npm ci`.
- A local `develop` branch.

## 1. The check on this branch

```sh
npm run own-code
```

Expected: one line with the merge base's size, the worktree's size and the
net change, which is this feature's own net change (FR-012, SC-005); exit 0.

## 2. The develop baseline

In the `develop` worktree with a clean tree, or on this branch before any
change:

```sh
npm run own-code
```

Expected: both sizes equal and net 0 (FR-009). The size is the own-code size
of `develop` recorded in `tasks.md` (SC-006).

## 3. The limit, its boundary and approval

`npm run test:own-code` builds synthetic Git repositories with a `develop`
branch and a feature branch and runs the check in them:

- 300 net lines pass; 301 fail (SC-001);
- an added `**Own-code limit**: 450` line lets 400 pass; 320 does not; a line
  already on `develop` does not count (SC-002);
- tests, upstream copies by recorded hash, and non-code files add nothing;
  one changed byte makes an upstream copy own code;
- deleting own code gives a negative net change and passes;
- no `develop` branch fails.

## 4. The backfire rebuild's vendored files (SC-004)

Run this branch's check with the rebuild commit as the working directory:

```sh
tmp=$(mktemp -d)
git worktree add --detach "$tmp/rebuild" 8a1d2f0
(cd "$tmp/rebuild" && node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON "$OLDPWD/scripts/own_code.ts")
git worktree remove "$tmp/rebuild"
```

Expected: the net change is a few lines at most. That commit adds about 5,850
code lines of vendored jev-judge-mcp source under
`packages/backfire/src/jev_judge_mcp/`, so any of it counted as own code would
show as thousands.

## 5. Full verification

```sh
npm run verify
```

Expected: `VERIFIED`.
