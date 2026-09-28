# Research: Wiki Vaults

## R1. Which document units change (backfire, before editing)

**Decision**: Change the 17 units that backfire classified as naming the
storage folder, the policy units the brief names (constitution VI, IX and
Governance, `AGENTS.md` Records, `docs/architecture.md`, the skill and its
schema template), and nothing else. The 16 units classified as assuming a
single instance are all in feature 009's records and stay as its history
(spec Clarifications).

**Method**: Every tracked Markdown file (177) was split into block units with
feature 008's splitter (`doc_regions.units.split`; two feature 008 records
that quote region markers were split without masking). Units matching a broad
filter (`wiki`, `vault`, `instance`, `raw/`, `DATA/`, `STATE/`, `local/share`,
`local/state`, `XDG`, `data root`, `storage`) became 327 candidates. Each was
sent to `backfire_classify` with four classes: `storage_folder` (names or
describes where instances are stored; takes precedence), `single_instance`
(assumes one instance without naming the folder), `concept` (Wiki or its
layers) and `unrelated`. Requests ran through the code build's development
profile from `packages/backfire`, over MCP.

**Result**: 17 `storage_folder`, 16 `single_instance`, 175 `concept`, 119
`unrelated`; 51 of them were flagged for review rather than accepted
automatically.

- `storage_folder`: constitution 77-85; `docs/architecture.md` 143-154; the
  skill 15-18 and 61-63; feature 009's contract 24-25, data model 11-25,
  33-40, 76-79 and 106-109, quickstart 20-32, research 91-98, spec 17-21,
  196-200, 281-285 and 360-361, and tasks 166-170 and 203-211. All but spec
  360-361 contain `wikis`; that one says "the default instance folder" and
  stays, since it names no folder.
- `single_instance`: feature 009's contract 18-22, plan 10-12 and 36-38, spec
  28-30, 71-76, 143-145, 194, 202-206, 214-215, 265-266, 286, 352-353 and
  405-411, and tasks 173 and 177-178. They describe what feature 009 built.
- Review-flagged `concept` units outside feature 009 were read by hand:
  constitution 57-58 ("each instance under the application's data root")
  changes with VI; the rest (architecture 45-49, 132-139, 141, 485-488;
  features 006, 007 and 008) do not concern the storage folder.

**Cost**: 32 requests (the first batches of 64 items often failed with
`provider_error` or `malformed_output`, so they were resent in batches of 16
and then 4, with up to three attempts each), 41 provider judgments, 24 of
them successful. Input tokens 129,907; output tokens 151,206 (from the
server's session records).

**Alternatives considered**: `git grep wikis` alone finds the literal
mentions but not wording that assumes one instance; classifying all units of
all files without the filter would have sent about ten times as much text for
units that cannot concern the Wiki.

## R2. Checking the edited documents (backfire, after editing)

**Decision**: Run feature 008's judgment step, `deno task doc-regions:prepare
-- --base develop --max-evidence-chars 20000`, and send its `backfire_verify`
and `backfire_classify` requests; then send one more `backfire_verify` for the
changed units of documents outside its targets (the skill, the schema
template and feature 009's records) with the script diff and this spec's
decisions as evidence. Correct units judged contradicted or flagged, or
record why they stand.

**Rationale**: Feature 008's targets are `README.md`, `docs/architecture.md`
and `docs/backfire.md`, with `AGENTS.md` and the constitution report-only; the
brief asks for the judgment on every changed document.

**Result** (at commit `948011b`): no unit needed a correction.

- Prepare's requests covered 220 units, with the diffs of the script, the
  skill and its schema template as evidence. No unit was contradicted. Eight
  were flagged for review: constitution 58-59, 61-67, 91-93 and 154-156,
  `AGENTS.md` 70-74, and `docs/architecture.md` 10-25, 155-160 and 162-170.
  Six of them were judged supported and two unsupported. They stand, because
  their source is the user's decisions in this spec, and prepare excludes
  `specs/` from evidence. The three units the feature added to
  `docs/architecture.md` (the vault introduction, the vault table and the
  rules paragraph) were classified as agent regions; none becomes a
  mechanical region, because no repository file lists the vaults.
- The extra request covered the 18 changed units of the skill, the schema
  template and feature 009's records, with the script diff and this spec's
  Input and Clarifications as evidence. One unit was contradicted: feature
  009's contract line "`--wiki <name>` selects `vaults/<name>/` and defaults
  to `default`". It stands as feature 009's history, which keeps only the
  folder rename (spec Clarifications); this feature's
  [contract](contracts/raw-import-cli.md) states the new default. The five
  units flagged for review (skill 31-36 and 96-99, schema template 53-55,
  feature 009's data model 106-109 and spec 196-200, and tasks 166-170) were
  supported or say only what feature 009 built.
- `deno task doc-regions:audit` reported 19 MemoryLint warnings, all of the
  `boundary` kind on the constitution (list items it would move to
  `AGENTS.md`). They are reported to the user, not acted on.

**Cost**: 5 requests, 10 provider judgments (5 successful; the others were
retried). Input tokens 160,074; output tokens 45,141. The records went to a
separate state folder for this step, so the counts contain no other session's
calls.
Together with R1: 37 requests, 51 judgments, 289,981 input tokens.

## R3. Tests

**Decision**: Keep feature 009's black-box tests and change only their paths
from `wikis/` to `vaults/` and the default instance's name from `default` to
`work`. Add two cases: `init`, `admit` and `verify` without `--wiki` create
and use `DATA/vaults/work/` and `STATE/vaults/work/`, and create nothing named
`wikis`; a synthetic exported conversation admitted with `--wiki chat` becomes
one valid revision.

**Rationale**: FR-002 and FR-004 are the only behavior changes; the existing
cases already cover named vaults, locks, staging and XDG defaults.

## R4. Moving the live instance

**Decision**: After `git flow feature finish vaults`:

1. Record the instance's latest commit, commit count and `git status
   --porcelain` output, and the list of its state folder.
2. Check with `lsof +D` that no process holds files open under
   `DATA/wikis/` or `STATE/wikis/`, and that the user's session that writes
   student pages is idle; otherwise ask through the develop session.
3. Check that `DATA/vaults/` and `STATE/vaults/` do not exist or hold no
   `work` folder.
4. `mv DATA/wikis/default DATA/vaults/work` and
   `mv STATE/wikis/default STATE/vaults/work` on the same file system.
5. Compare the recorded values; run `verify` on `work`.
6. Run `init` for `default`, `chat` and `code`, and `verify` on each.
7. Remove the then empty `DATA/wikis/` and `STATE/wikis/` with `rmdir`.

**Rationale**: A rename keeps the Git repository, the index, the user's
uncommitted edits and the read-only raw revisions exactly as they are. The
instance's schema does not name `wikis/`, so nothing inside it changes.
`CACHE/raw-import/default/` holds only staging, which the next run cleans;
it is left alone.

**Alternatives considered**: Copying and deleting would rewrite every file's
metadata and risk a partial copy; migration code in the script would be
locally owned code for a one-time step (constitution VII).
