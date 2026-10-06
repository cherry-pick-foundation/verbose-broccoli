# Security review: Spec Kit 1.1.0 adoption (T025, slice S2c)

Reviewer: Claude Code (Sonnet 5.5), read-only. Dispatch ctx_5d23e633156e.
Sources read on 2026-10-06 (UTC) from public GitHub. Nothing was installed or
run. The clone is in `/tmp/t025/spec-kit` (checked out at tag `v1.1.0`).
One small stdlib-only demo of path behavior is in `/tmp/t025/symdemo`.

## Verdict

**Adopt with conditions.** The upstream change adds no telemetry, no new
network host, no new dependency, and no new code that runs at install or
upgrade time. The one serious problem is a fit problem with this repository's
`.agents/skills` links: the planned `specify integration upgrade` would delete
the ten core `SKILL.md` files it has just written (F1). Conditions are listed
at the end.

Findings by severity: High 1, Medium 3, Low 4, Info 6 (14 in all).

## What was compared

- Command line: tag `v1.0.12` (`e77daa9`, 2026-09-25) to `v1.1.0`
  (`f1d3a4f8337ebbd3ae22760a9c12e3352b93a175`, 2026-10-02). 135 files, 41
  commits. About 10,900 added lines are tests.
- Project files: upstream `v1.0.1` (`9118ed1`, the revision the repository
  installed on 2026-09-12) to `v1.1.0`, for `scripts/bash`, `templates` and
  the bundled extensions `agent-context`, `assess`, `bug`, `git`, plus the new
  `github`.
- Repository files read: `.specify/`, `.agents/skills/`, `.codex/config.toml`,
  `tools/spec-kit/pyproject.toml` and `uv.lock`, `licenses/`, `docs/architecture.md`.

Hash check of installed files against upstream (so I know what is local):

- `.specify/scripts/bash/*` and `.specify/templates/*` equal the upstream files
  after the installer's own rendering (`__SPECKIT_COMMAND_X__` becomes
  `$speckit-x`). No hand edits there.
- Extensions `assess`, `bug`, `git` are byte-identical in `v1.0.12` and
  `v1.1.0` and equal the installed copies. Only `agent-context` changes
  (`extension.yml` version 1.0.1 to 1.0.2 and one line `"mcode": "AGENTS.md"`
  in `agent-context-defaults.json`). Its scripts, README and command file are
  unchanged.
- Local deviations that exist today: `agent-context-config.yml` has
  `context_file: ".claude/rules/current-plan.md"`; `.specify/extensions.yml`
  has the two agent-context after hooks non-optional and every git hook
  disabled; all 20 `speckit-*` `SKILL.md` files carry the plugin-rule pointer
  line; `.specify/.gitignore` has an added `.cache/` rule.
  `licenses/third-party-notices.md:45-64` already records these.

## Findings

### F1. High, blocks T028 as written: the upgrade deletes the ten core skill files through the links

Evidence:

- `src/specify_cli/integrations/base.py:638-642` (`write_file_and_record`):
  writes `dest.write_bytes(...)`, then records the key
  `dest.resolve().relative_to(project_root.resolve())`. `resolve()` follows
  the directory link, so the key becomes `plugins/code/skills/speckit-plan/SKILL.md`
  (after the move, `skills/code/...`), not `.agents/skills/speckit-plan/SKILL.md`.
- `.specify/integrations/codex.manifest.json` (installed 2026-09-12) records
  the ten keys as `.agents/skills/speckit-*/SKILL.md`.
- `integrations/command_upgrade.py:298` computes
  `stale_keys = set(old_files) - set(new_files)`, which is all ten old keys.
  Lines 301-308 then call `stale_manifest.uninstall(project_root, force=True)`.
  `integrations/manifest.py:386` does `path.unlink()` on `root/<old key>`. That
  path is a regular file seen through the link, so the real file in the plugin
  folder is removed. The `rmdir` of the parent fails on a link
  (`NotADirectoryError`), so the links stay but the files are gone.
- Demo in `/tmp/t025/symdemo` (plain `pathlib`, not Spec Kit code) printed:
  recorded key `plugins/code/skills/speckit-plan/SKILL.md`; real file written
  True; after the stale unlink, real file exists False; link still present True.
- `base.py` and `manifest.py` are the same in `v1.0.12`, `v1.1.0` and upstream
  `main` (9fb13c15, 2026-10-06), so no upstream fix is waiting. No upstream
  issue about this was found with a `gh search issues` query on 2026-10-06.

Failure case: run `specify integration upgrade --force` in the feature
worktree. It prints "upgraded successfully" and leaves ten empty skill
folders. Git can restore the old content, but then the upgrade is lost.

### F2. Medium: local edits block the upgrade without `--force`, and `--force` overwrites them

Evidence:

- A hash check of the repository against `.specify/integrations/*.manifest.json`
  (run on 2026-10-06) shows all ten `.agents/skills/speckit-*/SKILL.md` files
  and `.specify/.gitignore` differ from the recorded hashes.
- `command_upgrade.py:77-85`: modified files stop the upgrade (exit 1) unless
  `--force` is given.
- `--force` overwrites the pointer line in the ten core skills.
  `shared_infra.py:24-33` (`SPECIFY_GITIGNORE_CONTENT`) has no `.cache/` rule,
  so a forced refresh drops the repository's `.cache/` line. Extension catalog
  cache files then show up as untracked (`.specify/extensions/.cache/`).
- The ten extension skills lose the pointer too (see F3, F4).

Not a security risk. It matters for T026 (preset for the pointer) and for the
diff review.

### F3. Medium: re-registration writes extension skills, including four the repository does not package

Evidence:

- `command_upgrade.py:335` calls `_register_extensions_for_agent(..., force=True)`
  for the active integration (`integrations/_helpers.py:392-426`). It calls
  `register_enabled_extensions_for_agent` (`extensions/__init__.py:3881`),
  which renders every command of every enabled extension.
- The git extension declares five commands (`.specify/extensions/git/extension.yml:18-34`);
  the registry lists all five for codex. Only `speckit-git-validate` exists in
  `.agents/skills/` (`docs/architecture.md:711`: "Only `speckit-git-validate`
  is packaged").
- Expected result: new real directories `.agents/skills/speckit-git-feature`,
  `-git-commit`, `-git-initialize`, `-git-remote`, not links, untracked. The
  other ten extension skills are rewritten through their links and lose the
  pointer line.
- I could not confirm this without running the command; it follows from the
  code path above.

### F4. Medium: extension update or forced re-add resets hook settings; config must survive

Evidence:

- `extensions/_command_update_transaction.py:551`:
  `manager.remove(extension_id, keep_config=True)`, then a reinstall.
  `extensions/__init__.py:5889` re-registers each hook with
  `"optional": entry.get("optional", True)` and `"enabled": True`. Upstream
  `extensions/agent-context/extension.yml` says `optional: true`, so the
  repository's non-optional after hooks (`.specify/extensions.yml:108-115`,
  `134-141`) revert to optional prompts. Only a disabled state is restored
  (transaction lines after 551).
- The user config `agent-context-config.yml` is copied back after the update
  (`_command_update_transaction.py`, "Restore user config files" block), so
  `context_file` should survive. If it is lost, the extension self-seeds from
  `agent-context-defaults.json` (`codex` to `AGENTS.md`) and would write into
  the root `AGENTS.md`, which `docs/architecture.md` says is maintained by the
  user.

Condition: verify both after the upgrade (see C4).

### F5. Low: network use is small and only in the extension update path

Evidence:

- `integration upgrade`, `integration install`, `preset` registration and the
  shared-infra refresh do not import any HTTP code: a search of
  `integrations/_helpers.py`, `command_upgrade.py`, `base.py` and
  `shared_infra.py` for `urllib|open_url|requests|download|Catalog` finds only
  a docstring.
- `specify extension update` builds `ExtensionCatalog`
  (`extensions/__init__.py:4457-4460`, `4618-4635`) and fetches two catalogs
  from `raw.githubusercontent.com` (default: install allowed; community:
  discovery only). For a bundled extension with no `download_url` it installs
  the local packaged copy (`_command_update_discovery.py`, branch
  `ext_info.get("bundled") and not download_url`). If a live catalog entry
  ever gains a `download_url`, it would download an archive; the SHA-256 check
  is optional (`shared_infra.py:48-100`).
- `specify extension add agent-context --force` takes the bundled copy first
  (`extensions/command_add.py:147`) and makes no catalog call. Use it instead
  of `update` (C5). Do not pass `--dev`: it creates links to a cache folder
  (`link_commands=True`).
- No new hosts were added from `v1.0.12` to `v1.1.0`: the only URLs in the
  added lines are `github.com/github/spec-kit`, `api.github.com`, the GitHub
  MCP server page, a MiniMax repository link in a docstring and a
  `api.tenant.ghe.com` example.
- Credentials: `~/.specify/auth.json` does not exist on this machine
  (checked 2026-10-06). `GITHUB_TOKEN` or `GH_TOKEN` is attached only to
  `github.com`, `api.github.com`, `codeload.github.com` and similar GitHub
  hosts (`authentication/github_http.py:58-92`). The `v1.1.0` change adds
  GHE.com tenant support behind the `auth.json` trust list; unused here.
- Telemetry: a search of `src/` for telemetry, analytics, sentry and similar
  finds only comments about event handlers. None added.

### F6. Low: the bash scripts in `.specify/scripts` change; two behavior changes can affect callers

Diff `v1.0.1` to `v1.1.0` (`git diff v1.0.1 v1.1.0 -- scripts/bash`, 213 added
lines across four scripts):

- `setup-plan.sh` (lines 15-24): an unknown argument now exits with an error,
  and the JSON/text key `SPECS_DIR` is renamed `FEATURE_DIR`. The only
  consumer in this repository is the generated
  `plugins/code/skills/speckit-plan/SKILL.md:58`, which the same upgrade
  rewrites to `FEATURE_DIR`. No other file uses `SPECS_DIR` as a key
  (`grep`, 2026-10-06).
- `check-prerequisites.sh`: new `--require-spec` flag; the `analyze` and
  `converge` skills now pass it. Missing `spec.md` becomes a hard error.
- `common.sh`: new env override `SPECKIT_PYTHON_EXECUTABLE`, with
  `SPECKIT_PYTHON` kept as a deprecated fallback (`common.sh:409-411`; also
  `create-new-feature.sh:187`). The repository sets `SPECKIT_PYTHON` to
  `tools/spec-kit/.venv/bin/python` in `.claude/settings.json:3` and
  `.codex/config.toml:27`, so it still works. The override must also import
  PyYAML, which the venv python does. It now also drives preset resolution.
  The override is run as `"$override" -c '<fixed code>'`; it comes from the
  user's own environment, so this is no new trust boundary.
- `SPECIFY_FEATURE_NO_PERSIST=1` (`common.sh:172-177`,
  `create-new-feature.sh:464-465`) stops writes to `.specify/feature.json`.
  Opt-in; unset by default.
- `create-new-feature.sh`: Unicode-safe branch names. It probes locales with
  `sed` on every call and pipes the description to a fixed `python -c` script
  on stdin. The description is not interpolated into code. A non-ASCII name
  without a UTF-8 locale or Python 3 now errors out instead of being mangled.
- `resolve_template` wrapper loop is rewritten to stop an endless loop on a
  literal `{CORE_TEMPLATE}` (a bug fix). The `../` check on manifest file
  names now excludes a leading `../` only through `*../*` (pattern `../*` was
  redundant); no change in what is accepted.
- No new `curl`, `wget`, `eval`, or write outside `.specify/` and the repo's
  own `specs/`.
- Template text (`templates/commands/*.md`) changes are wording only. The
  notable one: a broken `extensions.yml` is now reported to the user instead
  of silently skipping hooks; the constitution Sync Impact Report is called
  scratch to remove before commit.

### F7. Low: the upgrade opens `.codex/config.toml`, but writes it only if it holds Spec Kit hook blocks

Evidence:

- Codex declares `events_config_file = ".codex/config.toml"`
  (`integrations/codex/__init__.py:44-45`). With no built-in codex events, no
  extension `events:` (none of the four declare any) and no
  `.specify/integration-events.yml`, the resolved set is empty, so
  `events/__init__.py:1385-1387` calls `_remove_native_event_hooks`
  (`events/__init__.py:1652`).
- `_remove_toml_entries` (`events/__init__.py:2227-2275`) rewrites the file
  only when its regex finds a `[[hooks.X]]` block with `speckit_marker = true`
  (`cleaned == existing` returns at line 2262). `.codex/config.toml` has
  `hooks = true` and no `[[hooks.` block (`grep`, 2026-10-06), so it stays
  untouched. `.specify/events.py` does not exist, so nothing is deleted.
- Same code in `v1.0.12`; the 1.0.1 install did not have it, so this is the
  first time this repository sees it.

### F8. Low: bookkeeping that must change with the adoption

- `licenses/third-party-notices.md:45-64` names revision `9118ed15...`
  (release 1.0.1) for the core skills and `.specify/` files, and `e77daa90...`
  (1.0.12) for the extensions. `AGENTS.md` ("Upstream adoption and
  attribution") says to update the notice in the same change. It must name
  `f1d3a4f8337ebbd3ae22760a9c12e3352b93a175` (1.1.0) and keep the local
  deviation list (pointer lines, `context_file`, hooks).
- `tools/spec-kit/uv.lock` pins `specify-cli` by tag and commit
  (`rev=v1.0.12#e77daa9...`). The tag `v1.1.0` is unsigned
  (`gh api repos/github/spec-kit/commits/v1.1.0`: `verified: false, reason:
  unsigned`; release made by `github-actions[bot]`, no assets). Check that the
  new lock entry shows commit `f1d3a4f8337ebbd3ae22760a9c12e3352b93a175`.
- `docs/architecture.md:~715` states the 1.0.12 pin and commit `e77daa9`; it
  needs the new values.

### F9. Info: new code-execution surface, not triggered by the upgrade

`v1.1.0` adds `specify workflow step add` from a local folder or archive
(`workflows/step/installer.py`, 852 new lines). Packages hold executable
Python (`installer.py:27`), run when a workflow that names the step runs. The
installer does not import or execute `__init__.py` at install time
(`installer.py:324`), rejects symlinks, and limits packages to 512 entries,
50 MiB and 32 levels (`installer.py:29-31`). The repository does not use
custom steps. Do not use this feature without a separate review.

### F10. Info: changes in code paths this repository does not use

New `mcode` integration, `generic` integration registration, GHE.com release
download support, bundle pin checks, copilot/shai/vibe fixes, workflow
expression fixes, community-catalog entries, and a new `agentic-sdlc` guide.
The repository installs only `codex`, script type `sh`. No effect expected.
The workflow runtime did not change in how it starts processes
(`workflows/step/shell`, `prompt` unchanged except error text).

### F11. Info: `taskstoissues` move to a bundled GitHub extension

- Commit `987c9b8` (2026-09-29, in 1.0.13, so part of 1.1.0): adds
  `extensions/github` (version 1.0.1, MIT, command `speckit.github.taskstoissues`,
  requires `git` and the GitHub MCP server). Its commit message says this is
  "stage 1 ... opt-in"; stage 2 (deprecate) and 3 (remove) are still ahead.
- The core command stays in 1.1.0: `templates/commands/taskstoissues.md` exists
  and is changed only by the hook-error wording. `extensions/github/README.md`
  says `specify init` does not install the extension.
- `integration upgrade` and `extension update` act only on installed
  extensions; the `github` extension is not installed by them, and the
  extension's script `resolve-tasks.sh` only runs if you install it and call
  its command. It would write `.specify/feature.json` (gitignored), reads the
  `origin` remote, and uses the GitHub MCP tools.
- This repository uses Linear (`AGENTS.md` "Records"), so no action beyond what
  T028 already says: record the move, change nothing. Watch for stage 3: once
  upstream removes the core command, `integration upgrade` would stale-delete
  `speckit-taskstoissues`.

### F12. Info: licenses

- Spec Kit: MIT, "Copyright GitHub, Inc.". `LICENSE` is unchanged from
  `v1.0.1` to `v1.1.0` (`git diff --stat` empty), and `licenses/github-spec-kit.txt`
  is identical to the `v1.1.0` `LICENSE` (`diff` on 2026-10-06).
- New `github` extension: MIT (`extensions/github/extension.yml:10`), covered
  by the same notice.
- No dependency was added or changed: `pyproject.toml` `dependencies` is the
  same list in `v1.0.12` and `v1.1.0` (typer, click, rich, readchar, pyyaml,
  packaging, pathspec, json5). The only `pyproject.toml` changes are the
  version and one `force-include` line for `extensions/github`. The lock file
  needs only the `specify-cli` entry rewritten.

### F13. Info: advisories and provenance

On 2026-10-06 (UTC): `gh api repos/github/spec-kit/security-advisories` returned
`[]` (also with `state=published`); GraphQL `securityVulnerabilities` for pip
package `specify-cli` returned no nodes; `vulnerabilityAlerts` count was 0
(that field may need repository access, so treat it as weak evidence). There is
no `specify-cli` advisory in `/advisories`. Upstream `SECURITY.md` points to
`opensource-security@github.com`. Release `v1.1.0` (2026-10-02T18:02:50Z):
not draft, not prerelease. The tag commit is unsigned. I did not audit the
third-party packages already in the lock; they do not change.

### F14. Info: what the commands write (complete list, from code)

`specify integration upgrade codex --script sh` writes:

- `.specify/scripts/bash/*.sh`, `.specify/templates/*.md`, `.specify/.gitignore`
  (`shared_infra.py`, install with `refresh_managed`; `--force` overwrites
  regular files; symlinks and files under a symlinked parent are never
  overwritten).
- `.specify/integrations/{codex,speckit}.manifest.json` (temp file plus
  `os.replace`, `manifest.py` `save`), `.specify/integration.json`,
  `.specify/init-options.json`.
- `.agents/skills/speckit-*/SKILL.md` for the ten core commands, through the
  links (`base.py:640`), then the extension and preset re-registration (F3).
- `chmod +x` on `.sh` files under `.specify/scripts` and `.specify/extensions`
  only (`__init__.py:213-250`).
- Reads (no write expected) `.codex/config.toml` (F7).
- Does not replace or remove the `.agents/skills` link entries themselves
  (`unlink` hits files; `rmdir` on a link raises and is ignored;
  `_ensure_safe_*` checks refuse to follow links for shared infra, not for
  skills). Does not touch `AGENTS.md`, `.claude/`, `plugins/`, `skills/`
  content other than the `SKILL.md` files above. No process is started and no
  network call is made.

`specify extension add agent-context --force` (or `update`) writes
`.specify/extensions/agent-context/*`, `.specify/extensions/.registry`,
`.specify/extensions.yml` (hooks reset, F4), the skill `SKILL.md` through its
link, and temporary `.specify/extensions/.backup/...` (removed on success).
`update` also writes `.specify/extensions/.cache/` (catalog).
`specify preset` re-registration writes only `.specify/presets/` state plus
skills for presets that override commands; `linear-issue` is a template-only
preset.

## What I could not verify

I did not run `specify`, `uv` or any installer (rule). F1, F3 and F4 come from
reading the code and one stdlib demo, not from a run. The cheapest proof is a
throwaway run in a scratch copy (C1).

Jev tools were not used, so no privacy-gate refusal occurred.

## Conditions for adoption

1. **F1 (required).** Do not run `integration upgrade` against linked skill
   folders as T028 says. Either run it first in a scratch copy of the
   repository where the ten core `speckit-*` skill folders are real
   directories (so manifest keys stay `.agents/skills/...`), then copy the ten
   `SKILL.md` files into `skills/code/` and restore the links; or prove
   otherwise with a scratch run. After any run, `git status` must show no
   deleted `SKILL.md`. Change T028's acceptance text: writes go through the
   links, but the old manifest keys do not match.
2. **F2.** Apply T026's preset before the upgrade, or re-add the pointer to
   all 20 skills afterwards; check with the skills link test. Expect
   `--force`; re-add the `.cache/` rule in `.specify/.gitignore` after the
   forced refresh (or confirm the preset/commit flow keeps it).
3. **F3.** After the run, delete any new real directories
   `.agents/skills/speckit-git-{feature,commit,initialize,remote}` (they are
   not packaged by decision), and confirm every entry in `.agents/skills` is
   still a link.
4. **F4.** After the extension step, check that
   `.specify/extensions/agent-context/agent-context-config.yml` still says
   `context_file: ".claude/rules/current-plan.md"`, that root `AGENTS.md` is
   unchanged, and restore `optional: false` on the two agent-context hooks in
   `.specify/extensions.yml`. That is a small hand edit with no Spec Kit
   command behind it; the orchestrator should accept it explicitly against
   U-2026-10-06l ("not hand edits").
5. **F5.** Use `specify extension add agent-context --force` (bundled copy, no
   network, no `--dev`) rather than `extension update`. Always pass
   `--script sh`. Do not run `specify self upgrade` or `specify check`.
6. **F8.** Update `licenses/third-party-notices.md` and `docs/architecture.md`
   to 1.1.0 in the same change; confirm the new `uv.lock` entry names commit
   `f1d3a4f8337ebbd3ae22760a9c12e3352b93a175` and that nothing else in the
   lock changes.
7. Re-run the repository checks that read `.specify/` output (`npm run verify`)
   and compare the installed files against `v1.1.0` (hash check as in this
   review) before finishing S2c.
