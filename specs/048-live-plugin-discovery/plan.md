# Implementation Plan: Live Plugin Discovery

**Branch**: `feature/live-plugin-discovery` | **Date**: 2026-10-02
**Spec**: [spec.md](spec.md) | **Issue**: CHE-82

## Approach and Estimate

Extend the existing client-preparation generator with a live project route.
Use Node's existing filesystem and path APIs to index canonical plugin skill
directories through relative links. Keep copied distribution separately callable.
Derive project MCP configuration from the existing plugin declarations and
resolve paths to the checkout; do not add a second maintained server definition.

Estimate before build: 150–300 maintained implementation lines plus focused
regression checks. This is an estimate, not a feature cap. There are no new
dependencies or upstream source adoptions. Record measured size before review;
apply the existing 1,000-line split-review rule if reached.

Approved resume amendment, 2026-10-02: add an estimated 50–100 maintained
implementation lines plus focused storage regressions. Ownership receipts and
retained paid/native evidence belong in state; reproducible distribution belongs
in cache. Use absolute XDG roots and standard defaults for unset, empty or relative
values, under `verbose-broccoli/workspaces/<worktree>/<task>/`. Client-required
project configuration stays in its supported location. Reuse Node filesystem
support; add no artifact manager, cleanup framework or dependencies.

Permanent producer storage uses operation `plugin-discovery`, separate from
this feature Run's `che-82` evidence directory. Identify a checkout by its
resolved absolute path: append the first 12 hex characters of SHA-256 to its
folder basename under the workspaces namespace. This isolates same-named
checkouts, including staging and recovery paths. A relocated configured
checkout must carry its ownership receipt explicitly to the new identity;
source/client configuration conflicts remain fail-closed.

## Technical Context

Node 24 TypeScript repository scripts and existing locked dependencies;
installed Codex and Claude Code on Linux. Canonical packages remain
`plugins/code`, `plugins/work` and `plugins/chat`. Local generated configuration
belongs in existing repository locations or ignored `.local/`; global client
settings and external runtimes remain outside the authorized write scope.

## Constitution Check

The change reuses an existing generator and standard-library filesystem APIs.
It keeps three portable plugin roots, package-local resources and existing data
ownership. Verification uses synthetic fixtures and metadata-only native
client probes, then the full repository suite. Planning does not complete an
implementation task. Only develop owns final ledger ticks and Linear writes.

## Ownership and Execution

Feature coordinator owns these Spec Kit records, persistent exact-file workflow
plan, scheduling, integration and one shared commit. It implements no feature
code. Parent Run is `run_e7efe7303f0e`; child Run is `run_1286efbc5cf6`.

The discovery worker owns `scripts/plugin-clients.ts`,
`scripts/plugin-skills-test.ts`, necessary root setup/config files and local
discovery links. The metadata worker owns both Backfire skill directory
renames, their metadata, active plugin references and license notice paths.
The documentation worker owns `README.md`, `docs/architecture.md` and existing
generated references. Workers must ask before crossing those boundaries.
They do not stage, commit, write Linear or run full verification independently.

Authoritative exact-file ownership plan:
`~/.local/state/verbose-broccoli/workspaces/feature-live-plugin-discovery/che-82/ownership-plan.json`.
The original disposable `/tmp` plan was lost at reboot; it was reconstructed
from staged paths and the retained ledger without repeating completed work.
It includes old/new renamed
paths and is passed with `--task che-82 --base
fd52a3c9fe6b0104e3b1d19671a756e2033f5947` to workflow. Update it when a real
scope change occurs, then rerun workflow before editing the new scope.

The resumed native coordinator is Dispatch `ctx_d613ab815717` under develop's
Task `task_4cb07a2ad58b`; its requested and effective launch are Codex
`gpt-6.1-sol` xhigh. It rebound existing Run `run_1286efbc5cf6`; temporary Run
`run_d682167f74b7` created before the resume amendment is superseded.
All 894 existing `.local/che-82` artifact files were copied byte-for-byte and
SHA-256 checked into the task state's `retained-before-storage/`; the manifest
is `retained-manifest.json`. Historical reports and paid results are preserved.
New authoritative worker reports, logs and receipts also use this task state.
Repository `.local/che-82` copies remain disposable editor views.

Launch workers natively with Orca, after task-specific Jev model-choice.
Each batch uses `systemd-run --user --scope -q -p CPUWeight=20 nice -n 10
taskset -c 4-7`. Interactive agent sessions remain unpinned. Ask develop for
the full-verification slot, check for another `turbo run`, and release the slot
on actual exit. Ask develop for integration after current develop is merged
and the exact result is verified and independently reviewed.

## Validation and Source Evidence

Focused checks cover source-edit readback, folder/frontmatter agreement,
resource/rule resolution, stale/broken links, name collisions, safe conflicts,
reruns and moved checkout roots, plus existing distribution invariants.
Client acceptance must show actual supported discovery, source paths and MCP
metadata, not infer acceptance from filesystem listings or test counts.

Targeted primary documentation supplied by main:
<https://learn.chatgpt.com/docs/build-skills>,
<https://code.claude.com/docs/en/skills>,
<https://code.claude.com/docs/en/plugin-marketplaces> and
<https://code.claude.com/docs/en/plugins-reference>.
Read targeted current client sources and help as needed, not the earlier
multi-repository research. CHE-78's plugin-server-loading bug records cover
copied distribution and are historical context, not live-source acceptance.

Before merge review, follow workflow's document-region prepare/audit judgment
instructions, report rules/constitution findings without unrelated edits, and
record decisions for changed document units. Use a fresh allowed reviewer from
a provider other than the implementer, with only scope and requirements.

## Integration Size Review

The first staged diff against develop is 938 additions and 65 deletions
(1,003 changed lines), including 49 discovery links, documentation, records
and focused regressions. The generator adds 228 maintained lines and removes
two; unchanged moved upstream resources do not add maintained implementation.
The existing split-review threshold is reached. Keep one feature: the unique
Backfire names are required before the shared index can reject collisions, and
project MCP setup, source discovery and native acceptance share one generator
and setup route. No independent implementation layer or extra dependency needs
a separate feature. The fresh merge reviewer may challenge this decision.

Resumed pre-freeze measurement: 74 changed files, 1,431 additions and 69
deletions before these final record lines, about 1,500 changed lines overall.
The final generator is +281/-4 lines (net +277); focused regressions are
+542/-12. Storage adds net 51 implementation lines within that generator.
Keep the same feature split: names, discovery, MCP setup and producer ownership
share one preparation route and must be accepted together. No independent
package, dependency or publication capability was added.
