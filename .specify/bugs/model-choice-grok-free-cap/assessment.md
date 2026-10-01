# Bug Assessment: Model choice offers Grok after its free usage cap is hit

- **Slug**: model-choice-grok-free-cap
- **Created**: 2026-10-01
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-79> (Linear CHE-79,
  read with `orca linear issue CHE-79 --comments`; host `linear.app`, allowlisted)
- **Verdict**: valid
- **Severity**: medium

## Report (summarized)

Model choice picked Grok twice on 2026-10-01 while Grok refused every
request. CodexBar (`grok-web`) and Orca's account list (`oauth`) showed only
a weekly window at 0% used, and `references/model-choice.md` said the account
"draws on a weekly credit pool".

## Cause

Grok's free tier caps each model at 1,000,000 tokens over a rolling 24-hour
window. Only the API's 429 error shows it, and Grok logs that error to
`~/.grok/logs/unified.jsonl` as `subscription:free-usage-exhausted ... tokens
(actual/limit): N/1000000`. Neither tracker reads it.

## Reproduction

`grep -h 'subscription:free-usage-exhausted' ~/.grok/logs/unified.jsonl | tail -1`
on 2026-10-01 holds an entry at 13:11:58.698Z for `grok-4.7` with
`1012248/1000000`, while `orca account list --json` reports the weekly window
unused.

## Remediation

Documentation only, reusing Grok's own log: correct the Grok facts in the
skill and say how to read the latest entry (time, model, actual/limit) as
backfire evidence; Grok is unavailable for that model until about 24 hours
after the heavy use. No new code.

## Other free agents

Searched Copilot's logs (`~/.copilot/logs`) and Antigravity's
(`~/.gemini/antigravity-cli/log`) for `resource_exhausted`, "quota exhausted",
"usage limit" and "rate limit": no hits. Cursor has no local log directory.
Copilot and Cursor trackers report the monthly window their plans cap;
Antigravity's quota is unread and already documented as unknown; MiniMax Code
is not a candidate. No same gap is shown. Open: none cheap; the skill now
tells agents to treat any limit refusal as unavailable until its window clears.
