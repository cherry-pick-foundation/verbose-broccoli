# Contract: ChatGPT export procedure

The section "ChatGPT exports" of
`plugins/work/skills/wiki-raw-import/SKILL.md` states these steps. An agent
that follows only that section and the skill's existing procedure must be
able to do each one.

1. **The user requests the export.** In ChatGPT on the web: **Settings >
   Data controls > Export data > Export > Confirm export**. This is an
   account action; the agent never performs it. A new request waits until an
   earlier one finishes.
2. **The user downloads it.** The link arrives by email or SMS within up to
   7 days, expires 24 hours after it arrives, and works only while signed in
   to the same account. The user saves the ZIP over
   `~/Documents/chatgpt/chatgpt-export.zip`. A download saved anywhere else
   would start a new source.
3. **The agent waits for go.** Nothing is admitted until the user asks.
4. **The agent checks the file.** `python3 -m zipfile -t` on the fixed file
   must pass; otherwise the agent stops and tells the user.
5. **The agent admits it.** The selection is the one line
   `{"path": "<home>/Documents/chatgpt/chatgpt-export.zip", "kind": "files"}`.
   The agent runs `admit` with `--wiki chat`, then with `--wiki work`
   (the work vault's student pages cite exports), and reports each outcome:
   `admitted`, or `already_admitted` when the export has not changed.
6. **The agent verifies and logs.** `verify` for each vault, one `log.md`
   entry per vault, and a commit in each vault's own repository, as the
   skill's existing steps 7 to 9 say.

The raw import's interface does not change; feature 012's
`specs/012-wiki-vaults/contracts/raw-import-cli.md` still applies.

Rule stated by the constitution, the skill, the schema template and the
architecture document: exported conversations are Raw evidence in the `chat`
and `work` vaults only; in the `default` and `code` vaults they stay in the
user's workspace.
