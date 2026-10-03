"""Source-faithful headline contract for the 2002/03 Vote Health overview."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_summary as overview,
)
from archive_govt_nz.domains.health_appropriations.vote_health_estimates_summary import (
    parse_overview_pages,
)


def _pages() -> list[str]:
    return [
        (
            "Appropriations sought for Vote Health in 2002/03 total $8,645.493 million. "
            "This is an increase of $940.846 million. Departmental appropriations total "
            "$166.917 million. $8,432.327 million (97.5% of the Vote) is for the funder. "
            "$26.398 million (0.3% of the Vote) relates to other services."
        ),
        (
            "Crown Revenue and Receipts. $19.851 million (0.2% of the Vote) relates to "
            "other expenses. The Ministry expects to collect $292.005 million of Crown "
            "revenue in 2002/03."
        ),
    ]


def test_overview_extracts_only_seven_phrase_anchored_headlines() -> None:
    pages = _pages()
    pages[0] = (
        pages[0]
        .replace("Vote Health in", "Vote\nHealth in")
        .replace("million. This", "million.\nThis")
    )
    rows = parse_overview_pages(pages)
    assert [row["summary_measure"] for row in rows] == [
        "vote_total",
        "vote_increase",
        "departmental_total",
        "non_departmental_total",
        "other_services_total",
        "other_expenses_total",
        "crown_revenue_total",
    ]
    assert [row["value"] for row in rows] == [
        Decimal("8645.493"),
        Decimal("940.846"),
        Decimal("166.917"),
        Decimal("8432.327"),
        Decimal("26.398"),
        Decimal("19.851"),
        Decimal("292.005"),
    ]
    assert all(row["currency_code"] is None for row in rows)
    assert rows[0]["unit"] == "$ million"
    assert rows[1]["reference_period"] == "2001/02_to_2002/03"
    assert rows[0]["source_phrase"] == (
        "Appropriations sought for Vote\nHealth in 2002/03 total $8,645.493 million"
    )


def test_2004_05_overview_extracts_eight_observed_amounts_without_summing() -> None:
    pages = [
        (
            "Appropriations sought for Vote Health in 2004/05 total $9,917.895 "
            "million, an increase of $332.540 million or 3.47% from 2003/04 "
            "(Supplementary Estimates). Departmental Appropriations. $168.608 "
            "million (1.70% of the Vote) relates to the functions of the Ministry "
            "of Health. $0.955 million (0.01% of the Vote) is a capital contribution "
            "to the Ministry of Health. Non-Departmental Appropriations. $9,748.332 "
            "million (98.29% of the Vote) is for the funders of health services. "
            "$543.703 million (5.48% of the Vote) is to provide capital funding and "
            "loan facilities. $59.666 million (0.60% of the Vote) relates to other "
            "services."
        ),
        (
            "Crown Revenue and Receipts. The Ministry expects to collect $503.067 "
            "million of Crown Revenue and Receipts in 2004/05."
        ),
    ]
    rows = overview.parse_overview_2004_05_pages(pages)
    assert [row["summary_measure"] for row in rows] == [
        "vote_total",
        "vote_increase",
        "departmental_functions",
        "departmental_capital_contribution",
        "non_departmental_total",
        "capital_funding",
        "other_services_total",
        "crown_revenue_total",
    ]
    assert [row["value"] for row in rows] == [
        Decimal("9917.895"),
        Decimal("332.540"),
        Decimal("168.608"),
        Decimal("0.955"),
        Decimal("9748.332"),
        Decimal("543.703"),
        Decimal("59.666"),
        Decimal("503.067"),
    ]
    assert rows[1]["reference_period"] == "2003/04_to_2004/05"
    assert "Supplementary Estimates" in rows[1]["source_phrase"]
    assert all(row["currency_code"] is None for row in rows)


def test_2005_06_overview_extracts_eight_gst_labelled_headlines() -> None:
    pages = [
        (
            "Appropriations sought for Vote Health in 2005/06 total $9,681 million "
            "(GST exclusive), an increase of $824.6 million or 9.3% from 2004/05 "
            "(Supplementary Estimates). Departmental Appropriations (GST exclusive) "
            "$150.198 million (1.55% of the Vote) relates to the functions of the "
            "Ministry of Health. Non-Departmental Appropriations (GST exclusive) "
            "$9,530.767 million (98.45% of the Vote) is for non-departmental expenditure. "
            "Service Funding $9,048.762 million (93.47% of the Vote) is for the funders "
            "of health services."
        ),
        (
            "Other Expenses incurred by the Crown (GST exclusive) "
            "$17.712 million (0.18% of the Vote) is for other expenses. "
            "Capital Funding $464.293 million (4.77% of the Vote) is to provide capital funding. "
            "Crown Revenue and Receipts (GST inclusive). The Ministry expects to "
            "collect $474.340 million of Crown Revenue and Receipts in 2005/06."
        ),
    ]
    rows = overview.parse_overview_2005_06_pages(pages)
    assert [row["summary_measure"] for row in rows] == [
        "vote_total",
        "vote_increase",
        "departmental_functions",
        "non_departmental_total",
        "service_funding_total",
        "other_expenses_total",
        "capital_funding",
        "crown_revenue_total",
    ]
    assert [row["value"] for row in rows] == [
        Decimal(9681),
        Decimal("824.6"),
        Decimal("150.198"),
        Decimal("9530.767"),
        Decimal("9048.762"),
        Decimal("17.712"),
        Decimal("464.293"),
        Decimal("474.340"),
    ]
    assert rows[0]["unit"] == "$ million, GST exclusive"
    assert rows[-1]["unit"] == "$ million, GST inclusive"
    assert rows[1]["reference_period"] == "2004/05_to_2005/06"


def test_2004_05_overview_rejects_missing_or_ambiguous_headlines() -> None:
    pages = [
        "Appropriations sought for Vote Health in 2004/05 total $9,917.895 million",
        (
            "Crown Revenue and Receipts. The Ministry expects to collect $503.067 "
            "million of Crown Revenue and Receipts in 2004/05."
        ),
    ]
    with pytest.raises(ValueError, match="vote_health_estimates_overview_contract"):
        overview.parse_overview_2004_05_pages(pages)


def test_normalizer_dry_run_and_local_write_are_source_pinned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"exactly retained PDF bytes")

    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self, *, extraction_mode: str) -> str:
            assert extraction_mode == "plain"
            return self.text

    class Reader:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.is_encrypted = False
            self.pages = [Page("front matter") for _ in range(44)]
            self.pages[1:3] = [Page(text) for text in _pages()]

    monkeypatch.setattr(
        overview,
        "SOURCE_SHA256",
        __import__("hashlib").sha256(source.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(overview, "PdfReader", Reader)
    operation = {
        "expected_sha256": overview.SOURCE_SHA256,
        "source_vintage": overview.VINTAGE,
        "source_locator": "https://example.test/vote-health.pdf",
        "observed_at": "2026-10-03T00:00:00Z",
    }
    planned = overview.normalize_vote_health_estimates_overview_2002_03(
        source,
        tmp_path / "planned",
        expected_sha256=str(operation["expected_sha256"]),
        source_vintage=str(operation["source_vintage"]),
        source_locator=str(operation["source_locator"]),
        observed_at=str(operation["observed_at"]),
    )
    assert planned["status"] == "planned"
    assert not (tmp_path / "planned").exists()

    written = overview.normalize_vote_health_estimates_overview_2002_03(
        source,
        tmp_path / "out",
        expected_sha256=str(operation["expected_sha256"]),
        source_vintage=str(operation["source_vintage"]),
        source_locator=str(operation["source_locator"]),
        observed_at=str(operation["observed_at"]),
        dry_run=False,
    )
    assert written["status"] == "passed"
    assert len(written["output_sha256"]) == 3  # type: ignore[arg-type]
    facts = pq.read_table(
        tmp_path / "out/vote_health_overview_facts.parquet"
    ).to_pylist()
    lineage = pq.read_table(tmp_path / "out/field_lineage.parquet").to_pylist()
    dispositions = pq.read_table(tmp_path / "out/page_dispositions.parquet").to_pylist()
    assert len(facts) == len(lineage) == 7
    assert facts[0]["value"] == Decimal("8645.493")
    assert facts[0]["currency_code"] is None
    assert facts[0]["rights_state"] == "not_evaluated"
    assert lineage[0]["raw_value"] == "8,645.493"
    assert {row["source_page"] for row in dispositions} == {2, 3}
    assert source.read_bytes() == b"exactly retained PDF bytes"


def test_normalizer_fails_closed_on_wrong_profile_or_output_target(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    operation = {
        "source_vintage": overview.VINTAGE,
        "source_locator": "https://example.test/vote-health.pdf",
        "observed_at": "2026-10-03T00:00:00Z",
    }
    with pytest.raises(ValueError, match="vote_health_estimates_overview_contract"):
        overview.normalize_vote_health_estimates_overview_2002_03(
            source,
            tmp_path / "wrong-profile",
            expected_sha256="0" * 64,
            source_vintage=str(operation["source_vintage"]),
            source_locator=str(operation["source_locator"]),
            observed_at=str(operation["observed_at"]),
        )


def test_2004_05_normalizer_reads_captured_source_and_writes_eight_facts(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/6d/6dac0aaa3fd181fffacf30cffa829b0f189e8b68ebfdbeb0dd5ef88736af96a2"
    )
    if not source.is_file():
        pytest.skip("captured 2004/05 Treasury source is unavailable")
    output = tmp_path / "out"
    result = overview.normalize_vote_health_estimates_overview_2004_05(
        source,
        output,
        expected_sha256=overview.SOURCE_SHA256_2004_05,
        source_vintage=overview.VINTAGE_2004_05,
        source_locator=(
            "https://www.treasury.govt.nz/publications/estimates/"
            "vote-health-estimates-appropriations-2004-05"
        ),
        observed_at="2026-10-03T00:00:00Z",
        dry_run=False,
    )
    facts = pq.read_table(output / "vote_health_overview_facts.parquet").to_pylist()
    assert result["status"] == "passed"
    assert [fact["value"] for fact in facts] == [
        Decimal("9917.895"),
        Decimal("332.540"),
        Decimal("168.608"),
        Decimal("0.955"),
        Decimal("9748.332"),
        Decimal("543.703"),
        Decimal("59.666"),
        Decimal("503.067"),
    ]
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert {row["reason"] for row in dispositions} == {
        "eight_reviewed_overview_headlines_only"
    }


@pytest.mark.parametrize(
    "mutate",
    [
        lambda pages: pages.__setitem__(0, pages[0].replace("million.", "millions.")),
        lambda pages: pages.__setitem__(
            1, pages[1].replace("of Crown revenue", "of other revenue")
        ),
        lambda pages: pages.__setitem__(
            0, pages[0] + " " + pages[0].split("Departmental")[1]
        ),
    ],
)
def test_overview_rejects_unreviewed_or_ambiguous_phrase_changes(
    mutate: Callable[[list[str]], None],
) -> None:
    pages = _pages()
    mutate(pages)
    with pytest.raises(ValueError, match="vote_health_estimates_overview_contract"):
        parse_overview_pages(pages)


def test_2005_06_normalizer_reads_captured_source_and_writes_eight_facts(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/9a/9a269a87a0cef8fc998fc1b012ae9fd734fb48b111504bb7a1ca01cdcf97c2b4"
    )
    if not source.is_file():
        pytest.skip("captured 2005/06 Treasury source is unavailable")
    output = tmp_path / "out"
    result = overview.normalize_vote_health_estimates_overview_2005_06(
        source,
        output,
        expected_sha256=overview.SOURCE_SHA256_2005_06,
        source_vintage=overview.VINTAGE_2005_06,
        source_locator=(
            "https://www.treasury.govt.nz/publications/estimates/"
            "vote-health-estimates-appropriations-2005-06"
        ),
        observed_at="2026-10-03T00:00:00Z",
        dry_run=False,
    )
    facts = pq.read_table(output / "vote_health_overview_facts.parquet").to_pylist()
    assert result["status"] == "passed"
    assert [fact["value"] for fact in facts] == [
        Decimal(9681),
        Decimal("824.6"),
        Decimal("150.198"),
        Decimal("9530.767"),
        Decimal("9048.762"),
        Decimal("17.712"),
        Decimal("464.293"),
        Decimal("474.340"),
    ]
    assert [fact["unit"] for fact in facts] == [
        "$ million, GST exclusive",
        "$ million, GST exclusive",
        "$ million, GST exclusive",
        "$ million, GST exclusive",
        "$ million, GST exclusive",
        "$ million, GST exclusive",
        "$ million, GST exclusive",
        "$ million, GST inclusive",
    ]
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert {row["reason"] for row in dispositions} == {
        "eight_reviewed_overview_headlines_only"
    }


def test_2006_07_overview_extracts_eight_reviewed_headlines() -> None:
    pages = [
        (
            "Appropriations sought for Vote Health in 2006/07 total $10,644.927 "
            "million, an increase of $834.759 million or 8.51% from 2005/06. "
            "Departmental Appropriations $157.408 million (1.48% of the Vote) "
            "relates to the functions of the Ministry of Health. Non-Departmental "
            "Appropriations $10,487.519 million (98.52% of the Vote) is for "
            "operating expenses incurred on behalf of the Crown and is intended "
            "to be spent as follows: Output Expenses $10,083.830 million "
            "(94.73% of the Vote) is for the funders of health services and will "
            "be spent as follows: Other Expenses $22.912 million "
            "(0.22% of the Vote) is for other expenses."
        ),
        (
            "Capital Expenditure $380.777 million (3.58% of the Vote) is to provide "
            "capital funding. Crown Revenue and Receipts: The Ministry expects to "
            "collect $529.194 million of Crown Revenue and Receipts in 2006/07."
        ),
    ]
    rows = overview.parse_overview_2006_07_pages(pages)
    assert [row["summary_measure"] for row in rows] == [
        "vote_total",
        "vote_increase",
        "departmental_functions",
        "non_departmental_total",
        "service_funding_total",
        "other_expenses_total",
        "capital_funding",
        "crown_revenue_total",
    ]
    assert [row["value"] for row in rows] == [
        Decimal("10644.927"),
        Decimal("834.759"),
        Decimal("157.408"),
        Decimal("10487.519"),
        Decimal("10083.830"),
        Decimal("22.912"),
        Decimal("380.777"),
        Decimal("529.194"),
    ]
    assert rows[1]["reference_period"] == "2005/06_to_2006/07"


def test_2006_07_normalizer_reads_captured_source_and_writes_eight_facts(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/86/866bce96ac216344c5dcdf25fee1f31548d5c32ba3cd94ef4b4977a495f509ea"
    )
    if not source.is_file():
        pytest.skip("captured 2006/07 Treasury source is unavailable")
    output = tmp_path / "out"
    result = overview.normalize_vote_health_estimates_overview_2006_07(
        source,
        output,
        expected_sha256=overview.SOURCE_SHA256_2006_07,
        source_vintage=overview.VINTAGE_2006_07,
        source_locator=(
            "https://www.treasury.govt.nz/publications/estimates/"
            "vote-health-estimates-appropriations-2006-07"
        ),
        observed_at="2026-10-03T00:00:00Z",
        dry_run=False,
    )
    facts = pq.read_table(output / "vote_health_overview_facts.parquet").to_pylist()
    assert result["status"] == "passed"
    assert [fact["value"] for fact in facts] == [
        Decimal("10644.927"),
        Decimal("834.759"),
        Decimal("157.408"),
        Decimal("10487.519"),
        Decimal("10083.830"),
        Decimal("22.912"),
        Decimal("380.777"),
        Decimal("529.194"),
    ]
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert {row["reason"] for row in dispositions} == {
        "eight_reviewed_overview_headlines_only"
    }


def test_2007_08_normalizer_reads_captured_source_and_writes_eight_facts(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/fc/fccd1fe0001e12f8238e6c4618328eac2da8d26729f997265b05688ec89a2795"
    )
    if not source.is_file():
        pytest.skip("captured 2007/08 Treasury source is unavailable")
    output = tmp_path / "out"
    result = overview.normalize_vote_health_estimates_overview_2007_08(
        source,
        output,
        expected_sha256=overview.SOURCE_SHA256_2007_08,
        source_vintage=overview.VINTAGE_2007_08,
        source_locator=(
            "https://www.treasury.govt.nz/publications/estimates/"
            "vote-health-estimates-appropriations-2007-08"
        ),
        observed_at="2026-10-03T00:00:00Z",
        dry_run=False,
    )
    facts = pq.read_table(output / "vote_health_overview_facts.parquet").to_pylist()
    assert result["status"] == "passed"
    assert [fact["value"] for fact in facts] == [
        Decimal("11928.703"),
        Decimal("1515.858"),
        Decimal("204.033"),
        Decimal("11724.670"),
        Decimal("10860.491"),
        Decimal("17.912"),
        Decimal("846.267"),
        Decimal("591.403"),
    ]


def test_2008_09_parser_preserves_qualified_rounded_amounts() -> None:
    pages = [
        (
            "The Minister of Health is responsible for appropriations in the Vote "
            "for the 2008/09 financial year totalling just over $12,240 million. "
            "Departmental Operating Appropriations A total of just over $227 "
            "million (1.9% of the Vote) relates to the functions of the Ministry "
            "of Health. Non-Departmental Operating Appropriations A total of "
            "just over $11,768 million (96.1% of the Vote) is for operating "
            "expenses to be incurred on behalf of the Crown. Output Expenses "
            "These total just over $11,745 million (95.9% of the Vote) and are "
            "to fund the purchases of health services. Other Expenses Incurred "
            "by the Crown A total of just over $23 million (0.2% of the Vote) "
            "is for other expenses. Capital Expenditure A total of nearly $244 "
            "million (2.0% of the Vote) is to provide capital funding."
        ),
        "Details of Appropriations",
    ]
    rows = overview.parse_overview_2008_09_pages(pages)
    assert [row["summary_measure"] for row in rows] == [
        "vote_total",
        "departmental_functions",
        "non_departmental_total",
        "service_funding_total",
        "other_expenses_total",
        "capital_funding",
    ]
    assert [row["value"] for row in rows] == [
        Decimal(12240),
        Decimal(227),
        Decimal(11768),
        Decimal(11745),
        Decimal(23),
        Decimal(244),
    ]
    assert "just over" in rows[0]["source_phrase"]
    assert "nearly" in rows[-1]["source_phrase"]
    assert rows[0]["unit"] == "$ million, approximate rounded source amount"


def test_2008_09_normalizer_reads_captured_source_and_marks_approximation(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/2d/2d346a460278fa278eef4fbda3f613d18bc13b486a1f2e21e503a05b5d3f9121"
    )
    if not source.is_file():
        pytest.skip("captured 2008/09 Treasury source is unavailable")
    output = tmp_path / "out"
    result = overview.normalize_vote_health_estimates_overview_2008_09(
        source,
        output,
        expected_sha256=overview.SOURCE_SHA256_2008_09,
        source_vintage=overview.VINTAGE_2008_09,
        source_locator=(
            "https://www.treasury.govt.nz/publications/estimates/"
            "vote-health-estimates-appropriations-2008-09"
        ),
        observed_at="2026-10-03T12:34:00.964355Z",
        dry_run=False,
    )
    facts = pq.read_table(output / "vote_health_overview_facts.parquet").to_pylist()
    assert result["status"] == "passed"
    assert [fact["value"] for fact in facts] == [
        Decimal(12240),
        Decimal(227),
        Decimal(11768),
        Decimal(11745),
        Decimal(23),
        Decimal(244),
    ]
    assert all("source_amount_is_not_exact" in fact["quality_flags"] for fact in facts)
    assert all(
        fact["unit"] == "$ million, approximate rounded source amount" for fact in facts
    )
