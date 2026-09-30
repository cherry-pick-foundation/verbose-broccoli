# Feature Specification: Google Workspace Access Through gws

**Feature Branch**: `feature/google-workspace`

**Created**: 2026-09-30

**Status**: Draft

**Linear issue**: CHE-52

**Input**: Linear issue CHE-52, "Give agents access to Google Workspace
through the Google Workspace CLI", and the develop session's task brief of
2026-09-30. The user uses Google Workspace (Docs to print worksheets, Slides
for class presentations) and decided that day to let agents work with it.
CHE-52 blocks four uses filed with it: print-ready worksheets as Google Docs
(CHE-53), paper worksheet results recorded in Sheets (CHE-54), lesson slide
drafts in Slides (CHE-55) and school exam dates in Calendar (CHE-56).

The user's decisions of 2026-09-30:

- Agents reach Google Workspace through the Google Workspace CLI, gws
  (<https://github.com/googleworkspace/cli>, Apache-2.0, from Google's
  Workspace GitHub organization). It covers every Workspace API, including
  creating Slides and writing Sheets and Forms, and ships agent skills. The
  Google Workspace extension named in Google's official MCP list
  (<https://github.com/gemini-cli-extensions/workspace>) only reads Slides and
  Sheets, so gws is the base. gws's own agent skills are reused unchanged
  where they fit and recorded like other upstream copies; the work plugin gets
  only the glue it needs.
- The user is the admin of the cherry-pick.org Google Workspace. A Google
  Cloud project under that organization gets an Internal OAuth app, which
  avoids Google's app verification and testing mode's 7-day token expiry. The
  user does the console steps and the sign-in, guided step by step; no agent
  asks for or handles the user's password. gcloud is not installed if the
  manual console setup works.
- Security: before gws is installed, a read-only security check of the
  pinned release's source and release assets covers network use, telemetry,
  credential storage, token handling, update behavior and what its agent
  skills let an agent do, with evidence for every finding.
- Scopes: the smallest set the four uses need, approved by the user with a
  reason for each before the consent screen is configured.
- Credentials: the OAuth client file and tokens live outside the repository
  where the user approves, at mode 0600 or stricter, and never appear in the
  repository or in messages. The user approves every file or folder created
  outside the repository.
- Pinning: pinned tool versions have one source, the project's mise file and
  lock that CHE-44 introduces, with a weekly automatic update (CHE-50). gws is
  pinned there once CHE-44 has merged; until then the reviewed release is
  tested from this worktree.
- Live checks: after sign-in, one test Doc is created in a Drive folder the
  user approves, read back and deleted. Every live action is reported.

## Clarifications

### Session 2026-09-30

- Q: Which scopes may gws request? → A: Exactly three groups, approved by the
  user: `https://www.googleapis.com/auth/drive.file` (create Docs, Sheets,
  Slides, Forms and folders, and read, edit or delete only files authorized
  to this app: those it created, or those the user opens with it through a
  Google file picker, which this setup does not have); `https://www.googleapis.com/auth/calendar.app.created` (a separate
  "Exam dates" calendar and only its events); and the `openid`,
  `userinfo.email` and `userinfo.profile` scopes gws adds to identify the
  account. Nothing else. Google's Discovery documents list `drive.file` for
  every create, edit and read call of Docs, Sheets, Slides, Forms and Drive
  files that the uses need, and `calendar.app.created` for `calendars.insert`
  and the event calls. The trade-off the user accepted: agents cannot open
  files, forms or calendars the user made by hand.
- Q: gws v0.22.5, the newest release, carries six RustSec advisories in its
  lockfile. Use the signed release unchanged (A) or build the tagged source
  with four libraries raised (C)? → A: A. Google's signed release unchanged,
  pinned with its checksum and build record in the project's mise file and
  lock, and moved forward by CHE-50's weekly update when upstream releases.
  The advisories and the risk reasoning are recorded in the release report's
  "Decision" section.
- Q: Where do the OAuth client file and the tokens live? → A: gws's own
  folder `~/.config/gws/` (0700, files 0600). The downloaded client file is
  moved there as `client_secret.json` (0600) and the copy in Downloads is
  deleted. The user confirmed that `~/.config` is not backed up or synced to
  a cloud service.
- Q: Which Drive folder does the live check use? → A: gws creates a folder
  "verbose-broccoli" at the top of My Drive; the test Doc "CHE-52 access
  check" goes inside and is deleted after it is read back; the folder stays
  for CHE-53 to CHE-55.
- Q: Which controls from the security check apply? → A: The coordinator
  runs the one-time sign-in with exactly the approved scopes while the user
  approves it in a browser with no other untrusted pages open; agents never
  run gws's `auth status`, `export`, `logout` or `setup` commands or its
  Model Armor options; logging stays off; gws runs only from folders with no
  `.env` in them or above them, with the gws credential variables cleared.
  Accepted limits: the sign-in's missing `state` and PKCE, the encryption
  key file beside the tokens, and no network allowlist. These approved
  controls replace the runtime report's controls 2 (a config folder named
  by variable) and 3 (a private staging folder outside repository trees);
  the runtime report's disposition line records each deviation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A reviewed gws release (Priority: P1)

Before any Google credential touches gws, the user reads a security check of
the exact release to be installed and decides whether and how to use it.

**Why this priority**: gws will hold OAuth tokens for the user's Workspace,
which also holds student records (CHE-54). Nothing else starts until the
check allows it.

**Independent Test**: The check's reports exist under
`specs/027-google-workspace/security/`, name the reviewed commit and assets,
give a verdict, and back every finding with a file:line or a command.

**Acceptance Scenarios**:

1. **Given** the pinned tag and its release assets, **When** the check runs,
   **Then** its reports cover network use, telemetry, credential storage,
   token handling, update behavior and the copied skills, each finding with
   evidence.
2. **Given** a verdict that requires controls, **When** gws is installed and
   used, **Then** each required control is applied or the user accepted its
   absence.

---

### User Story 2 - Signed-in access with the approved scopes (Priority: P1)

The user sets up the Cloud project and the Internal OAuth app, signs in once,
and agents can then create, read and delete their own Google files.

**Why this priority**: The four uses need working access.

**Independent Test**: `gws auth status` reports the signed-in account with
exactly the approved scopes; a test Doc is created in the approved folder,
read back and deleted, and a final lookup no longer finds it.

**Acceptance Scenarios**:

1. **Given** the approved scope list, **When** the user signs in, **Then** the
   token carries only those scopes plus the identity scopes gws always adds.
2. **Given** a signed-in gws, **When** an agent creates a Doc with known
   text, **Then** reading it back returns that text, and after deletion the
   Doc is gone.
3. **Given** a signed-in gws, **When** an agent calls an API outside the
   approved scopes (for example listing a Drive file gws did not create),
   **Then** Google refuses or returns nothing, and no data leaves the scope.

---

### User Story 3 - Agents know how to use gws here (Priority: P2)

An agent working on CHE-53 to CHE-56 finds, in the work plugin, gws's own
skills for the services it needs and a short local skill that says how gws is
set up in this repository.

**Why this priority**: Without it every later feature rediscovers the setup.

**Independent Test**: The copied skills match upstream byte for byte and
their `upstream.json` hashes; the local skill names the scopes and their
limits, the credential location, the confirmation rules and the controls from
the security check.

**Acceptance Scenarios**:

1. **Given** the work plugin, **When** an agent looks for how to create a Doc,
   Sheet, Slides deck, Form or calendar event, **Then** it finds the matching
   gws skill and the local skill's rules.
2. **Given** a copied gws skill, **When** it is compared with the pinned
   upstream file, **Then** it is identical and recorded in its
   `upstream.json` and in `licenses/THIRD_PARTY_NOTICES.md`.

---

### User Story 4 - One pinned version (Priority: P2)

gws's version is pinned in the project's mise file and lock with its
checksums, so every machine installs the reviewed release and CHE-50's weekly
update can move it.

**Why this priority**: The user's version policy keeps one source of pinned
tool versions.

**Independent Test**: `mise install` from the committed lock installs gws
0.22.5 with the lock's checksum, and `gws --version` prints 0.22.5.

**Acceptance Scenarios**:

1. **Given** CHE-44's mise file on `develop`, **When** this feature merges
   `develop`, **Then** gws is pinned there with its checksums for the
   supported platforms.

---

### Edge Cases

- The keyring is locked or unavailable when gws needs its encryption key.
- A `.env` file or an environment variable in an agent's shell changes gws's
  credential source or configuration directory.
- A refresh token is revoked or expires; gws reports an authentication error
  instead of falling back to other credentials.
- CHE-44 has not merged when this feature is otherwise ready.
- An agent tries to share, delete or email without the user's confirmation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A read-only security check of gws v0.22.5 (tag `v0.22.5`,
  commit `705fb0ecac6f4249679958f6325b809b63fdde17`) and its Linux release
  assets MUST cover network use, telemetry, credential storage, token
  handling, update behavior and what the copied agent skills let an agent do,
  with a file:line or a command as evidence for every finding. Its reviewers
  are chosen with the code plugin's `model-choice` skill.
- **FR-002**: gws MUST be installed only after the check allows it, from a
  release asset whose SHA-256 matches the release's checksum, and used with
  the check's required controls.
- **FR-003**: The Google Cloud project MUST belong to the cherry-pick.org
  organization, with an Internal OAuth consent screen, a Desktop-app OAuth
  client, and only the APIs the four uses need enabled. The user performs the
  console steps and the sign-in; agents guide them and never ask for or
  handle the password.
- **FR-004**: gws MUST sign in with exactly the scope list the user approved
  (see Clarifications), passed explicitly with `gws auth login --scopes`.
- **FR-005**: The OAuth client file and the tokens MUST live outside the
  repository in the location the user approved, with directories at 0700 and
  files at 0600 or stricter, and MUST NOT appear in the repository, commit
  messages, Orca messages, Linear or logs.
- **FR-006**: gws MUST be pinned in the project's mise file and lock after
  CHE-44 has merged into `develop`. Until then the reviewed release runs from
  this worktree's ignored `.local/` folder.
- **FR-007**: The work plugin MUST carry the gws agent skills that fit the
  approved scopes, copied unchanged from the pinned tag, each with an
  `upstream.json` (repository, tag, revision, path, SHA-256) and one notice
  entry in `licenses/THIRD_PARTY_NOTICES.md`; plus one local skill with the
  repository's glue: the scopes and what they allow, the credential location,
  the security check's controls, confirmation before sharing, deleting or
  sending, and reporting live actions.
- **FR-008**: After sign-in, a live check MUST create one test Doc in a Drive
  folder the user approves, read it back and delete it, and report each of
  these actions.
- **FR-009**: No student name or record MUST be written into the repository,
  Linear or Orca messages.

### Key Entities

- **OAuth client**: the Desktop-app client of the Internal consent screen;
  its JSON file identifies the app to Google.
- **Credentials**: gws's encrypted refresh token and its token cache, with
  the encryption key in the keyring or a key file.
- **Approved scopes**: the user-approved list of Google permissions.
- **Upstream skill copy**: an unchanged gws skill folder with its
  `upstream.json`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The security reports give a verdict and evidence for 100% of
  their findings.
- **SC-002**: `gws auth status` lists exactly the approved scopes plus the
  identity scopes.
- **SC-003**: The live check's Doc is created, read back with the same text
  and deleted; a lookup afterwards finds nothing.
- **SC-004**: No credential file is under the repository, and each credential
  file has mode 0600 or stricter in a 0700 directory.
- **SC-005**: `mise install` from the committed lock installs gws 0.22.5 with
  the lock's checksum.
- **SC-006**: `npm run verify` reports VERIFIED on the merged result.

## Assumptions

- The user holds the admin role for cherry-pick.org and can create a Cloud
  project under it.
- The laptop runs Linux with a Secret Service keyring on a D-Bus session.
- The four uses (CHE-53 to CHE-56) are built in their own features; this
  feature only gives access and instructions.
- Out of scope: Gmail, service accounts, domain-wide delegation, the
  `gws auth setup` path through gcloud, and the npm or Gemini extension
  distributions of gws.
