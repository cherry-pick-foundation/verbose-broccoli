# Third-party notices

## wondelai/skills — clean-code

- Source:
  <https://github.com/wondelai/skills/tree/c172996495bed0fcd26896a9416b2093fd7073f0/clean-code>
- Revision: `c172996495bed0fcd26896a9416b2093fd7073f0` (skill version 1.4.0).
- Reused: `SKILL.md` and all six reference files in
  `plugins/code/skills/clean-code/`.
- Adaptations: require the shared mechanical file selection; remove the
  diagnostic recommending extraction at twenty lines; let the checker own the
  length limit. Reference files remain unchanged.
- Copyright (c) 2025 Wondel.ai sp. z o.o.
  [MIT license](../plugins/code/skills/clean-code/LICENSE).

## Agent Plugins

The unchanged Agent Plugins 1.0 JSON Schemas are vendored for offline validation
with the already approved Ajv dependency. Sources:
<https://agent-plugins.org/schemas/1.0.0/plugin.schema.json> and
<https://agent-plugins.org/schemas/1.0.0/mcp.schema.json>. The unchanged
[Apache 2.0 license](../scripts/vendor/agent-plugins/LICENSE) is included.

## biomejs/biome — agent guidelines

- Source:
  <https://github.com/biomejs/biome/blob/d37f24b5fa901916a1e1b488857dd3ee4c8e74ec/AGENTS.md>
- Revision: `d37f24b5fa901916a1e1b488857dd3ee4c8e74ec`.
- Reused: the evidence, before-editing, implementation-gate, fresh-review, and
  comment rules in the root `AGENTS.md` sections "Every change" and "Review".
- Adaptations: Biome commands, crates, changesets, and skill links are removed;
  the reviewer comes from the other provider, and this repository's workflow and
  verification tasks replace Biome's checks.
- Copyright (c) 2023-present Biome Developers and Contributors. Used under the
  Apache License 2.0, the same license as this repository ([LICENSE](../LICENSE)).

## danyuchn/iso-24495-skill — English plain-language techniques

- Source:
  <https://github.com/danyuchn/iso-24495-skill/blob/113656b0a6a6cbeb3b3c2bb7cf3bc29349cb05cf/references/english-techniques.md>
- Revision: `113656b0a6a6cbeb3b3c2bb7cf3bc29349cb05cf`.
- Reused: the English techniques in the root `AGENTS.md` section "English
  replies".
- Adaptations: condensed to six points; they are the English section under
  "Language techniques" in the user's adapted `plain-language` skill.
- Copyright (c) 2026 Dustin Yuchen Teng.
  [MIT license](danyuchn-iso-24495-skill.txt).

## github/spec-kit — Spec Kit

- Source: <https://github.com/github/spec-kit/tree/9118ed15a0ba65053469a94c560ea5d233f75884>
- Revision: `9118ed15a0ba65053469a94c560ea5d233f75884` (release 1.0.1).
- Reused: the ten core `speckit-*` skills in `plugins/code/skills/` and Spec
  Kit 1.0.1's generated files under `.specify/`, except `.specify/extensions/`
  and `.specify/extensions.yml` (see release 1.0.12 below). Later local edits
  are recorded in Git history.
- Extensions: the bundled `agent-context`, `assess`, `bug` and `git` extensions
  from release 1.0.12
  (<https://github.com/github/spec-kit/tree/e77daa9021d20db26b878f7dfa5640fe5a42d04e/extensions>)
  are installed under `.specify/extensions/`, unchanged except the
  `context_file` setting in `agent-context-config.yml`. The generated
  `.specify/extensions.yml` disables every Git hook and enables the two
  `agent-context` after hooks as non-optional; upstream marks those hooks
  optional. The ten skills
  generated from their commands, `speckit-agent-context-update`,
  `speckit-assess-*`, `speckit-bug-*` and `speckit-git-validate`, are reused
  unchanged in `plugins/code/skills/`.
- Copyright GitHub, Inc. [MIT license](github-spec-kit.txt).

## github/awesome-copilot — git-commit

- Source:
  <https://github.com/github/awesome-copilot/tree/e24be77e6f203409cf99ab7d5a67e1540cb386d3/skills/git-commit>
- Revision: `e24be77e6f203409cf99ab7d5a67e1540cb386d3`.
- Reused unchanged: `plugins/code/skills/git-commit/SKILL.md`.
- Copyright GitHub, Inc. [MIT license](github-awesome-copilot.txt).

## posit-dev/skills — quarto-authoring

- Source:
  <https://github.com/posit-dev/skills/tree/6ef6595abcb940756032b0fda6ca8ff3c69aed06/quarto/quarto-authoring>
- Revision: `6ef6595abcb940756032b0fda6ca8ff3c69aed06`.
- Reused unchanged: `plugins/work/skills/quarto-authoring/`; provenance in its
  `UPSTREAM.md`.
- Copyright (c) 2025 Posit PBC.
  [MIT license](../plugins/work/skills/quarto-authoring/LICENSE).

## vyctorbrzezowski/skills — session-migrate

- Source:
  <https://github.com/vyctorbrzezowski/skills/tree/b9937f768d7a85e6e5f3c4b6988a3244828e6a28/skills/session-migrate>
- Revision: `b9937f768d7a85e6e5f3c4b6988a3244828e6a28`.
- Reused: `plugins/work/skills/session-migrate/`, with the adaptations recorded
  in its `UPSTREAM.md`.
- Copyright (c) 2026 Vyctor Brzezowski.
  [MIT license](../plugins/work/skills/session-migrate/LICENSE).

## jkudish/jev-mcp — Backfire skills

- Source:
  <https://github.com/jkudish/jev-mcp/tree/a1fcc1e47fc696614f081e23a66ff48a890f22fd>
- Revision: `a1fcc1e47fc696614f081e23a66ff48a890f22fd` (release 0.9.0).
- Reused: the agent skill `skills/jev`, copied as
  `plugins/code/skills/backfire/` and again as
  `plugins/work/skills/backfire/`, with the changes that each copy's
  `upstream.json` lists, and the Noul tool's definition, questions and
  decision logic in `packages/backfire/src/backfire/noul.py`.
- Copyright (c) 2026 Joey Kudish.
  [MIT license](../plugins/code/skills/backfire/LICENSE).

## typesafe-ai/skills — model-choice

- Source:
  <https://github.com/typesafe-ai/skills/tree/65a39f393687675ce170e6094757de20370365b9/skills/typesafe-ai>
- Revision: `65a39f393687675ce170e6094757de20370365b9` (tag v0.5.7).
- Reused: `SKILL.md` and `LICENSE` in `plugins/code/skills/model-choice/`.
- Adaptations: listed in the skill's `upstream.json`; the local
  `references/model-choice.md` is this repository's own text.
- Copyright (c) 2026 TypeSafe AI.
  [MIT license](../plugins/code/skills/model-choice/LICENSE).

## daviddrysdale/python-phonenumbers — work plugin pseudonymization

- Source: <https://github.com/daviddrysdale/python-phonenumbers>, published on
  PyPI as `phonenumbers` 9.0.40, a Python port of Google's libphonenumber.
- Used as a pinned Python dependency of `packages/backfire/`, in its optional
  `education` extra, locked in the workspace's `uv.lock` and installed by
  `npm run backfire:install` for the work plugin's `serve-mcp --education`.
  No source is copied into the repository.
- Copyright (C) 2009-2011 The Libphonenumber Authors. Apache License 2.0.

## browser-use/jev-ultrafast — chat web agent

- Source:
  <https://github.com/browser-use/jev-ultrafast/tree/1231850a0bf1a0c0341fe408ef1668dbbfdfac46>
- Revision: `1231850a0bf1a0c0341fe408ef1668dbbfdfac46`.
- Reused: the `jev_ultrafast` package, its offline tests, `examples/run.py`,
  `examples/flights.py` and `scripts/check_guards.py`, copied into
  `packages/jev-ultrafast/` with its license.
  `packages/jev-ultrafast/UPSTREAM.md` records the original files' SHA-256
  and every difference (provider selection and Orca browser mode).
- Copyright (c) 2026 Browser Use.
  [MIT license](../packages/jev-ultrafast/LICENSE).

## googleworkspace/cli — gws agent skills

- Source:
  <https://github.com/googleworkspace/cli/tree/v0.22.5/skills>
- Revision: `705fb0ecac6f4249679958f6325b809b63fdde17` (tag v0.22.5).
- Reused: the skill folders `gws-shared`, `gws-docs`, `gws-docs-write`,
  `gws-sheets`, `gws-sheets-read`, `gws-sheets-append`, `gws-slides`,
  `gws-forms`, `gws-drive-upload` and `gws-calendar-insert`, copied into
  `plugins/work/skills/`. Each copy's `upstream.json` records the original
  `SKILL.md`'s SHA-256.
- Adaptations: `gws-shared` only. Its "Community & Feedback Etiquette"
  section is removed, and a note after the title sends the reader to the
  local `google-workspace` skill first. The other nine are unchanged.
- Copyright 2026 Google LLC. Used under the Apache License 2.0, the same
  license as this repository ([LICENSE](../LICENSE)).
