"""Contracts for preserving observations across independent capture cohorts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations.capture_inventory import (
    CaptureSnapshot,
    InventorySnapshot,
    build_capture_inventory,
)


def _snapshot(name: str, rows: list[dict[str, Any]]) -> InventorySnapshot:
    return InventorySnapshot(
        name,
        json.dumps(
            {
                "schema_version": "archive-govt-nz.health-source-census/v1",
                "record_count": len(rows),
                "records": rows,
            }
        ).encode(),
    )


def _row(
    url: str = "https://example.govt.nz/a.pdf", **changes: object
) -> dict[str, Any]:
    return {
        "source_id": "a",
        "url": url,
        "family": "treasury_vote_health_document",
        "media_type": "application/pdf",
        "disposition": "discovered",
        **changes,
    }


def _capture(request: InventorySnapshot, **changes: object) -> CaptureSnapshot:
    row = json.loads(request.data)["records"][0]
    result = {
        "source_id": row["source_id"],
        "url": row["url"],
        "request_url_sha256": hashlib.sha256(row["url"].encode()).hexdigest(),
        "state": "captured",
        "sha256": "a" * 64,
        "bytes": 7,
        "rights": {"state": "eligible", "license": "CC-BY-4.0"},
        **changes,
    }
    manifest = {
        "schema_version": "archive-govt-nz.health-capture-manifest/v1",
        "capture_context": {
            "contract": "health-capture-resume/v1",
            "census_sha256": hashlib.sha256(request.data).hexdigest(),
        },
        "results": [result],
    }
    return CaptureSnapshot(
        InventorySnapshot("capture.json", json.dumps(manifest).encode()), request
    )


def test_inventory_preserves_observations_aliases_versions_and_repeatability() -> None:
    request = _snapshot("request.json", [_row()])
    second = _snapshot(
        "later.json",
        [
            _row(source_id="alias", disposition="captured", object_sha256="a" * 64),
            _row(
                "https://example.govt.nz/b.pdf",
                source_id="b",
                disposition="captured",
                object_sha256="a" * 64,
            ),
        ],
    )
    capture = _capture(request)
    result = build_capture_inventory((request, second), (capture,))
    assert result == build_capture_inventory((second, request), (capture,))
    assert result["summary"]["resource_count"] == 2
    assert result["summary"]["recorded_captured_resource_count"] == 2
    first = result["resources"][0]
    assert first["source_ids"] == ["a", "alias"]
    assert first["versions"] == ["a" * 64]
    assert len(first["census_observations"]) == 2
    assert (
        first["capture_observations"][0]["request_binding"]
        == "capture_time_request_hash_verified"
    )
    assert first["fixity_state"] == "not_replayed_by_inventory"
    assert first["rights_state"] == "not_evaluated_by_inventory"
    revised = _snapshot(
        "revision.json", [_row(disposition="captured", object_sha256="b" * 64)]
    )
    both = build_capture_inventory((request, revised), (capture,))["resources"][0]
    assert both["versions"] == ["a" * 64, "b" * 64]


def test_legacy_context_is_explicit_and_never_fabricated() -> None:
    request = _snapshot("request.json", [_row()])
    capture = _capture(request)
    manifest = json.loads(capture.manifest.data)
    del manifest["capture_context"]
    legacy = CaptureSnapshot(
        InventorySnapshot("legacy.json", json.dumps(manifest).encode())
    )
    result = build_capture_inventory((request,), (legacy,))
    assert (
        result["resources"][0]["capture_observations"][0]["request_binding"]
        == "not_verified_legacy_request_context_unavailable"
    )


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"url": "https://example.govt.nz/other.pdf"}, "capture_source_not_in_census"),
        ({"request_url_sha256": "b" * 64}, "capture_request_url_mismatch"),
        ({"sha256": "../unsafe"}, "capture_digest_invalid"),
        ({"bytes": -1}, "capture_size_invalid"),
    ],
)
def test_capture_rejects_unbound_or_invalid_results(
    change: dict[str, Any], code: str
) -> None:
    request = _snapshot("request.json", [_row()])
    with pytest.raises(ValueError, match=code):
        build_capture_inventory((request,), (_capture(request, **change),))


def test_exact_request_bytes_and_unique_input_names_are_required() -> None:
    request = _snapshot("request.json", [_row()])
    capture = _capture(request)
    changed = InventorySnapshot(request.name, request.data + b" ")
    with pytest.raises(ValueError, match="capture_request_hash_mismatch"):
        build_capture_inventory(
            (request,), (CaptureSnapshot(capture.manifest, changed),)
        )
    with pytest.raises(ValueError, match="input_name_conflict"):
        build_capture_inventory((request, changed), ())
    with pytest.raises(ValueError, match="capture_request_missing"):
        build_capture_inventory((request,), (CaptureSnapshot(capture.manifest),))


def test_hash_bound_original_unversioned_request_and_failed_capture_are_retained() -> (
    None
):
    census = _snapshot("census.json", [_row()])
    original = InventorySnapshot(
        "request.json", json.dumps({"records": [_row()]}).encode()
    )
    capture = _capture(original, state="retryable", sha256=None, bytes=0)
    result = build_capture_inventory((census,), (capture,))
    resource = result["resources"][0]
    assert resource["capture_observations"][0]["record"]["state"] == "retryable"
    assert (
        resource["capture_observations"][0]["request_binding"]
        == "capture_time_request_hash_verified"
    )
    assert resource["versions"] == []
    assert result["summary"]["recorded_captured_resource_count"] == 0


@pytest.mark.parametrize(
    ("document", "code"),
    [
        (
            {"schema_version": "unknown", "records": [], "record_count": 0},
            "inventory_input_schema_invalid",
        ),
        ({"records": "not rows", "record_count": 0}, "inventory_rows_invalid"),
        (
            {
                "records": [{"source_id": "x", "url": "https://example.govt.nz/x"}] * 2,
                "record_count": 2,
            },
            "inventory_source_id_missing_or_duplicate",
        ),
        (
            {"records": [_row("../not-a-url")], "record_count": 1},
            "inventory_source_url_invalid",
        ),
        ({"records": [_row()], "record_count": 2}, "inventory_census_count_mismatch"),
        (
            {"records": [_row(disposition="captured")], "record_count": 1},
            "capture_digest_invalid",
        ),
    ],
)
def test_malformed_census_fails_closed(document: dict[str, Any], code: str) -> None:
    doc = {"schema_version": "archive-govt-nz.health-source-census/v1", **document}
    with pytest.raises(ValueError, match=code):
        build_capture_inventory(
            (InventorySnapshot("bad.json", json.dumps(doc).encode()),), ()
        )


def test_retained_cohort_rebuild_matches_inventory_without_native_payloads() -> None:
    track = (
        Path(__file__).parents[3]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
    )
    expected_bytes = (track / "capture-inventory-20261017.json").read_bytes()
    expected = json.loads(expected_bytes)
    files = {p.name: p for p in track.glob("*.json")}
    files.update(
        {p.name: p for p in (track / "capture-cohorts-20261005").glob("*.json")}
    )
    snapshots = {
        name: InventorySnapshot(name, files[name].read_bytes())
        for name in expected["inputs"]
    }
    census_names = {
        o["census"] for r in expected["resources"] for o in r["census_observations"]
    }
    capture_inputs = {
        o["manifest"]: o["request"]
        for r in expected["resources"]
        for o in r["capture_observations"]
    }
    actual = build_capture_inventory(
        tuple(snapshots[name] for name in census_names),
        tuple(
            CaptureSnapshot(snapshots[name], snapshots[request] if request else None)
            for name, request in capture_inputs.items()
        ),
    )
    assert actual == expected
    assert actual["summary"] == {
        "resource_count": 152,
        "recorded_captured_resource_count": 84,
        "census_observation_count": 155,
        "capture_observation_count": 85,
    }
    assert (
        json.loads((track / "source-census.json").read_bytes())["record_count"] == 143
    )
