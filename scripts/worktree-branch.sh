#!/bin/sh
# Temporary glue; remove once `orca worktree create` offers a branch option.

fail() {
  printf 'worktree-branch: %s\n' "$1" >&2
  exit 1
}

root=$(git rev-parse --show-toplevel) || fail 'cannot find the worktree root'
name=${root##*/}

if ! branch=$(git symbolic-ref --quiet --short HEAD); then
  exit 0
fi

case $branch in
  main|develop|feature/*|release/*|hotfix/*) exit 0 ;;
esac

if git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
  exit 0
fi

has_other_branch=false
for ref in $(git for-each-ref --contains HEAD --format='%(refname)' refs/heads refs/remotes); do
  if [ "$ref" != "refs/heads/$branch" ]; then
    has_other_branch=true
    break
  fi
done
if [ "$has_other_branch" = false ]; then
  exit 0
fi

case $name in
  release-*)
    suffix=${name#release-}
    [ -n "$suffix" ] || fail 'release name must include a suffix'
    target=release/$suffix
    ;;
  hotfix-*)
    suffix=${name#hotfix-}
    [ -n "$suffix" ] || fail 'hotfix name must include a suffix'
    target=hotfix/$suffix
    ;;
  feature-*)
    suffix=${name#feature-}
    [ -n "$suffix" ] || fail 'feature name must include a suffix'
    target=feature/$suffix
    ;;
  *) target=feature/$name ;;
esac

if ! git check-ref-format --branch "$target" >/dev/null 2>&1; then
  fail "invalid target branch name: $target"
fi
if git show-ref --verify --quiet "refs/heads/$target"; then
  fail "target branch already exists: $target"
fi
if ! git branch -m "$target" >/dev/null 2>&1; then
  fail "could not rename branch to: $target"
fi
