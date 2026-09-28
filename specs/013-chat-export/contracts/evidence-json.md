# Contract: JSON evidence conversion

Applies to `wiki-consistency convert` (and the commands that convert on the
way, such as `prepare`) for a cited revision whose payload is a JSON file, a
JSON Lines file, or a ZIP whose members include them.

- A `.json` payload or member that parses is written back as JSON with every
  character itself, never as a `\uXXXX` escape. Keys, values and their order
  are kept.
- A `.jsonl` payload or member is handled line by line the same way; blank
  lines stay blank.
- Content that does not parse is returned as MarkItDown's plain text
  converter returns it; the conversion does not fail because of it.
- Other formats convert exactly as before.
- The evidence cache path's converter version changes, so conversions made
  before this change are not reused. Other commands' output and exit codes do
  not change.
