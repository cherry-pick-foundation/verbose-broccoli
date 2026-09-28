"""Prepare lossless Backfire requests from Markdown units and Git evidence."""

import os
from pathlib import Path, PurePosixPath
import subprocess

from doc_regions.config import load
from doc_regions.units import split


CLASSES = [
    {
        "id": "mechanical_candidate",
        "description": (
            "Text fully derivable from named source files by a deterministic generator, "
            "such as a table listing skills."
        ),
    },
    {
        "id": "agent_region",
        "description": (
            "Text requiring judgment or explanation, not fully derivable from named "
            "source files, such as design rationale."
        ),
    },
]


def verify_requests(groups):
    requests = []
    for units, evidence in groups:
        if not evidence:
            raise ValueError(
                "backfire_verify evidence limit is at least 1 item"
            )
        if len(evidence) > 249:
            raise ValueError("backfire_verify evidence limit is 249 items")
        claims_per_request = 672 // (
            3 if len(evidence) == 1 else len(evidence) + 4
        )
        for start in range(0, len(units), claims_per_request):
            batch = units[start : start + claims_per_request]
            requests.append(
                {
                    "tool": "backfire_verify",
                    "units": [unit["id"] for unit in batch],
                    "arguments": {
                        "claims": [unit["text"] for unit in batch],
                        "evidence": evidence,
                    },
                }
            )
    return requests


def classify_requests(units, purpose):
    requests = []
    for start in range(0, len(units), 64):
        batch = units[start : start + 64]
        requests.append(
            {
                "tool": "backfire_classify",
                "units": [unit["id"] for unit in batch],
                "arguments": {
                    "items": [
                        {"id": unit["id"], "text": unit["text"]}
                        for unit in batch
                    ],
                    "classes": CLASSES,
                    "purpose": purpose,
                },
            }
        )
    return requests


def git(root, *args):
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    ).stdout


def prepare(root, config_path, *, base, max_evidence_chars):
    if not isinstance(max_evidence_chars, int) or max_evidence_chars < 1:
        raise ValueError("max-evidence-chars must be a positive integer")
    root = Path(root).resolve()
    config = load(config_path, root)
    merge_base = git(root, "merge-base", base, "HEAD").strip()
    base_files = set(
        git(root, "ls-tree", "-r", "--name-only", "-z", merge_base).split("\0")
    )
    documents = sorted(config["targets"] + config["report_only"])
    units = []
    for document in documents:
        base_text = (
            git(root, "show", f"{merge_base}:{document}")
            if document in base_files
            else ""
        )
        source = (root / document).read_bytes().decode("utf-8")
        for unit in split(document, source, base_text):
            unit["report_only"] = document in config["report_only"]
            units.append(unit)

    diff_options = [
        "--no-ext-diff",
        "--no-textconv",
        "--no-color",
        "--no-renames",
    ]
    changed = git(
        root, "diff", *diff_options, merge_base, "--name-only", "-z", "--"
    ).split("\0")
    evidence = []
    for document in sorted(path for path in changed if path):
        if document in documents or any(
            PurePosixPath(document).full_match(pattern)
            for pattern in config["evidence_exclude"]
        ):
            continue
        diff = git(root, "diff", *diff_options, merge_base, "--", document)
        chunks = [
            diff[index : index + max_evidence_chars]
            for index in range(0, len(diff), max_evidence_chars)
        ]
        evidence.extend(
            {
                "id": document if len(chunks) == 1 else f"{document}#{index}",
                "text": chunk,
            }
            for index, chunk in enumerate(chunks, 1)
        )

    requests = verify_requests([(units, evidence)]) if evidence else []
    for document in config["targets"]:
        added = [
            unit
            for unit in units
            if unit["document"] == document and unit["added"]
        ]
        requests.extend(
            classify_requests(
                added, f"Find mechanical region candidates in {document}."
            )
        )
    return {"base": merge_base, "units": units, "requests": requests}
