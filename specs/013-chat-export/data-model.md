# Data Model: ChatGPT Export into the Chat Vault

No new stored structure. The feature reuses the raw import's BagIt revisions
and the consistency tool's evidence cache; this file names how an export maps
onto them.

## ChatGPT export

The ZIP file OpenAI delivers for one account (research R1).

| Member | Content | Evidence text |
| --- | --- | --- |
| `conversations.json`, or numbered conversation JSON files in larger exports | Every conversation still in the account, as JSON | Yes, through the JSON converter |
| `chat.html` | A viewer whose conversations sit in a script | No text |
| Other JSON files (for example account and feedback data) | Account data | Yes, as JSON text |
| Images, audio and other media | Attachments | What MarkItDown's converters give; members they cannot read are skipped |

Validation: the file passes `python3 -m zipfile -t` before admission.

## Fixed export file

`~/Documents/chatgpt/chatgpt-export.zip` in the user's workspace. The user
saves each new export over it. It is the original, and its resolved absolute
path is the `Internal-Sender-Identifier` of the export source in each vault.
Neither the agent nor the raw import moves, changes or deletes it.

## Export source

One source in each of the `chat` and `work` vaults, stored at
`raw/files/<source-id>/<revision>/data/chatgpt-export.zip`.

| State | Trigger | Result |
| --- | --- | --- |
| No source | First admission | New source ID, first revision |
| Latest revision equals the file | Admission | `already_admitted`, nothing written |
| File changed | Admission after a new export | New revision under the same source ID; earlier revisions stay |

The two vaults' sources have different source IDs and are independent: each
vault records its own admissions.

## Evidence text

The consistency tool's conversion of a cited revision, stored once under
`CACHE/wiki-evidence/<vault>/markitdown-<converter version>/<source-id>/<revision>.md`.
The converter version is MarkItDown's version plus a local revision for the
JSON converter, so a conversion made before this feature is not reused.
