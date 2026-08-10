"""Derivative transformation and reconciliation contracts."""

from pathlib import Path

from archive_govt_nz.derivatives import build_dataset_derivatives


def test_derivatives_are_deterministic_and_duckdb_reconciled(tmp_path: Path) -> None:
    records = [
        {
            "id": "d1",
            "title": "Treasury",
            "name": "treasury",
            "organization": {"name": "The Treasury"},
            "resources": [{"id": "r1"}],
            "unknown": {"retained": True},
        }
    ]
    first = build_dataset_derivatives(records, tmp_path / "one")
    second = build_dataset_derivatives(records, tmp_path / "two")
    assert first.row_count == 1
    assert first.jsonl_sha256 == second.jsonl_sha256
    assert first.transformation_version == "derivatives/v1"
    assert "unknown_ckan_fields_not_projected" in first.information_loss
    assert first.parquet_path.read_bytes() == second.parquet_path.read_bytes()
    assert first.raw_ckan_path.read_bytes() == second.raw_ckan_path.read_bytes()
    assert b'"unknown"' in first.raw_ckan_path.read_bytes()
    assert len(first.raw_ckan_sha256) == 64
