"""Regression for mixed item rights in one verified artifact."""

from __future__ import annotations

import json
import runpy
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from archive_govt_nz.warc import write_response_record

_module = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "tools/bronze_archiver.py")
)
digest = _module["digest"]
prepare = _module["prepare"]


def test_mixed_batch_holds_changed_bytes_and_rejects_tampering(tmp_path: Path) -> None:
    """No receipt or path alone admits a changed original or mismatched WARC."""
    url = "https://example.test"
    body = b"reviewed text"
    h = digest(body)
    w = write_response_record(
        tmp_path / "source.warc",
        url=url,
        status_code=200,
        headers={"content-type": "text/plain"},
        body=body,
    )
    item = {
        "uri": url,
        "sha256": h,
        "byte_count": len(body),
        "status": "captured",
        "status_code": 200,
        "warc": {
            "path": "build/warc/web/source.warc",
            "sha256": w.sha256,
            "record_id": w.record_id,
        },
    }
    another = {**item, "uri": url + "/other"}
    members = {
        "receipts/web/capture.json": json.dumps(
            {"source_set": "web", "status": "captured", "targets": [item, another]}
        ).encode(),
        "receipts/web/archive.json": b'{"status":"verified","failures":[]}',
        "receipts/web/replay.json": b'{"status":"verified","corrupted_records":0}',
        f"cas/web/sha256/{h[:2]}/{h}": body,
        "warc/web/source.warc": w.path.read_bytes(),
    }

    def artifact() -> bytes:
        stream = BytesIO()
        with ZipFile(stream, "w") as z:
            for k, v in members.items():
                z.writestr(k, v)
        return stream.getvalue()

    policy = {
        "targets": {
            url: {
                h: {
                    "decision": "publish",
                    "licence": "fixture",
                    "attribution": "fixture",
                    "policy": "fixture",
                    "content_type": "text/plain",
                }
            },
            another["uri"]: {},
        }
    }
    manifest, files = prepare(artifact(), "web", policy, {})
    assert [r["status"] for r in manifest["records"]] == ["archived", "held"]
    assert len(files) == 2
    members["warc/web/source.warc"] += b"extra"
    with pytest.raises(ValueError, match="resume_warc_mismatch"):
        prepare(artifact(), "web", policy, {})
