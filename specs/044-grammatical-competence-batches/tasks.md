---

description: "Task list for grammatical competence profiles, later batches"
---

# Tasks: Grammatical Competence Profiles, Later Batches

**Input**: Design documents from `specs/044-grammatical-competence-batches/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: No repository code changes; acceptance is operational: copy
digests read back, `raw_import.py verify`, the vault's Wiki check and the
counts per material. `npm run verify` runs on the result merged with
`develop`.

**Organization**: One feature orchestrator (currently Codex `gpt-6.1-sol` at
`xhigh`) owns these records and the vault steps and asks the develop session
for the user's decisions. Proposers are Orca workers: Codex `gpt-6.1-sol` at
`xhigh`, one per material (the user's fixed choice). The final review comes
from a provider other than the implementer's.

**Private data**: No task writes source names, source text, inventory text or
student data into the repository, commits, or Orca or Linear messages. The
exact file lists and checks are in the private survey folder
(`~/.local/state/verbose-broccoli/grammatical-competence/survey/`).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [x] T001 Write `spec.md`, `plan.md` and this file.
  - 2026-10-02: setup ran from `orca.yaml` under the CPU wrapper, then again
    through the single `mise run setup` task after CHE-74 merged (develop
    `3d4613f`, merged into the branch); `npm run doctor` passed.
  - Model choice for this orchestrator (launch evidence from the develop
    session; probabilities do not prove correctness): backfire Jev
    (OpenRouter `typesafe/jev-1.13`) chose Claude (0.69, confidence 0.62),
    then Sonnet at high effort (0.50, confidence 0.44), for a difficult
    operational scope; Codex weekly use was 68% until 2026-10-03T17:28:48Z,
    Claude session 16% and weekly 55%. The proposers are not chosen this
    way: the user fixed Codex `gpt-6.1-sol` at `xhigh`.

---

## Phase 2: User Story 1 - Reconcile what remains (P1)

- [x] T002 [US1] Compare the survey list with the 63 recorded profiles by
  SHA-256 and dedupe.
  - 2026-10-02 (read-only): of the survey's 512 materials, 63 have a
    profile (55 textbook volumes, 7 office papers, 1 listening paper). The
    historical 439 candidates are now 438: 46 textbook volumes of the 2015
    curriculum, 85 national papers, 133 education-office papers (the survey
    listed 140; 7 are profiled) and 174 middle-school exams, plus 7 photo
    sets that stay out.
  - Not repeated: 11 of the first batch's volumes show as `partial` only
    because the survey also lists 45 HWP copies of lessons that were
    profiled from their HWPX twin (every one has a twin of the same name).
    3 more 2022 entries are whole-book publisher PDFs, not main-text
    worksheets; they are left out.
  - Duplicate: one loose paper is the same file (same SHA-256) as an office
    paper; it counts once. Two office papers and two 2015 files are already
    admitted in the vault but have no profile.
  - Hash groups across stores do not matter for the new lists, because each
    list names one source path per digest.
- [x] T003 [US1] Convert every listed file to text, read-only.
  - 2026-10-02: 1,144 files (every listed file of the 512 materials) with
    `pdftotext -raw` and python-hwpx through markitdown, in the CPU wrapper,
    3 processes. 16 zip members first failed in my script only (a name
    decoding bug), then read after the fix.
  - Left out: 13 national papers that are scanned PDFs without text; 7 papers
    (6 national, 1 office) whose old HWP files the converter cannot read, so
    the user may convert them first; 2 more files inside materials whose other
    files are readable (1 scanned PDF in a national paper, 1 unreadable HWP in
    an office paper); 7 photo sets (46 JPGs); 4 HWP twins in
    2015 volumes.
  - Result: 418 materials can be profiled: 46 textbook volumes, 66 national
    papers, 132 office papers, 174 middle-school exams.
- [x] T004 [US2] Write one exact file list per batch in the private survey
  folder (`lists-2026-10-02/`): source path, SHA-256, size, destination.
  - 2026-10-02: textbooks-2015 46 volumes, 324 files, 59 MB; education-office
    132 papers, 133 files, 131 MB (all inside zips); national-papers 66
    papers, 80 files, 121 MB (34 inside zips); school-middle 174 papers, 174
    HWP files, 50 MB; `excluded.tsv` has the reasons. English letters read:
    1.54 million, 2.81 million, 1.82 million and 1.40 million; at the first
    batch's rates about 25,000, 33,000, 21,000 and 16,000 sentences (the
    first batch had about 15,600).
  - Exam destinations are per-paper folders because 17 file names collide.
  - Dry run, nothing copied: the SHA-256 of all 711 listed files, read
    again from the originals (zip members included), equals the lists'.

---

## Phase 3: User Story 2 - The user's decision (P1)

- [x] T005 [US2] Ask the develop session for the user's batch order and the
  first batch's exact-list approval.
  - 2026-10-02: asked with counts and the recommendation 1 (2015 textbooks)
    then 2, 3, 4, because the 2015 textbooks use the same worksheet format
    as the profiled 2022 ones, have no unreadable file, and the 2024 to 2026
    grade-3 school exams belong to the 2015 curriculum, so their link to a
    textbook needs batch 1. A first wave of 12 volumes measures real Codex
    `xhigh` use before the rest.
  - 2026-10-02: the user approved the order (2015 textbooks, education-office
    papers, national papers, school exams) and the exact first list: 46
    volumes, 324 files, 59.1 MB, copied (never moved) into
    `~/Documents/20_reference/textbooks/`, then a first profiling wave of 12
    volumes, then a measurement of Codex use before the rest. The exam
    batches' lists and the per-paper folder layout need their own approval
    before any copy.

---

## Phase 4: User Story 3 - Profile the approved batches (P1)

Waits for T005. One block per approved batch.

- [x] T006 [US3] Copy the approved files; read each destination's SHA-256 back
  and compare with the list; write the selection; `raw_import.py admit` and
  `verify`.
  - Batch 1 (2015 textbooks), 2026-10-02: 324 files copied, never moved, into
    `~/Documents/20_reference/textbooks/` (the folder went from 294 to 618
    files); the SHA-256 of all 324 copies read back equal to the list's, by
    the copy script and again by `sha256sum -c`; all 324 originals still
    exist. `admit`: 324 admitted, 0 already admitted, 0 refused, 0 failed.
    `verify`: 771 revisions, 0 invalid. Vault commit `50312ca`.
- [ ] T007 [US3] (batch 1: 46 of 46 recorded) Per material: `inventory`, `extract`, one native Orca worker
  (Codex `gpt-6.1-sol`, `xhigh`), `record --unchecked`; counts per material
  in this file.
  - 2026-10-03 final textbook closeout: all 46 approved volumes are recorded unchecked, with 21,505 sentences and 512,862 matches (zero dropped or unclear). The six saved proposals contributed 1,986 sentences and 40,139 matches across 51 sources; complete structural, inventory, source-order, uncovered-text coverage and record-readback checks found zero failures. The earlier 40 profile pairs match vault commit `f7248f8` byte for byte; all six saved run folders and their paid outputs are retained unchanged.
  - Final-six ordinal sentence/match counts: 41: 259/5,499; 42: 294/5,957; 43: 317/7,082; 44: 270/6,150; 45: 491/8,483; 46: 355/6,968. The 475 uncovered spans containing Latin letters were inspected and excluded as headings, labels, phrase-only material or non-English translations; zero full English sentences remain unresolved. Hash-bound dispositions are in the closeout evidence folder.
  - 2026-10-02 reboot pause: 40 volumes remain recorded; all six final proposers (41 to 46) succeeded and were released, with worker-reported totals of 1,986 rows and 40,139 matches across 51 sources. Their six private run folders remain; parent validation is complete only for 41 and remains pending for 42 to 46, before later unchecked recording.
  - Resume from private `survey/lists-2026-10-02/textbooks-2015.tsv` and Run `run_d56f85e2efc3`, coordinated by `structworker_b0565862-30b6-4726-acb3-63ac0e71a861`; child Task/Dispatch IDs remain in that Run. Parent Task `task_40cc757a9328` / Dispatch `ctx_9b26bdbec20e` was stopped before reboot, so fresh develop direction and authority are needed before continuing.
- [ ] T008 [US3] (all 46 textbook records persisted) `wiki-consistency` `update` and `check`, the log entry, a
  vault commit per batch, and the run folders deleted after their record
  commits.
  - 2026-10-03 closeout evidence is retained under `~/.local/state/verbose-broccoli/workspaces/feature-grammatical-competence-batches/che-71/final-textbook-closeout/ctx_4a0389b23feb/`. All 324 approved originals, copies and admitted payloads match the listed digests; raw integrity passed 771 revisions with zero invalid. Wiki update passed; changed records have zero check findings, while two date findings on unchanged unrelated pages remain. Vault commit `79441fb` records only the final six profile pairs, generated index and append-only log; the vault is clean. Conversion reused 52 cached revisions; preparation made zero judgment requests and reported six record-description units unverifiable against bounded raw evidence. Keyword indexing is preserved, but semantic search, page comparisons and cross-reference searches remain unavailable. Develop approved stopping only the owned whole-corpus embedding processes, with exit and cache/output preservation proof retained; no saved run folder was deleted.
  - 2026-10-02 reboot pause: vault commit `f7248f8` remains clean; the earlier repository verification passed 47/47 tasks before this pause note. Final-six Wiki work, recording commit, run-folder cleanup and independent review remain pending; no workflow or verification was run for the user-authorized pause note.

  - Batch 1, wave 1 (first 12 of 46 volumes), 2026-10-02: 12 profiles recorded
    unchecked, 7,563 sentences, 189,998 items, 0 dropped, 0 unclear
    (432, 565, 665, 357, 404, 888, 1,057, 814, 562, 769, 486 and 564
    sentences per volume). Proposers: Codex `gpt-6.1-sol` at `xhigh`, native
    Orca workers; 6 of the 12 were restarted from their partial files after
    Orca closed (the old sessions ended). Local checks of each proposer: 0
    failures; `record` refused no row. Wiki check on the changed pages: 0
    problems (108 problems on earlier pages remain, CHE-58); judgment step: 0
    requests, 12 units unverifiable because they describe the records;
    semantic search was not ready (keyword search ran). Vault commits
    `50312ca` (admission) and `730b168` (profiles); the 12 run folders were
    deleted.
  - 2026-10-02 resumed phase: live reconciliation found 34 recorded volumes
    (17,082 sentences, 423,758 matches), with 22 profile pairs uncommitted.
    Six native Codex `gpt-6.1-sol` / `xhigh` proposers resumed volumes 33 and
    36 to 40; all settled and were released. Recorded unchecked: 2,437
    sentences and 48,965 matches; per-volume sentence/match counts are
    33: 578/14,860; 36: 463/8,098; 37: 318/6,021; 38: 382/6,469;
    39: 363/7,139; 40: 333/6,378. Source order, containment, keys, no Hangul,
    coverage passes and saved-record comparisons found zero failures.
    All 34 earlier profile pairs remain byte unchanged; all 324 approved
    originals, copies and admitted payloads match their listed digests.
    Total: 40 profiles, 19,519 sentences, 472,723 matches; zero dropped or
    unclear items. Volumes 41 to 46 remain queued, with 51 approved files
    and no run folders prepared; no new input is needed beyond develop's
    next phase direction. Exam-list approvals remain pending.
  - T008 resumed phase: updated the index, checked the Wiki, reused 196
    readable cached revisions, and prepared zero judgment requests.
    The 28 record-description units were unverifiable against bounded raw
    evidence. Semantic search remained unavailable after embedding
    completed; page comparisons and cross-reference searches did not run.
    The post-log command found zero profile/index/log findings and two
    existing date findings on unchanged unrelated pages: the whole-vault
    check is not fully passing. Develop explicitly accepted these limits
    for this phase. Vault commit `f7248f8` records the 22 preserved and six
    resumed profiles, index and log; 28 completed run folders were deleted
    after that commit. Repository verification uses task
    `task_40cc757a9328` and baseline `f91aec6`; final ticks and review remain
    with develop. No executable code was added.
  - Codex use: the weekly window went from 68% to 73% used (CodexBar, read
    2026-10-02 05:03 KST), with every Codex session counted, so at most 5
    points for this wave, about 0.66 points per 1,000 sentences. The rest of
    batch 1 (34 volumes, about 17,000 sentences at the survey's letter
    counts) would take about 11 points, the three exam batches (about 70,000
    sentences) about 46 more. The window resets 2026-10-03T17:28:48Z.

---

## Phase 5: Review and finish

- [ ] T009 Merge the latest `develop`, run `npm run verify` (one full run at
  a time on the machine, in the CPU wrapper), measure the change against
  `develop`, move the board status to `in-review`.
  - 2026-10-03 closeout: current-develop integration, full verification and independent review receipts belong in the immutable Dispatch evidence folder named under T008; its final `report.md` is the handoff. Develop owns review acceptance, integration, final ticks and remaining batch approvals.
- [ ] T010 Fresh review from another provider that its data scope permits;
  record the reviewed commit; ask the develop session for the finish slot;
  never push, release or merge into `main`.

Phase 3 and admission are complete; the profiling notes above state current
progress. Phase 5 review and integration remain unperformed.

---

## Handoff (2026-10-02, pause before Orca closes)

Historical restart notes follow. Current phase notes above supersede their
runtime handles, unfinished counts and next steps; Git records commit state.

- **Orchestrator**: Claude Code, Sonnet 5.5, high effort, session ID
  `7aaee383-1ce0-4932-9e82-056a0e824bbf`; branch
  `feature/grammatical-competence-batches` (its own folder); its Orca
  dispatch `ctx_a181488bb17e` under develop's run `run_8b222073b123`; its own
  child run for proposers `run_af91f417141f`.
- **Step**: batch 1 (2015 textbooks), first profiling wave of 12 volumes, in
  the order of the first 12 rows of the private list
  `lists-2026-10-02/textbooks-2015.tsv` (called v1 to v12 here; run folder =
  the row's material ID). Copy, admission and raw `verify` are done (T006).
- **Recorded unchecked in the work vault, not yet Wiki-checked or committed
  there** (profile page and data file each, vault Git shows them untracked):
  v1 432 sentences, v2 565, v3 665, v4 357, v6 888. Helper scripts (rec.py, finish.sh, brief.txt, copyfiles.py, prep.py) are in
  `/tmp/claude-1000/che71/`, not in the repository, and may be gone after a reboot:
  `record --inventory inventories/english-grammar-profile.md --name <ID>
  --title <title> --summary <line> --proposer 'Codex, gpt-6.1-sol, xhigh'
  --unchecked`, run from the skill folder with `--run <ID>`.
- **Proposers in progress** (Codex `gpt-6.1-sol`, `xhigh`, native Orca
  workers, one per volume; partial `proposals.jsonl` in each run folder under
  `~/.local/state/verbose-broccoli/grammatical-competence/`): v5 403 rows
  (dispatch `ctx_651cbe10a1f3`), v7 no file yet (`ctx_4fe7d152ad9a`), v8 813
  rows (`ctx_41f487f24681`), v9 no file yet (`ctx_394ef8707874`), v10 768 rows
  (`ctx_8d8e0c189bb1`), v11 486 rows (`ctx_9f565081fb5b`). A proposer is an
  agent-chat session that ends when Orca closes; restart it natively with the
  same brief, and tell it to keep and re-read its partial file (a worker can
  rewrite the whole file, so check that rows stay in text order and every
  sentence is covered before `record`).
- **Not started**: v12. Run folders for v1 to v12 already hold
  `inventory.tsv` and `text/` from `inventory` and `extract`.
- **Brief used for every proposer**: the procedure's "Proposals" section and
  tier rule, the run folder's `inventory.tsv` and `text/*.txt`, output
  `proposals.jsonl`, own checks (JSON, keys, text in extraction, no Hangul),
  then `worker_done` with counts only.
- **Next steps**: restart v5 and v7 to v11 and start v12 (six at a time,
  `worker-start --agent codex --model gpt-6.1-sol --effort xhigh --worktree
  current`); on each `worker_done` run `record --unchecked` for that volume
  and release the worker; then `wiki-consistency` `update` and `check`, the
  vault `wiki/log.md` entry, one vault commit; measure Codex weekly use before
  and after the wave and report it; ask develop whether to continue with the
  other 34 volumes; the exam batches need their own list approvals. Then T009
  and T010.
- **Open questions**: none for the user; the exam batches' lists and per-paper
  layout await approval after batch 1.
- **Codex use**: no usage-limit error so far.
- **2026-10-02 after Orca restarted** (Resume all received): the six Codex
  proposers had exited; each was fenced (`worker-stop`, then `worker-abandon`
  after Orca showed it exited) and released. Six replacement workers (Codex
  `gpt-6.1-sol`, `xhigh`, new tasks with a resume note: re-read the partial
  file, keep it if valid, append the missing rows) now run for v5 and v7 to
  v11: dispatches `ctx_03ef9fa3ca93`, `ctx_22174ec9a6dd`, `ctx_946ff2582e52`, `ctx_8e76edce2981`, `ctx_c53473b5a90b`, `ctx_1992e9b728b5`. v12 is not started.
  The old dispatches `ctx_651cbe10a1f3`, `ctx_4fe7d152ad9a`,
  `ctx_41f487f24681`, `ctx_394ef8707874`, `ctx_8d8e0c189bb1` and
  `ctx_9f565081fb5b` are abandoned.
