# Implementation Plan: Live Plugin Discovery

**Branch**: `feature/live-plugin-discovery` | **Issue**: CHE-82
**Spec**: [spec.md](spec.md) | **Date**: 2026-10-02

## Approach

Reuse `scripts/plugin-clients.ts`, Node filesystem/path support and the locked
setup. Keep each skill body/resources in its owning plugin; shared project
indices contain relative links only. Backfire code and education names are
unique, with their existing privacy boundaries and shared license/reference
bytes preserved. Local MCP configuration derives from existing declarations.
Optional copied distribution remains a separate cache output.

Receipts and bounded pending intent belong in XDG state; reproducible packages
belong in cache. Absolute XDG roots are honored; unset, empty or relative values
use standard home defaults. Permanent producers use
`verbose-broccoli/workspaces/<basename>-<sha12>/plugin-discovery/`; SHA-256 hashes
the resolved absolute path as UTF-8. Same-name checkouts are isolated. A moved
configured checkout explicitly transfers its receipt; unknown edits fail closed.

Client files use exclusive same-directory staging and atomic replacement,
retaining POSIX mode/owner. `plugins:clean-codex` removes only the completed
receipt's exact block, including its owned separator. Both feature and develop
must be clean before normal finish; final develop must be prepared again for
MCP readiness. Canonical Claude skill paths are resolved before relative Read
paths through the existing shared instruction, without another skill tree.

## Scope and Limits

Exactly three portable plugin roots remain. No dependency, installer, artifact
manager, provider profile, publication manifest or release automation was added.
Linux installed Codex/Claude are the acceptance target. Other platforms, models,
watcher timing and helper/asset execution are explicit limits. Atomic replacement
requires directory/ownership permissions; ACLs, xattrs, inode/hard-link identity,
power-loss durability and concurrent preparation are not guaranteed.

No private/credential/vault/student/library data operations, global client
changes, external runtime changes, push or main release are authorized. Only
develop owns Linear, final ledger ticks and integration.

## Ownership and Execution

Parent coordination Run is `run_e7efe7303f0e`; feature Run is `run_1286efbc5cf6`.
The native feature coordinator owns Spec records, exact ownership and one commit
writer; substantive implementation, batch verification and review use native
Orca workers. The current exact-file plan is authoritative at
`~/.local/state/verbose-broccoli/workspaces/feature-live-plugin-discovery/che-82/ownership-plan.json`.
The lost disposable reboot plan was reconstructed; 894 retained native/paid
artifacts were copied and hash-checked in `retained-before-storage/` without
repeating completed calls. Completed captures are immutable; each new attempt
uses its injected Dispatch directory set in initial instructions. `.local/`
contains disposable editor copies. Supported tool metadata keeps its own paths.

Use workflow task `che-82`, base
`fd52a3c9fe6b0104e3b1d19671a756e2033f5947` and that plan before edits, after scope
changes and before completion. All batches use CPUWeight 20, nice 10 and CPUs
4-7; interactive sessions remain unpinned. Develop serializes full verification
and integration. Real command exit and the same-run summary govern validation;
source changes require renewed evidence. Fresh final review differs from every
implementing provider, receives only final scope/requirements, and includes the
current main-owned policy revision-2 packet.

## Validation and Evidence

Regressions cover canonical metadata and live/index links, resource/rule/helper
resolution, source edits, missing/stale/duplicate paths, user settings/conflicts,
XDG defaults/isolation, relocation, optional distribution, denials, torn and
completed writes, cleanup and byte-exact reruns. The two newly demonstrated
path/separator cases fail against the prior source and pass after closure.
Native discovery/invocation and metadata-only MCP evidence are retained with
source readback; two changed-behavior Claude probes used realpath then native
Read of the canonical owning rules, with strict empty MCP and no data calls.

Primary references: [Codex skills](https://learn.chatgpt.com/docs/build-skills),
[Claude skills](https://code.claude.com/docs/en/skills),
[marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), and
[manifest paths](https://code.claude.com/docs/en/plugins-reference).
Document judgments use bounded genuinely changed units and retained text/source
matches; advisory findings have source-based dispositions, not final approval.

Operational limits are recorded separately: four raw files from an earlier
failed verification were overwritten; original failure report/summary/receipts
and two hash-verified restorations survive. One unreserved passing run retained
its scheduling error; the existing workflow's before/after all-source guard and
current-content comparison established technical identity without a retroactive
grant. These do not change the current source's verification claims.

## Measured Size and Split Review

Before build: 150-300 production lines; storage amendment: 50-100 additional
lines; final narrow closure: 5-15 lines, each an estimate rather than a cap.
Current final production delta: generator +421/-6 (net +415) and existing hook
+6/-0. Focused regression delta is +1363/-9. The final whole-feature diff exceeds
1,000 changed lines; exact current totals are recorded below after compaction.

Keep one feature: unique names precede the shared index, and discovery, MCP,
ownership, atomic writes and cleanup share one preparation route and acceptance.
No independent package or publication capability needs splitting. Fresh review
may challenge this judgment. Historical interim figures remain in Git and
immutable task evidence; they are not presented as the current total.

Current whole-feature totals: 78 files changed, 2433 insertions(+), 72 deletions(-).
