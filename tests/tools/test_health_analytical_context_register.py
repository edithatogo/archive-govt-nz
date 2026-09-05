"""Validate the analytical-context register's evidence boundaries."""

from __future__ import annotations

import re
from pathlib import Path


def test_context_register_preserves_exact_ids_and_unresolved_joins() -> None:
    """The register must not turn metadata leads into promoted denominators."""
    root = Path(__file__).parents[2]
    path = (
        root
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
        / "analytical-context-register.md"
    )
    text = path.read_text(encoding="utf-8")
    for source_id in (
        "stats_nz_cpi-053a0705526fac8d",
        "stats_nz_qes-faab0efe46470af8",
        "stats_nz_gdp-9fc80ed4b7f234b2",
        "stats_nz_population-806dead2a5b8ab69",
    ):
        assert text.count(source_id) == 1
    assert "DPEQ.SG1CTOT" in text
    assert "Metadata lead only" in text
    assert "no unified join" in text
    assert "cannot support per-capita spending" in text
    assert "No row establishes rights" in text
    assert not re.search(r"\| Resident population \|.*\| Captured \|", text)
