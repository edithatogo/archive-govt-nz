"""Source layout inventories bind to captured bytes and reviewed Silver manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations.source_layout_baseline import (
    SourceLayoutBaselineError,
    build_source_layout_baseline_report,
)


def _write_manifest(
    root: Path, name: str, digest: str, vintage: str, dimension: str
) -> None:
    directory = root / name
    directory.mkdir(parents=True)
    payload = {
        "schema_version": "archive-govt-nz.test-silver/v1",
        "source_object_sha256": digest,
        "source_vintage": vintage,
        "transformation_id": "test-workbook/v1",
        "workbook_inventory": {
            "kind": "xlsx",
            "schema_version": "archive-govt-nz.workbook-inventory/v1",
            "package_member_count": 1,
            "package_members": ["xl/workbook.xml"],
            "sheets": [
                {
                    "title": "Raw Data",
                    "state": "visible",
                    "dimension": dimension,
                    "max_row": int(dimension.rsplit(":", maxsplit=1)[-1][1:]),
                    "max_column": 2,
                    "table_names": [],
                    "table_ranges": [],
                }
            ],
        },
    }
    (directory / "MANIFEST.json").write_text(json.dumps(payload), encoding="utf-8")


def test_layout_baselines_bind_captured_inputs_and_report_vintage_variation(
    tmp_path: Path,
) -> None:
    cas = tmp_path / "cas"
    silver = tmp_path / "silver"
    census_records = []
    capture_results = []
    digests = []
    for source_id, vintage, payload in (
        ("source-a", "Budget-2025", b"source A"),
        ("source-b", "Budget-2026", b"source B"),
    ):
        digest = hashlib.sha256(payload).hexdigest()
        digests.append(digest)
        path = cas / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        census_records.append(
            {
                "source_id": source_id,
                "family": "budget",
                "title": vintage,
                "disposition": "captured",
                "object_sha256": digest,
            }
        )
        capture_results.append(
            {
                "source_id": source_id,
                "state": "captured",
                "sha256": digest,
                "bytes": len(payload),
            }
        )
    _write_manifest(silver, "repeat-a", digests[0], "Budget-2025", "A1:B2")
    _write_manifest(silver, "repeat-b", digests[0], "Budget-2025", "A1:B2")
    _write_manifest(silver, "next-vintage", digests[1], "Budget-2026", "A1:B3")
    census = json.dumps(
        {
            "schema_version": "archive-govt-nz.health-source-census/v1",
            "cutoff": "2026-09-30",
            "records": census_records,
        }
    ).encode()
    capture = json.dumps({"cutoff": "2026-09-30", "results": capture_results}).encode()

    report = build_source_layout_baseline_report(census, capture, silver, cas)

    assert report["summary"] == {
        "captured_object_count_verified": 2,
        "captured_objects_with_layout_baseline": 2,
        "captured_sources_with_layout_baseline": 2,
        "captured_sources_without_layout_baseline": 0,
        "layout_manifest_count": 3,
        "transformation_count": 1,
    }
    comparison = report["comparisons"][0]
    assert comparison["vintages"][0]["state"] == "stable"
    assert comparison["cross_vintage_state"] == "layout_variation_observed"
    assert comparison["normalization_approval"] == "not_granted"
    assert report == build_source_layout_baseline_report(census, capture, silver, cas)


def test_layout_baseline_rejects_corrupt_cas_bytes(tmp_path: Path) -> None:
    cas = tmp_path / "cas"
    silver = tmp_path / "silver"
    digest = hashlib.sha256(b"original").hexdigest()
    path = cas / digest[:2] / digest
    path.parent.mkdir(parents=True)
    path.write_bytes(b"tampered")
    census = json.dumps(
        {
            "schema_version": "archive-govt-nz.health-source-census/v1",
            "cutoff": "2026-09-30",
            "records": [
                {
                    "source_id": "source-a",
                    "disposition": "captured",
                    "object_sha256": digest,
                }
            ],
        }
    ).encode()
    capture = json.dumps(
        {
            "cutoff": "2026-09-30",
            "results": [
                {
                    "source_id": "source-a",
                    "state": "captured",
                    "sha256": digest,
                    "bytes": 8,
                }
            ],
        }
    ).encode()

    with pytest.raises(SourceLayoutBaselineError, match="bronze_object_hash_mismatch"):
        build_source_layout_baseline_report(census, capture, silver, cas)


def test_unmatched_and_nonworkbook_silver_manifests_stay_unassessed(
    tmp_path: Path,
) -> None:
    cas = tmp_path / "cas"
    silver = tmp_path / "silver"
    payload = b"captured input"
    digest = hashlib.sha256(payload).hexdigest()
    cas_path = cas / digest[:2] / digest
    cas_path.parent.mkdir(parents=True)
    cas_path.write_bytes(payload)
    for directory, manifest in (
        (
            "normalized-nonworkbook",
            {"source_object_sha256": digest, "transformation_id": "csv/v1"},
        ),
        (
            "stale-outside-census",
            {"source_object_sha256": "a" * 64, "transformation_id": "csv/v1"},
        ),
    ):
        path = silver / directory / "MANIFEST.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(manifest), encoding="utf-8")
    census = json.dumps(
        {
            "schema_version": "archive-govt-nz.health-source-census/v1",
            "cutoff": "2026-09-30",
            "records": [
                {"source_id": "source-a", "disposition": "captured", "family": "cpi"}
            ],
        }
    ).encode()
    capture = json.dumps(
        {
            "cutoff": "2026-09-30",
            "results": [
                {
                    "source_id": "source-a",
                    "state": "captured",
                    "sha256": digest,
                    "bytes": len(payload),
                }
            ],
        }
    ).encode()

    report = build_source_layout_baseline_report(census, capture, silver, cas)

    assert report["summary"]["captured_sources_without_layout_baseline"] == 1
    assert report["layouts"] == []
    assert report["excluded_silver_manifests"][0]["state"] == (
        "outside_pinned_capture_scope"
    )
    assert report["unassessed_source_ids"] == ["source-a"]
    manifest_path = silver / "normalized-nonworkbook" / "MANIFEST.json"
    malformed_manifest = {
        "source_object_sha256": digest,
        "source_vintage": "2026-Q2",
        "transformation_id": "test/v1",
        "workbook_inventory": {"sheets": None},
    }
    manifest_path.write_text(json.dumps(malformed_manifest), encoding="utf-8")
    with pytest.raises(
        SourceLayoutBaselineError, match="silver_workbook_sheets_invalid"
    ):
        build_source_layout_baseline_report(census, capture, silver, cas)
    malformed_manifest["workbook_inventory"]["sheets"] = [None]
    manifest_path.write_text(json.dumps(malformed_manifest), encoding="utf-8")
    with pytest.raises(
        SourceLayoutBaselineError, match="silver_workbook_sheet_invalid"
    ):
        build_source_layout_baseline_report(census, capture, silver, cas)


def test_capture_census_and_bronze_fixity_gates_fail_closed(tmp_path: Path) -> None:
    payload = b"captured bytes"
    digest = hashlib.sha256(payload).hexdigest()
    cas = tmp_path / "cas"
    object_path = cas / digest[:2] / digest
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(payload)
    silver = tmp_path / "silver"
    census = {
        "schema_version": "archive-govt-nz.health-source-census/v1",
        "cutoff": "2026-09-30",
        "records": [{"source_id": "source-a", "disposition": "captured"}],
    }
    capture = {
        "cutoff": "2026-09-30",
        "results": [
            {
                "source_id": "source-a",
                "state": "captured",
                "sha256": digest,
                "bytes": len(payload),
            }
        ],
    }

    cases = [
        (
            census | {"schema_version": "wrong"},
            capture,
            "source_census_schema_invalid",
        ),
        (
            census,
            capture | {"cutoff": "wrong"},
            "capture_census_cutoff_mismatch",
        ),
        (
            census,
            capture | {"results": []},
            "capture_census_reconciliation_mismatch",
        ),
        (
            census
            | {"records": [{"source_id": "source-a", "disposition": "out_of_scope"}]},
            capture,
            "capture_inventory_state_mismatch",
        ),
        (
            census,
            capture | {"results": [capture["results"][0] | {"bytes": 999}]},
            "bronze_object_size_mismatch",
        ),
        (
            census,
            capture | {"results": [capture["results"][0] | {"sha256": "a" * 64}]},
            "bronze_object_missing",
        ),
    ]
    for source_census, capture_manifest, error in cases:
        with pytest.raises(SourceLayoutBaselineError, match=error):
            build_source_layout_baseline_report(
                json.dumps(source_census).encode(),
                json.dumps(capture_manifest).encode(),
                silver,
                cas,
            )
