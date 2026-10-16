"""Validate the analytical-context register's evidence boundaries."""

from __future__ import annotations

import json
from pathlib import Path


def test_context_register_distinguishes_leads_from_pinned_analytical_policies() -> None:
    """Keep discovery leads distinct from captured inputs and bounded policies."""
    root = Path(__file__).parents[2]
    track = (
        root / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
    )
    text = (track / "analytical-context-register.md").read_text(encoding="utf-8")
    for source_id in (
        "stats_nz_cpi-053a0705526fac8d",
        "stats_nz_qes-faab0efe46470af8",
        "stats_nz_gdp-9fc80ed4b7f234b2",
        "stats_nz_population-806dead2a5b8ab69",
    ):
        assert text.count(source_id) == 1
    rows = {
        line.split("|")[1].strip(): line
        for line in text.splitlines()
        if line.startswith("| ")
    }
    quarterly = rows["Quarterly resident-population lead"]
    assert all(
        value in quarterly for value in ("DPE054AA", "DPE054FF", "Mean year ended")
    )
    assert "Retained discovery lead" in quarterly
    assert "Do not substitute quarterly stocks" in quarterly
    annual = rows["Annual resident population"]
    assert "DPE056AA" in annual
    assert "Numeric export captured, normalized and projected" in annual
    assert "March fiscal periods are unsupported" in annual
    assert "Not an all-age resident denominator" in rows["Working-age population"]
    assert "No unified join" in rows["Forecast Crown expense sources"]
    assert "no health-input-cost deflator" in rows["CPI"]
    for name in ("shares", "per-capita", "cpi-benchmark"):
        receipt = json.loads(
            (track / f"fiscal-health-{name}-20261004.json").read_text()
        )
        assert receipt["query_receipt"]["formula_policy"] in text
        assert receipt["bronze_sha256"] in text
    assert "grants no new derivative redistribution rights" in text
    assert "*** Update File:" not in text
