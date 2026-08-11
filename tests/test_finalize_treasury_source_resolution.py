"""Contracts for deterministic, fail-closed Treasury source resolution."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType


ROOT = Path(__file__).parents[1]


def _load_tool() -> ModuleType:
    path = ROOT / "tools" / "finalize_treasury_source_resolution.py"
    spec = importlib.util.spec_from_file_location("finalize_resolution", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolution_covers_every_unresolved_resource_deterministically() -> None:
    """Every unresolved ID has one stable, independently classed outcome."""
    module = _load_tool()
    plan = json.loads(
        (ROOT / "evidence" / "phase-6-treasury-capture-plan.json").read_text(
            encoding="utf-8"
        )
    )
    recovery = json.loads(
        (ROOT / "evidence" / "ckan-datastore-recovery.json").read_text(encoding="utf-8")
    )
    config = json.loads(
        (ROOT / "config" / "treasury-source-resolution.json").read_text(
            encoding="utf-8"
        )
    )

    first = module.resolve(plan, recovery, config, observed_at="2026-08-11T00:00:00Z")
    second = module.resolve(plan, recovery, config, observed_at="2026-08-11T00:00:00Z")

    assert first == second
    assert first["counts"] == {
        "resources": 47,
        "authoritative_replacement": 31,
        "rights_evidenced": 13,
        "tombstone": 3,
    }
    assert len({row["resource_id"] for row in first["resources"]}) == 47


def test_resolution_keeps_nzdmo_without_rights_evidence_as_tombstones() -> None:
    """NZDMO resources remain tombstones when authority cannot be evidenced."""
    module = _load_tool()
    plan = json.loads(
        (ROOT / "evidence" / "phase-6-treasury-capture-plan.json").read_text(
            encoding="utf-8"
        )
    )
    recovery = json.loads(
        (ROOT / "evidence" / "ckan-datastore-recovery.json").read_text(encoding="utf-8")
    )
    config = json.loads(
        (ROOT / "config" / "treasury-source-resolution.json").read_text(
            encoding="utf-8"
        )
    )
    receipt = module.resolve(plan, recovery, config, observed_at="2026-08-11T00:00:00Z")

    tombstones = [row for row in receipt["resources"] if row["state"] == "tombstone"]
    assert len(tombstones) == 3
    assert all(row["source_host"] == "www.nzdmo.govt.nz" for row in tombstones)
    assert {row["reason"] for row in tombstones} == {
        "no_verified_secure_replacement",
        "rights_evidence_unavailable",
    }


def test_resolution_rejects_non_authoritative_replacement_host() -> None:
    """A third-party URL cannot be promoted as an authoritative replacement."""
    module = _load_tool()
    plan = {
        "outcomes": [
            {
                "dataset_id": "d",
                "resource_id": "r",
                "source_url": "http://www.treasury.govt.nz/old",
                "decision": {"reason": "unsafe_scheme", "sanitized_filename": "x"},
            }
        ]
    }
    config = {
        "schema_version": "treasury-source-resolution-config/v1",
        "official_replacements": {
            "http://www.treasury.govt.nz/old": "https://example.com/not-authoritative"
        },
        "rights_evidence": {},
    }

    with pytest.raises(ValueError, match="authoritative host"):
        module.resolve(plan, {"resources": []}, config, observed_at="x")
