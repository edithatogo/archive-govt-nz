"""Common-dispatch contract for the reviewed Vote Health source PDF."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_vote_health import TEXT
from tests.domains.health_appropriations.test_vote_health_revenue import _pages

from archive_govt_nz.domains.health_appropriations import (
    vote_health,
    vote_health_estimates_2002_03_adapter,
    vote_health_pdf_adapter,
    vote_health_revenue,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)
from archive_govt_nz.domains.health_appropriations.vote_health_estimates_2002_03_adapter import (
    VoteHealthEstimates2002TablesAdapter,
)
from archive_govt_nz.domains.health_appropriations.vote_health_pdf_adapter import (
    vote_health_pdf_registration,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
        AdapterRegistration,
    )

VINTAGE = "Treasury-Vote-Health-Supplementary-2003-04"
OBSERVED_AT = "2026-08-29T19:31:00Z"


def _pdf_pages() -> list[str]:
    pages = ["front matter"] * 22
    pages[1] = TEXT
    pages[4] = (
        "Part B1 - Details of Appropriations\n"
        "Sector Policy 12,459 - 110 - 12,569 - Source reason prose."
    )
    pages[5] = "Part E - Statement of Intent"
    pages[19:21] = _pages()
    return pages


class _Page:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self, *, extraction_mode: str) -> str:
        assert extraction_mode in {"layout", "plain"}
        return self.text


class _Reader:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        self.is_encrypted = False
        self.pages = [_Page(text) for text in _pdf_pages()]


def _registration() -> AdapterRegistration:
    return vote_health_pdf_registration(
        source_locator="https://example.test/supp04health.pdf",
        source_vintage=VINTAGE,
        observed_at=OBSERVED_AT,
    )


def test_one_registered_pdf_adapter_emits_three_table_profiles_repeatably(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(vote_health_pdf_adapter, "PdfReader", _Reader)
    bronze = b"%PDF-1.7\nreviewed source fixture"
    original = bytes(bronze)
    digest = hashlib.sha256(bronze).hexdigest()
    registrations = (_registration(),)

    first = dispatch_bronze(
        bronze,
        source_sha256=digest,
        media_type="application/pdf",
        registrations=registrations,
    )
    repeated = dispatch_bronze(
        bronze,
        source_sha256=digest,
        media_type="application/pdf",
        registrations=registrations,
    )

    assert first.selection.status == "selected"
    assert first.selection.adapter_id == "nz-treasury-vote-health-2003-04-tables"
    assert first.output == repeated.output
    assert bronze == original
    assert len(first.output.records) == 22
    recordsets = [row["recordset"] for row in first.output.records]
    assert recordsets.count("vote_health_appropriation_summary_fact") == 4
    assert recordsets.count("vote_health_appropriation_detail_fact") == 1
    assert recordsets.count("vote_health_crown_revenue_fact") == 17
    assert first.output.records[0]["source_object_sha256"] == digest
    total = next(
        row
        for row in first.output.records
        if row.get("appropriation_type") == "Total Appropriations for 2003/04"
    )
    assert total["total_appropriations"] == 9_585_355
    assert any(
        row.source_coordinate == "pdf:page=5"
        and row.disposition == "partially_normalized"
        for row in first.output.losses
    )
    assert any(
        row.source_coordinate == "pdf:page=6" and row.disposition == "preserved_only"
        for row in first.output.losses
    )
    assert len(first.output.lineage) == 77


def test_pdf_adapter_is_fail_closed_on_vintage_and_fixity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(vote_health_pdf_adapter, "PdfReader", _Reader)
    bronze = b"%PDF-1.7\nreviewed source fixture"
    digest = hashlib.sha256(bronze).hexdigest()
    wrong_vintage = vote_health_pdf_registration(
        source_locator="source.pdf",
        source_vintage="Treasury-Vote-Health-Estimates-2003-04",
        observed_at=OBSERVED_AT,
    )
    selected = dispatch_bronze(
        bronze,
        source_sha256=digest,
        media_type="application/pdf",
        registrations=(wrong_vintage,),
    )
    assert selected.selection.status == "preserved_only"
    assert selected.selection.reason == "no_matching_layout"
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        _registration().adapter.extract(bronze, source_sha256="0" * 64)


def test_dispatch_records_match_the_three_existing_pdf_normalizers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(vote_health_pdf_adapter, "PdfReader", _Reader)
    monkeypatch.setattr(vote_health, "PdfReader", _Reader)
    monkeypatch.setattr(vote_health_revenue, "PdfReader", _Reader)
    bronze = b"%PDF-1.7\nreviewed source fixture"
    digest = hashlib.sha256(bronze).hexdigest()
    source = tmp_path / "vote-health.pdf"
    source.write_bytes(bronze)
    context = {
        "expected_sha256": digest,
        "source_vintage": VINTAGE,
        "source_locator": "https://example.test/supp04health.pdf",
        "observed_at": OBSERVED_AT,
        "dry_run": False,
    }
    expected = []
    expected_lineage = []
    for output_name, normalizer in (
        (
            "summary",
            lambda output: vote_health.normalize_vote_health_summary(
                source, output, **context
            ),
        ),
        (
            "detail",
            lambda output: vote_health.normalize_vote_health_detail(
                source, output, **context
            ),
        ),
        (
            "revenue",
            lambda output: vote_health_revenue.normalize_vote_health_revenue(
                source, output, **context
            ),
        ),
    ):
        output = tmp_path / output_name
        normalizer(output)
        fact_file = {
            "summary": "vote_health_summary_facts.parquet",
            "detail": "vote_health_detail_facts.parquet",
            "revenue": "vote_health_revenue_facts.parquet",
        }[output_name]
        expected.extend(pq.read_table(output / fact_file).to_pylist())
        expected_lineage.extend(
            pq.read_table(output / "field_lineage.parquet").to_pylist()
        )

    actual = _registration().adapter.extract(bronze, source_sha256=digest)
    assert sorted(actual.records, key=lambda row: str(row["record_id"])) == sorted(
        expected, key=lambda row: str(row["record_id"])
    )
    assert sorted(
        (
            row.record_id,
            row.field,
            row.source_coordinate,
            row.raw_value,
            row.normalized_value,
            row.rule,
        )
        for row in actual.lineage
    ) == sorted(
        (
            str(row["record_id"]),
            str(row["field"]),
            str(row["source_coordinate"]),
            row["raw_value"],
            row["normalized_value"],
            str(row["rule"]),
        )
        for row in expected_lineage
    )


def test_context_registry_can_include_exact_vote_health_pdf() -> None:
    registrations = context_adapter_registrations(
        cpi=AdapterContext("cpi.csv", "2026-Q2", OBSERVED_AT),
        population=AdapterContext("population.csv", "2026-08-18", OBSERVED_AT),
        qes=AdapterContext("qes.xlsx", "QES-2026-Q2", OBSERVED_AT),
        gdp=AdapterContext("gdp.xlsx", "GDP-March-2026", OBSERVED_AT),
        vote_health=AdapterContext("vote-health.pdf", VINTAGE, OBSERVED_AT),
    )
    assert "nz-treasury-vote-health-2003-04-tables" in {
        row.adapter_id for row in registrations
    }


def test_context_registry_can_include_estimates_2002_03_profile() -> None:
    registrations = context_adapter_registrations(
        cpi=AdapterContext("cpi.csv", "2026-Q2", OBSERVED_AT),
        population=AdapterContext("population.csv", "2026-08-18", OBSERVED_AT),
        qes=AdapterContext("qes.xlsx", "QES-2026-Q2", OBSERVED_AT),
        gdp=AdapterContext("gdp.xlsx", "GDP-March-2026", OBSERVED_AT),
        vote_health_estimates_2002_03=AdapterContext(
            "est02health.pdf", vote_health.DETAIL_VINTAGE_2002_03, OBSERVED_AT
        ),
    )
    registration = next(
        row for row in registrations if "estimates-2002-03" in row.adapter_id
    )
    assert registration.adapter_id == "nz-treasury-vote-health-estimates-2002-03-tables"
    assert registration.media_type == "application/pdf"


def test_estimates_2002_03_common_adapter_emits_complete_rows_and_all_page_losses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bronze = b"synthetic pinned 2002/03 PDF bytes"
    digest = hashlib.sha256(bronze).hexdigest()
    pages = ["front matter"] * 44
    pages[15] = "Part B1 - Details of Appropriations"
    pages[41] = "Part E - Statement"
    pages[42] = "Part F - Crown Revenue and Receipts"
    pages[43] = "Part F1 - Current and Capital Revenue and Receipts (continued)"

    class Reader:
        is_encrypted = False

        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.pages = [_Page(text) for text in pages]

    def parse_detail_page(text: str, **_kwargs: object) -> list[dict[str, Any]]:
        if text != pages[15]:
            return []
        return [
            {
                "appropriation_name": f"Appropriation {number}",
                "tokens": {
                    "department_annual": "1",
                    "department_other": "-",
                    "non_departmental_annual": "3",
                    "non_departmental_other": "4",
                    "total_appropriations": "8",
                    "change": "0",
                },
            }
            for number in range(27)
        ]

    monkeypatch.setattr(vote_health_estimates_2002_03_adapter, "PdfReader", Reader)
    monkeypatch.setattr(vote_health_estimates_2002_03_adapter, "_SOURCE_SHA256", digest)
    monkeypatch.setattr(vote_health, "parse_detail_page", parse_detail_page)
    monkeypatch.setattr(
        vote_health_revenue,
        "parse_estimates_2002_03_revenue_pages",
        lambda _texts: [
            {
                "source_page": 43 + number // 9,
                "revenue_name": (
                    "Total Capital Receipts"
                    if number == 14
                    else "Total Crown Revenue and Receipts"
                    if number == 15
                    else f"Revenue {number}"
                ),
                "tokens": {
                    "prior_year_budgeted": "1",
                    "prior_year_estimated_actual": "-",
                    "current_year_budgeted": "3",
                },
            }
            for number in range(16)
        ],
    )
    adapter = VoteHealthEstimates2002TablesAdapter(
        "https://example.test/est02health.pdf",
        vote_health.DETAIL_VINTAGE_2002_03,
        OBSERVED_AT,
    )

    output = adapter.extract(bronze, source_sha256=digest)

    assert adapter.matches_layout(bronze)
    assert len(output.records) == 43
    assert output.records[0]["department_other"] is None
    assert output.records[0]["rights_state"] == "not_evaluated"
    assert len(output.lineage) == 210
    assert len(output.losses) == 44
    assert output.losses[15].disposition == "partially_normalized"
    assert output.losses[42].disposition == "normalized"
    assert output.losses[43].disposition == "normalized"
    assert output.losses[15].reason == "complete_six_value_rows_only"
    assert output.losses[0].disposition == "preserved_only"


def test_estimates_2002_03_common_adapter_fails_closed_on_layout_and_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bronze = b"synthetic pinned 2002/03 PDF bytes"
    digest = hashlib.sha256(bronze).hexdigest()
    monkeypatch.setattr(vote_health_estimates_2002_03_adapter, "_SOURCE_SHA256", digest)
    monkeypatch.setattr(
        vote_health_estimates_2002_03_adapter,
        "PdfReader",
        lambda *_args, **_kwargs: type("Reader", (), {"is_encrypted": True})(),
    )
    adapter = VoteHealthEstimates2002TablesAdapter(
        "https://example.test/est02health.pdf",
        vote_health.DETAIL_VINTAGE_2002_03,
        OBSERVED_AT,
    )

    output = adapter.extract(bronze, source_sha256=digest)

    assert not adapter.matches_layout(bronze)
    assert output.records == ()
    assert output.losses[0].disposition == "preserved_only"
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        adapter.extract(bronze, source_sha256="0" * 64)
