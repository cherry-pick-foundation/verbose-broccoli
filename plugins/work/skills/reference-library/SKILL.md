---
name: reference-library
description: >
  Follow the shared Zotero reference library's admission, item, topic-home,
  tag, triage and safety rules before adding or changing outside sources.
  Use for reference-library writes or read-only organization proposals.
---

Read [the work area rules](../../AGENTS.md) before using this skill.

# Reference library

These are the user's library decisions of 2026-10-08, maintained in the
repository and reviewed like code. [Sources and rule provenance](references/sources.md) distinguish
those decisions from the supporting guidance. Reading this skill does not authorize
changes to Zotero, its settings or its server. Changing the library or its settings
and scheduling the triage session are separate tasks.

## Admission and items

Keep one item for each outside source agents cite or reuse: papers, books,
standards, official guides, laws and web documents. Exclude student data,
personal data and private files, including in attachments and notes.
This is the user's admission boundary decided on 2026-10-08.

Before adding an item, search the library using its Digital Object Identifier
(DOI), International Standard Book Number (ISBN) or URL. Trust a matching DOI
for source identity; a similar title alone does not establish a duplicate.
This follows the user's decision and [zotkit's duplicate guidance](references/sources.md#zotkit).

Use Zotero's item type to describe the source form. Do not add tags that repeat
that type. This follows the user's decision and [zotkit's redundancy guidance](references/sources.md#zotkit).
Give each item a readable Citation Key using `creator-short-title-year`, with
hyphen-separated words: `niso-z3919-2005` and `zotero-local-api-2026` illustrate
the pattern. The pattern is the user's decision; readable names are supported by
[Anthropic's tool guidance](references/sources.md#anthropic).

When a source could change or disappear, attach a stored PDF or page copy,
rather than a linked file. [Zotero's file documentation](references/sources.md#zotero-files)
explains stored copies and page snapshots. Keep agent summaries in child notes
under the source item; the first line must name the agent and date, for example
`Agent: Codex; Date: 2026-10-08`. Child notes come from
[Zotero's notes documentation](references/sources.md#zotero-notes); the attribution
line is the user's decision.

Keep Zotero's automatic tags off. [Zotero's collections and tags documentation](references/sources.md#zotero-collections)
describes the setting. Changing library settings is a separate task.

## Collections and topic homes

Use one shallow collection axis: topic. Each triaged item has exactly one home.
New items wait without a home in Zotero's built-in Unfiled Items view until triage;
do not create an inbox collection. Projects and workflow state belong in tags.
The single-home policy comes from the user's decision and
[zotkit's organization guidance](references/sources.md#zotkit).
[Zotero's collections documentation](references/sources.md#zotero-collections)
explains Unfiled Items; Zotero itself allows multiple collection memberships.

Choose the home by the source's primary contribution, rather than its format,
method, publisher or the project using it, following
[zotkit's tie-breaker](references/sources.md#zotkit). A standard about networks
belongs with network operations; being a standard does not make it a knowledge
management source. A study of teaching with AI belongs with education when its
contribution is a teaching result; a new agent technique belongs with agent tooling.
If the primary contribution remains unclear, keep the item unfiled pending the
triage session's questions. Do not invent a sixth home or file it in two homes.

The user selected these five home names on 2026-10-08. Their boundaries apply
the primary-contribution rule; they do not create Zotero collections.

| Home | Belongs here | Does not belong here |
| --- | --- | --- |
| Education research and teaching | Sources primarily about learning, pedagogy, curriculum, assessment or teaching materials. | Agent design, general software, infrastructure or knowledge organization whose primary contribution is technical, even when used in teaching. |
| Agent tooling and AI | Sources primarily about artificial intelligence (AI), models, agent behavior, prompting, evaluation or tools and protocols specifically for agents. | Teaching outcomes using AI; general software development; deployment or network operations; reference organization using agents. |
| Software and repository tools | Sources primarily about general programming, libraries, testing, build tools, version control or repository workflows. | Agent-specific methods and tooling; running servers or networks; knowledge organization; pedagogy. |
| Server and network operations | Sources primarily about deploying, administering, securing or maintaining running servers, services, networks and their protocols. | Developing general software; agent techniques; teaching; metadata or knowledge organization. |
| Knowledge management and standards | Sources primarily about organizing, preserving, retrieving or citing knowledge, including metadata, vocabularies, reference libraries and standards for those activities. | Standards whose subject is education, AI, software or network operations; those follow their subject home. Other homes' technical or teaching contributions do not belong here. |

## Tags and triage

Use lowercase English tag values, with hyphens between words and a namespace
prefix. The user's vocabulary is:

| Namespace | Permitted values | Admission rule |
| --- | --- | --- |
| `status:` | `to-triage`, `triaged`, `summarized`, `needs-review` | Closed; use only these values. |
| `source:` | `official`, `standard`, `research`, `community`, `vendor` | Closed; required on every source item. |
| `topic:` | Terms admitted during triage | Open; new terms enter only through triage. |
| `project:` | Terms admitted during triage | Open; new terms enter only through triage. |

The namespaces and values are user decisions. Namespaced tags and complete
coverage of a required axis follow [zotkit](references/sources.md#zotkit).
Use one preferred term for each concept and keep candidate terms and dated
change history, following [NISO Z39.19](references/sources.md#niso). Include the
author in that history as the user decided.

Any agent may add a permitted source with `status:to-triage` and a `source:`
tag, leaving it in Unfiled Items. One scheduled agent triage session files
items into their single homes and applies tags from the vocabulary. Log every
new term as a candidate with its date and author during triage. Batch unclear
home or term choices into a few questions for the user instead of guessing.
The writing roles and schedule are the user's decisions;
[zotkit](references/sources.md#zotkit) supports batching ambiguous questions,
and [NISO Z39.19](references/sources.md#niso) supports candidate-term records.
Scheduling that session is a separate task.

## Analysis and safe writes

Keep analysis read-only: propose changes without applying them. Apply changes
serially, one batch at a time, with no more than 50 items per batch and a backup
before changes. This follows the user's decision and
[zotkit's workflow](references/sources.md#zotkit).

Before a bulk change, back up, perform a dry run, apply to one or two items and
check the result, then apply the remaining items in bounded batches.
This follows the user's decision and
[zotero-agent's safety rules](references/sources.md#zotero-agent).

Keep delete tools blocked. When removal is authorized, move items to trash,
never permanently erase them or empty trash. These are the user's decisions
of 2026-10-08. [Zotero](references/sources.md#zotero-collections) documents a
default trash retention period of 30 days, which settings can change. Trash is
not a replacement for a backup.
[zotero-agent](references/sources.md#zotero-agent) also recommends trash over erasure.

[Zotero's local API documentation](references/sources.md#zotero-local-api) is
an interface reference, not evidence that this installation supports writes.
This skill introduces no API commands, integrations or enforcement tools.
