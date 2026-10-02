"""PDF layout baselines retain page structure without extracted content."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.errors import FileNotDecryptedError, PdfReadError

from archive_govt_nz.domains.health_appropriations.pdf_layout_baseline import (
    PdfLayoutBaselineError,
    _parse_pdf,
    build_pdf_layout_baseline_report,
)


def _blank_pdf(width: int, height: int) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=width, height=height)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _capture_fixture(
    tmp_path: Path, pdfs: list[tuple[str, bytes]]
) -> tuple[bytes, bytes, Path]:
    cas = tmp_path / "cas"
    records = []
    results = []
    for source_id, payload in pdfs:
        digest = hashlib.sha256(payload).hexdigest()
        path = cas / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        records.append(
            {
                "source_id": source_id,
                "family": "treasury_vote_health_document",
                "title": source_id,
                "disposition": "captured",
            }
        )
        results.append(
            {
                "source_id": source_id,
                "state": "captured",
                "content_type": "application/pdf",
                "sha256": digest,
                "bytes": len(payload),
            }
        )
    census = json.dumps(
        {
            "schema_version": "archive-govt-nz.health-source-census/v1",
            "cutoff": "2026-09-30",
            "records": records,
        }
    ).encode()
    capture = json.dumps({"cutoff": "2026-09-30", "results": results}).encode()
    return census, capture, cas


def test_pdf_layout_report_records_page_geometry_and_vintage_variation(
    tmp_path: Path,
) -> None:
    census, capture, cas = _capture_fixture(
        tmp_path,
        [
            ("vote-health-2025", _blank_pdf(612, 792)),
            ("vote-health-2026", _blank_pdf(720, 900)),
        ],
    )

    report = build_pdf_layout_baseline_report(census, capture, cas)

    assert report["summary"] == {
        "pdf_capture_count": 2,
        "layout_baseline_count": 2,
        "layout_unavailable_count": 0,
        "family_count": 1,
    }
    assert report["families"][0]["state"] == "layout_variation_observed"
    assert len(report["pdf_layouts"][0]["layout"]["page_layouts"]) == 1
    assert all(
        "text" not in page
        for row in report["pdf_layouts"]
        for page in row.get("layout", {}).get("page_layouts", [])
    )
    assert report == build_pdf_layout_baseline_report(census, capture, cas)


def test_pdf_layout_report_rejects_bronze_fixity_mismatch(tmp_path: Path) -> None:
    census, capture, cas = _capture_fixture(
        tmp_path, [("vote-health-2025", _blank_pdf(612, 792))]
    )
    results = json.loads(capture)
    digest = results["results"][0]["sha256"]
    (cas / digest[:2] / digest).write_bytes(b"tampered")

    with pytest.raises(PdfLayoutBaselineError, match="pdf_bronze_object_hash_mismatch"):
        build_pdf_layout_baseline_report(census, capture, cas)


def test_pdf_layout_report_rejects_capture_without_census_identity(
    tmp_path: Path,
) -> None:
    census, capture, cas = _capture_fixture(
        tmp_path, [("vote-health-2025", _blank_pdf(612, 792))]
    )
    manifest = json.loads(capture)
    manifest["results"][0]["source_id"] = "unlisted-source"

    with pytest.raises(PdfLayoutBaselineError, match="pdf_capture_identity_invalid"):
        build_pdf_layout_baseline_report(census, json.dumps(manifest).encode(), cas)


def test_pdf_layout_report_ignores_non_pdf_capture_records(tmp_path: Path) -> None:
    census, capture, cas = _capture_fixture(
        tmp_path, [("vote-health-2025", _blank_pdf(612, 792))]
    )
    manifest = json.loads(capture)
    manifest["results"][0]["content_type"] = "application/octet-stream"

    report = build_pdf_layout_baseline_report(
        census, json.dumps(manifest).encode(), cas
    )

    assert report["summary"]["pdf_capture_count"] == 0
    assert report["pdf_layouts"] == []


def test_parse_pdf_reports_encrypted_and_malformed_sources_as_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class EncryptedReader:
        is_encrypted = True

        def __init__(self, *_: object, **__: object) -> None:
            pass

    monkeypatch.setattr(
        "archive_govt_nz.domains.health_appropriations.pdf_layout_baseline.PdfReader",
        EncryptedReader,
    )
    assert _parse_pdf(b"valid-reader-stub") == (None, "encrypted_pdf")
    monkeypatch.setattr(
        "archive_govt_nz.domains.health_appropriations.pdf_layout_baseline.PdfReader",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(PdfReadError("bad PDF")),
    )
    assert _parse_pdf(b"malformed") == (None, "pdf_parse_error")
    assert FileNotDecryptedError("locked")


def test_pdf_layout_report_fails_closed_on_invalid_inputs_and_bronze_metadata(
    tmp_path: Path,
) -> None:
    census, capture, cas = _capture_fixture(
        tmp_path, [("vote-health-2025", _blank_pdf(612, 792))]
    )
    invalid_inputs = [
        (b"not-json", capture, "pdf_layout_input_invalid"),
        (
            json.dumps({"schema_version": "unknown"}).encode(),
            capture,
            "pdf_layout_census_schema_invalid",
        ),
        (
            census,
            json.dumps({"cutoff": "other", "results": []}).encode(),
            "pdf_layout_cutoff_mismatch",
        ),
        (
            json.dumps(
                {
                    "schema_version": "archive-govt-nz.health-source-census/v1",
                    "cutoff": "2026-09-30",
                    "records": None,
                }
            ).encode(),
            capture,
            "pdf_layout_input_shape_invalid",
        ),
    ]
    for invalid_census, invalid_capture, error in invalid_inputs:
        with pytest.raises(PdfLayoutBaselineError, match=error):
            build_pdf_layout_baseline_report(invalid_census, invalid_capture, cas)

    manifest = json.loads(capture)
    manifest["results"][0]["bytes"] += 1
    with pytest.raises(PdfLayoutBaselineError, match="pdf_bronze_object_size_mismatch"):
        build_pdf_layout_baseline_report(census, json.dumps(manifest).encode(), cas)

    digest = manifest["results"][0]["sha256"]
    (cas / digest[:2] / digest).unlink()
    with pytest.raises(PdfLayoutBaselineError, match="pdf_bronze_object_missing"):
        build_pdf_layout_baseline_report(census, capture, cas)
