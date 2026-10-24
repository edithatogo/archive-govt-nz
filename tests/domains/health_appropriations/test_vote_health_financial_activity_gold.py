# SPDX-License-Identifier: Apache-2.0
"""Contracts for the pinned 2014/15 Vote Health activity Gold projection."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations import (
    vote_health_financial_activity_gold as gold,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2014_15_financial_activity as silver,
)


def _page() -> str:
    return """VOTE HEALTH
Supporting Information
Part 1 - Vote as a Whole
1.2 - Trends in the Vote
Summary of Financial Activity
2014/15 Supplementary Estimates
Estimates $000
Departmental Transactions $000
Non-Departmental Transactions $000
Total Transactions $000
Total $000
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


def _silver_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, str]:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"fixture source bytes")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(silver, "SOURCE_SHA256", digest)

    class Page:
        def extract_text(self) -> str:
            return _page()

    class Reader:
        is_encrypted = False

        def __init__(self, *_: object, **__: object) -> None:
            self.pages = [Page() for _ in range(silver.PAGE_COUNT)]

    monkeypatch.setattr(silver, "PdfReader", Reader)
    package = tmp_path / "silver"
    receipt = silver.normalize(
        source,
        package,
        expected_sha256=digest,
        source_vintage=silver.VINTAGE,
        source_locator=silver.SOURCE_LOCATOR,
        observed_at="2026-10-25T00:00:00Z",
        dry_run=False,
    )
    manifest_pin = hashlib.sha256((package / "MANIFEST.json").read_bytes()).hexdigest()
    assert receipt["status"] == "passed"
    return package, manifest_pin


def test_projection_is_pinned_source_separated_and_repeatable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    silver_dir, silver_pin = _silver_package(tmp_path, monkeypatch)
    first = tmp_path / "gold-first"
    second = tmp_path / "gold-second"

    planned = gold.export_vote_health_financial_activity(silver_dir, silver_pin, first)
    assert planned == {
        "schema_version": gold.VERSION,
        "status": "dry_run",
        "row_count": 14,
        "lineage_row_count": 70,
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
    assert not first.exists()

    receipt = gold.export_vote_health_financial_activity(
        silver_dir, silver_pin, first, write=True
    )
    replay = gold.export_vote_health_financial_activity(
        silver_dir, silver_pin, second, write=True
    )
    assert receipt["manifest_sha256"] == replay["manifest_sha256"]
    for name in first.iterdir():
        assert (second / name.name).read_bytes() == name.read_bytes()

    facts, lineage, summary = gold.read_vote_health_financial_activity(
        first, receipt["manifest_sha256"]
    )
    assert facts.num_rows == 14
    assert lineage.num_rows == 70
    first_row = facts.to_pylist()[0]
    assert first_row["source_row_ordinal"] == 1
    assert first_row["source_silver_manifest_sha256"] == silver_pin
    assert first_row["estimates"] == 100_000
    assert first_row["non_departmental_transactions"] == -500
    assert summary["calculations"] == "none"
    assert summary["semantic_comparability"] == "not_established"
    assert summary["sections"] == {
        "appropriations": 10,
        "crown_revenue_and_capital_receipts": 4,
    }

    query = gold.query_vote_health_financial_activity(
        first,
        receipt["manifest_sha256"],
        section="crown_revenue_and_capital_receipts",
    )
    assert query["status"] == "verified"
    assert query["row_count"] == 4
    assert query["rows"][0]["source_row_ordinal"] == 11
    assert query["rows"][0]["departmental_transactions"] is None
    assert query["rows"][0]["source_silver_manifest_sha256"] == silver_pin
    assert query["rights"] == "not_evaluated"
    assert query["publication"] == "not_performed"


def test_projection_fails_closed_on_silver_or_gold_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    silver_dir, silver_pin = _silver_package(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        gold.export_vote_health_financial_activity(
            silver_dir, "0" * 64, tmp_path / "bad"
        )
    facts_path = silver_dir / "vote_health_financial_activity_facts.parquet"
    silver_facts = facts_path.read_bytes()
    facts_path.write_bytes(silver_facts + b"drift")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        gold.export_vote_health_financial_activity(
            silver_dir, silver_pin, tmp_path / "silver-drift"
        )
    facts_path.write_bytes(silver_facts)

    output = tmp_path / "gold"
    receipt = gold.export_vote_health_financial_activity(
        silver_dir, silver_pin, output, write=True
    )
    with (output / "summary.json").open("ab") as stream:
        stream.write(b" ")
    assert (
        gold.query_vote_health_financial_activity(output, receipt["manifest_sha256"])[
            "status"
        ]
        == "failed"
    )
    (output / "summary.json").write_bytes(b"corrupt")
    assert (
        gold.query_vote_health_financial_activity(output, receipt["manifest_sha256"])[
            "status"
        ]
        == "failed"
    )


def test_query_bounds_and_silver_output_path_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    silver_dir, silver_pin = _silver_package(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="vote_health_financial_activity_gold_invalid"):
        gold.export_vote_health_financial_activity(
            silver_dir, silver_pin, silver_dir / "nested", write=True
        )
    assert (
        gold.query_vote_health_financial_activity(
            tmp_path / "missing", silver_pin, limit=True
        )["status"]
        == "failed"
    )
    assert (
        gold.query_vote_health_financial_activity(
            tmp_path / "missing", silver_pin, section="unapproved", limit=1
        )["status"]
        == "failed"
    )
