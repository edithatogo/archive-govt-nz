"""Contracts for the pinned 2023/24 Vote Health summary slice."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2023_24 as module,
)

_PAGE_TEXT = """Appropriations and Capital Injections Vote Health
The Supplementary Estimates of Appropriations 2023/24 B.7 483
Total Annual Appropriations and Forecast Permanent Appropriations and Multi -Year Appropriations 2023/24
Estimates Budget $000 Supplementary Estimates Budget $000 Total Budget $000
Total Annual Appropriations and Forecast Permanent Appropriations 25,312,361 1,783,119 27,095,480
Total Forecast MYA Non-Departmental Capital Expenditure 1,197,543 (90,672) 1,106,871
Total Annual Appropriations and Forecast Permanent Appropriations and Multi-Year
Appropriations 26,509,904 1,692,447 28,202,351
Capital Injection Authorisations 2023/24 Estimates Budget $000 Supplementary Estimates Budget $000 Total Budget $000
Ministry of Health - Capital Injection (M36) (A21) - - -
"""
_LABELS = tuple(label for label, _ in module._EXPECTED_ROWS)  # noqa: SLF001


def test_parser_preserves_four_named_rows_and_source_column_tokens() -> None:
    rows = module.parse_summary_page([(5, _PAGE_TEXT)])

    assert tuple(row["summary_label"] for row in rows) == _LABELS
    assert rows[0]["tokens"] == {
        "estimates_budget": "25,312,361",
        "supplementary_estimates_budget": "1,783,119",
        "total_budget": "27,095,480",
    }
    assert rows[2]["tokens"]["total_budget"] == "28,202,351"
    assert (
        rows[3]["source_label"] == "Ministry of Health - Capital Injection (M36) (A21)"
    )


@pytest.mark.parametrize(
    ("pages", "error"),
    [
        ([(4, _PAGE_TEXT)], "vote_health_2023_24_page_span"),
        ([(5, _PAGE_TEXT.replace("2023/24", "2019/20"))], "vote_health_2023_24_layout"),
        (
            [
                (
                    5,
                    _PAGE_TEXT.replace(
                        "Total Forecast MYA Non-Departmental Capital Expenditure",
                        "Missing row",
                    ),
                )
            ],
            "vote_health_2023_24_summary_row",
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

    with pytest.raises(ValueError, match="vote_health_2023_24_identity"):
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
    assert str(facts[0]["estimates_budget"]) == "25312361.000"
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
            "source_page": 5,
            "disposition": "partially_normalized",
            "reason": "four_named_page_five_summary_rows_only",
        }
    ]
