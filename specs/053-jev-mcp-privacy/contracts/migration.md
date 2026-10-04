# Migration Contract

Assumption: the historical dependency inventory below remains evidence of migration order. The built migration is recorded first; W3 line references describe HEAD 447f3f70cb30b33524e3f6a5e2b110a3b74e3863, not current callers.

## Built migration evidence

Phase A record: 61ff8b2, c28179f and c6610cb. Independent dependency review: f1dcad8 and 8582214. Portable skills: 76fc1a8. Gate core: 3ad4ae0. Proxy and all-tool tests: 40e2645. The coordinator inspected Phase A; CHE-84 holds were released for CHE-86 judgment/provider/privacy sections on 2026-10-05 at develop b7f3223, merged by c3e2c53. These records do not grant unrelated scope.

Workspace integration 750af5b, discovery 0e14ca3, work launchers ec352a9, Wiki/doc-regions 3c5279c and operator/current docs 579e869 repointed the repository consumers. Chat migration ec5f7f9, trust fixes aa6c319 and call accounting 9e80a5d completed the required dependency handoff before deletion 28e4ff0 (T018/T019). Reproduce the history with `git log --oneline $(git merge-base HEAD develop)..HEAD`.

Credit-offers `_answer` and browser `validate_choice` keep the former guarantees locally: exact choice/probability keys, finite nonboolean probabilities in [0,1], sum tolerance `0.01 + 1e-12`, chosen argmax tolerance `1e-9`, unknown malformed confidence and no margin condition. Browser sums preserve JavaScript numeric-key ordering. Both callers launch only the gated proxy and explicitly pass only an absolute `XDG_CONFIG_HOME`; the MCP SDK supplies baseline environment (`packages/credit-offers/src/credit_offers/__init__.py:35-52,132-178`; `packages/jev-ultrafast/src/jev_ultrafast/model.py:13-29,104-135`).

The browser charges attempted operation/target calls before dispatch, including failures; `MAX_STEPS * 2` is 120 attempts, separate from the 60-action guard (`agent.py:77-109`). Default upstream retries permit up to 3 fetch attempts per dispatched request (up to 360 explicit fetch attempts); actual processed requests and billing remain unknown. The proxy does not set `JEV_MCP_MAX_ATTEMPTS` (default 3, clamped 1-6). The 1.7-second per-step startup is a mocked-run figure only. Text generation remains held.

28e4ff0 removes the old tracked implementation, both old skills, guide, region scripts and dependency edges. Comparing `28e4ff0^:uv.lock` with `28e4ff0:uv.lock` shows ten removed packages: anyascii, backfire, jev-judge-mcp, jiter, openai, sniffio, system-one-adapter, tenacity, tomlkit and typesafe-sdk. `mcp` and `mcp-types` remain 2.2.0. Root `.python-version` is the sole pin for the gate and the three former Backfire-pin readers; existing unrelated package/tool pins remain. No private data is removed.

Numeric EduOK, dropped integer progress counters, restored supported upstream errors, one-direction ordinary-text candidate collisions and native Node resolution are implemented as recorded in [privacy-gate.md](privacy-gate.md). Final review/frozen verification, the held text helper, main's legacy-named Wiki domain-roster location and real-list population, and user-owned first-release activation remain open.

## Historical repoint order

1. Add reviewed gate/proxy, synthetic tests and upstream `jev` skill copies without registering a second live route.
2. After handoff, resolve workspace/locks and synthetic fixture runtime; apply the settled Wiki-domain separation with CHE-84 agreement, and apply the settled byte-identical portable-skill convention before imports or declarations change. Shared discovery/docs integration stays held until CHE-84 handoff.
3. Repoint `plugins/work/skills/wiki-raw-import/scripts/session_select.py:19-20,386,433-470`: `backfire_education.roster.load_roster` and `backfire_education.pseudonymize.compile_roster_pattern` currently feed a direct `backfire serve-mcp --education` launcher. Replace matching imports with the admitted minimal gate API, keep classification receipts and private-source safeguards, and launch `jev-mcp`. Existing `jev_classify` items/classes/purpose need actual result/error checks.
4. Repoint **HELD** `plugins/work/skills/grammatical-competence/scripts/grammatical_competence.py:146-162,170-172,210-214`: replace direct education Backfire launcher and JSON parser assumptions. Remove only the provider-era Hangul proposal refusal; preserve exact source/order/key/resume checks and bounded serialized requests.
5. Repoint **HELD** `packages/wiki-consistency/src/wiki_consistency/rules.py:12-13,204-275`: imports `backfire.failures.JudgmentError` and `backfire_education.roster.load_roster`. Its richer domain roster uses school spellings, names and student IDs for page validation. Preserve that domain behavior in a work-owned source interface; do not store IDs in the gate list. Root settled this separation on 2026-10-04: the work consumer owner retains source-backed domain checks, with CHE-84 agreement before deleting the old imports. That implementation handoff still blocks deletion.
6. Repoint request contracts in `packages/doc-regions/src/doc_regions/requests.py:33-42,45-76,80-143,189-190` and **HELD** Wiki requests/tests. Keep whole-payload bounds; remove transliteration only where its purpose was Hangul refusal. Current upstream accepts `claims/evidence`, `items/classes/purpose` and `propositions/context/auto_accept`; strict objects reject old fields.
7. Coordinate model-choice's `references/model-choice.md:234-243,294-329` launcher/tool examples with its `typesafe-ai` owner. Refresh both upstream `jev` skills and current links/rules. Historical specs, receipts and assessments remain unchanged.
8. Obtain chat-owner credit-offers repoint evidence; then replace manifests with one gated server, regenerate owned discovery and test native metadata. Delete obsolete implementation/dependencies only after every dependency edge is removed and the current caller scan is clean.

## Chat handoffs: exact dependency edges

The following W3 inventory and handoff requirements are historical. Their implemented outcome is recorded above; pending chat repoint no longer blocks deletion.

Credit-offers imports `ChoiceQuestion` from `jev_judge_mcp.domain`, `ProviderError` from `jev_judge_mcp.providers`, `DEFAULT_MODEL` from `jev_judge_mcp.providers.resolver`, `validate_choice` from `jev_judge_mcp.validation`, and `backfire.providers as providers` (`packages/credit-offers/src/credit_offers/__init__.py:13-18`). `judge` calls `provider_factory()(None)`, `evaluate(state, questions, DEFAULT_MODEL, None)` and close at lines 74-79. Consumers expect `.answers`, `.choice` and `.probabilities` at 130-157. Manifest dependencies are `packages/credit-offers/pyproject.toml:10,19`; skill policy references are `plugins/chat/skills/credit-offers/SKILL.md:22-23,78-80` (W3:50-54).

Chat owner must replace this with a bounded FastMCP client call to the same proxy, adapt classification probabilities/decision/error/close/usage, and preserve tracker filtering, six-hour window, notifications and exit statuses 0/1/3. Exact candidate files: `packages/credit-offers/pyproject.toml`, `packages/credit-offers/src/credit_offers/__init__.py`, `packages/credit-offers/tests/test_credit_offers.py`, `plugins/chat/skills/credit-offers/SKILL.md`. CHE-86 records and waits for this handoff; its workers do not rewrite them. The scheduled provider decision stays with the user. Pending chat work blocks Backfire/PyModel deletion rather than silently breaking imports.

Jev Ultrafast has no Backfire/System One imports. `packages/jev-ultrafast/pyproject.toml:11` depends on browser-harness and httpx. Direct provider selection/HTTP is in `packages/jev-ultrafast/src/jev_ultrafast/model.py:16-67`; OpenRouter's decisions root is `packages/jev-ultrafast/src/jev_ultrafast/providers.toml:18-22`. `choose` sends operation/target Choice heads at model.py:138-194; text generation sends page/goal text at 239-283 (W3:56-58).

Settled latest Root amendment: browser-choice judgments go through this gate in a later chat-owner task; the text-generation helper stays held, with no ungated student-data route. The direct HTTP model route cannot satisfy the always-on privacy gate or be accepted as a documented limit. The chat owner implements browser routing under its own handoff. Candidate files are `packages/jev-ultrafast/src/jev_ultrafast/model.py`, `packages/jev-ultrafast/src/jev_ultrafast/providers.toml`, `packages/jev-ultrafast/tests/test_agent.py`, `packages/jev-ultrafast/tests/test_providers.py`, `packages/jev-ultrafast/upstream.md`, `plugins/chat/skills/web-agent/SKILL.md`. Preserve own-tab controls at skill lines 69-74 and `packages/jev-ultrafast/scripts/check_guards.py`. CHE-86 performs no browser run or chat rewrite; it records the settled boundary and exact handoff. Routing acceptance requires chat-owner evidence; the text-generation hold is not an ungated route.

## Tool and skill changes

Upstream 0.13.0 keeps `jev_noul` with <=64 propositions, <=2,000 characters each and auto_accept >0.5. No production bespoke Noul shape was found in W3:42-48; prove compatibility with synthetic fixtures before deleting the 204-line local port and its copied-source notice. `jev_score` is absent; W3:48 and upstream-comparison.json found promises in docs/tests and no production caller. Confirm the synchronized production scan before removing those promises. `jev_audit` is the upstream extraction-audit tool, not a generic score replacement.

Review/gate use `diff` string or `files[] {path,diff}`, exactly one mode. Root settled this on 2026-10-04: remove Python-only `tests_format`, `tests_sha256`, `tests_weight` and typed error-code envelope assumptions at callers. Local evidence hashes and receipts stay authoritative; preserve local execution evidence and never infer actual testing from `jev_gate` output. Refresh `jev` from the pinned npm skill and retain needed privacy/own-account guidance, using the upstream name. Do not globally rename historical records (W1:155-203; D8).

## Runtime pin and external activation

The old-pin inventory below is historical; the three readers now use the root pin. External activation remains pending.

Read-only verification on 2026-10-04 found `.config/mise.toml:33` and `.github/workflows/docs-check.yml:33` reading `packages/backfire/.python-version`; `scripts/root-config-test.ts:258,267-270` creates the Backfire fixture directory and copies that pin. Both the root and package pin currently read `3.14.4`. T011 repoints all three readers/fixtures to the ROOT `.python-version`, preserving the reviewed runtime without a duplicate pin. T018 requires a clean scan for the removed path and `npm run test:root-config` before deleting the package pin. These files were inspected, not edited by the documentation worker.

Feature source finishes into develop. Main effective registration/provider-path updates wait for the FIRST OFFICIAL RELEASE, whose timing belongs to the user. Main holds RELEASED states only; no develop fast-forward or ad hoc merge into main. The release gets a fresh whole-repository review. Repository acceptance does not activate external clients, rewrite globals or authorize removal of preserved user data.

## Delete last

Source deletion was committed in 28e4ff0 after the caller migration. The inventory and private-data boundary below remain the deletion contract, not pending authorization to repeat deletion.

Remove the exact tracked `packages/backfire/` inventory only after caller/manifest checks, including its provider/config/credit/failure modules, Noul port, education persistence/detectors, obsolete tests and legal-district copy. Then remove `scripts/backfire-regions.ts`, `scripts/backfire-regions-test.ts`, old Backfire skill copies and `docs/backfire.md` after replacement links exist. Remove `jev-judge-mcp` and `system-one-adapter` from integrated locks only after credit-offers is clear. Retain unrelated adapter consumers if the synchronized scan finds any. Remove copied-source notices with their copies, not installed dependency licenses by association (AGENTS.md:85-92; W3:7-22).

Legacy real lists, mapping tables, locks, paid results and private source bytes remain untouched. Main separately decides operational retirement at the authorized first-official-release activation window. No authorization to remove private data follows from source deletion.
