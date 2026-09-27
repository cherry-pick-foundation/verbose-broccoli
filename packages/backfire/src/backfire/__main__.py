import argparse
import asyncio


async def _unconfigured_judge(state, questions, *, deadline, record_file=None):
    # T018 replaces this placeholder with the in-process judge.
    raise RuntimeError("backend_not_configured: the judge is not implemented yet")


def main() -> None:
    parser = argparse.ArgumentParser(prog="backfire")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("serve-mcp", help="Serve MCP over stdio")
    subcommands.add_parser("ready", help="Check backend readiness")
    args = parser.parse_args()
    if args.command == "serve-mcp":
        from backfire.server import serve

        asyncio.run(serve(_unconfigured_judge))
        return
    parser.error(f"{args.command}: not implemented yet")


if __name__ == "__main__":
    main()
