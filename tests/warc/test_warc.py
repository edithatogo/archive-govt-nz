"""WARC receipt safety contracts."""

from pathlib import Path

import pytest

from archive_govt_nz.warc import WarcError, write_response_record


@pytest.mark.parametrize("status", [200, 302, 403, 404])
def test_warc_material_transaction_fixtures_are_reconstructable(
    tmp_path: Path, status: int
) -> None:
    """Success, redirect, and denial receipts preserve bounded diagnostics."""
    receipt = write_response_record(
        tmp_path / f"{status}.warc",
        url="https://catalogue.data.govt.nz/resource.csv",
        status_code=status,
        headers={"Content-Type": "text/csv", "Content-Length": "3"},
        body=b"abc",
        record_id=f"urn:uuid:{status}",
    )
    text = receipt.path.read_text(encoding="utf-8")
    assert f"HTTP/1.1 {status}" in text
    assert "WARC-Payload-Digest: sha256:" in text
    assert "abc" in text
    assert receipt.sha256


def test_warc_record_is_bounded_and_redacts_sensitive_headers(tmp_path: Path) -> None:
    """Only safe response headers and origin/path enter the record."""
    receipt = write_response_record(
        tmp_path / "capture.warc",
        url="https://catalogue.data.govt.nz/resource.csv?signature=secret",
        status_code=200,
        headers={
            "Content-Type": "text/csv",
            "Authorization": "Bearer secret",
            "ETag": "v1",
        },
        body=b"a,b\n1,2\n",
        record_id="urn:uuid:test",
    )
    text = receipt.path.read_text(encoding="utf-8")
    assert "WARC/1.1" in text
    assert "signature" not in text
    assert "Authorization" not in text
    assert "catalogue.data.govt.nz/resource.csv" in text
    assert receipt.byte_count == receipt.path.stat().st_size


def test_warc_rejects_non_https(tmp_path: Path) -> None:
    """Unsafe transport never receives a preservation receipt."""
    with pytest.raises(WarcError) as raised:
        write_response_record(
            tmp_path / "capture.warc",
            url="http://example.test/data",
            status_code=200,
            headers={},
            body=b"x",
        )
    assert raised.value.error_class == "unsafe_url"
