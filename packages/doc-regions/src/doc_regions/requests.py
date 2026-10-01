"""Prepare lossless Jev requests from Markdown units and Git evidence."""

import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess

from anyascii import anyascii

from doc_regions.config import load
from doc_regions.units import split

CLASSES = [
    {
        "id": "mechanical_candidate",
        "description": (
            "Text fully derivable from named source files by a deterministic "
            "generator, "
            "such as a table listing skills."
        ),
    },
    {
        "id": "agent_region",
        "description": (
            "Text requiring judgment or explanation, not fully derivable from "
            "named "
            "source files, such as design rationale."
        ),
    },
]

# Hangul syllables and Jamo, composed or decomposed; backfire refuses a request
# that holds any (`hangul_remaining`).
_HANGUL_RUN = re.compile(
    r"[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7ff\uffa0-\uffdc]+"
)


def latin(text):
    """Spell each run of Hangul in Latin letters, so a request can be sent."""
    return _HANGUL_RUN.sub(lambda run: anyascii(run[0]).lower(), text)


# A request of about 45,800 claim characters (106 claims) and one of 224
# short claims drew OpenRouter's `400 max_tokens_exceeded`; 110 claims and
# four hand-split requests of about 11,500 characters were answered. Neither
# jev-judge-mcp nor backfire splits requests. Evidence is the same in every
# request of a group, so it does not count here.
MAX_CLAIMS = 110
MAX_CLAIM_CHARS = 12000


def claim_batches(units, claims_per_request):
    """Split units in order; a batch stays within both claim limits.

    A unit longer than the character limit still gets a batch of its own.
    """
    batch, chars = [], 0
    for unit in units:
        size = len(unit["text"])
        if batch and (
            len(batch) == claims_per_request or chars + size > MAX_CLAIM_CHARS
        ):
            yield batch
            batch, chars = [], 0
        batch.append(unit)
        chars += size
    if batch:
        yield batch


def verify_requests(groups):
    """Build bounded jev_verify requests from units and evidence."""
    requests = []
    for units, evidence in groups:
        if not evidence:
            raise ValueError("jev_verify evidence limit is at least 1 item")
        if len(evidence) > 249:
            raise ValueError("jev_verify evidence request cap is 249 items")
        claims_per_request = min(
            MAX_CLAIMS,
            672 // (3 if len(evidence) == 1 else len(evidence) + 4),
        )
        for batch in claim_batches(units, claims_per_request):
            requests.append(
                {
                    "tool": "jev_verify",
                    "units": [unit["id"] for unit in batch],
                    "arguments": {
                        "claims": [unit["text"] for unit in batch],
                        "evidence": evidence,
                    },
                }
            )
    return requests


def classify_requests(units, purpose):
    """Build batched jev_classify requests."""
    requests = []
    for start in range(0, len(units), 64):
        batch = units[start : start + 64]
        requests.append(
            {
                "tool": "jev_classify",
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
    """Run a Git command at the repository root and return its output."""
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    ).stdout


def prepare(root, config_path, *, base, max_evidence_chars):
    """Prepare requests for changed document units and evidence."""
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
    # The units keep their Hangul; the requests carry it spelled in Latin
    # letters, in claims and evidence alike.
    sendable = [{**unit, "text": latin(unit["text"])} for unit in units]

    diff_options = [
        "--no-ext-diff",
        "--no-textconv",
        "--no-color",
        "-M",
    ]
    fields = git(
        root, "diff", *diff_options, merge_base, "--name-status", "-z", "--"
    ).split("\0")
    # Each entry is its status letter and one path, or two for a rename or
    # copy, so a renamed file is evidence as one rename diff, not as a whole
    # deletion plus a whole addition.
    changed, index = {}, 0
    while index < len(fields) - 1:
        paths = 2 if fields[index][0] in "RC" else 1
        old, new = fields[index + 1], fields[index + paths]
        changed[new] = [old, new] if paths == 2 else [new]
        index += 1 + paths
    evidence = []
    for document, paths in sorted(changed.items()):
        if document in documents or any(
            PurePosixPath(document).full_match(pattern)
            for pattern in config["evidence_exclude"]
        ):
            continue
        diff = latin(git(root, "diff", *diff_options, merge_base, "--", *paths))
        chunks = [
            diff[index : index + max_evidence_chars]
            for index in range(0, len(diff), max_evidence_chars)
        ]
        evidence.extend(
            {
                "id": latin(document)
                if len(chunks) == 1
                else f"{latin(document)}#{index}",
                "text": chunk,
            }
            for index, chunk in enumerate(chunks, 1)
        )

    requests = verify_requests([(sendable, evidence)]) if evidence else []
    for document in config["targets"]:
        added = [
            unit
            for unit in sendable
            if unit["document"] == document and unit["added"]
        ]
        requests.extend(
            classify_requests(
                added, f"Find mechanical region candidates in {document}."
            )
        )
    return {"base": merge_base, "units": units, "requests": requests}
