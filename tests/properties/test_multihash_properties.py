"""Property contracts for Bronze multi-hash content identity."""

from __future__ import annotations

import base64
import hashlib

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.bronze.multihash import (
    StreamingMultiHasher,
    compute_cidv1_from_sha256,
    compute_multihash_triplet,
)


@given(payload=st.binary(max_size=16_384), chunk_size=st.integers(1, 1024))
def test_streaming_and_one_shot_multihashes_are_identical(
    payload: bytes, chunk_size: int
) -> None:
    """Chunk boundaries cannot alter any content-identity field."""
    streamed = StreamingMultiHasher()
    for offset in range(0, len(payload), chunk_size):
        streamed.update(payload[offset : offset + chunk_size])

    expected = compute_multihash_triplet(payload)
    actual = streamed.finish()

    assert actual == expected
    assert actual.sha256 == hashlib.sha256(payload).hexdigest()
    assert actual.size_bytes == len(payload)
    assert len(actual.blake3) == 64


@given(digest=st.binary(min_size=32, max_size=32))
def test_cidv1_encodes_the_raw_sha256_multihash(digest: bytes) -> None:
    """CIDv1 output has the exact raw-codec and SHA-256 multihash envelope."""
    cid = compute_cidv1_from_sha256(digest)
    padded = cid[1:].upper() + "=" * ((8 - len(cid[1:]) % 8) % 8)

    assert cid.startswith("bafkrei")
    assert cid == cid.lower()
    assert base64.b32decode(padded) == b"\x01\x55\x12\x20" + digest


@given(length=st.integers(0, 64).filter(lambda value: value != 32))
def test_cidv1_rejects_every_non_sha256_digest_length(length: int) -> None:
    """Only a raw 32-byte SHA-256 digest may enter the CID encoder."""
    with pytest.raises(ValueError, match="Expected 32-byte"):
        compute_cidv1_from_sha256(b"x" * length)
