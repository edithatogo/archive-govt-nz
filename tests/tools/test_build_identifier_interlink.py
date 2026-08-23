"""Tests for the cross-domain identifier interlink builder."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = Path(__file__).parents[2] / "tools" / "build_identifier_interlink.py"
_SPEC = importlib.util.spec_from_file_location("build_identifier_interlink", _TOOL_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

load_legislation_ids = _MODULE.load_legislation_ids
load_health_pairs = _MODULE.load_health_pairs
load_publication_identities = _MODULE.load_publication_identities
validate_domain_ids = _MODULE.validate_domain_ids
find_collisions = _MODULE.find_collisions
build_interlink = _MODULE.build_interlink

_UUID = "118d7365-8678-4fc2-b036-dcf6b16ca4b3"
_UUID2 = "1e3838ae-bf34-404c-961b-f35aa55e56fa"


class TestLoaders:
    """Identifier source loader coverage."""

    def test_load_legislation_ids(self, tmp_path: Path) -> None:
        """Checkpoint work IDs load as strings."""
        p = tmp_path / "chk.json"
        p.write_text(
            json.dumps({"processed_work_ids": ["w-1", "w-2"]}), encoding="utf-8"
        )
        assert load_legislation_ids(p) == ["w-1", "w-2"]

    def test_load_legislation_rejects_non_array(self, tmp_path: Path) -> None:
        """Non-array processed IDs fail closed."""
        p = tmp_path / "chk.json"
        p.write_text(json.dumps({"processed_work_ids": "x"}), encoding="utf-8")
        with pytest.raises(TypeError, match="array"):
            load_legislation_ids(p)

    def test_load_health_pairs(self, tmp_path: Path) -> None:
        """Health pairs load only complete dataset/resource entries."""
        p = tmp_path / "snap.json"
        snap = {
            "resources": [
                {"dataset_id": _UUID, "resource_id": _UUID2},
                {"dataset_id": "", "resource_id": "x"},
            ]
        }
        p.write_text(json.dumps(snap), encoding="utf-8")
        pairs = load_health_pairs(p)
        assert len(pairs) == 1
        assert pairs[0]["dataset_id"] == _UUID

    def test_load_publication_identities(self, tmp_path: Path) -> None:
        """HF slugs and Zenodo DOI load from a readback receipt."""
        p = tmp_path / "rb.json"
        rb = {
            "huggingface": {"a/slug": {}, "b/slug2": {}},
            "zenodo": {"doi": "10.5281/zenodo.123"},
        }
        p.write_text(json.dumps(rb), encoding="utf-8")
        pubs = load_publication_identities(p)
        assert pubs["hf_slugs"] == ["a/slug", "b/slug2"]
        assert pubs["zenodo_dois"] == ["10.5281/zenodo.123"]


class TestValidation:
    """Per-domain identifier shape validation coverage."""

    def test_valid_uuid_passes(self) -> None:
        """Well-formed UUIDs produce no findings."""
        assert validate_domain_ids("health-resource", [_UUID]) == []

    def test_malformed_uuid_flagged(self) -> None:
        """Malformed health UUIDs are flagged."""
        findings = validate_domain_ids("health-resource", ["not-a-uuid"])
        assert any("malformed UUID" in f for f in findings)

    def test_empty_identifier_flagged(self) -> None:
        """Empty identifiers are flagged in any domain."""
        findings = validate_domain_ids("legislation", [" "])
        assert any("empty identifier" in f for f in findings)

    def test_hf_slug_shape(self) -> None:
        """HF slug validation accepts org/name and rejects bare names."""
        assert validate_domain_ids("publication-hf", ["a/b.c"]) == []
        findings = validate_domain_ids("publication-hf", ["noslash"])
        assert any("malformed slug" in f for f in findings)

    def test_zenodo_doi_shape(self) -> None:
        """Zenodo DOI validation accepts the canonical pattern only."""
        assert validate_domain_ids("publication-zenodo", ["10.5281/zenodo.123"]) == []
        findings = validate_domain_ids("publication-zenodo", ["10.1/xyz"])
        assert any("malformed DOI" in f for f in findings)

    def test_legislation_ids_unrestricted_shape(self) -> None:
        """Non-empty legislation work IDs pass shape validation."""
        assert validate_domain_ids("legislation", ["act-2026-0001"]) == []


class TestCollisions:
    """Cross-domain collision detection coverage."""

    def test_collision_detected(self) -> None:
        """Identical raw IDs across domains are reported."""
        collisions = find_collisions({"a": ["x"], "b": ["x"]})
        assert len(collisions) == 1
        assert "cross-domain collision" in collisions[0]

    def test_no_collision_within_domain(self) -> None:
        """Duplicate IDs within one domain are not cross-domain collisions."""
        assert find_collisions({"a": ["x", "x"]}) == []


class TestBuildInterlink:
    """Receipt assembly coverage."""

    def test_receipt_schema_and_counts(self) -> None:
        """Receipt carries schema, counts, relationships, and status."""
        receipt = build_interlink(
            ["w-1"],
            [{"dataset_id": _UUID, "resource_id": _UUID2}],
            {"hf_slugs": ["o/ds"], "zenodo_dois": ["10.5281/zenodo.9"]},
        )
        assert receipt["schema_version"] == "archive-govt-nz.identifier-interlink/v1"
        assert receipt["domains"]["legislation"]["count"] == 1
        assert receipt["domains"]["health-resource"]["count"] == 1
        assert receipt["domains"]["publication-hf"]["count"] == 1
        assert receipt["relationships"]["health_resource_to_dataset"] == {_UUID2: _UUID}
        assert receipt["status"] == "passed"

    def test_findings_present_status(self) -> None:
        """Malformed inputs produce findings-present status."""
        receipt = build_interlink(
            [],
            [{"dataset_id": "bad", "resource_id": "worse"}],
            {},
        )
        assert receipt["status"] == "findings-present"
        assert receipt["findings_count"] >= 2
