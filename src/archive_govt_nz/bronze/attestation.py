"""Offline Ed25519 Manifest Sealing and Attestation Engine for Bronze Strata B1.

Pure-Python RFC 8032 compliant Ed25519 digital signature signing and verification
for cryptographic manifest attestation without external SaaS dependencies.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

# RFC 8032 Edwards25519 Curve Constants
_Q: Final[int] = 2**255 - 19
_L: Final[int] = 2**252 + 27742317777372353535851937790883648493
_D: Final[int] = -121665 * pow(121666, _Q - 2, _Q) % _Q
_I: Final[int] = pow(2, (_Q - 1) // 4, _Q)
_ED25519_KEY_BYTES: Final[int] = 32
_ED25519_SIG_BYTES: Final[int] = 64


def _inv(x: int) -> int:
    return pow(x, _Q - 2, _Q)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_D * y * y + 1)
    x = pow(xx, (_Q + 3) // 8, _Q)
    if (x * x - xx) % _Q != 0:
        x = (x * _I) % _Q
    if x % 2 != 0:
        x = _Q - x
    return x


_BY: Final[int] = 4 * _inv(5) % _Q
_BX: Final[int] = _xrecover(_BY)
_B: Final[tuple[int, int]] = (_BX, _BY)


def _edwards_add(p: tuple[int, int], q: tuple[int, int]) -> tuple[int, int]:
    x1, y1 = p
    x2, y2 = q
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + _D * x1 * x2 * y1 * y2) % _Q
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - _D * x1 * x2 * y1 * y2) % _Q
    return (x3, y3)


def _scalarmult(p: tuple[int, int], e: int) -> tuple[int, int]:
    if e == 0:
        return (0, 1)
    q = _scalarmult(p, e // 2)
    q = _edwards_add(q, q)
    if e & 1:
        q = _edwards_add(q, p)
    return q


def _encodeint(y: int) -> bytes:
    return y.to_bytes(_ED25519_KEY_BYTES, "little")


def _encodepoint(p: tuple[int, int]) -> bytes:
    x, y = p
    b = bytearray(_encodeint(y))
    if x & 1:
        b[31] |= 0x80
    return bytes(b)


def _decodeint(b: bytes) -> int:
    return int.from_bytes(b, "little")


def _decodepoint(b: bytes) -> tuple[int, int]:
    y = int.from_bytes(b[:31] + bytes([b[31] & 0x7F]), "little")
    x = _xrecover(y)
    if bool(x & 1) != bool(b[31] & 0x80):
        x = _Q - x
    return (x, y)


def _h(m: bytes) -> bytes:
    return hashlib.sha512(m).digest()


def _derive_public_key(sk_bytes: bytes) -> bytes:
    h = _h(sk_bytes)
    a = int.from_bytes(h[:_ED25519_KEY_BYTES], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    point = _scalarmult(_B, a)
    return _encodepoint(point)


def _sign(sk_bytes: bytes, m: bytes) -> bytes:
    h = _h(sk_bytes)
    a = int.from_bytes(h[:_ED25519_KEY_BYTES], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    pub = _encodepoint(_scalarmult(_B, a))
    r = int.from_bytes(_h(h[_ED25519_KEY_BYTES:] + m), "little") % _L
    point_r = _scalarmult(_B, r)
    k = int.from_bytes(_h(_encodepoint(point_r) + pub + m), "little") % _L
    s = (r + k * a) % _L
    return _encodepoint(point_r) + _encodeint(s)


def _verify(pk_bytes: bytes, m: bytes, sig_bytes: bytes) -> bool:
    if len(sig_bytes) != _ED25519_SIG_BYTES or len(pk_bytes) != _ED25519_KEY_BYTES:
        return False
    try:
        point_r = _decodepoint(sig_bytes[:_ED25519_KEY_BYTES])
        point_a = _decodepoint(pk_bytes)
        s = _decodeint(sig_bytes[_ED25519_KEY_BYTES:])
        k = (
            int.from_bytes(_h(sig_bytes[:_ED25519_KEY_BYTES] + pk_bytes + m), "little")
            % _L
        )
        lhs = _scalarmult(_B, s)
        rhs = _edwards_add(point_r, _scalarmult(point_a, k))
    except Exception:  # noqa: BLE001
        return False
    else:
        return lhs == rhs


@dataclass(frozen=True, slots=True)
class ManifestSignature:
    """Attestation receipt for a cryptographically sealed Bronze manifest."""

    manifest_id: str
    manifest_sha256: str
    public_key: str
    signature: str
    signed_at: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            "schema_version": "archive-govt-nz.manifest-signature/v1",
            "manifest_id": self.manifest_id,
            "manifest_sha256": self.manifest_sha256,
            "public_key": self.public_key,
            "signature": self.signature,
            "signed_at": self.signed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManifestSignature:
        """Construct from dictionary."""
        return cls(
            manifest_id=str(data["manifest_id"]),
            manifest_sha256=str(data["manifest_sha256"]),
            public_key=str(data["public_key"]),
            signature=str(data["signature"]),
            signed_at=str(data["signed_at"]),
        )


class Ed25519Signer:
    """Deterministic Ed25519 signer for Bronze manifests."""

    def __init__(self, private_key_bytes: bytes) -> None:
        """Initialize signer with 32-byte secret seed."""
        if len(private_key_bytes) != _ED25519_KEY_BYTES:
            msg = (
                f"Private key seed must be {_ED25519_KEY_BYTES} bytes, "
                f"got {len(private_key_bytes)}"
            )
            raise ValueError(msg)
        self._private_key = private_key_bytes
        self._public_key = _derive_public_key(private_key_bytes)

    @classmethod
    def generate(cls) -> Ed25519Signer:
        """Generate a random cryptographically secure keypair."""
        return cls(secrets.token_bytes(_ED25519_KEY_BYTES))

    @classmethod
    def from_hex(cls, hex_seed: str) -> Ed25519Signer:
        """Load signer from a 64-hex-character seed."""
        return cls(bytes.fromhex(hex_seed))

    @property
    def public_key_bytes(self) -> bytes:
        """Return 32-byte public key."""
        return self._public_key

    @property
    def public_key_hex(self) -> str:
        """Return hex-encoded public key."""
        return self._public_key.hex()

    def sign(self, message: bytes) -> bytes:
        """Sign binary message with Ed25519 private key."""
        return _sign(self._private_key, message)

    def sign_hex(self, message: bytes) -> str:
        """Sign binary message and return hex signature."""
        return self.sign(message).hex()


class Ed25519Verifier:
    """Public key verifier for Ed25519 signatures."""

    def __init__(self, public_key_bytes: bytes) -> None:
        """Initialize verifier with 32-byte public key."""
        if len(public_key_bytes) != _ED25519_KEY_BYTES:
            msg = (
                f"Public key must be {_ED25519_KEY_BYTES} bytes, "
                f"got {len(public_key_bytes)}"
            )
            raise ValueError(msg)
        self._public_key = public_key_bytes

    @classmethod
    def from_hex(cls, public_key_hex: str) -> Ed25519Verifier:
        """Construct verifier from 64-hex public key string."""
        return cls(bytes.fromhex(public_key_hex))

    def verify(self, message: bytes, signature_bytes: bytes) -> bool:
        """Verify binary signature against message."""
        return _verify(self._public_key, message, signature_bytes)

    def verify_hex(self, message: bytes, signature_hex: str) -> bool:
        """Verify hex-encoded signature against message."""
        try:
            sig_bytes = bytes.fromhex(signature_hex)
        except ValueError:
            return False
        return self.verify(message, sig_bytes)


def seal_manifest(
    manifest_data: str | bytes | Path,
    signer: Ed25519Signer,
    *,
    output_sig_path: Path | None = None,
) -> ManifestSignature:
    """Seal a Bronze manifest and emit a detached .sig attestation."""
    raw_bytes: bytes
    if isinstance(manifest_data, Path):
        raw_bytes = manifest_data.read_bytes()
    elif isinstance(manifest_data, str):
        raw_bytes = manifest_data.encode("utf-8")
    else:
        raw_bytes = manifest_data

    parsed = json.loads(raw_bytes.decode("utf-8"))
    manifest_id = str(parsed.get("manifest_id", "unknown"))
    manifest_sha = hashlib.sha256(raw_bytes).hexdigest()
    sig_hex = signer.sign_hex(raw_bytes)

    attestation = ManifestSignature(
        manifest_id=manifest_id,
        manifest_sha256=manifest_sha,
        public_key=signer.public_key_hex,
        signature=sig_hex,
        signed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    if output_sig_path is not None:
        output_sig_path.write_text(
            json.dumps(attestation.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return attestation


def verify_manifest_seal(
    manifest_data: str | bytes | Path,
    signature_data: ManifestSignature | dict[str, Any] | Path,
    *,
    expected_public_key: str | None = None,
) -> bool:
    """Verify that a manifest matches its detached .sig signature."""
    raw_manifest: bytes
    if isinstance(manifest_data, Path):
        raw_manifest = manifest_data.read_bytes()
    elif isinstance(manifest_data, str):
        raw_manifest = manifest_data.encode("utf-8")
    else:
        raw_manifest = manifest_data

    attestation: ManifestSignature
    if isinstance(signature_data, Path):
        sig_dict = json.loads(signature_data.read_text(encoding="utf-8"))
        attestation = ManifestSignature.from_dict(sig_dict)
    elif isinstance(signature_data, dict):
        attestation = ManifestSignature.from_dict(signature_data)
    else:
        attestation = signature_data

    pub_key_hex = expected_public_key or attestation.public_key
    if expected_public_key and expected_public_key != attestation.public_key:
        return False

    verifier = Ed25519Verifier.from_hex(pub_key_hex)
    return verifier.verify_hex(raw_manifest, attestation.signature)
