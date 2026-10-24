# SPDX-License-Identifier: Apache-2.0
"""The tracked layout reports reconcile to one fixity-pinned capture cohort."""

from __future__ import annotations

import json
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
