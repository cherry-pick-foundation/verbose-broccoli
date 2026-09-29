"""Classify items in batches with backfire_classify; resume from an existing result file."""
import asyncio, json, os, sys
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
ROOT = Path("/home/choi-eunchang/workspaces/verbose-broccoli/feature-turborepo/packages/backfire")
D = Path(__file__).parent
items_path, out_path = sys.argv[1:3]
BATCH = int(os.environ.get("BATCH", "8")); CONC = int(os.environ.get("CONC", "3"))
items = json.load(open(items_path))
classes = json.load(open(D / "classes.json"))
context = (D / os.environ.get("CONTEXT", "context.txt")).read_text()
purpose = os.environ.get("PURPOSE", "Select the change sites for a trial that moves this repository's TypeScript tooling from Deno to Node.js and Turborepo and its three Python packages into one uv workspace; only must_change sites will be edited.")
done = json.load(open(out_path)) if os.path.exists(out_path) else {}
sem = asyncio.Semaphore(CONC)
async def main():
    params = StdioServerParameters(command=str(ROOT / ".venv/bin/python"), args=["-m", "backfire", "serve-mcp"], cwd=str(ROOT))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            todo = [it for it in items if it["id"] not in done]
            batches = [todo[i:i+BATCH] for i in range(0, len(todo), BATCH)]
            async def one(batch):
                async with sem:
                    args = {"items": [{"id": it["id"], "text": it["text"][:2000]} for it in batch], "classes": classes, "purpose": purpose, "context": context}
                    for attempt in range(3):
                        res = await s.call_tool("backfire_classify", args)
                        text = "".join(getattr(b, "text", "") for b in res.content)
                        try:
                            value = json.loads(text)
                        except json.JSONDecodeError:
                            print("retry", batch[0]["id"], text[:100], flush=True); await asyncio.sleep(15); continue
                        for row in value.get("results", []):
                            done[row["id"]] = row
                        json.dump(done, open(out_path, "w"), indent=1, ensure_ascii=False)
                        print("ok", batch[0]["id"], len(value.get("results", [])), value.get("usage"), flush=True)
                        return
            await asyncio.gather(*(one(b) for b in batches))
asyncio.run(main())
