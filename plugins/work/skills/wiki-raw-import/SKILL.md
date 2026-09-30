---
name: wiki-raw-import
description: Copy original documents the user confirms into a verbose-broccoli Wiki instance's raw/ layer, one BagIt revision per file with its source recorded, and check raw/ integrity. Use when the user wants to admit documents as raw evidence, including ChatGPT exports and local Claude Code or Codex sessions, re-import changed originals, or verify raw/; not for writing Wiki pages.
---

# Wiki Raw Import

Admit the user's original documents into a Wiki instance's `raw/` by copying
them. The originals stay where they are and are only read. Each copy becomes a
read-only BagIt bag that records the original path, the original's
modification time, the admission time and the SHA-256 digest. The instance's
`AGENTS.md`, copied from [assets/AGENTS.md](assets/AGENTS.md), describes the
layout.

`CONFIG`, `DATA`, `STATE` and `CACHE` below are the `verbose-broccoli` folders
under the XDG configuration, data, state and cache roots (by default
`~/.config`, `~/.local/share`, `~/.local/state` and `~/.cache`). Each Wiki
instance, called a vault, is `DATA/vaults/<vault>/`. The user keeps four:
`work` for education work, the default here; `default` for knowledge that
belongs to no single plugin; `chat` for exported conversations; and `code`
for coding knowledge from any project.

Run the script from this skill's folder:

```sh
uv run --locked --script scripts/raw_import.py init
uv run --locked --script scripts/raw_import.py admit --selection <file>
uv run --locked --script scripts/raw_import.py verify
```

Add `--wiki <vault>` for a vault other than `work`; use the vault the user
names, and ask when it is unclear. Exit 0 means every
item succeeded, 1 means at least one item was refused or failed (or `verify`
found an invalid revision), and 2 means an error stopped the command. For an
invalid argument, selection or configuration, a missing instance or a held
lock, nothing was written.

## Procedure

1. **Survey a location read-only.** Report its size, file count and file
   types from `du` and file listings. Do not open files, and do not enter a
   folder that is excluded or holds operational or private data (for example
   student records). Say which files look like originals and which look like
   the user's edits, conversions, tool output or program data.
2. **Ask for a decision.** Present the location with its size, counts and your
   first judgment. The user decides whether it is admitted, left out or
   excluded. Record the decision where the current task keeps its records,
   with the location, the first judgment and the decision only.
3. **Write exclusions.** Put the locations the user excludes in
   `CONFIG/config.toml`:

   ```toml
   [wiki.raw_import]
   exclude = ["/absolute/path"]
   ```

   `admit` refuses every file under an excluded path and under `DATA`,
   `STATE` and `CACHE`.
4. **Build the file list.** For an admitted location, list the exact regular
   files to copy, with each file's raw kind: `files` (default), `notes` (the
   user's own text notes), `assets` (images and other media) or `web`
   (captured web pages). Exported conversations, admitted only into the
   `chat` and `work` vaults, and exported Claude Code and Codex sessions,
   admitted into any vault, are `files`. Expand folders into files. Point
   out files whose names or locations suggest operational or private data.
   Show the list and its total size to the user and wait for approval.
5. **Write the selection.** Write the approved list as JSON Lines to
   `STATE/vaults/<vault>/selections/<name>.jsonl`, one
   `{"path": "/absolute/path", "kind": "files"}` per line.
6. **Import.** Run `init` (it changes nothing that exists), then `admit
   --selection <file>`. Keep the JSON Lines report outside every repository.
   Resolve or report each `refused` and `failed` item with its reason. A
   rerun of the same selection skips finished items and adds a revision only
   for originals that changed. A file whose name contains the literal text
   `%0A` or `%0D` always fails, because bagit decodes those sequences in
   manifest names; nothing is published for it. Report it to the user.
7. **Check.** Run `verify`. If it reports an invalid revision, stop and tell
   the user; do not edit or delete anything in `raw/`.
8. **Log and commit.** Append one entry to the instance's `wiki/log.md`:

   ```markdown
   ## [YYYY-MM-DD] raw-import | <location>

   admitted N, already admitted N, refused N, failed N
   ```

   Commit it in the instance's own Git repository (`raw/` is ignored there).
9. **Clean up.** Remove the selection file after `verify` passes.

## ChatGPT exports

The user's ChatGPT conversations reach the vaults through OpenAI's account
data export. An export holds the whole account; conversations cannot be
picked. Each export is admitted unchanged into the `chat` vault and then into
the `work` vault, whose pages about students can cite it.

1. **The user requests it.** In ChatGPT on the web: **Settings > Data
   controls > Export data > Export**, then **Confirm export**. This and every
   other account step are the user's; never do them. A new request waits
   until the previous one has finished.
2. **The user saves it.** A download link arrives by email or SMS within up
   to 7 days. It expires 24 hours after it arrives and works only while
   signed in to the same account. The user saves the ZIP over
   `~/Documents/chatgpt/chatgpt-export.zip`. Every export goes to this one
   file: the raw import knows a source by its path, so a changed file there
   becomes a new revision of the same source, while a file saved anywhere
   else would start a new source.
3. **Wait for go.** Admit an export only when the user asks.
4. **Check the file.** Run
   `python3 -m zipfile -t ~/Documents/chatgpt/chatgpt-export.zip`. If it does
   not exit 0 after printing `Done testing`, stop: the download is partial or
   damaged, and the user downloads it again or requests a new export.
5. **Admit it into both vaults.** The selection is the one line
   `{"path": "<absolute path of the file>", "kind": "files"}`. Follow steps 5
   to 9 of the procedure above for the `chat` vault, then for the `work`
   vault (`--wiki chat`, then `--wiki work`), so each vault gets its own
   selection, log entry and commit. An unchanged export is reported as
   `already_admitted`.

## Claude Code and Codex sessions

To offer the local Claude Code and Codex sessions to the vaults, follow
[references/session-selection.md](references/session-selection.md). It
renders, filters, scans and classifies them and ends with the lists the user
approves, which then go through steps 5 to 9 above, one selection per vault.

## Boundaries

- Copy only files the user approved in a selection. Never move, change or
  delete an original, and never edit or delete a revision in `raw/`.
- Keep file names, file contents and private paths out of code repositories,
  commits and Orca or Linear messages. Records there give locations,
  decisions and counts only.
- Exported conversations are raw evidence only in the `chat` and `work`
  vaults, exported Claude Code and Codex sessions in any vault they belong
  to, and other conversation records in none. Program-owned data (for example a sync client's journals or a
  reference manager's database) is not raw evidence. Copy an item from a
  program-owned folder only when the user selects it.
