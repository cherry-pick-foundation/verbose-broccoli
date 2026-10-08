# Sources and rule provenance

The user decided the policy in WHA-3 and chose the five topic homes in WHA-4
on 2026-10-08. Exact tag values, admission exclusions, Citation Key pattern,
agent/date attribution, writing roles, triage scheduling and blocked delete tools
are local decisions, not requirements imposed by the sources below. The skill
paraphrases the relevant guidance and does not adopt upstream code or commands.
Public sources were consulted on 2026-10-08.

## Zotero collections

[Zotero: Collections and Tags](https://www.zotero.org/support/collections_and_tags),
sections The Zotero Collections Model, Unfiled Items, Trash and Automatic Tags.
Supports the distinction between collections and tags, the unfiled view,
automatic-tag setting and default 30-day trash retention. Zotero allows multiple
homes; the one-home restriction is this library's policy.

## Zotero notes

[Zotero: Notes](https://www.zotero.org/support/notes), Child Notes.
Supports attaching a summary note to its source item. Naming the agent and date
on its first line is this library's policy.

## Zotero files

[Zotero: Adding Files](https://www.zotero.org/support/attaching_files),
Stored Files and Linked Files; Adding Files via the Browser.
Supports managed stored copies and page snapshots rather than local-file links.
The library decides when a source requires a preserved copy.

## Zotero local API

[Zotero: Local API](https://www.zotero.org/support/dev/web_api/v3/local_api).
Describes the desktop interface and version-dependent write support. It does
not establish this installation's version, authorization or tool availability;
none was probed and no Zotero requests were made for this pilot.

## zotkit

[zotkit: Organizing a Zotero library with agents](https://github.com/oldantique/zotkit/blob/HEAD/docs/organizing-with-agents.md),
Design principles, The agent workflow, duplicate guidance and Division of labor.
Supports shallow homes, primary-contribution routing, namespaced tags, avoiding
item-type redundancy, DOI identity, read-only proposals, serial writes in batches
of at most 50 after backup, and grouping unclear choices for the owner.
The library adopts only its decided subset, not zotkit's additional namespaces,
audit operations, configuration or tools.

## zotero-agent

[zotero-agent: Instructions for agents](https://github.com/alex-roc/zotero-agent/blob/HEAD/AGENTS.md),
Safety rules and Batch edits.
Supports backup, dry-run preview, checking one or two items first and using trash
rather than permanent erasure. This citation does not load those instructions
or authorize setup, restarts, merges or installation.

## NISO

[NISO: ANSI/NISO Z39.19-2005 (R2010), Guidelines for the Construction, Format,
and Management of Monolingual Controlled Vocabularies](https://www.niso.org/publications/ansiniso-z3919-2005-r2010),
sections 5.3 (principles), 11.1.4 (term records), 11.1.6 (candidate terms)
and 11.3.2.2 (history of changes). The [standard text](https://www.anzsi.org/wp-content/uploads/2019/05/z39-19-2005r2010.pdf)
supports preferred terms, candidate records and dated change history. Recording
the author as well is the user's chosen traceability rule; the exact namespaces
and terms remain the user's decisions.

## Anthropic

[Anthropic: Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents),
Returning meaningful context from your tools.
Supports meaningful names over opaque identifiers. Applying that principle to
Citation Keys, and choosing their pattern, are local decisions rather than
an Anthropic citation-format specification.
