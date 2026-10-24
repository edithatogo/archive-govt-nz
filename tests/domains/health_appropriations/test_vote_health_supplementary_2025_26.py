"""Contracts for the pinned 2025/26 Vote Health summary slice."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2025_26 as module,
)

_PAGE_TEXT = """The Supplementary Estimates of Appropriations 2025/26
Total Annual Appropriations and Forecast Permanent Appropriations and Multi -Year Appropriations
2025/26 Estimates Budget $000 Supplementary Estimates Budget $000 Total Budget $000
Total Annual Appropriations and Forecast Permanent Appropriations 28,832,736 873,096 29,705,832
Total Forecast MYA Departmental Output Expenses 6,823 450 7,273
Total Forecast MYA Non-Departmental Output Expenses 25,670 - 25,670
Total Forecast MYA Non-Departmental Capital Expenditure 2,186,988 4,357 2,191,345
Total Annual Appropriations and Forecast Permanent Appropriations and Multi-Year
Appropriations 31,052,217 877,903 31,930,120
Capital Injection Authorisations 2025/26 Estimates Budget $000 Supplementary Estimates Budget $000 Total Budget $000
Ministry of Health - Capital Injection (M36) (A21) - 707 707
"""


def test_parser_preserves_six_named_rows_and_source_column_tokens() -> None:
    rows = module.parse_summary_page([(6, _PAGE_TEXT)])

    assert len(rows) == 6
    assert rows[0]["tokens"] == {
        "estimates_budget": "28,832,736",
        "supplementary_estimates_budget": "873,096",
        "total_budget": "29,705,832",
    }
    assert rows[2]["tokens"]["supplementary_estimates_budget"] == "-"
    assert rows[4]["tokens"]["total_budget"] == "31,930,120"
    assert rows[5]["source_label"].endswith("(M36) (A21)")


@pytest.mark.parametrize(
    ("pages", "error"),
    [
        ([(5, _PAGE_TEXT)], "vote_health_2025_26_page_span"),
        ([(6, _PAGE_TEXT.replace("2025/26", "2019/20"))], "vote_health_2025_26_layout"),
        (
            [
                (
                    6,
                    _PAGE_TEXT.replace(
                        "Total Forecast MYA Non-Departmental Output Expenses",
                        "Missing row",
                    ),
                )
            ],
            "vote_health_2025_26_summary_row",
        ),
    ],
)
def test_parser_fails_closed_on_page_period_or_row_drift(
    pages: list[tuple[int, str]], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        module.parse_summary_page(pages)


def test_parser_fails_closed_when_summary_rows_are_reordered() -> None:
    first = "Total Annual Appropriations and Forecast Permanent Appropriations 28,832,736 873,096 29,705,832"
    second = "Total Forecast MYA Departmental Output Expenses 6,823 450 7,273"
    text = _PAGE_TEXT.replace(f"{first}\n{second}", f"{second}\n{first}")

    with pytest.raises(ValueError, match="vote_health_2025_26_summary_order"):
        module.parse_summary_page([(6, text)])


def test_normalizer_rejects_unpinned_locator(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture bytes")

    with pytest.raises(ValueError, match="vote_health_2025_26_identity"):
        module.normalize(
            source,
            tmp_path / "silver",
            expected_sha256=module.SOURCE_SHA256,
            source_vintage=module.VINTAGE,
            source_locator="https://example.invalid/wrong.pdf",
            observed_at="2026-10-06T00:00:00Z",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_vintage", "wrong-vintage"),
        ("expected_sha256", "0" * 64),
    ],
)
def test_normalizer_rejects_unpinned_identity_fields(
    tmp_path: Path, field: str, value: str
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture bytes")
    kwargs = {
        "expected_sha256": module.SOURCE_SHA256,
        "source_vintage": module.VINTAGE,
        "source_locator": module.SOURCE_LOCATOR,
        "observed_at": "2026-10-06T00:00:00Z",
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match="vote_health_2025_26_identity"):
        module.normalize(source, tmp_path / "silver", **kwargs)  # type: ignore[arg-type]


def test_normalizer_rejects_preexisting_output(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture bytes")
    output = tmp_path / "silver"
    output.mkdir()
    with pytest.raises(ValueError, match="vote_health_2025_26_path"):
        module.normalize(
            source,
            output,
            expected_sha256=module.SOURCE_SHA256,
            source_vintage=module.VINTAGE,
            source_locator=module.SOURCE_LOCATOR,
            observed_at="2026-10-06T00:00:00Z",
        )


def test_normalizer_rejects_missing_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="vote_health_2025_26_path"):
        module.normalize(
            tmp_path / "missing.pdf",
            tmp_path / "silver",
            expected_sha256=module.SOURCE_SHA256,
            source_vintage=module.VINTAGE,
            source_locator=module.SOURCE_LOCATOR,
            observed_at="2026-10-06T00:00:00Z",
        )


@pytest.mark.parametrize("case", ["encrypted", "wrong_page_count"])
def test_normalizer_rejects_encrypted_or_wrong_page_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture bytes")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", digest)

    class Reader:
        def __init__(self) -> None:
            self.is_encrypted = case == "encrypted"
            count = module.PAGE_COUNT - int(case == "wrong_page_count")
            self.pages = [object() for _ in range(count)]

    monkeypatch.setattr(module, "PdfReader", lambda *_args, **_kwargs: Reader())
    with pytest.raises(ValueError, match="vote_health_2025_26_pdf_identity"):
        module.normalize(
            source,
            tmp_path / "silver",
            expected_sha256=digest,
            source_vintage=module.VINTAGE,
            source_locator=module.SOURCE_LOCATOR,
            observed_at="2026-10-06T00:00:00Z",
        )


def test_normalizer_emits_six_rows_and_complete_cell_lineage(
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

        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.pages = [Page() for _ in range(module.PAGE_COUNT)]

    monkeypatch.setattr(module, "PdfReader", Reader)
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

    facts = pq.read_table(
        output / "vote_health_supplementary_summary_facts.parquet"
    ).to_pylist()
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert receipt["counts"] == {"pages": 1, "facts": 6}
    assert len(facts) == 6
    assert facts[2]["supplementary_estimates_budget"] is None
    assert len(lineage) == 18
    assert {row["source_page"] for row in dispositions} == {6}
    assert dispositions[0]["reason"] == "six_named_page_six_summary_rows_only"


def test_normalizer_dry_run_returns_plan_without_creating_outputs(
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

        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.pages = [Page() for _ in range(module.PAGE_COUNT)]

    monkeypatch.setattr(module, "PdfReader", Reader)
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
    assert receipt["counts"] == {"pages": 1, "facts": 6}
    assert not output.exists()
