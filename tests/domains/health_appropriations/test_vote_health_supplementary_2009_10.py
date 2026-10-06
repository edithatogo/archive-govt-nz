"""Contracts for the pinned 2009/10 Supplementary Estimates totals."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2009_10 as module,
)

_LABELS = module._EXPECTED_LABELS  # noqa: SLF001 - source-pinned category labels


def _pages() -> list[tuple[int, str]]:
    header = (
        "VOTE HEALTH 2009/10 Supplementary Estimates\n"
        "Estimates Budget $000 Supplementary Estimates Budget $000 Total Budget $000\n"
    )
    pages = dict.fromkeys(module.PAGES, header)
    values = (
        ("217,249", "4,448", "221,697"),
        ("12,382,270", "(205,837)", "12,176,433"),
        ("23,637", "350", "23,987"),
        ("35,410", "(18,145)", "17,265"),
        ("319,149", "(42,655)", "276,494"),
        ("12,977,715", "(261,839)", "12,715,876"),
    )
    locations = (2, 5, 5, 6, 6, 6)
    for label, row, page in zip(_LABELS, values, locations, strict=True):
        pages[page] += f"{label} {' '.join(row)}\n"
    return sorted(pages.items())


def _mock_reader(monkeypatch: pytest.MonkeyPatch, *, page_count: int = 7) -> None:
    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self) -> str:
            return self.text

    class Reader:
        is_encrypted = False

        def __init__(self, *_: object, **__: object) -> None:
            texts = dict(_pages())
            self.pages = [
                Page(texts.get(number + 1, "")) for number in range(page_count)
            ]

    monkeypatch.setattr(module, "PdfReader", Reader)


def test_parser_retains_six_totals_and_negative_source_tokens() -> None:
    rows = module.parse_category_totals(_pages())

    assert tuple(row["total_label"] for row in rows) == _LABELS
    assert [row["source_page"] for row in rows] == [2, 5, 5, 6, 6, 6]
    assert rows[1]["tokens"]["supplementary_estimates_budget"] == "(205,837)"


@pytest.mark.parametrize(
    ("pages", "error"),
    [
        (_pages()[:-1], "vote_health_2009_10_page_span"),
        (
            [(2, "VOTE HEALTH 2014/15 Supplementary Estimates"), *_pages()[1:]],
            "vote_health_2009_10_layout",
        ),
        (
            [
                (
                    number,
                    text.replace(
                        "Total Annual and Permanent Appropriations", "Total Other"
                    ),
                )
                for number, text in _pages()
            ],
            "vote_health_2009_10_total_set",
        ),
    ],
)
def test_parser_fails_closed_on_span_vintage_and_total_set(
    pages: list[tuple[int, str]], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        module.parse_category_totals(pages)


def test_normalizer_writes_source_lineage_and_partial_page_dispositions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)
    _mock_reader(monkeypatch)

    output = tmp_path / "silver"
    receipt = module.normalize(
        source,
        output,
        expected_sha256=digest,
        source_vintage=module.VINTAGE,
        source_locator=module.SOURCE_LOCATOR,
        observed_at="2026-10-06T09:00:00Z",
        dry_run=False,
    )

    assert receipt["status"] == "passed"
    facts = pq.read_table(
        output / "vote_health_category_total_facts.parquet"
    ).to_pylist()
    assert len(facts) == 6
    assert str(facts[1]["supplementary_estimates_budget"]) == "-205837.000"
    assert facts[2]["rights_state"] == "not_evaluated"
    assert len(pq.read_table(output / "field_lineage.parquet").to_pylist()) == 18
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert [row["source_page"] for row in dispositions] == list(module.PAGES)


def test_wrong_source_locator_fails_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)
    _mock_reader(monkeypatch)

    with pytest.raises(ValueError, match="vote_health_2009_10_identity"):
        module.normalize(
            source,
            tmp_path / "silver",
            expected_sha256=digest,
            source_vintage=module.VINTAGE,
            source_locator="https://example.invalid/wrong.pdf",
            observed_at="2026-10-06T09:00:00Z",
        )
    assert not (tmp_path / "silver").exists()
