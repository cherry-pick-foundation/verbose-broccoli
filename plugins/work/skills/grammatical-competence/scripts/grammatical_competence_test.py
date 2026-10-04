import asyncio
from contextlib import asynccontextmanager
import hashlib
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

from wiki_consistency import evidence
from wiki_consistency.instance import instance_path
from wiki_consistency.instance import read_metadata
from wiki_consistency.instance import revisions

sys.path.insert(0, str(Path(__file__).parent))
import grammatical_competence as profile

REVISION = "20260930T000000000000Z"
INVENTORY = "inventories/inventory.qmd"
ROWS = [
    ("ID", "Label", "Type", "Level", "Statement", "Examples", "Tier"),
    ("keep", "Keep", "Group", " A1 ", "Shows support.", "One.\nTwo.", "N/A"),
    ("drop", "Drop", "Group", "A1", "Shows contradiction.", "Drop.", None),
    ("silent", "Silent", "Group", "A2", "Unsupported.", "Silent.", None),
    ("accept", "Accept", "Group", "A2", "Needs review.", "Accept.", None),
    ("reject", "Reject", "Group", "A2", "Also needs review.", "Reject.", None),
    ("wide", "Range", "Two  words", "B1", "Wide range.", "Wide.", "2"),
    ("small", "Range", "Two words", "A2", "Small range.", "Small.", "1"),
    ("alone", "Alone", "Group", "B2", "Only tier.", "Alone.", "1"),
]
PAGE = {
    "title": "Synthetic inventory",
    "summary": "An inventory for tests.",
    "topics": ["Teaching materials"],
    "sources": [{"id": "inventory-source", "revision": REVISION}],
    "inventory": {
        "sheet": "Items",
        "columns": {"id": "ID", "label": ["Label", "Type"], "level": "Level"}
        | {"statement": "Statement", "examples": "Examples", "family": "Tier"},
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
    f"record --inventory {INVENTORY} --name sample "
    "--title 'Synthetic material' --summary 'Synthetic profile.' "
    "--proposer 'test agent, test model, max'"
)


def _run(command):
    return profile.main(
        ["--wiki", "synthetic", "--run", "run"] + shlex.split(command)
    )


def _bag(root, source, name, content, revision=REVISION):
    bag = root / "raw/files" / source / revision
    bag.mkdir(parents=True)
    (bag / name).write_bytes(content)
    bagit.make_bag(
        str(bag),
        bag_info={"External-Identifier": source, "Admission-Time": revision},
    )


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
            "items": k,
        }
        for t, k in rows
    ]
    (run / "proposals.jsonl").write_text(
        "".join(f"{json.dumps(r)}\n" for r in rows)
    )


@pytest.fixture
def vault(tmp_path, monkeypatch):
    """Set up a synthetic vault with an inventory and a one-line material."""
    for name in ("DATA", "STATE", "CACHE"):
        monkeypatch.setenv(f"XDG_{name}_HOME", str(tmp_path / name.lower()))
    root = instance_path("synthetic", os.environ)
    (root / "wiki/inventories").mkdir(parents=True)
    book = Workbook()
    book.active.title = "Items"
    for row in ROWS:
        book.active.append(row)
    book.save(tmp_path / "inventory.xlsx")
    _bag(
        root,
        "inventory-source",
        "inventory.xlsx",
        (tmp_path / "inventory.xlsx").read_bytes(),
    )
    _bag(
        root,
        "material-source",
        "material.txt",
        b"First sentence. Second sentence.",
    )
    front = yaml.safe_dump(PAGE, sort_keys=False)
    (root / "wiki" / INVENTORY).write_text(
        f"---\n{front}---\n\nSynthetic inventory."
    )
    return root


@pytest.fixture
def jev(monkeypatch):
    stub = SimpleNamespace(modes=[], calls=[], reply=lambda _: REPLY)

    @asynccontextmanager
    async def server(*mode):
        stub.modes.append(mode)
        yield None

    async def verify(_, arguments):
        stub.calls.append(arguments)
        return stub.reply(arguments)

    monkeypatch.setattr(profile, "_jev", server)
    monkeypatch.setattr(profile, "_verify", verify)
    return stub


def test_check_sorts_and_record_lists_unclear_items(vault, jev, capsys):
    before = _snapshot(vault)
    assert _run(f"inventory --inventory {INVENTORY}") == 0
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    tsv = (run / "inventory.tsv").read_text().splitlines()
    assert tsv[0] == "1\tA1\tKeep / Group\tShows support."
    _proposals(run, ("First   sentence.", [5, 1, 2, 3, 4]))
    capsys.readouterr()
    assert _run(f"check --inventory {INVENTORY}") == 1  # One result is unknown.
    report = json.loads(capsys.readouterr().out)
    assert (report["calls"], report["tokens"], report["invalid"]) == (1, 5, 1)
    assert jev.modes == [()]
    (call,) = jev.calls
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

    assert not (run / "review.md").exists()

    assert _run(RECORD) == 0
    (row,) = _jsonl(vault / "wiki/profiles/sample.jsonl")
    page = (vault / "wiki/profiles/sample.qmd").read_text()
    front = yaml.safe_load(page.split("---\n", 2)[1])
    assert row == {
        "n": 1,
        "source": "material-source",
        "part": "Unit 1",
        "text": "First sentence.",
        "items": ["keep"],
        "unclear": ["accept", "reject"],
    }
    assert front["profile"] == {
        "inventory": f"../{INVENTORY}",
        "data": "sample.jsonl",
        "proposer": "test agent, test model, max",
        "checker": "synthetic stub",
        "counts": {"sentences": 1, "kept": 1, "dropped": 2, "unclear": 2},
    }
    assert front["sources"] == [
        {"id": "material-source", "revision": REVISION},
        {"id": "inventory-source", "revision": REVISION},
    ]
    assert _snapshot(vault) == before


@pytest.mark.usefixtures("vault")
def test_refuses_absent_sentence_and_unknown_key(jev, capsys):
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    # The Korean sentence is also absent from the synthetic source.
    rows = (
        ("Not extracted.", [1]),
        ("First sentence.", [99]),
        ("\uccab \ubb38\uc7a5.", [1]),
    )
    _proposals(run, *rows)
    assert _run(f"check --inventory {INVENTORY}") == 1
    assert not (run / "checks.jsonl").exists() and not jev.calls
    err = capsys.readouterr().err
    assert "proposal 1: sentence is absent" in err
    assert "proposal 2: item key is not in the inventory" in err
    assert "proposal 3: sentence is absent" in err


@pytest.mark.usefixtures("vault")
def test_failure_stops_the_run_and_a_rerun_resumes(jev, capsys):
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    _proposals(run, ("First sentence.", [1]), ("Second sentence.", [1]))
    ok = {"results": [{"verdict": "verified", "action": "auto"}]}

    def failing(_):
        if len(jev.calls) == 2:
            raise RuntimeError("provider failed")
        return ok

    jev.reply = failing
    assert _run(f"check --inventory {INVENTORY}") == 2
    assert "row 2: provider failed" in capsys.readouterr().err
    checks = run / "checks.jsonl"
    assert [c["row"] for c in _jsonl(checks)] == [1]
    with checks.open("a") as stream:
        stream.write('{"row": 2')  # A torn line from a killed run.
    jev.reply = lambda _: ok
    assert _run(f"check --inventory {INVENTORY}") == 0
    sent = [c["evidence"].split("\n")[0][10:] for c in jev.calls]
    assert sent == ["First sentence.", "Second sentence.", "Second sentence."]
    assert [c["row"] for c in _jsonl(checks)] == [1, 2]


@pytest.mark.usefixtures("vault")
def test_budget_refusal_happens_before_any_write(monkeypatch):
    monkeypatch.setattr(profile, "LIMIT", 1)
    assert _run(f"inventory --inventory {INVENTORY}") == 2
    assert not (profile._run_dir("run") / "inventory.tsv").exists()


def test_verify_reads_real_tool_results():
    def session(is_error, text):
        async def call_tool(*_):
            content = [TextContent(type="text", text=text)]
            return CallToolResult(content=content, is_error=is_error)

        return SimpleNamespace(call_tool=call_tool)

    reply = asyncio.run(profile._verify(session(False, json.dumps(REPLY)), {}))
    assert reply == REPLY
    with pytest.raises(ValueError, match="jev-mcp verification failed"):
        asyncio.run(
            profile._verify(session(True, "backend_not_configured"), {})
        )


@pytest.mark.usefixtures("vault")
def test_record_sorts_stored_results_again_at_a_threshold(jev):
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    _proposals(run, ("First sentence.", [1, 2, 3]))
    jev.reply = lambda _: {
        "provider": "synthetic",
        "model": "stub",
        "results": [
            {"verdict": "verified", "action": "review", "confidence": 0.6},
            {"verdict": "verified", "action": "review", "confidence": 0.4},
            {"verdict": "unsupported", "action": "review", "confidence": 0.7},
        ],
    }
    assert _run(f"check --inventory {INVENTORY}") == 0
    assert _run(f"{RECORD} --auto-accept 0.5") == 0
    root = instance_path("synthetic", os.environ)
    (row,) = _jsonl(root / "wiki/profiles/sample.jsonl")
    assert (row["items"], row["unclear"]) == (["keep"], ["drop"])
    page = (root / "wiki/profiles/sample.qmd").read_text()
    profile_block = yaml.safe_load(page.split("---\n")[1])["profile"]
    assert profile_block["auto_accept"] == 0.5
    counts = {"sentences": 1, "kept": 1, "dropped": 1, "unclear": 1}
    assert profile_block["counts"] == counts


@pytest.mark.usefixtures("vault")
def test_a_tier_family_is_one_item(jev):
    assert _run(f"inventory --inventory {INVENTORY}") == 0
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    tsv = (run / "inventory.tsv").read_text().splitlines()
    assert [line.split("\t")[0] for line in tsv] == list("1234578")
    assert tsv[5:] == [
        "7\tA2/B1\tRange / Two words\tSmall range.; Wide range.",
        "8\tB2\tAlone / Group\tOnly tier.",
    ]
    _proposals(run, ("First sentence.", [6]))
    assert _run(f"check --inventory {INVENTORY}") == 1
    _proposals(run, ("First sentence.", [7]))
    jev.reply = lambda _: {
        "results": [{"verdict": "verified", "action": "auto"}]
    }
    assert _run(f"check --inventory {INVENTORY}") == 0
    (call,) = jev.calls
    assert call["claims"] == [
        "First sentence. shows Range / Two words: Small range.; Wide range."
    ]
    assert call["evidence"].endswith(
        "small\nRange / Two words\nSmall range.; Wide range.\nSmall.\nWide."
    )
    assert _run(RECORD) == 0
    root = instance_path("synthetic", os.environ)
    (row,) = _jsonl(root / "wiki/profiles/sample.jsonl")
    assert row["items"] == ["small"]


@pytest.mark.usefixtures("vault")
def test_map_checks_sections_without_hangul_and_records_them(
    jev, capsys, monkeypatch
):
    root = instance_path("synthetic", os.environ)
    reference = {
        "title": "Synthetic reference",
        "summary": "A reference for tests.",
        "topics": ["Teaching materials"],
        "sources": [{"id": "reference-source", "revision": REVISION}],
        "reference": {"text": f"../../text/reference-source/{REVISION}.qmd"},
    }
    (root / "wiki/references").mkdir()
    front = yaml.safe_dump(reference, sort_keys=False)
    (root / "wiki/references/reference.qmd").write_text(f"---\n{front}---\n")
    # The third line is Korean, escaped, so this file holds no Hangul.
    lines = (
        "# Unit 1",
        "Support here.",
        "\ud55c\uad6d\uc5b4",
        "# Unit 2",
        "Else.",
    )
    _bag(root, "reference-source", "reference.txt", "\n".join(lines).encode())
    evidence.convert(
        root,
        "synthetic",
        profile.roots(os.environ)["cache"],
        {"reference-source": revisions(root)["reference-source"]},
    )
    retained = evidence.read(root, "reference-source", REVISION)
    offset = retained["first_line"] - 1
    run = profile._run_dir("run")
    run.mkdir(parents=True)
    index = (
        f"Unit 1\t{offset + 1}\t{offset + 3}\tTitle\n"
        f"Unit 2\t{offset + 4}\t{offset + 5}\n"
        f"Past the end\t{offset + 4}\t{offset + 9}\n"
    )
    (run / "sections.tsv").write_text(index)
    mapping = "map --inventory inventories/inventory.qmd "
    mapping += "--reference references/reference.qmd"

    def rows(*found):
        text = "".join(
            json.dumps({"item": k, "sections": s}) + "\n" for k, s in found
        )
        (run / "mappings.jsonl").write_text(text)

    rows((6, []), (1, ["Unit 1"] * 4), (1, ["Unit 3"]), (1, ["Past the end"]))
    assert _run(mapping) == 1
    err = capsys.readouterr().err
    assert "mapping 1: item key is not in the inventory" in err
    assert "mapping 2: more than three sections" in err
    assert "mapping 3: section is not in the index or has Hangul" in err
    assert "mapping 4: section lines are outside the text" in err
    assert "must list every inventory key exactly once" in err
    limit = profile.SECTION
    monkeypatch.setattr(profile, "SECTION", 5)
    rows((1, ["Unit 2"]))
    assert _run(mapping) == 1
    assert "mapping 1: section is over 5 characters" in capsys.readouterr().err
    monkeypatch.setattr(profile, "SECTION", limit)
    assert not jev.calls

    others = [(key, []) for key in (2, 3, 4, 5, 7, 8)]
    rows((2, []), (1, ["Unit 1", "Unit 2"]), (2, []), *others[2:])
    assert _run(mapping) == 1  # Key 2 twice, key 3 missing.
    assert "exactly once" in capsys.readouterr().err
    rows((1, ["Unit 1", "Unit 2"]), *others)
    jev.reply = lambda _: {
        "provider": "synthetic",
        "model": "stub",
        "results": [
            {"verdict": "verified", "action": "auto"},
            {"verdict": "verified", "action": "review"},
        ],
    }
    assert _run(mapping) == 0
    (call,) = jev.calls
    assert jev.modes == [()]
    assert call["claims"][0] == (
        "Synthetic reference, section Unit 1, explains Keep / Group: "
        "Shows support."
    )
    assert call["evidence"] == (
        "Item keep: Keep / Group\nShows support.\nOne.\nTwo.\n\n"
        "Section Unit 1:\n# Unit 1\nSupport here.\n\n"
        "Section Unit 2:\n# Unit 2\nElse."
    )
    record = RECORD.replace("--name sample", "--name inventory--reference")
    record += " --reference references/reference.qmd"
    rows((1, ["Unit 1", "Unit 2"]), *others[:-1])
    assert _run(record) == 1
    assert "exactly once" in capsys.readouterr().err
    rows((1, ["Unit 1", "Unit 2"]), *others)
    assert _run(record) == 0
    data = _jsonl(root / "wiki/mappings/inventory--reference.jsonl")
    assert data == [
        {
            "item": "keep",
            "sections": [
                {"label": "Unit 1", "lines": [offset + 1, offset + 3]}
            ],
            "unclear": [{"label": "Unit 2", "lines": [offset + 4, offset + 5]}],
        },
    ] + [
        {"item": item, "sections": [], "unclear": []}
        for item in ("drop", "silent", "accept", "reject", "small", "alone")
    ]
    page = (root / "wiki/mappings/inventory--reference.qmd").read_text()
    front, problems = read_metadata(
        root, "wiki/mappings/inventory--reference.qmd"
    )
    assert not problems
    assert "[reference](../references/reference.qmd)" in page
    assert front["mapping"] == {
        "inventory": f"../{INVENTORY}",
        "reference": "../references/reference.qmd",
        "data": "inventory--reference.jsonl",
        "proposer": "test agent, test model, max",
        "checker": "synthetic stub",
        "counts": {"items": 7, "kept": 1, "dropped": 0, "unclear": 1},
    }
    assert front["sources"] == [
        {"id": "inventory-source", "revision": REVISION},
        {"id": "reference-source", "revision": REVISION},
    ]


@pytest.mark.usefixtures("vault")
def test_record_unchecked_keeps_every_valid_proposal(jev, capsys):
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    _proposals(run, ("First sentence.", [2, 1, 1]), ("Not extracted.", [1]))
    assert _run(f"{RECORD} --unchecked") == 1
    assert "proposal 2: sentence is absent" in capsys.readouterr().err
    root = instance_path("synthetic", os.environ)
    assert not (root / "wiki/profiles").exists()
    _proposals(run, ("First sentence.", [2, 1, 1]))
    assert _run(f"{RECORD} --unchecked") == 0
    assert not jev.calls and not (run / "checks.jsonl").exists()
    (row,) = _jsonl(root / "wiki/profiles/sample.jsonl")
    assert (row["items"], row["unclear"]) == (["keep", "drop"], [])
    page = (root / "wiki/profiles/sample.qmd").read_text()
    block = yaml.safe_load(page.split("---\n")[1])["profile"]
    assert block["checker"] == "none"
    counts = {"sentences": 1, "kept": 2, "dropped": 0, "unclear": 0}
    assert block["counts"] == counts


def test_inherited_inventory_and_generated_checker_override(vault, jev):
    defaults = dict(PAGE)
    defaults["inventory"] = {**PAGE["inventory"], "claim": "Ancestor {text}"}
    (vault / "wiki/_metadata.yml").write_text(yaml.safe_dump(defaults))
    (vault / "wiki/inventories/_metadata.yml").write_text(
        yaml.safe_dump(
            {
                "inventory": {
                    "claim": "Directory {text}",
                    "columns": {"level": "Level"},
                },
                "topics": ["Teaching materials", "Synthetic topic"],
            }
        )
    )
    (vault / "wiki" / INVENTORY).write_text(
        '---\ninventory:\n  claim: "Page {text} {label} {statement}"\n'
        "---\nInventory body.\n"
    )
    metadata, entries = profile._inventory(vault, INVENTORY)
    assert entries[1]["id"] == "keep"
    assert metadata["topics"] == ["Teaching materials", "Synthetic topic"]
    assert metadata["inventory"]["claim"].startswith("Page")
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    _proposals(
        run,
        ("First sentence.", [1]),
        ("Second sentence.", []),
        ("First sentence.", [1]),
    )
    original = (run / "proposals.jsonl").read_bytes()
    (vault / "wiki/profiles").mkdir()
    (vault / "wiki/profiles/_metadata.yml").write_text(
        yaml.safe_dump(
            {
                "profile": {
                    "inventory": f"../{INVENTORY}",
                    "checker": "Inherited checker",
                    "custom": {"keep": True},
                },
            }
        )
    )
    assert _run(f"{RECORD} --unchecked") == 0
    front, problems = read_metadata(vault, "wiki/profiles/sample.qmd")
    assert not problems
    assert front["profile"]["checker"] == "none"
    assert front["profile"]["custom"] == {"keep": True}
    assert (
        f"[inventory](../{INVENTORY})"
        in (vault / "wiki/profiles/sample.qmd").read_text()
    )
    rows = _jsonl(vault / "wiki/profiles/sample.jsonl")
    assert [r["text"] for r in rows] == [
        "First sentence.",
        "Second sentence.",
        "First sentence.",
    ]
    assert [r["items"] for r in rows] == [["keep"], [], ["keep"]]
    assert [r["n"] for r in rows] == [1, 2, 3]
    assert (run / "proposals.jsonl").read_bytes() == original
    assert not jev.calls


def test_retained_pdf_reuse_pins_revision_and_exact_extraction(
    vault, monkeypatch
):
    _bag(vault, "retained-source", "book.pdf", b"synthetic PDF payload")
    path = vault / f"text/retained-source/{REVISION}.qmd"
    path.parent.mkdir(parents=True)
    front = {
        "source-id": "retained-source",
        "revision": REVISION,
        "sha256": hashlib.sha256(b"synthetic PDF payload").hexdigest(),
        "checked-against-original": True,
    }
    path.write_text(
        "---\n"
        + yaml.safe_dump(front)
        + "---\nFull retained sentence.\nUnlocated sentinel.\n"
    )
    before = path.read_bytes()

    def no_conversion(*unused_args, **unused_kwargs):
        raise AssertionError("existing retained source must be reused")

    monkeypatch.setattr(profile.evidence, "convert", no_conversion)
    assert _run("extract --source retained-source") == 0
    run = profile._run_dir("run")
    assert (
        run / "text/retained-source.txt"
    ).read_text() == "Full retained sentence.\nUnlocated sentinel.\n"
    receipt = json.loads((run / "extractions.json").read_text())[
        "retained-source"
    ]
    assert receipt["checked-against-original"] is None
    assert "missing or stale original review evidence" in receipt["problems"]
    assert "missing locator evidence" in receipt["problems"]
    _bag(
        vault,
        "retained-source",
        "book.pdf",
        b"new synthetic PDF payload",
        "20261004T000000000000Z",
    )
    (run / "proposals.jsonl").write_text(
        json.dumps(
            {
                "source": "retained-source",
                "part": "Unit 1",
                "text": "Full retained sentence.",
                "items": [],
            }
        )
        + "\n"
    )
    assert _run(f"{RECORD} --unchecked") == 0
    metadata, problems = read_metadata(vault, "wiki/profiles/sample.qmd")
    assert not problems
    assert metadata["sources"][0] == {
        "id": "retained-source",
        "revision": REVISION,
    }
    assert _run("extract --source retained-source") == 0
    assert path.read_bytes() == before
    path.write_bytes(before + b"Correction.\n")
    assert _run(f"{RECORD} --unchecked") == 2


def test_legacy_run_refuses_without_touching_paid_results(vault, capsys):
    run = profile._run_dir("run")
    (run / "text").mkdir(parents=True)
    (run / "text/material-source.txt").write_text("First sentence.")
    _proposals(run, ("First sentence.", []))
    checks = b'{"row": 1, "provider": null, "results": []}\n'
    (run / "checks.jsonl").write_bytes(checks)
    assert _run(f"{RECORD} --unchecked") == 2
    assert "provenance" in capsys.readouterr().err
    assert _run("extract --source material-source") == 2
    assert (run / "checks.jsonl").read_bytes() == checks
    assert not (vault / "wiki/profiles/sample.qmd").exists()


@pytest.mark.parametrize(
    "target",
    [
        "../../outside.qmd",
        "../../text/link/revision.qmd",
        "../../text/source/link.qmd",
        "../../text/link/../source/link.qmd",
    ],
)
def test_reference_rejects_escaping_and_symlink_paths(vault, tmp_path, target):
    outside = tmp_path / "outside.qmd"
    outside.write_text("Forbidden bytes.")
    (vault / "text/source").mkdir(parents=True)
    (vault / "text/link").symlink_to(tmp_path, target_is_directory=True)
    (vault / "text/source/link.qmd").symlink_to(outside)
    reference = {**PAGE, "reference": {"text": target}}
    (vault / "wiki/references").mkdir()
    (vault / "wiki/references/reference.qmd").write_text(
        "---\n" + yaml.safe_dump(reference) + "---\n"
    )
    args = SimpleNamespace(reference="references/reference.qmd")
    with pytest.raises(ValueError, match="text/|symlink"):
        profile._sections(vault, args, profile._run_dir("run"))


def test_metadata_problem_keeps_source_and_line(vault):
    (vault / "wiki/inventories/_metadata.yml").write_text("inventory: [\n")
    with pytest.raises(ValueError, match=r"wiki/inventories/_metadata.yml:\d+"):
        profile._page(vault, INVENTORY)


def test_empty_source_refuses_and_empty_profile_stays_unchecked(vault, jev):
    _bag(vault, "empty-source", "empty.txt", b"123\n")
    before = _snapshot(vault)
    assert _run("extract --source empty-source") == 2
    run = profile._run_dir("run")
    assert not (run / "text/empty-source.txt").exists()
    run.mkdir(parents=True, exist_ok=True)
    _proposals(run)
    assert _run(f"{RECORD} --unchecked") == 0
    front, problems = read_metadata(vault, "wiki/profiles/sample.qmd")
    assert not problems and front["profile"]["checker"] == "none"
    assert front["profile"]["counts"] == {
        "sentences": 0,
        "kept": 0,
        "dropped": 0,
        "unclear": 0,
    }
    assert (vault / "wiki/profiles/sample.jsonl").read_bytes() == b""
    assert not jev.calls and _snapshot(vault) == before


def test_korean_proposal_is_checked_when_present_in_source(vault, jev):
    text = "\uccab \ubb38\uc7a5."
    _bag(vault, "korean-source", "synthetic.txt", text.encode())
    assert _run("extract --source korean-source") == 0
    run = profile._run_dir("run")
    proposal = {
        "source": "korean-source",
        "part": "synthetic",
        "text": text,
        "items": [1],
    }
    (run / "proposals.jsonl").write_text(json.dumps(proposal) + "\n")
    jev.reply = lambda _: {
        "results": [{"verdict": "verified", "action": "auto"}]
    }
    assert _run(f"check --inventory {INVENTORY}") == 0
    assert text in jev.calls[0]["evidence"]
    assert set(jev.calls[0]) == {"claims", "evidence"}


@pytest.mark.parametrize("text", ["not JSON", "[]", "{}"])
def test_verify_rejects_malformed_results(text):
    async def call_tool(*unused_args):
        return CallToolResult(content=[TextContent(type="text", text=text)])

    with pytest.raises(ValueError, match="jev-mcp verification failed"):
        asyncio.run(profile._verify(SimpleNamespace(call_tool=call_tool), {}))


def test_verification_launcher_uses_gated_proxy(monkeypatch):
    launches = []

    @asynccontextmanager
    async def transport(server):
        launches.append(server)
        yield None, None

    class Client:
        def __init__(self, *unused):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *unused):
            pass

        async def initialize(self):
            pass

    monkeypatch.setattr(profile, "stdio_client", transport)
    monkeypatch.setattr(profile, "ClientSession", Client)

    async def launch():
        async with profile._jev():
            pass

    asyncio.run(launch())
    assert launches[0].command == "uv"
    assert launches[0].args == [
        "--directory",
        str(profile.PROXY),
        "run",
        "--frozen",
        "--offline",
        "--no-sync",
        "jev-mcp",
    ]


@pytest.mark.usefixtures("vault")
def test_text_usage_is_retained_without_inventing_token_counts(jev, capsys):
    assert _run("extract --source material-source") == 0
    run = profile._run_dir("run")
    _proposals(run, ("First sentence.", [1]))
    usage = {"input_tokens": "synthetic", "output_tokens": {"nested": 1}}
    jev.reply = lambda _: {
        "results": [{"verdict": "verified", "action": "auto"}],
        "usage": usage,
    }
    capsys.readouterr()
    assert _run(f"check --inventory {INVENTORY}") == 0
    assert json.loads(capsys.readouterr().out)["tokens"] == 0
    assert _jsonl(run / "checks.jsonl")[0]["usage"] == usage
