"""Contracts for the pinned 2014/15 Vote Health financial activity page."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2014_15_financial_activity as module,
)


def _page() -> str:
    return """VOTE HEALTH
Supporting Information
Part 1 - Vote as a Whole
1.2 - Trends in the Vote
Summary of Financial Activity
2014/15
Supplementary Estimates
Estimates
$000
Departmental
Transactions
$000
Non-
Departmental
Transactions
$000
Total
Transactions
$000
Total
$000
Appropriations
Output Expenses 100,000 1,000 (500) 500 100,500
Benefits or Related Expenses - N/A - - -
Borrowing Expenses - - - - -
Other Expenses 200 - (20) (20) 180
Capital Expenditure 5,000 300 200 500 5,500
Intelligence and Security Department Expenses and Capital
Expenditure - - N/A - -
Multi-Category Expenses and Capital Expenditure (MCA)
Output Expenses - - - - -
Other Expenses - - - - -
Capital Expenditure - N/A - - -
Total Appropriations 105,200 1,300 (520) 780 105,980
Crown Revenue and Capital Receipts
Tax Revenue - N/A - - -
Non-Tax Revenue 700 N/A 80 80 780
Capital Receipts 30 N/A 40 40 70
Total Crown Revenue and Capital Receipts 730 N/A 120 120 850
"""


def test_parser_preserves_all_rows_columns_sections_and_null_tokens() -> None:
    rows = module.parse_financial_activity([(7, _page())])

    assert len(rows) == 14
    assert rows[0]["source_label"] == "Output Expenses"
    assert rows[0]["tokens"] == {
        "estimates": "100,000",
        "departmental_transactions": "1,000",
        "non_departmental_transactions": "(500)",
        "total_transactions": "500",
        "total": "100,500",
    }
    assert rows[5]["source_label"].endswith("Expenditure")
    assert rows[6]["section"] == "appropriations"
    assert rows[10]["section"] == "crown_revenue_and_capital_receipts"
    assert rows[10]["tokens"]["departmental_transactions"] == "N/A"
    assert rows[1]["tokens"]["estimates"] == "-"


@pytest.mark.parametrize(
    ("pages", "error"),
    [
        ([(6, _page())], "vote_health_2014_15_financial_activity_page_span"),
        (
            [(7, _page().replace("2014/15", "2012/13"))],
            "vote_health_2014_15_financial_activity_layout",
        ),
        (
            [
                (
                    7,
                    _page().replace(
                        "Output Expenses 100,000", "Other Expenses 100,000"
                    ),
                )
            ],
            "vote_health_2014_15_financial_activity_row_set",
        ),
    ],
)
def test_parser_refuses_page_vintage_and_row_drift(
    pages: list[tuple[int, str]], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        module.parse_financial_activity(pages)


def test_normalizer_emits_decimal_facts_full_lineage_and_page_disposition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)

    class Page:
        def extract_text(self) -> str:
            return _page()

    class Reader:
        is_encrypted = False

        def __init__(self, *_: object, **__: object) -> None:
            self.pages = [Page() for _ in range(module.PAGE_COUNT)]

    monkeypatch.setattr(module, "PdfReader", Reader)
    output = tmp_path / "silver"
    receipt = module.normalize(
        source,
        output,
        expected_sha256=digest,
        source_vintage=module.VINTAGE,
        source_locator=module.SOURCE_LOCATOR,
        observed_at="2026-10-23T00:00:00Z",
        dry_run=False,
    )

    assert receipt["status"] == "passed"
    assert receipt["counts"] == {"pages": 1, "facts": 14, "lineage": 70}
    facts = pq.read_table(
        output / "vote_health_financial_activity_facts.parquet"
    ).to_pylist()
    assert facts[0]["non_departmental_transactions"] == -500
    assert facts[1]["estimates"] is None
    assert '"-"' in facts[1]["raw_values_json"]
    assert all(row["rights_state"] == "not_evaluated" for row in facts)
    assert facts[0]["source_label"] == facts[6]["source_label"] == "Output Expenses"
    assert facts[0]["record_id"] != facts[6]["record_id"]
    assert len(pq.read_table(output / "field_lineage.parquet").to_pylist()) == 70
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    assert all("ordinal=" in row["source_coordinate"] for row in lineage)
    page = pq.read_table(output / "page_dispositions.parquet").to_pylist()[0]
    assert page["source_page"] == 7
    assert page["disposition"] == "partially_normalized"


def test_normalizer_rejects_unpinned_context_and_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)
    output = tmp_path / "silver"

    with pytest.raises(ValueError, match="financial_activity_identity"):
        module.normalize(
            source,
            output,
            expected_sha256=digest,
            source_vintage="another edition",
            source_locator=module.SOURCE_LOCATOR,
            observed_at="2026-10-23T00:00:00Z",
        )

    output.mkdir()
    with pytest.raises(ValueError, match="financial_activity_path"):
        module.normalize(
            source,
            output,
            expected_sha256=digest,
            source_vintage=module.VINTAGE,
            source_locator=module.SOURCE_LOCATOR,
            observed_at="2026-10-23T00:00:00Z",
        )


@pytest.mark.parametrize(
    ("encryption_state", "page_count"), [("encrypted", 44), ("clear", 43)]
)
def test_normalizer_rejects_encrypted_or_wrong_page_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    encryption_state: str,
    page_count: int,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)

    class Reader:
        is_encrypted = encryption_state == "encrypted"

        def __init__(self, *_: object, **__: object) -> None:
            self.pages = [object() for _ in range(page_count)]

    monkeypatch.setattr(module, "PdfReader", Reader)
    with pytest.raises(ValueError, match="financial_activity_pdf_identity"):
        module.normalize(
            source,
            tmp_path / "silver",
            expected_sha256=digest,
            source_vintage=module.VINTAGE,
            source_locator=module.SOURCE_LOCATOR,
            observed_at="2026-10-23T00:00:00Z",
        )


def test_normalizer_dry_run_does_not_create_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)

    class Page:
        def extract_text(self) -> str:
            return _page()

    class Reader:
        is_encrypted = False

        def __init__(self, *_: object, **__: object) -> None:
            self.pages = [Page() for _ in range(module.PAGE_COUNT)]

    monkeypatch.setattr(module, "PdfReader", Reader)
    output = tmp_path / "silver"
    result = module.normalize(
        source,
        output,
        expected_sha256=digest,
        source_vintage=module.VINTAGE,
        source_locator=module.SOURCE_LOCATOR,
        observed_at="2026-10-23T00:00:00Z",
    )

    assert result["status"] == "planned"
    assert result["counts"] == {"pages": 1, "facts": 14, "lineage": 70}
    assert not output.exists()
