"""Unit tests for Bronze streaming multi-hasher and IPFS CIDv1 engine."""

from __future__ import annotations

import pytest

from archive_govt_nz.bronze.manifest import build_bronze_record
from archive_govt_nz.bronze.models import (
    STANDARD_RECORD_LINK_COLUMNS,
    BronzePayloadFixity,
)
from archive_govt_nz.bronze.multihash import (
    StreamingMultiHasher,
    compute_cidv1_from_sha256,
    compute_multihash_triplet,
)


def test_standard_record_link_columns_includes_cidv1() -> None:
    """STANDARD_RECORD_LINK_COLUMNS contains nz_content_cidv1."""
    assert "nz_content_cidv1" in STANDARD_RECORD_LINK_COLUMNS


def test_cidv1_empty_string_rfc_vector() -> None:
    """Empty payload produces the canonical IPFS CIDv1 raw multihash."""
    triplet = compute_multihash_triplet(b"")
    assert (
        triplet.cidv1 == "bafkreihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku"
    )
    assert triplet.size_bytes == 0


def test_cidv1_hello_world_test_vector() -> None:
    """Known test string produces valid bafkrei... IPFS multihash."""
    triplet = compute_multihash_triplet(b"hello world\n")
    assert (
        triplet.cidv1 == "bafkreifjjcie6lypi6ny7amxnfftagclbuxndqonfipmb64f2km2devei4"
    )
    assert triplet.size_bytes == 12


def test_streaming_multihasher_incremental_parity() -> None:
    """Incremental chunk feeding yields identical hashes to one-shot calculation."""
    data = b"Arbitrary raw payload chunking test data for Bronze CAS fixity" * 10
    oneshot = compute_multihash_triplet(data)

    hasher = StreamingMultiHasher()
    chunk_size = 17
    for i in range(0, len(data), chunk_size):
        hasher.update(data[i : i + chunk_size])
    streamed = hasher.finish()

    assert streamed.sha256 == oneshot.sha256
    assert streamed.blake3 == oneshot.blake3
    assert streamed.cidv1 == oneshot.cidv1
    assert streamed.size_bytes == oneshot.size_bytes


def test_compute_cidv1_from_sha256_length_guard() -> None:
    """compute_cidv1_from_sha256 raises ValueError on invalid digest length."""
    with pytest.raises(ValueError, match="Expected 32-byte raw SHA-256 digest"):
        compute_cidv1_from_sha256(b"short")


def test_bronze_record_and_fixity_cidv1_roundtrip() -> None:
    """BronzeRecord contains cidv1 and round-trips via dictionary models."""
    payload = b'{"record": "nz-gazette-2026-01"}'
    rec = build_bronze_record(
        record_id="rec-001",
        domain="gazette",
        payload_bytes=payload,
        source_url="https://gazette.govt.nz/notice/001",
        cas_path="cas/sha256/123",
        media_type="application/json",
    )

    assert rec.fixity.cidv1 is not None
    assert rec.fixity.cidv1.startswith("bafkrei")

    fixity_dict = rec.fixity.to_dict()
    assert "cidv1" in fixity_dict
    assert fixity_dict["cidv1"] == rec.fixity.cidv1

    restored_fixity = BronzePayloadFixity.from_dict(fixity_dict)
    assert restored_fixity.cidv1 == rec.fixity.cidv1
