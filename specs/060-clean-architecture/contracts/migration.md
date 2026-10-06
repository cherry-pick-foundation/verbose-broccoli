# Migration Contract

## Dependency and Packaging Boundary

Each capability implementation belongs to its workspace package. Source imports
point inward: composition may import adapters/application/domain; adapters may
import application/domain; application may import its ports and domain;
domain may import only its pure rules and required pure dependencies.
No inner layer imports composition, delivery, network, Git or storage adapters.

Use import-linter per Python package and dependency-cruiser for TypeScript.
Preserve workspace cycle and public-entry checks. Package tests demonstrate
forbidden imports fail, pure policy can run without external effects, and
composition connects real adapters. Pure pathlib/datetime-like value handling
must be distinguished from actual filesystem/clock effects where used.

Plugins remain Agent Plugins 1.0 roots. Their maintained role is delivery and
composition, including skills and declared servers. Client-discovered resources
resolve inside the portable plugin root; ordinary declared command arguments
remain external-tool arguments. Copyable skills retain their existing working
delivery contract. Package-owned generated resources have one source and a
deterministic drift/build check; no second maintained implementation is allowed.
Standard npm packaging must pass the copied-skill case before checker deletion.

## Preserved Public Entries

The document-region CLI keeps `doc-regions check|update|prepare|audit`,
the existing explicit configuration argument, command exit behavior and
`__main__.main` invocation. Root task names remain
`doc-regions:check|update|prepare|audit` and `test:doc-regions`.

Preserve these currently consumed module/name pairs:

| Module | Names |
| --- | --- |
| `doc_regions.config` | `files` |
| `doc_regions.regions` | `check`, `scan`, `shape`, `update`, `_split_lf_lines` |
| `doc_regions.requests` | `MAX_CLAIM_CHARS`, `classify_requests`, `verify_requests` |
| `doc_regions.units` | `split` |

Other current supported public behavior is also baseline; this list identifies
the ten known held-consumer names, not permission to remove unlisted exports.
Forwarding modules contain no implementation copies. Protect held consumers
with a package-owned import/behavior test instead of editing their files.

Credit offers keeps `credit-offers --hours|--end|--notify`, the six-hour default,
block-boundary validation, zero calls for empty blocks, one classify call for a
supported populated block, current output/error/exit classes and notification
conditions. The tracker stays the source; no claiming offers or new scheduling
setting is introduced.

Workflow and Clean Code preserve their actual help, JSON, exit and scope
contracts, including the copied-skill check. Native automation entry paths stay
usable from current hooks/configuration and from documented working directories.
The baseline is the existing tests plus independently reviewed positive,
negative and boundary cases, not an implementer-generated expected output alone.

## Data and Ownership Boundary

Structure changes do not move wiki layers, credentials, tool configuration or
live user data. Preserve per-writer budgets, interrupted-write cleanup, source
readback and recovery contracts. Use synthetic fixtures only.

Held scopes: plugins/work, wiki-consistency and jev-ultrafast until the named
feature owners release them; education-privacy-gate until develop coordinates
the metadata bug. Replacement trials also hold plugin-clients, secrets-refresh,
session_select.py and jev-ultrafast implementation. Recheck current sources and
trial decisions before any held scope is dispatched.

## Slice Integration Evidence

Before editing, after scope changes and before completion run workflow with
the same task/base/plan context. Run narrow checks, then full verify under the
prescribed low-priority CPU scope, with no concurrent machine-wide verify.
Record actual outcomes and unperformed cases, not collection counts.

A fresh provider other than the implementer's reviews the current merged-base
tree with only scope/requirements. Resolve actionable findings, rerun affected
checks and renew materially changed review. Review whether to split at 1,000
changed lines, without treating that count as a cap. Obtain develop's serialized
finish slot; current base drift requires integration, verification and review
again. Finish/issue/task ticks remain develop-owned; no push is authorized.
