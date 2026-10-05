# Implementation Plan: Wiki container naming

**Branch**: `feature/wiki-container-naming` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

## Summary

Replace the existing data-container literals and raw-stage guard. Update current
Wiki instructions and focused synthetic fixtures; inspect consumer readiness.
No new dependency, compatibility layer, registry or migration implementation.
Estimated owned runtime delta: three literal edits and docstring wording.

## Technical Context

**Language/Version**: Existing Python 3.14 and Node 24 TypeScript tests.
**Primary Dependencies**: Existing pathlib, argparse, bagit and pytest.
**Storage**: Existing XDG paths; immutable BagIt raw and local Wiki Git.
**Testing**: Existing pytest and Node test suites, regression against old literals.
**Target Platform**: Linux native clients and checkout-local command lines.
**Project Type**: Existing library and command-line tools.
**Performance Goals**: Existing behavior; no performance-sensitive change.
**Constraints**: Synthetic checks only; no private data/settings writes.
**Scale/Scope**: Four named wikis, existing custom names; current Wiki terminology.

## Constitution Check

Before and after design: preserve sources and storage ownership; no new store,
registry, package or dependency. Tests prove positive, negative and boundary path
behavior. An explicit user naming decision amends current principle VI wording
with a normal fix/PATCH bump; historical governance wording remains unchanged.
Final assessment is other-provider; root alone integrates. All gates are met by
the planned scope, subject to actual checks and independent review.

## Project Structure

Feature records live here: spec, plan, research, data-model, paths contract,
quickstart, tasks, quality checklist and final record. Existing code edits are
`packages/wiki-consistency/src/wiki_consistency/instance.py` and
`plugins/work/skills/wiki-raw-import/scripts/{raw_import,session_select}.py`.
Tests use `packages/wiki-consistency/tests/{test_instance,test_main,conftest}.py`,
`plugins/work/skills/wiki-raw-import/scripts/session_select_test.py` and
`scripts/wiki-raw-import-test.ts`. Current prose changes are exact files in the
external workflow plan, limited to Wiki-domain wording.

## Execution and ownership

Coordinator implements locally; a fresh native other-provider reviewer follows.
No parallel writer is needed for three literal edits. The Korean Wiki owner keeps
lint.py/test_lint.py and F2 files. Root owns full-verify scheduling, Linear,
finishing and final ledger ticks. Evidence is retained under
`~/.local/state/verbose-broccoli/workspaces/feature-wiki-container-naming/che-90/ctx_0944eec65615/`.
