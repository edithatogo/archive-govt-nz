"""Synthetic generated contracts for archive framing and admission boundaries."""

from __future__ import annotations

import gzip
import io
import os
import tempfile
import zipfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from archive_govt_nz.bronze.sniffer import (
    MAX_SNIFF_HEADER_BYTES,
    sniff_magic_mime,
    validate_payload_signature,
)
from archive_govt_nz.cli_integrity import (
    _resolve_manifest_entry,
    _verify_wacz_path,
    _verify_warc_stream,
)

_EXAMPLES = int(os.environ.get("ARCHIVE_FUZZ_EXAMPLES", "100"))
if not 1 <= _EXAMPLES <= 1000:
    msg = "ARCHIVE_FUZZ_EXAMPLES must be between 1 and 1000"
    raise ValueError(msg)
_BOUNDED = settings(max_examples=_EXAMPLES, deadline=1000)
_PAYLOAD = st.binary(max_size=4096)


def _record(payload: bytes, *, declared: int | None = None) -> bytes:
    """Build a synthetic WARC resource with an independently computed byte count."""
    length = len(payload) if declared is None else declared
    header = f"WARC/1.1\r\nWARC-Type: resource\r\nContent-Length: {length}\r\n\r\n"
    return header.encode("ascii") + payload


@_BOUNDED
@given(
    prefix=st.binary(min_size=MAX_SNIFF_HEADER_BYTES, max_size=MAX_SNIFF_HEADER_BYTES),
    tail=_PAYLOAD,
)
def test_sniffing_depends_only_on_the_documented_prefix(
    prefix: bytes, tail: bytes
) -> None:
    """Bytes beyond the sniff budget cannot change a signature decision."""
    assert sniff_magic_mime(prefix + tail) == sniff_magic_mime(prefix)
    assert validate_payload_signature(prefix + tail) == validate_payload_signature(
        prefix
    )


@_BOUNDED
@given(payload=_PAYLOAD)
def test_arbitrary_bytes_produce_consistent_admission_receipts(payload: bytes) -> None:
    """Rejection always has an error; successful signatures carry no error."""
    result = validate_payload_signature(payload, "application/pdf")
    assert result.detected_mime == sniff_magic_mime(payload)
    assert result.is_valid == (result.error is None)
    if result.is_valid:
        assert result.detected_mime == "application/pdf"
        assert not result.is_polyglot


@_BOUNDED
@given(
    tag=st.sampled_from([b"<html>", b"<HEAD>", b"<body>", b"<!DOCTYPE html>"]),
    tail=_PAYLOAD,
)
def test_disguised_html_cannot_enter_pdf_admission(tag: bytes, tail: bytes) -> None:
    """HTML at the beginning of a claimed PDF must fail closed."""
    result = validate_payload_signature(tag + tail, " APPLICATION/PDF ; charset=utf-8 ")
    assert not result.is_valid
    assert result.detected_mime == "text/html"


@_BOUNDED
@given(payloads=st.lists(_PAYLOAD, min_size=1, max_size=8))
def test_warc_record_count_is_conserved_across_binary_payloads(
    payloads: list[bytes],
) -> None:
    """Embedded CR/LF and header-like bytes cannot split a counted record."""
    stream = io.BytesIO(b"\r\n\r\n".join(_record(payload) for payload in payloads))
    assert _verify_warc_stream(stream) == len(payloads)
    assert stream.read() == b""


@_BOUNDED
@given(payload=_PAYLOAD, extra=st.integers(min_value=1, max_value=4096))
def test_truncated_warc_payloads_are_rejected(payload: bytes, extra: int) -> None:
    """A declared byte count cannot be satisfied by a shorter physical payload."""
    stream = io.BytesIO(_record(payload, declared=len(payload) + extra))
    with pytest.raises(ValueError, match=r"^truncated_warc_record$"):
        _verify_warc_stream(stream)


@_BOUNDED
@given(length=st.integers(min_value=-(10**30), max_value=-1))
def test_negative_warc_lengths_are_rejected_before_reading_payload(length: int) -> None:
    """Negative lengths never become unbounded or wrapped reads."""
    with pytest.raises(ValueError, match=r"^invalid_warc_content_length$"):
        _verify_warc_stream(io.BytesIO(_record(b"", declared=length)))


@_BOUNDED
@given(payload=_PAYLOAD, compressed=st.booleans())
def test_wacz_members_preserve_warc_framing(
    payload: bytes, *, compressed: bool
) -> None:
    """ZIP and optional gzip wrapping preserve the independently known count."""
    raw = _record(payload)
    member = gzip.compress(raw, mtime=0) if compressed else raw
    suffix = ".warc.gz" if compressed else ".warc"
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic.wacz"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("datapackage.json", "{}")
            archive.writestr("archive/synthetic" + suffix, member)
        assert _verify_wacz_path(path) == 1


@_BOUNDED
@given(
    parts=st.lists(
        st.from_regex(r"[a-z]{1,12}", fullmatch=True), min_size=0, max_size=8
    )
)
def test_manifest_parent_segments_never_escape_the_root(parts: list[str]) -> None:
    """Any explicit parent segment is refused before filesystem lookup."""
    relative = "/".join([*parts, "..", "synthetic.bin"])
    with (
        tempfile.TemporaryDirectory() as directory,
        pytest.raises(ValueError, match=r"^unsafe_fixity_path$"),
    ):
        _resolve_manifest_entry(Path(directory), {"path": relative})
