"""Contracts for the fixed Vote Health Part F revenue layout."""

from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import vote_health_revenue
from archive_govt_nz.domains.health_appropriations.vote_health_revenue import (
    _amount,
    parse_revenue_pages,
)


def _pages() -> list[str]:
    first = ["Part F - Crown Revenue and Receipts"]
    second = []
    for number in range(16):
        target = first if number < 8 else second
        target.append(
            f"Total Revenue {chr(ord('A') + number)} {number + 1} - {number + 1}"
        )
    second.extend(["Total Crown Revenue and", "Receipts", "100 2 102"])
    return ["\n".join(first), "\n".join(second)]


def test_parser_requires_fixed_complete_part_f_rows() -> None:
    rows = parse_revenue_pages(_pages())
    assert len(rows) == 17
    assert rows[-1]["revenue_name"] == "Total Crown Revenue and Receipts"
    assert rows[0]["tokens"]["supplementary_estimates"] == "-"


def test_parser_rejects_missing_layout_marker() -> None:
    pages = _pages()
    pages[0] = pages[0].replace("Part F", "different")
    with pytest.raises(ValueError, match="vote_health_revenue_pdf_contract"):
        parse_revenue_pages(pages)


def test_amount_preserves_parenthesized_negative() -> None:
    assert _amount("( 82,900)") == -82900
    assert _amount("-") is None
    with pytest.raises(ValueError, match="vote_health_revenue_pdf_contract"):
        _amount("not-a-number")


def test_normalizer_writes_provenance_preserving_part_f_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")

    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self, *, extraction_mode: str) -> str:
            assert extraction_mode == "plain"
            return self.text

    class Reader:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.is_encrypted = False
            pages = ["front matter"] * 19 + _pages() + ["blank"]
            self.pages = [Page(text) for text in pages]

    monkeypatch.setattr(vote_health_revenue, "PdfReader", Reader)
    planned = vote_health_revenue.normalize_vote_health_revenue(
        source,
        tmp_path / "planned",
        expected_sha256="41cf6794ba4200b839c53531555f0f3998df4cbb01a4d5cb0b94e3ca5e23947d",
        source_vintage="Treasury-Vote-Health-Supplementary-2003-04",
        source_locator="https://example.test/supp04health.pdf",
        observed_at="2026-08-29T19:31:00Z",
    )
    assert planned["status"] == "planned"
    assert not (tmp_path / "planned").exists()
    receipt = vote_health_revenue.normalize_vote_health_revenue(
        source,
        tmp_path / "out",
        expected_sha256="41cf6794ba4200b839c53531555f0f3998df4cbb01a4d5cb0b94e3ca5e23947d",
        source_vintage="Treasury-Vote-Health-Supplementary-2003-04",
        source_locator="https://example.test/supp04health.pdf",
        observed_at="2026-08-29T19:31:00Z",
        dry_run=False,
    )
    assert receipt["status"] == "passed"
    assert receipt["counts"] == {"pages": 2, "facts": 17}
    facts = pq.read_table(
        tmp_path / "out/vote_health_revenue_facts.parquet"
    ).to_pylist()
    assert facts[-1]["revenue_name"] == "Total Crown Revenue and Receipts"
    assert facts[-1]["total_budgeted"] == 102
