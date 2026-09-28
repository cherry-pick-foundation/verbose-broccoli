"""Deterministic Cog generators for Wiki page and source metadata."""

from email.parser import Parser
from pathlib import Path
import re

from doc_regions.config import files

from wiki_consistency.instance import SPECIAL_PAGES, _metadata


def page_catalog(source_glob):
    root = Path.cwd().resolve()
    wiki = root / "wiki"
    rows = []
    for path in files(root, source_glob):
        relative = path.relative_to(root).as_posix()
        if relative in SPECIAL_PAGES:
            continue
        try:
            page_path = path.relative_to(wiki).as_posix()
        except ValueError as error:
            raise ValueError(
                f"page_catalog source is outside wiki/: {relative}"
            ) from error
        metadata, problems = _metadata(path.read_text(encoding="utf-8"))
        if problems:
            problem = problems[0]
            raise ValueError(
                f"{relative}:{problem['line']}: {problem['message']}"
            )
        rows.append((page_path, metadata["title"], metadata["summary"]))
    return "".join(
        f"- [{title}]({path}) — {summary}\n"
        for path, title, summary in sorted(rows)
    )


def _bag_info(path):
    return Parser().parsestr(path.read_text(encoding="utf-8"))


def _manifest(path):
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            raise ValueError(f"invalid SHA-256 manifest line in {path}")
        digest, payload = parts
        if payload.startswith("data/"):
            entries.append((payload.removeprefix("data/"), digest.lower()))
    if len(entries) != 1:
        raise ValueError(f"expected one payload entry in {path}")
    return entries[0]


def source_provenance(bag_info_glob, manifest_glob):
    root = Path.cwd().resolve()
    bag_infos = files(root, bag_info_glob)
    manifests = files(root, manifest_glob)
    info_by_parent = {path.parent: path for path in bag_infos}
    manifest_by_parent = {path.parent: path for path in manifests}
    if info_by_parent.keys() != manifest_by_parent.keys():
        raise ValueError(
            "bag-info and manifest source globs must name the same revisions"
        )

    revisions = []
    source_ids, kinds = set(), set()
    for bag_path in sorted(info_by_parent):
        parts = bag_path.relative_to(root).parts
        if len(parts) != 4 or parts[0] != "raw":
            raise ValueError(f"not a raw BagIt revision: {bag_path}")
        _, kind, source_id, revision = parts
        info = _bag_info(info_by_parent[bag_path])
        if info.get("External-Identifier") != source_id:
            raise ValueError(
                f"External-Identifier does not match {source_id}: {bag_path}"
            )
        modified = info.get("Source-Modified")
        oxum = info.get("Payload-Oxum")
        if not modified or not oxum or not oxum.split(".", 1)[0].isdigit():
            raise ValueError(
                f"missing Source-Modified or Payload-Oxum: {bag_path}"
            )
        name, digest = _manifest(manifest_by_parent[bag_path])
        source_ids.add(source_id)
        kinds.add(kind)
        revisions.append(
            (revision, modified, oxum.split(".", 1)[0], digest, name)
        )

    if len(source_ids) != 1 or len(kinds) != 1:
        raise ValueError("source_provenance must name revisions of one source")
    names = {revision[4] for revision in revisions}
    if len(names) != 1:
        raise ValueError("a source's payload name changed between revisions")

    source_id = next(iter(source_ids))
    kind = next(iter(kinds))
    name = next(iter(names))
    output = f"Source `{source_id}` (`{kind}`), original file `{name}`:\n\n"
    for revision, modified, size, digest, _ in sorted(revisions):
        output += (
            f"- `{revision}`: modified `{modified}`, {size} bytes, "
            f"SHA-256 `{digest}`\n"
        )
    return output
