# SPDX-License-Identifier: Apache-2.0
"""The tracked layout reports reconcile to one fixity-pinned capture cohort."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations.source_layout_reconciliation import (
    SourceLayoutReconciliationError,
    reconcile_source_layout_reports,
)

TRACK = (
    Path(__file__).resolve().parents[3]
    / "conductor"
    / "tracks"
    / "health_appropriations_medallion_assimilation_20260829"
)


def _evidence() -> tuple[bytes, bytes, bytes]:
    return (
        (TRACK / "source-census.json").read_bytes(),
        (TRACK / "source-layout-baseline-20261003.json").read_bytes(),
        (TRACK / "source-pdf-layout-baseline-20261018.json").read_bytes(),
    )


def test_workbook_and_pdf_baselines_reconcile_without_promoting_gaps() -> None:
    census, workbook, pdf = _evidence()
    report = reconcile_source_layout_reports(census, workbook, pdf, workbook, pdf)

    assert report["summary"] == {
        "captured_source_count": 75,
        "sources_with_structural_baseline": 65,
        "sources_without_structural_baseline": 10,
        "workbook_layout_source_count": 6,
        "pdf_layout_source_count": 59,
        "pdf_layout_unavailable_count": 0,
    }
    assert report["pinned_reports"]["workbook"]["layout_manifest_count"] == 10
    assert report["pinned_reports"]["pdf"]["pdf_capture_count"] == 59
    assert report["pinned_reports"]["workbook"]["recheck_layout_rows_unchanged"] is True
    assert report["pinned_reports"]["pdf"]["recheck_layout_rows_unchanged"] is True
    by_type = {row["media_type"]: row for row in report["media_types"]}
    assert by_type["application/pdf"]["sources_without_structural_baseline"] == 0
    assert by_type[
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ] == {
        "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "captured_source_count": 12,
        "sources_with_structural_baseline": 6,
        "sources_without_structural_baseline": 6,
    }
    assert all("url" not in row for row in report["unassessed_sources"])
    assert {row["reason"] for row in report["unassessed_sources"]} == {
        "silver_workbook_inventory_missing",
        "no_matching_workbook_or_pdf_layout_profile",
    }


def test_reconciliation_rejects_changed_layout_or_capture_identity() -> None:
    census, workbook, pdf = _evidence()
    changed_workbook = json.loads(workbook)
    changed_workbook["layouts"][0]["layout_sha256"] = "0" * 64
    with pytest.raises(
        SourceLayoutReconciliationError, match="workbook_layout_recheck_changed"
    ):
        reconcile_source_layout_reports(
            census,
            workbook,
            pdf,
            json.dumps(changed_workbook).encode(),
            pdf,
        )

    changed_pdf = json.loads(pdf)
    changed_pdf["capture_manifest_sha256"] = "0" * 64
    with pytest.raises(
        SourceLayoutReconciliationError, match="layout_cohort_identity_mismatch"
    ):
        reconcile_source_layout_reports(
            census, workbook, pdf, workbook, json.dumps(changed_pdf).encode()
        )


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("census_json", "source_census_invalid"),
        ("census_object", "source_census_invalid"),
        ("census_schema", "source_census_schema_invalid"),
        ("workbook_schema", "workbook_baseline_schema_invalid"),
        ("pdf_schema", "pdf_baseline_schema_invalid"),
        ("records_missing", "source_census_records_invalid"),
        ("record_not_object", "source_census_row_invalid"),
        ("duplicate_source", "source_id_missing_or_duplicate"),
        ("captured_fixity", "captured_source_fixity_invalid"),
        ("captured_media", "captured_source_media_type_missing"),
        ("layout_rows_missing", "layout_rows_invalid"),
        ("layout_row_not_object", "layout_row_invalid"),
        ("unknown_layout_source", "layout_source_not_captured"),
        ("wrong_layout_media", "layout_source_media_type_mismatch"),
        ("layout_fixity", "layout_source_fixity_mismatch"),
        ("layout_fingerprint", "layout_fingerprint_invalid"),
        ("duplicate_pdf_source", "layout_source_duplicate"),
        ("pdf_recheck_changed", "pdf_layout_recheck_changed"),
        ("unassessed_mismatch", "workbook_unassessed_sources_mismatch"),
        ("excluded_invalid", "excluded_silver_manifests_invalid"),
    ],
)
def test_reconciliation_fails_closed_on_malformed_or_changed_evidence(  # noqa: C901, PLR0912, PLR0915 - mutation matrix covers the error contract.
    mutation: str, code: str
) -> None:
    census_bytes, workbook_bytes, pdf_bytes = _evidence()
    census = json.loads(census_bytes)
    workbook = json.loads(workbook_bytes)
    pdf = json.loads(pdf_bytes)
    workbook_recheck = deepcopy(workbook)
    pdf_recheck = deepcopy(pdf)

    captured = next(
        row for row in census["records"] if row["disposition"] == "captured"
    )
    workbook_row = workbook["layouts"][0]
    pdf_row = pdf["pdf_layouts"][0]
    if mutation == "census_json":
        census_bytes = b"not-json"
    elif mutation == "census_object":
        census_bytes = b"[]"
    elif mutation == "census_schema":
        census["schema_version"] = "unknown"
    elif mutation == "workbook_schema":
        workbook["schema_version"] = "unknown"
    elif mutation == "pdf_schema":
        pdf_recheck["schema_version"] = "unknown"
    elif mutation == "records_missing":
        census["records"] = None
    elif mutation == "record_not_object":
        census["records"][0] = "invalid"
    elif mutation == "duplicate_source":
        census["records"].append(deepcopy(census["records"][0]))
    elif mutation == "captured_fixity":
        captured["object_sha256"] = "bad"
    elif mutation == "captured_media":
        captured["media_type"] = ""
    elif mutation == "layout_rows_missing":
        workbook["layouts"] = None
    elif mutation == "layout_row_not_object":
        workbook["layouts"][0] = None
    elif mutation == "unknown_layout_source":
        workbook["layouts"][0]["source_id"] = "not-captured"
    elif mutation == "wrong_layout_media":
        workbook_row["source_id"] = pdf_row["source_id"]
    elif mutation == "layout_fixity":
        workbook_row["source_object_sha256"] = "0" * 64
    elif mutation == "layout_fingerprint":
        workbook_row["layout_sha256"] = "bad"
    elif mutation == "duplicate_pdf_source":
        pdf["pdf_layouts"].append(deepcopy(pdf_row))
    elif mutation == "pdf_recheck_changed":
        pdf_recheck["pdf_layouts"][0]["layout_sha256"] = "0" * 64
    elif mutation == "baseline_overlap":
        workbook["layouts"][0]["source_id"] = pdf_row["source_id"]
        workbook["layouts"][0]["source_object_sha256"] = pdf_row["source_object_sha256"]
    elif mutation == "unassessed_mismatch":
        workbook_recheck["unassessed_source_ids"] = []
    elif mutation == "excluded_invalid":
        workbook_recheck["excluded_silver_manifests"] = "invalid"

    if mutation not in {"census_json", "census_object"}:
        census_bytes = json.dumps(census).encode()
        census_digest = hashlib.sha256(census_bytes).hexdigest()
        for report in (workbook, pdf, workbook_recheck, pdf_recheck):
            report["source_census_sha256"] = census_digest

    with pytest.raises(SourceLayoutReconciliationError, match=code):
        reconcile_source_layout_reports(
            census_bytes,
            json.dumps(workbook).encode(),
            json.dumps(pdf).encode(),
            json.dumps(workbook_recheck).encode(),
            json.dumps(pdf_recheck).encode(),
        )
