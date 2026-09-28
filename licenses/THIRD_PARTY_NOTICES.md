# Third-party notices

## Node compatibility types

- `@types/node@22.20.2` (MIT, DefinitelyTyped contributors) pins the existing
  Deno compatibility API types for type checks. This adds no Node executable or
  runtime adapter.

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
- `clean_code.ts` reuses ESLint, typescript-eslint, TypeScript, and Deno
  standard libraries through the skill's isolated, pinned Deno configuration.
  The local code connects the approved scope predicates to those
  implementations.

## runreal/deno-monorepo-template

- Source: <https://github.com/runreal/deno-monorepo-template>
- Revision: `7f7144cfce5f456fd5f59b50d525a872ddb338e0`
- Reused: `apps/`, `packages/`, root `deno.jsonc` workspace organization and
  root task orchestration.
- Adaptation: three Agent Plugins replace the example web applications; approved
  dependency pins and Deno permission policy replace the template stack. The
  plugin roots now use `plugins/{chat,code,work}` and strict `deno.json`; the
  original template attribution and parsed configuration remain preserved.
- Copyright (c) 2025 runreal. [MIT license](runreal-deno-monorepo-template.txt).

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

## jkudish/jev-mcp — backfire tools

- Source:
  <https://github.com/jkudish/jev-mcp/tree/a1fcc1e47fc696614f081e23a66ff48a890f22fd>
- Revision: `a1fcc1e47fc696614f081e23a66ff48a890f22fd` (release 0.9.0).
- Reused: the tool definitions and decision logic of `src/index.ts` and
  `src/lib.ts`, ported to Python as the `backfire` tools in
  `packages/backfire/src/backfire/`. The port's five recorded differences, the
  original files' SHA-256 and the license text are in
  `packages/backfire/src/backfire/UPSTREAM.md`. No upstream source file is
  copied into the repository.
- Reused: the agent skill `skills/jev`, vendored as
  `plugins/code/skills/backfire/` with four recorded changes that its
  `upstream.json` lists.
- Copyright (c) 2026 Joey Kudish.
  [MIT license](../plugins/code/skills/backfire/LICENSE).

## typesafe-ai/system-one-adapter-python — backfire judgments

- Source: <https://github.com/typesafe-ai/system-one-adapter-python>, published
  on PyPI as `system-one-adapter` 0.2.1.
- Used as a pinned Python dependency of `packages/backfire/`, locked in its
  `uv.lock` and installed with it by `uv sync`. No source is copied into the
  repository.
- Copyright (c) 2026 TypeSafe AI. MIT license.

## nedbat/cog — document regions

- Source: <https://github.com/nedbat/cog>, published on PyPI as `cogapp`
  3.6.0.
- Used as a pinned Python dependency of `packages/doc-regions/`, locked in its
  `uv.lock`, to check and regenerate mechanical regions. No source is copied
  into the repository.
- Copyright (c) 2004-2024 Ned Batchelder. MIT license.

## executablebooks/markdown-it-py — document units

- Source: <https://github.com/executablebooks/markdown-it-py>, published on
  PyPI as `markdown-it-py` 4.2.0.
- Used as a pinned Python dependency of `packages/doc-regions/`, locked in its
  `uv.lock`, to split agent regions into units. No source is copied into the
  repository.
- Copyright (c) 2020 ExecutableBookProject. MIT license. It includes
  markdown-it, Copyright (c) 2014 Vitaly Puzrin, Alex Kocharin, MIT license.

## lycheeverse/lychee — local link check

- Source: <https://github.com/lycheeverse/lychee/releases/tag/lychee-v0.24.2>.
- Used as a host tool at `~/.local/bin/lychee`, installed from the release's
  `lychee-x86_64-unknown-linux-gnu.tar.gz` after a SHA-256 check, and run
  offline by `deno task doc-regions:check`. Nothing is copied into the
  repository.
- Copyright (c) 2022 The lychee maintainers. MIT or Apache-2.0, at the user's
  choice.

## RbBtSn0w/spec-kit-extensions — MemoryLint audit

- Source:
  <https://github.com/RbBtSn0w/spec-kit-extensions/releases/tag/memorylint-v1.5.1>,
  archive `memorylint.zip` with SHA-256
  `df4b31049dcd7f794e7bbed1460b5f5f5008b12a966939366e354926bb5f6648`.
- Used by `deno task doc-regions:audit`, which downloads the archive into the
  user's cache and runs its read-only `scripts/audit_workspace.py`. Nothing is
  copied into the repository.
- Copyright (c) 2026 Spec-kit Community. MIT license.
