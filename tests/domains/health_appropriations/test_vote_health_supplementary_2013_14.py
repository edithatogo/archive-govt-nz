"""Contract tests for the pinned 2013/14 Supplementary Estimates totals."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2013_14 as module,
)

_LABELS = module._EXPECTED_LABELS  # noqa: SLF001 - source-pinned expected labels


def _pages() -> list[tuple[int, str]]:
    header = (
        "VOTE HEALTH 2013/14 Supplementary Estimates\n"
        "Estimates Budget $000 Supplementary Estimates Budget $000 Total Budget $000\n"
    )
    pages = dict.fromkeys(module.PAGES, header)
    locations = (2, 2, 5, 5, 6, 6)
    for index, (label, page) in enumerate(zip(_LABELS, locations, strict=True)):
        values = ("-", "(1,250)", "2,500") if index == 0 else ("1,000", "250", "1,250")
        pages[page] += f"{label} {' '.join(values)}\n"
    return sorted(pages.items())


def _reversed_rows() -> list[tuple[int, str]]:
    pages = _pages()
    number, text = pages[0]
    rows = [line for line in text.splitlines() if line.startswith("Total ")]
    assert len(rows) == 2
    lines = text.splitlines()
    positions = [lines.index(row) for row in rows]
    lines[positions[0]], lines[positions[1]] = lines[positions[1]], lines[positions[0]]
    pages[0] = (number, "\n".join(lines))
    return pages


def _missing_row() -> list[tuple[int, str]]:
    pages = _pages()
    number, text = pages[0]
    lines = text.splitlines()
    lines.remove(next(line for line in lines if line.startswith("Total ")))
    pages[0] = (number, "\n".join(lines))
    return pages


def _mock_reader(
    monkeypatch: pytest.MonkeyPatch, *, encrypted: bool = False, page_count: int = 44
) -> None:
    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self) -> str:
            return self.text

    class Reader:
        is_encrypted = encrypted

        def __init__(self, *_: object, **__: object) -> None:
            texts = dict(_pages())
            self.pages = [
                Page(texts.get(number + 1, "")) for number in range(page_count)
            ]

    monkeypatch.setattr(module, "PdfReader", Reader)


def test_parser_preserves_six_named_totals_and_source_tokens() -> None:
    rows = module.parse_category_totals(_pages())

    assert tuple(row["total_label"] for row in rows) == _LABELS
    assert rows[0]["source_page"] == 2
    assert rows[0]["tokens"] == {
        "estimates_budget": "-",
        "supplementary_estimates_budget": "(1,250)",
        "total_budget": "2,500",
    }


@pytest.mark.parametrize(
    ("pages", "error"),
    [
        (_pages()[:-1], "vote_health_2013_14_page_span"),
        (
            [(2, "2012/13 Supplementary Estimates"), *_pages()[1:]],
            "vote_health_2013_14_layout",
        ),
        (
            _missing_row(),
            "vote_health_2013_14_total_set",
        ),
        (
            _reversed_rows(),
            "vote_health_2013_14_total_set",
        ),
    ],
)
def test_parser_fails_closed_on_span_vintage_rows_and_order(
    pages: list[tuple[int, str]], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        module.parse_category_totals(pages)


def test_normalizer_writes_facts_lineage_and_partial_page_dispositions(
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
        observed_at="2026-10-06T00:00:00Z",
        dry_run=False,
    )

    assert receipt["status"] == "passed"
    facts = pq.read_table(
        output / "vote_health_category_total_facts.parquet"
    ).to_pylist()
    assert len(facts) == 6
    assert facts[0]["estimates_budget"] is None
    assert str(facts[0]["supplementary_estimates_budget"]) == "-1250.000"
    assert facts[0]["rights_state"] == "not_evaluated"
    assert len(pq.read_table(output / "field_lineage.parquet").to_pylist()) == 18
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert [row["source_page"] for row in dispositions] == list(module.PAGES)


def test_dry_run_and_identity_mismatch_do_not_write(
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
        observed_at="2026-10-06T00:00:00Z",
    )
    assert receipt["status"] == "planned"
    assert not output.exists()
    with pytest.raises(ValueError, match="vote_health_2013_14_identity"):
        module.normalize(
            source,
            output,
            expected_sha256=digest,
            source_vintage=module.VINTAGE,
            source_locator="https://example.invalid/wrong.pdf",
            observed_at="2026-10-06T00:00:00Z",
        )


def test_normalizer_rejects_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)
    output = tmp_path / "silver"
    output.mkdir()
    with pytest.raises(ValueError, match="vote_health_2013_14_path"):
        module.normalize(
            source,
            output,
            expected_sha256=digest,
            source_vintage=module.VINTAGE,
            source_locator=module.SOURCE_LOCATOR,
            observed_at="2026-10-06T00:00:00Z",
        )


@pytest.mark.parametrize(
    ("encryption", "page_count"), [("encrypted", 44), ("clear", 43)]
)
def test_normalizer_rejects_encrypted_or_wrong_page_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    encryption: str,
    page_count: int,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)
    _mock_reader(
        monkeypatch, encrypted=encryption == "encrypted", page_count=page_count
    )
    with pytest.raises(ValueError, match="vote_health_2013_14_pdf_identity"):
        module.normalize(
            source,
            tmp_path / "silver",
            expected_sha256=digest,
            source_vintage=module.VINTAGE,
            source_locator=module.SOURCE_LOCATOR,
            observed_at="2026-10-06T00:00:00Z",
        )
