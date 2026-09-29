#!/bin/sh
# Count non-blank lines of locally owned code and tooling configuration at a revision (default HEAD).
rev=${1:-HEAD}
cd /home/choi-eunchang/workspaces/verbose-broccoli/feature-turborepo || exit 1
git ls-tree -r --name-only "$rev" | grep -E '\.(ts|mjs|js|py|sh|json|toml|yml|yaml)$|^scripts/git(-flow)?-hooks/' \
  | grep -v -E '^(specs|\.specify|licenses|docs)/|/fixtures/|__snapshots__|^scripts/vendor/|^plugins/code/hooks/|^plugins/code/tests/|(^|/)(deno\.lock|uv\.lock|package-lock\.json)$|/UPSTREAM|^\.codex/|^\.claude/|^plugins/work/skills/quarto-authoring/|^tools/spec-kit/|schema\.json$' \
  | while read -r f; do n=$(git show "$rev:$f" | grep -c -v '^[[:space:]]*$'); printf '%s\t%s\n' "$n" "$f"; done
