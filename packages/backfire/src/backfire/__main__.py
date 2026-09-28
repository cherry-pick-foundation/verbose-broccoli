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
        # Lazy command import.
        from backfire.judge import judge  # noqa: PLC0415

        # Lazy command import.
        from backfire.server import serve  # noqa: PLC0415

        if (script := os.environ.get("BACKFIRE_TEST_JUDGE_SCRIPT")) is not None:
            # Lazy test-only import.
            from pathlib import Path  # noqa: PLC0415

            # Lazy test-only import.
            from runpy import run_path  # noqa: PLC0415

            helper = (
                Path(__file__).resolve().parents[2]
                / "tests"
                / "scripted_judge.py"
            )
            judge = run_path(str(helper))["ScriptedJudge"].from_file(script)
        asyncio.run(serve(judge))
        return
    if args.command == "ready":
        # Lazy command import.
        from backfire.ready import main as ready  # noqa: PLC0415

        raise SystemExit(ready())


if __name__ == "__main__":
    main()
