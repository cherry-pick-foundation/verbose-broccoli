# Implementation Plan: Raw derivatives

**Branch**: `feature/raw-derivatives` | **Date**: 2026-09-30 |
**Spec**: [spec.md](spec.md) | **Linear issue**: CHE-59

## Summary

Remove the 43 checked derivative bags from the work vault's raw layer by
hand, repoint or drop the page citations and links that reach them, log the
removal, and add a short judgment rule to the raw-import skill, the vault
schema template and the four vault schemas. No code changes.

## Technical Context

- **Repository files**: `plugins/work/skills/wiki-raw-import/SKILL.md` (steps
  1 and 4) and `plugins/work/skills/wiki-raw-import/assets/AGENTS.md` ("Raw
  evidence").
- **Vault files** (each vault is its own Git repository under
  `~/.local/share/verbose-broccoli/vaults/`): `AGENTS.md` of `default`,
  `chat`, `code` and `work`; in `work` also `wiki/sources/local-materials.md`,
  the student pages that cite removed bags, and `wiki/log.md`. `raw/` is
  outside Git.
- **Checks**: `raw_import.py verify --wiki work`, `wiki-consistency check
  --wiki work`, `npm run verify`.

## Constitution Check

- Principle VI (Wiki storage): raw is create-only. The user approved this
  removal on 2026-09-30 as a one-time exception, recorded in the vault's
  `wiki/log.md` and in [removals.md](removals.md).
- Reuse before implementing: the rule is text in existing documents; no new
  code, no classifier, no delete command.

## Approach

1. A read-only worker checks [removals.md](removals.md) against the issue's
   categories before anything is deleted.
2. The implementing worker traces each removed file to the original it came
   from among the remaining bags. It rewrites the citations and links in
   `local-materials.md` and the student pages, or drops them where raw holds
   no original. It also drops the links to the trashed worksheet folders.
3. It removes the 43 bag folders (`chmod -R u+w`, then `rm -r`) and runs
   `verify`.
4. It runs `update` and `check`, and appends one log entry.
5. It adds the rule to the skill, the template and the four vault schemas.
6. The orchestrator reviews each diff and commits the repository and each
   vault's own repository.

## Coordination

The concept-profile feature (CHE-57) edits the same vault. It committed its
schema and catalog as vault commit `d0c8830`, and warns before its next
vault commit, so the two features never commit `wiki/log.md` edits at the
same time.
