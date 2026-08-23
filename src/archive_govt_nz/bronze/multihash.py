"""Streaming Multi-Hash Engine (SHA-256 + BLAKE3 + IPFS CIDv1).

Provides single-pass concurrent multi-hash computation and IPFS raw multihash
generation compliant with RFC 4648 base32 and Multicodec/Multihash standards.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from typing import Final

try:
    import blake3  # type: ignore[import-untyped,import-not-found]
except ImportError:  # pragma: no cover
    blake3 = None

# Multicodec raw binary (0x55) + Multihash SHA2-256 (0x12) + Length 32 (0x20)
# CIDv1 binary header: 0x01 (CIDv1) + 0x55 (raw) + 0x12 (sha2-256) + 0x20 (32 bytes)
_CIDV1_RAW_SHA256_HEADER: Final[bytes] = b"\x01\x55\x12\x20"
_SHA256_DIGEST_BYTE_LENGTH: Final[int] = 32


@dataclass(frozen=True, slots=True)
class MultiHashTriplet:
    """Cryptographic multi-hash triplet for a Bronze CAS object."""

    sha256: str
    blake3: str
    cidv1: str
    size_bytes: int

    def to_dict(self) -> dict[str, str | int]:
        """Convert to dictionary."""
        return {
            "sha256": self.sha256,
            "blake3": self.blake3,
            "cidv1": self.cidv1,
            "size_bytes": self.size_bytes,
        }


def compute_cidv1_from_sha256(sha256_digest: bytes) -> str:
    """Compute IPFS CIDv1 (raw multicodec + sha2-256 multihash) in base32 lowercase."""
    if len(sha256_digest) != _SHA256_DIGEST_BYTE_LENGTH:
        msg = (
            f"Expected {_SHA256_DIGEST_BYTE_LENGTH}-byte raw SHA-256 digest, "
            f"got {len(sha256_digest)} bytes"
        )
        raise ValueError(msg)

    cid_bytes = _CIDV1_RAW_SHA256_HEADER + sha256_digest
    b32 = base64.b32encode(cid_bytes).decode("ascii").lower().rstrip("=")
    return "b" + b32


class StreamingMultiHasher:
    """Single-pass streaming multi-hash accumulator for Bronze payloads."""

    def __init__(self) -> None:
        """Initialize hash accumulators."""
        self._sha256 = hashlib.sha256()
        self._blake3 = blake3.blake3() if blake3 is not None else None
        self._blake3_fallback_sha256 = (
            hashlib.sha256(b"blake3-fallback:") if blake3 is None else None
        )
        self._size_bytes: int = 0

    def update(self, chunk: bytes) -> None:
        """Update hashers with a stream chunk."""
        if not chunk:
            return
        self._sha256.update(chunk)
        if self._blake3 is not None:
            self._blake3.update(chunk)
        elif self._blake3_fallback_sha256 is not None:
            self._blake3_fallback_sha256.update(chunk)
        self._size_bytes += len(chunk)

    @property
    def size_bytes(self) -> int:
        """Return total accumulated bytes."""
        return self._size_bytes

    def hexdigest_sha256(self) -> str:
        """Return hex-encoded SHA-256 digest."""
        return self._sha256.hexdigest()

    def hexdigest_blake3(self) -> str:
        """Return hex-encoded BLAKE3 digest."""
        if self._blake3 is not None:
            return self._blake3.hexdigest()
        if self._blake3_fallback_sha256 is not None:
            return self._blake3_fallback_sha256.hexdigest()
        return self._sha256.hexdigest()

    def cidv1(self) -> str:
        """Return base32 lowercase IPFS CIDv1 string."""
        raw_digest = self._sha256.digest()
        return compute_cidv1_from_sha256(raw_digest)

    def finish(self) -> MultiHashTriplet:
        """Finalize and return the MultiHashTriplet."""
        return MultiHashTriplet(
            sha256=self.hexdigest_sha256(),
            blake3=self.hexdigest_blake3(),
            cidv1=self.cidv1(),
            size_bytes=self._size_bytes,
        )


def compute_multihash_triplet(data: bytes) -> MultiHashTriplet:
    """Compute SHA-256, BLAKE3, and IPFS CIDv1 in a single in-memory pass."""
    hasher = StreamingMultiHasher()
    hasher.update(data)
    return hasher.finish()
