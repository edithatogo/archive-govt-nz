"""Preservation-layer count reconciliation contracts."""

from archive_govt_nz.layer_reconciliation import reconcile_layer_counts


def test_layer_counts_reconcile_without_claiming_complete_capture() -> None:
    """Matching layers reconcile while retaining the completeness limitation."""
    result = reconcile_layer_counts(
        manifest_counts={
            "raw_ckan_responses": 7,
            "captured_objects": 12,
            "derivatives": 3,
        },
        raw_count=7,
        captured_count=12,
        derivative_count=3,
    )

    assert result["status"] == "reconciled"
    assert all(result["checks"].values())
    assert "complete source capture" in result["limitations"][0]


def test_layer_count_drift_is_a_discrepancy() -> None:
    """Any layer-count mismatch fails closed."""
    result = reconcile_layer_counts(
        manifest_counts={
            "raw_ckan_responses": 7,
            "captured_objects": 12,
            "derivatives": 3,
        },
        raw_count=6,
        captured_count=12,
        derivative_count=3,
    )

    assert result["status"] == "discrepancy"
    assert result["checks"]["raw_ckan_responses"] is False
