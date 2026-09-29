"""Call one backfire tool through the repository package's MCP server.

Usage: bf.py <tool> <args.json> [<out.json>]
"""
import asyncio, json, sys
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path("/home/choi-eunchang/workspaces/verbose-broccoli/feature-turborepo/packages/backfire")

async def main(tool, args_path, out_path):
    args = json.loads(Path(args_path).read_text())
    params = StdioServerParameters(command=str(ROOT / ".venv/bin/python"), args=["-m", "backfire", "serve-mcp"], cwd=str(ROOT))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool(tool, args)
            text = "".join(getattr(b, "text", "") for b in res.content)
            try:
                value = json.loads(text)
                out = json.dumps(value, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                out = text
            if out_path:
                Path(out_path).write_text(out)
            print(out)

asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
