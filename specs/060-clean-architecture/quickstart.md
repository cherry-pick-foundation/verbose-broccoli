# Validation Guide: Clean Architecture Migration

## Planning and Baseline

Use a trusted checkout with the current locked tools/dependencies installed.
Run the active Spec Kit setup scripts through the tool environment so PyYAML
is on PATH. The feature directory is specs/060-clean-architecture.

```sh
npm run workflow -- --task clean-architecture-plan --base d9392f14b332a484db13f2f21af68007955abe9f
uv run --project tools/spec-kit --frozen --offline --no-sync bash .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
git diff --check
```

Read-only consistency analysis checks spec, plan and tasks against the constitution.
It does not approve implementation or finish a task. Record its actual output.

Before each code slice, save its baseline contract and narrow test output with
that Dispatch's immutable evidence. Keep the current public entry and no-student
boundary from [contracts/migration.md](contracts/migration.md).

## First Capability Checks

The current root task names are stable entry points before and after moves.

```sh
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 npm run test:doc-regions
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 npm run test:credit-offers
npm run python:imports
npm run clean-architecture
npm run doc-regions:check
```

For document regions, exercise malformed markers, missing generator/input,
symlink/root escapes, stale generated output, Markdown/Quarto link views,
update byte preservation and failures. Verify the ten held-consumer imports
from the package-owned case, then run unchanged wiki-consistency tests.

For credit offers, exercise empty/populated blocks, duplicates/malformed rows,
one classify call, failed judgments, notification failure and exit behavior.
Command help must run without tracker/provider calls. All fixtures are synthetic.

## Command and Hook Checks

```sh
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 npm run test:clean-code
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 npm run test:workflow
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 npm run test:cli-contract
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 npm run test:coordinator-context
```

The CLI contract check includes real child processes, help/error output and a
copied independently runnable skill. A package install or type check alone
does not satisfy it. Preserve fixed shell/hook entry paths and their existing
tests. Negative import fixtures must fail the named Python/TypeScript rules.

## Backend Slice

Run the security review before adapter adoption. Use synthetic settings/lists
and the real gated route described in [contracts/judgments.md](contracts/judgments.md).
Verify both configured backends, the actual route fields, bad-request recovery,
Jev-only selection and slow/timeout/cancellation behavior. Live non-personal
development calls use approved credit; record the actual count and outcomes.
This planning guide does not activate private configuration.

## Full Verification and Integration

First inspect the machine for another full verification process:

```sh
pgrep -af "turbo run"
```

Wait if another actual Turborepo run is active; ignore the inspection shell itself.
Then run exactly one full verification under the user's CPU policy:

```sh
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 npm run verify
```

Required result: exit 0 and VERIFIED from that run's summary. Preserve its log
and summary; cached tasks are valid only under the current cache contract.
Rerun workflow after scope changes and before completion with the same context.

Before merge, follow workflow's document-judgment/audit instructions, record
unperformed checks, commit the slice record, obtain the current-base independent
review and ask develop for the serialized finish slot. Recheck develop's tip;
any drift requires integration, verification and renewed review. Develop owns
the final merge, Linear state and ledger ticks. A pending hold is not success.
