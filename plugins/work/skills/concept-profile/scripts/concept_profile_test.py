import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import shlex
import sys
from types import SimpleNamespace

import bagit
from mcp.types import CallToolResult
from mcp.types import TextContent
from openpyxl import Workbook
import pytest
import yaml

from wiki_consistency.instance import instance_path

sys.path.insert(0, str(Path(__file__).parent))
import concept_profile as profile

REVISION = "20260930T000000000000Z"
CATALOG = "catalogs/catalog.md"
ROWS = [
    ("ID", "Label", "Type", "Level", "Statement", "Examples"),
    ("keep", "Keep", "Group", " A1 ", "Shows support.", "One.\nTwo."),
    ("drop", "Drop", "Group", "A1", "Shows contradiction.", "Drop."),
    ("silent", "Silent", "Group", "A2", "Unsupported.", "Silent."),
    ("accept", "Accept", "Group", "A2", "Needs review.", "Accept."),
    ("reject", "Reject", "Group", "A2", "Also needs review.", "Reject."),
]
PAGE = {
    "title": "Synthetic catalog",
    "summary": "A catalog for tests.",
    "topics": ["Teaching materials"],
    "sources": [{"id": "catalog-source", "revision": REVISION}],
    "catalog": {
        "sheet": "Concepts",
        "columns": {"id": "ID", "label": ["Label", "Type"], "level": "Level"}
        | {"statement": "Statement", "examples": "Examples"},
        "claim": "{text} shows {label}: {statement}",
    },
}
REPLY = {
    "provider": "synthetic",
    "model": "stub",
    "usage": {"input_tokens": 3, "output_tokens": 2},
    "results": [
        {"verdict": "verified", "action": "auto"},
        {"verdict": "contradicted", "action": "auto"},
        {"verdict": "unsupported", "action": "auto"},
        {"verdict": "verified", "action": "review"},
        {"verdict": "unknown", "action": "review"},
    ],
}
RECORD = (
    f"record --catalog {CATALOG} --name sample --title 'Synthetic material' "
    "--summary 'Synthetic profile.' --proposer 'test agent, test model, max'"
)


def _run(command):
    return profile.main(
        ["--wiki", "synthetic", "--run", "run"] + shlex.split(command)
    )


def _bag(root, source, name, content):
    bag = root / "raw/files" / source / REVISION
    bag.mkdir(parents=True)
    (bag / name).write_bytes(content)
    bagit.make_bag(str(bag), bag_info={"External-Identifier": source})


def _jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def _snapshot(root):
    files = (root / "raw").rglob("*")
    return {p.relative_to(root): p.read_bytes() for p in files if p.is_file()}


def _proposals(run, *rows):
    rows = [
        {
            "source": "material-source",
            "part": "Unit 1",
            "text": t,
            "concepts": k,
        }
        for t, k in rows
    ]
    (run / "proposals.jsonl").write_text(
        "".join(f"{json.dumps(r)}\n" for r in rows)
    )


@pytest.fixture
def vault(tmp_path, monkeypatch):
    """Set up a synthetic vault with a catalog and a one-line material."""
    for name in ("DATA", "STATE", "CACHE"):
        monkeypatch.setenv(f"XDG_{name}_HOME", str(tmp_path / name.lower()))
    root = instance_path("synthetic", os.environ)
    (root / "wiki/catalogs").mkdir(parents=True)
    book = Workbook()
    book.active.title = "Concepts"
    for row in ROWS:
        book.active.append(row)
    book.save(tmp_path / "catalog.xlsx")
    _bag(
        root,
        "catalog-source",
        "catalog.xlsx",
        (tmp_path / "catalog.xlsx").read_bytes(),
    )
    _bag(
        root,
        "material-source",
        "material.txt",
        b"First sentence. Second sentence.",
    )
    front = yaml.safe_dump(PAGE, sort_keys=False)
    (root / "wiki" / CATALOG).write_text(
        f"---\n{front}---\n\nSynthetic catalog."
    )
    return root


@pytest.fixture
def backfire(monkeypatch):
    stub = SimpleNamespace(sessions=0, calls=[], reply=lambda _: REPLY)

    @asynccontextmanager
    async def server():
        stub.sessions += 1
        yield None

    async def verify(_, arguments):
        stub.calls.append(arguments)
        return stub.reply(arguments)

    monkeypatch.setattr(profile, "_backfire", server)
    monkeypatch.setattr(profile, "_verify", verify)
    return stub


def test_check_sorts_and_record_applies_the_review(vault, backfire, capsys):
    before = _snapshot(vault)
    assert _run(f"catalog --catalog {CATALOG}") == 0
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    tsv = (run / "catalog.tsv").read_text().splitlines()
    assert tsv[0] == "1\tA1\tKeep / Group\tShows support."
    _proposals(run, ("First   sentence.", [5, 1, 2, 3, 4]))
    capsys.readouterr()
    assert _run(f"check --catalog {CATALOG}") == 1  # One result is unknown.
    report = json.loads(capsys.readouterr().out)
    assert (report["calls"], report["tokens"], report["invalid"]) == (1, 5, 1)
    assert backfire.sessions == 1
    (call,) = backfire.calls
    assert (
        call["claims"][0]
        == "First sentence. shows Keep / Group: Shows support."
    )
    assert call["evidence"].startswith("Sentence: First sentence.\n\n")
    assert "keep\nKeep / Group\nShows support.\nOne.\nTwo." in call["evidence"]
    (check,) = _jsonl(run / "checks.jsonl")
    outcomes = [r["outcome"] for r in check["results"]]
    assert outcomes == ["kept", "dropped", "dropped", "unclear", "unclear"]
    assert (check["provider"], check["model"]) == ("synthetic", "stub")

    assert _run(RECORD) == 0
    (row,) = _jsonl(vault / "wiki/profiles/sample.jsonl")
    assert (row["concepts"], row["unclear"]) == (["keep"], ["accept", "reject"])
    sheet = run / "review.md"
    sheet.write_text(
        sheet.read_text().replace('[ ] 1 "accept"', '[x] 1 "accept"')
    )
    assert _run(f"{RECORD} --reviewed") == 0
    (row,) = _jsonl(vault / "wiki/profiles/sample.jsonl")
    page = (vault / "wiki/profiles/sample.md").read_text()
    front = yaml.safe_load(page.split("---\n", 2)[1])
    assert row == {
        "n": 1,
        "source": "material-source",
        "part": "Unit 1",
        "text": "First sentence.",
        "concepts": ["keep", "accept"],
        "unclear": [],
    }
    assert front["profile"] == {
        "catalog": f"../{CATALOG}",
        "data": "sample.jsonl",
        "proposer": "test agent, test model, max",
        "checker": "synthetic stub",
        "counts": {"sentences": 1, "kept": 2, "dropped": 3, "unclear": 0},
    }
    assert front["sources"] == [
        {"id": "material-source", "revision": REVISION},
        {"id": "catalog-source", "revision": REVISION},
    ]
    assert _snapshot(vault) == before


@pytest.mark.usefixtures("vault")
def test_refuses_absent_sentence_and_unknown_key(backfire, capsys):
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    rows = ("Not extracted.", [1]), ("First sentence.", [99]), ("첫 문장.", [1])
    _proposals(run, *rows)
    assert _run(f"check --catalog {CATALOG}") == 1
    assert not (run / "checks.jsonl").exists() and not backfire.calls
    err = capsys.readouterr().err
    assert "proposal 1: sentence is absent" in err
    assert "proposal 2: concept key is not in the catalog" in err
    assert "proposal 3: backfire takes English only, no Hangul" in err


@pytest.mark.usefixtures("vault")
def test_failure_stops_the_run_and_a_rerun_resumes(backfire, capsys):
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    _proposals(run, ("First sentence.", [1]), ("Second sentence.", [1]))
    ok = {"results": [{"verdict": "verified", "action": "auto"}]}

    def failing(_):
        if len(backfire.calls) == 2:
            raise RuntimeError("provider failed")
        return ok

    backfire.reply = failing
    assert _run(f"check --catalog {CATALOG}") == 2
    assert "row 2: provider failed" in capsys.readouterr().err
    checks = run / "checks.jsonl"
    assert [c["row"] for c in _jsonl(checks)] == [1]
    with checks.open("a") as stream:
        stream.write('{"row": 2')  # A torn line from a killed run.
    backfire.reply = lambda _: ok
    assert _run(f"check --catalog {CATALOG}") == 0
    sent = [c["evidence"].split("\n")[0][10:] for c in backfire.calls]
    assert sent == ["First sentence.", "Second sentence.", "Second sentence."]
    assert [c["row"] for c in _jsonl(checks)] == [1, 2]


@pytest.mark.usefixtures("vault")
def test_budget_refusal_happens_before_any_write(monkeypatch):
    monkeypatch.setattr(profile, "LIMIT", 1)
    assert _run(f"catalog --catalog {CATALOG}") == 2
    assert not (profile._run_dir("run") / "catalog.tsv").exists()


def test_verify_reads_real_tool_results():
    def session(is_error, text):
        async def call_tool(*_):
            content = [TextContent(type="text", text=text)]
            return CallToolResult(content=content, is_error=is_error)

        return SimpleNamespace(call_tool=call_tool)

    reply = asyncio.run(profile._verify(session(False, json.dumps(REPLY)), {}))
    assert reply == REPLY
    with pytest.raises(ValueError, match="backend_not_configured"):
        asyncio.run(
            profile._verify(session(True, "backend_not_configured"), {})
        )
