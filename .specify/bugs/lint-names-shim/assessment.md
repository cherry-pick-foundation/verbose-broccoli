# Bug Assessment: lint-names test fails where ls-lint resolves through the mise shim

- **Slug**: lint-names-shim
- **Created**: 2026-09-30
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-66> (Linear CHE-66,
  read with `orca linear issue CHE-66`; host `linear.app`, allowlisted)
- **Verdict**: valid
- **Severity**: high (it stops `npm run verify` for every feature in a
  shim-based shell)

## Report (verbatim or summarized)

`npm run verify` fails on `develop` `a5b4600` at `//#test:lint-names`. Both
cases in `scripts/lint-names-test.ts` fail with `mise ERROR No version is set
for shim: ls-lint`. Shells whose PATH reaches the real install folder first
pass, which is why CHE-65's own runs passed. Expected: the test passes however
`ls-lint` is found, with the version the repository pins, and without a global
mise setting.

## Symptom

The test runs `scripts/lint-names.sh` in a temporary Git repository under
`/tmp`. Where `ls-lint` resolves to mise's shim
(`~/.local/share/mise/shims/ls-lint`), the shim looks for a mise config from
the current folder, finds none there, and exits with the error above.

## Reproduction

On 2026-09-30 at `develop` `a5b4600` (mise 2026.9.17, Node 24):

```sh
SHIM=~/.local/share/mise/shims
env -i HOME=$HOME PATH="$SHIM:/usr/bin:/bin" node --permission \
  --allow-fs-read='*' --allow-fs-write=/tmp --allow-child-process \
  --test scripts/lint-names-test.ts
```

Both cases fail with the shim error. Merely prepending the shims folder to an
activated shell's PATH is not enough: the run passed, because `npm run` and
the activated shell kept the real install folder reachable first.

## Suspected Code Paths

- `scripts/lint-names-test.ts:14-25` — `run` passes the caller's PATH on, so
  `sh scripts/lint-names.sh` finds whatever `ls-lint` the shell finds.
- `scripts/lint-names.sh:17` — calls `ls-lint` by name. In the repository root
  the shim works, so the script itself is fine; only the test's `/tmp`
  repositories lack a mise config.

## Root Cause Hypothesis

The test relies on PATH to name the right `ls-lint`. A shim is the right
answer only inside a folder with a mise config. Confidence: high; the
reproduction shows the exact error.

## Proposed Remediation

**Preferred**: in the test, resolve the pinned binary once from the repository
root with `mise which ls-lint`, and put its folder first on the PATH of every
command the test runs. Where the shim is first on PATH, the real binary now
wins. The script stays unchanged.

**Alternatives**:

- Run `ls-lint` through `mise exec` with the repository's config. Rejected: the
  script would need the repository path, and mise would run in `/tmp`.
- A global mise setting. Ruled out by the issue.

**Files likely to change**:

- `scripts/lint-names-test.ts`

**Tests to add or update**:

- The two existing cases, run with the shims folder ahead of the real binary's
  folder on PATH. Without the fix they fail on any machine with mise shims; the
  test file sets that PATH itself, so the failure no longer depends on the
  shell.

## Risks & Considerations

- The test needs `mise` on PATH; the repository already requires it
  (`mise.toml`).
- On a machine with no shims folder, the test is not a regression check for the
  shim, but still passes.

## Open Questions

- None.
