#!/bin/sh
# File-only checkout has no old bytes; renewing identical reviewed trust is safe.
config=.config/mise.toml
if [ "${3:-1}" != 0 ]; then
  git diff --quiet "$1" ${2:+"$2"} -- "${config}"
  case $? in
    1) ;;
    *) exit 0 ;;
  esac
fi
[ -f "${config}" ] && [ ! -L "${config}" ] || exit 0
reviewed=$(git rev-parse --verify "refs/heads/develop:${config}" 2>/dev/null) || exit 0
current=$(git hash-object --no-filters -- "${config}") || exit 0
[ "${current}" = "${reviewed}" ] || exit 0
mise trust "${config}"
