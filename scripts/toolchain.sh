#!/bin/sh
# Print one hash over what cached Turborepo tasks run from outside the
# repository's own files, so that a change to any of it changes every task
# hash and reruns the task (specs/039-cpu-load-relief/research.md, D3 and
# D4): the versions of the programs, their resolved interpreters, the Git
# configuration that lives outside the repository, and the contents of the
# installed npm trees, which Turborepo's globs skip. Only standard output is
# hashed: warnings can carry process IDs, and a missing program prints
# nothing, which still changes the hash.
{
  node --version
  npm --version
  uv --version
  readlink -f "$(uv python find 3.14)" .venv/bin/python \
    tools/ruff/.venv/bin/python tools/shellcheck/.venv/bin/python \
    tools/check-jsonschema/.venv/bin/python
  python3 --version
  git --version
  git flow version
  vale --version
  git config --system --includes --list
  git config --global --includes --list
  find node_modules packages/wiki-consistency/node_modules -type f -print0 |
    sort -z | xargs -0 sha256sum
} 2>/dev/null | sha256sum
