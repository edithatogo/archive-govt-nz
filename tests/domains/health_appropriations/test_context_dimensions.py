"""Contracts for literal-only source context dimension mappings."""

from __future__ import annotations

import pytest

from archive_govt_nz.domains.health_appropriations.adapter_protocol import FieldLineage
from archive_govt_nz.domains.health_appropriations.context_dimensions import (
    context_source_dimensions,
)


def test_context_dimensions_are_literal_unresolved_and_stably_linked() -> None:
    rows = (
        {
            "record_id": "r2",
            "source_vintage": "2026-Q2",
            "series_reference": "CPIQ.SE9A",
            "period_token": "2026.06",
            "unit": "Index",
            "index_base": None,
        },
        {
            "record_id": "r1",
            "source_vintage": "2026-Q2",
            "series_reference": "CPIQ.SE9A",
            "period_token": "2026.03",
            "unit": "Index",
            "index_base": None,
        },
    )
    lineage = tuple(
        FieldLineage(
            row["record_id"],
            field,
            f"csv:{row['record_id']}:{field}",
            value,
            value,
            "retain",
        )
        for row in rows
        for field, value in (
            ("series_reference", row["series_reference"]),
            ("period_token", row["period_token"]),
            ("unit", row["unit"]),
        )
    )
    first = context_source_dimensions(rows, lineage, family="cpi")
    second = context_source_dimensions(
        tuple(reversed(rows)), tuple(reversed(lineage)), family="cpi"
    )
    assert first == second
    mappings, links = first
    assert mappings
    assert all(
        row.target is None and row.method is None and not row.evidence
        for row in mappings
    )
    assert {item.raw_value for item in links} >= {"CPIQ.SE9A", "2026.06", "Index"}
    assert all(item.source_coordinate.startswith("csv:") for item in links)


def test_context_dimensions_reject_unknown_family() -> None:
    with pytest.raises(ValueError, match="unknown_context_dimension_family"):
        context_source_dimensions((), (), family="unknown")
