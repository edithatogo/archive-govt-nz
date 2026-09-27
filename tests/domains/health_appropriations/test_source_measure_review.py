"""The source/measure review remains precise about coverage and evidence gaps."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations.source_measure_review import (
    validate_review,
)

ROOT = Path(__file__).resolve().parents[3]
TRACK = ROOT / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
REPORT = TRACK / "source-measure-review-20260927.json"


def test_review_reports_exact_series_and_preserves_blockers() -> None:
    report = validate_review(REPORT, ROOT)
    assert report["series_count"] == 8
    assert report["source_families"]["vote_health"]["captured_documents"] == 58
    assert report["source_families"]["vote_health"]["estimates_years"] == [
        1998,
        1999,
        2000,
        2001,
        2002,
        2003,
        2004,
        2005,
        2006,
        2007,
        2014,
        2015,
        2016,
        2017,
        2022,
        2023,
        2024,
        2025,
        2026,
    ]
    assert report["source_families"]["vote_health"]["supplementary_years"] == [
        1998,
        1999,
        2000,
        2001,
        2002,
        2003,
        2004,
        2005,
        2006,
        2007,
        2008,
        2009,
        2010,
        2011,
        2013,
        2014,
        2015,
        2016,
        2017,
        2018,
        2019,
        2020,
        2021,
        2022,
        2023,
        2024,
        2025,
    ]
    assert report["series"]["population"]["series_id"].startswith("DPE056AA")
    assert report["series"]["population"]["rights"] == "infoshare_export_not_evaluated"
    assert "2011Q2" in report["series"]["gdp"]["vintage_or_range"]
    assert "2026Q1" in report["series"]["gdp"]["vintage_or_range"]
    assert (
        "Official GDP release for June 2026 exists"
        in report["series"]["gdp"]["vintage_or_range"]
    )
    assert report["source_families"]["historical_editions"]["complete"] is False
    assert (
        len(report["source_families"]["vote_health"]["discovered_estimates_urls"]) == 10
    )
    assert (
        len(report["source_families"]["vote_health"]["discovered_supplementary_urls"])
        == 2
    )


def test_review_rejects_unsubstantiated_admission(tmp_path: Path) -> None:
    report = json.loads(REPORT.read_text())
    report["series"]["population"]["rights"] = "approved"
    path = tmp_path / "review.json"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match=r"invalid source-measure review"):
        validate_review(path, ROOT)
