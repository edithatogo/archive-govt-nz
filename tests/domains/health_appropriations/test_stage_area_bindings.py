"""Recovered stage mappings retain source identity and partial worksheet scope."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from tests.domains.health_appropriations.test_area_accounting import inputs, pinned

from archive_govt_nz.domains.health_appropriations.area_accounting import (
    reconcile_areas,
)
from archive_govt_nz.domains.health_appropriations.stage_area_bindings import (
    project_stage_bindings,
)


def fixture() -> tuple[
    dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]
]:
    donor, census, receipt = inputs()
    receipt["output_sha256"] = {"field_lineage.parquet": "f" * 64}
    coverage = {
        "source_locator": receipt["source_locator"],
        "source_object_sha256": "a" * 64,
        "manifest_sha256": "e" * 64,
        "facts": 1,
        "record_ids": ["record-1"],
        "lineage": 2,
    }
    links = [
        {
            "record_id": "record-1",
            "source_object_sha256": "a" * 64,
            "field": "amount",
            "source_coordinate": "'Raw Data'!A2",
        },
        {
            "record_id": "record-1",
            "source_object_sha256": "a" * 64,
            "field": "unit",
            "source_coordinate": "Raw Data!Q4",
        },
    ]
    units = reconcile_areas(pinned(donor), pinned(census))["units"]
    return receipt, coverage, links, units


def test_verified_selection_binds_exact_unit_without_resolving_remainder() -> None:
    receipt, coverage, links, units = fixture()
    before = deepcopy((receipt, coverage, links, units))
    result = project_stage_bindings("budget", receipt, coverage, links, units)
    sheet = next(r for r in units if r["kind"] == "workbook_sheet")
    assert result[0]["unit_id"] == sheet["unit_id"]
    assert result[0]["amount_coordinates"] == ["A2"]
    assert result[0]["field_coordinates"] == {"amount": ["A2"], "unit": ["Q4"]}
    assert result[0]["coverage"] == "partial"
    assert result[0]["record_ids"] == ["record-1"]
    assert result == project_stage_bindings(
        "budget", receipt, coverage, list(reversed(links)), units
    )
    assert (receipt, coverage, links, units) == before
    assert {r["state"] for r in units} == {"unresolved"}


def test_crown_outside_donor_inventory_stays_source_separated() -> None:
    receipt, coverage, links, units = fixture()
    receipt["source_object_sha256"] = coverage["source_object_sha256"] = "d" * 64
    receipt["source_locator"] = coverage["source_locator"] = (
        "https://publisher.example/crown.xlsx"
    )
    for link in links:
        link["source_object_sha256"] = "d" * 64
    result = project_stage_bindings("crown", receipt, coverage, links, units)
    assert result[0]["unit_id"] is None
    assert result[0]["inventory_state"] == "source_separated"
    assert result[0]["reason"] == "source_not_in_donor_inventory"
    with pytest.raises(ValueError, match="stage_area_binding_contract"):
        project_stage_bindings("budget", receipt, coverage, links, units)


@pytest.mark.parametrize("coordinate", ["'Raw Data'!A0", "'Raw Data'!Q5", "Unknown!A1"])
def test_unproven_coordinates_fail_closed(coordinate: str) -> None:
    receipt, coverage, links, units = fixture()
    links[0]["source_coordinate"] = coordinate
    with pytest.raises(ValueError, match="stage_area_binding_contract"):
        project_stage_bindings("budget", receipt, coverage, links, units)


def test_foreign_lineage_cannot_bind_a_valid_stage() -> None:
    receipt, coverage, links, units = fixture()
    links[0]["source_object_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="stage_area_binding_contract"):
        project_stage_bindings("budget", receipt, coverage, links, units)
