# F1 Contract: Text, Metadata and Citations

Status: base data contract and scoped implementation settled; final acceptance
pending. F1 owns this contract; F2 consumes it through develop. Current source
and synthetic verification evidence are recorded in tasks.md.

## Retained text

`text/<source-id>/<revision>.qmd` contains the full extraction in its original
language. It starts with this synthetic front matter:

```yaml
---
source-id: 0199a0e2-7c1b-7d3e-9f00-000000000000
revision: 20260928T010203000000Z
sha256: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
converter:
  name: markitdown
  version: recorded-version
checked-against-original: false
conversion-status: extracted
---
```

Values come from the bag and actual conversion/review receipt. Unknown legacy
converter/version or review evidence uses `null` and a reported missing-evidence
finding. It must not pass as reviewed or as complete conversion provenance.
Existing side-file text is copied without rewriting its body. A correction stays
in Git and a new raw revision gets another file; default conversion cannot
replace an existing retained extraction. `extracted` records returned backend
output, not completeness or original review; partial/unknown results remain
explicit. A true review header needs an actual caller receipt with raw `sha256`,
current complete-file `extraction-sha256` and an evidence reference. Any byte
correction invalidates an earlier receipt; conversion cannot manufacture review.

Page markers such as `## Page 25 {#p-25}` or fenced div `{#p-25}` delimit actual
original pages, not estimated chunks. Section markers such as `{#sec-purpose}`
identify a source section. Locators are stable after review; absent original
page-boundary evidence is reported, not inferred from character counts.

## Metadata

Ordinary `wiki/**/*.qmd` pages retain title, summary, topics and source revision
entries. `wiki/index.qmd`, `wiki/overview.qmd`, `wiki/log.qmd` keep their current
special roles. The catalog stays Cog with page input `wiki/**/*.qmd`. When inherited
metadata affects the catalog, name each existing `_metadata.yml` as another
literal source argument to the same generator; no absent glob or implicit
unnamed metadata input is allowed. Reuse current `doc_regions.shape/files`
validation and reject an omitted ancestor default before reading its contents.

Read `_metadata.yml` from the Wiki root to the containing folder, then page front
matter, in-process. Follow Quarto precedence: document over directory over
ancestor defaults; mappings merge recursively and sequence merging follows the
verified Quarto rule: maps recurse; arrays merge unique entries in order,
including scalar/list pairs; empty/null array overrides retain inheritance.
Preserve meaningful page values, including explicit
unchecked profile status. Consolidate only values proved equivalent by readback;
shared profile inventory paths remain relative to the consuming page. Do not
run `quarto inspect` per page or inject defaults into body prose.

Public interfaces are `instance.read_metadata(instance, document,
named_defaults=None)` for the full mapping/problems and
`instance.metadata_sources(instance, document)` for safe ordered ancestor names
without content reads. F2 rediscovers the list each run and fingerprints exact
page bytes plus ordered dependency names/bytes in its own freshness code.

## Citations and judgments

Every supported knowledge sentence cites its evidence, for example
`The synthetic result is supported [@source/r1, p. 25].` Citation keys are
generated from bags only as `<source-id>/<revision>`. Page source entries retain
only their exact `id` and `revision`, with no optional alias. A citation of a
revision not declared by the consuming page fails; no newest-revision fallback.

Supported locators must cover single pages (`p. 25`), contiguous page ranges
(`pp. 25-26`) and explicit source sections (`sec. purpose`, resolving
`sec-purpose`). Multi-source brackets separate citations with semicolons.
Unrecognized syntax reports an unresolved locator rather than ignoring it.
Native `quarto pandoc` parses citations; reviewed pinned pySBD 0.3.4 supplies
candidate English spans. Exact native literal alignment is restricted to
supported plain paragraphs/list prose because this native reader cannot combine
citations with source positions. Bounds, complete non-whitespace coverage,
original slicing, repeated occurrences and citation ownership must be proved.
Unsupported formatting/tables/callouts/blockquotes, protected or ambiguous prose,
malformed mappings and uncovered text are explicit unresolved failures. No
unconditional linguistic completeness claim or general parser fallback is made.

Resolve only the cited source/revision/hash and markers. A page span ends at the
next page marker; a section span ends at the next section at its level or above.
A range needs every interior page. Duplicate/missing markers, ambiguous source keys,
wrong hash/revision, absent text or unknown provenance fail clearly. Evidence
contains only the located body spans, with exact source/revision/locator IDs.
No whole-source, latest-revision or lexical-search fallback can broaden it.
Existing body text without usable locators stays preserved and is reported
unverifiable; migration does not manufacture semantic review or rerun proposals.
Overview evidence remains its linked English pages; log/catalog remain excluded
from paid judgments. Cross-page candidates use existing search without expanding
the citation evidence. Requests remain deterministic and within the existing claim/item/decision and
caller evidence limits. No separate whole-body cap is defined; 12,000 applies
to claim text only. Acceptance measures full serialized tool-argument characters
and UTF-8 bytes, including JSON/evidence, without inventing a new cap or proving
provider HTTP/token expansion or live provider acceptance.

## Derived bibliography and F2 boundary

At each consuming run, derive citation data from BagIt records into a private
XDG cache attempt, never persist a bibliography in text/Wiki/site Git. The only
source registry is raw. Entries expose an exact key, source ID, revision, hash
and bag-derived title/metadata; no author/date is invented. Cache output is
rebuildable and stale previous output is never treated as current evidence.
`evidence.bibliography(instance, revisions, *, budget_bytes, env=None)` yields a
fresh private cache `sources.json` Path inside a context, removed on successful,
failed or catchably interrupted exit. CSL entries contain id, type=document,
title=BagIt payload filename and `custom` source/revision/hash/raw provenance.
Do not use the expired Path outside the context or publish unselected private
labels by inference.

F2 passes this run's cache bibliography path to its rendering path and retains
chosen English version provenance for Korean `site/` pages with tags. F2 owns
translation freshness, publish workflow and renderer integration. Main owns
audience, student-bearing and publication selection; these choices cannot make
raw/text/Wiki a published source by inference.
No `ko/` tree. No executable cells, heavy includes/shortcodes or replacement of
Cog with Quarto listings. Shared checker/schema edits require develop ownership.
