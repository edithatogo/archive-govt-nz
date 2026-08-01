"""Tests for Ministry of Health inventory reconciliation."""

import importlib.util
from pathlib import Path
from typing import Any, cast

_SPEC = importlib.util.spec_from_file_location(
    "reconcile_moh_discovery",
    Path(__file__).parents[2] / "tools" / "reconcile_moh_discovery.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
reconcile = _MODULE.reconcile


def _receipt(
    datasets: list[dict[str, Any]], observed: str = "2026-08-01T00:00:00Z"
) -> dict[str, object]:
    return {
        "schema": "archive-govt-nz.moh-discovery/v1",
        "observed_at": observed,
        "scope": {
            "datasets": datasets,
            "resource_count": sum(int(x["resource_count"]) for x in datasets),
        },
    }


def test_reconcile_reports_stable_dataset_inventory() -> None:
    """Identical inventories reconcile as stable."""
    datasets = cast(
        "list[dict[str, Any]]",
        [{"id": "a", "resource_count": 2}, {"id": "b", "resource_count": 1}],
    )
    result = reconcile(_receipt(datasets), _receipt(datasets, "2026-08-02T00:00:00Z"))
    assert result["stable"] is True
    assert result["counts"]["first_resources"] == 3


def test_reconcile_reports_added_and_changed_datasets() -> None:
    """Added and changed datasets are explicitly reported."""
    first = _receipt([{"id": "a", "resource_count": 1}])
    second = _receipt(
        [{"id": "a", "resource_count": 2}, {"id": "b", "resource_count": 1}]
    )
    result = reconcile(first, second)
    assert result["stable"] is False
    assert result["counts"]["added_dataset_ids"] == ["b"]
    assert result["counts"]["changed_dataset_ids"] == ["a"]
