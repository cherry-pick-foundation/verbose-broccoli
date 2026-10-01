#!/bin/sh
# Check file and folder names with ls-lint (.config/ls-lint.yml) in every path
# that Git does not ignore. ls-lint has no .gitignore support, so this adds
# the ignored paths as literal `ignore` entries through a second config read
# from standard input; ls-lint merges it with .config/ls-lint.yml.
# `--directory` lists an ignored folder once, not its contents. Paths come
# from Git as literal names (`core.quotepath=off` keeps non-ASCII names
# unquoted) and are quoted for YAML; none is a wildcard pattern
# (specs/034-kebab-file-names/security/ls-lint-2.3.1.md, control 3). The
# 60-second limit is that review's control 2. A name that holds a newline
# cannot match an entry and is checked.
set -eu

ignored="$(git -c core.quotepath=off ls-files --others --ignored --exclude-standard --directory)"
{
  echo 'ignore:'
  printf '%s' "${ignored}" | sed "s/'/''/g; s|/\$||; s|.*|  - '&'|"
} | timeout 60 ls-lint -config .config/ls-lint.yml -config /dev/stdin
