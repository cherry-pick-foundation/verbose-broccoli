# Supported path contract

With an absolute XDG_DATA_HOME, both builders select
`XDG_DATA_HOME/verbose-broccoli/llm-wiki/<name>`. Unset, empty or relative values
use `HOME/.local/share/verbose-broccoli/llm-wiki/<name>`. The default name stays
work; default, chat, code, work and valid custom names are supported.
Existing rejection of empty, dot, parent, slash-containing and NUL names remains.
Commands accept their existing --wiki placement. The old container is not a
fallback. Session staging refuses raw trees inside llm-wiki before mkdir.
Real sources, Wiki history and actual container/link settings are outside this
change. Readiness inspection alone cannot authorize removing the existing link.
