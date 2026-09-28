"""Run the Backfire command line entry points."""

import argparse
import asyncio
import os


def main() -> None:
    """Run the selected Backfire command."""
    parser = argparse.ArgumentParser(prog="backfire")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("serve-mcp", help="Serve MCP over stdio")
    subcommands.add_parser("ready", help="Check backend readiness")
    args = parser.parse_args()
    if args.command == "serve-mcp":
        from backfire.judge import (  # noqa: PLC0415  # Lazy command import.
            judge,
        )
        from backfire.server import (  # noqa: PLC0415  # Lazy command import.
            serve,
        )

        if (script := os.environ.get("BACKFIRE_TEST_JUDGE_SCRIPT")) is not None:
            from pathlib import Path  # noqa: PLC0415  # Lazy test-only import.
            from runpy import (  # noqa: PLC0415  # Lazy test-only import.
                run_path,
            )

            helper = (
                Path(__file__).resolve().parents[2]
                / "tests"
                / "scripted_judge.py"
            )
            judge = run_path(str(helper))["ScriptedJudge"].from_file(script)
        asyncio.run(serve(judge))
        return
    if args.command == "ready":
        from backfire.ready import (  # noqa: PLC0415  # Lazy command import.
            main as ready,
        )

        raise SystemExit(ready())


if __name__ == "__main__":
    main()
