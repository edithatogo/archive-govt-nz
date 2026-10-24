"""Contracts for the source-pinned 2005/06 Vote Health overview totals."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2005_06 as module,
)

_ROWS = (
    ("Output Expenses", "9,198,960 169,943 1,361 9,034,543 - 9,205,847"),
    ("Benefits and Other Unrequited Expenses", "- N/A N/A - - -"),
    ("Borrowing Expenses", "- N/A N/A - - -"),
    ("Other Expenses", "17,712 - - 21,983 - 21,983"),
    ("Capital Expenditure", "464,293 N/A N/A 582,338 - 582,338"),
    (
        "Intelligence and Security Department Expenses and Capital Expenditure",
        "- - - N/A N/A -",
    ),
    ("Total Appropriations", "9,680,965 169,943 1,361 9,638,864 - 9,810,168"),
)


def _text() -> str:
    rows = "\n".join(f"{label} {cells}" for label, cells in _ROWS)
    return (
        "VOTE HEALTH\n2005/06\nSummary of Financial Activity\n"
        "Main Estimates $000 Annual $000 Other $000 Annual $000 Other $000 Total $000\n"
        f"Appropriations\n{rows}\nCrown Revenue and Receipts\n"
    )


def _mock_reader(
    monkeypatch: pytest.MonkeyPatch, *, page_count: int = module.PAGE_COUNT
) -> None:
    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self) -> str:
            return self.text

    class Reader:
        is_encrypted = False

        def __init__(self, *_: object, **__: object) -> None:
            self.pages = [
                Page(_text() if number == 2 else "") for number in range(page_count)
            ]

    monkeypatch.setattr(module, "PdfReader", Reader)


def test_parser_keeps_original_labels_columns_and_null_tokens() -> None:
    rows = module.parse_overview_totals(_text())

    assert tuple(row["appropriation_label"] for row in rows) == tuple(
        label for label, _ in _ROWS
    )
    assert rows[0]["tokens"]["main_estimates"] == "9,198,960"
    assert rows[1]["tokens"]["department_annual"] == "N/A"
    assert rows[3]["tokens"]["main_estimates"] == "17,712"


@pytest.mark.parametrize(
    ("text", "error"),
    [
        (_text().replace("2005/06", "2004/05"), "vote_health_2005_06_layout"),
        (
            _text().replace("Crown Revenue and Receipts", "Revenue"),
            "vote_health_2005_06_layout",
        ),
        (
            _text().replace("9,810,168", "9,810,168 9"),
            "vote_health_2005_06_row_cells",
        ),
        (
            _text().replace("Total Appropriations", "Grand Total"),
            "vote_health_2005_06_row_cells",
        ),
    ],
)
def test_parser_fails_closed_on_layout_and_total_drift(text: str, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        module.parse_overview_totals(text)


def test_normalizer_writes_typed_facts_raw_tokens_and_lineage(
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
        observed_at="2026-10-07T00:00:00Z",
        dry_run=False,
    )

    assert receipt["status"] == "passed"
    facts = pq.read_table(
        output / "vote_health_appropriation_overview_facts.parquet"
    ).to_pylist()
    assert len(facts) == 7
    assert str(facts[0]["main_estimates"]) == "9198960.000"
    assert facts[1]["department_annual"] is None
    assert facts[1]["rights_state"] == "not_evaluated"
    assert "N/A" in facts[1]["raw_values_json"]
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    assert len(lineage) == 42
    not_applicable = [row for row in lineage if row["raw_value"] == "N/A"]
    assert len(not_applicable) == 8
    assert all(row["normalized_value"] == "None" for row in not_applicable)
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert dispositions[0]["source_page"] == module.PAGE


def test_wrong_source_identity_fails_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)

    with pytest.raises(ValueError, match="vote_health_2005_06_identity"):
        module.normalize(
            source,
            tmp_path / "silver",
            expected_sha256=digest,
            source_vintage=module.VINTAGE,
            source_locator="https://example.invalid/wrong.pdf",
            observed_at="2026-10-07T00:00:00Z",
        )
    assert not (tmp_path / "silver").exists()
