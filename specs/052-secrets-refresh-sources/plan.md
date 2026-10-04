# Implementation Plan: Multi-source Secrets Refresh

**Branch**: `feature/secrets-refresh-sources` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

**Input**: CHE-85 dispatch and spec 052.

## Summary

Extend the existing script with sources and mappings, fixed-path validation, byte-preserving variable updates and whole-file content. Keep collect/validate/prepare/rename order and sanitized failures.

## Technical Context

**Language/Version**: TypeScript executed by the existing Node runtime.
**Primary Dependencies**: Existing pinned bws 2.1.0; Node built-ins only.
**Storage**: External XDG operator JSON, token files and fixed client targets.
**Testing**: Existing node:test and fake bws, isolated synthetic homes under /tmp.
**Target Platform**: Linux single-user workstation.
**Project Type**: Repository command glue.
**Performance Goals**: One list call per configured source.
**Constraints**: No live credentials/network/global changes; no full verify in worker.
**Scale/Scope**: Small operator mapping; no general file writer or recovery framework.

## Reuse

| Need | Reused implementation | Owned glue |
| --- | --- | --- |
| Secret fetch | Pinned bws secret list JSON | Per-source loop/environment |
| Private token checks | Existing readPrivate + Node fs flags | No-follow and closed descriptors |
| Path identity and fixed targets | Node path/fs | Allowlist and alias checks |
| Existing lines | Node Buffer | Replace mapped values only |
| File publication | Node exclusive writes/rename | Prepare all before rename |
| Tests | Existing node:test fake bws pattern | Multi-source fixtures and boundary cases |

Initial estimate: 100-160 added implementation lines, plus tests and records, against main's 50-120 estimate. Measure final git diff --stat; size is not a cap. Security validation may increase this estimate. No dependency adoption or copied upstream source.

## Constitution Check

Before research and after design: integration glue reuses the existing bws review/pin and Node APIs; credentials remain outside Git; offline positive/negative tests prove file readback and unchanged originals. Private temporary files are bounded to one per target per normal run, removed on ordinary failure; abrupt interruption cleanup is manual. Other-provider final review and full verify belong to the coordinator. No rule or constitution change.

## Project Structure

scripts/secrets-refresh.ts and scripts/secrets-refresh-test.ts remain the command and tests. This directory contains spec, plan, research, data-model, quickstart, contracts/operator-config, checklists/requirements and tasks. Only the secrets sections of docs/backfire.md and docs/architecture.md and a dated note in the existing bws security record change.

## Phases and validation

1. Specification/checklist, then research/plan/model/contract/quickstart.
2. Tasks and read-only consistency analysis before script edits.
3. Offline regression tests, implementation, documentation.
4. Narrow tests, ESLint, TypeScript and workflow scope evidence, diff review and local commit.
5. Coordinator full verify, independent review and integration; develop owns final task ticks.

## Split review

2026-10-04: the implementation/test replacement plus required records exceed 1,000 changed lines. Keep this as one cohesive feature: schema, all-source preflight, fixed-path security, byte preservation and tests cannot be delivered independently without an incomplete refresh contract. No unrelated supporting tool or new package was added. The worker reports measured code/tests/docs sizes in its completion; the coordinator still owns independent review and integration.

Measured implementation: 296 total lines, +274/-94 against base (net +180); tests +607/-206 before record-only completion notes. The increase over the initial estimate is the required fixed-target/canonical/inode protection, malformed-input validation and byte-preserving replacement, not supporting tooling. The final committed diff stat is reported through Orca.
