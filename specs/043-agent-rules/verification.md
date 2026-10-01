# Verification record

Assumption: these results validate the checkpoints named below, not feature
completion. The four decisions are applied and CHE-74 is integrated. The
review's consumer fixes are verified; a supported fresh final review remains.

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

## Latest-develop integration and first review

The committed tip `6273bba` passed full verification with summary
`3K6RBoUIimtMY7ZxDKkwxakpr7F`: 42 successful, five cached, zero failed.
Develop then added two ledger-only commits, `808896d` and `965afb9`.
They were integrated without conflicts as `e371b73`; develop `965afb9` is
its ancestor. An inadvertently overlapping verification completed before it
could be stopped; `.local/che-80-latest-verify.log` is excluded from acceptance.
After no other Turbo process remained, an exclusive CPU-wrapped run passed:
VERIFIED, summary `3K6UEtKT69TdboGpoBT0fqWtZZz`, 16 successful, 31 cached,
47 attempted, zero failed, exit 0. Prepared request bodies and all 331 units
were byte-identical to the four already judged requests, so those results
were reused without additional model calls.

The first native Claude review settled and was released. Its source findings
are preserved in ignored `.local/che-80-final-review.md`: missing plugin-rule
reads outside the repository, stale committed verification evidence, and a
shared-operations ownership gloss outside this feature's writable scope.
The latter was relayed to develop. The native receipt reported fable/high,
but develop later confirmed that Orca lost the alias and the session ran Opus.
This review is not final acceptance. New native Claude launches use full model
IDs and must check actual assistant message.model; that field does not prove
reasoning effort.

The consumer fix adds only one relative rule pointer to each of 48 skill
entrypoints. The existing isolated-package test now copies the plugin rules
and checks every entrypoint's pointer and resolved destination. Before the
pointers were added, it failed on the missing code/backfire pointer; afterwards
all three tests passed. Fresh client loading from another directory remains
untested; the checks prove packaged resource reachability, not client behavior.

Main paused all work for the checkout layout change, then develop forwarded
Resume all. Explicit branch checks now confirm that the folder main holds
develop and the folder develop holds main; this feature stayed on its branch.
The first focused lint command incorrectly appended a TypeScript path to the
combined Python lint command, which failed while parsing it as Python; that
invocation is not source verification. A direct gts single-file invocation
also exited 1 without lint diagnostics. The correct configured `npm run lint`
then passed (exit 0, Python reports All checks passed). Names lint and
document-region checks passed with no problems. All 48 entrypoints are
byte-identical to HEAD after removing exactly their one inserted pointer.
The renewed impact check passed; Clean Code still selects no files. The
Ponytail review of the three changed TypeScript paths found no added abstraction
or dependency; the new assertions extend the existing isolated-package check.

The pointer/model-ID tree passed exclusive CPU-wrapped full verification:
VERIFIED, summary `3K6aGtfFbMH7OBCGjKaxBdjEBPZ`, 42 successful, five cached,
47 attempted, zero failed, exit 0. The audit still reports only the same 20
constitution warnings. New document preparation has the same 331 unit records
but 28 request groups because the 48 pointer files enlarge the evidence list.
Develop is deciding whether to repeat that batch or retain unchanged-unit
dispositions with a bounded judgment of the new consumer claims; this is pending.
Four renewed review-choice calls bring this feature's successful Jev count to 17.

## Restart resumption, 2026-10-02

The fresh Dispatch preserved the committed implementation and owned pointer
edits. Git confirms main/.git, main on main, develop on develop and this
worktree on feature/agent-rules; HEAD includes current develop `965afb9`.
Setup was already completed and CHE-74 integrated; it was not repeated.
The configured workflow ran again with CHE-80/base develop. Packaging tests
pass 3/3 and workflow tests 45/45; document checks report no problems.
All 48 skill files retain every original byte after removing exactly the one
inserted rule pointer; every destination resolves. The active repository
search finds no worker-dispatch.md pointer. The audit still reports only the
same 20 constitution warnings, with the false path claim unchanged.

The coordinator confirmed that one Claude session temporarily holds both
main and develop roles. Shared preferences still define the separate roles;
model-choice's role paragraph remains unchanged pending a user decision.
Fresh Claude usage shows session 2%, weekly 57% and Fable-only 8%, with room
for the previously selected non-Opus reviewer. The full-ID candidate and
native effort route remain supported by current help; no selection retry or
client setting change was needed.

The feature diff at this checkpoint is 65 files, 983 insertions and 46
deletions. The split review retained one feature: judgment rules, their 48
identical pointers and the existing packaging check share one acceptance
boundary; about half the lines are required feature records. The coordinator
accepted this split decision. No new dependency or runtime was added.

Prepared unit hashes matched for all 331 units, but shared evidence hashes
changed, so no earlier disposition qualified for reuse. The coordinator
authorized full rejudgment. One 224-claim attempt was refused with
`max_tokens_exceeded`; its exit 0 was excluded from acceptance. Calls stopped
until the coordinator approved exact pointer compaction and smaller batches.
Four successful Jev-only calls then judged all 331 units and three extra
consumer claims: unit totals 31 verified, 300 unsupported, zero contradicted,
135 review; extra claims all verified, one review. All review dispositions,
snapshot hashes and the 48 before/after file hashes are in
[document-judgments.md](document-judgments.md). This phase made five attempts,
four successful and one refused; feature totals are 21 successful Jev calls.
No fallback, unchanged retry, external settings or private-data access occurred.

The resumed complete tree passed exclusive CPU-wrapped full verification:
VERIFIED, summary `3K6du8i5q7GsBRTihqkrMwAkbYQ`, 42 successful tasks, five
cached, zero failed, exit 0. Its log is `.local/che-80-resume-full-verify.log`. This checks
the pointer/model-ID source and current judgment records. The record of this
result is committed with the diff; verification of that committed tip is the
reviewer's acceptance artifact. The code diff review found no unnecessary
abstraction or dependency; Clean Code scope still selects no files.


## Integrated review corrections, 2026-10-02

Latest develop `c0b630b` was merged cleanly in `5abb75d`. The renewed read-only
Claude Sonnet review of `b687dea` found no privacy, source-fidelity or approval
boundary defect. Its actionable provenance, ownership, report-only and record
findings were corrected: all 14 upstream JSON records describe the pointer
patch without changing source hashes; notices and three provenance documents
agree; model-choice links to canonical code judgment rules; chat links its
current decision record; work rules omit obsolete naming history.

Develop explicitly approved task-coordinator wording in workflow, feature
record commits by the feature orchestrator, and Linear, final ledger ticks and
finish-slot grants by develop. The constitution's main-ownership clause at
lines 167-170 and the shared operations file's old Main gloss remain stale,
outside this writable scope. They were reported to develop. This does not
change standing main/develop model roles.

The Ponytail loader resolves the plugin-rule pointer before injecting it into
session text. Its absolute-link assertion failed before the fix and the
isolated-package check passes afterwards: four packaging tests and 45 workflow
tests passed; document checks report no problems. A formatting check caught
one long test expression and the existing formatter corrected only that file.
The focused complexity review found no added abstraction or dependency.
New local implementation is one string replacement plus the existing test's
reachability assertion; source provenance updates are records, not new runtime.

Four bounded Jev calls rejudged the final 331 units: 45 verified, 285 unsupported,
one contradicted, 142 review. The contradiction is the unchanged constitution's
main-ownership wording, reported without rewriting it. Three new consumer
claims are verified automatically. All review flags, exact hashes and pointer
byte comparisons are in document-judgments.md. All evidence changed, so none
of the earlier responses qualified for reuse. Successful feature calls total
25, with one earlier refusal; no general-model fallback occurred.

The interrupted committed-tip run `3K6e9JLE4nsse3kvmWCs1EOPi54` is excluded:
33 successful plus five cached did not cover 45 attempted tasks, despite its
exit 0 and VERIFIED message. Develop filed the pre-existing gate gap as CHE-81.
Final acceptance requires success plus cached equal attempted, all task exit
codes zero and no cancelled or force-killed tasks. The current audit reports
20 constitution warnings (19 boundary, one false file-absence claim); these
remain report-only and are not acted on here.

Fresh Claude usage at 19:42 UTC is session 12%, weekly 59%, Fable-only 9%.
The selected full Sonnet ID and native xhigh route remain eligible; the final
review will use a fresh native worker. Client loading from another directory
and other native providers remain unperformed. The earlier Sonnet source
review's actual assistant model matched `claude-sonnet-5-5`; effort was shown
only by the launch receipt. Its terminal was released after settlement.

Committed-tip full verification, fresh integrated-tree review and the serialized
finish slot remain pending at this checkpoint.


The integrated source diff is 84 files, 1234 insertions and 98
deletions against develop. The split review retains one feature: the judgment
rules, 48 identical pointers, provenance and consumer checks share one
acceptance boundary; most added lines are feature records. Develop accepted
this split decision. The larger provenance scope corrects records for the same
pointer patch; it adds no capability or dependency.
