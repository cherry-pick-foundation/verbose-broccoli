# Bug Verification: Plugin server loading

- **Slug**: plugin-server-loading
- **Tested**: 2026-10-02
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: pass (repository and synthetic client checks)

## Assumption and boundaries

Client packages retain checkout dependencies. Saved-client settings and
installed caches remain unchanged; the preview below requires approval.
All client behavior probes used synthetic configuration without credentials,
private vaults, rosters, saved sessions or external model requests. The
connector endpoint was replaced with unused loopback port 9.

## Checks performed

| Check | Result | Evidence |
| --- | --- | --- |
| Failing regression before the fix | pass | `npm run test:plugin-skills`: 2 passed, 1 failed; expected `backfire-code`, observed `backfire`. |
| Focused tests after the fix and resume | pass | Same command: 4 passed, 0 failed; source readback, distinct modes, copying, regeneration, bad input, duplicate identities, interrupted writes, resource links and storage budget. |
| Portable schemas and preparation | pass | `npm run plugins:prepare` validated both schemas and produced the ignored distribution. |
| TypeScript, lint and import policy | pass | `npm run typecheck`, full `npm run lint` and workflow graph policy completed. A generated-copy lint fixture failed before excluding `.local/` and passed afterward. |
| Document references | pass | `npm run doc-regions:check`: no problems. |
| Claude Code 2.1.287 | pass | Isolated configuration; validated prepared plugins; `claude mcp list` connected `plugin:code:backfire-code`, `plugin:work:backfire-education`, `plugin:work:reference-library`. |
| Codex 0.159.2 | pass | Supported local marketplace install in isolated `CODEX_HOME`; `codex mcp list --json` returned all three servers and correct mode arguments. |
| Codex live discovery | pass | App-server `mcpServerStatus/list` discovered 12 tools for each Backfire mode and 28 for the connector. |
| Supported same-version refresh | pass | Replaced Work's isolated installed `0.1.0` declaration with an empty server list; education disappeared. `codex plugin add work@verbose-broccoli` restored all declarations without a version bump. |
| Modes and continued service | pass | Both client-resolved Backfire commands initialized. Malformed `jev_decide` arguments failed; subsequent `tools/list` returned 12 tools. Valid synthetic requests reached Work's missing `education.toml` gate and Code's missing provider configuration; another `tools/list` succeeded after each refusal. |
| Full repository verification | pass | CPU-wrapped `npm run verify`, exit 0; 47 successful Turbo checks, 47 total; same-run summary `3K6ciYHVUCVOZqfd3y1d2rGnnUw`, execution exit code 0 and failed count 0. Feature and develop base were `965afb9938078d8121306e44f680b24b8ff5970e`. |
| Saved clients | metadata only | Earlier selected readback found the user-configured `reference-library` and no selected Backfire server. Only names, enabled state, transport type and the education flag were reported. |
| Operational data, model turns and individual copied skills | not run | No library operation, real roster/vault input, client agent model turn or external model request. Preparation does not prove every copied skill's runtime behavior. |

Batch commands used `systemd-run --user --scope -q -p CPUWeight=20 nice -n 10
taskset -c 4-7`; no other `turbo run` was active before full verification.
The synthetic CLI and JSON-RPC probe is
`.local/plugin-server-loading/client-smoke.py`; its resumed readback is
`client-resumed.log`. Full output is `verify-native-resume.log` in that same
ignored scratch folder. Sources were frozen throughout verification.

## Document judgments

Three completed `jev_verify` development requests covered 282 units:
6 verified, 2 contradicted, 274 unsupported and 45 flagged for review.
The old server-name claim was corrected. The flagged canonical command
block stands because its source arguments are unchanged; its next paragraph
explains preparation before copying. Other flagged target units are headings
or unchanged descriptions not established by this manifest diff. Changed
architecture passages agree with source manifests, the writer and actual
isolated client readback. No target unit remains contradicted.

Report-only findings were 8 constitution and 11 root `AGENTS.md` units
flagged for insufficient diff evidence. Memorylint 1.5.1 reported 20
constitution warnings, mainly boundary suggestions; its missing
`scripts/workflow.ts` claim is false. These files remain unchanged and the
advisory findings are reported to develop. The required complexity pass
found no extra abstraction; it does not give final approval.

## Saved-client preview and integration

`git worktree list --porcelain` confirms `main` holds the main branch and
primary `.git`, while the permanent `develop` checkout is
`/home/choi-eunchang/workspaces/verbose-broccoli/develop`. After integration,
confirm its branch and run CPU-wrapped `npm run plugins:prepare` there.
Installed runtime references must point at that permanent checkout.

The following supported commands would update the saved Codex marketplace
source and refresh Code and Work. They have not run in the saved client:

```sh
codex plugin marketplace add /home/choi-eunchang/workspaces/verbose-broccoli/develop/.local/plugin-clients --json
codex plugin add code@verbose-broccoli --json
codex plugin add work@verbose-broccoli --json
```

The preview changes `marketplaces.verbose-broccoli`'s source path and enables
Code and Work. Their installed MCP files derive from the prepared declarations.
An existing user server with the same name remains a separate precedence
question. Claude can load the prepared directories with `--plugin-dir` in a
new invocation; persisting that path needs a separately approved change.
No saved configuration file is proposed as a second maintained declaration.

Develop owns saved-client approval, the serialized finish, Linear and final
ledger updates. The independent merge review must be recorded by a
content-free tip commit naming its actual reviewed parent. Earlier verification
attempts rejected a changed snapshot or were interrupted; only the completed
run above counts. This task resumed after Orca restart with its uncommitted
patch preserved and the permanent checkout paths rechecked.
