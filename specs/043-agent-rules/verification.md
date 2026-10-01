# Verification record

Assumption: these initial results validate the resolved draft, not feature
completion. The four decisions are applied and CHE-74 is integrated; final
integrated verification has passed. The independent review remains pending.

## Initial draft, 2026-10-02

The exact existing `orca.yaml` setup block ran under
`systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7`.
The system Python parsed the block without changing it; the mise Python shim
had refused the untrusted worktree before setup. The unchanged setup then
trusted the configuration and all 13 doctor checks passed. The branch script
left this checkout on `feature/agent-rules`.

The Linear ownership regression failed before the source fix (one test, one
failure). After the fix, `npm run test:workflow` passed all 45 tests.
`git diff --check`, `npm run lint:names`, `npm run doc-regions:check` and the
workflow import-policy check passed; policy reported zero errors or warnings.
Clean Code scope reported zero selected files and zero scope errors, so no
Clean Code review applies. The Ponytail review of the two changed workflow
files found no added complexity; no implementation or dependency was added.

Source coverage accounted for root eight, code two, work ten and chat one
merged entries, including pending dispositions. All three plugin rule pointers
resolved, model-choice's code-rule pointer resolved, and its deleted dispatch
pointer was absent. Coverage does not settle the four pending decisions.

The initial full `npm run verify -- --task CHE-80` passed with VERIFIED and the
same Turbo run summary. Its log is in ignored `.local/che-80-verify.log`.
This run predates integration of develop's CHE-74 merge, so it is not the final
integrated-tree result. All batch checks used the CPU wrapper; no other
`turbo run` process was found before this full run.

## Rule audit

MemoryLint 1.5.1 returned 20 warning findings for the constitution: 19 boundary
classifications and one reality finding. They are report-only. Seven boundary
findings classify the sync-impact comment as active rules; other findings ask
to move existing storage, privacy and workflow clauses. None authorizes a
constitution edit in this feature. The reality finding at constitution line 13
claims `scripts/workflow.ts` is absent; that path exists and was read and tested
in this run, so that claim is false for this checkout. No audit-driven
constitution change was made.

## Client and runtime limits

This feature inspected current worker-start help and its version-matched guide,
Claude help, Copilot configuration help and Antigravity's live catalog. Copilot's
saved JSON-with-comments configuration exposed no explicit model, tier or
effort values in the selected fields, so it is not a proven model-choice
candidate from that evidence. No settings were changed. Cursor's tracker still
shows an Oct 16 free-plan reset, but a zero usage reading does not revoke the
supplied limit refusal without fresh successful-use evidence.

Native launch, ask/reply, follow-up, stop/release and nested-worker test facts
in the dispatch were supplied by the coordinator; this feature has not yet
repeated them. Fresh Claude/Codex automatic rule loading, a new Copilot launch,
Grok launch support, external client installation, web-chat account capability
and live education behavior have not been tested here. No student/raw/vault
data or credential contents were read or written. External client settings were
not changed; only selected Copilot launch-configuration metadata was inspected.

Initial document judgment requests were prepared before develop integration
but not sent. After integration, requests were regenerated and five tool calls
judged 297 units on OpenRouter `typesafe/jev-1.13`: 24 verified, 270 unsupported,
three contradicted and 106 requiring review. Most units are unchanged and the
feature diff supplies no evidence for them. The active
architecture wording assigning the judgment step to the main agent is changed
to the feature orchestrator; the two other contradiction flags concern
unchanged text with low confidence and are retained with reasons. No
report-only constitution rule was changed by this judgment pass.

## CHE-74 integration, 2026-10-02

The resolved draft was committed as `fd95f7a`. The first merge stopped at the
commit hook because CHE-74 moved the mise configuration to an untrusted path.
The uncommitted merge was aborted. The same no-fast-forward merge was then
staged, the authorized `.config/mise.toml` trust applied, and the single
`mise run setup` task ran unchanged under the CPU wrapper. All 15 current
doctor checks passed. The default merge message and normal commit hook produced
`18e77dc`, integrating develop `3d4613f`; develop is its ancestor. No merge
conflict was encountered or resolved by hand. At that checkpoint, final
decisions and integrated verification/review remained pending.

Develop then required a Git pause for moving the repository's Git directory
from develop to main. Git quiet was confirmed: no active Git-dependent command
or child Dispatch remained. Setup, workflow, verification, Git and helpers
that invoke Git stay paused until develop forwards Resume git. Ordinary
document/report reads and edits continue within the feature scope.

The original ask then returned the delegated choices A/A/A/B, now recorded in
coverage.md and applied without widening their scope. The new plugin rule files
join document-region report-only inputs. A CPU-wrapped file-only Python check
passed for final source counts 8/2/10/1, all four rule pointers, deleted-pointer
absence, develop's Linear ownership and all three report-only plugin inputs.
Git-dependent checks still await Resume git; the pause does not imply feature
completion.

## Resumed final checks, 2026-10-02

After Main's explicit Resume git, Git confirmed the common directory at
main/.git, this branch unchanged at `18e77dc` and develop unchanged at
`3d4613f`. The final workflow uses CHE-80 and base develop; it requests REVIEW
mode and reports difficult from 16 paths and 775 changed lines at that
checkpoint. Main reports unchanged status/HEAD for seven worktrees and unchanged
64 refs; this feature confirmed its own branch and develop as above.

The current focused workflow tests pass 45/45; names lint, document-region
checks and `git diff --check` pass. Both impact bundles report zero errors and
warnings, three files and two dependencies. The actual document configuration
loader selects root, constitution and all three plugin AGENTS.md files as
report-only, with no overlap with update targets. Rule audit still returns the
same 20 constitution warnings described above and no plugin-rule findings.

Four final Jev-only OpenRouter calls judged all 331 prepared units: 30 verified,
300 unsupported and one contradicted; 113 require review. Every final flag is
listed with its disposition in [document-judgments.md](document-judgments.md).
The sole contradiction is the unchanged constitution sync comment, confidence
0.13; it remains report-only historical context. No automatic finding widened
the requested source scope or approval boundary.

Four additional Jev-only calls chose the other-provider reviewer, model, effort
and time budget, recorded under T005. This feature has made 13 successful Jev
tool calls: nine document judgments and four review choices. Supplied domain
decision results are separate. Full verification and native reviewer launch
precede the finish request; no final approval is claimed here.

The integrated full `npm run verify -- --task CHE-80 --base develop` passed:
VERIFIED and same-run summary `3K6Q6PIdtTtAQllF9naKmJMzaaI`, 47 successful
tasks, zero failed, exit 0. The log is ignored `.local/che-80-final-verify.log`.
This includes the final rule, consumer and decision edits. Recording this
result changes only feature records; the committed review tip is verified again
before reviewer launch so the report update is not an unverified final tree.
