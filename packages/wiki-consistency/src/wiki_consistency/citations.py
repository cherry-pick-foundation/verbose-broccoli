"""Map native Pandoc citations to candidate sentence slices of plain prose.

Pandoc's Markdown reader has no sourcepos extension. Existing block line maps
bound the original input; full literal alignment proves the supported mapping.
Formatting and ambiguous sentence attachment remain unresolved, not inferred.
"""

import json
import os
import re
import subprocess
import tempfile

import pysbd

from doc_regions.requests import MAX_CLAIM_CHARS

MAX_PAGE_CHARS = 1024 * 1024


def _unresolved(unit, reason):
    return {**unit, "citations": [], "citation_problem": reason}


def _pattern(inlines):
    parts = []
    for node in inlines:
        if node["t"] == "Str":
            parts.append(re.escape(node["c"]))
        elif node["t"] == "Space":
            parts.append(r"[ \t]+")
        elif node["t"] == "SoftBreak":
            parts.append(r"\r?\n[ \t]*")
        else:
            raise ValueError("unsupported native inline structure")
    return "".join(parts)


def _align(unit, blocks):
    text = unit["text"]
    first = len(text) - len(text.lstrip())
    last = len(text.rstrip())
    if unit["kind"] == "list_item":
        if len(blocks) != 1 or blocks[0]["t"] not in {
            "BulletList",
            "OrderedList",
        }:
            raise ValueError("unsupported native list structure")
        block = blocks[0]
        items = block["c"] if block["t"] == "BulletList" else block["c"][1]
        if len(items) != 1:
            raise ValueError("unprovable list item mapping")
        marker = re.match(r"(?:[-+*]|[0-9]+[.)])[ \t]+", text[first:last])
        if marker is None:
            raise ValueError("unprovable native list prefix")
        first += marker.end()
        blocks = items[0]
    if len(blocks) != 1 or blocks[0]["t"] not in {"Para", "Plain"}:
        raise ValueError("unsupported native prose structure")
    inlines = blocks[0]["c"]
    patterns, groups = [], []
    for node in inlines:
        literal = node["c"][1] if node["t"] == "Cite" else [node]
        patterns.append(f"({_pattern(literal)})")
        if node["t"] == "Cite":
            groups.append((len(patterns), node["c"][0]))
    match = re.fullmatch("".join(patterns), text[first:last])
    if match is None:
        raise ValueError("native text does not match the exact original block")
    projection = list(text)
    citations = []
    for number, records in groups:
        start, end = (first + value for value in match.span(number))
        if not text[start:end].startswith("[@") or not text[start:end].endswith(
            "]"
        ):
            raise ValueError(
                "only parenthetical citation brackets are supported"
            )
        located = []
        for record in records:
            if (
                record["citationPrefix"]
                or record["citationMode"]["t"] != "NormalCitation"
            ):
                raise ValueError("unsupported native citation mode or prefix")
            suffix = record["citationSuffix"]
            if any(node["t"] not in {"Str", "Space"} for node in suffix):
                raise ValueError("unsupported native locator structure")
            locator = (
                "".join(
                    node["c"] if node["t"] == "Str" else " " for node in suffix
                )
                .replace("\u00a0", " ")
                .removeprefix(",")
                .strip()
            )
            located.append({"key": record["citationId"], "locator": locator})
        if not located:
            raise ValueError("empty native citation group")
        citations.append({"start": start, "end": end, "sources": located})
        projection[start:end] = "x" * (end - start)
    for number, node in enumerate(inlines, 1):
        if node["t"] == "SoftBreak":
            start, end = (first + value for value in match.span(number))
            projection[start:end] = " " * (end - start)
    # Prefixes/trailing block whitespace are outside native prose content.
    projection[:first] = " " * first
    projection[last:] = " " * (len(text) - last)
    return "".join(projection), citations


def _sentences(unit, projection, citations):
    if len(projection) != len(unit["text"]):
        raise ValueError("projection changed the source length")
    if (
        any(character in projection for character in "\"'“”‘’()[]«»")
        or "--" in projection
    ):
        raise ValueError("protected quotation or parenthesis needs review")
    if re.search(r"[.!?][A-Za-z]", projection):
        raise ValueError("punctuation without whitespace needs review")
    prior = 0
    for citation in citations:
        start, end = citation["start"], citation["end"]
        if not (
            type(start) is int
            and type(end) is int
            and prior <= start < end <= len(projection)
        ):
            raise ValueError("invalid or overlapping citation bounds")
        prior = end
    spans = pysbd.Segmenter(language="en", clean=False, char_span=True).segment(
        projection
    )
    result, prior, owned = [], 0, []
    for number, span in enumerate(spans, 1):
        start, end = span.start, span.end
        if (
            type(start) is not int
            or type(end) is not int
            or not prior <= start < end <= len(projection)
            or projection[start:end] != span.sent
            or projection[prior:start].strip()
        ):
            raise ValueError("invalid sentence bounds or dropped source text")
        attached = [
            c for c in citations if start <= c["start"] and c["end"] <= end
        ]
        if any(
            start < c["end"] and c["start"] < end and c not in attached
            for c in citations
        ):
            raise ValueError("sentence crosses a citation group")
        if len(attached) > 1:
            raise ValueError("uncertain attachment of multiple citation groups")
        if attached and (
            projection[attached[0]["end"] : end].strip()
            not in {"", ".", "!", "?"}
            or not projection[start : attached[0]["start"]].strip()
        ):
            raise ValueError("citation is not sentence-final")
        original = unit["text"]
        first_line = unit["first_line"] + original[:start].count("\n")
        last_line = first_line + original[start:end].rstrip().count("\n")
        result.append(
            {
                **unit,
                "id": f"{unit['id']}:s{number}@{start}-{end}",
                "block_id": unit["id"],
                "first_line": first_line,
                "last_line": last_line,
                "start": start,
                "end": end,
                "text": original[start:end],
                "citations": attached[0]["sources"] if attached else [],
                "citation_problem": None
                if attached
                else "missing sentence citation",
            }
        )
        owned.extend(attached)
        prior = end
    if projection[prior:].strip() or owned != citations:
        raise ValueError("dropped source text or unowned citation")
    return result


def sentences(units):
    """Parse one page bundle, returning exact candidate slices or findings.

    Synthetic fenced containers bind native blocks to existing source maps;
    their IDs never enter claims. Source text is inert Pandoc input, not render
    input. This restricted mapping makes no linguistic completeness claim.
    """
    if sum(len(unit["text"]) for unit in units) > MAX_PAGE_CHARS:
        return [
            _unresolved(unit, "page exceeds native input limit")
            for unit in units
        ]
    result, eligible = {}, []
    for index, unit in enumerate(units):
        if unit["kind"] not in {"paragraph", "list_item"}:
            result[index] = [_unresolved(unit, "unsupported non-prose block")]
        elif len(unit["text"]) > MAX_CLAIM_CHARS:
            result[index] = [
                _unresolved(unit, "block exceeds sentence input limit")
            ]
        elif ":::" in unit["text"] or "{{<" in unit["text"]:
            result[index] = [_unresolved(unit, "unsupported div or shortcode")]
        else:
            eligible.append((index, unit))
    if eligible:
        bundle = "\n\n".join(
            f"::: {{#u-{index}}}\n{unit['text']}\n:::"
            for index, unit in eligible
        )
        try:
            with tempfile.TemporaryDirectory(prefix="wiki-pandoc-") as run:
                env = {
                    "PATH": os.environ.get("PATH", os.defpath),
                    "HOME": run,
                    "XDG_CACHE_HOME": run,
                    "XDG_CONFIG_HOME": run,
                    "XDG_DATA_HOME": run,
                    "XDG_STATE_HOME": run,
                }
                parsed = subprocess.run(
                    [
                        "quarto",
                        "pandoc",
                        "--from",
                        "markdown-smart",
                        "--to",
                        "json",
                    ],
                    input=bundle,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=20,
                    env=env,
                    cwd=run,
                )
                blocks = json.loads(parsed.stdout)["blocks"]
            if len(blocks) != len(eligible):
                raise ValueError("native bundle mapping changed")
            for (index, unit), block in zip(eligible, blocks, strict=True):
                try:
                    if block["t"] != "Div" or block["c"][0][0] != f"u-{index}":
                        raise ValueError("unprovable native bundle mapping")
                    projection, citations = _align(unit, block["c"][1])
                    result[index] = _sentences(unit, projection, citations)
                except (ValueError, KeyError, TypeError, IndexError) as error:
                    result[index] = [_unresolved(unit, str(error))]
        except (
            OSError,
            ValueError,
            subprocess.SubprocessError,
            KeyError,
            TypeError,
            IndexError,
        ) as error:
            for index, unit in eligible:
                result[index] = [
                    _unresolved(
                        unit,
                        "native citation parsing unavailable: "
                        f"{type(error).__name__}",
                    )
                ]
    return [
        sentence for index in range(len(units)) for sentence in result[index]
    ]
