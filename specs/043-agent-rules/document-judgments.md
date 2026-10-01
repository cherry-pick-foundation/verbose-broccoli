# Document judgment dispositions

Assumption: evidence can be silent about an unchanged claim. Jev results are
advice, not final approval or client/runtime acceptance.

## Current integrated snapshot

Latest develop `c0b630b` is integrated. Four successful OpenRouter
`typesafe/jev-1.13` calls judged 331 prepared units: 45 verified, 285 unsupported,
one contradicted and 142 review actions. Three extra consumer claims were
verified automatically. All flagged units have dispositions below; unsupported
does not mean false.

All shared evidence content changed after the review fixes, so no old results
qualified for byte-identical reuse. The coordinator authorized full rejudgment
with existing development credit and batches of at most 110 claims. These
requests held 110, 110, 110 and four claims. The evidence keeps every non-pointer
diff and compresses only the 48 identical insertions, checked against original
and current bytes and hashes. No provider fallback or unchanged retry occurred.

The previous pointer snapshot had 31 verified, 300 unsupported, zero
contradicted and 135 review actions. It is superseded. Its first 224-claim
attempt was refused with `max_tokens_exceeded`, stopped and reported; process
exit 0 was excluded. Feature totals are 25 successful Jev calls, including eight
reviewer-choice calls, plus one refused attempt. Supplied domain choices are
separate.

## Snapshot hashes

SHA-256 uses sorted-key JSON with unescaped Unicode for unit/evidence arrays;
the compact evidence hash uses its exact UTF-8 bytes.

- base: `c0b630b1f9e4d41f95154a0b7e3285e67faf598e`
- units_sha256: `31df2ca27e23db0aa8d2fb49b93fb4451554457963177e962e09eb5aabc38712`
- full_evidence_sha256: `1d9c496fa33086e592852b5cbb773ce6705912138ff38827e7e033174287faa7`
- compact_evidence_sha256: `ec1f55886434d408a9defdb826c103996c3febd2b7e9a777e31b28424278ad3c`
- compact evidence: 42789 characters; no reused results.

## Review dispositions

| Unit | Verdict | Confidence | Disposition |
| --- | --- | ---: | --- |
| `.specify/memory/constitution.md:1-16` | verified | 0.40 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:18-18` | unsupported | 0.38 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:20-20` | unsupported | 0.75 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:22-22` | unsupported | 0.63 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:24-26` | unsupported | 0.69 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:28-28` | unsupported | 0.79 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:34-34` | unsupported | 0.70 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:38-38` | verified | 0.42 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:40-43` | unsupported | 0.30 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:56-56` | unsupported | 0.68 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:69-74` | unsupported | 0.67 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:75-79` | unsupported | 0.52 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:96-96` | unsupported | 0.40 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:114-119` | unsupported | 0.54 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:121-121` | verified | 0.33 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:123-146` | verified | 0.43 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:148-150` | unsupported | 0.76 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:152-152` | unsupported | 0.78 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:154-155` | unsupported | 0.75 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:156-158` | unsupported | 0.58 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:159-161` | unsupported | 0.75 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:162-162` | verified | 0.24 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:167-170` | contradicted | 0.58 | Report stale main ownership to develop. Constitution is outside writable scope; retain under current governing precedence. |
| `.specify/memory/constitution.md:171-174` | verified | 0.57 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:175-205` | unsupported | 0.64 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:206-207` | unsupported | 0.74 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:211-211` | unsupported | 0.56 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:213-276` | unsupported | 0.57 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `.specify/memory/constitution.md:278-278` | unsupported | 0.59 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:1-1` | unsupported | 0.35 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:3-8` | unsupported | 0.52 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:14-14` | unsupported | 0.71 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:16-18` | unsupported | 0.49 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:19-21` | unsupported | 0.78 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:24-25` | unsupported | 0.75 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:27-29` | unsupported | 0.63 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:30-30` | verified | 0.34 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:32-32` | verified | 0.44 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:34-34` | unsupported | 0.37 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:35-35` | verified | 0.56 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:36-36` | unsupported | 0.51 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:37-38` | unsupported | 0.31 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:39-39` | verified | 0.43 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:41-41` | unsupported | 0.32 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:43-43` | unsupported | 0.72 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:47-47` | verified | 0.45 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:49-49` | unsupported | 0.77 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:51-51` | unsupported | 0.40 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:53-55` | unsupported | 0.41 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:57-61` | unsupported | 0.39 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:88-88` | unsupported | 0.58 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:94-97` | unsupported | 0.51 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:105-105` | verified | 0.32 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:107-108` | verified | 0.30 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:109-110` | verified | 0.51 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:115-115` | verified | 0.79 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:136-136` | unsupported | 0.78 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:143-146` | unsupported | 0.77 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:147-148` | unsupported | 0.66 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:149-150` | unsupported | 0.67 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:153-155` | verified | 0.74 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:156-158` | unsupported | 0.36 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:168-170` | unsupported | 0.76 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:171-172` | unsupported | 0.69 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:173-173` | unsupported | 0.68 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:174-174` | unsupported | 0.51 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `AGENTS.md:175-176` | unsupported | 0.63 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `README.md:1-1` | unsupported | 0.39 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `README.md:3-6` | unsupported | 0.38 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `README.md:8-10` | unsupported | 0.29 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `README.md:12-14` | unsupported | 0.45 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:1-1` | verified | 0.37 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:3-6` | unsupported | 0.21 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:8-8` | unsupported | 0.67 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:10-34` | unsupported | 0.63 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:103-123` | unsupported | 0.46 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:125-133` | verified | 0.56 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:206-206` | unsupported | 0.55 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:208-214` | unsupported | 0.69 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:216-224` | unsupported | 0.43 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:264-270` | unsupported | 0.72 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:272-275` | unsupported | 0.33 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:335-341` | unsupported | 0.33 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:347-350` | unsupported | 0.64 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:382-382` | verified | 0.26 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:384-393` | unsupported | 0.33 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:397-399` | unsupported | 0.63 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:441-441` | unsupported | 0.54 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:443-444` | unsupported | 0.78 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:488-488` | unsupported | 0.69 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:490-498` | unsupported | 0.77 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:532-532` | verified | 0.69 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:534-538` | verified | 0.39 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:548-549` | unsupported | 0.53 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:559-563` | verified | 0.56 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:565-569` | unsupported | 0.65 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:571-571` | verified | 0.26 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:573-576` | verified | 0.39 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:580-584` | verified | 0.62 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:621-634` | verified | 0.23 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:655-659` | unsupported | 0.59 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:701-701` | unsupported | 0.47 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:703-708` | unsupported | 0.55 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:714-718` | unsupported | 0.31 | Retain: root Records, Linear preset and workflow implement the approved develop/feature ownership split. |
| `docs/architecture.md:719-724` | verified | 0.53 | Retain: root Records, Linear preset and workflow implement the approved develop/feature ownership split. |
| `docs/architecture.md:739-743` | verified | 0.72 | Retain: root Records, Linear preset and workflow implement the approved develop/feature ownership split. |
| `docs/architecture.md:744-744` | unsupported | 0.21 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:746-749` | unsupported | 0.54 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:751-756` | unsupported | 0.68 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:757-758` | verified | 0.73 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:769-774` | unsupported | 0.57 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/architecture.md:775-786` | unsupported | 0.23 | Retain: configured doc-regions targets/report_only, prepare/audit commands and loader match this process; runtime client behavior is not claimed. |
| `docs/architecture.md:787-791` | unsupported | 0.76 | Retain: configured doc-regions targets/report_only, prepare/audit commands and loader match this process; runtime client behavior is not claimed. |
| `docs/architecture.md:792-795` | unsupported | 0.70 | Retain: configured doc-regions targets/report_only, prepare/audit commands and loader match this process; runtime client behavior is not claimed. |
| `docs/architecture.md:796-798` | unsupported | 0.28 | Retain: configured doc-regions targets/report_only, prepare/audit commands and loader match this process; runtime client behavior is not claimed. |
| `docs/backfire.md:1-1` | unsupported | 0.77 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:3-12` | unsupported | 0.75 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:14-21` | unsupported | 0.76 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:25-26` | unsupported | 0.56 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:28-30` | unsupported | 0.58 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:117-120` | unsupported | 0.44 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:165-165` | unsupported | 0.60 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:206-206` | unsupported | 0.66 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:248-248` | unsupported | 0.67 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:324-325` | unsupported | 0.71 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/backfire.md:339-342` | unsupported | 0.78 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/reference/commands.md:1-1` | unsupported | 0.44 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/reference/commands.md:3-3` | unsupported | 0.70 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/reference/plugins.md:1-1` | unsupported | 0.27 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `docs/reference/plugins.md:3-3` | unsupported | 0.50 | Unchanged unit retained; the feature diff does not contradict it. Unsupported is not evidence of falsity. |
| `plugins/chat/AGENTS.md:1-1` | unsupported | 0.53 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/code/AGENTS.md:1-1` | unsupported | 0.27 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/code/AGENTS.md:3-3` | verified | 0.54 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/code/AGENTS.md:14-15` | verified | 0.65 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/code/AGENTS.md:17-17` | unsupported | 0.53 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/code/AGENTS.md:19-22` | unsupported | 0.58 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/work/AGENTS.md:1-1` | unsupported | 0.36 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/work/AGENTS.md:13-13` | unsupported | 0.79 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/work/AGENTS.md:15-20` | unsupported | 0.73 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/work/AGENTS.md:22-26` | unsupported | 0.68 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/work/AGENTS.md:84-89` | unsupported | 0.78 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |
| `plugins/work/AGENTS.md:99-99` | unsupported | 0.77 | Report-only rule. Retain current governing source and approved migration decisions; no automatic rewrite. |

## Additional consumer claims

| Claim | Verdict | Confidence | Disposition |
| --- | --- | ---: | --- |
| The Ponytail instruction loader resolves the code plugin rules pointer to the installed package absolute path before injecting skill text. | verified | 1.00 | Retain; source patch and focused consumer checks agree. |
| Upstream provenance records describe the plugin rules pointer as a local patch while preserving original upstream revisions and hashes. | verified | 1.00 | Retain; source patch and focused consumer checks agree. |
| Workflow assigns feature record commits to the feature orchestrator and Linear changes to the develop orchestrator. | verified | 1.00 | Retain; source patch and focused consumer checks agree. |

## Pointer byte preservation

Every skill differs from latest develop only by its one plugin-rule pointer
and a blank line after the front matter. Original upstream hashes remain
provenance, not hashes of the patched local copies.

| Skill | Base SHA-256 | Current SHA-256 |
| --- | --- | --- |
| `plugins/chat/skills/credit-offers/SKILL.md` | `0c664b3fa11d2f1bdf5020707798fb5d5273844d408289643798f104846a72d5` | `1e5615c623e7d7e4dd9dea6f7abcec8cea5a81b1d84584124baa1fe2cfb0e126` |
| `plugins/chat/skills/web-agent/SKILL.md` | `a8fde3496c2be902b31ebb2f09256ecf0d9d5fbd2bd54368a26571a64bf4a6c8` | `d34414b77116397a1f0a76daa9aae117d8a90fd6f4b1946ca136caffd42654c8` |
| `plugins/code/skills/backfire/SKILL.md` | `b9623d3511b44b9e04f680e1c0855240de721d4f54211932a36d3f486614bff3` | `390c6d16de9880bd104f4e82e9c7d7d01abc461db4e594f5e46ba8ec9dcf30ff` |
| `plugins/code/skills/clean-code/SKILL.md` | `598411aaf75101a0abb620be3f15ffd519df6b7aa1ed2dcca0e724f97903e72f` | `f95116956acecf9fc4a5acd3c216407c093996c3979c15688d2a56502320aef0` |
| `plugins/code/skills/git-commit/SKILL.md` | `554d1a3c6d95f15bc1170160659ecdc9a9958b64f377f3988941b672c249b13f` | `b7a6328de2a3790a9446a3067ee68e46bab12acfa688b70c81295ae6c01f77d0` |
| `plugins/code/skills/model-choice/SKILL.md` | `c03f9eae0d01bf22c4b625b773a50ec83201abb907e0cbcd972189ebac39c716` | `334240709620228df7a0f5ae6e6aaff96cb986a897c8fad017a40872d7450184` |
| `plugins/code/skills/ponytail-audit/SKILL.md` | `5560b8e383dbe2ddfddc873a1e2bf2e586e23e0cd7d995537482b2315331f6d1` | `1a2a70558870b63e6f2c0b59f335785c0a2a7b9e6479a79d528be28a17090714` |
| `plugins/code/skills/ponytail-debt/SKILL.md` | `c84fba75f0ca12bfe83f9a78ea02fd125c5dd3f1fbb18124105a489937f284e6` | `8c491e03d8cf810e9fada645d195e37f51e6e69cb81513bfafe0d560c3167e63` |
| `plugins/code/skills/ponytail-review/SKILL.md` | `40df33b58fc6ef889b93585733feb9566b76e9586efa7f376785c1e995197ac0` | `6b62c0995dade1cde7ba5d4b860295f47300222ecdd40c7fa5a8dcb537f1de5d` |
| `plugins/code/skills/ponytail/SKILL.md` | `1316a2f3f95741d2300b116fe0c2d81ce4a9568656ed0a62643f54aaf09957f2` | `110fd4a588f09ae9f2ea560e4d1ec02fdcef914be605ae7e5699d627fd136d8d` |
| `plugins/code/skills/speckit-agent-context-update/SKILL.md` | `02e3a158a6f6b452a8d18e75393a7d22752e2b9a9fa86fb48982653d75df5780` | `4a11efd0fb71660f6c5afccd1a2ee76f4812b3e35712bc0099725a6cc08fa324` |
| `plugins/code/skills/speckit-analyze/SKILL.md` | `f2c4922f92e69cba230313925ff0a3eccfe5e2460aaf9a78339465acea6e255d` | `42e1642ec432ccc8d9a2853a4f3334db7ec6b291301d95fb4d7f9298e209851e` |
| `plugins/code/skills/speckit-assess-decide/SKILL.md` | `aac9a75729fa271a0dd6983ae5c1784f95e2d0de8cf211b2e7f0de78abaa3bf0` | `28437b8fc183a9b73f0d25eab1b9f2aa207d59dae5a0deb6b2ee2f5a3851265f` |
| `plugins/code/skills/speckit-assess-define/SKILL.md` | `1b16495c46dd6f8d0f396f1ca8b910424a79b118bf154b9207610f66fa52d491` | `1572a0db1000042ad6cd0506751813dc38b8e2f3dcfb87e71aa497e5f778e434` |
| `plugins/code/skills/speckit-assess-intake/SKILL.md` | `819c9602f6175b1c5a8cc31aace48ced0a20c11ae2a953261c3c115623e897ed` | `202a33a93591f2d33e9d7b0c47703cf1336c13619b707f69763ff6b727d2b449` |
| `plugins/code/skills/speckit-assess-research/SKILL.md` | `570d9ab488fd011939089a331c2876b26d94a2d118f2e1cd02b89916c9e85018` | `7ec3123bc8bba94a8c6db2d8d836f58652f573a66c4fa7e4be1e6df91fdf2372` |
| `plugins/code/skills/speckit-assess-shape/SKILL.md` | `4619436daf1a2375ed50b2580c5ab0aeab61cfc3fab455bbf9428f309c768cef` | `f76d1d38a2cda6b8e7cf6d89dcfc4273a8958e62bedbbaef36dd9e9c159a159b` |
| `plugins/code/skills/speckit-bug-assess/SKILL.md` | `588fb6f24530d6c7d435b7a18752bbf13e316ce5265996262c6b70815ebc7685` | `3c1f11e7a28788412d4394cacd91ca93bdbb50129f193547189ccd3a6bcb417c` |
| `plugins/code/skills/speckit-bug-fix/SKILL.md` | `fbd1365c4e8932d7db0c4f878e701faa7be807aa28b2b033890ed347a4559e4d` | `733ca3dbb1e39a540bdc89378ae9c24ac1812d3e398f229c0be504d1925eae0a` |
| `plugins/code/skills/speckit-bug-test/SKILL.md` | `031433e81a2b4f85566e37848263cff7a65424a97f2c7724d96f863140d719be` | `f87add7777efa965d9ee3dedd06dcec6cb47954792963847a022e429688f3f74` |
| `plugins/code/skills/speckit-checklist/SKILL.md` | `8320111ff46e857d0be7b19840ecdb4a4c4420283cd49849ec4199f3f78fcf6c` | `4ba2c3bb456ccbe5b4caf6ebabaefe196028d081a8221638a55de822d7eca15b` |
| `plugins/code/skills/speckit-clarify/SKILL.md` | `4b5ac0430fecc2d35bc511f915ef0a8683179c44c755c02dddebb1571314600d` | `3b63b3beeaf425a2f5b23692f0bd738d76c91486611477acb6e306c95b9dd6ac` |
| `plugins/code/skills/speckit-constitution/SKILL.md` | `ff1c53d0919320a4ff24832ad8cdad11d7aec01cc0da8975c5c4801ce4b26f38` | `72542fe7b1ce1e77e751035a186dd5031ee70e0cd5dec9470ce70c8f14ba6724` |
| `plugins/code/skills/speckit-converge/SKILL.md` | `53fcc116e33338948e122e616fac09710db513b4cbe3c6d2887cc1d8eb8ab584` | `711d7db347abbe671875cc72bfee5ca812b19b0b2e501decd8330ff5bf3cba0f` |
| `plugins/code/skills/speckit-git-validate/SKILL.md` | `59f38e01de13af26984f1f30367be4be751b19a532cb556f452ce7795cc21921` | `fa2308f2449e25003d241b15862f959fab1a18bd3c1b16effceca94368f38d93` |
| `plugins/code/skills/speckit-implement/SKILL.md` | `ad3ff917f45aa4c744ac0af95550ff3bdc5137684cee3ad9a1a5a088a0414807` | `19e2f38f2c6a9babb101232b4c4d81340d6472268a51cf05e2eb6c1e41c6e4ca` |
| `plugins/code/skills/speckit-plan/SKILL.md` | `94a2c69cdd7d0cdda67e7f92a6c6f280b139a875fde38b6bfcf1194dc671439e` | `f1260ac97f5dcf28be592f01074b053a71d415c090672756ffa0ae0e75814aa2` |
| `plugins/code/skills/speckit-specify/SKILL.md` | `ea5bf8037e95a348d05d0d3e29e7a216bbdd7c1bb7a256b0b12698a9f887f822` | `819a52903c6b740e82532e93c30f5a46cc25f266adbfd2ab2bed3789997aa1a5` |
| `plugins/code/skills/speckit-tasks/SKILL.md` | `248ae2e1e99beb4e6c0f49d824acb3e7ac8d105f16ec9f9e3ef1a3c6107ced4d` | `168d0fa8585f933a85196bac0c677cccfe9d75c3b23147c6d964c45755ba5f00` |
| `plugins/code/skills/speckit-taskstoissues/SKILL.md` | `0b846de853933dd50736574075b2728427b90f3bead85a9c1c37286396ccb3c6` | `b992837eac9f191b1851c2f480703e2b10056803a15d90467b0c8f9eed2f6336` |
| `plugins/code/skills/verification-before-completion/SKILL.md` | `2befe7fc55bcadaa3d97dd9e8efeb633d2561c0ebe74c5a8b17c4d9e7e4520b3` | `066f5d449850750238513e8874fa22246fb1450248bd7bb98bfcdb369597dfd2` |
| `plugins/work/skills/backfire/SKILL.md` | `32a60316f9d603d27c676b11ac2a91f7744f5971345872bd34a820963aba9726` | `f93c1d37e2c2ad90cdd8463e8cb73353b6ed3c6e80b3819d622883a9bf3fc4e5` |
| `plugins/work/skills/google-workspace/SKILL.md` | `320762e8a9c865cae95c1d8838e68955210fca94f220aec565a172d69b10a19d` | `e8eca0f82c6318e3786fbe8727cb4b45398e51b055d60c3403e5942d9c76dd6e` |
| `plugins/work/skills/grammatical-competence/SKILL.md` | `f3e2b1f851aa6442b2141990c9f658e7cd9c9fd46e67a03fcc220c96bfaa6c20` | `7627230c685e442e3d73b78ceef9b200906d98f888bfc91fdf33edc6414bab1a` |
| `plugins/work/skills/gws-calendar-insert/SKILL.md` | `5c54f18a615b9706a364815f9e3c0ef8c83bba8a67adf217e25dd7c829e2119e` | `bc4f76e1fa7521ce2b3eff7383bd710902c9471ff3b0755bd83a2fd977fc9170` |
| `plugins/work/skills/gws-docs-write/SKILL.md` | `219028230078e0d14df314f2ae18b5918721fb5e298bba7d0a010937b2965045` | `9ca060feeba6cf394a5817eefbae422532f116d2c8bca1788d458e8319ac230b` |
| `plugins/work/skills/gws-docs/SKILL.md` | `676eb7a1d9e4a7bde0d19669299858daea3220650657199f21dcebb7fa6bf9d6` | `e912fb5d58efd918747f75087c6a8eddfc84a4bd41f9fbcda3c55e01befcd9f1` |
| `plugins/work/skills/gws-drive-upload/SKILL.md` | `7ffd4bdffab870e3aab8b9081b60d485dc5d0bb7f6e6524ee84100a630f84595` | `23c55b40a16d21855890d037b211ff101d62eb5c62bf6ade6fdab42bf9e8e379` |
| `plugins/work/skills/gws-forms/SKILL.md` | `857801e4e8b710002bdf7ac8f7a5c39a0475e4c8c5b17a1e65fa5c487c00f9f3` | `5a5e047add3f872893029ed3275f453b43d90553635d7f6a53e5fa80ab729820` |
| `plugins/work/skills/gws-shared/SKILL.md` | `3912d2d8f2f8ed07e91aae9c35913398d75eac665e1dbb8c8b227463484a3d39` | `79391303e53106b11f43c11d46ab586e247b15b6381ca79a23a5c8ff49e51610` |
| `plugins/work/skills/gws-sheets-append/SKILL.md` | `20611381c4ee91f4eeb6491185e0780207bfc08fff66d0c1d1c22c2c75c68657` | `098d1b7adb0109ac765bbd9c7cee99fee2ab4de91a8f1396fb197d92aa8dbff7` |
| `plugins/work/skills/gws-sheets-read/SKILL.md` | `2308eab564907f4d8789de030dadebf9187988a944a57da9ffd49ce7a4ecafef` | `ddbb99ac37ae6db712cabb7788fec6d60380c1cd2f8644619eb34d6333843b50` |
| `plugins/work/skills/gws-sheets/SKILL.md` | `e0db8bb632b3425b6f10dac7b30c85a4ba6ed0fd8421bccd3d2242588cc02208` | `b108444dfd1a81021d8249c70f93ff42466883cefd5fa25efdf74593f38288d0` |
| `plugins/work/skills/gws-slides/SKILL.md` | `ac0feaccf8292d5a8de0f4e3fbbdc20b94cf15afea652d127ddc12f631e190a3` | `adea3c77c0664baf567727bdc9d409809530bd692c2416420112c3cec4718001` |
| `plugins/work/skills/quarto-authoring/SKILL.md` | `57beae14195562148b1cb9409cd95228df52265d0d7ace639004014f8b95df16` | `6eea4ef8af3df112182ccea2fcc7e463562fac5cf5cc944a9dc6f062dc20bd83` |
| `plugins/work/skills/session-migrate/SKILL.md` | `051060df7d7decbe36a5b3879fa1a8f344a159ce06d848ceae225ad21f173ce3` | `8700b7ad2345ed78c31fa524d31f1a5ad8bb59221984f944efb78795ba30c02c` |
| `plugins/work/skills/wiki-consistency/SKILL.md` | `2c999bdf9b41a3410c4f6883a011959407493ffff642807c24b816b682715fb4` | `ec1233e8637f71748e93041d81ec9ee18c737a3ea012b56a729860bb4ca05e13` |
| `plugins/work/skills/wiki-raw-import/SKILL.md` | `49a30394f028773396e8096126a2919ecd6597c3cf3d3b815d818294e058ad80` | `9d26d2bfc90308e2ad2bdf625803011ddc888ef1ecb44b9356654802974ca5c4` |
