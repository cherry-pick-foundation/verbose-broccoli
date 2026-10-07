# Command reference

Generated file. Do not edit; refresh with npm run doc-regions:update.

<!-- [[[cog import doc_sources; cog.out(doc_sources.task_table("package.json", "turbo.json")) ]]] -->
| Task                           | Invocation                             | Declared description                                                                                                                                                             |
| ------------------------------ | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| check                          | npm run check                          |                                                                                                                                                                                  |
| clean-architecture             | npm run clean-architecture             |                                                                                                                                                                                  |
| clean-code                     | npm run clean-code                     |                                                                                                                                                                                  |
| clean-code:scope               | npm run clean-code:scope               |                                                                                                                                                                                  |
| commitlint                     | npm run commitlint                     |                                                                                                                                                                                  |
| constitution:bump              | npm run constitution:bump              |                                                                                                                                                                                  |
| doc-regions:audit              | npm run doc-regions:audit              | Run MemoryLint's read-only audit on AGENTS.md and the constitution                                                                                                               |
| doc-regions:check              | npm run doc-regions:check              | Check mechanical regions and local links in the target documents, offline and without writing                                                                                    |
| doc-regions:prepare            | npm run doc-regions:prepare            | Print jev-mcp requests for the agent regions before a develop merge review \(pass --base and --max-evidence-chars\)                                                              |
| doc-regions:update             | npm run doc-regions:update             | Regenerate stale mechanical regions in the target documents                                                                                                                      |
| doctor                         | npm run doctor                         | Run mise's project checks; uncached because it checks the installed tools and environments                                                                                       |
| education-privacy-gate:install | npm run education-privacy-gate:install |                                                                                                                                                                                  |
| format                         | npm run format                         |                                                                                                                                                                                  |
| format:check                   | npm run format:check                   |                                                                                                                                                                                  |
| lint                           | npm run lint                           |                                                                                                                                                                                  |
| lint:fix                       | npm run lint:fix                       |                                                                                                                                                                                  |
| lint:names                     | npm run lint:names                     | Check file and folder names with ls-lint; uncached because Turborepo does not hash empty folders                                                                                 |
| lint:shell                     | npm run lint:shell                     |                                                                                                                                                                                  |
| python:imports                 | npm run python:imports                 |                                                                                                                                                                                  |
| secrets:refresh                | npm run secrets:refresh                |                                                                                                                                                                                  |
| skills:validate                | npm run skills:validate                |                                                                                                                                                                                  |
| test                           | npm run test                           |                                                                                                                                                                                  |
| test:clean-architecture        | npm run test:clean-architecture        |                                                                                                                                                                                  |
| test:clean-code                | npm run test:clean-code                |                                                                                                                                                                                  |
| test:cli-contract              | npm run test:cli-contract              |                                                                                                                                                                                  |
| test:commit-msg                | npm run test:commit-msg                |                                                                                                                                                                                  |
| test:constitution-bump         | npm run test:constitution-bump         | Test the constitution version bump; uncached because it runs mise exec, whose version and global config are not hashed                                                           |
| test:coordinator-context       | npm run test:coordinator-context       |                                                                                                                                                                                  |
| test:credit-offers             | npm run test:credit-offers             |                                                                                                                                                                                  |
| test:doc-regions               | npm run test:doc-regions               |                                                                                                                                                                                  |
| test:education-privacy-gate    | npm run test:education-privacy-gate    |                                                                                                                                                                                  |
| test:git-flow                  | npm run test:git-flow                  |                                                                                                                                                                                  |
| test:grammatical-competence    | npm run test:grammatical-competence    |                                                                                                                                                                                  |
| test:gts                       | npm run test:gts                       |                                                                                                                                                                                  |
| test:jev-ultrafast             | npm run test:jev-ultrafast             |                                                                                                                                                                                  |
| test:lint-names                | npm run test:lint-names                | Test the name check; uncached because it finds ls-lint through mise, whose version and global config are not hashed                                                              |
| test:mise-doctor               | npm run test:mise-doctor               | Test mise's project checks; uncached because it runs mise, whose version and global config are not hashed                                                                        |
| test:reference-library         | npm run test:reference-library         | Test the reference-library setup; uncached because it runs gio, a desktop program whose presence and version are not hashed                                                      |
| test:root-config               | npm run test:root-config               | Test the root layout, the single source of tool pins, the setup task and the Python package tasks; uncached because it runs mise, whose version and global config are not hashed |
| test:ruff                      | npm run test:ruff                      |                                                                                                                                                                                  |
| test:secrets-refresh           | npm run test:secrets-refresh           |                                                                                                                                                                                  |
| test:session-select            | npm run test:session-select            |                                                                                                                                                                                  |
| test:skills-links              | npm run test:skills-links              |                                                                                                                                                                                  |
| test:turbo-cache               | npm run test:turbo-cache               |                                                                                                                                                                                  |
| test:wiki-consistency          | npm run test:wiki-consistency          |                                                                                                                                                                                  |
| test:wiki-raw-import           | npm run test:wiki-raw-import           |                                                                                                                                                                                  |
| test:workflow                  | npm run test:workflow                  |                                                                                                                                                                                  |
| test:worktree-branch           | npm run test:worktree-branch           |                                                                                                                                                                                  |
| turborepo                      | npm run turborepo                      |                                                                                                                                                                                  |
| typecheck                      | npm run typecheck                      |                                                                                                                                                                                  |
| verify                         | npm run verify                         |                                                                                                                                                                                  |
| wiki-consistency:install       | npm run wiki-consistency:install       |                                                                                                                                                                                  |
| workflow                       | npm run workflow                       |                                                                                                                                                                                  |
<!-- [[[end]]] -->

<!-- [[[cog import doc_sources; cog.out(doc_sources.command_help("scripts/workflow.ts", "skills/code/clean-code/scripts/clean-code.ts")) ]]] -->
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
