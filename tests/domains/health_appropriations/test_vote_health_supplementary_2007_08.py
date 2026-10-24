"""Contracts for the pinned 2007/08 Supplementary Estimates totals."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2007_08 as module,
)

_LABELS = module._EXPECTED_LABELS  # noqa: SLF001 - source-pinned category labels


def _pages() -> list[tuple[int, str]]:
    header = (
        "VOTE HEALTH 2007/08 Supplementary Estimates\n"
        "Estimates Budget $000 Supplementary Estimates Budget $000 Total Budget $000\n"
    )
    pages = dict.fromkeys(module.PAGES, header)
    values = (
        ("204,033", "11,798", "215,831"),
        ("10,860,491", "(225,819)", "10,634,672"),
        ("17,912", "6,180", "24,092"),
        ("-", "18,537", "18,537"),
        ("846,267", "(530,407)", "315,860"),
        ("11,928,703", "(719,711)", "11,208,992"),
    )
    locations = (2, 5, 5, 5, 6, 6)
    for label, row, page in zip(_LABELS, values, locations, strict=True):
        pages[page] += f"{label} {' '.join(row)}\n"
    return sorted(pages.items())


def _mock_reader(monkeypatch: pytest.MonkeyPatch, *, page_count: int = 36) -> None:
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
    assert [row["source_page"] for row in rows] == [2, 5, 5, 5, 6, 6]
    assert rows[1]["tokens"]["supplementary_estimates_budget"] == "(225,819)"


@pytest.mark.parametrize(
    ("pages", "error"),
    [
        (_pages()[:-1], "vote_health_2007_08_page_span"),
        (
            [(2, "VOTE HEALTH 2014/15 Supplementary Estimates"), *_pages()[1:]],
            "vote_health_2007_08_layout",
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
            "vote_health_2007_08_total_set",
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
    assert str(facts[1]["supplementary_estimates_budget"]) == "-225819.000"
    assert facts[2]["rights_state"] == "not_evaluated"
    assert facts[3]["estimates_budget"] is None
    raw_values = facts[3]["raw_values_json"]
    assert raw_values
    assert "-" in raw_values
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    assert len(lineage) == 18
    dash_lineage = [row for row in lineage if row["raw_value"] == "-"]
    assert len(dash_lineage) == 1
    assert dash_lineage[0]["field"] == "estimates_budget"
    assert dash_lineage[0]["normalized_value"] == "None"
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

    with pytest.raises(ValueError, match="vote_health_2007_08_identity"):
        module.normalize(
            source,
            tmp_path / "silver",
            expected_sha256=digest,
            source_vintage=module.VINTAGE,
            source_locator="https://example.invalid/wrong.pdf",
            observed_at="2026-10-06T09:00:00Z",
        )
    assert not (tmp_path / "silver").exists()
