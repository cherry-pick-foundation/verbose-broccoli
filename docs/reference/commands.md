# Command reference

Generated file. Do not edit; refresh with npm run doc-regions:update.

<!-- [[[cog import doc_sources; cog.out(doc_sources.task_table("package.json", "turbo.json")) ]]] -->
| Task                     | Invocation                       | Declared description                                                                                                 |
| ------------------------ | -------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| backfire:install         | npm run backfire:install         |                                                                                                                      |
| check                    | npm run check                    |                                                                                                                      |
| clean-architecture       | npm run clean-architecture       |                                                                                                                      |
| clean-code               | npm run clean-code               |                                                                                                                      |
| clean-code:scope         | npm run clean-code:scope         |                                                                                                                      |
| commitlint               | npm run commitlint               |                                                                                                                      |
| constitution:bump        | npm run constitution:bump        |                                                                                                                      |
| doc-regions:audit        | npm run doc-regions:audit        | Run MemoryLint's read-only audit on AGENTS.md and the constitution                                                   |
| doc-regions:check        | npm run doc-regions:check        | Check mechanical regions and local links in the target documents, offline and without writing                        |
| doc-regions:prepare      | npm run doc-regions:prepare      | Print backfire requests for the agent regions before a develop merge review \(pass --base and --max-evidence-chars\) |
| doc-regions:update       | npm run doc-regions:update       | Regenerate stale mechanical regions in the target documents                                                          |
| doctor                   | npm run doctor                   | Run mise's project checks                                                                                            |
| format                   | npm run format                   |                                                                                                                      |
| format:check             | npm run format:check             |                                                                                                                      |
| lint                     | npm run lint                     |                                                                                                                      |
| lint:fix                 | npm run lint:fix                 |                                                                                                                      |
| lint:shell               | npm run lint:shell               |                                                                                                                      |
| plugins:validate         | npm run plugins:validate         |                                                                                                                      |
| python:imports           | npm run python:imports           |                                                                                                                      |
| test                     | npm run test                     |                                                                                                                      |
| test:backfire            | npm run test:backfire            |                                                                                                                      |
| test:clean-architecture  | npm run test:clean-architecture  |                                                                                                                      |
| test:clean-code          | npm run test:clean-code          |                                                                                                                      |
| test:cli-contract        | npm run test:cli-contract        |                                                                                                                      |
| test:commit-msg          | npm run test:commit-msg          |                                                                                                                      |
| test:concept-profile     | npm run test:concept-profile     |                                                                                                                      |
| test:constitution-bump   | npm run test:constitution-bump   |                                                                                                                      |
| test:credit-offers       | npm run test:credit-offers       |                                                                                                                      |
| test:doc-regions         | npm run test:doc-regions         |                                                                                                                      |
| test:git-flow            | npm run test:git-flow            |                                                                                                                      |
| test:gts                 | npm run test:gts                 |                                                                                                                      |
| test:jev-ultrafast       | npm run test:jev-ultrafast       |                                                                                                                      |
| test:mise-doctor         | npm run test:mise-doctor         |                                                                                                                      |
| test:plugin-skills       | npm run test:plugin-skills       |                                                                                                                      |
| test:plugins-validate    | npm run test:plugins-validate    |                                                                                                                      |
| test:ruff                | npm run test:ruff                |                                                                                                                      |
| test:wiki-consistency    | npm run test:wiki-consistency    |                                                                                                                      |
| test:wiki-raw-import     | npm run test:wiki-raw-import     |                                                                                                                      |
| test:workflow            | npm run test:workflow            |                                                                                                                      |
| test:worktree-branch     | npm run test:worktree-branch     |                                                                                                                      |
| turborepo                | npm run turborepo                |                                                                                                                      |
| typecheck                | npm run typecheck                |                                                                                                                      |
| verify                   | npm run verify                   |                                                                                                                      |
| wiki-consistency:install | npm run wiki-consistency:install |                                                                                                                      |
| workflow                 | npm run workflow                 |                                                                                                                      |
<!-- [[[end]]] -->

<!-- [[[cog import doc_sources; cog.out(doc_sources.command_help("scripts/workflow.ts", "plugins/code/skills/clean-code/scripts/clean_code.ts")) ]]] -->
## clean-code

```text
Usage: clean-code

Description:

  Check the mechanically selected Clean Code subset from the target workspace root.

Options:

  -h, --help  - Show this help.
  --scope     - Report the shared skill/checker file scope only.
```

## workflow

```text
Usage: workflow

Description:

  Select work mode, inspect code graphs and verify the current Git snapshot.

Options:

  -h, --help            - Show this help.
  --task      <id>      - Task identity for skill announcements.           (Default: "workspace")
  --base      <ref>     - Baseline Git commit or reference.                (Default: "HEAD")
  --plan      <path>    - JSON plan with exact files for each task.
  --verify              - Run checks and read the same Turbo run summary.  (Default: false)
  --graph     <choice>  - Inspect impact, symbol or policy.
  --file      <path>    - Repository-relative graph target file.
  --line      <line>    - Positive 1-based symbol line.
  --column    <column>  - Positive 1-based UTF-16 symbol column.
```
<!-- [[[end]]] -->
