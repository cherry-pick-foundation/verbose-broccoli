from types import SimpleNamespace

import pytest

from doc_regions.units import split
from wiki_consistency import citations


def _parse(text):
    return citations.sentences(split("wiki/test.qmd", text))


def test_native_bundle_maps_two_sentences_and_repeated_occurrences(monkeypatch):
    text = "Same result [@source/r1, p. 25]. " * 12
    real_run = citations.subprocess.run
    calls = []

    def record(*args, **kwargs):
        calls.append(args[0])
        return real_run(*args, **kwargs)

    monkeypatch.setattr(citations.subprocess, "run", record)
    result = _parse(text)
    assert len(calls) == 1
    assert calls[0] == [
        "quarto",
        "pandoc",
        "--from",
        "markdown-smart",
        "--to",
        "json",
    ]
    assert len(result) == 12
    assert len({item["id"] for item in result}) == 12
    assert all(item["citation_problem"] is None for item in result)
    assert "".join(item["text"] for item in result) == text
    assert all(
        text[item["start"] : item["end"]] == item["text"] for item in result
    )


def test_uncited_opening_never_inherits_later_citation():
    result = _parse(
        "Unsupported opening. Supported ending [@source/r1, p. 25]."
    )
    assert len(result) == 2
    assert result[0]["citation_problem"] == "missing sentence citation"
    assert result[0]["citations"] == []
    assert result[1]["citations"] == [{"key": "source/r1", "locator": "p. 25"}]


def test_native_soft_break_keeps_original_bytes_and_line_identity():
    text = (
        "This claim wraps\r\nacross lines [@source/r1, p. 25]. "
        "Next [@source/r1, p. 26].\r\n"
    )
    result = _parse(text)
    assert len(result) == 2
    assert all(item["citation_problem"] is None for item in result)
    assert result[0]["first_line"] == 1
    assert result[0]["last_line"] == 2
    assert result[1]["first_line"] == result[1]["last_line"] == 2
    assert "".join(item["text"] for item in result) == text


@pytest.mark.parametrize("prefix", ["- ", "1. ", "2) "])
def test_native_list_boundaries_are_distinct(prefix):
    result = _parse(
        f"{prefix}First [@source/r1, p. 25].\n"
        f"{prefix}Second [@source/r1, sec. purpose].\n"
    )
    assert len(result) == 2
    assert [item["first_line"] for item in result] == [1, 2]
    assert all(item["citation_problem"] is None for item in result)


def test_abbreviation_decimal_unicode_and_multisource_locators():
    result = _parse(
        "Dr. Example measured 3.14 café units 😊 "
        "[@source/r1, p. 25; @other/r2, pp. 25-26]. "
        "The purpose holds [@source/r1, sec. purpose]."
    )
    assert len(result) == 2
    assert result[0]["citations"] == [
        {"key": "source/r1", "locator": "p. 25"},
        {"key": "other/r2", "locator": "pp. 25-26"},
    ]
    assert all(item["citation_problem"] is None for item in result)


@pytest.mark.parametrize(
    "text",
    [
        '"Unsupported opening. Supported ending" [@source/r1, p. 25].',
        "(Unsupported opening. Supported ending) [@source/r1, p. 25].",
        "A 'Unsupported opening. Supported ending' [@source/r1, p. 25].",
        "[Unsupported opening. Supported ending] [@source/r1, p. 25].",
        "«Unsupported opening. Supported ending» [@source/r1, p. 25].",
        "--Unsupported opening. Supported ending-- [@source/r1, p. 25].",
        "Uncited.Supported [@source/r1, p. 25].",
        "First [@source/r1, p. 25].Second [@source/r1, p. 26].",
        "A literal ∯ mark [@source/r1, p. 25]. Next [@source/r1, p. 26].",
        "A **formatted** claim [@source/r1, p. 25].",
        r"An escaped \[@source/r1, p. 25] is not a citation.",
        "A narrative @source/r1 citation.",
        "First [@source/r1, p. 25] then more claim.",
        "First [@source/r1, p. 25] and second [@source/r1, p. 26].",
        "::: {.callout-note}\nClaim [@source/r1, p. 25].\n:::",
        "> Claim [@source/r1, p. 25].",
        "| Claim | Evidence |\n| --- | --- |\n| Result | [@source/r1, p. 25] |",
        "{{< include secret.qmd >}}",
        '```{python}\nraise AssertionError("must remain inert")\n```',
        "Hard  \nbreak [@source/r1, p. 25].",
    ],
)
def test_unsupported_shapes_keep_all_original_text_unresolved(text):
    raw = split("wiki/test.qmd", text)
    result = citations.sentences(raw)
    assert result
    assert all(item["citation_problem"] for item in result)
    assert [item["text"] for item in result] == [item["text"] for item in raw]


@pytest.mark.parametrize(
    "spans",
    [
        [(1, 5, "bcde")],
        [(0, 99, "abcde")],
        [(0, 4, "wrong")],
        [(0, 3, "abc"), (2, 5, "cde")],
        [(0, 2, "ab")],
        [(False, 5, "abcde")],
    ],
)
def test_dropped_invalid_and_overlapping_sentence_data_is_refused(
    monkeypatch, spans
):
    class Segmenter:
        def __init__(self, **kwargs):
            assert kwargs == {
                "language": "en",
                "clean": False,
                "char_span": True,
            }

        def segment(self, unused_text):
            return [
                SimpleNamespace(start=a, end=b, sent=text)
                for a, b, text in spans
            ]

    monkeypatch.setattr(citations.pysbd, "Segmenter", Segmenter)
    unit = split("wiki/x.qmd", "abcde")[0]
    with pytest.raises(ValueError, match="bounds|dropped"):
        citations._sentences(unit, "abcde", [])


@pytest.mark.parametrize("bounds", [[(-1, 2)], [(0, 9)], [(1, 3), (2, 4)]])
def test_malformed_citation_bounds_fail(bounds):
    unit = split("wiki/x.qmd", "abcde")[0]
    refs = [{"start": a, "end": b, "sources": []} for a, b in bounds]
    with pytest.raises(ValueError, match="citation bounds"):
        citations._sentences(unit, "abcde", refs)


def test_input_limit_precedes_native_execution(monkeypatch):
    calls = []
    monkeypatch.setattr(
        citations.subprocess,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    result = _parse("x" * (citations.MAX_PAGE_CHARS + 1))
    assert result[0]["citation_problem"] == "page exceeds native input limit"
    assert calls == []
