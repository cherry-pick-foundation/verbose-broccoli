# Feature Specification: ChatGPT Export into the Chat Vault

**Feature Branch**: `feature/chat-export`

**Created**: 2026-09-29

**Status**: Draft

**Linear issue**: CHE-20

**Input**: Linear issue CHE-20, "Export ChatGPT web conversations into the
chat vault", and the develop session's task brief of 2026-09-29: get the
user's ChatGPT web conversations into the chat vault, so chat knowledge is
read from the vault instead of by searching chat sessions each time. The issue
leaves these points to the spec: how conversations leave ChatGPT on the web,
which conversations are admitted and how often, how a re-export becomes new
raw revisions, whether the chat plugin gets its own import skill, and which
vault holds conversations about students.

## Background

- Feature 012 (CHE-19) made four vaults under
  `~/.local/share/verbose-broccoli/vaults/`: `default`, `chat`, `code` and
  `work`. Constitution principle VI 2.0.0 makes exported conversations raw
  evidence in the `chat` vault only; in every other vault they stay in the
  user's workspace.
- The work plugin's `wiki-raw-import` skill already admits a file into any
  vault the user names (`--wiki chat`); feature 012 tested it with a synthetic
  exported conversation. It identifies a source by the original's absolute
  path: a changed file at the same path becomes a new revision of the same
  source, and a file at a new path becomes a new source.
- The chat plugin serves the web chat apps: ChatGPT on the web now, claude.ai
  on the web later. It has no skills (constitution IX). The user has ChatGPT
  Plus or Pro without developer mode, so ChatGPT on the web cannot reach a
  local tool (CHE-10, `.specify/assessments/backfire-chat/decision.md`).
- The work vault's student pages were written from ChatGPT conversations that
  an agent read through the desktop app; their source ledger is the work
  vault's `wiki/sources/chat-session-records.md`.

OpenAI's help center, read on 2026-09-29 ("Exporting your ChatGPT history and
data", updated last month; "Transfer exported conversations between ChatGPT
accounts", updated two months ago), says:

- A signed-in Free, Go, Plus or Pro account requests an export under
  **Settings > Data controls > Export data > Export**, then **Confirm
  export**. The Privacy Portal offers the same data through a privacy
  request.
- An email or SMS message brings a download link within up to 7 days. The
  link expires 24 hours after it arrives and works only while signed in to the
  same account. A new request waits until the previous one finishes.
- The download is one ZIP file with the chat history and other account data.
  It holds `conversations.json`; larger exports may hold numbered conversation
  JSON files instead. An export cannot restore deleted chats.
- The export covers the whole account; the help center offers no choice of
  conversations. A single conversation can only be shared as a link, which
  publishes it. The ZIP file's name is not documented.

## Clarifications

### Session 2026-09-29

The develop session relayed these questions to the user and returned the
answers the same day; the user took every recommended option.

- Q: How do conversations leave ChatGPT on the web? → A: Through OpenAI's
  account data export in ChatGPT's settings. Not the Privacy Portal, a
  third-party browser extension or shared links.
- Q: Which conversations go in? → A: The whole export ZIP goes in unchanged.
  Pages are written later, only for the conversations the user picks.
- Q: How often? → A: On demand. The user requests an export when they want
  one, and the agent admits it after the user says go.
- Q: How does a re-export become a new revision of the same source? → A: The
  user keeps one fixed file, `~/Documents/chatgpt/chatgpt-export.zip`, and
  saves each new export over it. Admitting that file again adds a revision of
  the same source; earlier exports stay in raw. The raw import does not
  change.
- Q: Does the chat plugin get its own import skill? → A: No. The work
  plugin's `wiki-raw-import` skill gets a ChatGPT export section. The import
  runs in Claude Code or Codex, where the work plugin is loaded; ChatGPT on
  the web cannot run local scripts. Constitution IX does not change.
- Q: Which vault holds conversations about students? → A: The export is also
  admitted into the work vault, so the work vault's student pages can cite it
  and be checked. Constitution VI changes to allow exported conversations as
  raw evidence in the `chat` and `work` vaults; the ZIP is stored in both.
- Q: Does this feature also write the chat vault's first pages? → A: No. It
  ends with the export admitted, checked and readable as evidence. Writing
  pages needs the ingest workflow that the vault schema leaves to a later
  change; the develop session registers that as a separate issue.
- Q: Does the user request a real export now? → A: Yes. Admitting it into the
  real vaults waits for this feature's merge into `develop` and the user's
  go-ahead, and CHE-20 can close without it.

## User Scenarios & Testing *(mandatory)*

The actors are the user, who owns the ChatGPT account and the vaults and
decides what enters them, and a coding agent (Claude Code or Codex) that runs
the admission and checks on the user's behalf.

### User Story 1 - Admit a ChatGPT export into the chat vault (Priority: P1)

The user requests an export in ChatGPT on the web and, when the link arrives,
saves the ZIP as the fixed export file. When the user says go, the agent,
following one written procedure, admits that file into the chat vault as one
raw revision, verifies the vault and logs the admission.

**Why this priority**: Without admitted exports the chat vault stays empty and
chat knowledge can only come from searching chat sessions.

**Independent Test**: In a temporary home folder, admit a synthetic export ZIP
into the chat vault by following the procedure, then verify the vault and read
the log entry.

**Acceptance Scenarios**:

1. **Given** a synthetic export ZIP saved as the fixed export file, **When**
   the agent admits it into the chat vault, **Then** it becomes one verified
   revision there and the original is unchanged.
2. **Given** the procedure, **When** the agent reads it, **Then** it names the
   user's steps in ChatGPT, the waiting and expiry times, the fixed export
   file, and that the agent admits only after the user says go.
3. **Given** an admitted export, **When** the vault's raw layer is verified,
   **Then** the check passes.

---

### User Story 2 - A re-export becomes a new revision (Priority: P1)

Some time later the user requests a new export, which holds the old
conversations plus new ones, and saves it over the fixed export file. The
agent admits it again, so it becomes a new revision of the same source, and
the earlier revision stays.

**Why this priority**: Every export repeats the whole history. If each one
became a separate source, pages could not tell which export replaces which.

**Independent Test**: In a temporary home folder, admit a synthetic export,
save a changed one over the fixed file, and admit again; then admit once more
without a change.

**Acceptance Scenarios**:

1. **Given** an admitted export and a changed later export saved over the
   fixed file, **When** the agent admits it, **Then** the vault holds two
   revisions of one source and both verify.
2. **Given** an unchanged export file, **When** the agent admits it again,
   **Then** nothing new is added and the report says it was already admitted.

---

### User Story 3 - The work vault admits the same export (Priority: P1)

After admitting an export into the chat vault, the agent admits the same file
into the work vault, so that pages about students there can cite it. In the
`default` and `code` vaults, exported conversations stay excluded.

**Why this priority**: The work vault's student pages were written from
ChatGPT conversations; they can only be checked against an export if the work
vault holds it.

**Independent Test**: In a temporary home folder, admit one synthetic export
into the chat and the work vault; verify both. Read the rules in the
constitution, the skill and the vault schema template.

**Acceptance Scenarios**:

1. **Given** a synthetic export, **When** the agent admits it into the chat
   and the work vault, **Then** each vault holds one verified revision of it.
2. **Given** the constitution, the skill and the schema template, **When**
   the agent reads them, **Then** they allow exported conversations as raw
   evidence in the `chat` and `work` vaults only.

---

### User Story 4 - Conversations are readable as evidence (Priority: P2)

A page that cites an admitted export can be checked against it: the Wiki
consistency tool turns the cited export into text that contains the
conversations' words, including Korean text.

**Why this priority**: Knowledge written from the export is only trustworthy
if the existing consistency check can read the evidence it cites.

**Independent Test**: In a temporary vault, cite a synthetic export from a
page and run the consistency tool's conversion; search its output for known
phrases from the synthetic conversations.

**Acceptance Scenarios**:

1. **Given** a page citing an admitted synthetic export, **When** the cited
   revisions are converted, **Then** the text contains every message of the
   synthetic conversations, in Korean and in English.
2. **Given** a synthetic export whose JSON writes non-ASCII characters as
   escape sequences, **When** it is converted, **Then** the text contains the
   characters themselves.

---

### Edge Cases

- The download link expires after 24 hours: the user requests a new export;
  nothing is admitted from a partial download.
- A file that is not a complete ZIP, for example a download still in
  progress, is not admitted; the procedure checks the file before admitting.
- An export that holds numbered conversation files instead of
  `conversations.json` is admitted the same way, as one ZIP, and its
  conversations are readable as evidence.
- A second request while one is processing is refused by ChatGPT; the
  procedure says to wait.
- Conversations deleted in ChatGPT are missing from a later export; the
  earlier revision still holds them.
- An export saved under a different name or folder would start a new source;
  the procedure says to save it over the fixed file.
- A large export may exceed the consistency tool's search limits; the tool
  then lists the affected units as unverifiable, and the agent reports them.
- The export contains conversations about students; no student name or
  conversation content enters the repository, Linear or Orca messages.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The work plugin's `wiki-raw-import` skill MUST describe how a
  ChatGPT export reaches the vaults: the user's steps in ChatGPT, the waiting
  and expiry times, the fixed export file, the check that the file is a
  complete ZIP, the admission after the user says go into the `chat` vault and
  then the `work` vault, the verification and the log entries.
- **FR-002**: The export MUST leave ChatGPT through OpenAI's account data
  export; the user performs every account action (signing in, requesting,
  downloading).
- **FR-003**: The downloaded ZIP MUST be admitted unchanged, as one raw file
  of kind `files`, so each raw revision is the export OpenAI delivered.
- **FR-004**: Every export MUST be kept as the one fixed file
  `~/Documents/chatgpt/chatgpt-export.zip`, saved over the previous export,
  so that each changed export becomes a new revision of the same source in
  each vault. The raw import MUST NOT change.
- **FR-005**: Admission MUST happen only when the user asks for it.
- **FR-006**: The chat plugin MUST NOT gain a skill in this feature;
  constitution IX stays as it is.
- **FR-007**: Constitution principle VI MUST allow exported conversations as
  raw evidence in the `chat` and `work` vaults and keep them out of the other
  vaults' raw layers. The skill, the vault schema template and every other
  repository document that states this rule MUST say the same.
- **FR-008**: The Wiki consistency tool MUST convert a cited export revision
  into text that contains its conversations' messages, whether its JSON
  writes non-ASCII characters directly or as escape sequences.
- **FR-009**: Tests MUST use synthetic exports only. No real export, student
  name or conversation content enters the repository, Linear or Orca
  messages.
- **FR-010**: Nothing MUST be admitted into the user's real vaults, and no
  real vault's schema MUST change, without the user's go-ahead.

### Key Entities

- **ChatGPT export**: The ZIP file OpenAI delivers for one account. It holds
  every conversation still in the account, as `conversations.json` or
  numbered conversation files, plus a browsable `chat.html` and other account
  data.
- **Fixed export file**: `~/Documents/chatgpt/chatgpt-export.zip`, the one
  place the user keeps the latest export; it is the original of the export
  source in both vaults.
- **Export source**: In each of the chat and work vaults, the source whose
  revisions are the successive exports; each revision is one BagIt bag
  holding one export unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Following the procedure, an agent admits a synthetic export into
  temporary chat and work vaults, and both vaults' checks pass, with no other
  instructions.
- **SC-002**: Two successive synthetic exports saved over the fixed file give
  one source with two revisions in a vault; a third, unchanged admission adds
  nothing.
- **SC-003**: The consistency tool's conversion of a cited synthetic export
  contains every message text of its conversations, Korean and English, for
  both direct and escaped non-ASCII JSON.
- **SC-004**: The constitution, the skill, the vault schema template and the
  architecture document state the same rule: exported conversations are raw
  evidence in the `chat` and `work` vaults only.
- **SC-005**: No repository file, commit, Linear comment or Orca message from
  this feature contains a real conversation, a student name or a private file
  name.

## Assumptions

- OpenAI's account data export stays available for the user's plan; if it
  changes, the procedure changes.
- The export fits on the local disk three times: the fixed file and one raw
  copy in each of the two vaults, per changed export.
- Whether OpenAI writes non-ASCII characters in the export's JSON directly or
  as escape sequences is not documented; the user's real export will show it,
  and FR-008 covers both.
- The raw kind for an export is `files`, as feature 012 decided.
- The copies of the vault schema inside the user's real vaults are updated to
  the new rule after the merge, with the user's go-ahead; that is operational
  work, not a repository change.

## Out of Scope

- Writing Wiki pages from conversations, and the ingest workflow they need;
  the develop session registers a separate issue.
- A chat plugin skill; claude.ai on the web, which a later issue covers.
- Automated export requests, browser automation of ChatGPT, or reading
  conversations through ChatGPT's internal interfaces.
- Admitting the user's real export; it waits for the merge and the user's
  go-ahead.
- Changing how the work vault's existing student pages were written.
