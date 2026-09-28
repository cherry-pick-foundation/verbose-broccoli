# Feature Specification: Wiki Vaults

**Feature Branch**: `feature/vaults`

**Created**: 2026-09-28

**Status**: Draft

**Linear issue**: CHE-19

**Input**: Linear issue CHE-19, "Wiki vaults: rename wikis/ to vaults/ and keep
default, chat, code and work vaults", and the develop session's task brief of
2026-09-28. The user decided on 2026-09-28:

1. Rename `wikis/` to `vaults/` everywhere: the data and state roots under
   `~/.local/share/verbose-broccoli/` and `~/.local/state/verbose-broccoli/`,
   code, tests, skills, documents and the constitution, including feature
   009's spec records. Check the documents with backfire's judgment tools
   before and after editing.
2. Four vaults. The current `default` instance holds only education work (the
   raw imports and the per-student pages), so it becomes `vaults/work/` with
   its Git history and uncommitted edits intact. `default`, `chat` and `code`
   start empty; `default` is for knowledge that belongs to no single plugin.
3. Chat vault: exported conversations become raw originals in the chat vault,
   and its pages are written from them, so chat knowledge is read from the
   vault instead of by searching chat sessions each time. Constitution VI's
   rule that conversation records are not Raw evidence no longer applies to
   the chat vault.
4. Code vault: coding knowledge the code plugin keeps for work in any project
   (libraries, patterns, decisions). This repository's development memory
   stays in the Spec Kit records, code and Git; `AGENTS.md` says the code vault
   is not that memory.
5. Constitution IX's statement that the chat package has no persistent state
   changes, since the chat vault is its state.

A workflow that exports chat sessions and admits them is out of scope unless
the existing raw import already admits an exported chat file.

## Clarifications

### Session 2026-09-28

The develop session relayed these questions to the user and returned the
answers the same day.

- Q: Which vault does the raw import use when no vault is named? → A: `work`.
  The skill belongs to the work plugin, and today's data is education work. A
  plugin's Wiki skills use the vault named after the plugin by default;
  `default`, `chat` and `code` are chosen by name.
- Q: The raw import belongs to the work plugin, and a plugin does not open
  another plugin's private store. May it fill the chat vault? → A: Yes. Vaults
  are the user's shared Wiki storage, which any plugin's Wiki tool may write
  when the user selects the vault. The raw import serves the chat vault now.
  Exporting chat sessions is a separate issue, which the develop session
  registers; the chat plugin targets ChatGPT on the web, not the desktop apps.
- Q: Which Conventional Commits type does the constitution change take? → A:
  A breaking change, `feat(constitution)!`, which raises the version from 1.0.1
  to 2.0.0: the governed data folder changes and the old path stops working.
  The user approved it.
- Q: How far does the rename reach? → A: Only the storage folder's name
  changes. The concept names (Wiki, Wiki instance, the `raw/` and `wiki/`
  layers, the schema) and the raw import's `--wiki` option stay. Feature
  009's records get only the folder rename; their statements that feature 009
  built one `default` instance stay as its history. The shared schema template
  says that exported conversations are raw evidence only in the chat vault,
  and the existing instance's schema is left alone because it does not name
  the old path.

## User Scenarios & Testing *(mandatory)*

The actors are the user, who owns the Wiki data and decides what enters it,
and a coding agent (Claude Code, Codex or OMP) that runs the raw import and
maintains Wiki pages on the user's behalf.

### User Story 1 - The Wiki storage folder is `vaults/` (Priority: P1)

The agent runs the raw import. Each vault lives in `vaults/<name>/` under the
data root, and its run lock and selection lists live in `vaults/<name>/` under
the state root. No code, test, skill or document names `wikis/` as the
storage folder any more.

**Why this priority**: Every later step, including the move of the live Wiki,
depends on the tool and the documents agreeing on one folder name.

**Independent Test**: In a temporary home folder, create a vault, admit a
synthetic file and verify it; list the data and state roots.

**Acceptance Scenarios**:

1. **Given** an empty home folder, **When** the vault is created, **Then** it
   appears under `vaults/` in the data root and nothing appears under
   `wikis/`.
2. **Given** a created vault, **When** a file is admitted, **Then** the run
   lock is in `vaults/<name>/` under the state root.
3. **Given** the repository after the change, **When** it is searched for
   `wikis`, **Then** only records of this rename match; none says that
   `wikis/` is the storage folder.

---

### User Story 2 - Four vaults, and the raw import defaults to `work` (Priority: P1)

The user keeps four vaults: `default` for knowledge that belongs to no single
plugin, `chat` for the chat plugin, `code` for the code plugin and `work` for
the work plugin's education work. The raw import, a work plugin skill, uses
`work` unless the agent names another vault.

**Why this priority**: The education data moves to `work`; an import without a
vault name must keep landing there and not in an empty vault.

**Independent Test**: In a temporary home folder, run the raw import without a
vault name and with each of the four names; check where each vault appears.

**Acceptance Scenarios**:

1. **Given** no vault name, **When** the agent creates, fills or verifies a
   vault, **Then** the `work` vault is used.
2. **Given** the name `default`, `chat` or `code`, **When** the agent runs the
   raw import with it, **Then** only that vault is used.
3. **Given** the constitution, `AGENTS.md`, the architecture document and the
   skill, **When** the user reads them, **Then** they name the four vaults,
   their owners and the default rule the same way.

---

### User Story 3 - The chat vault admits exported conversations (Priority: P1)

The user exports a conversation to a file and asks the agent to admit it. The
agent copies it into the chat vault's `raw/` like any other original. In the
other vaults, conversation records stay excluded.

**Why this priority**: Decision 3 makes exported conversations the chat
vault's raw evidence; the existing tool can copy them once the rules allow it.

**Independent Test**: In a temporary home folder, admit a synthetic exported
conversation into the chat vault and verify it; read the rules in the skill
and the schema template.

**Acceptance Scenarios**:

1. **Given** a synthetic exported conversation file, **When** the agent admits
   it into the chat vault, **Then** it becomes one verified revision there.
2. **Given** the skill and the schema template, **When** the agent reads them,
   **Then** they allow exported conversations only in the chat vault.

---

### User Story 4 - The live Wiki moves to `vaults/work` intact (Priority: P2)

After the feature is merged into `develop`, the existing instance moves to
`vaults/work/` and its state folder to `vaults/work/` under the state root.
The empty `default`, `chat` and `code` vaults are created, and the old
`wikis/` folders are removed.

**Why this priority**: The data holds real student work; it must keep its Git
history and the user's uncommitted edits, but the move can only happen once
the merged tool reads the new folder.

**Independent Test**: Compare the instance's Git history and uncommitted
changes before and after the move, and run the tool's verification on every
vault.

**Acceptance Scenarios**:

1. **Given** the instance with uncommitted edits, **When** it is moved,
   **Then** its commit history and its uncommitted changes are the same as
   before.
2. **Given** the moved data, **When** every vault is verified, **Then** each
   passes.
3. **Given** the finished move, **When** the data and state roots are listed,
   **Then** no `wikis/` folder remains.

---

### Edge Cases

- A vault name other than the four, such as a test fixture's name, still works
  under `vaults/<name>/`; the tool does not restrict names beyond its existing
  rules.
- A leftover `wikis/` folder is neither read nor migrated by the tool; only the
  one-time move handles the live data.
- If `vaults/work/` already exists when the move starts, for example because
  the tool created it, the move stops instead of merging two folders.
- If a process has files open in the instance, or the user's session that
  writes student pages is busy, the move waits for the user's decision.
- A conversation file selected for a vault other than `chat` is refused by the
  procedure, not by the tool, which does not inspect contents.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The raw import MUST keep each vault at `DATA/vaults/<name>/`,
  and its run lock and selection lists under `STATE/vaults/<name>/`. Staging
  stays at `CACHE/raw-import/<name>/`.
- **FR-002**: Without a vault name, creating, admitting and verifying MUST use
  the `work` vault. `--wiki <name>` selects any name the tool already accepts.
- **FR-003**: The raw import MUST NOT read, create or change anything under a
  `wikis/` folder.
- **FR-004**: The raw import MUST admit a file into the chat vault exactly as
  into any other vault.
- **FR-005**: Constitution principle VI MUST name `vaults/` and the four vaults
  and MUST limit the rule that conversation records are not raw evidence to
  the vaults other than `chat`.
- **FR-006**: Constitution principle IX MUST say that the chat package's
  persistent state is its vault.
- **FR-007**: The constitution's Governance section MUST record the user's
  2026-09-28 decisions, and its version MUST become 2.0.0 through one breaking
  commit.
- **FR-008**: `AGENTS.md` MUST say that the code vault holds coding knowledge
  for work in any project and is not this repository's development memory.
- **FR-009**: `docs/architecture.md` MUST describe the four vaults, their
  owners, the default rule, and that any plugin's Wiki tool may write a vault
  the user selects.
- **FR-010**: The `wiki-raw-import` skill MUST name `vaults/` and the default
  vault `work`. The skill and its schema template MUST allow exported
  conversations as raw evidence only in the chat vault; the template names no
  storage path, because each vault gets its own copy.
- **FR-011**: Every other repository document, including feature 009's
  records, MUST name `vaults/` wherever it names the storage folder; concept
  names and the `--wiki` option stay.
- **FR-012**: Tests MUST use only synthetic fixtures; no student name or record
  enters the repository, Linear or Orca messages.
- **FR-013**: The one-time move MUST happen only after the feature is finished
  into `develop`, MUST use a same-file-system rename after checking that no
  process holds files open under the moved folders, and MUST NOT commit, edit
  or discard the user's uncommitted Wiki edits or rewrite `wiki/log.md`.
  Inside the vaults it MAY change only what the raw import's creation step
  writes, and the schema only if it names the old path.

### Key Entities

- **Vault**: One Wiki instance with the Raw, Wiki and Schema layers of
  principle VI, stored at `DATA/vaults/<name>/`. The four vaults are
  `default` (no single plugin), `chat` (exported conversations and the pages
  written from them; the chat package's persistent state), `code` (coding
  knowledge for any project) and `work` (education work).
- **Vault state**: The run lock and selection lists of one vault under
  `STATE/vaults/<name>/`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the merge, a search of `develop` for `wikis` finds only
  records of this rename: the constitution's amendment report and Governance
  history, and this feature's records. No code, test, skill or document names
  `wikis/` as the storage folder.
- **SC-002**: Four vaults exist under `~/.local/share/verbose-broccoli/vaults/`,
  and the tool's verification passes on each.
- **SC-003**: `vaults/work/` has the same latest commit, commit count and
  uncommitted-change list as the instance had before the move.
- **SC-004**: No `wikis/` folder remains under the data or state root.
- **SC-005**: The raw import's tests pass, including a run without a vault
  name that lands in `work` and an admission into the chat vault.
- **SC-006**: After editing, the document judgment step leaves no document
  unit judged contradicted or flagged for review without a correction or a
  recorded reason.

## Assumptions

- The data, state and cache roots are on one file system, as feature 009
  recorded, so a rename moves the instance, its Git repository and its
  uncommitted edits without copying.
- The existing instance's schema does not name `wikis/`, so the move does not
  change it.
- Existing exported conversation files can be admitted with the raw kind
  `files`; no new raw kind is added.
- Orca's project entries for the Wiki folders are the develop session's
  concern.
- `registry.json` stays unspecified; no consumer chooses among vaults through
  it yet.

## Out of Scope

- Exporting chat sessions from ChatGPT on the web and admitting them
  automatically; the develop session registers a separate issue.
- A raw import skill owned by the chat plugin, and Wiki pages for the chat,
  code and default vaults.
- Adapting the paused feature 010 (CHE-8) and the unstarted CHE-10, which merge
  `develop` after this feature.
