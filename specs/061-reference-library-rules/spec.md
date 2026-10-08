# Reference library rules

Issues: WHA-3 (decisions and review), WHA-4 (implementation).

Deliver an agent skill for the shared Zotero reference library. Preserve the
user's decided structure: one outside-source item, no private or personal data,
Zotero item types without redundant tags, readable Citation Keys, stored copies
for unstable sources, attributed child summaries, identifier search before adding,
DOI identity and automatic tags off.

Use shallow topic collections with one home per triaged item, Unfiled Items for
new items and no inbox. The five homes are Education research and teaching;
Agent tooling and AI; Software and repository tools; Server and network operations;
Knowledge management and standards. Each needs a belongs / does not belong rule.
Projects and workflow state use tags. Status and source vocabularies are closed;
source is required. Topic and project terms enter through triage. Any agent may
add to-triage items; one scheduled triage session files and tags them, records new
candidate terms with date and author, and groups unclear decisions for the user.

Analysis stays read-only. Writes are serial, backed up and limited to 50 items
per batch. Bulk changes use backup, dry run and a checked one-or-two-item pilot.
Delete tools stay blocked; removals use trash with 30-day retention. Rules live
in the repository and receive code-style review.

Acceptance: all decided points appear without reopening or extending policy;
each borrowed rule names its listed source in original prose; five disjoint
home boundaries are written; no student data, personal data or secrets appear;
the agent link and skill validation pass; npm run verify passes. The CEO gives
independent Claude Code review after Codex implementation. Main's privacy-scan
comment on WHA-3 gates any GitHub push or pull request.

Out of scope: Zotero changes, settings, server changes, collections creation,
triage scheduling, new tools or dependencies. Public source citations do not
adopt upstream instructions or code.
