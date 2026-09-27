"""Capture jev-mcp 0.9.0 on Node using only synthetic local judgments.

Run from the repository root with the required Node on PATH:
uv run --project packages/backfire --frozen --offline --no-sync python -m
backfire_tools.acceptance.capture_upstream

Only the source download and npm installation need network access. The source
is built unchanged in a temporary directory, never from a local checkout.
"""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from tempfile import TemporaryDirectory
from urllib.request import urlopen

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.exceptions import MCPError

from backfire_tools.acceptance.scripted_endpoint import scripted_endpoint

REVISION = "a1fcc1e47fc696614f081e23a66ff48a890f22fd"
SOURCE_URL = f"https://codeload.github.com/jkudish/jev-mcp/tar.gz/{REVISION}"
FIXTURES = Path(__file__).resolve().parents[5] / "scripts/backfire/fixtures"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_source(directory):
    archive = directory / "source.tar.gz"
    with urlopen(SOURCE_URL, timeout=60) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)
    with tarfile.open(archive) as source:
        source.extractall(directory, filter="data")
    return directory / f"jev-mcp-{REVISION}"


def wire(value):
    return value.model_dump(by_alias=True, exclude_unset=True)


async def capture_cases(source, node, cases):
    with scripted_endpoint() as (url, exchanges), anyio.fail_after(120):
        parameters = StdioServerParameters(
            command=node, args=["dist/index.js"], cwd=source,
            env={"JEV_PROVIDER": "compatible", "JEV_MCP_MAX_ATTEMPTS": "1",
                 "JEV_API_BASE_URL": url, "JEV_API_KEY": "synthetic-capture-key"},
        )
        async with stdio_client(parameters) as streams, ClientSession(*streams) as client:
            initialized = wire(await client.initialize())
            if initialized["serverInfo"] != {"name": "jev-mcp", "version": "0.9.0"}:
                raise ValueError("Unexpected upstream server identity.")
            tools = wire(await client.list_tools())
            captured = []
            for case in cases:
                start = len(exchanges)
                name = "jev_" + case["tool"].removeprefix("backfire_")
                try:
                    result = {"result": wire(await client.call_tool(name, case["arguments"]))}
                except MCPError as error:
                    # Transport failures must not become accepted tool-error fixtures.
                    if error.error.code not in (-32600, -32601, -32602, -32603):
                        raise
                    result = {"error": wire(error.error)}
                captured.append({
                    "id": case["id"], "tool": name, "arguments": case["arguments"],
                    "judgments": exchanges[start:], **result,
                })
    return initialized, tools, captured


def capture(cases_path, output):
    cases = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines()]
    if not cases or len({case["id"] for case in cases}) != len(cases):
        raise ValueError("Expected non-empty cases with unique ids.")
    node, npm = shutil.which("node"), shutil.which("npm")
    if not node or not npm:
        raise ValueError("Capture requires Node 22 or later and npm on PATH.")
    node_version = subprocess.check_output([node, "--version"], text=True).strip()
    if int(node_version.removeprefix("v").split(".")[0]) < 22:
        raise ValueError("Capture requires Node 22 or later.")
    npm_version = subprocess.check_output([npm, "--version"], text=True).strip()
    with TemporaryDirectory(prefix="backfire-upstream-") as temporary:
        directory = Path(temporary)
        source = fetch_source(directory)
        hashes = {name: sha256(source / name) for name in (
            "src/index.ts", "src/lib.ts", "src/provider.ts", "package.json", "package-lock.json",
        )}
        # A fresh HOME keeps npm away from the operator's credential/config files.
        env = {"PATH": os.environ["PATH"], "HOME": temporary}
        for arguments in (["ci", "--ignore-scripts"], ["run", "build"]):
            subprocess.run([npm, *arguments], cwd=source, env=env, check=True, timeout=300)
        if any(sha256(source / name) != digest for name, digest in hashes.items()):
            raise ValueError("Upstream build changed a captured source file.")
        initialized, tools, captured = asyncio.run(capture_cases(source, node, cases))
        metadata = {
            "source_url": SOURCE_URL, "revision": REVISION,
            "source_sha256": hashes, "archive_sha256": sha256(directory / "source.tar.gz"),
            "node": node_version, "npm": npm_version,
            "commands": ["npm ci --ignore-scripts", "npm run build", "node dist/index.js"],
            "environment": {"JEV_PROVIDER": "compatible", "JEV_MCP_MAX_ATTEMPTS": "1"},
            "initialize": initialized, "known_answers_sha256": sha256(cases_path),
            "case_count": len(captured),
            "judgment_count": sum(len(case["judgments"]) for case in captured),
            "answer_policy": "First Choice, Noul 0.875, middle Score; synthetic fidelity answers, not semantic expectations.",
        }
    output.mkdir(parents=True, exist_ok=True)
    for name, value in (("metadata.json", metadata), ("tools-list.json", tools)):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "cases.jsonl").write_text(
        "".join(json.dumps(case, ensure_ascii=False, separators=(",", ":")) + "\n" for case in captured),
        encoding="utf-8",
    )
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=FIXTURES / "known-answers-v1.jsonl")
    parser.add_argument("--output", type=Path, default=FIXTURES / "upstream-0.9.0")
    arguments = parser.parse_args()
    metadata = capture(arguments.cases, arguments.output)
    print(f"Captured {metadata['case_count']} cases and {metadata['judgment_count']} judgments in {arguments.output}")


if __name__ == "__main__":
    main()
