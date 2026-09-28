import json
import os
import signal
import socket
import zipfile

import pytest
from pptx import Presentation
from pptx.util import Inches

from wiki_consistency import evidence


def _docx_bytes(path):
    content_types = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''
    relationships = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
    document = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>Synthetic DOCX evidence</w:t></w:r></w:p><w:sectPr/></w:body>
</w:document>'''
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document)


def _pptx_bytes(path):
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    shape = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
    shape.text_frame.text = "Synthetic PPTX evidence"
    presentation.save(path)


def _pdf_bytes(stream):
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, value in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(value + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Root 1 0 R /Size {len(offsets)} >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


def _revision(instance, source_id, revision, filename, payload):
    bag = instance / "raw" / "files" / source_id / revision
    payload_path = bag / "data" / filename
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_bytes(payload)
    return {
        "kind": "files",
        "id": source_id,
        "revision": revision,
        "path": f"raw/files/{source_id}/{revision}",
    }


def _revisions(*items):
    return {item["id"]: [item] for item in items}


def _no_socket(*args, **kwargs):
    raise AssertionError("evidence conversion must not open a socket")


def test_convert_supported_files_and_pass_through(tmp_path, monkeypatch):
    instance = tmp_path / "instance"
    cache = tmp_path / "cache"
    instance.mkdir()
    docx = tmp_path / "source.docx"
    pptx = tmp_path / "source.pptx"
    _docx_bytes(docx)
    _pptx_bytes(pptx)

    items = [
        _revision(instance, "docx", "r1", docx.name, docx.read_bytes()),
        _revision(instance, "pptx", "r1", pptx.name, pptx.read_bytes()),
        _revision(
            instance,
            "pdf",
            "r1",
            "source.pdf",
            _pdf_bytes(b"BT /F1 12 Tf 72 72 Td (Synthetic PDF evidence) Tj ET"),
        ),
        _revision(instance, "text", "r1", "source.txt", b"Plain text evidence"),
        _revision(instance, "markdown", "r1", "source.md", b"# Markdown evidence\n"),
    ]
    monkeypatch.setattr(socket, "socket", _no_socket)

    result = evidence.convert(instance, "wiki-a", cache, _revisions(*items))

    assert result["converted"] == 5
    assert result["present"] == 0
    assert result["unreadable"] == []
    assert "Synthetic DOCX evidence" in evidence.read(cache, "wiki-a", "docx", "r1")["text"]
    assert "Synthetic PPTX evidence" in evidence.read(cache, "wiki-a", "pptx", "r1")["text"]
    assert "Synthetic PDF evidence" in evidence.read(cache, "wiki-a", "pdf", "r1")["text"]
    assert evidence.read(cache, "wiki-a", "text", "r1")["text"] == "Plain text evidence"
    assert evidence.read(cache, "wiki-a", "markdown", "r1")["text"] == "# Markdown evidence\n"
    assert {path.relative_to(cache).parts[0] for path in cache.rglob("*")} == {"wiki-evidence"}


def test_unreadable_revisions_record_the_reason(tmp_path):
    instance = tmp_path / "instance"
    cache = tmp_path / "cache"
    instance.mkdir()
    damaged = tmp_path / "damaged.docx"
    with zipfile.ZipFile(damaged, "w") as archive:
        archive.writestr("word/document.xml", "<broken>")
    items = [
        _revision(instance, "hwp", "r1", "unsupported.hwp", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
        _revision(
            instance,
            "image-pdf",
            "r1",
            "image.pdf",
            _pdf_bytes(b"q 0 0 1 rg 72 72 100 100 re f Q"),
        ),
        _revision(instance, "damaged", "r1", "damaged.docx", damaged.read_bytes()),
    ]

    result = evidence.convert(instance, "wiki-a", cache, _revisions(*items))

    reasons = {entry["id"]: entry["reason"] for entry in result["unreadable"]}
    assert reasons == {
        "hwp": "unsupported_format",
        "image-pdf": "empty_text",
        "damaged": "conversion_failed",
    }
    for source_id, reason in reasons.items():
        mark = cache / "wiki-evidence" / "wiki-a" / "markitdown-0.1.8" / source_id / "r1.unreadable.json"
        stored = json.loads(mark.read_text())
        assert stored["reason"] == reason
        assert isinstance(stored["detail"], str)
        assert evidence.read(cache, "wiki-a", source_id, "r1") == {"unreadable": reason}


def test_convert_never_rewrites_and_reads_unconverted_as_missing(tmp_path):
    instance = tmp_path / "instance"
    cache = tmp_path / "cache"
    instance.mkdir()
    item = _revision(instance, "source", "r1", "source.txt", b"first content")
    revisions = _revisions(item)

    assert evidence.convert(instance, "wiki-a", cache, revisions)["converted"] == 1
    target = cache / "wiki-evidence" / "wiki-a" / "markitdown-0.1.8" / "source" / "r1.md"
    original = target.read_bytes()
    item_path = instance / item["path"] / "data" / "source.txt"
    item_path.write_text("changed content")

    result = evidence.convert(instance, "wiki-a", cache, revisions)

    assert result["converted"] == 0
    assert result["present"] == 1
    assert target.read_bytes() == original
    with pytest.raises(LookupError):
        evidence.read(cache, "wiki-a", "missing", "r1")


def test_budget_is_checked_before_each_write(tmp_path):
    instance = tmp_path / "instance"
    cache = tmp_path / "cache"
    instance.mkdir()
    items = [
        _revision(instance, "a", "r1", "source.txt", b"alpha"),
        _revision(instance, "b", "r1", "source.txt", b"bravo"),
    ]

    with pytest.raises(ValueError, match="wiki-evidence.*budget"):
        evidence.convert(instance, "wiki-a", cache, _revisions(*items), budget_bytes=7)

    assert (cache / "wiki-evidence" / "wiki-a" / "markitdown-0.1.8" / "a" / "r1.md").exists()
    assert not (cache / "wiki-evidence" / "wiki-a" / "markitdown-0.1.8" / "b" / "r1.md").exists()
    assert not list(cache.rglob("*.wiki-consistency-tmp"))


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_interrupted_write_cleans_temporary_files(tmp_path, monkeypatch, signum):
    instance = tmp_path / "instance"
    cache = tmp_path / "cache"
    instance.mkdir()
    item = _revision(instance, "source", "r1", "source.txt", b"source evidence")

    def interrupt_rename(*args):
        os.kill(os.getpid(), signum)

    monkeypatch.setattr(evidence.os, "rename", interrupt_rename)
    with pytest.raises(SystemExit):
        evidence.convert(instance, "wiki-a", cache, _revisions(item))

    assert not list(cache.rglob("*.wiki-consistency-tmp"))
    assert not (cache / "wiki-evidence" / "wiki-a" / "markitdown-0.1.8" / "source" / "r1.md").exists()


def test_failed_rename_cleans_temporary_files(tmp_path, monkeypatch):
    instance = tmp_path / "instance"
    cache = tmp_path / "cache"
    instance.mkdir()
    item = _revision(instance, "source", "r1", "source.txt", b"source evidence")

    def fail_rename(*args):
        raise OSError("synthetic rename failure")

    monkeypatch.setattr(evidence.os, "rename", fail_rename)
    with pytest.raises(OSError, match="synthetic rename failure"):
        evidence.convert(instance, "wiki-a", cache, _revisions(item))

    assert not list(cache.rglob("*.wiki-consistency-tmp"))


def test_next_convert_removes_abandoned_temporary_files(tmp_path):
    instance = tmp_path / "instance"
    cache = tmp_path / "cache"
    instance.mkdir()
    stale = cache / "wiki-evidence" / ".abandoned.wiki-consistency-tmp"
    stale.parent.mkdir(parents=True)
    stale.write_text("partial")

    evidence.convert(instance, "wiki-a", cache, {})

    assert not stale.exists()
