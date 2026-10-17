"""Recovered stage mappings retain source identity and partial worksheet scope."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from tests.domains.health_appropriations.test_area_accounting import inputs, pinned

from archive_govt_nz.domains.health_appropriations import (
    stage_area_bindings as bindings,
)
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


def test_crown_format_property_is_retained_as_context_not_an_amount() -> None:
    receipt, coverage, links, units = fixture()
    links[-1]["field"] = "source_context"
    links[-1]["source_coordinate"] = "Raw Data!B2@number_format"
    result = project_stage_bindings("crown", receipt, coverage, links, units)
    assert result[0]["field_coordinates"]["source_context"] == ["B2@number_format"]
    assert result[0]["amount_coordinates"] == ["A2"]


@pytest.mark.parametrize(
    ("stage", "kind", "coordinate"),
    [
        ("budget", "source_context", "Raw Data!B2@number_format"),
        ("crown", "amount", "Raw Data!B2@number_format"),
        ("crown", "source_context", "Raw Data!B2@unknown_property"),
        ("crown", "source_context", "Raw Data!Q5@number_format"),
    ],
)
def test_unknown_or_misapplied_properties_fail_closed(
    stage: str, kind: str, coordinate: str
) -> None:
    receipt, coverage, links, units = fixture()
    links[-1]["field"] = kind
    links[-1]["source_coordinate"] = coordinate
    with pytest.raises(ValueError, match="stage_area_binding_contract"):
        project_stage_bindings(stage, receipt, coverage, links, units)


@pytest.mark.parametrize("mismatch", ["plan", "donor"])
def test_public_reader_binds_the_verified_plan_to_the_donor_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mismatch: str
) -> None:
    donor, census, _ = inputs()
    inventory = pinned(donor)
    plan = {
        "legacy_plan": {
            "donor_manifest_sha256": inventory.sha256
            if mismatch == "plan"
            else "f" * 64
        }
    }
    payload = json.dumps(plan, sort_keys=True, ensure_ascii=False, default=str)
    (tmp_path / "PLAN.json").write_text(payload + "\n")
    verification = {
        "plan_sha256": "0" * 64
        if mismatch == "plan"
        else hashlib.sha256(payload.encode()).hexdigest(),
        "coverage": [],
    }
    monkeypatch.setattr(bindings, "verify_eight", lambda *_args: verification)
    with pytest.raises(ValueError, match="stage_area_binding_contract"):
        bindings.build_stage_area_bindings(
            tmp_path,
            tmp_path / "store",
            manifest_sha256="e" * 64,
            donor=inventory,
            census=pinned(census),
        )
