"""Historical discovery evidence must retain the full scope and unknown fixity."""

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit


def test_historical_source_register_retains_scope_and_discovery_boundary() -> None:
    """No unvisited edition disappears and no observed link earns byte credit."""
    path = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
        / "historical-source-register.json"
    )
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "archive-govt-nz.health-historical-sources/v1"
    assert datetime.fromisoformat(report["observed_at"]).utcoffset() is not None
    assert report["edition_years"] == list(range(1997, 2027))
    assert report["edition_count"] == len(report["edition_years"])
    assert report["fully_enumerated_editions"] == []
    assert report["pending_editions"] == report["edition_years"]
    assert report["payload_capture_performed"] is False
    assert report["publication_authorized"] is False
    assert report["whole_history_complete"] is False
    records = report["resource_observations"]
    assert len(records) == 15
    assert len({row["url"] for row in records}) == len(records)
    assert len({(r["edition_year"], r["family"], r["kind"]) for r in records}) == 15
    assert {(r["family"], r["kind"]) for r in records} == {
        ("budget", "expenditure"),
        ("budget", "revenue"),
        ("befu", "charts"),
        ("befu", "expense_tables"),
        ("hyefu", "charts"),
        ("hyefu", "expense_tables"),
        ("befu", "sna_series_tables"),
        ("befu", "gaap_series_tables"),
        ("befu", "expenses"),
    }
    for row in records:
        assert row["edition_year"] in report["edition_years"]
        assert row["disposition"] == "discovered"
        assert row["sha256"] is None
        assert row["byte_count"] is None
        assert row["rights_state"] == "not_evaluated"
        assert row["landing_url"] in report["observed_pages"]
        parsed = urlsplit(row["url"])
        assert parsed.scheme == "https"
        assert parsed.netloc == "www.treasury.govt.nz"
        assert parsed.path.endswith((".xlsx", ".pdf"))
        assert not parsed.query
        assert not parsed.fragment
    for gap in report["edition_dispositions"]:
        assert gap["edition_year"] in report["edition_years"]
        assert gap["evidence_url"] in report["observed_pages"]
        assert gap["other_custodian_availability"] == "not_investigated"
