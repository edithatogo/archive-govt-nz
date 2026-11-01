"""Exercise the original packet import with a dated official scan."""

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from tools.legislation_packet_records import recover_records


def test_recover_official_scan(tmp_path: Path) -> None:
    """Keep the source timestamp and reject a substituted packet."""
    work = "act_public_1875_34"
    expression = work + "_en_2007-09-03B"
    payload = b"%PDF-1.7\nfixture\n%%EOF"
    row = {
        "work_id": work,
        "expression_id": expression,
        "source_url": "https://www.legislation.govt.nz/act/public/1875/34/en/2007-09-03B/official_scan.pdf",
        "file": "scan.pdf",
        "format": "pdf_original_scan",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "retrieved": "2026-11-01T00:30:00Z",
        "bytes": len(payload),
    }
    packet = tmp_path / "originals.zip"
    with ZipFile(packet, "w") as archive:
        archive.writestr("originals/scan.pdf", payload)
        archive.writestr(
            "manifest.json",
            json.dumps({"file_prefix": "originals/", "originals": [row]}),
        )
    titles = {work: "Fixture"}
    pin = hashlib.sha256(packet.read_bytes()).hexdigest()
    (record,) = recover_records(packet, pin, titles)
    assert record.expression_id == expression
    assert record.retrieval_timestamp == row["retrieved"]
    with pytest.raises(ValueError, match="digest mismatch"):
        recover_records(packet, "0" * 64, titles)
