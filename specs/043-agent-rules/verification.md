# Verification record

Assumption: these initial results validate the resolved draft, not feature
completion. The four explicit user decisions and latest-develop integration
still precede the final review and finish.

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
data, credential contents or external settings were read or written.

Document judgment requests were prepared before develop integration, but not
sent: the base moved to CHE-74's merge, so requests must be regenerated from
the integrated final diff. Live Jev calls so far: zero.
