# Contract: Settings Read by a Composition Root

Every component's composition root reads settings the same way, so a person
or agent can predict where a value comes from (R-OS-01, R-OS-03, R-OS-12).
Only the composition root reads settings; inner rings receive plain values
(R-CA-04).

## Folders

| Kind | Variable | Default when unset, empty or relative | Namespace |
| --- | --- | --- | --- |
| configuration | `XDG_CONFIG_HOME` | `~/.config` | `verbose-broccoli/` |
| state | `XDG_STATE_HOME` | `~/.local/state` | `verbose-broccoli/` |
| cache | `XDG_CACHE_HOME` | `~/.cache` | `verbose-broccoli/` |
| data | `XDG_DATA_HOME` | `~/.local/share` | `verbose-broccoli/` |
| runtime | `XDG_RUNTIME_DIR` | none; a tool that needs it fails with a message | `verbose-broccoli/` |

- A relative value is ignored, as the XDG specification requires (R-OS-01).
- Python packages resolve folders with `platformdirs` 4.12.3, already in
  `uv.lock`; its XDG resolver ignores non-absolute values
  (`platformdirs/_xdg.py`, checked 2026-10-06). TypeScript packages that need
  a folder use the same three-step rule inline in their composition root;
  no shared package is added for it until a second TypeScript consumer
  exists (FR-008).
- A folder created for writing gets mode `0700` (R-OS-01).

## Files

| File | Holds | Owner |
| --- | --- | --- |
| `$XDG_CONFIG_HOME/verbose-broccoli/config.toml` | optional settings, one table per component (`[credit-offers]`, …) | the user; constitution VI already assigns it |
| `$XDG_CONFIG_HOME/verbose-broccoli/providers/<provider>.env` | credentials, one `0600` file per provider | the user, refreshed by `npm run secrets:refresh`; never read or printed by agents |

## Behavior

1. A missing optional setting uses the component's documented default
   (R-OS-03 "required to default to safe fallbacks"; R-OS-08).
2. A missing required credential or endpoint stops only the command that
   needs it, exits as an execution failure under the CLI contract, and names
   the file and variable, never the value (FR-010).
3. Environment variables may override a setting only where the component's
   `README.md` documents the variable; no variable is required for normal use
   (R-OS-08).
4. Timeouts and limits that differ between providers, such as the GLM request
   timeout, are settings, not constants (R-GG-15).
5. Tests run the composition root with a temporary absolute `XDG_*` folder
   and never read the user's real folders.
