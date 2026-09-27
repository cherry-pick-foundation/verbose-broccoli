import argparse
import asyncio
import os


def main() -> None:
    parser = argparse.ArgumentParser(prog="backfire")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("serve-mcp", help="Serve MCP over stdio")
    subcommands.add_parser("ready", help="Check backend readiness")
    args = parser.parse_args()
    if args.command == "serve-mcp":
        from backfire.judge import judge
        from backfire.server import serve

        if (script := os.environ.get("BACKFIRE_TEST_JUDGE_SCRIPT")) is not None:
            from pathlib import Path
            from runpy import run_path

            helper = Path(__file__).resolve().parents[2] / "tests" / "scripted_judge.py"
            judge = run_path(str(helper))["ScriptedJudge"].from_file(script)
        asyncio.run(serve(judge))
        return
    parser.error(f"{args.command}: not implemented yet")


if __name__ == "__main__":
    main()
