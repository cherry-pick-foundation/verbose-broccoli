# Research: ChatGPT Export into the Chat Vault

All sources were read on 2026-09-29. The user's answers are in
[spec.md](spec.md#clarifications).

## R1. How conversations leave ChatGPT on the web

- **Decision**: OpenAI's account data export in ChatGPT's settings
  (**Settings > Data controls > Export data > Export > Confirm export**). The
  user performs every account step.
- **Rationale**: It is the only documented way to get the conversations out of
  a Plus or Pro account as files. OpenAI's help center ("Exporting your
  ChatGPT history and data") gives the steps, the delivery by email or SMS
  within up to 7 days, the 24-hour link and the ZIP contents; "Transfer
  exported conversations between ChatGPT accounts" adds that larger exports
  may hold numbered conversation JSON files instead of `conversations.json`.
  Both pages were read in Orca's browser because the help center refuses
  plain HTTP clients.
- **Alternatives considered**: the Privacy Portal (same data through a
  privacy request); third-party browser extensions that save chosen
  conversations (unofficial, read ChatGPT's internal interface, need an
  install); shared links (publish each conversation). The user chose the
  settings export.

## R2. How a re-export becomes a new revision

- **Decision**: The user keeps one fixed file,
  `~/Documents/chatgpt/chatgpt-export.zip`, and saves each new export over it.
  Admitting it again with the same selection adds a revision of the same
  source. The raw import does not change.
- **Rationale**: The raw import finds a source's latest revision by the
  original's resolved absolute path, stored as `Internal-Sender-Identifier`
  (`plugins/work/skills/wiki-raw-import/scripts/raw_import.py`,
  `latest_revision` and `admit_item`). A different digest at the same path
  becomes a new revision under the same source ID; an equal digest is
  `already_admitted`. The existing test "raw import US2: unchanged rerun adds
  nothing; changes and reversions retain every revision"
  (`scripts/wiki_raw_import_test.ts`) covers this for a text file. OpenAI does
  not document the ZIP's name, so downloads cannot be relied on to keep one
  path. A symbolic link to the newest download would be refused
  (`refusal`: "symbolic links are not admitted").
- **Alternatives considered**: each download as its own source (pages would
  have to work out which export is newest); a raw import option that names the
  source (new code). The user chose the fixed file.

## R3. Reading an export as evidence

- **Decision**: The Wiki consistency tool registers one JSON converter on its
  MarkItDown instance through MarkItDown's `register_converter` extension
  point. It parses `.json` and `.jsonl` content and writes it back with
  characters instead of escape sequences. Content that does not parse is
  returned as the plain text converter would return it. The evidence cache
  key gains a local converter revision so an earlier conversion of a JSON
  source is not reused.
- **Rationale**: MarkItDown 0.1.8, which the tool pins
  (`packages/wiki-consistency/pyproject.toml`), already converts a ZIP: its
  `ZipConverter` passes each member back through the same MarkItDown
  instance (`markitdown/converters/_zip_converter.py`), and `.json` members go
  to `PlainTextConverter`, which decodes the bytes as they are. Measured with
  synthetic exports: a `conversations.json` written with direct Korean
  characters converts to text containing them; the same data written with
  `\uXXXX` escapes converts to the escapes, so no Korean phrase matches.
  `chat.html` converts to no text, because its conversations sit in a script.
  OpenAI does not document which JSON form the export uses, and either is
  valid JSON. A registered converter also applies to ZIP members, so one
  converter covers direct JSON payloads and exports.
- **Alternatives considered**: upstream ChatGPT export converters that write
  one Markdown file per conversation (a second conversion path and a new
  dependency for one source type, while the evidence only needs readable
  text); a search found no MarkItDown plugin that unescapes JSON; decoding
  escape sequences in all converted text (would change backslashes in other
  documents).

## R4. Checking a download before admission

- **Decision**: The procedure runs `python3 -m zipfile -t <file>` on the
  fixed file and admits it only if the test passes.
- **Rationale**: Python's standard `zipfile` command reads every member and
  checks its CRC; a partial or damaged download fails. It needs no new tool.
- **Alternatives considered**: `unzip -tq` (Info-ZIP, not checked by
  `deno task doctor`); no check (a partial download would become raw
  evidence that can never be removed).

## R5. Where the rule on exported conversations lives

- **Decision**: Constitution VI allows exported conversations as Raw evidence
  in the `chat` and `work` vaults. The commit is `feat(constitution)`, which
  raises the version from 2.0.0 to 2.1.0. The same rule is updated in
  `plugins/work/skills/wiki-raw-import/SKILL.md`, its schema template
  `assets/AGENTS.md`, and `docs/architecture.md`.
- **Rationale**: These are the repository files that state the rule today
  (a search for "exported" and "conversation records" outside earlier
  features' records). The change widens what a principle allows without
  breaking any existing use, so it is a `feat` under the Governance version
  rule. The copies of the schema inside the user's four vaults are data, not
  repository files; they are updated after the merge with the user's
  go-ahead.
- **Alternatives considered**: citing the chat vault's export from work pages
  across vaults (new code in the consistency tool); keeping student-related
  conversations out of the work vault. The user chose to admit the export into
  both vaults.

## R6. Size limits

- **Decision**: No new limit. The procedure tells the agent to report
  unverifiable units as the consistency skill already does.
- **Rationale**: Each changed export is stored three times (the fixed file
  and one bag per vault). The evidence cache has a 1 GiB budget
  (`EVIDENCE_BUDGET_BYTES` in `evidence.py`), and qmd ranks exactly only up to
  20,000 chunks (recorded by feature 010), so a very large export can leave
  units unverifiable. The user's export size is unknown until it arrives.
- **Alternatives considered**: splitting exports (raw would no longer be the
  file OpenAI sent).
