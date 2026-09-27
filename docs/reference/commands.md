# Command reference

Generated file. Do not edit; refresh with deno task docs:generate.

Input owners: [deno.json](../../deno.json), [scripts/doctor.ts](../../scripts/doctor.ts), [scripts/workflow.ts](../../scripts/workflow.ts), [scripts/clean\_architecture.ts](../../scripts/clean_architecture.ts), [scripts/validate\_plugins.ts](../../scripts/validate_plugins.ts), [plugins/code/skills/clean-code/scripts/clean\_code.ts](../../plugins/code/skills/clean-code/scripts/clean_code.ts).

| Task                    | Invocation                        | Declared description                                                                                                                  |
| ----------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| check                   | deno task check                   |                                                                                                                                       |
| clean-architecture      | deno task clean-architecture      |                                                                                                                                       |
| clean-code              | deno task clean-code              |                                                                                                                                       |
| clean-code:scope        | deno task clean-code:scope        |                                                                                                                                       |
| docs:check              | deno task docs:check              |                                                                                                                                       |
| docs:generate           | deno task docs:generate           |                                                                                                                                       |
| doctor                  | deno task doctor                  | Verify Deno 2.9.6, Quarto 1.10.18, uv 0.11.32, git-flow 2.1.0 and its shared config, the Spec Kit environment and locked dependencies |
| format                  | deno task format                  |                                                                                                                                       |
| format:check            | deno task format:check            |                                                                                                                                       |
| lint                    | deno task lint                    |                                                                                                                                       |
| lint:fix                | deno task lint:fix                |                                                                                                                                       |
| plugins:validate        | deno task plugins:validate        |                                                                                                                                       |
| test                    | deno task test                    |                                                                                                                                       |
| test:clean-architecture | deno task test:clean-architecture |                                                                                                                                       |
| test:clean-code         | deno task test:clean-code         |                                                                                                                                       |
| test:cli-contract       | deno task test:cli-contract       |                                                                                                                                       |
| test:docs               | deno task test:docs               |                                                                                                                                       |
| test:doctor             | deno task test:doctor             |                                                                                                                                       |
| test:git-flow           | deno task test:git-flow           |                                                                                                                                       |
| test:plugin-skills      | deno task test:plugin-skills      |                                                                                                                                       |
| test:workflow           | deno task test:workflow           |                                                                                                                                       |
| typecheck               | deno task typecheck               |                                                                                                                                       |
| verify                  | deno task verify                  |                                                                                                                                       |
| workflow                | deno task workflow                |                                                                                                                                       |

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
  --deno      <path>  - Absolute path to standalone Deno.
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
