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
    assert report["summary"]["resource_count"] == 141
    assert report["summary"]["resource_dispositions"] == {
        "captured": 73,
        "out_of_scope": 68,
    }
    assert report["summary"]["context_series_vintage_count"] == 10
    resources = report["resources"]
    assert len({row["entity_id"] for row in resources}) == 141
    assert all(row["inventory_state"] for row in resources)
    assert all(
        row["temporal_coverage_state"].startswith("not_assessed") for row in resources
    )
    assert all(
        row["layout_drift_state"].startswith("not_assessed") for row in resources
    )
    assert all("not_evaluated" in row["rights"]["state"] for row in resources)
    contexts = report["context_series_vintages"]
    assert len({row["entity_id"] for row in contexts}) == 10
    assert all(row["target_vintage_label"] for row in contexts)
    assert all(row["rights"]["state"] == "not_evaluated" for row in contexts)
    assert report["capture_reconciliation"] == {
        "state": "recorded_not_replayed_manifest_unavailable",
        "matched_resource_count_recorded": 73,
        "manifest_name_recorded": "official-capture-2026-08-29-complete.json",
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
