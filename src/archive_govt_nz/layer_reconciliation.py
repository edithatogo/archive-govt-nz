"""Reconcile preservation-layer counts without transferring payloads."""

from __future__ import annotations

from typing import Any


def reconcile_layer_counts(
    *,
    manifest_counts: dict[str, int],
    raw_count: int,
    captured_count: int,
    derivative_count: int,
) -> dict[str, Any]:
    """Compare release-manifest counts with independently observed layers."""
    observed = {
        "raw_ckan_responses": raw_count,
        "captured_objects": captured_count,
        "derivatives": derivative_count,
    }
    checks = {key: manifest_counts.get(key) == value for key, value in observed.items()}
    return {
        "schema_version": "archive-govt-nz.layer-reconciliation/v1",
        "manifest": dict(manifest_counts),
        "observed": observed,
        "checks": checks,
        "status": "reconciled" if all(checks.values()) else "discrepancy",
        "limitations": [
            "Layer count reconciliation does not claim complete source capture.",
            (
                "Restricted and unavailable resources remain represented by policy "
                "receipts."
            ),
        ],
    }
