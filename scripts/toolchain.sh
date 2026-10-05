#!/bin/sh
# Print one hash over what cached Turborepo tasks run from outside the
# repository's own files, so that a change to any of it changes every task
# hash and reruns the task (specs/039-cpu-load-relief/research.md, D3 and
# D4): the versions of the programs, their resolved interpreters, the Git
# configuration that lives outside the repository, and the installed npm and
# uv environments. For each environment it lists every entry with its type,
# permissions and link target; it hashes the contents of the npm trees,
# which Turborepo's globs skip, and of the uv files that embed this
# worktree's path or name. Those are read with the path replaced and with an
# entry point's interpreter line reduced to "python" (uv writes python or
# python3, both links to the interpreter resolved above), so that worktrees
# with the same files still match; the shell activation scripts, which no
# task runs, hold the worktree's name and stay out. Only standard output is
# hashed: warnings can carry process IDs, and a missing program prints
# nothing, which still changes the hash.
export LC_ALL=C
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
  for tree in node_modules packages/wiki-consistency/node_modules \
    packages/education-privacy-gate/node_modules; do
    find "${tree}" -printf '%m %y %p %l\n' | sort
    find "${tree}" -type f -print0 | sort -z | xargs -0 sha256sum
  done
  for venv in .venv tools/ruff/.venv tools/shellcheck/.venv \
    tools/check-jsonschema/.venv; do
    find "${venv}" -name __pycache__ -prune -o -printf '%m %y %p %l\n' | sort
    grep -v '^prompt = ' "${venv}/pyvenv.cfg"
    find "${venv}/bin" "${venv}/lib" -type f ! -path '*/__pycache__/*' \
      ! -name 'activate*' ! -name 'deactivate*' \( -path "${venv}/bin/*" \
      -o -name '*.pth' -o -name direct_url.json \) | sort |
      while IFS= read -r file; do
        echo "${file}"
        sed "1s|^#!.*/bin/python3*$|#!python|; s|${PWD}|.|g" "${file}"
      done
  done
} 2>/dev/null | sha256sum
