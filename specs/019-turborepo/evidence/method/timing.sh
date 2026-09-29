#!/bin/bash
for i in 1 2; do
  cd /tmp/claude-1000/-home-choi-eunchang-workspaces-verbose-broccoli-feature-turborepo/ca64935e-e9f7-4ed8-9107-8675f8f79090/scratchpad/base-8ce9b2a && /usr/bin/time -v ~/.deno/bin/deno task check > /tmp/claude-1000/-home-choi-eunchang-workspaces-verbose-broccoli-feature-turborepo/ca64935e-e9f7-4ed8-9107-8675f8f79090/scratchpad/time-base-$i.log 2>&1; echo "base $i exit=$?"
  cd /home/choi-eunchang/workspaces/verbose-broccoli/feature-turborepo && /usr/bin/time -v npm run check > /tmp/claude-1000/-home-choi-eunchang-workspaces-verbose-broccoli-feature-turborepo/ca64935e-e9f7-4ed8-9107-8675f8f79090/scratchpad/time-branch-$i.log 2>&1; echo "branch $i exit=$?"
done
