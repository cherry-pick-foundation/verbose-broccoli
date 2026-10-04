# Implementation Plan: Post-merge Feature Cleanup

**Branch**: `feature/finish-cleanup` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: CHE-87 feature-finish-cleanup dispatch.

## Summary

Use git-flow-next's configured post-finish hook to print an operator checklist
after successful feature merges. Include the retained source tip and worktree
path; do not automate session settlement or worktree removal.

## Technical Context

**Language/Version**: POSIX shell; Node.js 24 for the existing test harness.

**Primary Dependencies**: Installed git-flow-next 2.1.0 and Git; no new dependency.

**Storage**: Git branch/worktree state; output is transient.

**Testing**: Existing `node:test` harness in `scripts/git-flow-test.ts`.

**Target Platform**: Linux developer worktrees.

**Project Type**: Repository workflow hook.

**Performance Goals**: One local status/ref inspection after each feature finish.

**Constraints**: No live Orca lifecycle mutation from a hook; preserve dirty,
unsettled, unrelated and unmerged state; no upstream patch or new framework.

**Scale/Scope**: One hook, focused additions to its existing integration test,
and the three standard Spec Kit records. Initial estimate: 35-55 shell and test
lines, plus records; final measured size is recorded below.

## Design

The existing `.gitflow` sets `gitflow.path.hooks` to
`scripts/git-flow-hooks`. git-flow-next 2.1.0 names post hooks
`post-flow-<type>-<action>`, passes `[name, origin, full branch]`, exports
`BRANCH`, `BASE_BRANCH` and `EXIT_CODE`, runs post hooks after success or
failure, and prints their output. The hook exits quietly on failed finishes.
On success, it resolves the retained branch tip and its worktree from Git,
reports current cleanliness, and prints a manual checklist. The Orca removal
command appears only when the worktree exists and Git confirms it is clean; Git
shell-quotes its selector, and the command uses `orca-ide`. Missing finish
status, tip or worktree facts produce a preserve-and-inspect message.

## Reuse

| Need | Reused implementation | Owned glue |
| --- | --- | --- |
| Finish event | `.gitflow` hook directory and git-flow-next hook runner | One post-finish shell hook |
| Branch tip and worktree | Git `rev-parse`, `worktree list`, and `status` | Safe output and manual cleanup steps |
| Regression | Existing synthetic real-finish harness | Two finishes and a failed finish case |

## Constitution Check

The change adds the requested post-merge reminder through the existing native
extension point. It avoids guessing whether Orca workers are settled and avoids
automated deletion. Only the approved hook, existing test and standard feature
records are changed. Full verification and independent review remain with the
coordinator.

## Project Structure

```text
scripts/git-flow-hooks/post-flow-feature-finish
scripts/git-flow-test.ts
specs/054-feature-finish-cleanup/{spec.md,plan.md,tasks.md}
```

## Validation

1. Add a real-finish regression and confirm it fails without the post hook.
2. Add the hook and run the focused git-flow harness; inspect its exact output
   and synthetic Git refs/worktrees, including dirty, missing and unreadable
   source states and quoted paths.
3. Run shell lint, whitespace checks and workflow. Request the coordinator's
   serialized full verification slot; the worker does not start full verify.
4. Review and commit the exact scoped diff through the normal hooks.

## Split Review

The implementation is a small shell hook plus an existing harness regression;
no split is needed. Final source is 49 shell lines; the test diff adds 205 and
removes 2 lines; the three records total 199 lines. The five-file diff adds
453 and removes 2 lines, with no separate tooling or dependency.
