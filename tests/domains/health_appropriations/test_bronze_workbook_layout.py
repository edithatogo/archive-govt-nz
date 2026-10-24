"""Bronze workbook structure is hash-bound without admitting its contents."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations.bronze_workbook_layout import (
    BronzeWorkbookLayoutError,
    build_bronze_workbook_layout_report,
)

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_CSV = "text/csv"


def _workbook(value: str) -> bytes:
    workbook = Workbook()
    sheet = workbook.create_sheet("Observed layout")
    sheet.append(["Column", value])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _evidence(cas: Path, files: dict[str, tuple[str, bytes]]) -> tuple[bytes, bytes]:
    records = []
    results = []
    for source_id, (media_type, payload) in sorted(files.items()):
        digest = hashlib.sha256(payload).hexdigest()
        (cas / digest[:2]).mkdir(parents=True, exist_ok=True)
        (cas / digest[:2] / digest).write_bytes(payload)
        records.append(
            {
                "source_id": source_id,
                "disposition": "captured",
                "media_type": media_type,
                "family": "fixture",
            }
        )
        results.append(
            {
                "source_id": source_id,
                "state": "captured",
                "sha256": digest,
                "bytes": len(payload),
            }
        )
    census = json.dumps(
        {
            "schema_version": "archive-govt-nz.health-source-census/v1",
            "cutoff": "2026-10-24T00:00:00Z",
            "records": records,
        },
        sort_keys=True,
    ).encode()
    capture = json.dumps(
        {"cutoff": "2026-10-24T00:00:00Z", "results": results}, sort_keys=True
    ).encode()
    return census, capture


def test_bronze_layout_report_fingerprints_structure_without_cell_values(
    tmp_path: Path,
) -> None:
    files = {
        "workbook-a": (_XLSX, _workbook("secret source value")),
        "workbook-b": (_XLSX, _workbook("another value")),
        "csv-a": (_CSV, b"not an xlsx"),
    }
    census, capture = _evidence(tmp_path / "cas", files)

    first = build_bronze_workbook_layout_report(census, capture, tmp_path / "cas")
    second = build_bronze_workbook_layout_report(census, capture, tmp_path / "cas")

    assert first == second
    assert first["summary"] == {
        "captured_source_count": 3,
        "captured_xlsx_count": 2,
        "xlsx_with_bronze_layout": 2,
        "xlsx_layout_unavailable": 0,
    }
    encoded = json.dumps(first)
    assert "secret source value" not in encoded
    assert "another value" not in encoded
    layouts = first["layouts"]
    assert isinstance(layouts, list)
    assert all(row["layout_sha256"] for row in layouts)
    assert first["limitations"]


def test_bronze_layout_report_rejects_capture_fixity_drift(tmp_path: Path) -> None:
    payload = _workbook("value")
    census, capture = _evidence(tmp_path / "cas", {"workbook": (_XLSX, payload)})
    record = json.loads(capture)
    record["results"][0]["bytes"] += 1

    with pytest.raises(
        BronzeWorkbookLayoutError, match="bronze_object_fixity_mismatch"
    ):
        build_bronze_workbook_layout_report(
            census, json.dumps(record).encode(), tmp_path / "cas"
        )


def test_bronze_layout_report_requires_complete_capture_reconciliation(
    tmp_path: Path,
) -> None:
    census, capture = _evidence(tmp_path / "cas", {"workbook": (_XLSX, _workbook("v"))})
    record = json.loads(capture)
    record["results"] = []

    with pytest.raises(
        BronzeWorkbookLayoutError, match="capture_census_reconciliation_mismatch"
    ):
        build_bronze_workbook_layout_report(
            census, json.dumps(record).encode(), tmp_path / "cas"
        )


@pytest.mark.parametrize(
    ("census_bytes", "capture_bytes", "error"),
    [
        (b"{", b"{}", "source_census_invalid"),
        (b"[]", b"{}", "source_census_invalid"),
        (
            json.dumps(
                {"schema_version": "wrong", "cutoff": "d", "records": []}
            ).encode(),
            json.dumps({"cutoff": "d", "results": []}).encode(),
            "source_census_schema_invalid",
        ),
        (
            json.dumps(
                {
                    "schema_version": "archive-govt-nz.health-source-census/v1",
                    "cutoff": "one",
                    "records": [],
                }
            ).encode(),
            json.dumps({"cutoff": "two", "results": []}).encode(),
            "capture_census_cutoff_mismatch",
        ),
    ],
)
def test_bronze_layout_report_rejects_invalid_pinned_documents(
    tmp_path: Path,
    census_bytes: bytes,
    capture_bytes: bytes,
    error: str,
) -> None:
    with pytest.raises(BronzeWorkbookLayoutError, match=error):
        build_bronze_workbook_layout_report(census_bytes, capture_bytes, tmp_path)


def test_bronze_layout_report_records_unavailable_workbook_profile(
    tmp_path: Path,
) -> None:
    census, capture = _evidence(
        tmp_path / "cas", {"workbook": (_XLSX, b"not a workbook")}
    )

    report = build_bronze_workbook_layout_report(census, capture, tmp_path / "cas")

    assert report["summary"]["xlsx_layout_unavailable"] == 1
    assert report["unavailable"] == [
        {"source_id": "workbook", "reason": "workbook_layout_invalid"}
    ]


def test_bronze_layout_report_rejects_malformed_capture_identity(
    tmp_path: Path,
) -> None:
    census, capture = _evidence(
        tmp_path / "cas", {"workbook": (_XLSX, _workbook("value"))}
    )
    record = json.loads(capture)
    record["results"][0]["sha256"] = "invalid"

    with pytest.raises(BronzeWorkbookLayoutError, match="capture_identity_invalid"):
        build_bronze_workbook_layout_report(
            census, json.dumps(record).encode(), tmp_path / "cas"
        )
