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
    assert rows[2]["source_qualifier_preserved"] is False
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
    assert rows[2]["source_qualifier_preserved"] is False


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
    assert {row["source_page"] for row in dispositions} == set(range(1, 45))
    assert (
        sum(row["disposition"] == "partially_normalized" for row in dispositions) == 2
    )
    assert (
        sum(row["disposition"] == "preserved_unreviewed" for row in dispositions) == 42
    )
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
        "eight_reviewed_overview_headlines_only",
        "not_reviewed_by_overview_profile",
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
        "eight_reviewed_overview_headlines_only",
        "not_reviewed_by_overview_profile",
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
    assert rows[2]["source_qualifier_preserved"] is False


def test_2007_08_exact_departmental_phrase_is_not_marked_as_qualified() -> None:
    pages = [
        (
            "Appropriations sought for Vote Health in 2007/08 total $12.345 million, "
            "an increase of $1.234 million or 14.56% from 2006/07. $123.456 million "
            "(1.71% of the Vote) relates to the functions of the Ministry of Health. "
            "$12.222 million (98.29% of the Vote) is for expenses incurred on behalf "
            "of the Crown. $11.111 million (91.05% of the Vote) is for funding and "
            "purchases of health services."
        ),
        (
            "Crown Revenue and Receipts. $0.018 million (0.15% of the Vote) is for "
            "other expenses. $1.234 million (7.09% of the Vote) is to provide "
            "capital funding. The Ministry expects to collect $0.456 million of "
            "Crown Revenue and Receipts in 2007/08."
        ),
    ]
    rows = overview.parse_overview_2007_08_pages(pages)
    departmental = next(
        row for row in rows if row["summary_measure"] == "departmental_functions"
    )
    assert departmental["source_qualifier_preserved"] is False


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
        "eight_reviewed_overview_headlines_only",
        "not_reviewed_by_overview_profile",
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
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert len(dispositions) == overview.PAGE_COUNT_2008_09
    assert {row["source_page"] for row in dispositions} == set(
        range(1, overview.PAGE_COUNT_2008_09 + 1)
    )
    assert {
        row["source_page"]
        for row in dispositions
        if row["disposition"] == "partially_normalized"
    } == {2}
    assert (
        sum(row["disposition"] == "preserved_unreviewed" for row in dispositions) == 7
    )


def test_2010_11_normalizer_rebuilds_selected_headlines_from_pinned_bronze_source(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/5d/5dabf866e4f60c5fdf9df88b3fcc5b0e537652d1d6817465efb46a97c0bbe497"
    )
    if not source.is_file():
        pytest.skip("captured 2010/11 Treasury source is unavailable")
    output = tmp_path / "out"
    result = overview.normalize_vote_health_estimates_overview_2010_11(
        source,
        output,
        expected_sha256=overview.SOURCE_SHA256_2010_11,
        source_vintage=overview.VINTAGE_2010_11,
        source_locator=(
            "https://www.treasury.govt.nz/publications/estimates/"
            "vote-health-estimates-appropriations-2010-11"
        ),
        observed_at="2026-10-03T18:31:59.293780Z",
        dry_run=False,
    )
    facts = pq.read_table(output / "vote_health_overview_facts.parquet").to_pylist()
    assert result["status"] == "passed"
    assert result["counts"] == {"pages": 2, "facts": 18}
    assert [fact["value"] for fact in facts] == [
        Decimal(13574),
        Decimal(858),
        Decimal(216),
        Decimal(12847),
        Decimal(12815),
        Decimal(10044),
        Decimal(970),
        Decimal(517),
        Decimal(905),
        Decimal(20),
        Decimal(95),
        Decimal(182),
        Decimal(83),
        Decimal(32),
        Decimal(511),
        Decimal(478),
        Decimal(15),
        Decimal(18),
    ]
    assert [fact["source_page"] for fact in facts] == [
        *([2] * 14),
        *([3] * 4),
    ]
    assert [
        "source_qualifier_preserved_in_raw_phrase" in fact["quality_flags"]
        for fact in facts
    ] == [
        True,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
    ]
    assert all("source_amount_is_not_exact" in fact["quality_flags"] for fact in facts)
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert len(dispositions) == overview.PAGE_COUNT_2010_11
    assert {row["source_page"] for row in dispositions} == set(
        range(1, overview.PAGE_COUNT_2010_11 + 1)
    )
    assert {
        row["source_page"]
        for row in dispositions
        if row["disposition"] == "partially_normalized"
    } == {2, 3}
    assert (
        sum(row["disposition"] == "preserved_unreviewed" for row in dispositions) == 7
    )


def test_2011_12_parser_keeps_selected_overview_values_and_qualifier_contract() -> None:
    page_two = """
    Appropriations sought for Vote Health in 2011/12 financial year
    totalling just over $13,953 million covering the following:
    Departmental Operating Appropriations
    A total of almost $205 million (1.5% of the Vote) relates to the functions
    of the Ministry of Health
    Non-Departmental Operating Appropriations
    A total of nearly $13,295 million (95.3% of the Vote) is for operating
    expenses to be incurred on behalf of the Crown
    Output Expenses
    These total nearly $13,267 million (95.1% of the Vote)
    Just over $10,498 million (75.2% of the Vote) to fund health services from DHBs
    Just over $1,028 million (7.4% of the Vote) to purchase national disability
    support services
    Just over $443 million (3.2% of the Vote) to purchase public health services
    Just over $807 million (5.8% of the Vote) to purchase national health services
    and to manage health sector risks
    Just under $156 million (1.1% of the Vote) to provide clinical training for
    health professionals
    $80 million (0.6% of the Vote) for a provision for DHB deficit support
    Nearly $179 million (1.3% of the Vote) to purchase primary health care services
    Just over $76 million (0.5% of the Vote) to fund other health and disability
    services
    Other Expenses Incurred by the Crown
    A total of nearly $28 million (0.2% of the Vote) is for other expenses
    """
    page_three = """
    Capital Expenditure
    Almost $454 million (3.3% of the Vote) is to provide capital funding
    Almost $419 million (3.1 % of the Vote) is to provide debt or equity for
    District Health Boards
    $15 million (0.1% of the Vote) is to provide interest-free loans to assist
    people in long term care
    Just over $20 million (0.1% of the Vote) is to purchase or develop assets
    for use by the Ministry of Health
    """
    rows = overview.parse_overview_2011_12_pages([page_two, page_three])
    assert [row["value"] for row in rows] == [
        Decimal(13953),
        Decimal(205),
        Decimal(13295),
        Decimal(13267),
        Decimal(10498),
        Decimal(1028),
        Decimal(443),
        Decimal(807),
        Decimal(156),
        Decimal(80),
        Decimal(179),
        Decimal(76),
        Decimal(28),
        Decimal(454),
        Decimal(419),
        Decimal(15),
        Decimal(20),
    ]
    assert [row["source_page"] for row in rows] == [*([2] * 13), *([3] * 4)]
    assert [row["source_qualifier_preserved"] for row in rows] == [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
    ]


def test_2012_13_parser_keeps_rounded_overview_values_and_source_qualifiers() -> None:
    page_two = """
    Overview of the Vote
    The Minister of Health is responsible for appropriations in the Vote for the
    2012/13 financial year totalling nearly $14,125 million covering the following:
    Departmental Operating Appropriations
    A total of nearly $191 million (1.4% of the Vote) relates to the functions
    of the Ministry of Health
    Non-Departmental Operating Appropriations
    A total of just over $13,645 million (96.6% of the Vote) is for operating
    expenses to be incurred on behalf of the Crown
    Output Expenses
    These total nearly $13,618 million (96.4% of the Vote)
    just over $10,819 million (76.6% of the Vote) to fund health services from DHBs
    nearly $1,053 million (7.5% of the Vote) to purchase national disability support services
    just over $800 million (5.7% of the Vote) to purchase national health services
    and provide clinical training for health professionals
    just over $476 million (3.4% of the Vote) to purchase public health services
    nearly $176 million (1.2% of the Vote) to purchase primary health care services
    just over $145 million (1.0% of the Vote) to purchase national maternity services
    $65 million (0.5% of the Vote) for a provision for DHB deficit support
    $52 million (0.4% of the Vote) to manage health sector risks
    just over $31 million (0.2% of the Vote) to fund other health and disability services
    Other Expenses Incurred by the Crown
    A total of just over $27 million (0.2% of the Vote) is for other expenses
    """
    page_three = """
    Capital Expenditure
    A total of nearly $289 million (2.0% of the Vote) is to provide Capital funding
    nearly $259 million (1.8% of the Vote) is to provide debt or equity for district
    health boards or Health Sector Crown Agencies
    $15 million (0.1% of the Vote) is to provide interest-free loans to assist
    people in long-term care
    $15 million (0.1% of the Vote) is to purchase or develop assets for use by
    the Ministry of Health
    """
    rows = overview.parse_overview_2012_13_pages([page_two, page_three])
    assert [row["value"] for row in rows] == [
        Decimal(14125),
        Decimal(191),
        Decimal(13645),
        Decimal(13618),
        Decimal(10819),
        Decimal(1053),
        Decimal(800),
        Decimal(476),
        Decimal(176),
        Decimal(145),
        Decimal(65),
        Decimal(52),
        Decimal(31),
        Decimal(27),
        Decimal(289),
        Decimal(259),
        Decimal(15),
        Decimal(15),
    ]
    assert [row["source_page"] for row in rows] == [*([2] * 14), *([3] * 4)]
    assert all(row["source_qualifier_preserved"] for row in rows)


def test_2012_13_normalizer_rebuilds_selected_headlines_from_pinned_bronze_source(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/59/5994108997ead9f301f71f73952b8fb04f6b1e4a00207c16dfe8b172f72b60ff"
    )
    if not source.is_file():
        pytest.skip("captured 2012/13 Treasury source is unavailable")
    result = overview.normalize_vote_health_estimates_overview_2012_13(
        source,
        tmp_path / "silver",
        expected_sha256=overview.SOURCE_SHA256_2012_13,
        source_vintage=overview.VINTAGE_2012_13,
        source_locator="https://www.treasury.govt.nz/publications/estimates/vote-health-estimates-appropriations-2012-13",
        observed_at="2026-10-03T22:37:57.436271Z",
        dry_run=False,
    )
    assert result["status"] == "passed"
    assert result["counts"] == {"pages": 2, "facts": 18}
    assert [
        row["disposition"]
        for row in pq.read_table(
            tmp_path / "silver/page_dispositions.parquet"
        ).to_pylist()
    ].count("preserved_unreviewed") == 6


def test_2013_14_parser_preserves_exact_rounded_overview_phrases() -> None:
    page_two = """
    Overview of the Vote
    The Minister of Health is responsible for appropriations in the Vote for the
    2013/14 financial year totalling nearly $14,656 million covering the following:
    Departmental Operating Appropriations
    A total of just over $191 million (1.3% of the Vote) relates to the functions
    of the Ministry of Health for policy advice and information services.
    Non-Departmental Operating Appropriations
    A total of just over $13,944 million (95.1% of the Vote) is for operating expenses
    to be incurred on behalf of the Crown and is intended to be spent as follows.
    Output Expenses
    These total nearly $13,916 million (95.0% of the Vote) and are to fund health services.
    just over $11,104 million (75.8% of the Vote) to fund health services from DHBs
    just over $1,103 million (7.5% of the Vote) to purchase national disability support services
    just over $808 million (5.5% of the Vote) to purchase national health services
    and provide clinical training for health professionals
    just over $442 million (3.0% of the Vote) to purchase public health services
    nearly $179 million (1.2% of the Vote) to purchase primary health care services
    just over $144 million (1.0% of the Vote) to purchase national maternity services
    $90 million (0.6% of the Vote) to manage health sector risks, including provision
    for DHB deficit support, and
    just over $44 million (0.3% of the Vote) to fund other health and disability services.
    Other Expenses Incurred by the Crown
    A total of just over $28 million (0.2% of the Vote) is for other expenses
    to fund provider development, legal expenses, and international obligations.
    """
    page_three = """
    Capital Expenditure
    A total of just over $520 million (3.6% of the Vote) is to provide Capital funding
    just over $490 million (3.3% of the Vote) is to provide debt or equity for district
    health boards or Health Sector Crown Agencies
    $15 million (0.1% of the Vote) is to provide interest-free loans to assist people
    in long-term care
    just over $15 million (0.1% of the Vote) is to purchase or develop assets for use
    by the Ministry of Health.
    """
    rows = overview.parse_overview_2013_14_pages([page_two, page_three])
    assert [row["value"] for row in rows] == [
        Decimal(14656),
        Decimal(191),
        Decimal(13944),
        Decimal(13916),
        Decimal(11104),
        Decimal(1103),
        Decimal(808),
        Decimal(442),
        Decimal(179),
        Decimal(144),
        Decimal(90),
        Decimal(44),
        Decimal(28),
        Decimal(520),
        Decimal(490),
        Decimal(15),
        Decimal(15),
    ]
    assert [row["source_page"] for row in rows] == [*([2] * 13), *([3] * 4)]
    assert [row["source_qualifier_preserved"] for row in rows] == [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        True,
        False,
        True,
    ]


def test_2013_14_normalizer_rebuilds_from_pinned_bronze_source(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/f2/f29271aad328bad5fcfdcf655c61dc6c59600a20666860c037ceb478bff681f1"
    )
    if not source.is_file():
        pytest.skip("captured 2013/14 Treasury source is unavailable")
    result = overview.normalize_vote_health_estimates_overview_2013_14(
        source,
        tmp_path / "silver",
        expected_sha256=overview.SOURCE_SHA256_2013_14,
        source_vintage=overview.VINTAGE_2013_14,
        source_locator="https://www.treasury.govt.nz/publications/estimates/vote-health-estimates-appropriations-2013-14",
        observed_at="2026-10-04T00:04:54.340387Z",
        dry_run=False,
    )
    assert result["status"] == "passed"
    assert result["counts"] == {"pages": 2, "facts": 17}
    dispositions = pq.read_table(
        tmp_path / "silver/page_dispositions.parquet"
    ).to_pylist()
    assert [row["disposition"] for row in dispositions].count(
        "partially_normalized"
    ) == 2
    assert [row["disposition"] for row in dispositions].count(
        "preserved_unreviewed"
    ) == 6


def test_2014_15_normalizer_rebuilds_eighteen_selected_headlines_from_bronze(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/03/039706f735a3652aa911e4fa7eaf776a6d534271d96e478aad0ce45789351dfb"
    )
    if not source.is_file():
        pytest.skip("captured 2014/15 Treasury source is unavailable")
    output = tmp_path / "silver"
    result = overview.normalize_vote_health_estimates_overview_2014_15(
        source,
        output,
        expected_sha256=overview.SOURCE_SHA256_2014_15,
        source_vintage=overview.VINTAGE_2014_15,
        source_locator="https://www.treasury.govt.nz/publications/estimates/vote-health-health-sector-estimates-appropriations-2014-15",
        observed_at="2026-08-29T09:00:17Z",
        dry_run=False,
    )
    facts = pq.read_table(output / "vote_health_overview_facts.parquet").to_pylist()
    assert result["status"] == "passed"
    assert result["counts"] == {"pages": 2, "facts": 18}
    assert [fact["value"] for fact in facts] == [
        *map(
            Decimal,
            (
                15557,
                193,
                14249,
                14221,
                11405,
                1118,
                820,
                430,
                170,
                147,
                75,
                57,
                28,
                1114,
                645,
                440,
                15,
                15,
            ),
        )
    ]
    risk_quality_flags = facts[10]["quality_flags"]
    assert risk_quality_flags
    assert "source_qualifier_preserved_in_raw_phrase" not in risk_quality_flags
    for index in (1, 15):
        assert (
            "source_qualifier_preserved_in_raw_phrase" in facts[index]["quality_flags"]
        )
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert [row["disposition"] for row in dispositions].count(
        "preserved_unreviewed"
    ) == 107


def test_2011_12_normalizer_rebuilds_selected_headlines_from_pinned_bronze_source(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/5b/5b56c8a0641a870d82558f2c61fc87df90bcabf318541af4c3d86ba8ce3063af"
    )
    if not source.is_file():
        pytest.skip("captured 2011/12 Treasury source is unavailable")
    output = tmp_path / "out"
    result = overview.normalize_vote_health_estimates_overview_2011_12(
        source,
        output,
        expected_sha256=overview.SOURCE_SHA256_2011_12,
        source_vintage=overview.VINTAGE_2011_12,
        source_locator=(
            "https://www.treasury.govt.nz/publications/estimates/"
            "vote-health-estimates-appropriations-2011-12"
        ),
        observed_at="2026-10-03T20:06:22Z",
        dry_run=False,
    )
    facts = pq.read_table(output / "vote_health_overview_facts.parquet").to_pylist()
    assert result["status"] == "passed"
    assert result["counts"] == {"pages": 2, "facts": 17}
    assert [fact["value"] for fact in facts] == [
        Decimal(13953),
        Decimal(205),
        Decimal(13295),
        Decimal(13267),
        Decimal(10498),
        Decimal(1028),
        Decimal(443),
        Decimal(807),
        Decimal(156),
        Decimal(80),
        Decimal(179),
        Decimal(76),
        Decimal(28),
        Decimal(454),
        Decimal(419),
        Decimal(15),
        Decimal(20),
    ]
    assert [fact["source_page"] for fact in facts] == [*([2] * 13), *([3] * 4)]
    assert [
        "source_qualifier_preserved_in_raw_phrase" in fact["quality_flags"]
        for fact in facts
    ] == [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
    ]
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert len(dispositions) == overview.PAGE_COUNT_2011_12
    assert {
        row["source_page"]
        for row in dispositions
        if row["disposition"] == "partially_normalized"
    } == {2, 3}
    assert (
        sum(row["disposition"] == "preserved_unreviewed" for row in dispositions) == 7
    )


def test_2009_10_overview_extracts_all_seventeen_pinned_money_statements() -> None:
    pages = [
        (
            "The Minister of Health is responsible for appropriations in the Vote "
            "for the 2009/10 financial year totalling just under $12,978 million, "
            "an increase of $899 million or 7.4% from 2008/09 (Supplementary "
            "Estimates) and covering the following: Departmental Operating "
            "Appropriations A total of just over $217 million (1.7% of the Vote) "
            "relates to the functions of the Ministry of Health. Non-Departmental "
            "Operating Appropriations A total of nearly $12,406 million (95.6% of "
            "the Vote) is for operating expenses to be incurred on behalf of the "
            "Crown. Output Expenses These total just over $12,382 million (95.5% "
            "of the Vote) and are to fund the purchases of health services as "
            "follows: Nearly $9,700 million (74.8% of the Vote) to fund health "
            "services from DHBs through the DHB appropriations. Just over $895 "
            "million (6.9% of the Vote) to purchase national disability support "
            "services. Nearly $515 million (4.0% of the Vote) to purchase public "
            "health services. Almost $841 million (6.5% of the Vote) to purchase "
            "national health services and provide clinical training for health "
            "professionals. Nearly $242 million (1.9% of the Vote) to manage health "
            "sector risks. Just over $154 million (1.2% of the Vote) to purchase "
            "primary health care services. Nearly $36 million (0.3% of the Vote) "
            "to fund other health and disability services. Other Expenses Incurred "
            "by the Crown A total of nearly $24 million (0.2% of the Vote) is for "
            "other expenses. Capital Expenditure A total of nearly $355 million "
            "(2.7% of the Vote) is to provide capital funding. Just over $304 "
            "million (2.3 % of the Vote) is to provide debt or equity for District "
            "Health Boards or the New Zealand Blood Service. $15 million (0.1% of "
            "the Vote) is to provide interest-free loans. Just over $35 million "
            "(0.3% of the Vote) is to purchase or develop assets for use by the "
            "Ministry of Health."
        ),
        "Details of Appropriations",
    ]

    rows = overview.parse_overview_2009_10_pages(pages)
    assert [row["value"] for row in rows] == [
        Decimal(12978),
        Decimal(899),
        Decimal(217),
        Decimal(12406),
        Decimal(12382),
        Decimal(9700),
        Decimal(895),
        Decimal(515),
        Decimal(841),
        Decimal(242),
        Decimal(154),
        Decimal(36),
        Decimal(24),
        Decimal(355),
        Decimal(304),
        Decimal(15),
        Decimal(35),
    ]


def test_2010_11_overview_extracts_eighteen_source_anchored_statements() -> None:
    pages = [
        (
            "The Minister of Health is responsible for appropriations in the Vote "
            "for the 2010/11 financial year totalling just under $13,574 million, "
            "an increase of $858 million or 6.7% from 2009/10 (Supplementary "
            "Estimates) and covering the following. Departmental Operating "
            "Appropriations A total of just over $216 million (1.6% of the Vote) "
            "relates to the functions of the Ministry of Health. Non-Departmental "
            "Operating Appropriations A total of nearly $12,847 million (94.6% "
            "of the Vote) is for operating expenses to be incurred on behalf of "
            "the Crown. Output Expenses These total nearly $12,815 million "
            "(94.4% of the Vote) and are to fund the purchases of health services "
            "as follows: Just over $10,044 million (74.0% of the Vote) to fund "
            "health services from DHBs through the DHB appropriations. Just over "
            "$970 million (7.1% of the Vote) to purchase national disability "
            "support services. Just over $517 million (3.8% of the Vote) to "
            "purchase public health services. Just over $905 million (6.7% of "
            "the Vote) to purchase national health services and provide clinical "
            "training for health professionals. Nearly $20 million (0.1% of the "
            "Vote) to manage health sector risks. $95 million (0.7% of the Vote) "
            "for a provision for DHB deficit support. Just over $182 million "
            "(1.4% of the Vote) to purchase primary health care services. Just "
            "over $83 million (0.6% of the Vote) to fund other health and "
            "disability services. Other Expenses Incurred by the Crown A total "
            "of nearly $32 million (0.2% of the Vote) is for other expenses."
        ),
        (
            "Capital Expenditure A total of nearly $511 million (3.8% of the "
            "Vote) is to provide capital funding. Nearly $478 million (3.5 % "
            "of the Vote) is to provide debt or equity for District Health Boards "
            "or Health Sector Crown Agencies. $15 million (0.1% of the Vote) is "
            "to provide interest-free loans. Just over $18 million (0.1% of the "
            "Vote) is to purchase or develop assets for use by the Ministry of "
            "Health. Details of these appropriations are set out in Parts 2-6."
        ),
    ]
    rows = overview.parse_overview_2010_11_pages(pages)
    assert [row["value"] for row in rows] == [
        Decimal(13574),
        Decimal(858),
        Decimal(216),
        Decimal(12847),
        Decimal(12815),
        Decimal(10044),
        Decimal(970),
        Decimal(517),
        Decimal(905),
        Decimal(20),
        Decimal(95),
        Decimal(182),
        Decimal(83),
        Decimal(32),
        Decimal(511),
        Decimal(478),
        Decimal(15),
        Decimal(18),
    ]
    assert [row["source_page"] for row in rows] == [*([2] * 14), *([3] * 4)]
    assert "just under $13,574 million" in rows[0]["source_phrase"]
    assert "$95 million" in rows[10]["source_phrase"]
    assert rows[2]["source_qualifier_preserved"] is True
    assert rows[9]["source_qualifier_preserved"] is True
    assert rows[10]["source_qualifier_preserved"] is False
    assert rows[16]["source_qualifier_preserved"] is False


def test_2009_10_normalizer_rebuilds_all_headlines_from_pinned_bronze_source(
    tmp_path: Path,
) -> None:
    source = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/"
        "sha256/ac/acd253a1d68738a06e5310c002f8051698146fe018d3d6c10fc6b5e0f6d7ac1f"
    )
    if not source.is_file():
        pytest.skip("captured 2009/10 Treasury source is unavailable")
    output = tmp_path / "out"
    result = overview.normalize_vote_health_estimates_overview_2009_10(
        source,
        output,
        expected_sha256=overview.SOURCE_SHA256_2009_10,
        source_vintage=overview.VINTAGE_2009_10,
        source_locator=(
            "https://www.treasury.govt.nz/publications/estimates/"
            "vote-health-estimates-appropriations-2009-10"
        ),
        observed_at="2026-10-03T16:31:35.751358Z",
        dry_run=False,
    )
    facts = pq.read_table(output / "vote_health_overview_facts.parquet").to_pylist()
    assert result["status"] == "passed"
    assert result["counts"] == {"pages": 1, "facts": 17}
    assert [fact["value"] for fact in facts] == [
        Decimal(12978),
        Decimal(899),
        Decimal(217),
        Decimal(12406),
        Decimal(12382),
        Decimal(9700),
        Decimal(895),
        Decimal(515),
        Decimal(841),
        Decimal(242),
        Decimal(154),
        Decimal(36),
        Decimal(24),
        Decimal(355),
        Decimal(304),
        Decimal(15),
        Decimal(35),
    ]
    assert all("source_amount_is_not_exact" in fact["quality_flags"] for fact in facts)
    dispositions = pq.read_table(output / "page_dispositions.parquet").to_pylist()
    assert len(dispositions) == overview.PAGE_COUNT_2009_10
    assert {row["source_page"] for row in dispositions} == set(
        range(1, overview.PAGE_COUNT_2009_10 + 1)
    )
    assert {
        row["source_page"]
        for row in dispositions
        if row["disposition"] == "partially_normalized"
    } == {2}
    assert (
        sum(row["disposition"] == "preserved_unreviewed" for row in dispositions) == 7
    )
