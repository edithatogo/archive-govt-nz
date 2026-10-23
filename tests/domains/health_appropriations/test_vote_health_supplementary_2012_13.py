"""Contracts for the source-pinned 2012/13 financial-activity summary."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2012_13 as module,
)


def _page() -> str:
    return """VOTE HEALTH
Part 1 - Summary of the Vote
Part 1.3 - Trends in the Vote
Summary of Financial Activity
2012/13
Supplementary Estimates
Estimates Departmental Transactions Non-Departmental Transactions Total Transactions Total
$000 $000 $000 $000 $000
Appropriations
Output Expenses 13,808,822 (8,071) (133,978) (142,049) 13,666,773
Benefits and Other Unrequited Expenses - N/A - - -
Borrowing Expenses - - - - -
Other Expenses 27,347 - 1,073 1,073 28,420
Capital Expenditure 288,574 (2,260) 267,378 265,118 553,692
Intelligence and Security Department Expenses and Capital
Expenditure
- - N/A - -
Total Appropriations 14,124,743 (10,331) 134,473 124,142 14,248,885
Crown Revenue and Capital Receipts
Tax Revenue - N/A - - -
Non-Tax Revenue 614,788 N/A 5,504 5,504 620,292
Capital Receipts 36,499 N/A (9,000) (9,000) 27,499
Total Crown Revenue and Capital Receipts 651,287 N/A (3,496) (3,496) 647,791
"""


def test_parser_preserves_sections_all_columns_and_literal_missing_tokens() -> None:
    rows = module.parse_financial_activity([(2, _page())])

    assert len(rows) == 11
    assert rows[0]["source_label"] == "Output Expenses"
    assert rows[0]["tokens"] == {
        "estimates": "13,808,822",
        "departmental_transactions": "(8,071)",
        "non_departmental_transactions": "(133,978)",
        "total_transactions": "(142,049)",
        "total": "13,666,773",
    }
    assert rows[5]["source_label"].endswith("Expenditure")
    assert rows[7]["section"] == "crown_revenue_and_capital_receipts"
    assert rows[7]["tokens"]["departmental_transactions"] == "N/A"


@pytest.mark.parametrize(
    ("pages", "error"),
    [
        ([(1, _page())], "vote_health_2012_13_page_span"),
        ([(2, _page().replace("2012/13", "2011/12"))], "vote_health_2012_13_layout"),
        (
            [
                (
                    2,
                    _page().replace(
                        "Output Expenses 13,808,822", "Outputs Expenses 13,808,822"
                    ),
                )
            ],
            "vote_health_2012_13_row_set",
        ),
    ],
)
def test_parser_fails_closed_on_wrong_page_vintage_or_row(
    pages: list[tuple[int, str]], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        module.parse_financial_activity(pages)


def test_normalizer_writes_facts_lineage_and_page_disposition(
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
    assert receipt["counts"] == {"pages": 1, "facts": 11, "lineage": 55}
    facts = pq.read_table(
        output / "vote_health_financial_activity_facts.parquet"
    ).to_pylist()
    assert facts[0]["departmental_transactions"] == -8071
    assert facts[1]["estimates"] is None
    assert facts[1]["raw_values_json"].find('"N/A"') >= 0
    assert all(row["rights_state"] == "not_evaluated" for row in facts)
    assert len(pq.read_table(output / "field_lineage.parquet").to_pylist()) == 55
    pages = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert pages[0]["disposition"] == "partially_normalized"
