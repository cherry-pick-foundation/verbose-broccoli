#!/bin/sh
# Print one hash over the programs outside the repository that cached
# Turborepo tasks run, so that a different version of any of them changes
# every task hash and reruns the task (specs/039-cpu-load-relief/research.md,
# D3). Each line is a version, a resolved interpreter path, or the Git
# configuration that lives outside the repository. Only standard output is
# hashed: warnings can carry process IDs, and a missing program prints
# nothing, which still changes the hash.
{
  node --version
  npm --version
  uv --version
  readlink -f "$(uv python find 3.14)" .venv/bin/python tools/*/.venv/bin/python
  python3 --version
  git --version
  git flow version
  vale --version
  git config --system --includes --list
  git config --global --includes --list
} 2>/dev/null | sha256sum
