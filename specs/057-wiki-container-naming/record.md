# CHE-90 feature record

Assumption: existing XDG roots and instance selectors remain the supported
interface; only the container and current Wiki vocabulary change.

The repository now selects `verbose-broccoli/llm-wiki/<name>` in
`plugins/work/skills/wiki-raw-import/scripts/raw_import.py:375` and
`packages/wiki-consistency/src/wiki_consistency/instance.py:37`.
The consistency command calls the shared resolver at `__main__.py:77`;
grammatical competence calls it at `grammatical_competence.py:575`.
The raw-stage guard at `session_select.py:59` follows the new name too.
No new dependency, registry, fallback or runtime abstraction was added.
Current Wiki rules, skills, examples and architecture use wiki for an instance.
Historical specs, upstream vocabulary, external password-vault references and
historical constitution Governance are preserved. The current constitution
amendment uses commitizen's normal fix/PATCH step, from 2.7.0 to 2.7.1.
A follow-up fix/PATCH correction to current capitalized wording advances it
once more to 2.7.2, as required for a second amending commit.

Synthetic acceptance runs without the old container link for default, chat,
code and work. Instance tests also cover absolute, unset, empty and relative
XDG values. Existing invalid/custom-name checks remain. Command-line tests
exercise actual initialization, admission, verification and repeated init,
read back copied payloads and preserve synthetic source bytes and timestamps;
consistency check preserves the complete instance tree. Stage refusal happens
before creating a folder. These tests concern synthetic fixtures only.

Old builders failed 17 focused instance cases, four consistency command cases,
four staging cases and all four new import command cases. After the change,
123 focused Python tests passed; the broader affected run passed 646 tests,
and the raw-import suite passed all 49 tests. The first direct Python run
failed on external tool execution; rerunning through pinned `mise exec`
passed, without changing application code. Ruff and document-region checks
passed. Full verification and independent review must have positive receipts
in the retained attempt directory before integration; this record alone is
not acceptance or permission to unlink.

Consumer inspection on 2026-10-05 read paths, public builder files, plugin
metadata and process working directories. Seven other checkouts still had
all three old literals: the primary checkout, develop, feature-evp-oewn-senses,
feature-exam-calendar, feature-finish-cleanup, feature-korean-web-wiki and
feature-weekly-tool-update. Agent processes were present in the primary,
develop, exam-calendar, finish-cleanup and Korean-Wiki checkouts. A process
in a checkout does not prove a live Wiki writer or loaded helper version.
Global Wiki skill links resolved to develop. Codex reported all three local
plugins installed but disabled; its Work source still contained the old
raw-import builder. Claude reported no installed plugins. The inspected
Codex/Claude plugin-cache and OMP skill roots contained no additional regular
builder copies; symlinked marketplace sources were inspected through their
resolved source paths. Refreshing consumers is outside this feature's scope.

Main must keep the temporary link until the integrated paths reach active
checkouts and any retained installed source. This inspection does not establish
that every future consumer is ready. No real Wiki command, data move, private
writer lease, raw admission/conversion, private page edit, publication, client
settings change or link removal was performed. Real data and Git history
preservation rests on making no writes there, not on an unperformed private
integrity audit.

Document preparation retained all 334 original units but judged only the 24
whose text differed from develop, in two bounded calls through the same gated
proxy. Sixteen were verified and eight unsupported; 18 required review and
none were contradicted. Naming changes stand on the approved direction and
three exact source edits. Broader unchanged content in those paragraphs is
not newly established by the rename diff. Report-only root/plugin rules and
constitution findings were not used to alter policy. MemoryLint's 21 findings
recommend moving existing constitution sections/header details into AGENTS.md;
that is outside the rename and the constitution intentionally owns them.
Classification of the path paragraph was agent-region/review (.59 top
probability, .19 confidence): keep this short authored paragraph; adding a
path generator is unnecessary here. A spelling cleanup and amendment-date
correction did not change any behavior asserted by these retained calls.

Authoritative logs, exact command outputs, consumer snapshot and immutable
paid results are under
`~/.local/state/verbose-broccoli/workspaces/feature-wiki-container-naming/che-90/ctx_0944eec65615/`.
Root's setup and original choices are retained under develop's
`wiki-container-naming/attempt-20261005t090023z/`. Native reviewer selection is
Claude Code claude-sonnet-5-5/medium, chosen by fresh Jev (.68 probability,
.59 confidence, no escape/contradiction). Only positive native start and final
review receipts establish the reviewer and outcome. Root owns the finish,
post-merge verification and task ticks; main owns the link decision.

The first independent Claude built-in review inspected 633d5c5. Its two
current-spelling findings were fixed, including remaining test helper names.
The instance regression now also creates a legacy folder and still selects the
new folder. The decision date and amendment date intentionally differ. Three
container literals remain the minimal implementation; no shared abstraction is
needed. State-list guidance is now explicit: old lists are passed unchanged via
`--selection`, with no automatic lookup or state lock. Metadata-only inspection
found empty legacy selections directories for code and work, none for default
or chat, and no new state selections directories. No list names or contents were
read or moved. The corrected frozen snapshot requires renewed final review.
