"""Contracts for evidence-bounded whole-census source-health reporting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations.source_health_report import (
    CaptureEvidence,
    SourceHealthReportError,
    _capture_inputs,
    _verify_capture_result,
    build_report,
    render_markdown,
)

TRACK = (
    Path(__file__).parents[3]
    / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
)


def _real_report() -> dict[str, Any]:
    census_bytes = (TRACK / "source-census.json").read_bytes()
    context_bytes = (TRACK / "context-census.json").read_bytes()
    return build_report(
        json.loads(census_bytes),
        census_bytes,
        json.loads(context_bytes),
        context_bytes,
    )


def test_whole_census_report_has_a_state_for_every_resource_and_series_vintage() -> (
    None
):
    report = _real_report()

    assert report["schema_version"] == "archive-govt-nz.health-source-health-report/v1"
    assert report["summary"]["resource_count"] == 142
    assert report["summary"]["resource_dispositions"] == {
        "captured": 74,
        "out_of_scope": 68,
    }
    assert report["summary"]["context_series_vintage_count"] == 11
    resources = report["resources"]
    assert len({row["entity_id"] for row in resources}) == 142
    assert all(row["inventory_state"] for row in resources)
    assert all(
        row["temporal_coverage_state"].startswith("not_assessed") for row in resources
    )
    assert all(
        row["layout_drift_state"].startswith("not_assessed") for row in resources
    )
    assert all("not_evaluated" in row["rights"]["state"] for row in resources)
    contexts = report["context_series_vintages"]
    assert len({row["entity_id"] for row in contexts}) == 11
    assert all(row["target_vintage_label"] for row in contexts)
    assert all(row["rights"]["state"] == "not_evaluated" for row in contexts)
    assert report["capture_reconciliation"] == {
        "state": "recorded_not_replayed_manifest_unavailable",
        "matched_resource_count_recorded": 74,
        "manifest_name_recorded": "official-capture-2026-09-30-health-refresh.json",
    }


def test_markdown_lists_each_inventory_identity_and_states_limits() -> None:
    report = _real_report()

    markdown = render_markdown(report)

    assert "treasury-vote-health-pdf-0951064262bf028c" in markdown
    assert "population-national-annual-mean" in markdown
    assert "policy_reference_recorded_not_evaluated" in markdown
    assert "not_assessed_per_vintage_baseline_not_in_census" in markdown
    assert "recorded_not_replayed_manifest_unavailable" in markdown


def test_source_census_duplicate_ids_fail_closed() -> None:
    census = {
        "schema_version": "archive-govt-nz.health-source-census/v1",
        "record_count": 2,
        "records": [
            {"source_id": "same", "disposition": "captured"},
            {"source_id": "same", "disposition": "out_of_scope"},
        ],
    }
    context = {
        "schema_version": "archive-govt-nz.health-source-context-census/v1",
        "series": [{"id": "one", "vintage": "v1"}],
    }

    with pytest.raises(SourceHealthReportError, match="source_id_missing_or_duplicate"):
        build_report(census, b"census", context, b"context")


@pytest.mark.parametrize(
    ("census", "context", "error"),
    [
        ({"schema_version": "wrong"}, {"schema_version": "ok"}, "unsupported_source"),
        (
            {
                "schema_version": "archive-govt-nz.health-source-census/v1",
                "record_count": 0,
                "records": [],
            },
            {"schema_version": "wrong"},
            "unsupported_context",
        ),
        (
            {
                "schema_version": "archive-govt-nz.health-source-census/v1",
                "record_count": 1,
                "records": [],
            },
            {
                "schema_version": "archive-govt-nz.health-source-context-census/v1",
                "series": [{"id": "one", "vintage": "v1"}],
            },
            "source_census_record_count_mismatch",
        ),
    ],
)
def test_invalid_census_headers_fail_closed(
    census: dict[str, object], context: dict[str, object], error: str
) -> None:
    with pytest.raises(SourceHealthReportError, match=error):
        build_report(census, b"census", context, b"context")


def test_context_series_requires_unique_id_and_explicit_vintage() -> None:
    census = {
        "schema_version": "archive-govt-nz.health-source-census/v1",
        "record_count": 0,
        "records": [],
    }
    context = {
        "schema_version": "archive-govt-nz.health-source-context-census/v1",
        "series": [
            {"id": "same", "vintage": "v1"},
            {"id": "same", "vintage": "v2"},
        ],
    }

    with pytest.raises(
        SourceHealthReportError, match="context_series_identity_or_vintage_missing"
    ):
        build_report(census, b"census", context, b"context")


def test_capture_manifest_and_bronze_fixity_are_independently_reconciled(
    tmp_path: Path,
) -> None:
    payload = b"captured source bytes"
    digest = hashlib.sha256(payload).hexdigest()
    census = {
        "schema_version": "archive-govt-nz.health-source-census/v1",
        "cutoff": "2026-08-29",
        "record_count": 2,
        "capture_reconciliation": {
            "matched": 1,
            "capture_manifest": "capture.json",
        },
        "records": [
            {
                "source_id": "source-1",
                "title": "Source vintage 1",
                "family": "fiscal",
                "disposition": "captured",
                "object_sha256": digest,
                "license": "CC-BY-4.0",
                "rights_uri": "https://example.org/rights",
            },
            {
                "source_id": "source-2",
                "title": "Explicitly excluded vintage",
                "family": "fiscal",
                "disposition": "out_of_scope",
            },
        ],
    }
    context = {
        "schema_version": "archive-govt-nz.health-source-context-census/v1",
        "series": [{"id": "series-1", "vintage": "v1", "gaps": []}],
    }
    capture = {
        "cutoff": "2026-08-29",
        "results": [
            {
                "source_id": "source-1",
                "state": "captured",
                "sha256": digest,
                "bytes": len(payload),
                "rights": {
                    "license": "CC-BY-4.0",
                    "evidence": "https://example.org/rights",
                    "state": "eligible",
                },
            }
        ],
    }
    cas_root = tmp_path / "cas"
    object_path = cas_root / digest[:2] / digest
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(payload)
    census_bytes = json.dumps(census).encode()
    context_bytes = json.dumps(context).encode()
    capture_bytes = json.dumps(capture).encode()

    report = build_report(
        census,
        census_bytes,
        context,
        context_bytes,
        CaptureEvidence(capture, capture_bytes, "capture.json", cas_root),
    )

    assert report["capture_reconciliation"] == {
        "state": "capture_manifest_and_bronze_objects_verified",
        "manifest_name_recorded": "capture.json",
        "manifest_sha256": hashlib.sha256(capture_bytes).hexdigest(),
        "matched_resource_count_verified": 1,
        "bronze_object_count_verified": 1,
        "bronze_bytes_verified": len(payload),
        "capture_rights_states_recorded": {"eligible": 1},
    }
    resources = {row["entity_id"]: row for row in report["resources"]}
    assert resources["source-1"]["capture_receipt_rights_state"] == "eligible"
    assert resources["source-1"]["rights"]["state"] == (
        "policy_reference_recorded_not_evaluated"
    )
    assert resources["source-2"]["capture_receipt_rights_state"] == (
        "not_independently_verified"
    )


def test_capture_fixity_mismatch_fails_closed(tmp_path: Path) -> None:
    payload = b"original"
    digest = hashlib.sha256(payload).hexdigest()
    census = {
        "schema_version": "archive-govt-nz.health-source-census/v1",
        "cutoff": "cutoff",
        "record_count": 1,
        "capture_reconciliation": {
            "matched": 1,
            "capture_manifest": "capture.json",
        },
        "records": [
            {
                "source_id": "source-1",
                "disposition": "captured",
                "object_sha256": digest,
                "license": "CC-BY-4.0",
                "rights_uri": "https://example.org/rights",
            }
        ],
    }
    context = {
        "schema_version": "archive-govt-nz.health-source-context-census/v1",
        "series": [{"id": "series-1", "vintage": "v1"}],
    }
    capture = {
        "cutoff": "cutoff",
        "results": [
            {
                "source_id": "source-1",
                "state": "captured",
                "sha256": digest,
                "bytes": len(payload),
                "rights": {
                    "license": "CC-BY-4.0",
                    "evidence": "https://example.org/rights",
                },
            }
        ],
    }
    cas_root = tmp_path / "cas"
    object_path = cas_root / digest[:2] / digest
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(b"changed")

    with pytest.raises(SourceHealthReportError, match="capture_object_digest_mismatch"):
        build_report(
            census,
            json.dumps(census).encode(),
            context,
            json.dumps(context).encode(),
            CaptureEvidence(
                capture,
                json.dumps(capture).encode(),
                "capture.json",
                cas_root,
            ),
        )


def _minimal_inputs(
    *, records: list[object] | None = None, series: list[object] | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    census_records = records if records is not None else []
    context_series = (
        series if series is not None else [{"id": "series", "vintage": "v1"}]
    )
    return (
        {
            "schema_version": "archive-govt-nz.health-source-census/v1",
            "record_count": len(census_records),
            "records": census_records,
        },
        {
            "schema_version": "archive-govt-nz.health-source-context-census/v1",
            "series": context_series,
        },
    )


@pytest.mark.parametrize(
    ("records", "series", "error"),
    [
        ([None], None, "source_census_row_invalid"),
        ([{"source_id": "source"}], None, "source_disposition_missing"),
        (None, [None], "context_census_row_invalid"),
        (None, [], "context_census_series_missing"),
    ],
)
def test_invalid_census_rows_fail_closed(
    records: list[object] | None,
    series: list[object] | None,
    error: str,
) -> None:
    census, context = _minimal_inputs(records=records, series=series)
    with pytest.raises(SourceHealthReportError, match=error):
        build_report(census, b"census", context, b"context")


@pytest.mark.parametrize(
    ("census", "manifest", "name", "error"),
    [
        (
            {
                "records": [],
                "capture_reconciliation": {"capture_manifest": "capture.json"},
            },
            {"results": None},
            "capture.json",
            "capture_manifest_shape_invalid",
        ),
        (
            {"records": []},
            {"results": []},
            "capture.json",
            "capture_reconciliation_record_missing",
        ),
        (
            {"records": [], "capture_reconciliation": {}},
            {"results": []},
            "capture.json",
            "capture_manifest_name_missing",
        ),
        (
            {
                "records": [],
                "capture_reconciliation": {"capture_manifest": "capture.json"},
            },
            {"results": []},
            "other.json",
            "capture_manifest_name_mismatch",
        ),
        (
            {
                "cutoff": "one",
                "records": [],
                "capture_reconciliation": {"capture_manifest": "capture.json"},
            },
            {"cutoff": "two", "results": []},
            "capture.json",
            "capture_manifest_cutoff_mismatch",
        ),
        (
            {
                "records": [None],
                "capture_reconciliation": {"capture_manifest": "capture.json"},
            },
            {"results": []},
            "capture.json",
            "source_census_row_invalid",
        ),
        (
            {
                "records": [{}],
                "capture_reconciliation": {"capture_manifest": "capture.json"},
            },
            {"results": []},
            "capture.json",
            "source_id_missing_or_duplicate",
        ),
    ],
)
def test_capture_input_contract_failures(
    census: dict[str, Any], manifest: dict[str, Any], name: str, error: str
) -> None:
    with pytest.raises(SourceHealthReportError, match=error):
        _capture_inputs(
            census,
            CaptureEvidence(manifest, b"manifest", name, Path("unused-cas")),
        )


def _valid_capture_fixture(
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], str, Path]:
    payload = b"capture fixture"
    digest = hashlib.sha256(payload).hexdigest()
    census_row = {
        "source_id": "source-1",
        "disposition": "captured",
        "object_sha256": digest,
        "license": "CC-BY-4.0",
        "rights_uri": "https://example.org/rights",
    }
    result = {
        "source_id": "source-1",
        "state": "captured",
        "sha256": digest,
        "bytes": len(payload),
        "rights": {
            "license": "CC-BY-4.0",
            "evidence": "https://example.org/rights",
            "state": "eligible",
        },
    }
    cas_root = tmp_path / "cas"
    path = cas_root / digest[:2] / digest
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return census_row, result, digest, cas_root


@pytest.mark.parametrize(
    ("result", "inventory", "error"),
    [
        (None, {}, "capture_result_invalid"),
        (
            {"source_id": "", "sha256": "f" * 64},
            {},
            "capture_result_identity_or_digest_invalid",
        ),
        (
            {"source_id": "source", "sha256": "bad"},
            {},
            "capture_result_identity_or_digest_invalid",
        ),
        (
            {"source_id": "missing", "sha256": "f" * 64},
            {},
            "capture_result_not_in_census",
        ),
    ],
)
def test_capture_result_identity_contract_failures(
    tmp_path: Path,
    result: object,
    inventory: dict[str, Any],
    error: str,
) -> None:
    with pytest.raises(SourceHealthReportError, match=error):
        _verify_capture_result(result, inventory, tmp_path, set())


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("rights", "capture_result_rights_missing"),
        ("census", "capture_result_census_mismatch"),
        ("missing_object", "capture_object_missing"),
        ("digest", "capture_object_digest_mismatch"),
        ("size", "capture_object_size_mismatch"),
    ],
)
def test_capture_result_evidence_contract_failures(
    tmp_path: Path, mutation: str, error: str
) -> None:
    census_row, result, digest, cas_root = _valid_capture_fixture(tmp_path)
    if mutation == "rights":
        result.pop("rights")
    elif mutation == "census":
        result["state"] = "out_of_scope"
    elif mutation == "missing_object":
        (cas_root / digest[:2] / digest).unlink()
    elif mutation == "digest":
        (cas_root / digest[:2] / digest).write_bytes(b"changed bytes")
    elif mutation == "size":
        result["bytes"] = 0
    with pytest.raises(SourceHealthReportError, match=error):
        _verify_capture_result(result, {"source-1": census_row}, cas_root, set())


def test_capture_manifest_inventory_and_count_mismatches_fail_closed(
    tmp_path: Path,
) -> None:
    census, context = _minimal_inputs(
        records=[{"source_id": "source-1", "disposition": "captured"}]
    )
    census["capture_reconciliation"] = {
        "matched": 0,
        "capture_manifest": "capture.json",
    }
    capture = CaptureEvidence(
        {"cutoff": None, "results": []}, b"{}", "capture.json", tmp_path
    )
    with pytest.raises(
        SourceHealthReportError, match="capture_result_inventory_set_mismatch"
    ):
        build_report(census, b"census", context, b"context", capture)

    census, context = _minimal_inputs(
        records=[{"source_id": "source-1", "disposition": "out_of_scope"}]
    )
    census["capture_reconciliation"] = {
        "matched": 1,
        "capture_manifest": "capture.json",
    }
    capture = CaptureEvidence(
        {"cutoff": None, "results": []}, b"{}", "capture.json", tmp_path
    )
    with pytest.raises(SourceHealthReportError, match="capture_result_count_mismatch"):
        build_report(census, b"census", context, b"context", capture)
