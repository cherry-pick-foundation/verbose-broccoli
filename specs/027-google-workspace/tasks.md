---

description: "Task list for Google Workspace access through gws"
---

# Tasks: Google Workspace Access Through gws

**Input**: Design documents from `specs/027-google-workspace/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: The repository change is Markdown, JSON and TOML; `npm run
verify` checks packaging, formatting, generated references and document
regions. Acceptance is a real sign-in and a live create, read and delete of
one Doc (constitution V), recorded under T006.

**Organization**: Main (a Claude Code orchestrator) owns the Spec Kit
records, guides the user through the console steps, runs the sign-in and the
live check, reviews each worker's diff and commits it. Every worker's agent,
model and effort is chosen with the code plugin's `model-choice` skill; the
final review comes from the provider other than the implementer's.

**Private data**: No task writes a student name or record, a credential, or
the contents of a credential file into the repository or into Orca or Linear
messages.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US4)

---

## Phase 1: Security check

- [x] T001 [US1] Review gws v0.22.5's source and Linux release assets
  read-only in two parts: A, runtime (network, telemetry, updates,
  credential storage, token handling, environment); B, release provenance,
  dependencies and the agent skills (FR-001; plan.md R2).
  - 2026-09-30: two Codex workers on `gpt-daybreak-blue-latest` at xhigh
    (backfire: 0.48, confidence 0.41). A: install with limits (0 high,
    4 medium, 3 low, 3 info). B: do not install unchanged (1 high, 4 medium,
    2 low, 2 info), for six RustSec advisories in the lockfile; B's
    follow-up rated them three low and three not applicable for this use.
    The user chose the signed release unchanged (spec, Clarifications).

## Phase 2: Google Cloud setup (user, guided)

- [x] T002 [US2] Bring the scope list to the user before the consent screen
  (FR-004). 2026-09-30: approved as proposed.
- [x] T003 [US2] Guide the user through the project and the APIs (FR-003).
  2026-09-30: the user created project `endless-orb-510203-v7` in the
  cherry-pick.org organization and enabled the Drive, Docs, Sheets, Slides,
  Forms and Calendar APIs.
- [x] T004 [US2] Guide the user through the Internal consent screen, the
  declared scopes and a Desktop client (FR-003). 2026-09-30: done; the app
  is "verbose-broccoli-gws" and the client kept Google's default name,
  "Desktop client 1".
- [x] T005 [US2] Move the downloaded client file into the approved folder
  (FR-005). 2026-09-30: `~/.config/gws/` created at 0700; the file moved
  there as `client_secret.json` at 0600 without being printed; no copy is
  left in Downloads.

## Phase 3: Sign-in and live check

- [x] T006 [US2] Install the reviewed release into `.local/gws/bin/`, sign
  in with the approved scopes, and run the live check (FR-002, FR-004,
  FR-008).
  - Install: the GNU asset's SHA-256 matched the release checksum; the
    extracted binary is byte-identical to the one reviewed; `gws --version`
    printed 0.22.5.
  - Sign-in, run by the coordinator from the worktree root (no `.env`, gws
    variables cleared, key backend `file`); the link was opened in the
    user's browser without passing through messages; the user approved.
    gws reported the user's cherry-pick.org account and exactly
    `drive.file`, `calendar.app.created`, `openid`, `userinfo.email` and
    `userinfo.profile`. `~/.config/gws/` is 0700 and every file in it is
    0600, the Discovery cache included.
  - Live actions, 2026-09-30 04:14 UTC: created the folder
    "verbose-broccoli" at the top of My Drive (kept); created the Doc
    "CHE-52 access check" inside it; appended one line; read it back (the
    text matched); deleted it; a lookup then returned 404 and the folder
    listed no files. Scope checks: a Drive list showed only that folder,
    and `calendarList.list` was refused with 403 (insufficient scopes).
  - Found: gws saved the delete call's empty reply as an empty
    `download.html` in the working directory; it was removed, and the local
    skill warns about it.

## Phase 4: Work plugin (US3)

- [x] T007 [US3] Copy the ten gws skills of plan.md R4 into
  `plugins/work/skills/` with an `upstream.json` each; edit `gws-shared`
  as recorded (FR-007).
- [x] T008 [US3] Write `plugins/work/skills/google-workspace/SKILL.md` from
  plan.md R5 (FR-007).
- [x] T009 [US3] Add the notice entry, the work plugin's description, the
  architecture paragraph and the generated reference refresh (FR-007).
  - T007 to T009: one Claude Code worker on `fable` at medium (backfire:
    0.60, confidence 0.54). The nine unchanged copies are byte-identical to
    the tag and all ten `skill_sha256` values match; `npm run verify`
    printed VERIFIED. The coordinator's diff review sent back one fix: create
    Docs, Sheets and Slides directly in the folder with Drive
    `files.create`, as the live check did. gws `--dry-run` validated the
    skill's RAW append and `files.update` commands, and `gws schema`
    prints each method's scopes as the skill says.
  - While verifying, `gts lint` also linted the git-ignored upstream clone
    under `.local/gws/`; the coordinator moved the clone out of the
    worktree instead of changing the lint ignores.

## Phase 5: Pin (US4)

- [x] T010 [US4] After CHE-44 merges into `develop`, merge `develop`, pin
  `"github:googleworkspace/cli" = "0.22.5"` in `mise.toml`, lock it,
  `mise trust` the reviewed file, `mise install --locked`, and check that
  the mise-installed `gws --version` prints 0.22.5 and that the lock's
  checksum matches T006's (FR-006).
  - Handoff, 2026-09-30 (computer restart): T001 to T009 are done and
    committed, and develop `845255f` (CHE-46) is merged in (`ba7a6ad`); no
    worker is running. Blocked on CHE-44 reaching `develop`. Next: merge
    `develop`, then start T010 with the task text saved in the git-ignored
    `.local/che-52-handoff/impl3.txt` (Claude Code, `fable`, medium, as
    chosen for T007 to T009), then T011. The reviewed binary is in
    `.local/gws/bin/`.
  - Done, 2026-09-30: pinned gws in `mise.toml`, locked its seven platforms
    with `mise lock` (each with GitHub attestation provenance; linux-x64 is
    `sha256:de78ecdb…8c5c1f`, T006's checksum), and added it to `orca.yaml`'s
    install line and `docs/architecture.md`. After `mise trust` and
    `mise install --locked`, the mise-installed `gws --version` prints
    `gws 0.22.5` and `cmp` finds the binary identical to `.local/gws/bin/gws`.
    `.github/workflows/check.yml` still installs only the other four tools;
    that stays, because no check runs gws. The coordinator compared all
    seven locked checksums with the release's `.sha256` assets: all match.

## Phase 6: Finish

- [ ] T011 Run `npm run verify` on the merged result; the develop merge
  review by a fresh Codex reviewer; the review-record commit; git flow
  feature finish; CHE-52 to Done.
  - Size, against `develop` `0e8e177`: 1,841 lines added and 14 deleted.
    Of the added lines, 987 are these records and the security reports, 614
    are the unchanged skill copies with their `upstream.json` files, 47 are
    `mise.lock`, and 193 are authored text (the local skill, the notice, the
    docs and the pin). Not split: the size is records and upstream copies.
  - Document judgment step: `npm run doc-regions:prepare -- --base develop
    --max-evidence-chars 40000` at `develop` `0e8e177` produced 240 units in
    eleven `jev_verify` requests and one `jev_classify` request, sent through
    backfire (OpenRouter, `typesafe/jev-1.13`, 12 calls). The two units this
    feature added, the "Google Workspace through gws" heading and paragraph
    in `docs/architecture.md`, were verified (0.85 and 0.93); the mise
    paragraph with gws was verified (0.70). The 53 other units flagged for
    review are sections this feature does not change, where the diff says
    nothing. One unit was judged contradicted at confidence 0.21:
    `AGENTS.md:32`, reuse step 3 ("an unstable upstream implementation with
    the smallest necessary patch"). It stands: the only patch is the recorded
    two-edit change to the copied `gws-shared`, and `AGENTS.md` findings are
    reported to the user, not changed. Both added units were classified as
    possible mechanical regions with confidence under 0.1; they stay agent
    text, because no file they could be generated from exists.
  - `npm run doc-regions:audit` (MemoryLint 1.5.1): 19 boundary warnings,
    all suggesting that constitution passages move to `AGENTS.md`. They
    exist on `develop` already, and this feature changes neither file; they
    are reported to the user only.
  - Develop merge review of `39ba4f0` by a fresh Codex reviewer on
    `gpt-6-luna` at medium (backfire: 0.93, confidence 0.92), given only the
    scope and the requirements: request changes, 0 blocker, 2 major,
    1 minor. Major: the release report's "do not install" verdict read as
    final beside the user's option A; the runtime report's controls 2 and 3
    differed from the approved controls without an explicit record. Minor:
    `drive.file` was described as reaching only files gws created, while
    Google's documentation also includes files opened through a file
    picker. Resolved: both reports got a disposition line, the release
    report's Decision section lists the accepted advisories and how each
    other control is carried out, the spec records the deviations, and the
    spec, plan and local skill (a Claude Code `fable` worker at medium)
    describe `drive.file` as files authorized to the app, which without a
    picker means the files gws created. The fixes change records and
    wording, not the implementation, so the coordinator reviewed them
    instead of a second review round.
  - Develop moved to `ff5ff91` (CHE-47) before the finish. Its merge
    (`c134e76`) combined both features' mise pins: gws beside CHE-47's
    betterleaks 1.9.0 and SpecStory 2.15.1 in `mise.toml`, `mise.lock` and
    `orca.yaml`, and the architecture's mise paragraph now names all seven
    tools. `mise install --locked` of the seven tools and `npm run doctor`
    passed, and `npm run verify` printed VERIFIED. The document judgment
    step rerun at `ff5ff91` (240 units, 12 calls) verified both added units
    (0.79 and 0.89) and the mise paragraph (0.63), and judged no unit
    contradicted. A fresh review of the new tip follows.

## Dependencies

- T001 before T006. T002 before T004. T004 before T005; T005 before T006.
- T007 to T009 need only T001 and plan.md.
- T010 needs CHE-44 on `develop`.
- T011 last.
