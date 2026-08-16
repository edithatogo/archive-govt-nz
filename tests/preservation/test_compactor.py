"""Test suite for ArchiveCompactor."""

from __future__ import annotations

import gzip
import zipfile
from typing import TYPE_CHECKING

from archive_govt_nz.compactor import ArchiveCompactor

if TYPE_CHECKING:
    from pathlib import Path


def test_create_warc_record() -> None:
    """Validate ISO 28500 single WARC record generation."""
    rec = ArchiveCompactor.create_warc_record(
        uri="https://health.govt.nz",
        content_type="text/html",
        payload=b"<html>Hello</html>",
        warc_date="2026-08-17T00:00:00Z",
    )
    assert b"WARC/1.0\r\n" in rec
    assert b"WARC-Type: response\r\n" in rec
    assert b"WARC-Target-URI: https://health.govt.nz\r\n" in rec
    assert b"<html>Hello</html>" in rec


def test_pack_records_to_warc_gz_and_wacz(tmp_path: Path) -> None:
    """Validate packing multiple records into .warc.gz and .wacz."""
    records = [
        ("https://health.govt.nz/feed", b"<rss></rss>", "application/rss+xml"),
        ("https://health.govt.nz/page", b"<html>Page</html>", "text/html"),
    ]
    warc_gz = tmp_path / "archive.warc.gz"
    out_warc = ArchiveCompactor.pack_records_to_warc_gz(records, warc_gz)
    assert out_warc.is_file()

    # Verify warc gz is readable
    with gzip.open(out_warc, "rb") as gz:
        data = gz.read()
    assert b"WARC-Type: warcinfo" in data
    assert b"WARC-Target-URI: https://health.govt.nz/feed" in data

    # Pack to WACZ
    wacz_path = tmp_path / "archive.wacz"
    out_wacz = ArchiveCompactor.pack_to_wacz(
        out_warc, {"manifest": "v1", "records": 2}, wacz_path
    )
    assert out_wacz.is_file()

    with zipfile.ZipFile(out_wacz, "r") as zf:
        namelist = zf.namelist()
        assert "datapackage.json" in namelist
        assert "archive/archive.warc.gz" in namelist
