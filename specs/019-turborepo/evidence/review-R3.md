# CHE-32 final review R3: coordinator changes

Assumption: the user's 2026-09-29 approval of the governance wording is the separate governance-step exception recorded in `tasks.md` T014, even though the earlier selected-site lists leave those governance sites unchanged.

Scope: read-only review at `9d8af61` of `b1f8fff`, `d5eb6be`, the coordinator-authored additions in `bcaf7cc`, and the `spec.md`, `research.md`, and `tasks.md` records against the implementation and commit history. I did not edit, stage, or commit other files.

## Findings

1. **Should-fix — architecture documentation omits the code plugin's package manifest.** `docs/architecture.md:11` says only the clean-code skill has its own npm package manifest, but `plugins/code/package.json:1-5` is a second `package.json` at the plugin root, added by D18 to declare the `./cli` export. D18 describes this manifest at `research.md:215-220`, while T008 records it at `tasks.md:102-103`. Clarify that the plugin-root file is import-boundary metadata and the nested skill manifest is the installable skill's dependency manifest; also make `docs/architecture.md:22` say “npm package manifest” when describing the chat package.

2. **Note — D18's saved decision result omits its input record.** `research.md:225-227` cites `evidence/decide-d18.json`, but that file has only the tool result and indexed requirement checks (`decide-d18.json:1-19`); it has no `arguments` block containing the decision question, evidence, candidates, requirements, or priorities. Unlike D17's artifact (`decide-d17.json:4-24`), the D18 artifact therefore does not let a reader audit which inputs produced the choice. Preserve the D18 arguments alongside the result, as done for D17, to fully satisfy `spec.md:144-148`'s retained-judgment requirement.

## Review notes

- D17 matches the user decision and the constitution's amendment rule: `b1f8fff` is `feat(constitution)` with no breaking marker, and the constitution moves from 2.1.0 to 2.2.0 exactly as the middle-version bump requires (`.specify/memory/constitution.md:2-3, 211-218, 261`).
- The governance edits in `AGENTS.md` and the constitution match the user-approved npm command wording. The full-removal selection leaves the earlier `AGENTS.md` hits unchanged; the later user authorization is recorded in the feature input and T014 records the applied wording (`spec.md:22-26`; `selected-sites-full-removal.md:31-34`; `tasks.md:130-135`).
- D18's replacement manifest carries the old selected `plugins/code/deno.json` export into `plugins/code/package.json`; Git recognizes the path change as a 78% rename. The three root dependencies match the clean-code skill manifest and root lock, and a read-only Node resolver check found all three from the skill script's path.
- `d5eb6be` changes four files (`AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/backfire.md`); `docs/reference/commands.md` is changed in `bcaf7cc`, not `d5eb6be`.
- The feature remains in progress: `spec.md:7` and `tasks.md:136-138` leave final verification, fresh reviews, the review record, feature finish, and issue completion pending, which matches the unmerged branch state.

## Commands and results

- `git status --short --branch` — exit 0. The initial snapshot was clean; later snapshots showed untracked `review-CR1.md`, `review-CR2.md`, and `review-CR3.md`, which I did not open or modify.
- `git diff --stat 8ce9b2a 9d8af61` and `git diff --name-status 8ce9b2a 9d8af61` — exit 0.
- `git show --stat` / `git show` for `b1f8fff`, `d5eb6be`, and `bcaf7cc` — exit 0.
- `git diff --check b1f8fff^ b1f8fff`, `git diff --check d5eb6be^ d5eb6be`, and `git diff --check bcaf7cc^ bcaf7cc -- package.json package-lock.json plugins/code/package.json` — exit 0.
- `git diff --check 8ce9b2a 9d8af61 -- . ':!specs/019-turborepo/evidence/logs/**'` — exit 0. The full diff check without the exclusion exits 2 because captured Turborepo logs contain trailing spaces in task labels and timing output.
- Read-only Node check comparing the three root and skill dependency pins with `package-lock.json` — exit 0; all pins match.
- Read-only Node `createRequire(...).resolve(...)` for `eslint`, `typescript-eslint`, and `@typescript-eslint/utils` from the clean-code script path — exit 0; all resolve from root `node_modules`.
- `rg -n 'plugins/code/package\.json'` across both selected-site lists and `classify-full-removal.json` — exit 1 (no direct entry); the prior `plugins/code/deno.json` is selected for deletion at `selected-sites-full-removal.md:110-112`, and Git records the resulting path as a rename.
- `npm run workflow`, `npm run verify`, and test/build commands were not run because this was a strict read-only review; `workflow` and `verify` write `.git/workflow` evidence.
