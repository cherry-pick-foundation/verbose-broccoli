# Command reference

Generated file. Do not edit; refresh with npm run docs:generate.

Input owners: [package.json](../../package.json), [turbo.json](../../turbo.json), [scripts/doctor.ts](../../scripts/doctor.ts), [scripts/workflow.ts](../../scripts/workflow.ts), [scripts/clean\_architecture.ts](../../scripts/clean_architecture.ts), [scripts/validate\_plugins.ts](../../scripts/validate_plugins.ts), [plugins/code/skills/clean-code/scripts/clean\_code.ts](../../plugins/code/skills/clean-code/scripts/clean_code.ts).

| Task                     | Invocation                       | Declared description                                                                                                                                                                                                                             |
| ------------------------ | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| backfire:build           | npm run backfire:build           |                                                                                                                                                                                                                                                  |
| backfire:eval            | npm run backfire:eval            |                                                                                                                                                                                                                                                  |
| backfire:install         | npm run backfire:install         |                                                                                                                                                                                                                                                  |
| backfire:ready           | npm run backfire:ready           |                                                                                                                                                                                                                                                  |
| check                    | npm run check                    |                                                                                                                                                                                                                                                  |
| clean-architecture       | npm run clean-architecture       |                                                                                                                                                                                                                                                  |
| clean-code               | npm run clean-code               |                                                                                                                                                                                                                                                  |
| clean-code:scope         | npm run clean-code:scope         |                                                                                                                                                                                                                                                  |
| commitlint               | npm run commitlint               |                                                                                                                                                                                                                                                  |
| doc-regions:audit        | npm run doc-regions:audit        | Run MemoryLint's read-only audit on AGENTS.md and the constitution                                                                                                                                                                               |
| doc-regions:check        | npm run doc-regions:check        | Check mechanical regions and local links in the target documents, offline and without writing                                                                                                                                                    |
| doc-regions:prepare      | npm run doc-regions:prepare      | Print backfire requests for the agent regions before a develop merge review (pass --base and --max-evidence-chars)                                                                                                                               |
| doc-regions:update       | npm run doc-regions:update       | Regenerate stale mechanical regions in the target documents                                                                                                                                                                                      |
| docs:check               | npm run docs:check               |                                                                                                                                                                                                                                                  |
| docs:generate            | npm run docs:generate            |                                                                                                                                                                                                                                                  |
| doctor                   | npm run doctor                   | Verify Node.js 24.12.0 or later, Turborepo 2.11.5, Quarto 1.10.18, uv 0.11.32, git-flow 2.1.0 and its shared config, lychee 0.24.2, Ruff 0.16.9, the Spec Kit, ShellCheck, doc-regions and wiki-consistency environments and locked dependencies |
| format                   | npm run format                   |                                                                                                                                                                                                                                                  |
| format:check             | npm run format:check             |                                                                                                                                                                                                                                                  |
| lint                     | npm run lint                     |                                                                                                                                                                                                                                                  |
| lint:fix                 | npm run lint:fix                 |                                                                                                                                                                                                                                                  |
| lint:shell               | npm run lint:shell               |                                                                                                                                                                                                                                                  |
| plugins:validate         | npm run plugins:validate         |                                                                                                                                                                                                                                                  |
| test                     | npm run test                     |                                                                                                                                                                                                                                                  |
| test:backfire            | npm run test:backfire            |                                                                                                                                                                                                                                                  |
| test:backfire-slow       | npm run test:backfire-slow       |                                                                                                                                                                                                                                                  |
| test:clean-architecture  | npm run test:clean-architecture  |                                                                                                                                                                                                                                                  |
| test:clean-code          | npm run test:clean-code          |                                                                                                                                                                                                                                                  |
| test:cli-contract        | npm run test:cli-contract        |                                                                                                                                                                                                                                                  |
| test:commit-msg          | npm run test:commit-msg          |                                                                                                                                                                                                                                                  |
| test:credit-offers       | npm run test:credit-offers       |                                                                                                                                                                                                                                                  |
| test:doc-regions         | npm run test:doc-regions         |                                                                                                                                                                                                                                                  |
| test:docs                | npm run test:docs                |                                                                                                                                                                                                                                                  |
| test:doctor              | npm run test:doctor              |                                                                                                                                                                                                                                                  |
| test:git-flow            | npm run test:git-flow            |                                                                                                                                                                                                                                                  |
| test:gts                 | npm run test:gts                 |                                                                                                                                                                                                                                                  |
| test:jev-ultrafast       | npm run test:jev-ultrafast       |                                                                                                                                                                                                                                                  |
| test:plugin-skills       | npm run test:plugin-skills       |                                                                                                                                                                                                                                                  |
| test:ruff                | npm run test:ruff                |                                                                                                                                                                                                                                                  |
| test:wiki-consistency    | npm run test:wiki-consistency    |                                                                                                                                                                                                                                                  |
| test:wiki-raw-import     | npm run test:wiki-raw-import     |                                                                                                                                                                                                                                                  |
| test:workflow            | npm run test:workflow            |                                                                                                                                                                                                                                                  |
| test:worktree-branch     | npm run test:worktree-branch     |                                                                                                                                                                                                                                                  |
| typecheck                | npm run typecheck                |                                                                                                                                                                                                                                                  |
| verify                   | npm run verify                   |                                                                                                                                                                                                                                                  |
| wiki-consistency:install | npm run wiki-consistency:install |                                                                                                                                                                                                                                                  |
| workflow                 | npm run workflow                 |                                                                                                                                                                                                                                                  |

## clean-architecture

```text
Usage: clean-architecture

Description:

  Check import directions, cycles and public package boundaries from the workspace root.

Options:

  -h, --help  - Show this help.
```

## clean-code

```text
Usage: clean-code

Description:

  Check the mechanically selected Clean Code subset from the target workspace root.

Options:

  -h, --help  - Show this help.
  --scope     - Report the shared skill/checker file scope only.
```

## doctor

```text
Usage: doctor

Description:

  Check runtime identities, versions and locked dependencies.

Options:

  -h, --help          - Show this help.
  --quarto    <path>  - Absolute path to Quarto.
  --report    <path>  - Create a new JSON report; requires write permission.
```

## plugins:validate

```text
Usage: plugins:validate [roots...]

Description:

  Validate portable plugin and MCP manifests against the pinned schemas.

Options:

  -h, --help  - Show this help.
```

## workflow

```text
Usage: workflow

Description:

  Select work mode, inspect code graphs and verify the current Git snapshot.

Options:

  -h, --help            - Show this help.
  --task      <id>      - Task identity for the evidence loop.       (Default: "workspace")
  --base      <ref>     - Baseline Git commit or reference.          (Default: "HEAD")
  --plan      <path>    - JSON plan with exact files for each task.
  --verify              - Run all checks and retain evidence.        (Default: false)
  --graph     <choice>  - Inspect impact, symbol or policy.
  --file      <path>    - Repository-relative graph target file.
  --line      <line>    - Positive 1-based symbol line.
  --column    <column>  - Positive 1-based UTF-16 symbol column.
```
