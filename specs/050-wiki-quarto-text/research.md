# Research: Persistent Text and Quarto Wiki

## Reuse already implemented capabilities

Decision: reuse source admission and BagIt authority from 009/012/030; retain
English/privacy rules from 014 and current schema. Those earlier records remain
history. No held branch is an implementation source.

Starting-base evidence (`5c489af38c5d42af8fb71a9649db32d97c39c864`): `instance.py:194-226` discovers only `wiki/**/*.md` and reads
per-page YAML; `sources.py:12-40` generates a Cog topic catalog; `lint.py:228-290`
checks the committed `wiki/log.md` prefix; `evidence.py:235-392` uses existing
MarkItDown/JSON/HWPX conversion paths and immutable cache writes. This supports
adaptation, not rebuilding raw storage or converters.

Alternatives: repeating converters or using Quarto listings would duplicate
implemented behavior or lose the readable Markdown/Docusaurus agent catalog.
Main's listings and per-page inspect measurements are reused as supplied;
no redundant benchmark is planned.

## Native metadata and citation syntax

Decision: folder defaults use `_metadata.yml`; Python checker merges metadata
without a Quarto process for every page. Quarto documents directory inheritance,
document-over-directory priority and object/array merging in its
[project guide](https://quarto.org/docs/projects/quarto-projects.html#metadata-merging),
read 2026-10-04. Its [citation guide](https://quarto.org/docs/authoring/citations.html#citation-syntax)
uses Pandoc keys and page locators. The checker supports the required locator
forms through reused parsing before narrow source-locator glue.

Alternative: `quarto inspect` per page repeats the supplied ~0.6-second per-page
cost. A general new document parser is outside scope; a substantial unsupported
capability stops dispatch and is reported with upstream options.

## Independent current-source wave

Repository trace: `task_d36372a606f1` / `ctx_9832c2de7df4`, Codex
`gpt-6.1-sol` high, Jev selected probability .77/confidence .71; first checkpoint
45 minutes (.45/.33). Vault read-only preservation inventory:
`task_caec57ab6079` / `ctx_17cfaf8b5c36`, Codex `gpt-6.1-sol` medium,
.80/.77; first checkpoint 30 minutes (.85/.83). These are estimates, not stopping
caps. Launch receipts confirm requested/effective model and effort agree.

Inputs/results/launch receipts are immutable in the planning state directory
named in tasks.md. Repository trace settled. The settled inventory report is retained at
`../ctx_17cfaf8b5c36/report.md` relative to the planning state root. It confirms
176 pages (work 134/code 36/chat 3/default 3), all 109 profile checker values
`none`, four side files `verification-needed`, and unchanged vault/raw/cache/Git
receipts. Code has 11 foreign staged edits, so its migration remains held pending
main's selected review. The inventory worker was released after accepted settlement. Worktree starts at the approved
base; setup later generated unrelated client config, retained for runtime and
cleaned only through its receipt-owned supported command before commits.


## Truthful metadata inputs and extension checks

Decision: keep the Cog page glob and add literal existing metadata paths only
when inherited values are consumed. Current `doc_regions.regions.shape` already
accepts multiple literal source arguments; `validate` calls `files` for each. A
metadata-consuming generator must reject an unnamed ancestor dependency.

The independent trace reports synthetic current Vale/lychee behavior skips qmd
inputs. Exact receipts and the smallest upstream-supported checking route remain
in that worker's report; suffix discovery alone cannot establish link acceptance.

## Settled foundation and sentence gap

Foundation report `ctx_be847b88577b/report-settled.md` is retained in the CHE-84
state root. All 13 source hashes match its snapshot after restart. Installed
Quarto 1.10.18 inspection and source show recursive map merging and ordered
unique array combination; empty/null array overrides preserve inherited entries.
This is a one-fixture probe, not per-page production inspection.

Main approved existing literal metadata inputs to Cog through develop
`msg_d65e95808fbb`, lifting the catalog interpretation condition. The page pattern
stays wiki/**/*.qmd. F2 consumes ordered ancestor dependencies and exact page
bytes for its own freshness fingerprint.

Native Pandoc Cite boundaries do not prove one sentence per segment. The scoped
read-only upstream review settled before conditional pySBD 0.3.4 adoption,
authorized in develop `msg_97f674fbf11f`; syntok was not adopted. Synthetic
coverage, protected-quote ambiguity and conservative unresolved behavior must
settle before claiming every sentence was attributed. No custom NLP parser is
planned.


## Current request-budget contract

Develop rechecked the current constructor, Jev schemas and prior bug records in
`msg_447d75c780a0`: 12,000 limits claim text only; no separately approved complete
body cap exists and the provider limit is unpublished. Keep existing claim,
evidence-item, decision-cell and caller evidence ceilings. Measure the complete
serialized tool arguments and UTF-8 bytes without inventing a cap, truncating or
dropping exact evidence. Provider HTTP templates/token expansion and live
acceptance remain unverified. No repeated paid probe was authorized.


## Retained acceptance and operational boundaries

Full frozen-source verification attempt 02 passed all 47 Turbo checks with no
source drift. Its exact evidence and current writer/reviewer owners are in
[tasks.md](tasks.md). The actual existing corpus has zero canonical inline source
citations; format migration preserves prior unchecked status and supplies no
sentence-evidence verdict. Four legacy conversions retain unknown review/tool
fields and original body line offsets, preserving all 4,671 mapping span uses.

The document evidence planner preserved all 358 original units and complete
original evidence. Its 215 entries still include 193 partial and 118 unscoped
units; the largest compound unit yields 246,579 argument characters/bytes.
Both earlier refusals remain immutable, and the plan is not submission authority.
Source agreement is not proof of historical user decisions or actual host/account
behavior; missing support remains explicit instead of receiving unrelated diff
material. No new serialization cap or generic batching system was introduced.


## Cross-artifact consistency at source commit freeze

Requirements FR-001 through FR-014 map to setup/amendment T001-T002, discovery
and consumers T003-T007, retained evidence T008-T009/T012, requests/search
T010-T013, roles T014, migration T015-T018 and integration T020-T024. T019 is
explicitly held and is not an implemented-batch claim. All four user stories
have positive, negative and boundary synthetic evidence; actual Wiki sentence
judgments remain unchecked. Main owns audience/publication selection; F2 owns
its delivery implementation. The contract was corrected to express that same
ownership boundary. No constitution conflict or missing task dependency remains
in this record review; operational failures and final review/integration stay
explicitly pending instead of becoming task ticks.
