# Problem Definition: Backfire for the chat plugin

- **Slug**: backfire-chat
- **Created**: 2026-09-28
- **Inputs used**: intake.md | research.md

## Problem Statement

The user does education work in ChatGPT on the web and cannot call backfire's
judgments from there. Backfire, including the pseudonymization of student
identifiers before a judgment reaches its provider, runs only as a local stdio
server that Codex CLI and Claude Code start
([research.md](research.md#prior-art)).

## Affected Users & Stakeholders

- **Users**: the user, working in ChatGPT on the web on a Plus or Pro plan
  ([research.md](research.md#users--demand)).
- **Stakeholders**: the user, who decides and pays the provider; the students
  whose records a judgment may contain.

## Goals

- Backfire's tools can be called from a ChatGPT conversation on the web.
- Student identifiers are replaced before a judgment reaches backfire's
  provider, as in the work build.
- The user's machine accepts no inbound connection, and no public endpoint can
  spend the user's provider key.

## Non-Goals

- The ChatGPT desktop app and Claude Desktop, which the user does not work in.
- claude.ai on the web, which the user placed in a later issue.
- The code and work builds (CHE-10's own scope).

## Success Metrics

- Qualitative: ChatGPT on the web lists backfire's tools and completes one
  judgment whose provider request carries pseudonyms, not roster names
  (baseline: not possible today).

## Cost of Inaction

Backfire stays usable where it already runs, through the code and work plugins
in Codex CLI and Claude Code. Nothing breaks. The user cannot call it from
ChatGPT on the web.

## Open Questions

- Whether developer mode will reach this account, and with which tool
  permissions ([research.md](research.md#gaps--open-questions)).
