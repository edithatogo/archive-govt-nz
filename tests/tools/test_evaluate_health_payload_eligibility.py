"""Tests for the deterministic health payload eligibility evaluator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = (
    Path(__file__).parents[2] / "tools" / "evaluate_health_payload_eligibility.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "evaluate_health_payload_eligibility", _TOOL_PATH
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

load_resource_snapshot = _MODULE.load_resource_snapshot
load_licence_map = _MODULE.load_licence_map
evaluate_resource = _MODULE.evaluate_resource
evaluate_all = _MODULE.evaluate_all
main = _MODULE.main


def _resource(dataset_id: str = "ds-1", url: str | None = "https://x/y.xlsx") -> dict:
    return {
        "dataset_id": dataset_id,
        "resource_id": "res-1",
        "url": url,
        "name": "Resource",
    }


class TestLoaders:
    """Snapshot and licence-map loading coverage."""

    def test_load_snapshot_resources(self, tmp_path: Path) -> None:
        """Snapshot with a resources array loads its entries."""
        """Snapshot with a resources array loads its entries."""
        snap = tmp_path / "snap.json"
        snap.write_text(json.dumps({"resources": [_resource()]}), encoding="utf-8")
        assert len(load_resource_snapshot(snap)) == 1

    def test_load_snapshot_rejects_non_array(self, tmp_path: Path) -> None:
        """A snapshot without a resources array fails closed."""
        bad = tmp_path / "bad.json"
        bad.write_text("{}", encoding="utf-8")
        with pytest.raises(TypeError, match="resources"):
            load_resource_snapshot(bad)

    def test_load_licence_map_normalises(self, tmp_path: Path) -> None:
        """Licence map values are normalised to lowercase stripped strings."""
        m = tmp_path / "map.json"
        m.write_text(json.dumps({"ds-1": " CC-BY-4.0 "}), encoding="utf-8")
        assert load_licence_map(m) == {"ds-1": "cc-by-4.0"}

    def test_load_licence_map_missing_file(self, tmp_path: Path) -> None:
        """Absent licence map yields an empty mapping."""
        assert load_licence_map(tmp_path / "none.json") == {}


class TestEvaluateResource:
    """Per-resource fail-closed classification coverage."""

    def test_open_licence_is_eligible(self) -> None:
        """Affirmative open-licence evidence makes the resource eligible."""
        classification, reason = evaluate_resource(_resource(), {"ds-1": "cc-by-4.0"})
        assert classification == "payload-eligible"
        assert "cc-by-4.0" in reason

    def test_missing_map_entry_stays_decision_required(self) -> None:
        """Absent licence evidence keeps the resource decision-required."""
        classification, reason = evaluate_resource(_resource(), {})
        assert classification == "decision-required"
        assert "no licence evidence" in reason

    def test_restricted_licence_stays_decision_required(self) -> None:
        """Non-open licence evidence never admits a payload."""
        classification, _ = evaluate_resource(_resource(), {"ds-1": "copyright"})
        assert classification == "decision-required"

    def test_eligible_without_url_fails_closed(self) -> None:
        """Eligible licence without a retrievable URL stays closed."""
        classification, reason = evaluate_resource(_resource(url=None), {"ds-1": "cc0"})
        assert classification == "decision-required"
        assert "URL" in reason

    def test_missing_identity_fails_closed(self) -> None:
        """Missing identity fields fail closed regardless of licence."""
        resource = {"dataset_id": "", "resource_id": "", "url": None}
        classification, reason = evaluate_resource(resource, {"": "cc0"})
        assert classification == "decision-required"
        assert "identity" in reason


class TestEvaluateAll:
    """Receipt construction and count aggregation coverage."""

    def test_counts_and_receipt_schema(self) -> None:
        """Receipt schema, counts, and fail-closed criteria are recorded."""
        resources = [
            _resource("ds-open"),
            _resource("ds-closed"),
            _resource("ds-missing"),
        ]
        licence_map = {"ds-open": "ogl-nz", "ds-closed": "copyright"}
        receipt = evaluate_all(resources, licence_map)
        assert receipt["schema_version"] == "archive-govt-nz.health-eligibility/v1"
        assert receipt["counts"] == {
            "payload-eligible": 1,
            "decision-required": 2,
        }
        assert len(receipt["dispositions"]) == 3
        assert receipt["criteria"]["fail_closed_default"] is True

    def test_zero_eligible_on_empty_map(self) -> None:
        """Empty licence map yields an honest zero-eligible result."""
        receipt = evaluate_all([_resource()], {})
        assert receipt["counts"]["payload-eligible"] == 0
        assert receipt["counts"]["decision-required"] == 1
