"""Contracts for the pinned 2021/22 Vote Health summary slice."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2021_22 as module,
)

_PAGE_TEXT = """Appropriations and Capital Injections Vote Health
The Supplementary Estimates of Appropriations 2021/22 B.7 441
Total Annual Appropriations and Forecast Permanent Appropriations and Multi -Year Appropriations 2021/22
Estimates Budget $000 Supplementary Estimates Budget $000 Total Budget $000
Total Annual Appropriations and Forecast Permanent Appropriations 22,849,935 5,607,854 28,457,789
Total Forecast MYA Non-Departmental Capital Expenditure 1,548,255 (987,176) 561,079
Total Annual Appropriations and Forecast Permanent Appropriations and Multi-Year
Appropriations 24,398,190 4,620,678 29,018,868
Capital Injection Authorisations 2021/22 Estimates Budget $000 Supplementary Estimates Budget $000 Total Budget $000
Ministry of Health - Capital Injection (M36) (A21) 10,013 (5,664) 4,349
"""
_LABELS = tuple(label for label, _ in module._EXPECTED_ROWS)  # noqa: SLF001


def test_parser_preserves_four_named_rows_and_source_column_tokens() -> None:
    rows = module.parse_summary_page([(7, _PAGE_TEXT)])

    assert tuple(row["summary_label"] for row in rows) == _LABELS
    assert rows[0]["tokens"] == {
        "estimates_budget": "22,849,935",
        "supplementary_estimates_budget": "5,607,854",
        "total_budget": "28,457,789",
    }
    assert rows[2]["tokens"]["total_budget"] == "29,018,868"
    assert (
        rows[3]["source_label"] == "Ministry of Health - Capital Injection (M36) (A21)"
    )


@pytest.mark.parametrize(
    ("pages", "error"),
    [
        ([(6, _PAGE_TEXT)], "vote_health_2021_22_page_span"),
        ([(7, _PAGE_TEXT.replace("2021/22", "2019/20"))], "vote_health_2021_22_layout"),
        (
            [
                (
                    7,
                    _PAGE_TEXT.replace(
                        "Total Forecast MYA Non-Departmental Capital Expenditure",
                        "Missing row",
                    ),
                )
            ],
            "vote_health_2021_22_summary_row",
        ),
    ],
)
def test_parser_fails_closed_on_page_period_or_row_drift(
    pages: list[tuple[int, str]], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        module.parse_summary_page(pages)


def test_normalizer_rejects_unpinned_locator(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture bytes")

    with pytest.raises(ValueError, match="vote_health_2021_22_identity"):
        module.normalize(
            source,
            tmp_path / "silver",
            expected_sha256=module.SOURCE_SHA256,
            source_vintage=module.VINTAGE,
            source_locator="https://example.invalid/wrong.pdf",
            observed_at="2026-10-06T00:00:00Z",
        )


def test_normalizer_emits_summary_facts_lineage_and_page_disposition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture bytes")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)

    class Page:
        def extract_text(self) -> str:
            return _PAGE_TEXT

    class Reader:
        is_encrypted = False

        def __init__(self) -> None:
            self.pages = [Page() for _ in range(module.PAGE_COUNT)]

    monkeypatch.setattr(module, "PdfReader", lambda *_args, **_kwargs: Reader())
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
        output / "vote_health_supplementary_summary_facts.parquet"
    ).to_pylist()
    assert len(facts) == 4
    assert facts[0]["recordset"] == "vote_health_supplementary_summary_fact"
    assert str(facts[0]["estimates_budget"]) == "22849935.000"
    assert facts[0]["rights_state"] == "not_evaluated"
    assert "source_reported_summary_total" in facts[0]["quality_flags"]
    assert (
        "source_reported_capital_injection_authorisation" in facts[3]["quality_flags"]
    )
    assert "source_reported_summary_total" not in facts[3]["quality_flags"]
    assert len(pq.read_table(output / "field_lineage.parquet").to_pylist()) == 12
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert dispositions == [
        {
            "source_object_sha256": digest,
            "source_locator": module.SOURCE_LOCATOR,
            "source_page": 7,
            "disposition": "partially_normalized",
            "reason": "four_named_page_seven_summary_rows_only",
        }
    ]
