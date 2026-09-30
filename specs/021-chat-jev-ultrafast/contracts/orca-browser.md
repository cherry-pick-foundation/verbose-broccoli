# Contract: Orca browser mode

Applies to `packages/jev-ultrafast/src/jev_ultrafast/browser.py`. See
[research R3](../research.md#r3-orcas-built-in-browser).

## Mode

- `JEV_BROWSER` unset, empty or `orca`: Orca mode. `chrome`: upstream
  behavior, unchanged. Any other value raises an error naming it.

## Orca mode

1. Before `browser_harness` is imported, `BH_RUNTIME_DIR` and `BH_TMP_DIR`
   default to one private folder, `$XDG_RUNTIME_DIR/jev-ultrafast` (a short
   path; Unix socket paths are limited), unless the caller set them.
2. `Browser(url)` runs `orca tab create --url about:blank --worktree current
   --json` and keeps `result.browserPageId`.
3. It runs `orca exec --command "get cdp-url" --page <id> --json` and sets
   `BU_CDP_WS` to `result.cdpUrl` for the daemon it starts.
4. It stops any daemon left in the private folder, then calls upstream's
   `ensure_daemon()`.
5. It takes the target ID of the one page `Target.getTargets` lists and
   attaches to it. From here on, upstream's code runs unchanged: device
   metrics, focus emulation, `Page.navigate` to `url`, the ready-state wait,
   observation and actions.
6. `close()` runs `orca tab close --page <id> --json` and stops the daemon.
   It never closes a tab it did not open.
7. A failing or missing `orca` command raises an error with the command's
   message and a hint that `JEV_BROWSER=chrome` selects Chrome; the tab, if
   created, is closed.

Scrolling (`mouseWheel`) and screenshots are unchanged. They can stall when
the Orca tab is not drawn on screen (research R3; user decision 2026-09-30).
Browser jobs run one at a time.
