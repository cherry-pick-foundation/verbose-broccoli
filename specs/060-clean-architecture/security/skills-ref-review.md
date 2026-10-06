> **PARTIAL: paused by the coordinator (message sent 2026-10-06 11:29:39Z) before the final re-check.**
> Done: all five packages downloaded and hash-checked; full source read; closure, license, maintenance, advisory and offline checks; validator rules; fit count over the 48 repository `SKILL.md` files; this write-up with a verdict.
> Left: a second read-through of the findings against the evidence, and the runtime test under Python 3.14 (F6), which this review's rules forbid anyway. The verdict below stands on what was read.

# Dependency security review: skills-ref 0.1.1 (clean-architecture feature)

Date: 2026-10-06. Independent, read-only review. Nothing was installed, imported, built or run from these packages.
Write-up folder: `~/.local/state/verbose-broccoli/workspaces/feature-clean-architecture/security/skills-ref/ctx_2f6d86f86832/`. `EV` means its `evidence/` folder.
No Jev tool was tried, so there is no privacy-gate refusal to record. No student data was opened.

## How I reviewed

- Downloaded from PyPI by `curl`: the wheel and the sdist (source archive) of each of the five packages in the closure. Every file matches the SHA-256 that PyPI lists (`EV/artifact-sha256.txt`). The wheel hashes for `skills-ref` and `strictyaml` also match what `uv pip compile --generate-hashes` printed (`EV/uv-resolve-python314.txt`).
- Resolved the closure with `uv pip compile --no-build --universal --python-version 3.14` (the repository's Python). It only resolves; it installs nothing. Scratch copies are in `/tmp/skills-ref-review/` (`dl/` downloads, `x/` unpacked wheels, `x/sdist/` the skills-ref sdist).
- Read the full `skills_ref` source (856 lines with metadata). Searched the four dependencies with `grep` for network, process, file-write, environment and dynamic-code use, then read each hit.
- Checked every wheel's `RECORD` against the unpacked files: all hashes match and there are no unlisted files (`strictyaml` 45 files, `click` 21, `dateutil` 24, `skills_ref` 11, `six` 5).
- Public data: PyPI JSON and the PyPI provenance endpoint, the GitHub REST API (read only), OSV (`api.osv.dev`) and the GitHub Advisory Database.
- Limits. Static review only; I did not run the validator, so runtime behaviour on Python 3.14 is unverified (F6). "No advisory" means none on 2026-10-06. The PyPI project owner list is not in the JSON, so I could not check for owner changes.

## Dependency closure (what `uv` resolves today)

| Package | Version | Released | License (shipped) | Wheel only? |
| --- | --- | --- | --- | --- |
| `skills-ref` | 0.1.1 | 2026-01-10 | Apache-2.0 (`skills_ref-0.1.1.dist-info/licenses/LICENSE`) | Yes, pure Python |
| `click` | 8.5.0 (newest) | 2026-08-26 | BSD-3-Clause (`licenses/LICENSE.txt`) | Yes |
| `strictyaml` | 1.7.3 (newest) | 2023-03-10 | MIT (`LICENSE.txt`, "Colm O'Connor") | Yes |
| `python-dateutil` | 2.9.0.post0 (via strictyaml) | 2024-03-01 | Dual: Apache-2.0 or BSD-3-Clause (`LICENSE`; code before 2017-12-01 BSD only) | Yes |
| `six` | 1.17.0 (via dateutil) | 2024-12-04 | MIT (`LICENSE`) | Yes |

`click` 8.5.0 declares no dependencies (`click-8.5.0.dist-info/METADATA` has no `Requires-Dist`). The closure is five pure-Python packages. There is no `.so` or `.pyd` file and no `.pth` file in any wheel (`find` on the unpacked trees).

## 1. Verdict

**Adopt with conditions.** The code is small, reads only the `SKILL.md` it is given, and does no network, process or write work on the `validate` path. The conditions are about fit and provenance, not hidden behaviour. The most important one: the installed command is `agentskills`, not `skills-ref` (F1).

## 2. Findings

Severity scale: High (blocks), Medium (needs a condition), Low, Info. No finding blocks adoption.

| ID | Severity | Blocks? | Finding and evidence | Required condition |
| --- | --- | --- | --- | --- |
| F1 | Medium | No (plan fix) | The 0.1.1 package installs one command, `agentskills`, not `skills-ref`. Evidence: `skills_ref-0.1.1.dist-info/entry_points.txt:2` (`agentskills = skills_ref.cli:main`); sdist `pyproject.toml` `[project.scripts]`; the shipped README runs `agentskills validate path/to/skill`. Upstream `main` instead declares `skills-ref = ...` (`agentskills/agentskills` `skills-ref/pyproject.toml:17`, read 2026-10-06). The plan's commands (`specs/060-clean-architecture/plan.md:101`, `quickstart.md:31`: `uv run … skills-ref validate "$skill"`) would fail with "program not found". | Use `agentskills validate <skill-dir>` (or `python -m skills_ref.cli`, since `cli.py:124-125` has a `__main__` guard) in T013, the quickstart and the plan. Test that the verify task fails on a bad skill. |
| F2 | Medium | No | Upstream says the library is a demonstration, not for production. `skills-ref/README.md` on `main`: "This library is intended for demonstration purposes only. It is not meant to be used in production." (added 2026-02-15, commit 492e1b71; read 2026-10-06). The 0.1.1 README (Jan 2026) does not carry the notice (grep of sdist `README.md` and wheel `METADATA`: no hit). PyPI classifier is "Development Status :: 3 - Alpha". | Treat it as a development-time linter only. Never import it in shipped tools. Keep the repository's own link test for what it cannot check (plan.md:101-104). |
| F3 | Medium | No | Provenance is weak. (a) The declared repository `anthropics/agentskills` returns 404 on the GitHub API and web (2026-10-06); the project is now `agentskills/agentskills` (25,935 stars, Apache-2.0, last push 2026-08-09). PyPI metadata still points to the old URL (`EV/pypi-json/skills-ref-0.1.1.json`, `project_urls`). (b) No tag or release exists (`gh api …/tags`, `…/releases` returned nothing). (c) The 0.1.1 sdist has a different layout from `main` (root `pyproject.toml` plus `docs/`, `CLAUDE.md`; `main` keeps it under `skills-ref/` at version 0.1.0). The seven source files equal `main` after ignoring CRLF, except the version string and two `read_text(encoding='utf-8')` fixes (`parser.py:89`, `validator.py:172`). (d) No PyPI attestation (`/integrity/skills-ref/0.1.1/…/provenance` returned 404). (e) `main` has only 4 commits touching `skills-ref/` since 2025-12-18 (last 2026-08-03). | Pin the exact wheel hash in `tools/skills-ref/uv.lock` (`d35db5bb8de71ae301daf5ca9cb71f8a555e8c6f83a6d40e46a5bc09f8f461b5`). Record in the plan that the upstream URL moved. Do not bump without re-reading the diff. |
| F4 | Low | No | The validator is narrower than the plan's summary and stricter in one place. Checks: required `name` and `description`; `name` ≤ 64 after NFKC, lowercase, no leading, trailing or double hyphen, only letters, digits and `-` where "letters" means any Unicode alphanumeric (`validator.py:37-58`), and equal to the folder name (`:60-65`); `description` non-empty and ≤ 1,024 characters (`:70-84`); `compatibility` ≤ 500 (`:87-101`); any frontmatter key outside `name, description, license, allowed-tools, metadata, compatibility` is an error (`:15-22,104-115`). Not checked: the 500-line body limit, file references, `license`, `allowed-tools` and `metadata` types, empty `compatibility`. The frontmatter is cut at the first `---` anywhere (`parser.py:45`), so a value containing `---` truncates it. Fit with this repository (static count over 48 `SKILL.md` files): 47 use only allowed keys; `plugins/code/skills/ponytail/SKILL.md:16` has `argument-hint`, which would fail. No flow-style YAML found. | Decide before T013 how ponytail's `argument-hint` is handled (the copy is upstream; do not patch the validator). Do not claim that `validate` enforces the 500-line rule. |
| F5 | Low | No | `strictyaml` is barely maintained and vendors an old YAML parser. Last release 2023-03-10; repository last push 2025-05-23; 105 open issues (`EV/github/crdoconnor_strictyaml.json`). It bundles `ruamel.yaml` 0.16.13 as `strictyaml/ruamel/` (`strictyaml/ruamel/__init__.py:10-11`). That bundle contains the unsafe `Constructor` with `__import__` of tagged Python names (`ruamel/constructor.py:829-925`). It is not reachable: strictyaml loads with `RoundTripConstructor` (`parser.py:35`, `ruamel/constructor.py:1132`, a `SafeConstructor` subclass), and its scanner raises on every tag, anchor and flow token (`parser.py:193-217`). Only the repository's own `SKILL.md` files are parsed. No advisory exists (F11). | None beyond the pin. Do not point the validator at untrusted skill files without re-reading F5. |
| F6 | Low | No | Python 3.14 support is untested. `skills-ref` declares `>=3.11` with classifiers to 3.13 (`METADATA`); the repository requires 3.14. `grep` found no use of removed standard-library APIs (`collections.Mapping`, `imp`, `distutils`, `ast.Num`, `getargspec`, `utcnow`) in any of the five packages. I did not run it. | In T013, run `agentskills validate` once on one good and one bad skill under Python 3.14 and keep the result. |
| F7 | Info | No | Process and environment access exists only in `click` code that `skills-ref` does not call. `click` reads `_AGENTSKILLS_COMPLETE`; if set it enters shell completion (`click/core.py:1617-1622`), which runs `bash --norc -c 'echo "${BASH_VERSION}"'` (`shell_completion.py:395-410`). The pager, editor and launcher helpers (`_termui_impl.py:469,586,660,729,819-856`) are called only by `click.echo_via_pager`, `edit` and `launch`, which `skills_ref` never calls (it uses `click.echo` only: `cli.py:65-70,90,118`). `click.edit()` had an OS-command-injection advisory fixed in 8.3.3 (F11); 8.5.0 is later. | Do not export `_AGENTSKILLS_COMPLETE` in the verification environment. |
| F8 | Info | No | No install-time or import-time side effects. All five packages ship as wheels, so nothing runs at install (no `setup.py`, no build backend run). No `.pth`, no native code, one console script (`agentskills`). Import-time work is limited to constants and object creation: `dateutil` builds `UTC = tzutc()` and `gettz` without file access (`dateutil/tz/tz.py:129,1679`); it also loads submodules lazily (`dateutil/__init__.py:11-21`); `strictyaml` imports `dateutil.parser` (`scalar.py:9`) but calls it only for date validators (`:273,282`). `dateutil`'s bundled zone data is read only by `dateutil.zoneinfo` (`zoneinfo/__init__.py:13-33`). | Set uv `no-build = true` for the project so a missing wheel can never fall back to an sdist build. |
| F9 | Info | No | Network, process, file-write and environment access of the `validate` path: none for network, process and writes; the only I/O is `Path.exists()`, `is_dir()` and `read_text(encoding='utf-8')` on `SKILL.md` (`validator.py:161-172`, `parser.py:25,89`). `skills_ref` reads no environment variable. `to-prompt` also calls `Path.resolve()` (`prompt.py:38`) and prints the absolute path. Symlinked skill folders are followed by `exists()` and `read_text` (relevant to `.agents/skills` links; read only). | None. |
| F10 | Info | No | Licenses are permissive: Apache-2.0, BSD-3-Clause, MIT, and dateutil's Apache-2.0/BSD-3-Clause dual license. `strictyaml`'s wheel ships only its own MIT text; the bundled `ruamel.yaml` MIT notice is not in the wheel (`strictyaml-1.7.3.dist-info/` has `LICENSE.txt` only). Per `AGENTS.md`, installed dependencies need no `licenses/third-party-notices.md` entry, and nothing is copied into the repository. | None. Do not copy any of this code into the repository. |
| F11 | Info | No | Advisories on 2026-10-06: none for the five exact versions (OSV, GitHub Advisory Database, PyPI `vulnerabilities` field; `EV/advisories/`). Positive controls work: OSV returns 1 hit for `click` 7.0 and 4 for `pyyaml` 5.3; the GitHub query returns 4 for `pyyaml`. One advisory exists for older `click`: CVE-2026-7246 / GHSA-47fr-3ffg-hgmw (`click.edit()` command injection, affects up to 8.3.2, fixed 8.3.3; `EV/advisories/osvall-click.json`). `skills-ref`, `strictyaml`, `dateutil` and `six` have no advisory in any version. | Re-run at implementation time. Pin `click>=8.3.3` if the lock ever falls back. |
| F12 | Info | No | Maintenance signals. `click` is very active (push 2026-10-04, monthly releases: 8.4.0 2026-05-17, 8.5.0 2026-08-26; Pallets). `python-dateutil` push 2026-09-26, last release 2024-03-01. `six` push 2026-02-23, last release 2024-12-04, in maintenance mode. `skills-ref`: two releases on one day (0.1.0 and 0.1.1, 2026-01-10), none since. `click` 8.5.0 is 41 days old. Name and owner check: `skills-ref` lists as its author the person who wrote the first commit in the upstream repository (547831f3, 2025-12-18); no typosquat sign. | Accept. |
| F13 | Info | No | Offline use. The validator needs no network. Installing needs PyPI once. `uv run --frozen --offline --no-sync` works only if the environment already exists, so something must run `uv sync --project tools/skills-ref --frozen` first (with network or a warm uv cache). I could not test this without installing. | Make the first-time sync a documented setup step (mise setup) and let `verify` fail with a clear message if the environment is missing. |

## 3. What the validator checks (specification fit)

The upstream specification (sdist `docs/specification.mdx`) says: `name` is required, 1-64 characters, lowercase letters, digits and hyphens only, no leading or trailing hyphen, no `--`, equal to the parent folder name; `description` is required, 1-1,024 characters; optional `license`, `compatibility` (≤ 500), `metadata` (string map) and experimental `allowed-tools` (space-delimited string). The validator implements the name, description and compatibility limits and the folder match as listed in F4. The spec says "unicode lowercase alphanumeric" and then "`a-z`"; the code accepts any Unicode letter or digit. Both readings accept every name in this repository's skills (all names I read are ASCII lowercase with hyphens). The Unicode difference only matters if a name with a non-ASCII letter is ever added.

## 4. Answers to the focus questions

- **Network:** none in `skills_ref`, `strictyaml`, `dateutil` or `six`; `click` has no socket or HTTP import (`grep` of all five packages for `socket|urllib|http|requests|urlopen` found only `urllib.parse` in `strictyaml/scalar.py:13`, `urllib.parse` in `click/_termui_impl.py:803`, and `six`'s Python 2 name map `six.py:408`).
- **Process:** none on the `validate` path. Optional in `click` only (F7). `dateutil/zoneinfo/rebuild.py` uses `subprocess` to rebuild zone data and is not imported by anything.
- **File writes:** none in `skills_ref`. `click` writes only through editor, pager and temp-file helpers that are not called (F7).
- **Environment:** `skills_ref` none. `click` reads `PAGER`, `LESS`, `TERM`, editor variables and `_AGENTSKILLS_COMPLETE` (F7).
- **Import or install time:** nothing (F8).
- **Works offline:** yes at run time; first install needs the network (F13).
- **Licenses:** F10 and the closure table.
- **Maintenance:** F3, F5, F12.
- **Advisories:** none for the pinned versions (F11).

## 5. Open questions for the feature owner

1. How to treat `plugins/code/skills/ponytail/SKILL.md:16` (`argument-hint`): drop the key from the copy, exclude that skill, or accept a failing check? Not my call; it changes an upstream skill.
2. Should the plan keep citing the repository `anthropics/agentskills`? It no longer resolves; `agentskills/agentskills` does.

## Final verdict: adopt with conditions

Findings by severity: High 0, Medium 3 (F1, F2, F3), Low 3 (F4, F5, F6), Info 7 (F7-F13). None blocks adoption.

Conditions:

1. Call the command `agentskills validate`, not `skills-ref validate`, in T013, `plan.md:101` and `quickstart.md:31` (F1).
2. Pin `skills-ref` 0.1.1, `click` 8.5.0, `strictyaml` 1.7.3, `python-dateutil` 2.9.0.post0 and `six` 1.17.0 by hash in `tools/skills-ref/uv.lock`, with uv `no-build = true`; do not bump without a new review (F3, F8).
3. Use it only as a development-time check, never imported by shipped code; keep the repository's own link test (F2, F4).
4. Resolve the `argument-hint` case in ponytail before the check goes into `verify` (F4).
5. Run one passing and one failing skill under Python 3.14 in T013 and keep the output (F6).
6. Document the one-time `uv sync` and keep `_AGENTSKILLS_COMPLETE` unset in verification (F7, F13).
